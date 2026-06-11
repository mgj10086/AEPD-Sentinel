"""Admin Router - 管理接口（种子数据等）"""
from fastapi import APIRouter, Request
from datetime import datetime

from backend.agents.ae_coder import process_ae
from backend.services.audit_service import extract_username_from_token, write_audit_log

router = APIRouter(prefix="/api/admin", tags=["管理"])

# 模拟测试病例（从 Dashboard.vue 迁移到后端）
_MOCK_CASES = [
    {"ae_text": "患者出现头痛，轻度，自行缓解", "patient_id": "NSCLC-001", "visit_date": "2025-06-01", "drug_name": "XK-001"},
    {"ae_text": "患者出现恶心，持续约2小时，未予特殊处理", "patient_id": "NSCLC-002", "visit_date": "2025-06-02", "drug_name": "XK-001"},
    {"ae_text": "患者诉食欲下降，进食量减少约一半", "patient_id": "NSCLC-003", "visit_date": "2025-06-03", "drug_name": "XK-001"},
    {"ae_text": "患者出现皮疹，斑丘疹，外用激素软膏后缓解", "patient_id": "NSCLC-004", "visit_date": "2025-06-04", "drug_name": "XK-001"},
    {"ae_text": "患者出现免疫相关肺炎，CT显示间质性肺病，气促加重，收治入院", "patient_id": "NSCLC-005", "visit_date": "2025-06-05", "drug_name": "XK-001"},
    {"ae_text": "患者出现免疫相关肝炎，ALT 350 U/L（≥5×ULN），AST 280 U/L", "patient_id": "NSCLC-006", "visit_date": "2025-06-06", "drug_name": "XK-001"},
    {"ae_text": "患者出现疲乏，影响日常活动", "patient_id": "NSCLC-007", "visit_date": "2025-06-07", "drug_name": "XK-001"},
    {"ae_text": "患者出现发热，体温38.5°C", "patient_id": "NSCLC-008", "visit_date": "2025-06-08", "drug_name": "XK-001"},
    {"ae_text": "患者出现输液反应，寒战，轻度发热", "patient_id": "NSCLC-009", "visit_date": "2025-06-09", "drug_name": "XK-001"},
    {"ae_text": "患者出现肺炎，伴发热咳嗽，肺部感染，收入院治疗", "patient_id": "NSCLC-010", "visit_date": "2025-06-10", "drug_name": "XK-001"},
]


@router.post("/seed/mock-cases")
def seed_mock_cases(request: Request):
    """导入模拟测试病例"""
    user = extract_username_from_token(request.headers.get("Authorization", ""))
    results = []
    for item in _MOCK_CASES:
        try:
            result = process_ae(item)
            results.append(result)
        except Exception as e:
            results.append({"ae_text": item["ae_text"], "error": str(e)})
    write_audit_log(user, "admin", "seed", "mock-cases",
                    f"导入 {len(results)} 个模拟病例")
    return {"code": 200, "message": "success",
            "data": {"count": len(results), "results": results},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}
