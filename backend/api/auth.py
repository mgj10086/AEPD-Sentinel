"""Auth Router - 认证接口"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timedelta
import hashlib
import jwt

from backend.core.config import SECRET_KEY, ALGORITHM, TOKEN_EXPIRE
from backend.services.user_service import get_user_by_username, _hash, change_password
from backend.services.audit_service import extract_username_from_token, write_audit_log

router = APIRouter(prefix="/api/auth", tags=["认证"])

@router.post("/login")
def login(req: dict, request: Request):
    username = req.get("username", "")
    password = req.get("password", "")
    role = req.get("role", "")
    user = get_user_by_username(username)
    if not user or user["password_hash"] != _hash(password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = jwt.encode(
        {"sub": username, "role": user["role"], "name": user["name"],
         "exp": datetime.utcnow() + timedelta(seconds=TOKEN_EXPIRE)},
        SECRET_KEY, algorithm=ALGORITHM
    )
    # 写入审计日志
    write_audit_log(username, "auth", "login", username,
                    f"用户 {user['name']}({role}) 登录系统")
    return {"code": 200, "message": "success",
            "data": {"token": token, "role": user["role"],
                     "name": user["name"], "expires_in": TOKEN_EXPIRE},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}

@router.post("/change-password")
def change_self_password(req: dict, request: Request):
    """当前登录用户自助修改密码（需提供旧密码验证）"""
    old_password = req.get("old_password", "")
    new_password = req.get("new_password", "")

    # 参数校验
    if not old_password:
        raise HTTPException(status_code=400, detail="旧密码不能为空")
    if not new_password or len(new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度不能少于6位")
    if old_password == new_password:
        raise HTTPException(status_code=400, detail="新密码不能与旧密码相同")

    # 从 JWT 中提取当前用户名
    username = extract_username_from_token(request.headers.get("Authorization", ""))
    if not username or username == "anonymous":
        raise HTTPException(status_code=401, detail="无法识别当前用户，请重新登录")

    # 验证旧密码
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user["password_hash"] != _hash(old_password):
        raise HTTPException(status_code=400, detail="旧密码错误")

    # 更新密码
    change_password(user["user_id"], new_password)

    # 写入审计日志
    write_audit_log(username, "auth", "change_password", username,
                    "用户自助修改密码")
    return {"code": 200, "message": "密码修改成功",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}
