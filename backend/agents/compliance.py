"""Compliance Agent - 合规与质控"""
import json
from datetime import datetime, timedelta
from backend.core.database import get_db, execute_query


def check_sae_timeliness() -> list:
    with get_db() as conn:
        results = execute_query(conn, """
            SELECT sr.report_id, sr.ae_id, sr.cioms_fields, sr.report_status, sr.deadline,
                   ar.patient_id, ar.visit_date, ar.onset_date
            FROM sae_reports sr JOIN ae_results ar ON sr.ae_id = ar.ae_id
            WHERE sr.report_status != 'submitted'
        """)
    timeliness = []
    now = datetime.now()
    for r in results:
        deadline_str = r.get("deadline")
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, "%Y-%m-%dT%H:%M:%SZ")
                days_remaining = (deadline - now).days
                onset = r.get("onset_date") or r.get("visit_date") or ""
                if days_remaining < 0:
                    status = "overdue"
                elif days_remaining <= 2:
                    status = "urgent"
                else:
                    status = "normal"
                deadline_7 = ""
                deadline_15 = ""
                if onset:
                    try:
                        onset_dt = datetime.strptime(str(onset), "%Y-%m-%d")
                        deadline_7 = (onset_dt + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
                        deadline_15 = (onset_dt + timedelta(days=15)).strftime("%Y-%m-%dT%H:%M:%SZ")
                    except:
                        pass
                timeliness.append({
                    "report_id": r["report_id"], "patient_id": r.get("patient_id", ""),
                    "ae_start_date": str(onset) if onset else "",
                    "deadline_7day": deadline_7, "deadline_15day": deadline_15,
                    "days_remaining": days_remaining, "status": status
                })
            except:
                pass
    return timeliness


def check_field_completeness() -> list:
    with get_db() as conn:
        results = execute_query(conn, "SELECT report_id, cioms_fields FROM sae_reports")
    required_fields = [
        "patient_initials", "ae_description", "ae_start_date", "ae_serious",
        "suspect_drug_name", "reporter_qualification", "study_number",
        "sponsor", "narrative", "causality_method"
    ]
    completeness = []
    for r in results:
        cioms = json.loads(r["cioms_fields"]) if r.get("cioms_fields") else {}
        missing = [f for f in required_fields if not cioms.get(f)]
        completeness.append({
            "report_id": r["report_id"], "missing_fields": missing,
            "complete": len(missing) == 0
        })
    return completeness


def get_compliance_report(period: str = "weekly") -> dict:
    timeliness = check_sae_timeliness()
    completeness = check_field_completeness()
    total_reports = len(timeliness)
    on_time = sum(1 for t in timeliness if t["status"] != "overdue")
    timeliness_score = on_time / total_reports if total_reports > 0 else 1.0
    complete_reports = sum(1 for c in completeness if c["complete"])
    completeness_score = complete_reports / total_reports if total_reports > 0 else 1.0
    overall_score = round((timeliness_score * 0.5 + completeness_score * 0.5), 2)
    issues = []
    for t in timeliness:
        if t["status"] == "overdue":
            issues.append(f"报告{t['report_id']}已超期")
        elif t["status"] == "urgent":
            issues.append(f"报告{t['report_id']}即将超期(剩余{t['days_remaining']}天)")
    for c in completeness:
        if not c["complete"]:
            issues.append(f"报告{c['report_id']}缺失字段: {', '.join(c['missing_fields'])}")
    return {
        "sae_timeliness": timeliness, "field_completeness": completeness,
        "timeliness_score": round(timeliness_score, 2), "completeness_score": round(completeness_score, 2),
        "meddra_consistency": [], "overall_score": overall_score, "issues": issues
    }
