import chromadb
from chromadb.config import Settings
from pathlib import Path
from typing import List, Dict, Any, Union
import re
import hashlib
from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from rag_chatbot.config import settings
from langchain_huggingface import HuggingFaceEmbeddings


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
        
        # Initialize markdown splitter
        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
            ]
        )
        
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
                            'chunk_size': len(sub_chunk),
                            'source_type': 'markdown_document'
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
                        'chunk_size': len(text),
                        'source_type': 'markdown_document'
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
                    'chunk_size': len(section),
                    'source_type': 'markdown_document'
                }
            })
        
        return chunks
    
    def add_documents(self, docs_directory: Union[str, List[Document]] = "data/documents"):
        """
        Add documents to the vector database
        
        Args:
            docs_directory: Either a path to directory of markdown files (str),
                          or a list of LangChain Document objects (for repository ingestion)
        """
        # Check if it's a list (regardless of what's in it)
        if isinstance(docs_directory, list):
            self.add_document_objects(docs_directory)
            return
        
        # Handle directory path (existing markdown functionality)
        docs_path = Path(docs_directory)
        
        if not docs_path.exists():
            print(f"Warning: Directory does not exist: {docs_directory}")
            return
        
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


    def add_document_objects(self, documents: List[Document], batch_size: int = 100):
        """
        Add Document objects directly to the vector store (for repository code ingestion)
        
        Args:
            documents: List of LangChain Document objects
            batch_size: Number of documents to process in each batch
        """
        if not documents:
            print("No documents to add")
            return
        
        collection = self.get_or_create_collection()
        
        # Get existing IDs to avoid duplicates
        try:
            existing_ids = set(collection.get()["ids"])
            print(f"Found {len(existing_ids)} existing documents in collection")
        except Exception:
            existing_ids = set()
        
        texts = []
        metadatas = []
        ids = []
        
        print(f"Preparing {len(documents)} documents for indexing...")
        
        skipped_existing = 0
        
        for i, doc in enumerate(documents):
            # Create a TRULY unique identifier using MD5 hash
            # Include repo name to distinguish same files from different repos
            repo_name = doc.metadata.get('repo_name', 'unknown')
            source_file = doc.metadata.get('source_file', 'unknown')
            chunk_index = doc.metadata.get('chunk_index', 0)
            
            # Use more content for hash to avoid collisions (first 500 chars)
            content_sample = doc.page_content[:500] if len(doc.page_content) > 500 else doc.page_content
            
            # Create deterministic hash - same repo + file + chunk + content = same ID
            unique_string = f"{repo_name}|{source_file}|{chunk_index}|{content_sample}"
            doc_hash = hashlib.md5(unique_string.encode()).hexdigest()
            doc_id = f"repo_{doc_hash}"
            
            # Skip if already exists
            if doc_id in existing_ids:
                skipped_existing += 1
                continue
            
            texts.append(doc.page_content)
            metadatas.append(doc.metadata)
            ids.append(doc_id)
        
        if skipped_existing > 0:
            print(f"Skipped {skipped_existing} documents that already exist")
        
        if not texts:
            print("All documents already exist in collection")
            return
        
        # Process in batches
        total_batches = (len(texts) + batch_size - 1) // batch_size
        print(f"Processing {len(texts)} new documents in {total_batches} batches...")
        
        added_count = 0
        error_count = 0
        
        for batch_idx in range(0, len(texts), batch_size):
            batch_texts = texts[batch_idx:batch_idx + batch_size]
            batch_metadatas = metadatas[batch_idx:batch_idx + batch_size]
            batch_ids = ids[batch_idx:batch_idx + batch_size]
            
            try:
                # Get embeddings for batch
                batch_embeddings = self.embeddings.embed_documents(batch_texts)
                
                # Add to collection
                collection.add(
                    embeddings=batch_embeddings,
                    documents=batch_texts,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
                
                current_batch = (batch_idx // batch_size) + 1
                added_count += len(batch_texts)
                print(f"  ✓ Batch {current_batch}/{total_batches} complete ({len(batch_texts)} chunks, total: {added_count}/{len(texts)})")
                
            except Exception as e:
                error_count += 1
                current_batch = (batch_idx // batch_size) + 1
                print(f"  ✗ Error processing batch {current_batch}: {e}")
                # Continue processing remaining batches
                continue
        
        print(f"✓ Successfully added {added_count} new document chunks to vector store")
        if error_count > 0:
            print(f"⚠ {error_count} batches failed - approximately {len(texts) - added_count} chunks not added")

    def search(self, query: str, n_results: int = 5, filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant documents with optional metadata filtering
        
        Args:
            query: Search query string
            n_results: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {'language': 'python'})
        """
        collection = self.get_or_create_collection()
        
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)
        
        # Build query parameters
        query_params = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"]
        }
        
        # Add metadata filter if provided
        if filter_metadata:
            query_params["where"] = filter_metadata
        
        # Search
        results = collection.query(**query_params)
        
        # Format results
        formatted_results = []
        for i in range(len(results["documents"][0])):
            formatted_results.append({
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "similarity": 1 - results["distances"][0][i]  # Convert distance to similarity
            })
        
        return formatted_results

    def search_by_language(
        self, 
        query: str, 
        languages: List[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search with language filtering
        
        Args:
            query: Search query
            languages: List of language codes to filter by (e.g., ['python', 'java'])
            n_results: Number of results to return
        """
        # Get more results initially
        all_results = self.search(query, n_results=n_results * 3)
        
        # Filter by language if specified
        if languages:
            filtered_results = [
                r for r in all_results 
                if r['metadata'].get('language') in languages
            ]
            return filtered_results[:n_results]
        
        return all_results[:n_results]

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        collection = self.get_or_create_collection()
        
        try:
            count = collection.count()
            
            # Get sample of documents to analyze
            sample = collection.get(limit=min(count, 100))
            
            # Count by source type
            source_types = {}
            languages = {}
            file_categories = {}
            
            for metadata in sample.get('metadatas', []):
                # Count source types
                source_type = metadata.get('source_type', 'unknown')
                source_types[source_type] = source_types.get(source_type, 0) + 1
                
                # Count languages (for code files)
                if 'language' in metadata:
                    lang = metadata['language']
                    languages[lang] = languages.get(lang, 0) + 1
                
                # Count file categories
                if 'file_category' in metadata:
                    cat = metadata['file_category']
                    file_categories[cat] = file_categories.get(cat, 0) + 1
            
            return {
                "total_chunks": count,
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory,
                "source_types": source_types,
                "languages": languages,
                "file_categories": file_categories
            }
        except Exception as e:
            return {"error": str(e)}

    def clear_collection(self):
        """Clear all documents from the collection (use with caution!)"""
        try:
            self.client.delete_collection(name=self.collection_name)
            print(f"✓ Deleted collection: {self.collection_name}")
            self.get_or_create_collection()
            print(f"✓ Created fresh collection: {self.collection_name}")
        except Exception as e:
            print(f"Error clearing collection: {e}")

    def delete_by_repo(self, repo_name: str):
        """Delete all documents from a specific repository"""
        collection = self.get_or_create_collection()
        
        try:
            # Get all documents from this repo
            results = collection.get(
                where={"repo_name": repo_name}
            )
            
            if results['ids']:
                collection.delete(ids=results['ids'])
                print(f"✓ Deleted {len(results['ids'])} chunks from repository: {repo_name}")
            else:
                print(f"No documents found for repository: {repo_name}")
                
        except Exception as e:
            print(f"Error deleting repository documents: {e}")