from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.sessions import router as sessions_router
from app.api.messages import router as messages_router
from app.api.templates import router as templates_router
from app.api.webcontainer import router as webcontainer_router
from app.core import init_registry  # 新增导入

app = FastAPI(title="PageForge", version="0.1.0")

# CORS 配置 — 允许前端开发服务器跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:6000"],  # 前端新端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(sessions_router, prefix="/api/sessions", tags=["sessions"])
app.include_router(messages_router, prefix="/api/sessions", tags=["messages"])
app.include_router(templates_router, prefix="/api", tags=["templates"])
app.include_router(webcontainer_router, prefix="/api/webcontainer", tags=["webcontainer"])

# 启动时初始化注册中心
@app.on_event("startup")
async def startup():
    """启动时初始化注册中心"""
    init_registry()


@app.get("/api/health")
async def health():
    """健康检查接口"""
    return {"status": "ok"}