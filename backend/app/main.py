from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.sessions import router as sessions_router
from app.api.messages import router as messages_router
from app.api.checkpoints import router as checkpoints_router
from app.api import export
from app.checkpoint import CheckpointManager
from app.config import settings

app = FastAPI(title="PageForge", version="0.1.0")

# CORS 配置 — 允许前端开发服务器跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite 默认端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(sessions_router, prefix="/api/sessions", tags=["sessions"])
app.include_router(messages_router, prefix="/api/sessions", tags=["messages"])
app.include_router(checkpoints_router, prefix="/api/checkpoints", tags=["checkpoints"])
app.include_router(export.router, prefix="/api", tags=["export"])


@app.get("/api/health")
async def health():
    """健康检查接口"""
    return {"status": "ok"}


@app.get("/health")
async def health_check():
    """健康检查端点（包含 Redis 状态）"""
    manager = CheckpointManager(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB
    )
    
    redis_ok = manager.health_check()
    
    return {
        "status": "healthy" if redis_ok else "degraded",
        "redis": "connected" if redis_ok else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }
