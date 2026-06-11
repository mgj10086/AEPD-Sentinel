"""Notifications Router - 应用内通知接口"""
from fastapi import APIRouter, Query, Request
from datetime import datetime
from typing import Optional

from backend.services.notification_service import (
    get_unread_count, get_notifications, mark_as_read, mark_all_as_read
)
from backend.services.audit_service import extract_username_from_token

router = APIRouter(prefix="/api/notifications", tags=["通知"])


@router.get("/unread-count")
def unread_count(request: Request):
    user = extract_username_from_token(request.headers.get("Authorization", ""))
    count = get_unread_count(user)
    return {"code": 200, "message": "success", "data": {"count": count},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}


@router.get("/list")
def list_notifications(request: Request,
                       page: int = Query(1, ge=1),
                       page_size: int = Query(20, ge=1, le=100),
                       unread_only: bool = Query(False)):
    user = extract_username_from_token(request.headers.get("Authorization", ""))
    items, total = get_notifications(user, page, page_size, unread_only)
    return {"code": 200, "message": "success",
            "data": {"items": items, "total": total, "page": page, "page_size": page_size},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}


@router.put("/{notif_id}/read")
def mark_read(request: Request, notif_id: str):
    user = extract_username_from_token(request.headers.get("Authorization", ""))
    mark_as_read(notif_id, user)
    return {"code": 200, "message": "success",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}


@router.put("/read-all")
def mark_all_read(request: Request):
    user = extract_username_from_token(request.headers.get("Authorization", ""))
    mark_all_as_read(user)
    return {"code": 200, "message": "success",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}
