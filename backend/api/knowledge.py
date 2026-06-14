"""Knowledge Router - 知识库管理接口"""
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form, Request
from datetime import datetime
from typing import Optional

from backend.core.database import get_db, execute_query, execute_insert
from backend.services.knowledge_service import process_uploaded_file
from backend.services.rag_engine import search_documents
from backend.services.audit_service import extract_username_from_token, write_audit_log

router = APIRouter(prefix="/api/admin/knowledge", tags=["知识库管理"])

# 上传限制
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".md", ".csv", ".txt", ".pdf", ".json"}

@router.post("/upload")
async def upload_knowledge(file: UploadFile = File(...), type: str = Form(...), description: str = Form(""), request: Request = None):
    try:
        # 文件类型校验
        import os
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}。支持: {', '.join(ALLOWED_EXTENSIONS)}")
        # 文件大小校验
        content = await file.read()
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=400, detail=f"文件过大（{len(content)/1024/1024:.1f}MB），最大允许10MB")
        result = process_uploaded_file(content, file.filename, type, description)
        # 写入审计日志
        user_id = extract_username_from_token(request.headers.get("Authorization", "")) if request else "anonymous"
        write_audit_log(user_id, "knowledge", "upload", result["item_id"],
                        f"上传知识文档: {file.filename} 类型={type}")
        return {"code": 200, "message": "success", "data": result,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[Upload Error] {file.filename if file else '?'}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@router.get("/status/{task_id}")
def get_status(task_id: str):
    with get_db() as conn:
        results = execute_query(conn, "SELECT * FROM knowledge_items WHERE item_id = %s", (task_id,))
    if not results:
        raise HTTPException(status_code=404, detail="任务不存在")
    item = results[0]
    return {"code": 200, "message": "success",
            "data": {"task_id": item["item_id"], "status": item["status"], "progress": item["progress"], "message": item["message"]},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}

@router.get("/list")
def get_list(type: Optional[str] = Query(None), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    conditions, params = [], []
    if type: conditions.append("type = %s"); params.append(type)
    where = " AND ".join(conditions) if conditions else "1=1"
    offset = (page - 1) * page_size
    with get_db() as conn:
        total = execute_query(conn, f"SELECT COUNT(*) as cnt FROM knowledge_items WHERE {where}", params)[0]["cnt"]
        items = execute_query(conn, f"SELECT * FROM knowledge_items WHERE {where} ORDER BY created_at DESC LIMIT {page_size} OFFSET {offset}", params)
    return {"code": 200, "message": "success",
            "data": {"items": items, "total": total, "page": page, "page_size": page_size},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}

@router.get("/search")
def search_knowledge(query: str = Query(..., min_length=1), n_results: int = Query(5, ge=1, le=20)):
    """向量检索知识库"""
    results = search_documents(query, n_results=n_results)
    items = []
    for doc, meta in results:
        items.append({"content": doc[:500], "metadata": meta, "score": meta.get("distance", 0) if meta else 0})
    return {"code": 200, "message": "success",
            "data": {"query": query, "results": items, "total": len(items)},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}

@router.delete("/{item_id}")
def delete_item(item_id: str, request: Request):
    with get_db() as conn:
        execute_insert(conn, "DELETE FROM knowledge_items WHERE item_id = %s", (item_id,))
    # 写入审计日志
    user_id = extract_username_from_token(request.headers.get("Authorization", ""))
    write_audit_log(user_id, "knowledge", "delete", item_id,
                    f"删除知识文档: {item_id}")
    return {"code": 200, "message": "deleted", "data": {"message": "deleted"},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}
