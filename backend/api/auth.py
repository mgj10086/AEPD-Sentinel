"""Auth Router - 认证接口"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
import jwt
import sys, os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from core.config import MOCK_USERS, SECRET_KEY, ALGORITHM, TOKEN_EXPIRE

router = APIRouter(prefix="/api/auth", tags=["认证"])

@router.post("/login")
def login(req: dict):
    username = req.get("username", "")
    password = req.get("password", "")
    role = req.get("role", "")
    user = MOCK_USERS.get(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = jwt.encode(
        {"sub": username, "role": user["role"], "name": user["name"],
         "exp": datetime.utcnow() + timedelta(seconds=TOKEN_EXPIRE)},
        SECRET_KEY, algorithm=ALGORITHM
    )
    return {"code": 200, "message": "success",
            "data": {"token": token, "role": user["role"], "expires_in": TOKEN_EXPIRE},
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}