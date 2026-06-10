"""AE Agent - 不良事件编码与严重性初筛"""
import json
import time
import random
from datetime import datetime
from typing import List, Dict, Any
from backend.core.database import get_db, execute_query, execute_insert
from backend.core.config import EXPECTED_AES, TRIAL_DRUG
from backend.agents.deviation import process_patient_visit

MEDDRA_SYNONYMS = {
    "头痛": {"llt": "头痛", "llt_code": "10019211", "pt": "头痛", "pt_code": "10019211", "soc": "神经系统疾病", "soc_code": "10029205"},
    "头疼": {"llt": "头痛", "llt_code": "10019211", "pt": "头痛", "pt_code": "10019211", "soc": "神经系统疾病", "soc_code": "10029205"},
    "恶心": {"llt": "恶心", "llt_code": "10028813", "pt": "恶心", "pt_code": "10028813", "soc": "胃肠系统疾病", "soc_code": "10017947"},
    "反胃": {"llt": "恶心", "llt_code": "10028813", "pt": "恶心", "pt_code": "10028813", "soc": "胃肠系统疾病", "soc_code": "10017947"},
    "想吐": {"llt": "恶心", "llt_code": "10028813", "pt": "恶心", "pt_code": "10028813", "soc": "胃肠系统疾病", "soc_code": "10017947"},
    "呕吐": {"llt": "呕吐", "llt_code": "10047700", "pt": "呕吐", "pt_code": "10047700", "soc": "胃肠系统疾病", "soc_code": "10017947"},
    "食欲下降": {"llt": "食欲减退", "llt_code": "10003111", "pt": "食欲减退", "pt_code": "10003111", "soc": "胃肠系统疾病", "soc_code": "10017947"},
    "没胃口": {"llt": "食欲减退", "llt_code": "10003111", "pt": "食欲减退", "pt_code": "10003111", "soc": "胃肠系统疾病", "soc_code": "10017947"},
    "吃不下饭": {"llt": "食欲减退", "llt_code": "10003111", "pt": "食欲减退", "pt_code": "10003111", "soc": "胃肠系统疾病", "soc_code": "10017947"},
    "皮疹": {"llt": "皮疹", "llt_code": "10037844", "pt": "皮疹", "pt_code": "10037844", "soc": "皮肤及皮下组织类疾病", "soc_code": "10040785"},
    "斑丘疹": {"llt": "斑丘疹", "llt_code": "10025638", "pt": "斑丘疹", "pt_code": "10025638", "soc": "皮肤及皮下组织类疾病", "soc_code": "10040785"},
    "瘙痒": {"llt": "瘙痒", "llt_code": "10037481", "pt": "瘙痒", "pt_code": "10037481", "soc": "皮肤及皮下组织类疾病", "soc_code": "10040785"},
    "间质性肺病": {"llt": "间质性肺病", "llt_code": "10063871", "pt": "间质性肺病", "pt_code": "10063871", "soc": "呼吸系统、胸及纵隔疾病", "soc_code": "10038738"},
    "免疫相关肺炎": {"llt": "间质性肺病", "llt_code": "10063871", "pt": "间质性肺病", "pt_code": "10063871", "soc": "呼吸系统、胸及纵隔疾病", "soc_code": "10038738"},
    "气促": {"llt": "呼吸困难", "llt_code": "10013968", "pt": "呼吸困难", "pt_code": "10013968", "soc": "呼吸系统、胸及纵隔疾病", "soc_code": "10038738"},
    "咳嗽": {"llt": "咳嗽", "llt_code": "10011224", "pt": "咳嗽", "pt_code": "10011224", "soc": "呼吸系统、胸及纵隔疾病", "soc_code": "10038738"},
    "发热": {"llt": "发热", "llt_code": "10016558", "pt": "发热", "pt_code": "10016558", "soc": "全身性疾病及给药部位各种反应", "soc_code": "10018065"},
    "肺炎": {"llt": "肺炎", "llt_code": "10035664", "pt": "肺炎", "pt_code": "10035664", "soc": "感染及侵染类疾病", "soc_code": "10021871"},
    "肺部感染": {"llt": "肺部感染", "llt_code": "10035670", "pt": "肺炎", "pt_code": "10035664", "soc": "感染及侵染类疾病", "soc_code": "10021871"},
    "呼吸衰竭": {"llt": "呼吸衰竭", "llt_code": "10038781", "pt": "呼吸衰竭", "pt_code": "10038781", "soc": "呼吸系统、胸及纵隔疾病", "soc_code": "10038738"},
    "肝炎": {"llt": "肝炎", "llt_code": "10019851", "pt": "肝炎", "pt_code": "10019851", "soc": "肝胆系统疾病", "soc_code": "10019805"},
    "肝功能检查异常": {"llt": "肝功能检查异常", "llt_code": "10020858", "pt": "肝功能检查异常", "pt_code": "10020858", "soc": "肝胆系统疾病", "soc_code": "10019805"},
    "免疫相关肝炎": {"llt": "肝炎", "llt_code": "10019851", "pt": "肝炎", "pt_code": "10019851", "soc": "肝胆系统疾病", "soc_code": "10019805"},
    "疲乏": {"llt": "疲乏", "llt_code": "10046937", "pt": "疲乏", "pt_code": "10046937", "soc": "全身性疾病及给药部位各种反应", "soc_code": "10018065"},
    "输液反应": {"llt": "输液反应", "llt_code": "10043657", "pt": "输液反应", "pt_code": "10043657", "soc": "全身性疾病及给药部位各种反应", "soc_code": "10018065"},
    "贫血": {"llt": "贫血", "llt_code": "10002034", "pt": "贫血", "pt_code": "10002034", "soc": "血液及淋巴系统疾病", "soc_code": "10005329"},
    "血小板减少": {"llt": "血小板减少", "llt_code": "10043556", "pt": "血小板减少症", "pt_code": "10043556", "soc": "血液及淋巴系统疾病", "soc_code": "10005329"},
    "中性粒细胞减少": {"llt": "中性粒细胞减少", "llt_code": "10029354", "pt": "中性粒细胞减少症", "pt_code": "10029354", "soc": "血液及淋巴系统疾病", "soc_code": "10005329"},
}

SEVERITY_KEYWORDS = {
    "severe": ["住院", "收治", "危及生命", "死亡", "抢救", "严重", "重度", "5x", "5倍", "ULN", "ALT", "AST", "≥5"],
    "moderate": ["影响睡眠", "影响日常", "中度", "明显", "加重", "持续", "外用"],
    "mild": ["轻度", "轻微", "自行缓解", "未予特殊", "不适"]
}

SAE_CRITERIA_KEYWORDS = {
    "死亡": ["死亡", "抢救无效", "去世"],
    "危及生命": ["危及生命", "呼吸衰竭", "休克"],
    "导致住院": ["住院", "收治入院", "收治", "入院"],
    "残疾": ["残疾", "功能丧失"],
    "重要医学事件": ["ALT", "AST", "肝酶", "≥5", "5倍", "5x", "ULN", "肝炎", "免疫相关肝炎"]
}


def generate_ae_id():
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"AE-{ts}-{random.randint(100, 999)}"


def match_meddra(text: str) -> List[Dict[str, Any]]:
    results = []
    for keyword, mapping in MEDDRA_SYNONYMS.items():
        if keyword in text:
            confidence = 0.95 if keyword == mapping["llt"] else 0.88
            results.append({
                "llt_code": mapping["llt_code"], "llt_name": mapping["llt"],
                "pt_code": mapping["pt_code"], "pt_name": mapping["pt"],
                "soc_code": mapping["soc_code"], "soc_name": mapping["soc"],
                "confidence": confidence
            })
    seen = set()
    unique = []
    for r in results:
        if r["pt_name"] not in seen:
            seen.add(r["pt_name"])
            unique.append(r)
    return unique


def assess_severity(text: str) -> str:
    if any(kw in text for kw in SAE_CRITERIA_KEYWORDS.get("重要医学事件", [])):
        if "ALT" in text or "AST" in text:
            return "severe"
    if any(kw in text for kw in SAE_CRITERIA_KEYWORDS.get("死亡", [])):
        return "severe"
    if any(kw in text for kw in SAE_CRITERIA_KEYWORDS.get("导致住院", [])):
        return "severe"
    if any(kw in text for kw in SAE_CRITERIA_KEYWORDS.get("危及生命", [])):
        return "severe"
    if any(kw in text for kw in SEVERITY_KEYWORDS["severe"]):
        return "severe"
    if any(kw in text for kw in SEVERITY_KEYWORDS["moderate"]):
        return "moderate"
    if any(kw in text for kw in SEVERITY_KEYWORDS["mild"]):
        return "mild"
    return "mild"


def assess_sae(text: str) -> tuple:
    criteria = []
    for criterion, keywords in SAE_CRITERIA_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            criteria.append(criterion)
    return (len(criteria) > 0, criteria)


def check_expected(pt_name: str) -> bool:
    for expected in EXPECTED_AES:
        if expected in pt_name or pt_name in expected:
            return True
    return False


def assess_causality(text: str, drug_name: str, sae_flag: bool) -> str:
    if sae_flag and ("免疫相关" in text or "药物相关" in text):
        return "probable"
    if drug_name.lower() in text.lower():
        return "possible"
    return "possible"


def process_ae(req) -> Dict[str, Any]:
    start = time.time()
    codes = match_meddra(req.ae_text)
    if not codes:
        codes = [{
            "llt_code": "99999999", "llt_name": "其他症状",
            "pt_code": "99999999", "pt_name": "其他症状",
            "soc_code": "99999999", "soc_name": "各种检查", "confidence": 0.60
        }]
    severity = assess_severity(req.ae_text)
    sae_flag, sae_criteria = assess_sae(req.ae_text)
    expected_flag = any(check_expected(c["pt_name"]) for c in codes)
    causality = assess_causality(req.ae_text, req.drug_name, sae_flag)
    citations = []
    if expected_flag:
        citations.append(f"IB Section 4.8 - {TRIAL_DRUG}")
    citations.append("MedDRA v26.0")
    processing_time = int((time.time() - start) * 1000)
    ae_id = generate_ae_id()
    try:
        with get_db() as conn:
            execute_insert(conn, """
                INSERT INTO ae_results (ae_id, patient_id, visit_id, visit_date, ae_text, drug_name,
                    onset_date, end_date, reporter, meddra_codes, severity, sae_flag, sae_criteria,
                    expected_flag, causality_tentative, citations, processing_time_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                ae_id, req.patient_id, getattr(req, 'visit_id', None), req.visit_date,
                req.ae_text, req.drug_name, getattr(req, 'onset_date', None),
                getattr(req, 'end_date', None), getattr(req, 'reporter', None),
                json.dumps(codes, ensure_ascii=False), severity, sae_flag,
                json.dumps(sae_criteria, ensure_ascii=False), expected_flag,
                causality, json.dumps(citations, ensure_ascii=False), processing_time
            ))
    except Exception as e:
        print(f"DB save error: {e}")

    # Auto-detect deviations for this patient visit
    try:
        visit_date = getattr(req, 'visit_date', None)
        drug_name = getattr(req, 'drug_name', '')
        patient_id = req.patient_id
        if patient_id and visit_date:
            deviations = process_patient_visit(patient_id, visit_date, drug_name)
            if deviations:
                print(f"Detected {len(deviations)} deviation(s) for patient {patient_id}")
    except Exception as e:
        print(f"Deviation check error: {e}")

    return {
        "ae_id": ae_id, "meddra_codes": codes, "severity": severity,
        "sae_flag": sae_flag, "sae_criteria": sae_criteria,
        "expected_flag": expected_flag, "causality_tentative": causality,
        "citations": citations, "processing_time_ms": processing_time
    }
