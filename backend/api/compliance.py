"""Compliance Router - 合规质控接口"""
from fastapi import APIRouter, Query
from datetime import datetime
import sys, os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from core.database import get_db, execute_query
from agents.compliance import get_compliance_report, check_sae_timeliness

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