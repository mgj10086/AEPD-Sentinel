"""Health Check Router"""
from fastapi import APIRouter
import time

from backend.core.database import get_connection, _engine
from backend.services.rag_engine import CHROMA_AVAILABLE, client as chroma_client

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
            # SQLite: 直接使用 execute
            conn.execute("SELECT 1")
        conn.close()
        return True
    except Exception:
        return False


def _check_chroma() -> bool:
    """真实 ChromaDB 连接检查"""
    if not CHROMA_AVAILABLE:
        return False
    try:
        if chroma_client is not None:
            # 尝试获取 collection 列表来验证连接
            chroma_client.list_collections()
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
