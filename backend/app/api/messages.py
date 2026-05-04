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

    # 根据项目类型选择图
    is_new_project = getattr(session, 'project_type', None) == "react-vite-app"

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
        yield "event: MESSAGE_START\ndata: {}\n\n"

        # 根据项目类型选择图
        if is_new_project:
            try:
                from app.graph.graph_v2 import pageforge_graph_v2
                graph = pageforge_graph_v2
            except ImportError:
                graph = pageforge_graph
        else:
            graph = pageforge_graph

        async for event in graph.astream_events(
            state_input,
            version="v2",
        ):
            kind = event["event"]
            name = event.get("name", "")
            node = event.get("metadata", {}).get("langgraph_node", "")

            # ========== v2 图新事件处理 ==========
            if is_new_project:
                # 自定义事件：来自节点的 get_stream_writer()（intent_router / style_picker 等）
                if kind == "on_custom_event":
                    custom_data = event.get("data", {})
                    sse_event = custom_data.get("event", "")
                    sse_data = custom_data.get("data", {})
                    if sse_event:
                        yield ("event: " + sse_event +
                               "\ndata: " + json.dumps(sse_data, ensure_ascii=False) +
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

            # ========== 原有逻辑（v1 图或 v2 图的旧事件） ==========
            # ---- LLM 开始 ----
            if kind == "on_chat_model_start" and node == "execute":
                llm_call_count += 1
                if llm_call_count == 1:
                    label = "正在分析需求..."
                elif llm_call_count == 2:
                    label = "正在规划页面结构..."
                else:
                    label = f"正在优化调整（第 {llm_call_count - 1} 轮）..."
                payload = json.dumps({
                    "block_id": reasoning_bid,
                    "block_type": "reasoning",
                    "content": "\n" + label,
                })
                yield f"event: REASONING_CHUNK\ndata: {payload}\n\n"

            # ---- LLM 流式输出 ----
            elif kind == "on_chat_model_stream" and node == "execute":
                chunk = event["data"].get("chunk", {})
                if hasattr(chunk, "content") and chunk.content:
                    content_chunk = chunk.content

                    # 已在 HTML 模式 — 全部走 HTML_STREAM
                    if in_html_mode:
                        if "```" in content_chunk and len(content_chunk.strip()) <= 3:
                            in_html_mode = False
                            expecting_html = False
                            if generation_bid:
                                payload = json.dumps({
                                    "block_id": generation_bid,
                                    "block_type": "generation",
                                    "status": "done",
                                })
                                yield f"event: GENERATION_DONE\ndata: {payload}\n\n"
                                generation_bid = None
                        else:
                            yield "event: HTML_STREAM\ndata: " + json.dumps({"content": content_chunk}) + "\n\n"
                        continue

                    # expecting_html 但还没检测到 HTML — 缓冲累积
                    if expecting_html and not in_html_mode:
                        html_prefix_buffer += content_chunk
                        if "```html" in html_prefix_buffer:
                            if not in_html_mode:
                                payload = json.dumps({
                                    "block_id": generation_bid,
                                    "block_type": "generation",
                                    "status": "loading",
                                })
                                yield f"event: GENERATION_START\ndata: {payload}\n\n"
                            in_html_mode = True
                            parts = html_prefix_buffer.split("```html", 1)
                            after = parts[1] if len(parts) > 1 else ""
                            html_prefix_buffer = ""
                            if after.strip():
                                yield "event: HTML_STREAM\ndata: " + json.dumps({"content": after}) + "\n\n"
                            continue
                        elif "<!DOCTYPE" in html_prefix_buffer or "<html" in html_prefix_buffer.lower():
                            if not in_html_mode:
                                payload = json.dumps({
                                    "block_id": generation_bid,
                                    "block_type": "generation",
                                    "status": "loading",
                                })
                                yield f"event: GENERATION_START\ndata: {payload}\n\n"
                            in_html_mode = True
                            yield "event: HTML_STREAM\ndata: " + json.dumps({"content": html_prefix_buffer}) + "\n\n"
                            html_prefix_buffer = ""
                            continue
                        continue

                    # 普通文本 — 过滤空白
                    if content_chunk.strip():
                        payload = json.dumps({"block_type": "text", "content": content_chunk})
                        yield f"event: CHUNK_DELTA\ndata: {payload}\n\n"

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

                expecting_html = False
                html_prefix_buffer = ""

                if in_html_mode:
                    in_html_mode = False
                    if generation_bid:
                        payload = json.dumps({
                            "block_id": generation_bid,
                            "block_type": "generation",
                            "status": "done",
                        })
                        yield f"event: GENERATION_DONE\ndata: {payload}\n\n"
                        generation_bid = None

                reasoning_payload = json.dumps({
                    "block_id": reasoning_bid,
                    "block_type": "reasoning",
                    "content": f"\n正在调用 {tool_name} 工具...",
                })
                yield f"event: REASONING_CHUNK\ndata: {reasoning_payload}\n\n"

                tool_bid = next_bid()
                tool_payload = json.dumps({
                    "block_id": tool_bid,
                    "block_type": "tool_call",
                    "tool": tool_name,
                    "args": display_args,
                })
                yield f"event: TOOL_CALL\ndata: {tool_payload}\n\n"

            # ---- 工具调用结束 ----
            elif kind == "on_tool_end":
                tool_name = name
                result = event["data"].get("output", "")
                result_str = str(result)
                if len(result_str) > 300:
                    result_str = result_str[:300] + "..."

                if tool_bid:
                    payload = json.dumps({
                        "block_id": tool_bid,
                        "block_type": "tool_call",
                        "tool": tool_name,
                        "result": result_str,
                    })
                    yield f"event: TOOL_RESULT\ndata: {payload}\n\n"

                reasoning_done_payload = json.dumps({
                    "block_id": reasoning_bid,
                    "block_type": "reasoning",
                    "content": f"\n{tool_name} 工具调用完成",
                })
                yield f"event: REASONING_CHUNK\ndata: {reasoning_done_payload}\n\n"

                # skill 工具调用完成后，下一轮 LLM 输出预期是 HTML
                if "skill_" in tool_name:
                    expecting_html = True

            # ---- 工作流结束 ----
            elif kind == "on_chain_end" and name == "LangGraph":
                final_state = event["data"].get("output", {})

        # 强制收尾未结束的状态
        if in_html_mode and generation_bid:
            payload = json.dumps({
                "block_id": generation_bid,
                "block_type": "generation",
                "status": "done",
            })
            yield f"event: GENERATION_DONE\ndata: {payload}\n\n"

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
