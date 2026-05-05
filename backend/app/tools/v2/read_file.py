"""
V2 Tool: read_file

读取 session 目录下的文件内容。
执行时推送 tool_call:start/end 和 file_read 事件。
"""

import time
from pathlib import Path
from typing import Dict, Any
from langchain_core.tools import tool
from .security import SecurityValidator
from .config import MAX_READ_SIZE

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
def read_file(path: str, session_id: str, max_size: int = MAX_READ_SIZE) -> Dict[str, Any]:
    """
    读取 session 目录下的文件内容

    Args:
        path: 文件相对路径（如 "src/App.tsx"）
        session_id: 会话 ID
        max_size: 最大读取大小（字节），默认 512KB

    Returns:
        操作结果，包含 success、content、size、encoding 等信息
    """
    tool_id = f"read_file_{int(time.time() * 1000)}"
    start_time = time.time()

    # 推送工具开始事件
    if HAS_EMITTER:
        emit_tool_call_start(
            tool_id=tool_id,
            name="read_file",
            input={"path": path, "session_id": session_id},
        )

    try:
        # 1. 路径安全校验
        is_safe, abs_path, error = SecurityValidator.validate_path(path, session_id)
        if not is_safe:
            if HAS_EMITTER:
                emit_tool_call_end(tool_id, "error", error=error)
            return {"success": False, "error": error}

        # 2. 检查文件是否存在
        if not abs_path.exists():
            error = f"文件不存在: {path}"
            if HAS_EMITTER:
                emit_tool_call_end(tool_id, "error", error=error)
            return {"success": False, "error": error}

        # 3. 检查文件大小
        file_size = abs_path.stat().st_size
        if file_size > max_size:
            error = f"文件过大: {file_size} > {max_size}"
            if HAS_EMITTER:
                emit_tool_call_end(tool_id, "error", error=error)
            return {"success": False, "error": error}

        # 4. 读取文件内容
        content = abs_path.read_text(encoding='utf-8')

        # 推送工具结束事件
        if HAS_EMITTER:
            emit_tool_call_end(
                tool_id=tool_id,
                status="success",
                duration_ms=int((time.time() - start_time) * 1000),
            )

        return {
            "success": True,
            "path": path,
            "absolute_path": str(abs_path),
            "content": content,
            "size": file_size,
            "encoding": "utf-8",
            "session_id": session_id,
        }

    except PermissionError:
        error = f"权限不足，无法读取文件: {path}"
        if HAS_EMITTER:
            emit_tool_call_end(tool_id, "error", error=error)
        return {"success": False, "error": error}
    except UnicodeDecodeError:
        error = f"文件不是有效的 UTF-8 文本: {path}"
        if HAS_EMITTER:
            emit_tool_call_end(tool_id, "error", error=error)
        return {"success": False, "error": error}
    except Exception as e:
        error = f"文件读取失败: {str(e)}"
        if HAS_EMITTER:
            emit_tool_call_end(tool_id, "error", error=error)
        return {"success": False, "error": error}
