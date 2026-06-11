"""Users Router - 用户管理 CRUD"""
from fastapi import APIRouter, Query, HTTPException, Request
from datetime import datetime
from typing import Optional

from backend.services.user_service import (
    get_user_by_id, list_users, create_user, update_user,
    delete_user, change_password
)
from backend.core.auth_middleware import get_token_payload
from backend.services.audit_service import extract_username_from_token, write_audit_log

router = APIRouter(prefix="/api/admin/users", tags=["用户管理"])


def _require_admin(request: Request):
    """内联角色检查：仅 admin 可访问"""
    payload = get_token_payload(request)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="没有权限执行此操作")


@router.get("/list")
def get_users(request: Request,
              page: int = Query(1, ge=1),
              page_size: int = Query(20, ge=1, le=100),
              role: Optional[str] = Query(None),
              keyword: Optional[str] = Query(None)):
    _require_admin(request)
    items, total = list_users(page, page_size, role, keyword)
    return {"code": 200, "message": "success",
            "data": {"items": items, "total": total, "page": page, "page_size": page_size},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}


@router.get("/{user_id}")
def get_user(request: Request, user_id: str):
    _require_admin(request)
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"code": 200, "message": "success", "data": user,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}


@router.post("/create")
def create_user_endpoint(request: Request, req: dict):
    _require_admin(request)
    username = req.get("username", "").strip()
    password = req.get("password", "")
    name = req.get("name", "").strip()
    role = req.get("role", "cra")
    email = req.get("email", "")
    phone = req.get("phone", "")
    if not username or not password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")
    if role not in ("admin", "pv_specialist", "cra"):
        raise HTTPException(status_code=400, detail="无效的角色类型")
    user_id = create_user(username, password, name, role, email, phone)
    user = extract_username_from_token(request.headers.get("Authorization", ""))
    write_audit_log(user, "user_mgmt", "create", user_id,
                    f"创建用户 {username}({role})")
    return {"code": 200, "message": "success", "data": {"user_id": user_id},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}


@router.put("/{user_id}")
def update_user_endpoint(request: Request, user_id: str, req: dict):
    _require_admin(request)
    existing = get_user_by_id(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="用户不存在")
    update_user(user_id, **req)
    user = extract_username_from_token(request.headers.get("Authorization", ""))
    write_audit_log(user, "user_mgmt", "update", user_id, "更新用户信息")
    return {"code": 200, "message": "success",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}


@router.delete("/{user_id}")
def delete_user_endpoint(request: Request, user_id: str):
    _require_admin(request)
    existing = get_user_by_id(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="用户不存在")
    delete_user(user_id)
    user = extract_username_from_token(request.headers.get("Authorization", ""))
    write_audit_log(user, "user_mgmt", "delete", user_id, "删除用户")
    return {"code": 200, "message": "success",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}


@router.put("/{user_id}/password")
def change_password_endpoint(request: Request, user_id: str, req: dict):
    _require_admin(request)
    new_password = req.get("new_password", "")
    if not new_password or len(new_password) < 6:
        raise HTTPException(status_code=400, detail="密码长度不能少于6位")
    existing = get_user_by_id(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="用户不存在")
    change_password(user_id, new_password)
    user = extract_username_from_token(request.headers.get("Authorization", ""))
    write_audit_log(user, "user_mgmt", "update", user_id, "修改密码")
    return {"code": 200, "message": "success",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}
