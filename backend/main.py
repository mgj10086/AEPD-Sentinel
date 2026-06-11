"""AE Sentinel - Main FastAPI Application"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import time

from backend.core.config import PORT, HOST
from backend.core.database import init_db
from backend.core.rate_limit import rate_limit_middleware

# Import all routers
from backend.api.auth import router as auth_router
from backend.api.ae import router as ae_router
from backend.api.sae import router as sae_router
from backend.api.deviations import router as deviation_router
from backend.api.signals import router as signal_router
from backend.api.compliance import router as compliance_router
from backend.api.knowledge import router as knowledge_router
from backend.api.audit import router as audit_router
from backend.api.health import router as health_router
from backend.api.users import router as users_router
from backend.api.notifications import router as notifications_router

START_TIME = time.time()

app = FastAPI(
    title="AE Sentinel API",
    description="药物临床试验不良事件智能监测平台 - API",
    version="1.0.0"
)

# CORS — 生产环境通过 CORS_ORIGINS 环境变量配置允许的域名
_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware (120 req/min per client)
@app.middleware("http")
async def rate_limit(request: Request, call_next):
    return await rate_limit_middleware(request, call_next)

# Register all routers
app.include_router(auth_router)
app.include_router(ae_router)
app.include_router(sae_router)
app.include_router(deviation_router)
app.include_router(signal_router)
app.include_router(compliance_router)
app.include_router(knowledge_router)
app.include_router(audit_router)
app.include_router(health_router)
app.include_router(users_router)
app.include_router(notifications_router)

# Serve frontend
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def serve_frontend():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "AE Sentinel API is running. Visit /docs for API documentation."}

@app.on_event("startup")
async def startup():
    print("=" * 60)
    print("AE Sentinel 启动中...")
    print("=" * 60)

    # Initialize SQLite database
    try:
        init_db()
        print("数据库初始化完成")
    except Exception as e:
        print(f"数据库初始化错误: {e}")

    print("=" * 60)
    print(f"AE Sentinel 已启动 - http://{HOST}:{PORT}")
    print(f"API 文档: http://{HOST}:{PORT}/docs")
    print("=" * 60)
