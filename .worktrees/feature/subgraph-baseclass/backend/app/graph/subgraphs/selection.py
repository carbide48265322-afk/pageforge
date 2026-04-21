"""SelectionSubgraph - 功能选择模式

简单的选项展示 + 用户选择：
1. 生成/获取选项列表
2. 转换为选择界面（卡片/列表）
3. 中断等待用户选择
4. 记录选择结果
5. 支持多选/单选

子类只需实现 get_options() 方法。
"""

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum

from langgraph.graph import StateGraph, END
from langgraph.types import interrupt

from app.graph.state import AgentState
from .base import BaseSubgraph, SubgraphMode


class SelectionMode(str, Enum):
    """选择模式"""
    SINGLE = "single"      # 单选
    MULTIPLE = "multiple"  # 多选
    RANKING = "ranking"    # 排序


@dataclass
class Option:
    """选项定义"""
    id: str
    title: str
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    icon: Optional[str] = None
    disabled: bool = False


@dataclass
class SelectionResult:
    """选择结果"""
    selected_ids: List[str]
    selected_options: List[Option]
    mode: SelectionMode
    timestamp: datetime


class SelectionSubgraph(BaseSubgraph):
    """功能选择子图基类
    
    实现标准的选择流程：
    get_options → render → interrupt → record
    
    子类必须实现:
        - get_options(state): 获取选项列表
        
    可选覆盖:
        - render_options(options): 渲染选择界面
        - validate_selection(selection): 验证选择
    """
    
    mode = SubgraphMode.SELECTION
    selection_mode: SelectionMode = SelectionMode.SINGLE
    allow_custom: bool = False  # 是否允许自定义输入
    
    # 状态键
    _options_key: str = "options"
    _rendered_key: str = "rendered_ui"
    _selection_key: str = "user_selection"
    _result_key: str = "selection_result"
    _status_key: str = "status"
    
    def _build_internal(self) -> StateGraph:
        """构建选择子图"""
        graph = StateGraph(AgentState)
        
        # 节点
        graph.add_node(f"{self.name}_get_options", self._get_options_node)
        graph.add_node(f"{self.name}_render", self._render_node)
        graph.add_node(f"{self.name}_select", self._select_node)
        graph.add_node(f"{self.name}_validate", self._validate_node)
        
        # 入口
        graph.set_entry_point(f"{self.name}_get_options")
        
        # 边
        graph.add_edge(f"{self.name}_get_options", f"{self.name}_render")
        graph.add_edge(f"{self.name}_render", f"{self.name}_select")
        graph.add_edge(f"{self.name}_select", f"{self.name}_validate")
        
        # 验证条件边：重新选择 / 完成
        graph.add_conditional_edges(
            f"{self.name}_validate",
            self._should_retry,
            {
                "retry": f"{self.name}_render",  # 验证失败，重新选择
                "finish": END
            }
        )
        
        return graph
    
    def _get_subgraph_state(self, state: AgentState) -> Dict:
        """获取子图私有状态"""
        key = self.get_state_key()
        if key not in state:
            state[key] = {}
        return state[key]
    
    def _get_options_node(self, state: AgentState) -> Dict:
        """获取选项节点"""
        subgraph_state = self._get_subgraph_state(state)
        
        # 调用子类实现
        options = self.get_options(state)
        
        # 转换为 Option 对象
        option_objects = [
            opt if isinstance(opt, Option) else Option(**opt)
            for opt in options
        ]
        
        subgraph_state[self._options_key] = option_objects
        subgraph_state[self._status_key] = "options_loaded"
        
        return {self.get_state_key(): subgraph_state}
    
    def _render_node(self, state: AgentState) -> Dict:
        """渲染选择界面节点"""
        subgraph_state = self._get_subgraph_state(state)
        options = subgraph_state.get(self._options_key, [])
        
        # 调用渲染
        rendered = self.render_options(options)
        
        subgraph_state[self._rendered_key] = rendered
        subgraph_state[self._status_key] = "awaiting_selection"
        
        return {self.get_state_key(): subgraph_state}
    
    def _select_node(self, state: AgentState) -> Dict:
        """选择中断节点"""
        subgraph_state = self._get_subgraph_state(state)
        
        # 检查是否已有选择（恢复执行时）
        if subgraph_state.get(self._selection_key) is not None:
            return {self.get_state_key(): subgraph_state}
        
        options = subgraph_state.get(self._options_key, [])
        rendered = subgraph_state.get(self._rendered_key)
        
        # 触发中断
        result = interrupt({
            "type": "selection",
            "subgraph": self.name,
            "mode": self.selection_mode.value,
            "options": [
                {
                    "id": opt.id,
                    "title": opt.title,
                    "description": opt.description,
                    "icon": opt.icon,
                    "disabled": opt.disabled
                }
                for opt in options
            ],
            "ui": rendered,
            "allow_custom": self.allow_custom
        })
        
        # 保存选择
        subgraph_state[self._selection_key] = result
        
        return {self.get_state_key(): subgraph_state}
    
    def _validate_node(self, state: AgentState) -> Dict:
        """验证选择节点"""
        subgraph_state = self._get_subgraph_state(state)
        
        selection_data = subgraph_state.get(self._selection_key, {})
        options = subgraph_state.get(self._options_key, [])
        
        # 提取选择的ID
        selected_ids = selection_data.get("selected_ids", [])
        if isinstance(selected_ids, str):
            selected_ids = [selected_ids]
        
        # 查找选中的选项
        selected_options = [
            opt for opt in options
            if opt.id in selected_ids
        ]
        
        # 验证
        is_valid = self.validate_selection(selected_ids, selected_options)
        
        if is_valid:
            # 创建结果
            result = SelectionResult(
                selected_ids=selected_ids,
                selected_options=selected_options,
                mode=self.selection_mode,
                timestamp=datetime.now()
            )
            
            subgraph_state[self._result_key] = result
            subgraph_state[self._status_key] = "completed"
        else:
            subgraph_state[self._status_key] = "validation_failed"
        
        return {self.get_state_key(): subgraph_state}
    
    def _should_retry(self, state: AgentState) -> str:
        """判断是否重新选择"""
        subgraph_state = self._get_subgraph_state(state)
        
        if subgraph_state.get(self._status_key) == "validation_failed":
            # 清除选择，重新渲染
            subgraph_state[self._selection_key] = None
            return "retry"
        
        return "finish"
    
    # ========== 子类必须/可选实现 ==========
    
    @abstractmethod
    def get_options(self, state: AgentState) -> List[Union[Option, Dict]]:
        """获取选项列表（子类必须实现）
        
        Args:
            state: 当前状态
            
        Returns:
            List[Option]: 选项列表
        """
        pass
    
    def render_options(self, options: List[Option]) -> Dict:
        """渲染选择界面（子类可选覆盖）
        
        默认返回简单的卡片列表配置
        
        Args:
            options: 选项列表
            
        Returns:
            Dict: UI 配置
        """
        return {
            "type": "card_list",
            "title": f"请选择{self.description}",
            "mode": self.selection_mode.value,
            "items": [
                {
                    "id": opt.id,
                    "title": opt.title,
                    "description": opt.description,
                    "icon": opt.icon
                }
                for opt in options
            ]
        }
    
    def validate_selection(self, selected_ids: List[str], selected_options: List[Option]) -> bool:
        """验证选择（子类可选覆盖）
        
        默认验证：
        - 单选：必须选且只选1个
        - 多选：至少选1个
        
        Args:
            selected_ids: 选中的ID列表
            selected_options: 选中的选项对象
            
        Returns:
            bool: 是否有效
        """
        if not selected_ids:
            return False
        
        if self.selection_mode == SelectionMode.SINGLE and len(selected_ids) != 1:
            return False
        
        return True
