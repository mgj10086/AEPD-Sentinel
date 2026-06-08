"""Deviation Agent - 方案偏离识别与预警"""
import random
from datetime import datetime
from core.database import get_db, execute_insert


def generate_deviation_id():
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"DEV-{ts}-{random.randint(100, 999)}"


def check_visit_window(scheduled_date_str: str, actual_date_str: str, window_days: int = 3) -> dict:
    try:
        scheduled = datetime.strptime(scheduled_date_str, "%Y-%m-%d")
        actual = datetime.strptime(actual_date_str, "%Y-%m-%d")
        diff = abs((actual - scheduled).days)
        if diff > window_days:
            return {
                "deviation_id": generate_deviation_id(), "deviation_type": "访视超窗",
                "rule_id": "PD-001", "severity": "major",
                "description": f"访视实际日期{actual_date_str}，超出计划日期{scheduled_date_str}达{diff}天，超出允许窗口±{window_days}天",
                "action": "alert_cra", "status": "pending"
            }
    except:
        pass
    return None


def check_missing_tests(required_tests: list, completed_tests: list) -> dict:
    missing = [t for t in required_tests if t not in completed_tests]
    if missing:
        is_critical = any("肝" in t or "心" in t or "安全" in t for t in missing)
        return {
            "deviation_id": generate_deviation_id(), "deviation_type": "检查缺失",
            "rule_id": "PD-005", "severity": "major" if is_critical else "minor",
            "description": f"访视缺失{', '.join(missing)}检查",
            "action": "alert_cra", "status": "pending", "missing_tests": missing
        }
    return None


def save_deviation(deviation: dict, patient_id: str, visit_id: str = None):
    try:
        with get_db() as conn:
            execute_insert(conn, """
                INSERT INTO deviations (deviation_id, patient_id, visit_id, rule_id,
                    deviation_type, severity, description, action, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                deviation["deviation_id"], patient_id, visit_id,
                deviation.get("rule_id", ""), deviation["deviation_type"],
                deviation["severity"], deviation["description"],
                deviation["action"], deviation["status"]
            ))
    except Exception as e:
        print(f"DB save deviation error: {e}")
