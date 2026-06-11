"""Auth Router - 认证接口"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timedelta
import hashlib
import jwt

from backend.core.config import SECRET_KEY, ALGORITHM, TOKEN_EXPIRE
from backend.services.user_service import get_user_by_username, _hash
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
