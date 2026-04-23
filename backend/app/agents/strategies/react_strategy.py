from typing import List, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from app.config import llm
from app.core import registry
from .base_strategy import PlanningStrategy
from app.agents.task_analyzer import TaskAnalysis
from app.graph.state import AgentState

class ReActStrategy(PlanningStrategy):
    """ReAct策略 - 思考+行动循环"""

    def get_name(self) -> str:
        return "react"

    def get_description(self) -> str:
        return "ReAct模式：通过思考-行动循环动态解决问题，适合需要工具调用和探索性任务"

    def can_handle(self, analysis: TaskAnalysis) -> bool:
        return True  # ReAct是通用策略

    async def execute(self, state: AgentState, analysis: TaskAnalysis) -> AgentState:
        """执行ReAct策略"""
        user_message = state["user_message"]

        # 构建系统提示
        system_prompt = self._build_system_prompt(analysis)

        # 初始化消息列表
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]

        # 获取工具
        tools = registry.get_langchain_tools()
        llm_with_tools = llm.bind_tools(tools)

        # ReAct循环
        max_iterations = min(5, max(3, analysis.estimated_steps))

        for iteration in range(max_iterations):
            # 思考步骤
            thought = await self._thinking_step(messages, analysis)
            messages.append(thought)

            # 行动步骤
            action_response = await llm_with_tools.ainvoke(messages)
            messages.append(action_response)

            # 检查是否需要工具调用
            if action_response.tool_calls:
                tool_results = await self._execute_tools(action_response.tool_calls)
                messages.extend(tool_results)
            else:
                # 获得最终答案
                final_result = self._extract_result(action_response.content, analysis)
                return self.build_result(state, final_result)

        # 达到最大迭代次数
        return self.build_result(state, {
            "error": "达到最大迭代次数",
            "partial_result": messages[-1].content if messages else None
        })

    def _build_system_prompt(self, analysis: TaskAnalysis) -> str:
        """构建系统提示"""
        return f"""你是一个AI助手，使用ReAct（思考-行动）模式解决问题。

任务特征：
- 复杂度：{analysis.complexity:.2f}
- 结构化程度：{analysis.structured:.2f}
- 创造性需求：{analysis.creativity:.2f}

请按以下格式思考：
1. 思考：分析当前情况和下一步行动
2. 行动：执行具体操作或调用工具
3. 观察：分析行动结果

重复以上步骤直到问题解决。"""

    async def _thinking_step(self, messages: List, analysis: TaskAnalysis) -> AIMessage:
        """思考步骤"""
        thought_prompt = "请思考：基于当前信息，下一步应该做什么？"
        thought_response = await llm.ainvoke([
            *messages,
            HumanMessage(content=thought_prompt)
        ])
        return AIMessage(content=f"思考：{thought_response.content}")

    async def _execute_tools(self, tool_calls: List[Dict]) -> List[ToolMessage]:
        """执行工具调用"""
        tool_results = []

        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            # 执行工具
            tool_info = registry.get_tool_info(tool_name)
            if tool_info:
                result = await tool_info.function.ainvoke(tool_args)
                tool_msg = ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"]
                )
                tool_results.append(tool_msg)

        return tool_results

    def _extract_result(self, content: str, analysis: TaskAnalysis) -> Dict[str, Any]:
        """提取结果"""
        return {
            "content": content,
            "strategy": "react",
            "domain": analysis.domain,
            "complexity": analysis.complexity
        }