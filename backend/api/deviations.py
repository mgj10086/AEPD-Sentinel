"""Deviations Router - 方案偏离接口"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime
import sys, os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.core.database import get_db, execute_query, execute_insert

router = APIRouter(prefix="/api/deviations", tags=["方案偏离"])

@router.get("/rules")
def get_rules():
    with get_db() as conn:
        items = execute_query(conn, "SELECT * FROM deviation_rules")
    return {"code": 200, "message": "success", "data": items,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}

@router.get("/poll")
def poll_deviations(last_check_time: str = Query(...)):
    with get_db() as conn:
        items = execute_query(conn, "SELECT * FROM deviations WHERE created_at > ? AND status = 'pending' ORDER BY created_at DESC", (last_check_time,))
    return {"code": 200, "message": "success",
            "data": {"new_deviations": items, "latest_time": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}

@router.get("/list")
def get_deviations_list(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    severity: Optional[str] = Query(None), status: Optional[str] = Query(None), patient_id: Optional[str] = Query(None)):
    conditions, params = [], []
    if severity: conditions.append("severity = ?"); params.append(severity)
    if status: conditions.append("status = ?"); params.append(status)
    if patient_id: conditions.append("patient_id = ?"); params.append(patient_id)
    where = " AND ".join(conditions) if conditions else "1=1"
    offset = (page - 1) * page_size
    with get_db() as conn:
        total = execute_query(conn, f"SELECT COUNT(*) as cnt FROM deviations WHERE {where}", params)[0]["cnt"]
        items = execute_query(conn, f"SELECT * FROM deviations WHERE {where} ORDER BY created_at DESC LIMIT {page_size} OFFSET {offset}", params)
    return {"code": 200, "message": "success",
            "data": {"items": items, "total": total, "page": page, "page_size": page_size},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}

@router.get("/{deviation_id}")
def get_deviation_detail(deviation_id: str):
    with get_db() as conn:
        results = execute_query(conn, "SELECT * FROM deviations WHERE deviation_id = ?", (deviation_id,))
    if not results:
        raise HTTPException(status_code=404, detail="偏离记录不存在")
    return {"code": 200, "message": "success", "data": results[0],
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}

@router.put("/{deviation_id}/resolve")
def resolve_deviation(deviation_id: str, req: dict):
    with get_db() as conn:
        execute_insert(conn, "UPDATE deviations SET status = 'resolved', resolution = ?, resolved_by = ?, action_taken = ? WHERE deviation_id = ?",
            (req.get("resolution"), req.get("resolved_by"), req.get("action_taken"), deviation_id))
    return {"code": 200, "message": "resolved", "data": {"deviation_id": deviation_id},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}