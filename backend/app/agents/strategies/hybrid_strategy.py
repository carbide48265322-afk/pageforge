from typing import List, Dict, Any
from app.config import llm
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from .base_strategy import PlanningStrategy
from .react_strategy import ReActStrategy
from .plan_execute_strategy import PlanExecuteStrategy
from .chain_of_thought_strategy import ChainOfThoughtStrategy
from app.agents.task_analyzer import TaskAnalysis
from app.graph.state import AgentState

class HybridStrategy(PlanningStrategy):
    """Hybrid混合策略 - 多层级组合策略"""

    def get_name(self) -> str:
        return "hybrid"

    def get_description(self) -> str:
        return "混合模式：结合多种策略优势，适合复杂且多阶段的任务"

    def can_handle(self, analysis: TaskAnalysis) -> bool:
        return analysis.complexity > 0.7 and analysis.structured > 0.6

    async def execute(self, state: AgentState, analysis: TaskAnalysis) -> AgentState:
        """执行Hybrid混合策略"""
        user_message = state["user_message"]

        # 步骤1: 使用Chain-of-Thought进行高层规划
        planning_result = await self._high_level_planning(user_message, analysis)

        # 步骤2: 根据规划结果选择子策略
        subtasks = planning_result.get("subtasks", [])
        execution_results = []

        for subtask in subtasks:
            subtask_analysis = await self._analyze_subtask(subtask, analysis)
            subtask_result = await self._execute_subtask(state, subtask, subtask_analysis)
            execution_results.append(subtask_result)

        # 步骤3: 整合结果
        final_result = await self._integrate_results(planning_result, execution_results, analysis)

        return self.build_result(state, final_result)

    async def _high_level_planning(self, user_message: str, analysis: TaskAnalysis) -> Dict[str, Any]:
        """高层规划阶段"""
        planning_prompt = f"""你是一个高级规划师，需要对以下复杂任务进行分解和规划：

主任务：{user_message}

任务特征：
- 复杂度：{analysis.complexity:.2f}
- 结构化程度：{analysis.structured:.2f}
- 创造性需求：{analysis.creativity:.2f}
- 预估步骤数：{analysis.estimated_steps}

请完成以下工作：
1. 将任务分解为2-4个子任务
2. 确定子任务的执行顺序和依赖关系
3. 为每个子任务推荐最适合的策略
4. 识别关键风险点和应对方案

返回JSON格式：
{{
  "overview": "整体规划概述",
  "subtasks": [
    {{
      "id": "subtask_1",
      "title": "子任务标题",
      "description": "详细描述",
      "recommended_strategy": "react/plan_execute/chain_of_thought",
      "priority": 1,
      "dependencies": []
    }}
  ],
  "risks": ["风险点1", "风险点2"],
  "mitigation": ["应对方案1", "应对方案2"]
}}
"""

        response = await llm.ainvoke([HumanMessage(content=planning_prompt)])
        return self._parse_planning_response(response.content)

    async def _analyze_subtask(self, subtask: Dict[str, Any], parent_analysis: TaskAnalysis) -> TaskAnalysis:
        """分析子任务特征"""
        # 基于主任务分析和子任务描述创建子任务分析
        subtask_description = f"{subtask['title']}: {subtask['description']}"

        # 简化分析：基于推荐策略调整特征
        strategy = subtask.get("recommended_strategy", "react")

        if strategy == "plan_execute":
            return TaskAnalysis(
                complexity=parent_analysis.complexity * 0.8,
                structured=0.8,
                needs_tools=False,
                creativity=parent_analysis.creativity * 0.6,
                certainty=parent_analysis.certainty,
                estimated_steps=max(2, parent_analysis.estimated_steps // 3),
                domain=parent_analysis.domain,
                confidence=parent_analysis.confidence
            )
        elif strategy == "chain_of_thought":
            return TaskAnalysis(
                complexity=parent_analysis.complexity * 0.9,
                structured=0.5,
                needs_tools=False,
                creativity=0.8,
                certainty=parent_analysis.certainty * 0.8,
                estimated_steps=max(2, parent_analysis.estimated_steps // 2),
                domain=parent_analysis.domain,
                confidence=parent_analysis.confidence
            )
        else:  # react
            return TaskAnalysis(
                complexity=parent_analysis.complexity * 0.7,
                structured=0.4,
                needs_tools=True,
                creativity=parent_analysis.creativity * 0.5,
                certainty=parent_analysis.certainty * 0.9,
                estimated_steps=max(2, parent_analysis.estimated_steps // 2),
                domain=parent_analysis.domain,
                confidence=parent_analysis.confidence
            )

    async def _execute_subtask(self, state: AgentState, subtask: Dict[str, Any],
                              subtask_analysis: TaskAnalysis) -> Dict[str, Any]:
        """执行子任务"""
        # 创建子任务状态
        subtask_state = {
            **state,
            "user_message": subtask["description"]
        }

        # 根据推荐策略选择执行器
        strategy_name = subtask.get("recommended_strategy", "react")

        if strategy_name == "plan_execute":
            strategy = PlanExecuteStrategy()
        elif strategy_name == "chain_of_thought":
            strategy = ChainOfThoughtStrategy()
        else:
            strategy = ReActStrategy()

        # 执行子任务
        result = await strategy.execute(subtask_state, subtask_analysis)

        return {
            "subtask_id": subtask["id"],
            "subtask_title": subtask["title"],
            "strategy_used": strategy_name,
            "result": result.get("result", {}),
            "status": "completed" if result.get("is_complete", False) else "failed"
        }

    async def _integrate_results(self, planning_result: Dict[str, Any],
                                execution_results: List[Dict[str, Any]],
                                analysis: TaskAnalysis) -> Dict[str, Any]:
        """整合执行结果"""
        integration_prompt = f"""请整合以下子任务执行结果，形成完整的解决方案：

规划概述：
{planning_result.get('overview', '')}

执行结果：
{chr(10).join([f"- {result['subtask_title']} ({result['strategy_used']}): {result['status']}" for result in execution_results])}

详细结果：
{chr(10).join([f"{result['subtask_title']}: {result['result']}" for result in execution_results if result['result']])}

请提供一个完整的、整合的最终解决方案。"""

        response = await llm.ainvoke([
            SystemMessage(content="你是一个善于整合和总结的专家。"),
            HumanMessage(content=integration_prompt)
        ])

        return {
            "strategy": "hybrid",
            "planning": planning_result,
            "subtask_results": execution_results,
            "integrated_solution": response.content,
            "domain": analysis.domain,
            "complexity": analysis.complexity,
            "total_subtasks": len(execution_results),
            "successful_subtasks": len([r for r in execution_results if r["status"] == "completed"])
        }

    def _parse_planning_response(self, content: str) -> Dict[str, Any]:
        """解析规划响应"""
        import json
        import re

        # 尝试提取JSON
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass

        # 如果无法解析JSON，返回默认结构
        return {
            "overview": "混合策略执行规划",
            "subtasks": [
                {
                    "id": "subtask_1",
                    "title": "主任务执行",
                    "description": content[:200] + "..." if len(content) > 200 else content,
                    "recommended_strategy": "react",
                    "priority": 1,
                    "dependencies": []
                }
            ],
            "risks": ["执行风险"],
            "mitigation": ["监控执行过程"]
        }