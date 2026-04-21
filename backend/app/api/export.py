from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.services.export_service import ExportService
from app.services.session_service import SessionService
from app.services.version_service import VersionService

router = APIRouter()


@router.post("/sessions/{session_id}/export")
async def export_session_project(
    session_id: str,
    project_name: str = "pageforge-project"
):
    """导出会话的最新版本为完整项目"""
    session_service = SessionService()
    version_service = VersionService()
    
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 获取最新版本
    versions = version_service.list_versions(session_id)
    if not versions:
        raise HTTPException(status_code=404, detail="No versions found")
    
    latest_version = versions[-1]
    version_data = version_service.get_version(session_id, latest_version.version)
    
    if not version_data:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # 导出项目
    zip_data = ExportService.export_project(version_data.html, project_name)
    
    # 返回 ZIP 文件
    return StreamingResponse(
        iter([zip_data]),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={project_name}.zip"
        }
    )
