"""Health Check Router"""
from fastapi import APIRouter
import time

from backend.core.database import get_connection, _engine
import backend.services.rag_engine as rag_engine

START_TIME = time.time()

router = APIRouter(prefix="/api", tags=["健康检查"])


def _check_db() -> bool:
    """真实数据库连接检查"""
    try:
        conn = get_connection()
        if _engine == "mysql":
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        else:
            conn.execute("SELECT 1")
        conn.close()
        return True
    except Exception:
        return False


def _check_chroma() -> bool:
    """真实 ChromaDB 连接检查（通过模块引用避免 import 绑定过时）"""
    if not rag_engine.CHROMA_AVAILABLE:
        return False
    try:
        if rag_engine.client is not None:
            rag_engine.client.list_collections()
            return True
        return False
    except Exception:
        return False


@router.get("/health")
def health_check():
    uptime = int(time.time() - START_TIME)
    db_ok = _check_db()
    chroma_ok = _check_chroma()

    return {
        "code": 200,
        "message": "success",
        "data": {
            "llm_status": "mock",
            "vector_db_status": "healthy" if chroma_ok else "unhealthy",
            "mysql_status": "healthy" if db_ok else "unhealthy",
            "model_name": "rule-based-meddra-matcher",
            "uptime_seconds": uptime
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
