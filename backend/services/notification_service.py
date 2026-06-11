"""Notification Service - 应用内通知写入与查询"""

import uuid
from datetime import datetime
from typing import Optional
from backend.core.database import get_db, execute_insert, execute_query


def _generate_notification_id() -> str:
    return f"NOTIF-{uuid.uuid4().hex[:12].upper()}"


def create_notification(user_id: str, title: str, message: str = "",
                        notification_type: str = "info",
                        resource_type: str = "", resource_id: str = "") -> Optional[str]:
    """创建通知并返回 notification_id"""
    nid = _generate_notification_id()
    try:
        with get_db() as conn:
            execute_insert(conn, """
                INSERT INTO notifications
                    (notification_id, user_id, title, message,
                     notification_type, resource_type, resource_id, is_read, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (nid, user_id, title, message, notification_type,
                  resource_type, resource_id, 0,
                  datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
        return nid
    except Exception as e:
        print(f"Notification create error: {e}")
        return None


def get_unread_count(user_id: str) -> int:
    """获取用户未读通知数"""
    with get_db() as conn:
        result = execute_query(
            conn,
            "SELECT COUNT(*) as cnt FROM notifications WHERE user_id = %s AND is_read = 0",
            (user_id,)
        )
    return result[0]["cnt"] if result else 0


def get_notifications(user_id: str, page: int = 1, page_size: int = 20,
                      unread_only: bool = False) -> tuple:
    """分页获取用户通知列表"""
    conditions = ["user_id = %s"]
    params = [user_id]
    if unread_only:
        conditions.append("is_read = 0")
    where = " AND ".join(conditions)
    offset = (page - 1) * page_size
    with get_db() as conn:
        total = execute_query(
            conn, f"SELECT COUNT(*) as cnt FROM notifications WHERE {where}", params
        )[0]["cnt"]
        items = execute_query(
            conn, f"SELECT * FROM notifications WHERE {where} ORDER BY created_at DESC LIMIT {page_size} OFFSET {offset}",
            params
        )
    return items, total


def mark_as_read(notification_id: str, user_id: str):
    """标记单条通知为已读"""
    with get_db() as conn:
        execute_insert(conn,
                       "UPDATE notifications SET is_read = 1 WHERE notification_id = %s AND user_id = %s",
                       (notification_id, user_id))


def mark_all_as_read(user_id: str):
    """标记用户所有通知为已读"""
    with get_db() as conn:
        execute_insert(conn,
                       "UPDATE notifications SET is_read = 1 WHERE user_id = %s AND is_read = 0",
                       (user_id,))
