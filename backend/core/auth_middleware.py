"""Auth Middleware — JWT 角色权限验证"""
from functools import wraps
from fastapi import HTTPException, Request
from backend.core.config import SECRET_KEY, ALGORITHM


# 角色可访问的路由前缀
ROLE_PERMISSIONS = {
    "admin": ["*"],  # 管理员可访问所有
    "pv_specialist": [
        "/api/ae", "/api/saereport", "/api/signals", "/api/compliance",
        "/api/deviations", "/api/health", "/api/admin/knowledge",
    ],
    "cra": [
        "/api/ae", "/api/saereport", "/api/deviations",
        "/api/compliance", "/api/health",
    ],
}


def get_token_payload(request: Request) -> dict:
    """从请求中提取并解析 JWT token"""
    import jwt as pyjwt
    auth = request.headers.get("Authorization", "")
    if not auth:
        return {}
    try:
        token = auth.replace("Bearer ", "").strip()
        return pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return {}


def require_role(*allowed_roles: str):
    """装饰器：验证用户角色是否在允许列表中"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从 kwargs 中提取 request
            request = None
            for v in kwargs.values():
                if isinstance(v, Request):
                    request = v
                    break
            if not request:
                for v in (args or ()):
                    if isinstance(v, Request):
                        request = v
                        break

            if request:
                payload = get_token_payload(request)
                user_role = payload.get("role", "")
                if user_role not in allowed_roles:
                    raise HTTPException(status_code=403, detail="没有权限执行此操作")

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user(request: Request) -> dict:
    """获取当前用户信息（用于非阻断式获取）"""
    payload = get_token_payload(request)
    return {
        "username": payload.get("sub", "anonymous"),
        "role": payload.get("role", ""),
        "name": payload.get("name", ""),
    }
