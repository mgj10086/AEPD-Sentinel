"""Deviation Agent - 方案偏离识别与预警 + 自动检测"""
from datetime import datetime
from typing import Optional
from backend.core.database import get_db, execute_insert


def generate_deviation_id():
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"DEV-{ts}-{random.randint(100, 999)}"


def check_visit_window(scheduled_date_str: str, actual_date_str: str, window_days: int = 3) -> Optional[dict]:
    """检查访视窗口是否超窗"""
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


def check_missing_tests(required_tests: list, completed_tests: list) -> Optional[dict]:
    """检查是否有必做检查缺失"""
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


def check_visit_compliance(scheduled_date_str: str, actual_date_str: Optional[str] = None) -> Optional[dict]:
    """检查访视是否完全未做"""
    if not actual_date_str and scheduled_date_str < datetime.now().strftime("%Y-%m-%d"):
        return {
            "deviation_id": generate_deviation_id(), "deviation_type": "访视未做",
            "rule_id": "PD-002", "severity": "major",
            "description": f"计划访视日期{scheduled_date_str}，但未找到实际访视记录",
            "action": "alert_cra", "status": "open"
        }
    return None


def process_patient_visit(patient_id: str, visit_date: str, drug_name: str,
                          scheduled_visit_date: Optional[str] = None) -> list:
    """
    综合偏离检测：对一次访视执行所有规则检查
    返回检测到的偏离列表
    """
    deviations = []

    # PD-001: 访视超窗
    if scheduled_visit_date:
        result = check_visit_window(scheduled_visit_date, visit_date)
        if result:
            deviations.append(result)
            save_deviation(result, patient_id)

    # PD-002: 访视未做（如果计划日期已过但没有实际访视记录）
    if scheduled_visit_date:
        result = check_visit_compliance(scheduled_visit_date, visit_date)
        if result:
            deviations.append(result)
            save_deviation(result, patient_id)

    # PD-003: 用药依从性不足（需actual_dose数据，当前版本暂不自动检测）
    # 客户接入实际用药数据后，将此注释替换为基于 actual_dose < expected_dose * 0.8 的真实判断逻辑
    pass

    return deviations


def save_deviation(deviation: dict, patient_id: str, visit_id: str = None):
    """持久化偏离记录到数据库"""
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