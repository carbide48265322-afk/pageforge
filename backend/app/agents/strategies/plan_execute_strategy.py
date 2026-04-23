from typing import List, Dict, Any
from dataclasses import dataclass
from app.config import llm
from langchain_core.messages import HumanMessage
from .base_strategy import PlanningStrategy
from app.agents.task_analyzer import TaskAnalysis
from app.graph.state import AgentState

@dataclass
class PlanStep:
    """计划步骤"""
    id: str
    title: str
    description: str
    dependencies: List[str]
    estimated_time: int

@dataclass
class ExecutionPlan:
    """执行计划"""
    steps: List[PlanStep]
    total_estimated_time: int
    domain: str

class PlanExecuteStrategy(PlanningStrategy):
    """Plan-and-Execute策略 - 预先规划+分步执行"""

    def get_name(self) -> str:
        return "plan_execute"

    def get_description(self) -> str:
        return "计划执行模式：先制定详细计划，然后按步骤执行，适合结构化任务"

    def can_handle(self, analysis: TaskAnalysis) -> bool:
        return analysis.structured > 0.5  # 适合结构化任务

    async def execute(self, state: AgentState, analysis: TaskAnalysis) -> AgentState:
        """执行Plan-and-Execute策略"""
        user_message = state["user_message"]

        # 步骤1: 制定详细计划
        plan = await self._create_plan(user_message, analysis)

        # 步骤2: 按步骤执行
        execution_results = []
        completed_steps = set()

        for step in plan.steps:
            # 检查依赖是否满足
            if not self._dependencies_met(step, completed_steps):
                continue

            # 执行步骤
            step_result = await self._execute_step(step, state, analysis)
            execution_results.append(step_result)
            completed_steps.add(step.id)

            # 检查是否需要调整计划
            if self._need_plan_adjustment(step_result, analysis):
                plan = await self._adjust_plan(plan, step_result, analysis)

        # 构建最终结果
        final_result = self._build_final_result(plan, execution_results, analysis)
        return self.build_result(state, final_result)

    async def _create_plan(self, user_message: str, analysis: TaskAnalysis) -> ExecutionPlan:
        """创建执行计划"""
        planning_prompt = f"""为以下任务制定详细的执行计划：

任务：{user_message}

任务特征：
- 领域：{analysis.domain}
- 复杂度：{analysis.complexity:.2f}
- 预估步骤数：{analysis.estimated_steps}

请制定包含以下信息的计划：
1. 具体步骤（{analysis.estimated_steps}个左右）
2. 每个步骤的描述
3. 步骤间的依赖关系
4. 每个步骤的预估时间

返回JSON格式：
{{
  "steps": [
    {{
      "id": "step_1",
      "title": "步骤标题",
      "description": "步骤描述",
      "dependencies": [],
      "estimated_time": 30
    }}
  ],
  "total_estimated_time": 120
}}
"""

        response = await llm.ainvoke([HumanMessage(content=planning_prompt)])
        plan_data = self._parse_plan_response(response.content)

        steps = []
        for step_data in plan_data["steps"]:
            step = PlanStep(
                id=step_data["id"],
                title=step_data["title"],
                description=step_data["description"],
                dependencies=step_data.get("dependencies", []),
                estimated_time=step_data["estimated_time"]
            )
            steps.append(step)

        return ExecutionPlan(
            steps=steps,
            total_estimated_time=plan_data["total_estimated_time"],
            domain=analysis.domain
        )

    def _dependencies_met(self, step: PlanStep, completed_steps: set) -> bool:
        """检查依赖是否满足"""
        return all(dep in completed_steps for dep in step.dependencies)

    async def _execute_step(self, step: PlanStep, state: AgentState, analysis: TaskAnalysis) -> Dict[str, Any]:
        """执行单个步骤"""
        execution_prompt = f"""执行以下计划步骤：

步骤：{step.title}
描述：{step.description}

请提供详细的执行结果。"""

        response = await llm.ainvoke([
            HumanMessage(content=execution_prompt)
        ])

        return {
            "step_id": step.id,
            "step_title": step.title,
            "result": response.content,
            "status": "completed",
            "execution_time": step.estimated_time
        }

    def _need_plan_adjustment(self, step_result: Dict[str, Any], analysis: TaskAnalysis) -> bool:
        """检查是否需要调整计划"""
        # 基于执行结果判断是否需要调整
        return False  # 简化实现

    async def _adjust_plan(self, plan: ExecutionPlan, step_result: Dict[str, Any], analysis: TaskAnalysis) -> ExecutionPlan:
        """调整计划"""
        # 根据执行结果调整后续步骤
        return plan  # 简化实现

    def _build_final_result(self, plan: ExecutionPlan, execution_results: List[Dict], analysis: TaskAnalysis) -> Dict[str, Any]:
        """构建最终结果"""
        return {
            "strategy": "plan_execute",
            "plan": {
                "total_steps": len(plan.steps),
                "completed_steps": len(execution_results),
                "total_time": plan.total_estimated_time,
                "domain": plan.domain
            },
            "execution_results": execution_results,
            "domain": analysis.domain
        }

    def _parse_plan_response(self, content: str) -> Dict[str, Any]:
        """解析计划响应"""
        import json
        import re

        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            # 返回默认计划
            return {
                "steps": [
                    {
                        "id": "step_1",
                        "title": "执行任务",
                        "description": "根据需求执行任务",
                        "dependencies": [],
                        "estimated_time": 30
                    }
                ],
                "total_estimated_time": 30
            }