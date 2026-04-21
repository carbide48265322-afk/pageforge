import json
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.graph.graph import pageforge_graph
from app.services.session_service import SessionService
from app.services.version_service import VersionService
from app.checkpoint.manager import CheckpointManager

router = APIRouter()
session_service = SessionService()
version_service = VersionService()
checkpoint_manager = CheckpointManager()


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
        "created_at": session.created_at,
        "phase": "start",
        "stage": "start",
        "project_config": {},
        "design_concept": "",
        "conception_doc": "",
        "demo_html": "",
        "demo_instructions": "",
        "demo_link": "",
        "is_demo_ready": False,
        "task_list": [],
        "current_html": "",
        "validation_errors": [],
        "iteration_count": 0,
        "fix_count": 0,
        "response_message": "",
        "output_html": "",
        "output_version": 0,
        "is_complete": False,
        # 人机协作字段
        "human_input_pending": False,
        "human_input_checkpoint_id": None,
        "human_input_response": None,
        "prd_revision_count": 0,
        "prd_internal_iteration": 0,
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

            # ---- 阶段处理 ----
            if kind == "on_chat_model_start":
                if node == "start":
                    yield f"event: REASONING_CHUNK\ndata: {json.dumps({'block_id': reasoning_bid, 'block_type': 'reasoning', 'content': '\n正在初始化项目...'})}\n\n"
                elif node == "ideate":
                    yield f"event: REASONING_CHUNK\ndata: {json.dumps({'block_id': reasoning_bid, 'block_type': 'reasoning', 'content': '\n正在构想项目设计...'})}\n\n"
                elif node == "demo":
                    yield f"event: REASONING_CHUNK\ndata: {json.dumps({'block_id': reasoning_bid, 'block_type': 'reasoning', 'content': '\n正在准备项目演示...'})}\n\n"
                elif node == "execute":
                    llm_call_count += 1
                    if llm_call_count == 1:
                        label = "正在分析需求..."
                    elif llm_call_count == 2:
                        label = "正在规划页面结构..."
                    else:
                        label = f"正在优化调整（第 {llm_call_count - 1} 轮）..."
                    yield f"event: REASONING_CHUNK\ndata: {json.dumps({'block_id': reasoning_bid, 'block_type': 'reasoning', 'content': '\n' + label})}\n\n"

            # ---- LLM 流式输出 ----
            elif kind == "on_chat_model_stream":
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

            # ---- 人机协作检查点 ----
            elif kind == "on_chain_end" and name == "human_input":
                # 人机协作节点结束，发送 HUMAN_INPUT_REQUEST 事件
                node_output = event["data"].get("output", {})
                if node_output.get("human_input_request"):
                    yield f"event: HUMAN_INPUT_REQUEST\ndata: {json.dumps(node_output['human_input_request'])}\n\n"

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
            conception_doc = final_state.get("conception_doc", "")
            demo_link = final_state.get("demo_link", "")
            demo_html = final_state.get("demo_html", "")

            if output_html:
                yield f"event: HTML_UPDATE\ndata: {json.dumps({'html': output_html, 'version': output_version})}\n\n"

            if conception_doc:
                yield f"event: CHUNK_DELTA\ndata: {json.dumps({'block_type': 'text', 'content': f'\n## 项目构想\n{conception_doc}'})}\n\n"

            if demo_link:
                yield f"event: CHUNK_DELTA\ndata: {json.dumps({'block_type': 'text', 'content': f'\n## 项目演示\n演示链接: {demo_link}'})}\n\n"

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

async def resume_stream(session_id: str, checkpoint_id: str, user_message: str):
    """从检查点恢复执行 — SSE 流式响应
    
    当用户响应了人机协作检查点后，从检查点恢复图执行。
    """
    from datetime import datetime
    
    checkpoint = await checkpoint_manager.load(checkpoint_id)
    if not checkpoint:
        yield f"event: ERROR\ndata: {json.dumps({'content': 'Checkpoint not found'})}\n\n"
        return
    
    # 获取用户响应
    response = checkpoint.get("human_input_response")
    if not response:
        yield f"event: ERROR\ndata: {json.dumps({'content': 'No response found for checkpoint'})}\n\n"
        return
    
    # 重建 State
    state_input = {
        "user_message": user_message,
        "session_id": session_id,
        "base_html": checkpoint.get("state", {}).get("base_html", ""),
        "task_list": checkpoint.get("state", {}).get("task_list", []),
        "current_html": checkpoint.get("state", {}).get("current_html", ""),
        "validation_errors": [],
        "iteration_count": 0,
        "fix_count": 0,
        "response_message": "",
        "output_html": "",
        "output_version": 0,
        "is_complete": False,
        # 人机协作字段 - 用户已响应，不再等待
        "human_input_pending": False,
        "human_input_checkpoint_id": checkpoint_id,
        "human_input_response": response,
        "prd_revision_count": checkpoint.get("state", {}).get("prd_revision_count", 0),
        "prd_internal_iteration": 0,
        # 根据用户操作设置状态
        "requirements_approved": response.get("action") == "confirm",
        "prd_feedback": response.get("data", {}).get("feedback", "") if response.get("action") == "revise" else "",
    }
    
    # 继续执行图（从 execute 节点开始，跳过 intent 和 human_input）
    try:
        yield f"event: MESSAGE_START\ndata: {{}}\n\n"
        
        # 根据用户操作发送不同的提示
        if response.get("action") == "confirm":
            yield f"event: REASONING_CHUNK\ndata: {json.dumps({'block_id': 'blk_reasoning', 'block_type': 'reasoning', 'content': '\n用户已确认需求，继续执行...'})}\n\n"
        elif response.get("action") == "revise":
            yield f"event: REASONING_CHUNK\ndata: {json.dumps({'block_id': 'blk_reasoning', 'block_type': 'reasoning', 'content': '\n用户要求修改，重新生成 PRD...'})}\n\n"
        
        # 执行图（简化版，直接执行后续节点）
        async for event in pageforge_graph.astream_events(
            state_input,
            version="v2",
        ):
            kind = event["event"]
            name = event.get("name", "")
            
            # 处理各种事件类型（简化处理，复用 event_stream 的逻辑）
            if kind == "on_chat_model_start":
                yield f"event: REASONING_CHUNK\ndata: {json.dumps({'block_id': 'blk_reasoning', 'block_type': 'reasoning', 'content': '\n正在生成页面...'})}\n\n"
            
            elif kind == "on_chat_model_stream":
                chunk = event["data"].get("chunk", {})
                if hasattr(chunk, "content") and chunk.content:
                    content = chunk.content
                    if content.strip():
                        yield f"event: CHUNK_DELTA\ndata: {json.dumps({'block_type': 'text', 'content': content})}\n\n"
            
            elif kind == "on_chain_end" and name == "LangGraph":
                final_state = event["data"].get("output", {})
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
    """发送消息 — SSE 流式响应
    
    如果存在等待中的人机协作检查点，则将用户消息作为响应提交并恢复执行。
    否则，作为普通消息处理。
    """
    session = session_service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 检查是否有等待的人机协作检查点
    waiting = await checkpoint_manager.get_waiting_checkpoints(session_id)
    
    if waiting:
        # 有等待的检查点，解析用户消息作为响应
        try:
            response_data = json.loads(req.message)
            checkpoint_id = waiting[0]["checkpoint_id"]
            
            # 提交用户响应
            await checkpoint_manager.submit_human_response(
                checkpoint_id=checkpoint_id,
                action=response_data.get("action", "confirm"),
                data=response_data
            )
            
            # 从检查点恢复执行
            return StreamingResponse(
                resume_stream(session_id, checkpoint_id, req.message),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
        except json.JSONDecodeError:
            # 用户消息不是 JSON，当作普通消息处理
            pass
    
    # 普通消息处理
    return StreamingResponse(
        event_stream(session_id, req.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )