import chromadb
from chromadb.utils import embedding_functions

# 1. Point it specifically inside the backend folder
client = chromadb.PersistentClient(path="./backend/data/chroma_db")

default_ef = embedding_functions.DefaultEmbeddingFunction()

# 2. Use the name "ggc_oer_collection"
oer_collection = client.get_or_create_collection(
    name="ggc_oer_collection", 
    embedding_function=default_ef
)

# Adding the data
oer_collection.add(
    documents=["Cells are the basic building blocks of all living things...", "Mitosis is a process of cell division..."],
    metadatas=[{"source": "OpenStax Biology Ch1"}, {"source": "OpenStax Biology Ch10"}],
    ids=["id1", "id2"]
)
print("OER Data Ingested Successfully into backend/data/chroma_db")