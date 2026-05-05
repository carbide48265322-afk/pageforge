"""
Intent Router Node — P1.17
==========================

作为 graph_v2 的第一个节点，分析用户输入，决定后续走哪条分支。

实现方式：
- 使用 LLM 进行意图分类（轻量级，可用小模型）
- 结果写入 state（intent, confidence, tags, ui_style）
- SSE 事件（intent:result, intent:style_query）由 messages.py 翻译层读取 state 后推送

意图分类：
- chat: 纯对话（问候、闲聊、提问概念）
- code_gen: 一句话生成应用
- code_edit: 修改已有代码
- explain: 解释代码或概念
- debug: 调试问题
- file_operation: 文件操作
- unknown: 无法判断
"""

import json
import logging
from typing import TypedDict, Optional

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.config import get_stream_writer

logger = logging.getLogger(__name__)


# ========== Prompt 加载（统一管理） ==========
# 从 backend/app/prompts/*.md 加载，自动拼接全局身份（00_identity.md）
from app.prompts import load_prompt_with_identity

INTENT_SYSTEM_PROMPT = load_prompt_with_identity("01_intent_router")

# ========== LLM 获取（委托给 model_router）==========

def _get_llm():
    """获取意图识别专用 LLM（lite 级别）"""
    from app.core.model_router import get_intent_llm
    return get_intent_llm()


# ========== 内置风格配置降级方案 ==========
# 从 JSON 文件加载，与 style_picker 共享同一份 fallback 数据
import json as _json
import os as _os
_FALLBACK_STYLES_PATH = _os.path.join(
    _os.path.dirname(_os.path.abspath(__file__)),
    "..", "..", "prompts", "fallback_styles.json"
)
with open(_FALLBACK_STYLES_PATH, "r", encoding="utf-8") as _f:
    _FALLBACK_STYLES: dict = _json.load(_f)


# ========== 主节点函数 ===========

def intent_router(state: dict) -> dict:
    """
    意图识别节点函数
    
    输入: state["user_message"]
    输出: state + intent, confidence, tags, ui_style, etc.
    """
    user_message = state.get("user_message", "")
    logger.info(f"[IntentRouter] 开始识别意图: {user_message[:50]}...")

    # 通过 SSE 推送「开始识别」事件（使用 LangGraph stream_writer）
    try:
        writer = get_stream_writer()
        writer({
            "event": "intent:start",
            "data": {}
        })
    except Exception:
        pass  # 非流式模式忽略

    llm = _get_llm()

    logger.debug(f"[IntentRouter] 使用模型: {llm.model_name}")

    try:
        response = llm.invoke([
            SystemMessage(content=INTENT_SYSTEM_PROMPT),
            HumanMessage(content=user_message),
        ])

        logger.debug(f"[IntentRouter] LLM 原始响应: {response.content[:200]}...")

        # 解析 LLM 返回的 JSON
        content = response.content.strip()
        # 去除可能的 markdown 代码块包裹
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        result = json.loads(content)
        intent = result.get("intent", "unknown")
        confidence = float(result.get("confidence", 0.5))
        tags = result.get("tags", [])
        mode = result.get("mode")
        complexity = result.get("complexity")
        suggested_style = result.get("suggested_style")

        # confidence 过低时标记为 unknown
        if confidence < 0.5:
            intent = "unknown"

        logger.info(f"[IntentRouter] 识别结果: intent={intent}, confidence={confidence}, style={suggested_style}")

    except (json.JSONDecodeError, KeyError, Exception) as e:
        logger.error(f"[IntentRouter] LLM 调用异常: {type(e).__name__}: {e}", exc_info=True)
        intent = "unknown"
        confidence = 0.0
        tags = []
        mode = None
        complexity = None
        suggested_style = None

    # 确定 ui_style（风格关键词）
    ui_style = suggested_style or _infer_style_from_intent(intent, tags, user_message)
    
    # 通过 SSE 推送识别结果
    try:
        writer = get_stream_writer()
        writer({
            "event": "intent:result",
            "data": {
                "intent": intent,
                "confidence": confidence,
                "tags": tags,
                "mode": mode,
                "suggested_style": suggested_style,
            }
        })
    except Exception:
        pass

    # 如果需要征询风格偏好（code_gen 且无明确风格线索），推送 style_query
    if intent == "code_gen" and not suggested_style:
        try:
            writer = get_stream_writer()
            writer({
                "event": "intent:style_query",
                "data": {
                    "options": ["minimal", "vibrant", "dark", "glassmorphism"],
                    "auto_select": "minimal",
                    "timeout_ms": 5000,
                }
            })
        except Exception:
            pass

    # ── 智能路由：根据 intent + complexity 确定全局模型策略 ──
    from app.core.model_router import get_global_strategy
    model_strategy = get_global_strategy(intent, complexity)
    logger.info(f"[IntentRouter] 路由策略: {model_strategy}")

    # 返回更新后的 state
    return {
        **state,
        "intent": intent,
        "confidence": confidence,
        "tags": tags,
        "mode": mode,
        "complexity": complexity,
        "ui_style": ui_style,
        "model_strategy": model_strategy,
    }


# ========== 辅助函数 ===========

def _infer_style_from_intent(intent: str, tags: list, message: str) -> str:
    """
    根据意图、标签和消息内容推断合适的风格
    如果无法推断，返回 "minimal"（默认）
    """
    message_lower = message.lower()

    # 从消息内容直接匹配风格关键词
    style_keywords = {
        "dark": ["暗色", "暗黑", "黑色", "dark", "夜间", "黑夜"],
        "glassmorphism": ["玻璃", "透明", "glass", "glassmorphism", "毛玻璃"],
        "vibrant": ["鲜艳", "活泼", "彩色", "vibrant", "亮色", "多彩"],
        "minimal": ["极简", "简洁", "简约", "minimal", "简单"],
    }
    for style, keywords in style_keywords.items():
        if any(kw in message_lower for kw in keywords):
            return style

    # 根据项目类型推断
    if intent == "code_gen":
        if any(t in tags for t in ["admin", "dashboard", "management"]):
            return "minimal"  # 管理后台用极简
        if any(t in tags for t in ["portfolio", "showcase", "gallery"]):
            return "glassmorphism"  # 作品集用毛玻璃
        if any(t in tags for t in ["game", "entertainment", "fun"]):
            return "vibrant"  # 娱乐类用鲜艳

    # 默认
    return "minimal"


def get_fallback_style_config(style: str) -> dict:
    """
    获取内置降级风格配置（当 ui-ux-pro-max CLI 不可用时使用）
    """
    return _FALLBACK_STYLES.get(style, _FALLBACK_STYLES["minimal"])
