"""User Service - 用户管理 CRUD"""

import hashlib
import uuid
from typing import Optional
from backend.core.database import get_db, execute_query, execute_insert


def _hash(password: str) -> str:
    """SHA-256 哈希（与现有 MOCK_USERS 兼容）"""
    return hashlib.sha256(password.encode()).hexdigest()


def get_user_by_username(username: str) -> Optional[dict]:
    """根据用户名查询用户"""
    with get_db() as conn:
        users = execute_query(
            conn, "SELECT * FROM users WHERE username = %s", (username,)
        )
    return users[0] if users else None


def get_user_by_id(user_id: str) -> Optional[dict]:
    """根据 ID 查询用户"""
    with get_db() as conn:
        users = execute_query(
            conn, "SELECT * FROM users WHERE user_id = %s", (user_id,)
        )
    return users[0] if users else None


def list_users(page: int = 1, page_size: int = 20,
               role: Optional[str] = None,
               keyword: Optional[str] = None) -> tuple:
    """分页查询用户列表"""
    conditions = []
    params = []
    if role:
        conditions.append("role = %s")
        params.append(role)
    if keyword:
        conditions.append("(username LIKE %s OR name LIKE %s)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    where = " AND ".join(conditions) if conditions else "1=1"
    offset = (page - 1) * page_size
    with get_db() as conn:
        total = execute_query(
            conn, f"SELECT COUNT(*) as cnt FROM users WHERE {where}", params
        )[0]["cnt"]
        items = execute_query(
            conn, f"SELECT * FROM users WHERE {where} ORDER BY created_at DESC LIMIT {page_size} OFFSET {offset}",
            params
        )
    return items, total


def create_user(username: str, password: str, name: str,
                role: str = "cra", email: str = "", phone: str = "") -> str:
    """创建新用户，返回 user_id"""
    user_id = f"USR-{uuid.uuid4().hex[:8].upper()}"
    password_hash = _hash(password)
    with get_db() as conn:
        execute_insert(conn, """
            INSERT INTO users (user_id, username, password_hash, name, role, email, phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, username, password_hash, name, role, email, phone))
    return user_id


def update_user(user_id: str, **kwargs) -> bool:
    """更新用户字段（只更新提供的字段）"""
    allowed = {"name", "role", "email", "phone", "is_active"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False
    set_clause = ", ".join(f"{k} = %s" for k in updates)
    params = list(updates.values()) + [user_id]
    with get_db() as conn:
        execute_insert(conn,
                       f"UPDATE users SET {set_clause} WHERE user_id = %s",
                       params)
    return True


def delete_user(user_id: str) -> bool:
    """删除用户"""
    with get_db() as conn:
        execute_insert(conn, "DELETE FROM users WHERE user_id = %s", (user_id,))
    return True


def change_password(user_id: str, new_password: str) -> bool:
    """修改用户密码"""
    password_hash = _hash(new_password)
    with get_db() as conn:
        execute_insert(conn,
                       "UPDATE users SET password_hash = %s WHERE user_id = %s",
                       (password_hash, user_id))
    return True
