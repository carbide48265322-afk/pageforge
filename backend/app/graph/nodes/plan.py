"""
Plan Node — 计划制定节点

根据意图和思考结果，制定具体的执行计划。
通过 SSE 推送 plan_start / plan_update / plan_done 事件。
"""

import logging
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


PLAN_SYSTEM_PROMPT = """\
你是一个项目规划师，负责将用户需求拆解为可执行的步骤列表。

## 输出格式（严格 JSON）
{
  "steps": [
    {"id": 1, "label": "步骤描述"},
    ...
  ]
}

## 要求
- 步骤数量 3~8 个
- 每个步骤描述清晰、可验证
- 按照依赖顺序排列（先做的基础步骤在前）
- 保持步骤粒度适中（不要太细也不要太粗）
"""


def plan_node(state: dict) -> dict:
    """
    计划节点函数
    
    输入: state["user_message"], state.get("thought_summary"), state.get("tags")
    输出: state + plan_steps (供后续节点使用)
    """
    user_message = state.get("user_message", "")
    thought_summary = state.get("thought_summary", "")
    tags = state.get("tags", [])

    logger.info(f"[Plan] 开始制定计划")

    # TODO: 调用 LLM 生成计划步骤
    # 当前为占位实现

    # 默认计划（占位）
    plan_steps = [
        {"id": 1, "label": "初始化项目结构"},
        {"id": 2, "label": "生成核心组件"},
        {"id": 3, "label": "添加样式和交互"},
        {"id": 4, "label": "启动预览服务"},
    ]

    logger.info(f"[Plan] 计划制定完成，共 {len(plan_steps)} 个步骤")

    return {
        **state,
        "plan_steps": plan_steps,
    }
