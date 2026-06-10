"""Audit Service - 审计日志写入"""
import uuid
import json
from datetime import datetime
from backend.core.database import get_db, execute_insert
from backend.core.config import SECRET_KEY, ALGORITHM


def generate_log_id():
    """生成审计日志唯一ID"""
    return f"AUD-{uuid.uuid4().hex[:12].upper()}"


def extract_username_from_token(authorization: str) -> str:
    """从 Authorization Bearer token 中提取用户名"""
    if not authorization:
        return "anonymous"
    try:
        token = authorization.replace("Bearer ", "").strip()
        import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub", "unknown")
    except Exception:
        return "anonymous"


def write_audit_log(user_id: str, agent_type: str, action: str,
                    resource_id: str = "", detail: str = ""):
    """写入审计日志到 audit_logs 表"""
    log_id = generate_log_id()
    try:
        with get_db() as conn:
            execute_insert(conn, """
                INSERT INTO audit_logs (log_id, user_id, agent_type, action,
                    resource_id, detail, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                log_id, user_id, agent_type, action,
                resource_id, detail,
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            ))
    except Exception as e:
        print(f"Audit log write error: {e}")
