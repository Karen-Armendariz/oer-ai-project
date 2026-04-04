import chromadb
from sentence_transformers import SentenceTransformer
from pathlib import Path
import logging
import os

# Suppress technical logs from transformers and tokenizers
logging.getLogger("transformers").setLevel(logging.ERROR)
os.environ["TOKENIZERS_PARALLELISM"] = "false"

class OERRAGStore:
    def __init__(self, persist_directory="data/chroma_db", model_name="all-MiniLM-L6-v2"):
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.model = SentenceTransformer(model_name)
        self.collection = self.client.get_or_create_collection("oer_resources")

    def add_resources(self, resources):
        """Add list of OER resource dictionaries to the vector store."""
        ids = []
        documents = []
        metadatas = []
        embeddings = []

        for r in resources:
            doc_text = f"Title: {r['title']}\nDescription: {r['description']}\nCreators: {', '.join(r['creators'])}\nLicense: {r['license']}"
            
            # Use sentence-transformers to generate embeddings
            embedding = self.model.encode(doc_text).tolist()
            
            ids.append(str(r['id']))
            documents.append(doc_text)
            metadatas.append({
                "title": r['title'],
                "license": r['license'],
                "creators": ", ".join(r['creators']),
                "links": str(r['links']) # Store as string for metadata
            })
            embeddings.append(embedding)

        if ids:
            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )
            print(f"Index updated with {len(ids)} resources in ChromaDB.")

    def query_oer(self, syllabus_text, n_results=5):
        """Find the most relevant OER resources for the given syllabus text."""
        query_embedding = self.model.encode(syllabus_text).tolist()
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results

if __name__ == "__main__":
    store = OERRAGStore()
    print("OER RAG Store initialized.")
