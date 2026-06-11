"""Audit Service - 审计日志写入（含 HMAC 哈希链防篡改）"""
import uuid
import json
import hmac
import hashlib
from datetime import datetime
from backend.core.database import get_db, execute_insert, execute_query
from backend.core.config import SECRET_KEY, ALGORITHM, AUDIT_HMAC_KEY


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


def _compute_hmac(prev_hmac: str, fields: str) -> str:
    """HMAC-SHA256(secret, prev_hmac + fields)"""
    data = (prev_hmac or "") + fields
    return hmac.new(
        AUDIT_HMAC_KEY.encode(), data.encode(), hashlib.sha256
    ).hexdigest()


def _get_last_log(conn):
    """获取最后一个审计日志（用于哈希链）"""
    rows = execute_query(
        conn,
        "SELECT log_id, hmac FROM audit_logs ORDER BY created_at DESC, log_id DESC LIMIT 1"
    )
    return rows[0] if rows else None


def write_audit_log(user_id: str, agent_type: str, action: str,
                    resource_id: str = "", detail: str = ""):
    """写入审计日志到 audit_logs 表（含 HMAC 哈希链）"""
    log_id = generate_log_id()
    try:
        with get_db() as conn:
            last = _get_last_log(conn)
            prev_log_id = last["log_id"] if last else None
            prev_hmac = last["hmac"] if last else None
            created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            # 计算 HMAC: hash(prev_hmac + log_id + user_id + agent_type + action + resource_id + detail + created_at)
            fields = f"{log_id}{user_id}{agent_type}{action}{resource_id}{detail}{created_at}"
            curr_hmac = _compute_hmac(prev_hmac, fields)

            execute_insert(conn, """
                INSERT INTO audit_logs (log_id, user_id, agent_type, action,
                    resource_id, detail, created_at, prev_log_id, prev_hmac, hmac)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                log_id, user_id, agent_type, action,
                resource_id, detail, created_at,
                prev_log_id, prev_hmac, curr_hmac
            ))
    except Exception as e:
        print(f"Audit log write error: {e}")
