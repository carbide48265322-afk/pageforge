"""BaseSubgraph - 子图抽象基类

所有子图的终极基类，定义通用接口和编译缓存机制。
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional, Callable
from functools import lru_cache

from langgraph.graph import StateGraph
from langgraph.types import interrupt
from typing import Any

from app.graph.state import AgentState


class SubgraphMode(str, Enum):
    """子图运行模式"""
    HUMAN_IN_THE_LOOP = "human_in_the_loop"      # 人机协作
    DEBATE_VOTING = "debate_voting"                # 辩论投票
    PIPELINE_REFLECTION = "pipeline_reflection"    # 流水线自审
    SELECTION = "selection"                        # 功能选择


class BaseSubgraph(ABC):
    """子图抽象基类
    
    所有子图必须继承此类，实现 _build_internal() 方法。
    提供编译缓存，避免重复编译。
    
    Example:
        class MySubgraph(BaseSubgraph):
            name = "my_subgraph"
            mode = SubgraphMode.HUMAN_IN_THE_LOOP
            
            def _build_internal(self) -> StateGraph:
                graph = StateGraph(AgentState)
                # ... 添加节点和边
                return graph
    """
    
    # 子类必须定义的属性
    name: str = ""                          # 子图标识名
    description: str = ""                   # 子图描述
    mode: SubgraphMode = None               # 运行模式
    
    # 可选配置
    max_iterations: int = 3                 # 最大迭代次数（AI内部）
    timeout_seconds: Optional[int] = None   # 超时时间
    
    def __init__(self):
        self._compiled: Optional[Any] = None
        self._entry_node: Optional[str] = None
    
    @abstractmethod
    def _build_internal(self) -> StateGraph:
        """构建子图内部结构
        
        子类必须实现此方法，定义节点和边。
        
        Returns:
            StateGraph: 未编译的状态图
        """
        pass
    
    def compile(self, checkpointer: Any = None) -> Any:
        """编译子图（带缓存）
        
        Args:
            checkpointer: 可选的 checkpoint 存储
            
        Returns:
            CompiledGraph: 编译后的可执行图
        """
        if self._compiled is None:
            graph = self._build_internal()
            self._compiled = graph.compile(checkpointer=checkpointer)
        return self._compiled
    
    def get_entry_node(self) -> str:
        """获取入口节点名称
        
        默认使用子图名作为入口节点。
        子类可覆盖此方法自定义入口。
        
        Returns:
            str: 入口节点名
        """
        return self.name if self.name else "entry"
    
    def get_state_key(self) -> str:
        """获取该子图在 AgentState 中的状态键
        
        Returns:
            str: 状态键名，如 "requirement_state"
        """
        return f"{self.name}_state"
    
    def create_interrupt(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """创建中断请求
        
        统一封装 interrupt 调用，前端通过 mode 识别处理方式。
        
        Args:
            payload: 中断携带的数据（如表单schema、选项列表）
            
        Returns:
            Dict: 中断响应
        """
        return {
            "type": "subgraph_interrupt",
            "subgraph": self.name,
            "mode": self.mode.value,
            "payload": payload
        }
    
    def should_continue(self, state: AgentState) -> str:
        """判断是否继续执行（条件边用）
        
        子类可覆盖以实现自定义判断逻辑。
        
        Args:
            state: 当前状态
            
        Returns:
            str: "continue" 或 "interrupt"
        """
        # 默认：检查是否已收到用户响应
        subgraph_state = state.get(self.get_state_key(), {})
        if subgraph_state.get("user_response") is not None:
            return "continue"
        return "interrupt"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', mode={self.mode})>"
