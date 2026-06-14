"""Deviation Agent - 方案偏离识别与预警 + 自动检测

实现 7 条方案偏离规则（PD-001 ~ PD-007）：
  PD-001  访视超窗 — 实际访视日期超出计划窗口 ±3天
  PD-002  访视未做 — 计划访视日期已过但无实际访视记录
  PD-003  用药依从性不足 — 实际剂量 < 预期剂量的80%
  PD-004  禁止合并用药 — 患者使用了试验方案禁止的合并药物
  PD-005  计划检查未完成 — 必做安全性检查缺失
  PD-006  入组标准不符合 — 患者不满足试验入组条件
  PD-007  排除标准违反 — 患者存在应被排除的条件
"""
import random
from datetime import datetime
from typing import Optional, List


def generate_deviation_id():
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"DEV-{ts}-{random.randint(100, 999)}"


# ═══════════════════════════════════════════════════════════════
# PD-001: 访视超窗检查
# ═══════════════════════════════════════════════════════════════
def check_visit_window(scheduled_date_str: str, actual_date_str: str, window_days: int = 3) -> Optional[dict]:
    """检查访视日期是否超出允许窗口。默认 ±3 天，超出则触发 major 偏离。"""
    try:
        scheduled = datetime.strptime(scheduled_date_str, "%Y-%m-%d")
        actual = datetime.strptime(actual_date_str, "%Y-%m-%d")
        diff = abs((actual - scheduled).days)
        if diff > window_days:
            return {
                "deviation_id": generate_deviation_id(), "deviation_type": "访视超窗",
                "rule_id": "PD-001", "severity": "major",
                "description": f"访视实际日期{actual_date_str}，超出计划日期{scheduled_date_str}达{diff}天，超出允许窗口±{window_days}天",
                "action": "alert_cra", "status": "open"
            }
    except:
        pass
    return None


# ═══════════════════════════════════════════════════════════════
# PD-002: 访视未做检查
# ═══════════════════════════════════════════════════════════════
def check_visit_compliance(scheduled_date_str: str, actual_date_str: Optional[str] = None) -> Optional[dict]:
    """检查计划访视是否完全未执行。计划日期已过且无实际记录 → major。"""
    if not actual_date_str and scheduled_date_str < datetime.now().strftime("%Y-%m-%d"):
        return {
            "deviation_id": generate_deviation_id(), "deviation_type": "访视未做",
            "rule_id": "PD-002", "severity": "major",
            "description": f"计划访视日期{scheduled_date_str}，但未找到实际访视记录",
            "action": "alert_cra", "status": "open"
        }
    return None


# ═══════════════════════════════════════════════════════════════
# PD-003: 用药依从性检查
# ═══════════════════════════════════════════════════════════════
def check_medication_compliance(actual_dose: Optional[float], expected_dose: float,
                                drug_name: str = "", visit_date: str = "") -> Optional[dict]:
    """检查患者用药依从性。实际剂量不足预期80% → major 偏离。

    参数:
        actual_dose: 患者实际服用的剂量(mg)，None 表示无用药记录
        expected_dose: 方案规定的预期剂量(mg)
        drug_name: 药物名称（用于描述）
        visit_date: 访视日期（用于描述）
    """
    if actual_dose is None:
        # 无用药记录也是一种依从性不足
        return {
            "deviation_id": generate_deviation_id(), "deviation_type": "用药依从性不足",
            "rule_id": "PD-003", "severity": "major",
            "description": f"{visit_date} 访视：{drug_name} 无用药记录，无法评估依从性",
            "action": "alert_cra", "status": "open"
        }
    if expected_dose > 0 and actual_dose < expected_dose * 0.8:
        ratio = actual_dose / expected_dose * 100
        return {
            "deviation_id": generate_deviation_id(), "deviation_type": "用药依从性不足",
            "rule_id": "PD-003", "severity": "major",
            "description": f"{visit_date} 访视：{drug_name} 实际剂量 {actual_dose}mg，仅为预期剂量 {expected_dose}mg 的 {ratio:.0f}%，低于80%阈值",
            "action": "alert_cra", "status": "open"
        }
    return None


# ═══════════════════════════════════════════════════════════════
# PD-004: 禁止合并用药检查
# ═══════════════════════════════════════════════════════════════
def check_prohibited_drugs(concomitant_drugs: Optional[List[str]] = None,
                           prohibited_drugs: Optional[List[str]] = None,
                           patient_id: str = "") -> Optional[dict]:
    """检查患者是否使用了试验方案禁止的合并用药。

    参数:
        concomitant_drugs: 患者正在使用的合并用药列表
        prohibited_drugs: 试验方案禁止使用的药物列表（默认包含常见CYP诱导剂/免疫抑制剂等）
        patient_id: 患者编号
    """
    if not concomitant_drugs:
        return None
    if prohibited_drugs is None:
        # 默认禁止药物列表（临床试验常见禁止合并用药）
        prohibited_drugs = [
            "利福平", "卡马西平", "苯妥英", "圣约翰草",  # CYP3A4 强诱导剂
            "酮康唑", "伊曲康唑", "克拉霉素",            # CYP3A4 强抑制剂
            "环孢素", "他克莫司", "西罗莫司",            # 免疫抑制剂（抗肿瘤试验）
            "华法林", "阿哌沙班", "利伐沙班",            # 抗凝药（出血风险）
            "甲氨蝶呤", "环磷酰胺",                       # 其他化疗药（单药试验）
        ]
    violated = [d for d in concomitant_drugs if any(p in d for p in prohibited_drugs)]
    if violated:
        return {
            "deviation_id": generate_deviation_id(), "deviation_type": "禁止合并用药",
            "rule_id": "PD-004", "severity": "major",
            "description": f"患者 {patient_id} 使用了禁止合并用药: {', '.join(violated)}，违反试验方案合并用药规定",
            "action": "alert_cra", "status": "open"
        }
    return None


# ═══════════════════════════════════════════════════════════════
# PD-005: 计划安全性检查缺失
# ═══════════════════════════════════════════════════════════════
def check_missing_tests(required_tests: list, completed_tests: list) -> Optional[dict]:
    """检查访视要求的必做安全性检查是否全部完成。涉及肝/心/安全的缺失 → major。"""
    missing = [t for t in required_tests if t not in completed_tests]
    if missing:
        is_critical = any("肝" in t or "心" in t or "安全" in t for t in missing)
        return {
            "deviation_id": generate_deviation_id(), "deviation_type": "检查缺失",
            "rule_id": "PD-005", "severity": "major" if is_critical else "minor",
            "description": f"访视缺失{', '.join(missing)}检查",
            "action": "alert_cra", "status": "open", "missing_tests": missing
        }
    return None


# ═══════════════════════════════════════════════════════════════
# PD-006: 入组标准不符合检查
# ═══════════════════════════════════════════════════════════════
def check_inclusion_criteria(inclusion_met: Optional[bool] = None,
                             patient_id: str = "",
                             failed_criteria: Optional[List[str]] = None) -> Optional[dict]:
    """检查患者是否满足试验入组标准。

    参数:
        inclusion_met: 是否满足入组标准（None = 未评估，False = 不满足）
        patient_id: 患者编号
        failed_criteria: 不满足的具体入组标准描述列表
    """
    if inclusion_met is False:
        detail = f"患者 {patient_id} 不满足入组标准"
        if failed_criteria:
            detail += f": {', '.join(failed_criteria)}"
        return {
            "deviation_id": generate_deviation_id(), "deviation_type": "入组标准不符合",
            "rule_id": "PD-006", "severity": "major",
            "description": detail,
            "action": "alert_cra", "status": "open"
        }
    return None


# ═══════════════════════════════════════════════════════════════
# PD-007: 排除标准违反检查
# ═══════════════════════════════════════════════════════════════
def check_exclusion_criteria(exclusion_met: Optional[bool] = None,
                             patient_id: str = "",
                             triggered_criteria: Optional[List[str]] = None) -> Optional[dict]:
    """检查患者是否存在应被排除的条件。

    参数:
        exclusion_met: 是否触发了排除标准（True = 存在应排除的条件，应触发偏离）
        patient_id: 患者编号
        triggered_criteria: 触发的排除标准描述列表
    """
    if exclusion_met is True:
        detail = f"患者 {patient_id} 存在应被排除的条件"
        if triggered_criteria:
            detail += f": {', '.join(triggered_criteria)}"
        return {
            "deviation_id": generate_deviation_id(), "deviation_type": "排除标准违反",
            "rule_id": "PD-007", "severity": "major",
            "description": detail,
            "action": "alert_cra", "status": "open"
        }
    return None


# ═══════════════════════════════════════════════════════════════
# 综合偏离检测入口
# ═══════════════════════════════════════════════════════════════
def process_patient_visit(patient_id: str, visit_date: str, drug_name: str,
                          scheduled_visit_date: Optional[str] = None,
                          actual_dose: Optional[float] = None,
                          expected_dose: Optional[float] = None,
                          concomitant_drugs: Optional[List[str]] = None,
                          required_tests: Optional[List[str]] = None,
                          completed_tests: Optional[List[str]] = None,
                          inclusion_met: Optional[bool] = None,
                          exclusion_met: Optional[bool] = None) -> list:
    """
    综合偏离检测：对一次患者访视执行全部 7 条规则检查。
    返回检测到的偏离列表，同时自动持久化到数据库。

    参数:
        patient_id          患者编号（必填）
        visit_date          实际访视日期（必填）
        drug_name           药物名称（必填）
        scheduled_visit_date 计划访视日期，用于 PD-001/PD-002
        actual_dose         实际用药剂量(mg)，用于 PD-003
        expected_dose       预期用药剂量(mg)，用于 PD-003
        concomitant_drugs   合并用药列表，用于 PD-004
        required_tests      必做检查列表，用于 PD-005
        completed_tests     已完成检查列表，用于 PD-005
        inclusion_met       是否满足入组标准，用于 PD-006
        exclusion_met       是否触发排除标准，用于 PD-007
    """
    deviations = []

    # PD-001: 访视超窗
    if scheduled_visit_date:
        result = check_visit_window(scheduled_visit_date, visit_date)
        if result:
            deviations.append(result)

    # PD-002: 访视未做（计划日期已过但无实际记录）
    if scheduled_visit_date:
        result = check_visit_compliance(scheduled_visit_date, visit_date)
        if result:
            deviations.append(result)

    # PD-003: 用药依从性不足
    if expected_dose is not None and expected_dose > 0:
        result = check_medication_compliance(
            actual_dose, expected_dose, drug_name, visit_date)
        if result:
            deviations.append(result)

    # PD-004: 禁止合并用药
    if concomitant_drugs:
        result = check_prohibited_drugs(concomitant_drugs, patient_id=patient_id)
        if result:
            deviations.append(result)

    # PD-005: 计划安全性检查缺失
    if required_tests:
        result = check_missing_tests(required_tests, completed_tests or [])
        if result:
            deviations.append(result)

    # PD-006: 入组标准不符合
    if inclusion_met is not None:
        result = check_inclusion_criteria(inclusion_met, patient_id)
        if result:
            deviations.append(result)

    # PD-007: 排除标准违反
    if exclusion_met is not None:
        result = check_exclusion_criteria(exclusion_met, patient_id)
        if result:
            deviations.append(result)

    # 批量持久化
    for d in deviations:
        save_deviation(d, patient_id)

    return deviations


def save_deviation(deviation: dict, patient_id: str, visit_id: str = None):
    """持久化偏离记录到数据库，并自动触发通知。"""
    try:
        with get_db() as conn:
            execute_insert(conn, """
                INSERT INTO deviations (deviation_id, patient_id, visit_id, rule_id,
                    deviation_type, severity, description, action, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                deviation["deviation_id"], patient_id, visit_id,
                deviation.get("rule_id", ""), deviation["deviation_type"],
                deviation["severity"], deviation["description"],
                deviation["action"], deviation["status"]
            ))
        # P2: 对 alert_cra 类型的偏离自动产生通知
        if deviation.get("action") == "alert_cra":
            try:
                from backend.services.notification_service import create_notification
                create_notification(
                    user_id="cra_user",
                    title=f"新方案偏离: {deviation.get('deviation_type', '')}",
                    message=deviation.get("description", "")[:200],
                    notification_type="alert",
                    resource_type="deviation",
                    resource_id=deviation["deviation_id"]
                )
            except Exception as notif_e:
                print(f"Deviation notification error: {notif_e}")
        return True
    except Exception as e:
        print(f"DB save deviation error: {e}")
        return False


# 保持向后兼容 — 模块级 get_db / execute_insert 引用
from backend.core.database import get_db, execute_insert
