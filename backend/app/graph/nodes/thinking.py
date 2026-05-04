"""
Thinking Node — 思维链节点

LLM 思考过程，通过 SSE 推送 thinking_start / thinking_delta / thinking_end 事件。
SSE 事件由 messages.py 翻译层读取 state 后推送。
"""

import logging
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


THINKING_SYSTEM_PROMPT = """\
你是一个资深软件架构师，正在分析用户需求并思考实现方案。

请按以下结构进行思考：
1. 需求理解：用户想要什么？
2. 技术选型：需要哪些技术栈？
3. 架构设计：如何组织项目结构？
4. 实现步骤：分几步完成？

保持思考简洁，每个部分 2-3 句话即可。
"""


def thinking_node(state: dict) -> dict:
    """
    思维链节点函数
    
    输入: state["user_message"], state.get("intent"), state.get("tags")
    输出: state（思考内容通过 SSE 事件推送，不写入 state）
    """
    user_message = state.get("user_message", "")
    intent = state.get("intent", "unknown")
    tags = state.get("tags", [])

    logger.info(f"[Thinking] 开始思考（intent={intent}）")

    # TODO: 调用 LLM 进行思考
    # 当前为占位实现，实际应：
    # 1. 调用 LLM 生成思考内容
    # 2. 通过 SSE 推送 thinking_start / thinking_delta / thinking_end
    # 3. 思考摘要存入 state 供后续使用

    logger.info("[Thinking] 思考完成（占位实现）")

    return {
        **state,
        "thought_summary": f"正在为 {intent} 类型的需求设计实现方案",
    }
