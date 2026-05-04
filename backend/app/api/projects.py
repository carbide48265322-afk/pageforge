from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.services.session_service import SessionService
import json

router = APIRouter()
session_service = SessionService()


@router.get("/{session_id}/files")
async def get_project_files(session_id: str):
    """返回项目文件树结构"""
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # TODO: 从 WebContainer 或数据库获取文件列表
    # 临时返回空结构
    return {
        "project_id": session_id,
        "files": []
    }


@router.get("/{session_id}/content")
async def get_file_content(session_id: str, path: str):
    """返回指定文件内容"""
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not path:
        raise HTTPException(status_code=400, detail="Missing 'path' query parameter")
    
    # TODO: 从 WebContainer 或数据库读取文件内容
    # 临时返回空结构
    return {
        "project_id": session_id,
        "path": path,
        "content": "",
        "language": "typescript",
        "size_bytes": 0
    }
