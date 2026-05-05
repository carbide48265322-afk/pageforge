"""
Reply Node — 文本回复节点

处理 chat/unknown 意图的直接回复，以及 code_gen 完成后的总结回复。
通过 SSE 推送 text_delta / text_done 事件。
"""

import logging
import time
from langchain_core.messages import SystemMessage, HumanMessage
from .event_emitter import (
    emit_text_delta,
    emit_text_done,
)
from .llm_utils import stream_llm

logger = logging.getLogger(__name__)


# ========== Prompt 加载（统一管理） ==========
from app.prompts import load_prompt_with_identity

REPLY_SYSTEM_PROMPT = load_prompt_with_identity("05_reply")


def _build_reply_context(state: dict) -> str:
    """根据 intent 和 state 构建上下文信息注入 prompt"""
    intent = state.get("intent", "unknown")
    parts = [f"[意图: {intent}]"]

    if intent == "code_gen":
        files = state.get("files", [])
        if files:
            file_list = "\n".join(f"- {f.get('path', '?')} ({f.get('language', '?')})" for f in files)
            parts.append(f"已生成 {len(files)} 个文件：\n{file_list}")
        install_status = state.get("install_status", "")
        if install_status:
            parts.append(f"依赖安装状态: {install_status}")
    elif intent == "code_edit":
        parts.append("已完成代码修改")
    elif intent == "explain":
        summary = state.get("thought_summary", "")
        if summary:
            parts.append(f"思考摘要: {summary}")

    parts.append(f"\n用户原始消息: {state.get('user_message', '')}")
    return "\n".join(parts)


def reply_node(state: dict) -> dict:
    """
    回复节点函数

    输入: state["user_message"], state.get("intent"), state.get("files")
    输出: state + response_message + is_complete
    """
    user_message = state.get("user_message", "")
    intent = state.get("intent", "unknown")

    logger.info(f"[Reply] 开始生成回复（intent={intent}）")

    text_id = f"text_{int(time.time() * 1000)}"

    # 构建 prompt
    context = _build_reply_context(state)
    messages = [
        SystemMessage(content=REPLY_SYSTEM_PROMPT),
        HumanMessage(content=context),
    ]

    # 通过 stream_llm 流式调用
    response = stream_llm(
        node_name="reply",
        state=state,
        messages=messages,
        emit_start=lambda: None,  # text 不推 start，只有 delta/done
        emit_delta=lambda chunk: emit_text_delta(id=text_id, content=chunk),
        emit_end=lambda full: emit_text_done(id=text_id, content=full),
    )

    if not response:
        response = "已完成处理，但没有生成具体内容。"

    logger.info(f"[Reply] 完成，长度={len(response)}")

    return {
        **state,
        "response_message": response,
        "is_complete": True,
    }
