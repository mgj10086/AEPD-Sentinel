"""RAG Engine - ChromaDB向量检索"""
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from core.config import CHROMA_DIR, CHROMA_COLLECTION

try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

client = None
collection = None

def init_chroma():
    global client, collection
    if not CHROMA_AVAILABLE:
        print("ChromaDB not available, using fallback search")
        return False
    os.makedirs(CHROMA_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        collection = client.get_or_create_collection(
            name=CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"ChromaDB initialized, collection has {collection.count()} documents")
        return True
    except Exception as e:
        print(f"ChromaDB init error: {e}")
        return False

def add_documents(documents: list, metadatas: list = None, ids: list = None):
    global collection
    if not collection:
        if not init_chroma():
            return False
    if ids is None:
        ids = [f"doc_{i}" for i in range(len(documents))]
    if metadatas is None:
        metadatas = [{} for _ in documents]
    try:
        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        return True
    except Exception as e:
        print(f"ChromaDB add error: {e}")
        return False

def search_documents(query: str, n_results: int = 5, where: dict = None) -> list:
    global collection
    if not collection:
        if not init_chroma():
            return []
    try:
        kwargs = {"query_texts": [query], "n_results": n_results}
        if where:
            kwargs["where"] = where
        results = collection.query(**kwargs)
        if results["documents"]:
            return list(zip(results["documents"][0], results["metadatas"][0]))
        return []
    except Exception as e:
        print(f"ChromaDB search error: {e}")
        return []

def delete_documents(ids: list):
    global collection
    if not collection:
        return False
    try:
        collection.delete(ids=ids)
        return True
    except Exception as e:
        print(f"ChromaDB delete error: {e}")
        return False