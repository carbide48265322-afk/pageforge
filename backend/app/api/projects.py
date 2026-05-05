from fastapi import APIRouter, HTTPException, Query
from app.tools.v2.security import SecurityValidator
from app.tools.v2.config import GENERATED_PROJECTS_DIR, IGNORED_PATTERNS
from pathlib import Path

router = APIRouter()


@router.get("/{session_id}/files")
async def get_project_files(session_id: str):
    """
    返回项目文件列表（扁平结构）。
    扫描 generated_projects/sessions/{session_id}/ 目录，
    返回所有文件和目录的 path + type 列表。
    """
    # 校验 session_id
    is_valid, error = SecurityValidator.validate_session_id(session_id)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    session_dir = GENERATED_PROJECTS_DIR / session_id

    # 目录不存在时返回空列表（code_gen 可能尚未生成文件）
    if not session_dir.exists() or not session_dir.is_dir():
        return {"success": True, "files": []}

    files = []

    def _should_ignore(name: str) -> bool:
        return any(pattern in name for pattern in IGNORED_PATTERNS)

    def _scan(current_path: Path, prefix: str):
        """递归扫描目录，收集 files 和 directories"""
        try:
            for item in sorted(current_path.iterdir(), key=lambda x: (x.is_file(), x.name)):
                if _should_ignore(item.name):
                    continue

                rel_path = f"{prefix}/{item.name}" if prefix else item.name

                if item.is_dir():
                    files.append({"path": rel_path, "type": "directory"})
                    _scan(item, rel_path)
                elif item.is_file():
                    files.append({"path": rel_path, "type": "file"})
        except PermissionError:
            pass

    _scan(session_dir, "")

    return {"success": True, "files": files}


@router.get("/{session_id}/content")
async def get_file_content(
    session_id: str,
    path: str = Query(..., description="文件相对路径，如 src/App.tsx"),
):
    """
    返回指定文件内容。
    从 generated_projects/sessions/{session_id}/ 读取文件。
    """
    # 校验 session_id
    is_valid, error = SecurityValidator.validate_session_id(session_id)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    # 校验 path（防路径穿越）
    is_safe, abs_path, error = SecurityValidator.validate_path(path, session_id)
    if not is_safe:
        raise HTTPException(status_code=400, detail=error)

    # 文件不存在
    if not abs_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    if not abs_path.is_file():
        raise HTTPException(status_code=400, detail=f"Not a file: {path}")

    # 检测是否为二进制文件
    try:
        content = abs_path.read_text(encoding="utf-8")
        is_binary = False
    except UnicodeDecodeError:
        is_binary = True
        content = None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Read error: {str(e)}")

    return {
        "content": content,
        "isBinary": is_binary,
        "success": True,
    }
