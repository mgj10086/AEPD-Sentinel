"""AE Router - 不良事件编码接口"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime
import json
import sys, os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.core.database import get_db, execute_query, execute_insert
from backend.agents.ae_coder import process_ae

router = APIRouter(prefix="/api/ae", tags=["AE编码"])

@router.post("/process")
def process_single_ae(req: dict):
    ae_text = req.get("ae_text", "").strip()
    if not ae_text:
        raise HTTPException(status_code=400, detail={"code": 10001, "message": "AE文本为空"})
    for key in ['visit_id', 'onset_date', 'end_date', 'reporter']:
        if key not in req:
            req[key] = None
    result = process_ae(type('obj', (object,), req)())
    return {"code": 200, "message": "success", "data": result,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}

@router.post("/batch")
def process_batch_ae(req: dict):
    ae_list = req.get("ae_list", [])
    results = []
    success_count = 0
    fail_count = 0
    for item in ae_list:
        try:
            for key in ['visit_id', 'onset_date', 'end_date', 'reporter']:
                if key not in item:
                    item[key] = None
            result = process_ae(type('obj', (object,), item)())
            results.append(result)
            success_count += 1
        except Exception as e:
            fail_count += 1
            results.append({"error": str(e)})
    return {"code": 200, "message": "success",
            "data": {"results": results, "success_count": success_count, "fail_count": fail_count, "total_count": len(ae_list)},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}

@router.get("/results")
def get_ae_results(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    patient_id: Optional[str] = Query(None), sae_flag: Optional[bool] = Query(None),
    date_from: Optional[str] = Query(None), date_to: Optional[str] = Query(None)):
    conditions = []
    params = []
    if patient_id:
        conditions.append("patient_id = ?"); params.append(patient_id)
    if sae_flag is not None:
        conditions.append("sae_flag = ?"); params.append(1 if sae_flag else 0)
    if date_from:
        conditions.append("visit_date >= ?"); params.append(date_from)
    if date_to:
        conditions.append("visit_date <= ?"); params.append(date_to)
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    with get_db() as conn:
        total_result = execute_query(conn, f"SELECT COUNT(*) as cnt FROM ae_results WHERE {where_clause}", params)
        total = total_result[0]["cnt"]
        offset = (page - 1) * page_size
        items = execute_query(conn, f"SELECT * FROM ae_results WHERE {where_clause} ORDER BY created_at DESC LIMIT {page_size} OFFSET {offset}", params)
        for item in items:
            if item.get("meddra_codes"):
                item["meddra_codes"] = json.loads(item["meddra_codes"])
            if item.get("sae_criteria"):
                item["sae_criteria"] = json.loads(item["sae_criteria"])
            if item.get("citations"):
                item["citations"] = json.loads(item["citations"])
    return {"code": 200, "message": "success",
            "data": {"items": items, "total": total, "page": page, "page_size": page_size},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}

@router.get("/results/{ae_id}")
def get_ae_detail(ae_id: str):
    with get_db() as conn:
        results = execute_query(conn, "SELECT * FROM ae_results WHERE ae_id = ?", (ae_id,))
    if not results:
        raise HTTPException(status_code=404, detail="AE记录不存在")
    item = results[0]
    if item.get("meddra_codes"):
        item["meddra_codes"] = json.loads(item["meddra_codes"])
    if item.get("sae_criteria"):
        item["sae_criteria"] = json.loads(item["sae_criteria"])
    if item.get("citations"):
        item["citations"] = json.loads(item["citations"])
    return {"code": 200, "message": "success", "data": item,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}