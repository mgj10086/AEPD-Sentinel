"""SAE Report Agent - SAE报告自动生成"""
import json
import random
from datetime import datetime, timedelta
from backend.core.database import get_db, execute_query, execute_insert
from backend.core.config import TRIAL_NAME, TRIAL_DRUG, TRIAL_INDICATION


def generate_report_id():
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"SAE-{ts}-{random.randint(100, 999)}"


def generate_cioms_fields(ae_record: dict) -> dict:
    meddra_codes = ae_record.get("meddra_codes", [])
    if isinstance(meddra_codes, str):
        meddra_codes = json.loads(meddra_codes)
    pt_name = meddra_codes[0]["pt_name"] if meddra_codes else "未知"
    end_date = ae_record.get("end_date", "")
    if end_date and end_date != "持续中":
        outcome = "recovered"
    elif "死亡" in (ae_record.get("ae_text") or ""):
        outcome = "fatal"
    else:
        outcome = "ongoing"
    onset_date_str = ae_record.get("onset_date") or ae_record.get("visit_date")
    if onset_date_str:
        try:
            onset_date = datetime.strptime(str(onset_date_str), "%Y-%m-%d")
            deadline = onset_date + timedelta(days=7)
            deadline_str = deadline.strftime("%Y-%m-%dT%H:%M:%SZ")
        except:
            deadline_str = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        deadline_str = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    narrative = f"患者{ae_record.get('patient_id', '未知')}在使用{ae_record.get('drug_name', '试验药物')}期间"
    narrative += f"于{onset_date_str}出现{pt_name}。"
    narrative += f"AE原始描述：{ae_record.get('ae_text', '')}。"
    if ae_record.get("severity") == "severe":
        narrative += "该事件判定为严重不良事件。"
    return {
        "patient_initials": ae_record.get("patient_id", "UNK")[:3],
        "patient_dob": ae_record.get("patient_dob", "") or "",
        "patient_gender": ae_record.get("patient_gender", "") or "",
        "ae_description": ae_record.get("ae_text", ""),
        "ae_start_date": onset_date_str or "",
        "ae_end_date": end_date if isinstance(end_date, str) else "",
        "ae_serious": True, "ae_outcome": outcome,
        "suspect_drug_name": ae_record.get("drug_name", TRIAL_DRUG),
        "suspect_drug_dose": "",
        "suspect_drug_dates": f"{onset_date_str} - {end_date if isinstance(end_date, str) else 'ongoing'}",
        "concomitant_drugs": [], "reporter_qualification": "Physician",
        "study_number": TRIAL_NAME, "sponsor": "申办方", "narrative": narrative,
        "causality_method": "WHO-UMC Causality Assessment",
        "causality_score": ae_record.get("causality_tentative", "possible"),
        "dechallenge": "Not applicable", "rechallenge": "Not applicable",
        "_deadline": deadline_str,
        "_deadline_24h": (datetime.strptime(str(onset_date_str), "%Y-%m-%d") + timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ") if onset_date_str else ""
    }


def generate_sae_report(ae_id: str, reporter_name: str, reporter_org: str) -> dict:
    with get_db() as conn:
        results = execute_query(conn, "SELECT * FROM ae_results WHERE ae_id = %s", (ae_id,))
        if not results:
            raise ValueError(f"AE record {ae_id} not found")
        ae_record = results[0]
    cioms = generate_cioms_fields(ae_record)
    deadline = cioms.pop("_deadline")
    causality = ae_record.get("causality_tentative", "possible")
    meddra_codes = ae_record.get("meddra_codes", [])
    if isinstance(meddra_codes, str):
        meddra_codes = json.loads(meddra_codes)
    pt_name = meddra_codes[0]["pt_name"] if meddra_codes else ""
    similar_drug_info = f"针对{pt_name}，同类PD-1/PD-L1抑制剂（如帕博利珠单抗、纳武利尤单抗）"
    similar_drug_info += f"已知存在类似不良反应信号，发生率约1-5%。"
    similar_drug_info += f"建议参考最新研究者手册(IB)第4.8节。"
    report_id = generate_report_id()
    try:
        with get_db() as conn:
            execute_insert(conn, """
                INSERT INTO sae_reports (report_id, ae_id, cioms_fields, causality_assessment,
                    similar_drug_safety, report_status, deadline)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                report_id, ae_id, json.dumps(cioms, ensure_ascii=False),
                causality, similar_drug_info, "draft", deadline
            ))
    except Exception as e:
        print(f"DB save error: {e}")
    return {
        "report_id": report_id, "ae_id": ae_id, "cioms_fields": cioms,
        "causality_assessment": causality, "similar_drug_safety": similar_drug_info,
        "report_status": "draft",
        "created_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "deadline": deadline
    }
