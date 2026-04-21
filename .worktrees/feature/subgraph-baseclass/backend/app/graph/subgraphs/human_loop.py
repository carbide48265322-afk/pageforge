"""HumanInTheLoopSubgraph - 人机协作模式

模板化的人机协作流程：
1. AI 生成内容（PRD/设计稿/等）
2. 转换为表单 Schema
3. 中断等待用户确认/修改
4. 用户响应后继续
5. 支持 AI 内部迭代（最多3次）

子类只需实现 generate_content() 方法。
"""

from abc import abstractmethod
from typing import Any, Dict, Optional, Callable
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.types import interrupt

from app.graph.state import AgentState
from .base import BaseSubgraph, SubgraphMode


class HumanInTheLoopSubgraph(BaseSubgraph):
    """人机协作子图基类
    
    实现标准的人机协作模板：
    generate → to_schema → interrupt → process_response
    
    子类必须实现:
        - generate_content(state): 生成内容
        - to_schema(content): 内容转表单
        
    可选覆盖:
        - process_response(state, response): 处理用户响应
        - should_iterate(state): 判断是否迭代
    """
    
    mode = SubgraphMode.HUMAN_IN_THE_LOOP
    max_iterations: int = 3  # AI 内部迭代上限
    
    # 状态键（自动构建）
    _content_key: str = "generated_content"
    _schema_key: str = "form_schema"
    _response_key: str = "user_response"
    _iteration_key: str = "iteration_count"
    _status_key: str = "status"  # pending | confirmed | iterating
    
    def _build_internal(self) -> StateGraph:
        """构建人机协作子图内部结构
        
        节点流:
            entry → generate → to_schema → human_input → process → [iterate?] → exit
        """
        graph = StateGraph(AgentState)
        
        # 添加节点
        graph.add_node(f"{self.name}_generate", self._generate_node)
        graph.add_node(f"{self.name}_to_schema", self._to_schema_node)
        graph.add_node(f"{self.name}_human_input", self._human_input_node)
        graph.add_node(f"{self.name}_process", self._process_response_node)
        
        # 设置入口
        graph.set_entry_point(f"{self.name}_generate")
        
        # 添加边
        graph.add_edge(f"{self.name}_generate", f"{self.name}_to_schema")
        graph.add_edge(f"{self.name}_to_schema", f"{self.name}_human_input")
        
        # human_input 条件边：等待用户 或 继续
        graph.add_conditional_edges(
            f"{self.name}_human_input",
            self._should_wait_human,
            {
                "wait": END,  # 中断，等待用户
                "continue": f"{self.name}_process"
            }
        )
        
        # process 条件边：迭代 或 结束
        graph.add_conditional_edges(
            f"{self.name}_process",
            self._should_iterate,
            {
                "iterate": f"{self.name}_generate",  # 重新生成
                "finish": END
            }
        )
        
        return graph
    
    def _get_subgraph_state(self, state: AgentState) -> Dict:
        """获取该子图的私有状态"""
        key = self.get_state_key()
        if key not in state:
            state[key] = {}
        return state[key]
    
    def _generate_node(self, state: AgentState) -> Dict:
        """生成内容节点"""
        subgraph_state = self._get_subgraph_state(state)
        
        # 调用子类实现的生成逻辑
        content = self.generate_content(state)
        
        # 更新状态
        subgraph_state[self._content_key] = content
        subgraph_state[self._status_key] = "generated"
        subgraph_state[self._iteration_key] = subgraph_state.get(self._iteration_key, 0) + 1
        
        return {self.get_state_key(): subgraph_state}
    
    def _to_schema_node(self, state: AgentState) -> Dict:
        """转换为表单 Schema 节点"""
        subgraph_state = self._get_subgraph_state(state)
        content = subgraph_state.get(self._content_key)
        
        # 调用子类实现的转换逻辑
        schema = self.to_schema(content)
        
        subgraph_state[self._schema_key] = schema
        subgraph_state[self._status_key] = "awaiting_human"
        
        return {self.get_state_key(): subgraph_state}
    
    def _human_input_node(self, state: AgentState) -> Dict:
        """人机协作中断节点"""
        subgraph_state = self._get_subgraph_state(state)
        schema = subgraph_state.get(self._schema_key)
        
        # 检查是否已有用户响应（恢复执行时）
        if subgraph_state.get(self._response_key) is not None:
            return {self.get_state_key(): subgraph_state}
        
        # 触发中断
        result = interrupt({
            "type": "human_input",
            "subgraph": self.name,
            "schema": schema,
            "description": self.description,
            "iteration": subgraph_state.get(self._iteration_key, 0)
        })
        
        # 保存用户响应
        subgraph_state[self._response_key] = result
        
        return {self.get_state_key(): subgraph_state}
    
    def _process_response_node(self, state: AgentState) -> Dict:
        """处理用户响应节点"""
        subgraph_state = self._get_subgraph_state(state)
        response = subgraph_state.get(self._response_key)
        
        # 调用子类实现的处理逻辑
        processed = self.process_response(state, response)
        
        # 更新状态
        subgraph_state.update(processed)
        subgraph_state[self._status_key] = "processed"
        
        return {self.get_state_key(): subgraph_state}
    
    def _should_wait_human(self, state: AgentState) -> str:
        """判断是否等待用户"""
        subgraph_state = self._get_subgraph_state(state)
        
        # 已有响应，继续
        if subgraph_state.get(self._response_key) is not None:
            return "continue"
        
        # 需要等待用户
        return "wait"
    
    def _should_iterate(self, state: AgentState) -> str:
        """判断是否迭代"""
        subgraph_state = self._get_subgraph_state(state)
        current_iter = subgraph_state.get(self._iteration_key, 0)
        
        # 超过最大迭代次数，结束
        if current_iter >= self.max_iterations:
            return "finish"
        
        # 调用子类判断
        if self.should_iterate(state):
            # 清除响应，准备重新生成
            subgraph_state[self._response_key] = None
            subgraph_state[self._status_key] = "iterating"
            return "iterate"
        
        return "finish"
    
    # ========== 子类必须/可选实现的方法 ==========
    
    @abstractmethod
    def generate_content(self, state: AgentState) -> Any:
        """生成内容（子类必须实现）
        
        Args:
            state: 当前状态
            
        Returns:
            Any: 生成的内容（PRD/设计稿/等）
        """
        pass
    
    @abstractmethod
    def to_schema(self, content: Any) -> Dict:
        """内容转换为表单 Schema（子类必须实现）
        
        Args:
            content: 生成的内容
            
        Returns:
            Dict: JSON Schema 格式的表单定义
        """
        pass
    
    def process_response(self, state: AgentState, response: Dict) -> Dict:
        """处理用户响应（子类可选覆盖）
        
        默认将响应直接保存。
        子类可覆盖以实现：验证、转换、提取关键字段等。
        
        Args:
            state: 当前状态
            response: 用户响应数据
            
        Returns:
            Dict: 处理后的状态更新
        """
        return {"confirmed_data": response}
    
    def should_iterate(self, state: AgentState) -> bool:
        """判断是否迭代（子类可选覆盖）
        
        默认逻辑：
        - 用户标记需要修改 → 迭代
        - 用户确认 → 不迭代
        
        Args:
            state: 当前状态
            
        Returns:
            bool: 是否迭代
        """
        subgraph_state = self._get_subgraph_state(state)
        response = subgraph_state.get(self._response_key, {})
        
        # 检查用户是否要求修改
        return response.get("action") == "modify" or response.get("needs_revision", False)
