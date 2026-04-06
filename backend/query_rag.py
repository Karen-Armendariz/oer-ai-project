import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path

# Must match the path in ingest_oer.py exactly
DB_PATH = Path("./backend/data/chroma_db")
# Must match the syllabus file your teammate's script creates
SYLLABUS_PATH = Path("./backend/data/syllabi/sample_syllabus.txt") 
COLLECTION_NAME = "ggc_oer_collection"

def get_oer_recommendations():
    client = chromadb.PersistentClient(path=str(DB_PATH))
    ef = embedding_functions.DefaultEmbeddingFunction()
    
    # This will now find the collection because the names match
    collection = client.get_collection(name=COLLECTION_NAME, embedding_function=ef)

    if not SYLLABUS_PATH.exists():
        print(f"Error: Could not find syllabus at {SYLLABUS_PATH}")
        return

    syllabus_text = SYLLABUS_PATH.read_text(encoding="utf-8")
    results = collection.query(query_texts=[syllabus_text], n_results=2)

    print("\n--- AI Recommended OER Resources ---")
    for i, doc in enumerate(results['documents'][0]):
        print(f"Match #{i+1}: {doc[:200]}...")