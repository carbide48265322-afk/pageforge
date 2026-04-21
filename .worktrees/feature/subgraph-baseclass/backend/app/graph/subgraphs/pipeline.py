"""PipelineReflectionSubgraph - 流水线自审模式

多阶段流水线 + 每阶段自审迭代：
1. 定义阶段列表（如：架构→API→组件→页面）
2. 每个阶段：执行 → 自审 → [修复] → 确认
3. 阶段内最多3次自审迭代
4. 阶段通过 → 下一阶段
5. 全部通过 → 输出结果

子类只需定义 stages 和 execute_stage() 方法。
"""

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from enum import Enum

from langgraph.graph import StateGraph, END

from app.graph.state import AgentState
from .base import BaseSubgraph, SubgraphMode


class StageStatus(str, Enum):
    """阶段状态"""
    PENDING = "pending"
    RUNNING = "running"
    REVIEWING = "reviewing"
    ITERATING = "iterating"
    PASSED = "passed"
    FAILED = "failed"


@dataclass
class StageResult:
    """阶段执行结果"""
    stage_name: str
    output: Any                           # 阶段产出
    review_feedback: Optional[str] = None # 自审反馈
    issues: List[str] = field(default_factory=list)
    iteration_count: int = 0
    status: StageStatus = StageStatus.PENDING
    passed: bool = False


@dataclass
class PipelineResult:
    """流水线最终结果"""
    all_passed: bool
    stage_results: List[StageResult]
    final_output: Any
    total_iterations: int


class PipelineReflectionSubgraph(BaseSubgraph):
    """流水线自审子图基类
    
    实现标准的多阶段流水线模板：
    stage_1 → review → [iterate] → stage_2 → ... → finalize
    
    子类必须实现:
        - stages: List[str] 阶段列表
        - execute_stage(state, stage_name): 执行阶段
        - review_stage(state, stage_result): 自审阶段
        
    可选覆盖:
        - should_fix(review_result): 判断是否修复
        - on_stage_complete(stage_result): 阶段完成回调
    """
    
    mode = SubgraphMode.PIPELINE_REFLECTION
    stages: List[str] = []        # 子类必须定义
    max_stage_iterations: int = 3 # 每阶段最大迭代次数
    
    # 状态键
    _results_key: str = "stage_results"
    _current_stage_idx_key: str = "current_stage_idx"
    _current_iteration_key: str = "current_iteration"
    _final_output_key: str = "final_output"
    _status_key: str = "status"
    
    def _build_internal(self) -> StateGraph:
        """构建流水线子图"""
        graph = StateGraph(AgentState)
        
        # 节点
        graph.add_node(f"{self.name}_init", self._init_pipeline)
        graph.add_node(f"{self.name}_execute", self._execute_stage_node)
        graph.add_node(f"{self.name}_review", self._review_stage_node)
        graph.add_node(f"{self.name}_finalize", self._finalize_node)
        
        # 入口
        graph.set_entry_point(f"{self.name}_init")
        graph.add_edge(f"{self.name}_init", f"{self.name}_execute")
        
        # 执行 → 自审
        graph.add_edge(f"{self.name}_execute", f"{self.name}_review")
        
        # 自审条件边：迭代 / 下一阶段 / 结束
        graph.add_conditional_edges(
            f"{self.name}_review",
            self._next_step,
            {
                "iterate": f"{self.name}_execute",   # 重新执行当前阶段
                "next": f"{self.name}_execute",      # 进入下一阶段
                "finalize": f"{self.name}_finalize"  # 全部完成
            }
        )
        
        graph.add_edge(f"{self.name}_finalize", END)
        
        return graph
    
    def _get_subgraph_state(self, state: AgentState) -> Dict:
        """获取子图私有状态"""
        key = self.get_state_key()
        if key not in state:
            state[key] = {}
        return state[key]
    
    def _init_pipeline(self, state: AgentState) -> Dict:
        """初始化流水线"""
        subgraph_state = self._get_subgraph_state(state)
        
        # 初始化各阶段结果
        stage_results = [
            StageResult(stage_name=stage_name)
            for stage_name in self.stages
        ]
        
        subgraph_state[self._results_key] = stage_results
        subgraph_state[self._current_stage_idx_key] = 0
        subgraph_state[self._current_iteration_key] = 0
        subgraph_state[self._status_key] = "initialized"
        
        return {self.get_state_key(): subgraph_state}
    
    def _execute_stage_node(self, state: AgentState) -> Dict:
        """执行当前阶段"""
        subgraph_state = self._get_subgraph_state(state)
        
        stage_idx = subgraph_state[self._current_stage_idx_key]
        stage_name = self.stages[stage_idx]
        
        # 更新状态
        subgraph_state[self._status_key] = f"executing_{stage_name}"
        
        # 执行阶段
        output = self.execute_stage(state, stage_name)
        
        # 更新阶段结果
        stage_results = subgraph_state[self._results_key]
        stage_result = stage_results[stage_idx]
        stage_result.output = output
        stage_result.status = StageStatus.REVIEWING
        stage_result.iteration_count = subgraph_state.get(self._current_iteration_key, 0) + 1
        
        return {self.get_state_key(): subgraph_state}
    
    def _review_stage_node(self, state: AgentState) -> Dict:
        """自审当前阶段"""
        subgraph_state = self._get_subgraph_state(state)
        
        stage_idx = subgraph_state[self._current_stage_idx_key]
        stage_results = subgraph_state[self._results_key]
        stage_result = stage_results[stage_idx]
        
        subgraph_state[self._status_key] = f"reviewing_{stage_result.stage_name}"
        
        # 自审
        review_result = self.review_stage(state, stage_result)
        
        # 更新阶段结果
        stage_result.review_feedback = review_result.get("feedback")
        stage_result.issues = review_result.get("issues", [])
        stage_result.passed = review_result.get("passed", False)
        
        if stage_result.passed:
            stage_result.status = StageStatus.PASSED
            # 阶段完成回调
            self.on_stage_complete(stage_result)
        else:
            stage_result.status = StageStatus.ITERATING
        
        return {self.get_state_key(): subgraph_state}
    
    def _next_step(self, state: AgentState) -> str:
        """决定下一步"""
        subgraph_state = self._get_subgraph_state(state)
        
        stage_idx = subgraph_state[self._current_stage_idx_key]
        stage_results = subgraph_state[self._results_key]
        stage_result = stage_results[stage_idx]
        current_iter = subgraph_state.get(self._current_iteration_key, 0)
        
        # 当前阶段通过
        if stage_result.passed:
            # 是否是最后一个阶段
            if stage_idx >= len(self.stages) - 1:
                return "finalize"
            
            # 进入下一阶段
            subgraph_state[self._current_stage_idx_key] = stage_idx + 1
            subgraph_state[self._current_iteration_key] = 0
            return "next"
        
        # 未通过，检查是否超过最大迭代
        if current_iter >= self.max_stage_iterations:
            # 强制通过（或标记失败）
            stage_result.passed = True
            stage_result.status = StageStatus.PASSED
            
            if stage_idx >= len(self.stages) - 1:
                return "finalize"
            
            subgraph_state[self._current_stage_idx_key] = stage_idx + 1
            subgraph_state[self._current_iteration_key] = 0
            return "next"
        
        # 继续迭代
        subgraph_state[self._current_iteration_key] = current_iter + 1
        return "iterate"
    
    def _finalize_node(self, state: AgentState) -> Dict:
        """结束流水线，整理结果"""
        subgraph_state = self._get_subgraph_state(state)
        
        stage_results = subgraph_state.get(self._results_key, [])
        
        # 计算总迭代次数
        total_iterations = sum(r.iteration_count for r in stage_results)
        
        # 检查是否全部通过
        all_passed = all(r.passed for r in stage_results)
        
        # 收集最终输出（各阶段产出的组合）
        final_output = self.aggregate_outputs(stage_results)
        
        # 创建结果
        result = PipelineResult(
            all_passed=all_passed,
            stage_results=stage_results,
            final_output=final_output,
            total_iterations=total_iterations
        )
        
        subgraph_state[self._final_output_key] = result
        subgraph_state[self._status_key] = "completed"
        
        return {self.get_state_key(): subgraph_state}
    
    # ========== 子类必须/可选实现 ==========
    
    @abstractmethod
    def execute_stage(self, state: AgentState, stage_name: str) -> Any:
        """执行阶段（子类必须实现）
        
        Args:
            state: 当前状态
            stage_name: 阶段名称
            
        Returns:
            Any: 阶段产出
        """
        pass
    
    @abstractmethod
    def review_stage(self, state: AgentState, stage_result: StageResult) -> Dict:
        """自审阶段（子类必须实现）
        
        Args:
            state: 当前状态
            stage_result: 阶段执行结果
            
        Returns:
            Dict: {
                "passed": bool,       # 是否通过
                "feedback": str,      # 反馈内容
                "issues": List[str]   # 问题列表
            }
        """
        pass
    
    def on_stage_complete(self, stage_result: StageResult) -> None:
        """阶段完成回调（子类可选覆盖）
        
        可用于：日志记录、资源清理、触发外部事件等
        """
        pass
    
    def aggregate_outputs(self, stage_results: List[StageResult]) -> Any:
        """聚合各阶段输出（子类可选覆盖）
        
        默认返回所有阶段产出的字典
        
        Returns:
            Any: 最终聚合结果
        """
        return {
            r.stage_name: r.output
            for r in stage_results
        }
