import sys
from pathlib import Path

# Add src to path so we can import our modules
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))

from rag_chatbot.services.vector_service import VectorService
from rag_chatbot.config import settings

def main():
    print("Setting up ChromaDB for RAG...")
    
    # Initialize vector service
    vector_service = VectorService(persist_directory=settings.chromadb_path)
    
    # Add documents to vector database
    collection = vector_service.add_documents("data/documents")
    
    # Show stats
    stats = vector_service.get_collection_stats()
    print(f"\nVector database ready:")
    print(f"  Total chunks: {stats.get('total_chunks', 'Unknown')}")
    print(f"  Location: {stats.get('persist_directory', 'Unknown')}")
    
    # Test search
    print("\nTesting search...")
    results = vector_service.search("shesmu Gang", n_results=3)
    
    for i, result in enumerate(results, 1):
        print(f"\nResult {i} (similarity: {result['similarity']:.3f}):")
        print(f"Source: {result['metadata'].get('source_file', 'Unknown')}")
        print(f"Content: {result['content'][:200]}...")

if __name__ == "__main__":
    main()