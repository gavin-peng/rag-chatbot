import chromadb
from chromadb.config import Settings
from pathlib import Path
from typing import List, Dict, Any
import re
from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from rag_chatbot.config import settings
from langchain_community.embeddings import HuggingFaceEmbeddings

class VectorService:
    def __init__(self, persist_directory: str = None):
        if persist_directory is None:
            persist_directory = settings.chromadb_path
        
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection_name = "documents"
        
        # Use local embeddings instead of Google API
        print("Loading local embedding model...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print("Embedding model loaded successfully")
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def get_or_create_collection(self):
        """Get existing collection or create new one"""
        try:
            collection = self.client.get_collection(name=self.collection_name)
            print(f"Using existing collection: {self.collection_name}")
        except Exception:
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"Created new collection: {self.collection_name}")
        
        return collection

    def process_markdown_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process a markdown file into chunks"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "glossary" in file_path.name.lower():
            return self._process_glossary_file(content, file_path)
    
        # Extract source URL if present
        source_url = "Unknown"
        lines = content.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            if line.startswith("Source:"):
                source_url = line.replace("Source:", "").strip()
                break
        
        # Split by headers first
        try:
            header_splits = self.markdown_splitter.split_text(content)
        except Exception:
            # Fallback to regular splitting if markdown splitting fails
            header_splits = [content]
        
        # Further split large chunks
        chunks = []
        for i, split in enumerate(header_splits):
            if isinstance(split, str):
                text = split
                metadata = {}
            else:
                # LangChain Document object
                text = split.page_content
                metadata = split.metadata
            
            # Split large chunks further
            if len(text) > 1000:
                sub_chunks = self.text_splitter.split_text(text)
                for j, sub_chunk in enumerate(sub_chunks):
                    chunks.append({
                        'text': sub_chunk,
                        'metadata': {
                            **metadata,
                            'source_file': str(file_path.name),
                            'source_url': source_url,
                            'chunk_id': f"{file_path.stem}_{i}_{j}",
                            'chunk_size': len(sub_chunk)
                        }
                    })
            else:
                chunks.append({
                    'text': text,
                    'metadata': {
                        **metadata,
                        'source_file': str(file_path.name),
                        'source_url': source_url,
                        'chunk_id': f"{file_path.stem}_{i}",
                        'chunk_size': len(text)
                    }
                })
        
        return chunks

    def _process_glossary_file(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Process glossary files to keep definitions separate"""
        chunks = []
        
        # Split by ## headers
        sections = re.split(r'\n## ', content)
        
        for i, section in enumerate(sections):
            if not section.strip():
                continue
                
            # Add ## back except for first section
            if i > 0:
                section = "## " + section
                
            chunks.append({
                'text': section.strip(),
                'metadata': {
                    'source_file': str(file_path.name),
                    'chunk_id': f"{file_path.stem}_glossary_{i}",
                    'chunk_type': 'glossary_entry',
                    'chunk_size': len(section)
                }
            })
        
        return chunks
    
    def add_documents(self, docs_directory: str = "data/documents"):
        """Add all markdown documents to the vector database"""
        docs_path = Path(docs_directory)
        collection = self.get_or_create_collection()
        
        # Get existing document IDs to avoid duplicates
        try:
            existing_ids = set(collection.get()["ids"])
        except Exception:
            existing_ids = set()
        
        total_chunks = 0
        processed_files = 0
        
        for file_path in docs_path.glob("*.md"):
            print(f"Processing: {file_path.name}")
            
            chunks = self.process_markdown_file(file_path)
            
            # Filter out existing chunks
            new_chunks = [
                chunk for chunk in chunks 
                if chunk['metadata']['chunk_id'] not in existing_ids
            ]
            
            if not new_chunks:
                print(f"  Skipping {file_path.name} - already processed")
                continue
            
            # Generate embeddings
            texts = [chunk['text'] for chunk in new_chunks]
            try:
                embeddings = self.embeddings.embed_documents(texts)
                
                # Add to collection
                collection.add(
                    documents=texts,
                    metadatas=[chunk['metadata'] for chunk in new_chunks],
                    ids=[chunk['metadata']['chunk_id'] for chunk in new_chunks],
                    embeddings=embeddings
                )
                
                print(f"  Added {len(new_chunks)} chunks from {file_path.name}")
                total_chunks += len(new_chunks)
                processed_files += 1
                
            except Exception as e:
                print(f"  Error processing {file_path.name}: {e}")
        
        print(f"\nProcessing complete:")
        print(f"  Files processed: {processed_files}")
        print(f"  Total chunks added: {total_chunks}")
        
        return collection

    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        collection = self.get_or_create_collection()
        
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)
        
        # Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results["documents"][0])):
            formatted_results.append({
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "similarity": 1 - results["distances"][0][i]  # Convert distance to similarity
            })
        
        return formatted_results

    def get_collection_stats(self):
        """Get statistics about the collection"""
        collection = self.get_or_create_collection()
        
        try:
            count = collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            return {"error": str(e)}