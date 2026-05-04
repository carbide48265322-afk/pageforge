"""
Reply Node — 文本回复节点

处理 chat/unknown 意图的直接回复，以及 code_gen 完成后的总结回复。
通过 SSE 推送 text_start / text_delta / text_end 事件。
"""

import logging
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


REPLY_SYSTEM_PROMPT = """\
你是一个友好的 AI 助手，负责回复用户。

## 回复要求
- 简洁明了，不要太长
- 技术类问题要准确
- 如果是代码生成完成，简要说明生成了什么
- 合理使用 markdown 格式（加粗、列表）
"""


def reply_node(state: dict) -> dict:
    """
    回复节点函数
    
    输入: state["user_message"], state.get("intent"), state.get("files")
    输出: state + response_message
    """
    user_message = state.get("user_message", "")
    intent = state.get("intent", "unknown")
    files = state.get("files", [])

    logger.info(f"[Reply] 开始生成回复（intent={intent}）")

    # TODO: 调用 LLM 生成回复
    # 当前为占位实现
    
    if intent == "chat":
        response = f"你好！我是 PageForge，有什么可以帮你的吗？"
    elif intent == "code_gen":
        file_count = len(files) if files else 0
        response = f"✅ 已成功生成项目，共 {file_count} 个文件。预览很快就会就绪！"
    else:
        response = "已完成处理。"

    logger.info(f"[Reply] 回复完成")

    return {
        **state,
        "response_message": response,
        "is_complete": True,
    }
