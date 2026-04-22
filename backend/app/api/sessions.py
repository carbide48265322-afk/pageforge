from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from app.services.session_service import SessionService
from app.services.version_service import VersionService

router = APIRouter()
session_service = SessionService()
version_service = VersionService()


# ---------- 请求/响应模型 ----------

class CreateSessionResponse(BaseModel):
    """创建会话的响应"""
    session_id: str


class BaseVersionRequest(BaseModel):
    """切换基准版本的请求"""
    version: int


class BaseVersionResponse(BaseModel):
    """切换基准版本的响应"""
    success: bool
    current_base: int


# ---------- API 端点 ----------

@router.post("", response_model=CreateSessionResponse)
async def create_session():
    """创建新会话"""
    session = session_service.create_session()
    return CreateSessionResponse(session_id=session.id)


@router.get("/{session_id}/versions")
async def get_versions(session_id: str):
    """获取某个会话的所有版本列表（不含 HTML 内容）"""
    session = session_service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    versions = version_service.get_all_versions(session_id)
    return {
        "versions": versions,
        "current_base": session.current_base_version,
    }


@router.get("/{session_id}/html")
async def get_html(session_id: str, version: int | None = None):
    """获取指定版本的 HTML 内容，不传 version 则返回最新版本"""
    if version is None:
        v = version_service.get_latest_version(session_id)
    else:
        v = version_service.get_version(session_id, version)
    if v is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return {"html": v.html, "version": v.version}


@router.post("/{session_id}/base-version", response_model=BaseVersionResponse)
async def set_base_version(session_id: str, req: BaseVersionRequest):
    """切换当前基准版本 — 后续修改将基于此版本"""
    session = session_service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    v = version_service.get_version(session_id, req.version)
    if v is None:
        raise HTTPException(status_code=404, detail="Version not found")
    session.current_base_version = req.version
    session_service.save_session(session)
    return BaseVersionResponse(success=True, current_base=req.version)


@router.get("/{session_id}/export")
async def export_html(session_id: str, version: int | None = None):
    """导出 HTML 文件下载，不传 version 则导出最新版本"""
    if version is None:
        v = version_service.get_latest_version(session_id)
    else:
        v = version_service.get_version(session_id, version)
    if v is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return Response(
        content=v.html,
        media_type="text/html",
        headers={
            "Content-Disposition": f"attachment; filename=page-v{v.version}.html"
        },
    )