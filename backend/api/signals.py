"""Signals Router - 安全性信号接口"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime
import json
import sys, os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from core.database import get_db, execute_query, execute_insert
from agents.signal_agent import analyze_signal

router = APIRouter(prefix="/api/signals", tags=["安全性信号"])

@router.get("/list")
def get_signals_list(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None), drug_name: Optional[str] = Query(None)):
    conditions, params = [], []
    if status: conditions.append("signal_status = ?"); params.append(status)
    if drug_name: conditions.append("drug_name = ?"); params.append(drug_name)
    where = " AND ".join(conditions) if conditions else "1=1"
    offset = (page - 1) * page_size
    with get_db() as conn:
        total = execute_query(conn, f"SELECT COUNT(*) as cnt FROM signals WHERE {where}", params)[0]["cnt"]
        items = execute_query(conn, f"SELECT * FROM signals WHERE {where} ORDER BY created_at DESC LIMIT {page_size} OFFSET {offset}", params)
        for item in items:
            if item.get("related_literature"):
                item["related_literature"] = json.loads(item["related_literature"])
    return {"code": 200, "message": "success",
            "data": {"items": items, "total": total, "page": page, "page_size": page_size},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}

@router.get("/{signal_id}")
def get_signal_detail(signal_id: str):
    with get_db() as conn:
        results = execute_query(conn, "SELECT * FROM signals WHERE signal_id = ?", (signal_id,))
    if not results:
        raise HTTPException(status_code=404, detail="信号不存在")
    item = results[0]
    if item.get("related_literature"):
        item["related_literature"] = json.loads(item["related_literature"])
    return {"code": 200, "message": "success", "data": item,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}

@router.post("/trigger")
def trigger_analysis(req: dict):
    import threading
    drug_name = req.get("drug_name")
    analysis_period = req.get("analysis_period")
    def run():
        try: analyze_signal(drug_name, analysis_period)
        except Exception as e: print(f"Signal analysis error: {e}")
    threading.Thread(target=run, daemon=True).start()
    return {"code": 200, "message": "success",
            "data": {"task_id": f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}", "status": "running", "estimated_time": 30},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}

@router.get("/dashboard")
def get_dashboard():
    with get_db() as conn:
        total = execute_query(conn, "SELECT COUNT(*) as cnt FROM signals")[0]["cnt"]
    trend = [{"month": "2025-03", "count": 1}, {"month": "2025-04", "count": 2}, {"month": "2025-05", "count": 3}]
    by_soc = [{"soc_name": "肝胆系统疾病", "count": 5}, {"soc_name": "呼吸系统疾病", "count": 3}]
    return {"code": 200, "message": "success",
            "data": {"total_signals": total, "new_this_week": total, "by_soc": by_soc, "trend": trend},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}