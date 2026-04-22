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
    """SSE 事件流 — 扁平事件模型

    事件类型:
    - MESSAGE_START:   消息开始
    - REASONING_CHUNK: 思考内容增量
    - TOOL_CALL:       工具调用开始
    - TOOL_RESULT:     工具调用结束
    - GENERATION_START:HTML 生成开始（骨架屏）
    - GENERATION_DONE: HTML 生成完成
    - CHUNK_DELTA:     文本增量（打字机效果）
    - HTML_UPDATE:     最终 HTML（预览 iframe）
    - MESSAGE_FINISH:  消息结束
    - PING:            心跳保活
    - ERROR:           错误
    """
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
        # 固定 block_id 策略
        reasoning_bid = "blk_reasoning"
        tool_bid = None
        generation_bid = None
        block_counter = 0
        llm_call_count = 0
        # HTML 输出检测状态
        expecting_html = False   # generate_html/modify_html 工具调用后置为 True
        in_html_mode = False     # 检测到 HTML 内容后进入 HTML 模式
        html_prefix_buffer = ""  # expecting_html 时累积内容，用于检测跨 chunk 的标记

        def next_bid():
            nonlocal block_counter
            block_counter += 1
            return f"blk_{block_counter}"

        # 消息开始
        yield f"event: MESSAGE_START\ndata: {{}}\n\n"

        async for event in pageforge_graph.astream_events(
            state_input,
            version="v2",
        ):
            kind = event["event"]
            name = event.get("name", "")
            node = event.get("metadata", {}).get("langgraph_node", "")

            # ---- LLM 开始 ----
            if kind == "on_chat_model_start" and node == "execute":
                llm_call_count += 1
                if llm_call_count == 1:
                    label = "正在分析需求..."
                elif llm_call_count == 2:
                    label = "正在规划页面结构..."
                else:
                    label = f"正在优化调整（第 {llm_call_count - 1} 轮）..."
                yield f"event: REASONING_CHUNK\ndata: {json.dumps({'block_id': reasoning_bid, 'block_type': 'reasoning', 'content': '\n' + label})}\n\n"

            # ---- LLM 流式输出 ----
            elif kind == "on_chat_model_stream" and node == "execute":
                chunk = event["data"].get("chunk", {})
                if hasattr(chunk, "content") and chunk.content:
                    content = chunk.content

                    # 已在 HTML 模式 — 全部走 HTML_STREAM
                    if in_html_mode:
                        # 检测代码块结束标记
                        if "```" in content and len(content.strip()) <= 3:
                            # 纯 ``` 结束标记
                            in_html_mode = False
                            expecting_html = False
                            if generation_bid:
                                yield f"event: GENERATION_DONE\ndata: {json.dumps({'block_id': generation_bid, 'block_type': 'generation', 'status': 'done'})}\n\n"
                                generation_bid = None
                        else:
                            yield f"event: HTML_STREAM\ndata: {json.dumps({'content': content})}\n\n"
                        continue

                    # expecting_html 但还没检测到 HTML — 缓冲累积，检测跨 chunk 标记
                    if expecting_html and not in_html_mode:
                        html_prefix_buffer += content
                        # 检测完整标记
                        if "```html" in html_prefix_buffer:
                            if not in_html_mode:
                                yield f"event: GENERATION_START\ndata: {json.dumps({'block_id': generation_bid, 'block_type': 'generation', 'status': 'loading'})}\n\n"
                            in_html_mode = True
                            parts = html_prefix_buffer.split("```html", 1)
                            after = parts[1] if len(parts) > 1 else ""
                            html_prefix_buffer = ""
                            if after.strip():
                                yield f"event: HTML_STREAM\ndata: {json.dumps({'content': after})}\n\n"
                            continue
                        elif "<!DOCTYPE" in html_prefix_buffer or "<html" in html_prefix_buffer.lower():
                            if not in_html_mode:
                                yield f"event: GENERATION_START\ndata: {json.dumps({'block_id': generation_bid, 'block_type': 'generation', 'status': 'loading'})}\n\n"
                            in_html_mode = True
                            yield f"event: HTML_STREAM\ndata: {json.dumps({'content': html_prefix_buffer})}\n\n"
                            html_prefix_buffer = ""
                            continue
                        # 缓冲中还没检测到，不发送（防止 ```html 碎片渲染到对话区）
                        continue

                    # 普通文本 — 过滤空白
                    if content.strip():
                        yield f"event: CHUNK_DELTA\ndata: {json.dumps({'block_type': 'text', 'content': content})}\n\n"

            # ---- 工具调用开始 ----
            elif kind == "on_tool_start":
                tool_name = name
                tool_args = event["data"].get("input", {})
                display_args = {}
                for k, v in tool_args.items():
                    if isinstance(v, str) and len(v) > 200:
                        display_args[k] = v[:200] + "..."
                    else:
                        display_args[k] = v

                # 任意工具开始 → 重置 HTML 检测状态
                expecting_html = False
                html_prefix_buffer = ""

                if in_html_mode:
                    in_html_mode = False
                    if generation_bid:
                        yield f"event: GENERATION_DONE\ndata: {json.dumps({'block_id': generation_bid, 'block_type': 'generation', 'status': 'done'})}\n\n"
                        generation_bid = None

                yield f"event: REASONING_CHUNK\ndata: {json.dumps({'block_id': reasoning_bid, 'block_type': 'reasoning', 'content': f'\n正在调用 {tool_name} 工具...'})}\n\n"

                tool_bid = next_bid()
                yield f"event: TOOL_CALL\ndata: {json.dumps({'block_id': tool_bid, 'block_type': 'tool_call', 'tool': tool_name, 'args': display_args})}\n\n"

            # ---- 工具调用结束 ----
            elif kind == "on_tool_end":
                tool_name = name
                result = event["data"].get("output", "")
                result_str = str(result)
                if len(result_str) > 300:
                    result_str = result_str[:300] + "..."

                if tool_bid:
                    yield f"event: TOOL_RESULT\ndata: {json.dumps({'block_id': tool_bid, 'block_type': 'tool_call', 'tool': tool_name, 'result': result_str})}\n\n"

                yield f"event: REASONING_CHUNK\ndata: {json.dumps({'block_id': reasoning_bid, 'block_type': 'reasoning', 'content': f'\n{tool_name} 工具调用完成'})}\n\n"

                # skill 工具调用完成后，下一轮 LLM 输出预期是 HTML
                if "skill_" in tool_name:
                    expecting_html = True

            # ---- 工作流结束 ----
            elif kind == "on_chain_end" and name == "LangGraph":
                final_state = event["data"].get("output", {})

        # 强制收尾未结束的状态
        if in_html_mode and generation_bid:
            yield f"event: GENERATION_DONE\ndata: {json.dumps({'block_id': generation_bid, 'block_type': 'generation', 'status': 'done'})}\n\n"

        # 收尾
        if final_state:
            output_html = final_state.get("output_html", "")
            output_version = final_state.get("output_version", 0)
            response_msg = final_state.get("response_message", "")

            if output_html:
                yield f"event: HTML_UPDATE\ndata: {json.dumps({'html': output_html, 'version': output_version})}\n\n"

            if response_msg:
                yield f"event: CHUNK_DELTA\ndata: {json.dumps({'block_type': 'text', 'content': response_msg})}\n\n"

            session_service.add_message(
                session_id, "assistant",
                response_msg or "完成",
                html_version=output_version,
            )

        yield f"event: done\ndata: {{}}\n\n"

    except Exception as e:
        yield f"event: ERROR\ndata: {json.dumps({'content': str(e)})}\n\n"

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