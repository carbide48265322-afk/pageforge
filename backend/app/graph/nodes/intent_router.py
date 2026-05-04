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


# ========== 意图识别系统 Prompt ==========

INTENT_SYSTEM_PROMPT = """\
你是 PageForge 的意图路由器。分析用户输入，返回 JSON 格式的分类结果。

## 意图分类
- chat: 纯对话（问候、闲聊、提问概念、不涉及代码生成）
- code_gen: 一句话生成应用（"做个Todo"、"帮我建个博客"、"生成一个登录页面"）
- code_edit: 修改已有代码（"把按钮改成红色"、"加个搜索功能"、"优化性能"）
- explain: 解释代码或概念（"这段代码什么意思"、"什么是闭包"、"React useEffect 用法"）
- debug: 调试问题（"我的页面报错了"、"样式不对"、"打包失败"）
- file_operation: 文件操作（"删除这个文件"、"重命名"、"查看目录结构"）
- unknown: 无法判断

## 输出格式（严格 JSON，不要其他文字）
{
  "intent": "<分类>",
  "confidence": 0.0~1.0,
  "tags": ["<技术标签>"],
  "mode": "frontend|backend|fullstack|null",
  "complexity": "simple|medium|complex|null",
  "suggested_style": "<风格关键词，如 minimal/dark/glassmorphism/null>"
}

## 规则
1. confidence < 0.5 时 intent 设为 "unknown"
2. code_gen 类必须尝试提取 suggested_style（从描述中的风格线索推断，如"暗色系"→"dark"）
3. tags 尽量提取具体技术词（react/vite/tailwind/todo/crud 等）
4. mode 根据描述推断（前端项目→frontend，全栈→fullstack）
5. complexity 根据需求复杂度判断（单页→simple，多页→medium，复杂系统→complex）
"""

# ========== LLM 单例（延迟加载）==========

_llm = None

def _get_llm():
    """延迟加载 LLM，避免模块导入时就初始化"""
    global _llm
    if _llm is None:
        from app.config import settings
        from langchain_openai import ChatOpenAI
        _llm = ChatOpenAI(
            model=settings.llm_model or "gpt-4o-mini",  # 意图识别用小模型
            temperature=0.1,  # 低温度，确保分类稳定
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
    return _llm


# ========== 内置风格配置降级方案 ===========

_FALLBACK_STYLES = {
    "minimal": {
        "colors": {"primary": "#171717", "secondary": "#52525b", "background": "#ffffff", "accent": "#6366f1"},
        "typography": {"font_family": "'Inter', system-ui, sans-serif", "heading_weight": "600", "body_size": "14px"},
        "border_radius": "0.375rem",
        "shadows": {"sm": "0 1px 2px 0 rgb(0 0 0 / 0.05)"},
        "anti_patterns": ["不要用紫渐变", "不要用 Inter 之外的通用字体", "避免千篇一律的卡片设计"],
    },
    "dark": {
        "colors": {"primary": "#e2e8f0", "secondary": "#94a3b8", "background": "#0a0a0a", "accent": "#818cf8"},
        "typography": {"font_family": "'Inter', system-ui, sans-serif", "heading_weight": "700", "body_size": "14px"},
        "border_radius": "0.5rem",
        "shadows": {"sm": "0 1px 3px 0 rgb(255 255 255 / 0.1)"},
        "anti_patterns": ["不要用纯白文字", "避免使用蓝色系配色", "避免过亮的背景"],
    },
    "glassmorphism": {
        "colors": {"primary": "#6366f1", "secondary": "#8b5cf6", "background": "rgba(255,255,255,0.1)", "accent": "#f59e0b"},
        "typography": {"font_family": "'Inter', system-ui, sans-serif", "heading_weight": "600", "body_size": "14px"},
        "border_radius": "1rem",
        "shadows": {"sm": "0 8px 32px 0 rgb(31 38 135 / 0.37)"},
        "anti_patterns": ["不要用实色背景", "避免无透明度的元素", "不要过度使用模糊效果"],
    },
    "vibrant": {
        "colors": {"primary": "#f59e0b", "secondary": "#f97316", "background": "#fffbeb", "accent": "#ef4444"},
        "typography": {"font_family": "'Inter', system-ui, sans-serif", "heading_weight": "700", "body_size": "14px"},
        "border_radius": "0.75rem",
        "shadows": {"sm": "0 4px 6px -1px rgb(245 158 11 / 0.3)"},
        "anti_patterns": ["不要用灰色系", "避免过度设计", "不要使用小号字体"],
    },
}


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

    try:
        response = llm.invoke([
            SystemMessage(content=INTENT_SYSTEM_PROMPT),
            HumanMessage(content=user_message),
        ])

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
        logger.warning(f"[IntentRouter] LLM 解析失败，使用默认兜底: {e}")
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

    # 返回更新后的 state
    return {
        **state,
        "intent": intent,
        "confidence": confidence,
        "tags": tags,
        "mode": mode,
        "complexity": complexity,
        "ui_style": ui_style,
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
