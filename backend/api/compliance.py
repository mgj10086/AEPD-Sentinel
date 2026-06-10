"""Compliance Router - 合规质控接口"""
from fastapi import APIRouter, Query
from datetime import datetime

from backend.core.database import get_db, execute_query
from backend.agents.compliance import get_compliance_report, check_sae_timeliness

router = APIRouter(prefix="/api/compliance", tags=["合规质控"])

@router.get("/report")
def get_compliance_report_endpoint(period: str = Query("weekly"), date: str = Query(None)):
    report = get_compliance_report(period)
    return {"code": 200, "message": "success", "data": report,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}

@router.get("/sae-deadlines")
def get_sae_deadlines():
    timeliness = check_sae_timeliness()
    return {"code": 200, "message": "success", "data": timeliness,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}
