"""
V2 Tool: write_file

在 session 目录下创建或覆盖文件。
执行时推送 tool_call:start/end 和 file_created 事件。
"""

import os
import time
from pathlib import Path
from typing import Dict, Any
from langchain_core.tools import tool
from .security import SecurityValidator
from .config import MAX_FILE_SIZE

# 尝试导入 event_emitter（如果可用）
try:
    from app.graph.event_emitter import (
        emit_tool_call_start,
        emit_tool_call_end,
        emit_file_created,
    )
    HAS_EMITTER = True
except ImportError:
    HAS_EMITTER = False


@tool
def write_file(path: str, content: str, session_id: str) -> Dict[str, Any]:
    """
    在 session 目录下创建或覆盖文件

    Args:
        path: 文件相对路径（如 "src/App.tsx"）
        content: 文件内容
        session_id: 会话 ID（用于隔离不同用户的项目）

    Returns:
        操作结果，包含 success、absolute_path、file_size 等信息
    """
    tool_id = f"write_file_{int(time.time() * 1000)}"
    start_time = time.time()

    # 推送工具开始事件
    if HAS_EMITTER:
        emit_tool_call_start(
            tool_id=tool_id,
            name="write_file",
            input={"path": path, "session_id": session_id},
        )

    try:
        # 1. 路径安全校验
        is_safe, abs_path, error = SecurityValidator.validate_path(path, session_id)
        if not is_safe:
            if HAS_EMITTER:
                emit_tool_call_end(tool_id, "error", error=error)
            return {"success": False, "error": error}

        # 2. 文件大小校验
        content_size = len(content.encode('utf-8'))
        is_safe, error = SecurityValidator.validate_file_size(content_size, is_write=True)
        if not is_safe:
            if HAS_EMITTER:
                emit_tool_call_end(tool_id, "error", error=error)
            return {"success": False, "error": error}

        # 3. 自动创建父目录
        parent_dir = abs_path.parent
        if not parent_dir.exists():
            parent_dir.mkdir(parents=True, exist_ok=True)

        # 4. 写入文件
        abs_path.write_text(content, encoding='utf-8')

        # 推送文件创建事件
        if HAS_EMITTER:
            emit_file_created(
                file_path=path,
                name=abs_path.name,
                language=_infer_language(path),
                size_bytes=content_size,
            )

            # 推送工具结束事件
            emit_tool_call_end(
                tool_id=tool_id,
                status="success",
                duration_ms=int((time.time() - start_time) * 1000),
            )

        return {
            "success": True,
            "path": path,
            "absolute_path": str(abs_path),
            "file_size": content_size,
            "session_id": session_id,
        }

    except PermissionError:
        error = f"权限不足，无法写入文件: {path}"
        if HAS_EMITTER:
            emit_tool_call_end(tool_id, "error", error=error)
        return {"success": False, "error": error}
    except Exception as e:
        error = f"文件写入失败: {str(e)}"
        if HAS_EMITTER:
            emit_tool_call_end(tool_id, "error", error=error)
        return {"success": False, "error": error}


def _infer_language(path: str) -> str:
    """根据文件路径推断编程语言"""
    ext = path.split('.')[-1].lower()
    language_map = {
        'ts': 'typescript',
        'tsx': 'typescript',
        'js': 'javascript',
        'jsx': 'javascript',
        'json': 'json',
        'css': 'css',
        'scss': 'scss',
        'html': 'html',
        'md': 'markdown',
        'py': 'python',
    }
    return language_map.get(ext, 'text')
