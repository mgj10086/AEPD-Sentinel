"""Knowledge Service - 知识文档管理"""
import json
import os
import uuid
import re
from datetime import datetime

from backend.core.database import get_db, execute_query, execute_insert
from backend.services.rag_engine import init_chroma, add_documents, search_documents

def generate_item_id():
    return f"KNW-{uuid.uuid4().hex[:12]}"

def process_uploaded_file(file_content: bytes, file_name: str, doc_type: str, description: str = "") -> dict:
    item_id = generate_item_id()
    item = {
        "item_id": item_id, "title": file_name, "type": doc_type,
        "description": description, "status": "processing", "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
    ext = os.path.splitext(file_name)[1].lower()
    content = ""
    try:
        if ext == ".md":
            content = file_content.decode("utf-8")
        elif ext == ".csv":
            content = file_content.decode("utf-8")
            lines = content.split("\n")
            content = "\n".join(lines[:100])
        elif ext == ".txt":
            content = file_content.decode("utf-8")
        else:
            content = f"[{file_name}] 已上传"
    except: content = f"[{file_name}] 解析失败"
    
    with get_db() as conn:
        execute_insert(conn, "INSERT INTO knowledge_items (item_id, type, file_name, description, status, progress, message, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (item_id, doc_type, file_name, description, "processing", 0.5, "已上传，待向量化", item["created_at"]))
    
    # Add to ChromaDB
    try:
        success = add_documents([content], [{"item_id": item_id, "type": doc_type}], [item_id])
        if success:
            with get_db() as conn:
                execute_insert(conn, "UPDATE knowledge_items SET status = 'completed', progress = %s, message = %s WHERE item_id = %s",
                    (1.0, "已完成向量化", item_id))
            item["status"] = "completed"
            item["message"] = "向量化成功"
            item["progress"] = 1.0
        else:
            # ChromaDB 不可用时，标记为完成但注明未向量化
            with get_db() as conn:
                execute_insert(conn, "UPDATE knowledge_items SET status = 'completed', progress = %s, message = %s WHERE item_id = %s",
                    (1.0, "已保存（向量数据库不可用，跳过向量化）", item_id))
            item["status"] = "completed"
            item["message"] = "已保存（未向量化）"
            item["progress"] = 1.0
    except Exception as e:
        item["status"] = "failed"
        item["message"] = f"向量化失败: {str(e)}"
        try:
            with get_db() as conn:
                execute_insert(conn, "UPDATE knowledge_items SET status = %s, message = %s WHERE item_id = %s",
                    ("failed", item["message"], item_id))
        except Exception:
            pass  # 数据库更新失败不影响返回

    if "progress" not in item:
        item["progress"] = 0.5
    return item

def get_knowledge_list(doc_type: str = "", page: int = 1, page_size: int = 20) -> dict:
    offset = (page - 1) * page_size
    conditions, params = [], []
    if doc_type: conditions.append("type = %s"); params.append(doc_type)
    where = " AND ".join(conditions) if conditions else "1=1"
    with get_db() as conn:
        total = execute_query(conn, f"SELECT COUNT(*) as cnt FROM knowledge_items WHERE {where}", params)[0]["cnt"]
        items = execute_query(conn, f"SELECT * FROM knowledge_items WHERE {where} ORDER BY created_at DESC LIMIT {page_size} OFFSET {offset}", params)
    return {"total": total, "page": page, "page_size": page_size, "items": items}
