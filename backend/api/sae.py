"""SAE Router - SAE报告接口"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime
import json
import sys, os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.core.database import get_db, execute_query, execute_insert
from backend.agents.sae_report import generate_sae_report
from backend.services.export_service import export_to_docx, export_to_json, export_to_pdf

router = APIRouter(prefix="/api/saereport", tags=["SAE报告"])

@router.post("/generate")
def generate_report(req: dict):
    ae_id = req.get("ae_id")
    reporter_name = req.get("reporter_name", "")
    reporter_org = req.get("reporter_org", "")
    try:
        result = generate_sae_report(ae_id, reporter_name, reporter_org)
        return {"code": 200, "message": "success", "data": result,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
def get_sae_list(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None), patient_id: Optional[str] = Query(None)):
    conditions, params = [], []
    if status:
        conditions.append("sr.report_status = ?"); params.append(status)
    if patient_id:
        conditions.append("ar.patient_id = ?"); params.append(patient_id)
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    offset = (page - 1) * page_size
    with get_db() as conn:
        total = execute_query(conn, f"SELECT COUNT(*) as cnt FROM sae_reports sr JOIN ae_results ar ON sr.ae_id = ar.ae_id WHERE {where_clause}", params)[0]["cnt"]
        items = execute_query(conn, f"SELECT sr.*, ar.patient_id, ar.ae_text FROM sae_reports sr JOIN ae_results ar ON sr.ae_id = ar.ae_id WHERE {where_clause} ORDER BY sr.created_at DESC LIMIT {page_size} OFFSET {offset}", params)
        for item in items:
            if item.get("cioms_fields"):
                item["cioms_fields"] = json.loads(item["cioms_fields"])
    return {"code": 200, "message": "success",
            "data": {"items": items, "total": total, "page": page, "page_size": page_size},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}

@router.get("/{report_id}")
def get_sae_detail(report_id: str):
    with get_db() as conn:
        results = execute_query(conn, "SELECT sr.*, ar.patient_id, ar.ae_text FROM sae_reports sr JOIN ae_results ar ON sr.ae_id = ar.ae_id WHERE sr.report_id = ?", (report_id,))
    if not results:
        raise HTTPException(status_code=404, detail="SAE报告不存在")
    item = results[0]
    if item.get("cioms_fields"):
        item["cioms_fields"] = json.loads(item["cioms_fields"])
    return {"code": 200, "message": "success", "data": item,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}

@router.put("/{report_id}")
def update_sae_report(report_id: str, req: dict):
    cioms_fields = req.get("cioms_fields")
    causality = req.get("causality_assessment")
    status = req.get("report_status")
    updates, params = [], []
    if cioms_fields:
        updates.append("cioms_fields = ?"); params.append(json.dumps(cioms_fields, ensure_ascii=False))
    if causality:
        updates.append("causality_assessment = ?"); params.append(causality)
    if status:
        updates.append("report_status = ?"); params.append(status)
    if not updates:
        raise HTTPException(status_code=400, detail="无更新字段")
    params.append(report_id)
    with get_db() as conn:
        execute_insert(conn, f"UPDATE sae_reports SET {', '.join(updates)} WHERE report_id = ?", params)
    return {"code": 200, "message": "updated", "data": {"report_id": report_id},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}

@router.post("/{report_id}/export")
def export_sae_report(report_id: str, format: str = Query("json")):
    with get_db() as conn:
        results = execute_query(conn, "SELECT sr.*, ar.patient_id, ar.ae_text FROM sae_reports sr JOIN ae_results ar ON sr.ae_id = ar.ae_id WHERE sr.report_id = ?", (report_id,))
    if not results:
        raise HTTPException(status_code=404, detail="SAE报告不存在")
    report = results[0]
    if report.get("cioms_fields"):
        report["cioms_fields"] = json.loads(report["cioms_fields"])
    if format == "docx":
        buffer = export_to_docx(report)
        from fastapi.responses import StreamingResponse
        return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={report_id}.docx"})
    elif format == "json":
        buffer = export_to_json(report)
        from fastapi.responses import StreamingResponse
        return StreamingResponse(buffer, media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={report_id}.json"})
    else:
        buffer = export_to_pdf(report)
        from fastapi.responses import StreamingResponse
        return StreamingResponse(buffer, media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={report_id}.pdf"})