import json
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.graph.graph import pageforge_graph
from app.services.session_service import SessionService
from app.services.version_service import VersionService

router = APIRouter()
session_service = SessionService()
version_service = VersionService()


class MessageRequest(BaseModel):
    message: str


async def event_stream(session_id: str, message: str):
    """SSE 事件流生成器"""

    # 获取当前基准版本的 HTML
    session = session_service.get_session(session_id)
    if session is None:
        yield f"event: error\ndata: {json.dumps({'content': 'Session not found'})}\n\n"
        return

    base_version = session.current_base_version
    base_html = ""
    if base_version > 0:
        html = version_service.get_html(session_id, base_version)
        if html:
            base_html = html

    # 保存用户消息
    session_service.add_message(session_id, "user", message)

    # 发送 thinking 事件
    yield f"event: thinking\ndata: {json.dumps({'content': '正在分析需求...'})}\n\n"
    await asyncio.sleep(0.1)

    # 构建工作流输入
    state_input = {
        "user_message": message,
        "session_id": session_id,
        "base_html": base_html,
        "task_list": [],
        "current_html": "",
        "validation_errors": [],
        "iteration_count": 0,
        "fix_count": 0,
        "response_message": "",
        "output_html": "",
        "output_version": 0,
        "is_complete": False,
    }

    # 发送 tool_call 事件
    yield f"event: tool_call\ndata: {json.dumps({'tool': 'analyze_requirement', 'args': {'message': message}})}\n\n"
    await asyncio.sleep(0.1)

    # 执行工作流
    result = await pageforge_graph.ainvoke(state_input)

    # 发送 tool_result 事件
    yield f"event: tool_result\ndata: {json.dumps({'tool': 'analyze_requirement', 'result': result.get('task_list', [])})}\n\n"
    await asyncio.sleep(0.1)

    # 发送 tool_call 事件（生成 HTML）
    yield f"event: tool_call\ndata: {json.dumps({'tool': 'generate_html', 'args': {'task': result.get('task_list', [])}})}\n\n"
    await asyncio.sleep(0.1)

    # 发送 tool_result 事件
    yield f"event: tool_result\ndata: {json.dumps({'tool': 'generate_html', 'result': 'HTML generated'})}\n\n"
    await asyncio.sleep(0.1)

    # 发送 html_update 事件
    output_html = result.get("output_html", "")
    output_version = result.get("output_version", 0)
    yield f"event: html_update\ndata: {json.dumps({'html': output_html, 'version': output_version})}\n\n"
    await asyncio.sleep(0.1)

    # 发送 message 事件
    response_msg = result.get("response_message", "完成")
    yield f"event: message\ndata: {json.dumps({'content': response_msg})}\n\n"

    # 保存助手消息
    session_service.add_message(
        session_id, "assistant", response_msg,
        html_version=output_version,
    )

    # 发送 done 事件
    yield f"event: done\ndata: {json.dumps({'version': output_version})}\n\n"


@router.post("/{session_id}/messages")
async def send_message(session_id: str, req: MessageRequest):
    """发送消息 — SSE 流式响应"""
    session = session_service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return StreamingResponse(
        event_stream(session_id, req.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )