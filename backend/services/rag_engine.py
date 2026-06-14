"""RAG Engine - ChromaDB向量检索"""
import os

# 必须在 import chromadb 之前禁用遥探，否则 posthog capture() API 不兼容报错
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

from backend.core.config import CHROMA_DIR, CHROMA_COLLECTION

try:
    import chromadb
    CHROMA_AVAILABLE = True
    # 禁用 ChromaDB 遥探：直接替换 PostHog.capture 为 no-op
    # ChromaDB 1.5.x 的 telemetry 与新版 posthog 不兼容，env/settings 均无法阻止报错
    try:
        from chromadb.telemetry.posthog import PostHog
        PostHog.capture = lambda self, event: None
    except Exception:
        pass
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

    # ChromaDB 1.5.x 遥探与新版 posthog 不兼容，抑制 stderr 噪音
    import sys, io
    _stderr = sys.stderr
    sys.stderr = io.StringIO()
    try:
        try:
            client = chromadb.PersistentClient(
                path=CHROMA_DIR,
                settings=chromadb.Settings(anonymized_telemetry=False)
            )
        except TypeError:
            client = chromadb.PersistentClient(path=CHROMA_DIR)
    finally:
        sys.stderr = _stderr

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