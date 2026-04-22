"""子图基类定义"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, Callable, Any, Dict
from dataclasses import dataclass, field
from datetime import datetime

try:
    from langgraph.graph import StateGraph, END
except ImportError:
    # Mock for type checking
    StateGraph = Any
    END = Any

from app.graph.subgraphs.types import SubgraphType, SubgraphMode, StateT


@dataclass
class SubgraphConfig:
    """子图配置"""
    name: str
    subgraph_type: SubgraphType
    mode: SubgraphMode
    max_iterations: int = 3           # 最大自迭代次数
    enable_human_input: bool = False  # 是否需要人机协作
    enable_rollback: bool = True      # 是否支持回退


class BaseSubgraph(ABC, Generic[StateT]):
    """子图终极基类 - 所有子图继承"""
    
    def __init__(self, config: SubgraphConfig):
        self.config = config
        self._graph = None
        self._checkpoint_manager = None
    
    @property
    def name(self) -> str:
        return self.config.name
    
    @property
    def subgraph_type(self) -> SubgraphType:
        return self.config.subgraph_type
    
    @abstractmethod
    def build(self) -> StateGraph:
        """构建子图 - 子类必须实现"""
        pass
    
    def get_graph(self) -> StateGraph:
        """获取编译后的子图"""
        if self._graph is None:
            self._graph = self.build().compile()
        return self._graph

    def get_state_key(self) -> str:
        """获取子图在主状态中的私有 key"""
        return f"subgraph_{self.name}"

    @abstractmethod
    async def on_enter(self, state: StateT) -> StateT:
        """进入子图前的初始化"""
        pass
    
    @abstractmethod
    async def on_exit(self, state: StateT) -> StateT:
        """离开子图前的清理/快照保存"""
        pass
    
    def should_pause(self, state: StateT) -> bool:
        """判断是否暂停等待外部输入"""
        return self.config.enable_human_input


class HumanInTheLoopSubgraph(BaseSubgraph[Dict], ABC):
    """人机协作子图基类
    
    特征:
    - 生成内容后暂停等待用户
    - 支持 confirm/revise/back 操作
    - 用户循环不限次数
    """
    
    def __init__(self, name: str, max_iterations: int = 3, enable_rollback: bool = True):
        config = SubgraphConfig(
            name=name,
            subgraph_type=SubgraphType.HUMAN_IN_THE_LOOP,
            mode=SubgraphMode.INTERACTIVE,
            enable_human_input=True,
            max_iterations=max_iterations,
            enable_rollback=enable_rollback
        )
        super().__init__(config)
    
    @abstractmethod
    def generate_content(self, state: Dict) -> dict:
        """生成需要用户确认的内容"""
        pass
    
    @abstractmethod
    def create_human_input_schema(self, content: dict) -> dict:
        """创建人机协作表单 Schema"""
        pass
    
    def handle_response(self, state: Dict, response: dict) -> str:
        """处理用户响应，返回路由决策"""
        action = response.get("action", "confirm")
        
        if action == "confirm":
            return "confirm"
        elif action == "revise":
            return "revise"
        elif action == "back":
            return "back"
        else:
            return "confirm"


class PipelineReflectionSubgraph(BaseSubgraph[Dict], ABC):
    """流水线自审子图基类
    
    特征:
    - 流水线阶段顺序执行
    - 每阶段自审迭代（最多3次）
    - 失败可重试或跳过
    """
    
    def __init__(self, name: str, stages: list[str], max_iterations: int = 3):
        config = SubgraphConfig(
            name=name,
            subgraph_type=SubgraphType.PIPELINE_REFLECTION,
            mode=SubgraphMode.AUTONOMOUS,
            max_iterations=max_iterations,
            enable_human_input=False
        )
        super().__init__(config)
        self.stages = stages
    
    @abstractmethod
    async def execute_stage(self, state: Dict, stage: str) -> dict:
        """执行单个阶段"""
        pass
    
    @abstractmethod
    async def review_stage(self, state: Dict, stage: str, result: dict) -> dict:
        """自审阶段产出"""
        pass
    
    def should_retry(self, review_result: dict) -> bool:
        """判断是否需要重试"""
        return review_result.get("passed", False) is False
