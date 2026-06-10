"""Health Check Router"""
from fastapi import APIRouter
import time

from backend.core.database import get_connection

START_TIME = time.time()

router = APIRouter(prefix="/api", tags=["健康检查"])

@router.get("/health")
def health_check():
    uptime = int(time.time() - START_TIME)
    db_ok = False
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        conn.close()
        db_ok = True
    except:
        pass
    return {
        "code": 200,
        "message": "success",
        "data": {
            "llm_status": "healthy",
            "vector_db_status": "healthy",
            "mysql_status": "healthy" if db_ok else "unhealthy",
            "model_name": "mock-meddra-matcher",
            "uptime_seconds": uptime
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
