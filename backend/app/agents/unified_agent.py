from typing import Dict, Any, List
from app.graph.state import AgentState
from app.agents.task_analyzer import TaskAnalyzer, TaskAnalysis
from app.agents.strategies.base_strategy import PlanningStrategy
from app.agents.strategies.react_strategy import ReActStrategy
from app.agents.strategies.plan_execute_strategy import PlanExecuteStrategy

class UnifiedAgent:
    """统一Agent框架 - 智能选择最佳规划策略"""

    def __init__(self):
        self.task_analyzer = TaskAnalyzer()
        self.strategies = self._initialize_strategies()
        self.strategy_performance = {}  # 记录策略性能

    def _initialize_strategies(self) -> Dict[str, PlanningStrategy]:
        """初始化所有可用策略"""
        return {
            "react": ReActStrategy(),
            "plan_execute": PlanExecuteStrategy(),
            # 后续可以添加更多策略
            # "chain_of_thought": ChainOfThoughtStrategy(),
            # "hybrid": HybridStrategy()
        }

    async def process(self, state: AgentState) -> AgentState:
        """处理用户请求的主入口"""
        try:
            # 步骤1: 分析任务特征
            user_message = state["user_message"]
            task_analysis = await self.task_analyzer.analyze_task(user_message)

            # 步骤2: 选择最佳策略
            selected_strategy = self._select_best_strategy(task_analysis)

            # 步骤3: 执行选定策略
            result = await selected_strategy.execute(state, task_analysis)

            # 步骤4: 记录性能和结果
            self._record_execution_performance(selected_strategy.get_name(), task_analysis)

            # 步骤5: 返回统一格式的结果
            return self._format_final_result(result, task_analysis, selected_strategy)

        except Exception as e:
            return self._handle_error(state, e)

    def _select_best_strategy(self, analysis: TaskAnalysis) -> PlanningStrategy:
        """选择最佳规划策略"""
        # 首先获取推荐策略
        recommended_strategy = self.task_analyzer.get_strategy_recommendation(analysis)

        # 检查推荐策略是否可用
        if recommended_strategy in self.strategies:
            strategy = self.strategies[recommended_strategy]
            if strategy.can_handle(analysis):
                return strategy

        # 如果推荐策略不可用，按优先级选择
        strategy_priority = ["plan_execute", "react"]  # 优先级顺序

        for strategy_name in strategy_priority:
            if strategy_name in self.strategies:
                strategy = self.strategies[strategy_name]
                if strategy.can_handle(analysis):
                    return strategy

        # 默认返回ReAct策略
        return self.strategies["react"]

    def _format_final_result(self, result: AgentState, analysis: TaskAnalysis, strategy: PlanningStrategy) -> AgentState:
        """格式化最终结果"""
        return {
            **result,
            "task_analysis": {
                "complexity": analysis.complexity,
                "structured": analysis.structured,
                "domain": analysis.domain,
                "needs_tools": analysis.needs_tools
            },
            "strategy_info": {
                "name": strategy.get_name(),
                "description": strategy.get_description()
            },
            "execution_metadata": {
                "timestamp": self._get_timestamp(),
                "confidence": analysis.confidence
            }
        }

    def _record_execution_performance(self, strategy_name: str, analysis: TaskAnalysis):
        """记录策略执行性能"""
        if strategy_name not in self.strategy_performance:
            self.strategy_performance[strategy_name] = []

        # 记录性能指标（简化版本）
        performance_record = {
            "timestamp": self._get_timestamp(),
            "task_complexity": analysis.complexity,
            "task_domain": analysis.domain,
            "confidence": analysis.confidence
        }

        self.strategy_performance[strategy_name].append(performance_record)

    def _handle_error(self, state: AgentState, error: Exception) -> AgentState:
        """错误处理"""
        return {
            **state,
            "error": str(error),
            "strategy_used": "error_handler",
            "is_complete": False,
            "fallback_result": "很抱歉，处理您的请求时出现了问题。"
        }

    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_strategy_performance_report(self) -> Dict[str, Any]:
        """获取策略性能报告"""
        report = {}

        for strategy_name, performances in self.strategy_performance.items():
            if performances:
                avg_complexity = sum(p["task_complexity"] for p in performances) / len(performances)
                domains = [p["task_domain"] for p in performances]

                report[strategy_name] = {
                    "usage_count": len(performances),
                    "average_task_complexity": avg_complexity,
                    "common_domains": max(set(domains), key=domains.count) if domains else None,
                    "success_rate": 1.0  # 简化版本，假设都成功
                }

        return report

    def add_strategy(self, name: str, strategy: PlanningStrategy):
        """动态添加新策略"""
        self.strategies[name] = strategy

    def remove_strategy(self, name: str):
        """移除策略"""
        if name in self.strategies:
            del self.strategies[name]