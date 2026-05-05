"""
Graph 节点事件推送工具

封装 get_stream_writer 调用，为各个节点提供统一的事件推送接口。

设计：所有自定义事件统一用 "message" 作为 SSE event 类型，
事件细分类型放在 data.type 中，前端单点监听 + switch(data.type) 分发。
"""

import time

from langgraph.config import get_stream_writer


def emit_event(event_type: str, data: dict) -> None:
    """
    推送 SSE 事件

    Args:
        event_type: 事件细分类型（如 "intent:start"、"thinking_delta"），放入 data.type
        data: 事件数据（JSON 序列化）
    """
    try:
        writer = get_stream_writer()
        # 统一用 "message" 作为 SSE event 类型，细分类型放进 data.type
        payload = {"type": event_type, **data}
        writer({
            "event": "message",
            "data": payload,
        })
    except Exception:
        # 非流式模式下忽略错误
        pass


def emit_intent_start() -> None:
    """推送意图识别开始"""
    emit_event("intent:start", {})


def emit_intent_result(intent: str, confidence: float, tags: list, mode: str = None,
                       complexity: str = None, suggested_style: str = None) -> None:
    """推送意图识别结果"""
    emit_event("intent:result", {
        "intent": intent,
        "confidence": confidence,
        "tags": tags,
        "mode": mode,
        "complexity": complexity,
        "suggested_style": suggested_style,
    })


def emit_intent_style_query(options: list, auto_select: str = "minimal", timeout_ms: int = 5000) -> None:
    """推送风格查询请求"""
    emit_event("intent:style_query", {
        "options": options,
        "auto_select": auto_select,
        "timeout_ms": timeout_ms,
    })


def emit_intent_style_selected(style: str) -> None:
    """推送风格选择结果"""
    emit_event("intent:style_selected", {"style": style})


def emit_style_selected(style: str, primary_color: str = None, description: str = None, **kwargs) -> None:
    """推送风格选择结果（兼容格式）"""
    data = {"style": style}
    if primary_color:
        data["primary_color"] = primary_color
    if description:
        data["description"] = description
    data.update(kwargs)
    emit_event("style_selected", data)


def emit_thinking_start(id: str = None) -> None:
    """推送思维链开始"""
    emit_event("thinking_start", {"id": id or f"thinking_{int(time.time()*1000)}"})


def emit_thinking_delta(id: str, delta: str) -> None:
    """推送思维链增量内容"""
    emit_event("thinking_delta", {"id": id, "delta": delta})


def emit_thinking_end(id: str, content: str, summary: str = None) -> None:
    """推送思维链完成"""
    emit_event("thinking_end", {
        "id": id,
        "content": content,
        "summary": summary,
    })


def emit_plan_start(steps: list, current: int = 0, id: str = None) -> None:
    """推送计划开始"""
    emit_event("plan_start", {
        "id": id or f"plan_{int(time.time()*1000)}",
        "steps": steps,
        "current": current,
    })


def emit_plan_update(steps: list, current: int = None, is_complete: bool = False) -> None:
    """推送计划更新"""
    emit_event("plan_update", {
        "steps": steps,
        "current": current,
        "is_complete": is_complete,
    })


def emit_status_init(message: str = "初始化...") -> None:
    """推送初始化状态"""
    emit_event("status:init", {"message": message})


def emit_status_installing(message: str = "正在安装依赖...") -> None:
    """推送安装中状态"""
    emit_event("status:installing", {"message": message})


def emit_status_install_done(message: str = "依赖安装完成") -> None:
    """推送安装完成状态"""
    emit_event("status:install_done", {"message": message})


def emit_status_starting_dev(port: int = 3000, message: str = None) -> None:
    """推送开发服务器启动状态"""
    emit_event("status:starting_dev", {
        "port": port,
        "message": message or f"Dev Server 启动中 (端口 {port})",
    })


def emit_plan_done(steps: list) -> None:
    """推送计划完成"""
    emit_event("plan_done", {
        "steps": steps,
    })


def emit_tool_call_start(tool_id: str, name: str, input: dict = None) -> None:
    """推送工具调用开始"""
    emit_event("tool_call:start", {
        "id": tool_id,
        "name": name,
        "input": input,
    })


def emit_tool_call_end(tool_id: str, status: str, duration_ms: int = None,
                      error: str = None) -> None:
    """推送工具调用结束"""
    emit_event("tool_call:end", {
        "id": tool_id,
        "status": status,
        "duration_ms": duration_ms,
        "error": error,
    })


def emit_command_output(output: str) -> None:
    """推送命令实时输出"""
    emit_event("command_output", {
        "output": output,
    })


def emit_file_created(file_path: str, name: str, language: str = None,
                   size_bytes: int = None) -> None:
    """推送文件创建事件"""
    emit_event("file_created", {
        "path": file_path,
        "name": name,
        "language": language,
        "size_bytes": size_bytes,
    })


def emit_file_updated(file_path: str, name: str, language: str = None) -> None:
    """推送文件更新事件"""
    emit_event("file_updated", {
        "path": file_path,
        "name": name,
        "language": language,
    })


def emit_file_deleted(file_path: str) -> None:
    """推送文件删除事件"""
    emit_event("file_deleted", {
        "path": file_path,
    })


def emit_status_generation_done() -> None:
    """推送代码生成完成"""
    emit_event("status:generation_done", {
        "message": "代码生成已完成",
    })


def emit_status_preview_ready(url: str = None) -> None:
    """推送预览就绪"""
    emit_event("status:preview_ready", {
        "url": url,
    })


def emit_text_delta(id: str, content: str) -> None:
    """推送文本增量"""
    emit_event("text_delta", {
        "id": id,
        "delta": content,
    })


def emit_text_done(id: str, content: str = None) -> None:
    """推送文本完成"""
    data = {"id": id}
    if content is not None:
        data["content"] = content
    emit_event("text_done", data)
