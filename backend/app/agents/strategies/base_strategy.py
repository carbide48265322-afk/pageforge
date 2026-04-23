from abc import ABC, abstractmethod
from typing import Dict, Any
from app.graph.state import AgentState
from app.agents.task_analyzer import TaskAnalysis

class PlanningStrategy(ABC):
    """规划策略基类"""

    @abstractmethod
    async def execute(self, state: AgentState, analysis: TaskAnalysis) -> AgentState:
        """执行规划策略"""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """获取策略名称"""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """获取策略描述"""
        pass

    def can_handle(self, analysis: TaskAnalysis) -> bool:
        """判断是否能处理该任务"""
        return True  # 默认都能处理

    def build_result(self, state: AgentState, result_data: Any) -> AgentState:
        """构建统一的结果格式"""
        return {
            **state,
            "result": result_data,
            "strategy_used": self.get_name(),
            "is_complete": True
        }