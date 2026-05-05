"""
Plan Node — 计划制定节点

根据意图和思考结果，制定具体的执行计划。
通过 SSE 推送 plan_start / plan_update / plan_done 事件。
"""

import json
import logging
import time
from langchain_core.messages import SystemMessage, HumanMessage
from .event_emitter import (
    emit_plan_start,
    emit_plan_update,
    emit_plan_done,
)
from .llm_utils import stream_llm

logger = logging.getLogger(__name__)


# ========== Prompt 加载（统一管理） ==========
from app.prompts import load_prompt_with_identity

PLAN_SYSTEM_PROMPT = load_prompt_with_identity("03_plan")


def _parse_plan_steps(raw_text, intent: str) -> list[dict]:
    """
    从 LLM 返回的文本中解析 plan steps。
    解析失败时返回基于 intent 的内置降级方案。
    """
    # 防御：确保 raw_text 是字符串（streaming chunk 可能是其他类型）
    if not isinstance(raw_text, str):
        raw_text = str(raw_text) if raw_text is not None else ""

    # 尝试提取 JSON
    text = raw_text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    try:
        data = json.loads(text)
        steps = data.get("steps", [])
        if isinstance(steps, list) and len(steps) >= 2:
            logger.debug(f"[Plan] LLM 解析成功，{len(steps)} 个步骤")
            return steps
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        logger.warning(f"[Plan] LLM 输出 JSON 解析失败: {e}，使用降级方案")

    # 降级方案
    return _fallback_steps(intent)


def _fallback_steps(intent: str) -> list[dict]:
    """内置降级计划"""
    fallbacks = {
        "code_gen": [
            {"id": 1, "label": "初始化项目结构", "type": "init"},
            {"id": 2, "label": "生成核心组件", "type": "component"},
            {"id": 3, "label": "添加样式和交互", "type": "style"},
            {"id": 4, "label": "安装依赖并校验", "type": "deploy"},
        ],
        "code_edit": [
            {"id": 1, "label": "分析现有代码结构", "type": "init"},
            {"id": 2, "label": "执行代码修改", "type": "component"},
            {"id": 3, "label": "验证修改结果", "type": "test"},
        ],
    }
    return fallbacks.get(intent, [
        {"id": 1, "label": "分析需求", "type": "init"},
        {"id": 2, "label": "制定方案", "type": "component"},
        {"id": 3, "label": "执行完成", "type": "deploy"},
    ])


def plan_node(state: dict) -> dict:
    """
    计划节点函数

    输入: state["user_message"], state.get("thought_summary"), state.get("tags")
    输出: state + plan_steps (供后续节点使用)
    """
    user_message = state.get("user_message", "")
    intent = state.get("intent", "unknown")
    thought_summary = state.get("thought_summary", "")
    tags = state.get("tags", [])

    logger.info(f"[Plan] 开始制定计划（intent={intent}）")

    # ── 仅对 code_gen 和 code_edit 走 LLM 计划，其他意图直接用降级 ──
    if intent in ("code_gen", "code_edit"):
        plan_id = f"plan_{int(time.time() * 1000)}"

        context = (
            f"用户需求: {user_message}\n"
            f"意图: {intent}\n"
            f"思考结论: {thought_summary}\n"
            f"技术标签: {', '.join(tags)}"
        )

        full_text = stream_llm(
            node_name="plan",
            state=state,
            messages=[
                SystemMessage(content=PLAN_SYSTEM_PROMPT),
                HumanMessage(content=context),
            ],
            emit_start=lambda: emit_plan_start(id=plan_id, steps=[], current=0),
            emit_delta=lambda chunk: emit_plan_update(
                steps=_parse_plan_steps(chunk, intent),
                is_complete=False,
            ),
            emit_end=lambda full: emit_plan_done(
                steps=_parse_plan_steps(full, intent),
            ),
        )

        plan_steps = _parse_plan_steps(full_text, intent)
    else:
        # 非代码生成意图：直接降级
        plan_steps = _fallback_steps(intent)

    logger.info(f"[Plan] 计划制定完成，共 {len(plan_steps)} 个步骤")

    return {
        **state,
        "plan_steps": plan_steps,
    }
