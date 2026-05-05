"""
事件发射器 - 用于在graph节点中推送SSE事件
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# 全局事件发射器（可以被messages.py中的SSE处理器替换）
_event_emitter = None


def set_event_emitter(emitter):
    """设置全局事件发射器"""
    global _event_emitter
    _event_emitter = emitter


def _emit(event_type: str, data: Dict[str, Any]):
    """发送事件"""
    if _event_emitter:
        try:
            _event_emitter(event_type, data)
        except Exception as e:
            logger.warning(f"事件发送失败: {e}")


def emit_tool_call_start(tool_id: str, name: str, input: Dict[str, Any]):
    """发送工具调用开始事件"""
    _emit("tool_call:start", {
        "tool_id": tool_id,
        "name": name,
        "input": input,
        "timestamp": __import__('time').time()
    })


def emit_tool_call_end(tool_id: str, status: str, duration_ms: Optional[int] = None, error: Optional[str] = None):
    """发送工具调用结束事件"""
    _emit("tool_call:end", {
        "tool_id": tool_id,
        "status": status,
        "duration_ms": duration_ms,
        "error": error,
        "timestamp": __import__('time').time()
    })


def emit_file_created(file_path: str, name: str, language: str, size_bytes: Optional[int] = None):
    """发送文件创建事件"""
    _emit("file:created", {
        "file_path": file_path,
        "name": name,
        "language": language,
        "size_bytes": size_bytes,
        "timestamp": __import__('time').time()
    })


def emit_status_generation_done():
    """发送生成完成状态事件"""
    _emit("status:generation_done", {
        "timestamp": __import__('time').time()
    })


def emit_command_output(command: str, output: str, is_stderr: bool = False):
    """发送命令输出事件"""
    _emit("command:output", {
        "command": command,
        "output": output,
        "is_stderr": is_stderr,
        "timestamp": __import__('time').time()
    })


def emit_thinking_start(id: str):
    """发送思考开始事件"""
    _emit("thinking:start", {
        "id": id,
        "timestamp": __import__('time').time()
    })


def emit_thinking_delta(id: str, delta: str):
    """发送思考内容增量事件"""
    _emit("thinking:delta", {
        "id": id,
        "delta": delta,
        "timestamp": __import__('time').time()
    })


def emit_thinking_end(id: str, content: str, summary: str):
    """发送思考结束事件"""
    _emit("thinking:end", {
        "id": id,
        "content": content,
        "summary": summary,
        "timestamp": __import__('time').time()
    })


def emit_plan_start(id: str, steps: list, current: int = 0):
    """发送计划开始事件"""
    _emit("plan:start", {
        "id": id,
        "steps": steps,
        "current": current,
        "timestamp": __import__('time').time()
    })


def emit_plan_update(steps: list, is_complete: bool = False):
    """发送计划更新事件"""
    _emit("plan:update", {
        "steps": steps,
        "is_complete": is_complete,
        "timestamp": __import__('time').time()
    })


def emit_plan_done(steps: list):
    """发送计划完成事件"""
    _emit("plan:done", {
        "steps": steps,
        "timestamp": __import__('time').time()
    })


def emit_text_delta(id: str, content: str):
    """发送文本增量事件"""
    _emit("text:delta", {
        "id": id,
        "content": content,
        "timestamp": __import__('time').time()
    })


def emit_text_done(id: str, content: str):
    """发送文本完成事件"""
    _emit("text:done", {
        "id": id,
        "content": content,
        "timestamp": __import__('time').time()
    })


def emit_style_selected(style: str, primary_color: str, description: str):
    """发送风格选择事件"""
    _emit("style:selected", {
        "style": style,
        "primary_color": primary_color,
        "description": description,
        "timestamp": __import__('time').time()
    })