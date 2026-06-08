"""Knowledge Router - 知识库管理接口"""
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from datetime import datetime
from typing import Optional
import sys, os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from core.database import get_db, execute_query, execute_insert
from services.knowledge_service import process_uploaded_file

router = APIRouter(prefix="/api/admin/knowledge", tags=["知识库管理"])

@router.post("/upload")
async def upload_knowledge(file: UploadFile = File(...), type: str = Form(...), description: str = Form("")):
    content = await file.read()
    result = process_uploaded_file(content, file.filename, type, description)
    return {"code": 200, "message": "success", "data": result,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}

@router.get("/status/{task_id}")
def get_status(task_id: str):
    with get_db() as conn:
        results = execute_query(conn, "SELECT * FROM knowledge_items WHERE item_id = ?", (task_id,))
    if not results:
        raise HTTPException(status_code=404, detail="任务不存在")
    item = results[0]
    return {"code": 200, "message": "success",
            "data": {"task_id": item["item_id"], "status": item["status"], "progress": item["progress"], "message": item["message"]},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}

@router.get("/list")
def get_list(type: Optional[str] = Query(None), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    conditions, params = [], []
    if type: conditions.append("type = ?"); params.append(type)
    where = " AND ".join(conditions) if conditions else "1=1"
    offset = (page - 1) * page_size
    with get_db() as conn:
        total = execute_query(conn, f"SELECT COUNT(*) as cnt FROM knowledge_items WHERE {where}", params)[0]["cnt"]
        items = execute_query(conn, f"SELECT * FROM knowledge_items WHERE {where} ORDER BY created_at DESC LIMIT {page_size} OFFSET {offset}", params)
    return {"code": 200, "message": "success",
            "data": {"items": items, "total": total, "page": page, "page_size": page_size},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}

@router.delete("/{item_id}")
def delete_item(item_id: str):
    with get_db() as conn:
        execute_insert(conn, "DELETE FROM knowledge_items WHERE item_id = ?", (item_id,))
    return {"code": 200, "message": "deleted", "data": {"message": "deleted"},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}