import json
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.graph.graph_v2 import pageforge_graph_v2 as pageforge_graph
from app.services.session_service import SessionService
from app.services.version_service import VersionService

router = APIRouter()
session_service = SessionService()
version_service = VersionService()


class MessageRequest(BaseModel):
    message: str


async def event_stream(session_id: str, message: str):
    """SSE 事件流 — 扁平事件模型

    事件类型:
    - MESSAGE_START:   消息开始
    - REASONING_CHUNK: 思考内容增量
    - TOOL_CALL:       工具调用开始
    - TOOL_RESULT:     工具调用结束
    - GENERATION_START: HTML 生成开始（骨架屏）
    - GENERATION_DONE:  HTML 生成完成
    - CHUNK_DELTA:     文本增量（打字机效果）
    - HTML_UPDATE:     最终 HTML（预览 iframe）
    - MESSAGE_FINISH:  消息结束
    - PING:            心跳保活
    - ERROR:           错误
    - v2 新增:         intent:start/result, plan_*, tool_call:*, file_*, status:*, style_selected
    """
    session = session_service.get_session(session_id)
    if session is None:
        yield "event: error\ndata: " + json.dumps({"content": "Session not found"}) + "\n\n"
        return

    base_version = session.current_base_version
    base_html = ""
    if base_version > 0:
        html = version_service.get_html(session_id, base_version)
        if html:
            base_html = html

    session_service.add_message(session_id, "user", message)

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

    try:
        # 消息开始
        yield "event: MESSAGE_START\ndata: {}\n\n"

        final_state = None

        async for event in pageforge_graph.astream_events(
            state_input,
            version="v2",
        ):
            kind = event["event"]

            # ========== v2 事件处理 ==========
            # 自定义事件：来自节点的 get_stream_writer()（intent_router / style_picker 等）
            # 统一格式：writer 写入 {"event": "message", "data": {"type": "thinking_delta", ...}}
            # 我们直接透传 data 部分，SSE event 字段固定为 "message"
            if kind == "on_custom_event":
                custom_data = event.get("data", {})
                inner_event = custom_data.get("event", "")
                inner_data = custom_data.get("data", {})
                if inner_event == "message":
                    # 新格式：data.type 携带细分类型
                    yield ("event: message\n" +
                           "data: " + json.dumps(inner_data, ensure_ascii=False) +
                           "\n\n")
                elif inner_event:
                    # 旧格式兼容：直接透传
                    yield ("event: " + inner_event +
                           "\ndata: " + json.dumps(inner_data, ensure_ascii=False) +
                           "\n\n")
                continue

            # 备用兼容：意图识别事件（旧格式）
            if kind == "on_intent_recognized":
                data_str = json.dumps(event.get("data", {}), ensure_ascii=False)
                yield f"event: INTENT_RESULT\ndata: {data_str}\n\n"
                continue

            # 计划事件
            if kind == "on_plan_update":
                data_str = json.dumps(event.get("data", {}), ensure_ascii=False)
                yield f"event: PLAN_UPDATE\ndata: {data_str}\n\n"
                continue

            # 文件事件
            if kind == "on_file_created":
                data_str = json.dumps(event.get("data", {}), ensure_ascii=False)
                yield f"event: FILE_CREATED\ndata: {data_str}\n\n"
                continue

            # 状态机事件
            if kind == "on_status_update":
                data_str = json.dumps(event.get("data", {}), ensure_ascii=False)
                yield f"event: STATUS_UPDATE\ndata: {data_str}\n\n"
                continue

            # 工作流结束
            if kind == "on_chain_end":
                final_state = event["data"].get("output", {})

        # 收尾
        if final_state:
            output_html = final_state.get("output_html", "")
            output_version = final_state.get("output_version", 0)
            response_msg = final_state.get("response_message", "")

            if output_html:
                payload = json.dumps({"html": output_html, "version": output_version})
                yield f"event: HTML_UPDATE\ndata: {payload}\n\n"

            if response_msg:
                payload = json.dumps({"block_type": "text", "content": response_msg})
                yield f"event: CHUNK_DELTA\ndata: {payload}\n\n"

            session_service.add_message(
                session_id, "assistant",
                response_msg or "完成",
                html_version=output_version,
            )

        yield "event: done\ndata: {}\n\n"

    except Exception as e:
        yield "event: ERROR\ndata: " + json.dumps({"content": str(e)}) + "\n\n"


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
            "Access-Control-Allow-Origin": "*",
            "Content-Encoding": "none",
        },
    )
