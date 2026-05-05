"""
Thinking Node — 思维链节点

LLM 思考过程，通过 SSE 推送 thinking_start / thinking_delta / thinking_end 事件。
"""

import logging
import time
from langchain_core.messages import SystemMessage, HumanMessage
from .event_emitter import (
    emit_thinking_start,
    emit_thinking_delta,
    emit_thinking_end,
)
from .llm_utils import stream_llm

logger = logging.getLogger(__name__)


# ========== Prompt 加载（统一管理） ==========
from app.prompts import load_prompt_with_identity

THINKING_SYSTEM_PROMPT = load_prompt_with_identity("02_thinking")


def thinking_node(state: dict) -> dict:
    """
    思维链节点函数

    输入: state["user_message"], state.get("intent"), state.get("tags")
    输出: state + thought_summary（思考内容通过 SSE 事件推送）
    """
    user_message = state.get("user_message", "")
    intent = state.get("intent", "unknown")
    tags = state.get("tags", [])

    logger.info(f"[Thinking] 开始思考（intent={intent}）")

    thinking_id = f"thinking_{int(time.time() * 1000)}"

    # 构建思考上下文
    context_parts = [f"用户想要: {user_message}"]
    if intent and intent != "unknown":
        context_parts.append(f"意图类型: {intent}")
    if tags:
        context_parts.append(f"技术标签: {', '.join(tags)}")
    context = "\n".join(context_parts)

    full_content = stream_llm(
        node_name="thinking",
        state=state,
        messages=[
            SystemMessage(content=THINKING_SYSTEM_PROMPT),
            HumanMessage(content=context),
        ],
        emit_start=lambda: emit_thinking_start(id=thinking_id),
        emit_delta=lambda chunk: emit_thinking_delta(id=thinking_id, delta=chunk),
        emit_end=lambda full: emit_thinking_end(
            id=thinking_id,
            content=full,
            summary=f"为 {intent} 需求分析了实现方案",
        ),
    )

    thought_summary = full_content[:200] if full_content else "已完成分析"

    logger.info(f"[Thinking] 思考完成，摘要: {thought_summary[:50]}...")

    return {
        **state,
        "thought_summary": thought_summary,
    }
