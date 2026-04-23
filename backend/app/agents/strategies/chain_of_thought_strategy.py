from typing import List, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.config import llm
from .base_strategy import PlanningStrategy
from app.agents.task_analyzer import TaskAnalysis
from app.graph.state import AgentState

class ChainOfThoughtStrategy(PlanningStrategy):
    """Chain-of-Thought策略 - 引导式链式思考"""

    def get_name(self) -> str:
        return "chain_of_thought"

    def get_description(self) -> str:
        return "思维链模式：通过引导式链式思考解决复杂推理和创造性任务"

    def can_handle(self, analysis: TaskAnalysis) -> bool:
        return analysis.creativity > 0.5 or analysis.complexity > 0.6

    async def execute(self, state: AgentState, analysis: TaskAnalysis) -> AgentState:
        """执行Chain-of-Thought策略"""
        user_message = state["user_message"]

        # 构建思维链提示
        cot_prompt = self._build_cot_prompt(user_message, analysis)

        # 初始化思维链
        thoughts = []
        current_context = user_message

        # 思维链步骤
        max_steps = min(6, max(3, analysis.estimated_steps))

        for step in range(max_steps):
            # 生成下一步思考
            thought = await self._generate_thought(current_context, step + 1, analysis)
            thoughts.append(thought)

            # 更新上下文
            current_context = f"{current_context}\n\n思考步骤{step + 1}: {thought}"

            # 检查是否应该继续
            if self._should_continue_thinking(thought, step + 1, max_steps):
                continue
            else:
                break

        # 生成最终答案
        final_answer = await self._generate_final_answer(current_context, thoughts, analysis)

        final_result = {
            "strategy": "chain_of_thought",
            "thoughts": thoughts,
            "final_answer": final_answer,
            "domain": analysis.domain,
            "complexity": analysis.complexity,
            "creativity": analysis.creativity
        }

        return self.build_result(state, final_result)

    def _build_cot_prompt(self, user_message: str, analysis: TaskAnalysis) -> str:
        """构建思维链提示"""
        return f"""你是一个擅长复杂推理的AI助手。请通过逐步思考来解决以下问题：

问题：{user_message}

任务特征：
- 复杂度：{analysis.complexity:.2f}
- 创造性需求：{analysis.creativity:.2f}
- 领域：{analysis.domain}

请按以下格式进行思考：
1. 分析问题核心
2. 分解关键要素
3. 探索可能的解决方案
4. 评估各个方案的优劣
5. 选择最佳方案
6. 详细说明实施步骤

每个思考步骤都要详细展开，确保逻辑清晰。"""

    async def _generate_thought(self, context: str, step: int, analysis: TaskAnalysis) -> str:
        """生成单步思考"""
        thought_prompt = f"""基于当前上下文，请进行第{step}步思考：

当前上下文：
{context}

请详细思考这一步应该考虑什么，并给出具体的分析。"""

        response = await llm.ainvoke([
            SystemMessage(content="你是一个善于逐步思考的助手。"),
            HumanMessage(content=thought_prompt)
        ])

        return response.content

    def _should_continue_thinking(self, last_thought: str, current_step: int, max_steps: int) -> bool:
        """判断是否应该继续思考"""
        # 如果达到最大步骤数，停止
        if current_step >= max_steps:
            return False

        # 如果最后思考包含完成信号，停止
        completion_indicators = ["因此", "综上所述", "最终", "结论", "完成"]
        if any(indicator in last_thought for indicator in completion_indicators):
            return False

        # 默认继续思考
        return True

    async def _generate_final_answer(self, context: str, thoughts: List[str], analysis: TaskAnalysis) -> str:
        """生成最终答案"""
        summary_prompt = f"""基于以下思考过程，请给出最终的完整答案：

思考过程：
{chr(10).join([f'步骤{i+1}: {thought}' for i, thought in enumerate(thoughts)])}

请整合以上思考，给出清晰、完整的最终答案。"""

        response = await llm.ainvoke([
            SystemMessage(content="请基于思考过程给出最终答案。"),
            HumanMessage(content=summary_prompt)
        ])

        return response.content