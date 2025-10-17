# Debug script to see what chunks were created
from pathlib import Path
import sys
sys.path.append('src')
from rag_chatbot.services.vector_service import VectorService

vector_service = VectorService()
collection = vector_service.get_or_create_collection()

# Search for any chunks containing "Gang"
results = collection.get(
    where={"source_file": "shesmu_glossary.md"}
)

for i, doc in enumerate(results["documents"]):
    if "Gang" in doc:
        print(f"Chunk {i}:")
        print(doc)
        print("---")
