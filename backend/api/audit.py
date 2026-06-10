"""Audit Logs Router - 审计日志接口"""
from fastapi import APIRouter, Query
from datetime import datetime
from typing import Optional

from backend.core.database import get_db, execute_query

router = APIRouter(prefix="/api/admin/audit-logs", tags=["审计日志"])

@router.get("")
def get_audit_logs(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    agent_type: Optional[str] = Query(None), action: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None), date_to: Optional[str] = Query(None), user_id: Optional[str] = Query(None)):
    conditions, params = [], []
    if agent_type: conditions.append("agent_type = %s"); params.append(agent_type)
    if action: conditions.append("action = %s"); params.append(action)
    if user_id: conditions.append("user_id = %s"); params.append(user_id)
    if date_from: conditions.append("created_at >= %s"); params.append(date_from)
    if date_to: conditions.append("created_at <= %s"); params.append(date_to)
    where = " AND ".join(conditions) if conditions else "1=1"
    offset = (page - 1) * page_size
    with get_db() as conn:
        total = execute_query(conn, f"SELECT COUNT(*) as cnt FROM audit_logs WHERE {where}", params)[0]["cnt"]
        items = execute_query(conn, f"SELECT * FROM audit_logs WHERE {where} ORDER BY created_at DESC LIMIT {page_size} OFFSET {offset}", params)
    return {"code": 200, "message": "success",
            "data": {"items": items, "total": total, "page": page, "page_size": page_size},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}
