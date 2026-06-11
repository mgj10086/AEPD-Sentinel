"""Users Router - 用户管理 CRUD"""
from fastapi import APIRouter, Query, HTTPException, Request
from datetime import datetime
from typing import Optional

from backend.services.user_service import (
    get_user_by_id, list_users, create_user, update_user,
    delete_user, change_password
)
from backend.core.auth_middleware import require_role
from backend.services.audit_service import extract_username_from_token, write_audit_log

router = APIRouter(prefix="/api/admin/users", tags=["用户管理"])


@router.get("/list")
@require_role("admin")
def get_users(request: Request,
              page: int = Query(1, ge=1),
              page_size: int = Query(20, ge=1, le=100),
              role: Optional[str] = Query(None),
              keyword: Optional[str] = Query(None)):
    items, total = list_users(page, page_size, role, keyword)
    return {"code": 200, "message": "success",
            "data": {"items": items, "total": total, "page": page, "page_size": page_size},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}


@router.get("/{user_id}")
@require_role("admin")
def get_user(request: Request, user_id: str):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"code": 200, "message": "success", "data": user,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}


@router.post("/create")
@require_role("admin")
def create_user_endpoint(request: Request, req: dict):
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
    # 审计日志
    user = extract_username_from_token(request.headers.get("Authorization", ""))
    write_audit_log(user, "user_mgmt", "create", user_id,
                    f"创建用户 {username}({role})")
    return {"code": 200, "message": "success", "data": {"user_id": user_id},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}


@router.put("/{user_id}")
@require_role("admin")
def update_user_endpoint(request: Request, user_id: str, req: dict):
    existing = get_user_by_id(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="用户不存在")
    update_user(user_id, **req)
    user = extract_username_from_token(request.headers.get("Authorization", ""))
    write_audit_log(user, "user_mgmt", "update", user_id, "更新用户信息")
    return {"code": 200, "message": "success",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}


@router.delete("/{user_id}")
@require_role("admin")
def delete_user_endpoint(request: Request, user_id: str):
    existing = get_user_by_id(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="用户不存在")
    delete_user(user_id)
    user = extract_username_from_token(request.headers.get("Authorization", ""))
    write_audit_log(user, "user_mgmt", "delete", user_id, "删除用户")
    return {"code": 200, "message": "success",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}


@router.put("/{user_id}/password")
@require_role("admin")
def change_password_endpoint(request: Request, user_id: str, req: dict):
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
