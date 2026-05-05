"""
V2 Tool: list_files

列出 session 目录下的文件结构（支持递归）。
执行时推送 tool_call:start/end 事件。
"""

import time
from pathlib import Path
from typing import Dict, Any, List
from langchain_core.tools import tool
from .security import SecurityValidator
from .config import IGNORED_PATTERNS

# 尝试导入 event_emitter（如果可用）
try:
    from app.graph.event_emitter import (
        emit_tool_call_start,
        emit_tool_call_end,
    )
    HAS_EMITTER = True
except ImportError:
    HAS_EMITTER = False


@tool
def list_files(
    path: str,
    session_id: str,
    recursive: bool = False,
    max_depth: int = 3
) -> Dict[str, Any]:
    """
    列出 session 目录下的文件结构

    Args:
        path: 目录相对路径（如 "" 表示根目录，"src" 表示 src 子目录）
        session_id: 会话 ID
        recursive: 是否递归列出子目录
        max_depth: 最大递归深度（防止无限递归），默认 3

    Returns:
        操作结果，包含 success、files（文件列表）、directories（目录列表）、structure（树状结构）等
    """
    tool_id = f"list_files_{int(time.time() * 1000)}"
    start_time = time.time()

    # 推送工具开始事件
    if HAS_EMITTER:
        emit_tool_call_start(
            tool_id=tool_id,
            name="list_files",
            input={"path": path, "session_id": session_id, "recursive": recursive, "max_depth": max_depth},
        )

    try:
        # 1. 路径安全校验
        is_safe, abs_path, error = SecurityValidator.validate_path(path, session_id)
        if not is_safe:
            if HAS_EMITTER:
                emit_tool_call_end(tool_id, "error", error=error)
            return {"success": False, "error": error}

        # 2. 检查路径是否存在
        if not abs_path.exists():
            error = f"路径不存在: {path}"
            if HAS_EMITTER:
                emit_tool_call_end(tool_id, "error", error=error)
            return {"success": False, "error": error}

        # 3. 如果是文件，返回文件信息
        if abs_path.is_file():
            if HAS_EMITTER:
                emit_tool_call_end(
                    tool_id=tool_id,
                    status="success",
                    duration_ms=int((time.time() - start_time) * 1000),
                )
            return {
                "success": True,
                "type": "file",
                "path": path,
                "absolute_path": str(abs_path),
                "size": abs_path.stat().st_size,
            }

        # 4. 如果是目录，列出内容
        files: List[Dict[str, Any]] = []
        directories: List[Dict[str, Any]] = []

        def _should_ignore(name: str) -> bool:
            """判断是否应该忽略该文件/目录"""
            for pattern in IGNORED_PATTERNS:
                if pattern in name:
                    return True
            return False

        def _list_dir(current_path: Path, current_depth: int) -> List[Dict[str, Any]]:
            """递归列出目录"""
            if current_depth > max_depth:
                return []

            items = []
            try:
                for item in sorted(current_path.iterdir()):
                    # 跳过忽略的文件/目录
                    if _should_ignore(item.name):
                        continue

                    # 获取相对路径
                    try:
                        rel_path = item.relative_to(abs_path)
                    except ValueError:
                        continue

                    relative_path_str = str(rel_path).replace("\\", "/")

                    if item.is_file():
                        file_info = {
                            "type": "file",
                            "path": f"{path}/{relative_path_str}" if path else relative_path_str,
                            "name": item.name,
                            "size": item.stat().st_size,
                        }
                        files.append(file_info)
                        items.append(file_info)
                    elif item.is_dir():
                        dir_info = {
                            "type": "directory",
                            "path": f"{path}/{relative_path_str}" if path else relative_path_str,
                            "name": item.name,
                        }
                        directories.append(dir_info)

                        if recursive:
                            # 递归列出子目录内容
                            dir_info["children"] = _list_dir(item, current_depth + 1)

                        items.append(dir_info)
            except PermissionError:
                # 忽略无权限访问的目录
                pass

            return items

        structure = _list_dir(abs_path, 0)

        # 推送工具结束事件
        if HAS_EMITTER:
            emit_tool_call_end(
                tool_id=tool_id,
                status="success",
                duration_ms=int((time.time() - start_time) * 1000),
            )

        return {
            "success": True,
            "type": "directory",
            "path": path or ".",
            "absolute_path": str(abs_path),
            "files": files,
            "directories": directories,
            "structure": structure,
            "total_files": len(files),
            "total_directories": len(directories),
        }

    except PermissionError:
        error = f"权限不足，无法列出目录: {path}"
        if HAS_EMITTER:
            emit_tool_call_end(tool_id, "error", error=error)
        return {"success": False, "error": error}
    except Exception as e:
        error = f"列出目录失败: {str(e)}"
        if HAS_EMITTER:
            emit_tool_call_end(tool_id, "error", error=error)
        return {"success": False, "error": error}
