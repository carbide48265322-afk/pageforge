"""
PageForge LLM 流式调用公共工具

为 thinking/plan/reply 等节点提供统一的流式 LLM 调用模板。
"""

import logging
from typing import Callable
from langchain_core.messages import BaseMessage
from app.core.model_router import get_model_for_node

logger = logging.getLogger(__name__)


def stream_llm(
    node_name: str,
    state: dict,
    messages: list[BaseMessage],
    emit_start: Callable,
    emit_delta: Callable[[str], None],
    emit_end: Callable[[str], None],
) -> str:
    """
    统一流式 LLM 调用模板。

    各节点使用示例:
        full_text = stream_llm(
            node_name="reply",
            state=state,
            messages=[SystemMessage(prompt), HumanMessage(msg)],
            emit_start=lambda: emit_text_start(id=text_id),
            emit_delta=lambda chunk: emit_text_delta(id=text_id, content=chunk),
            emit_end=lambda full: emit_text_done(id=text_id, content=full),
        )

    Args:
        node_name: 节点名称（用于路由选择模型）
        state: 当前 AgentState
        messages: 发送给 LLM 的消息列表
        emit_start: 推送开始事件（无参回调）
        emit_delta: 推送增量事件（接收 chunk 文本）
        emit_end: 推送结束事件（接收完整文本）

    Returns:
        完整响应文本
    """
    llm = get_model_for_node(node_name, state)
    logger.debug(f"[stream_llm] node={node_name}, model={getattr(llm, 'model_name', '?')}")

    emit_start()

    chunks: list[str] = []
    try:
        for chunk in llm.stream(messages):
            text = getattr(chunk, "content", str(chunk))
            if text:
                chunks.append(text)
                emit_delta(text)
    except Exception as e:
        logger.error(f"[stream_llm] LLM 调用失败 node={node_name}: {e}", exc_info=True)
        # 降级：返回已收集内容
        if not chunks:
            chunks.append(f"[生成失败: {e}]")

    full_text = "".join(chunks)
    emit_end(full_text)
    return full_text
