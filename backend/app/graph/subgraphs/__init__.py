"""PageForge Subgraph 基类体系

提供5种子图模式：
- HumanInTheLoopSubgraph: 人机协作模式
- DebateVotingSubgraph: 辩论投票模式  
- PipelineReflectionSubgraph: 流水线自审模式
- SelectionSubgraph: 功能选择模式
- Hierarchical: 层级嵌套模式

主流程子图:
- RequirementSubgraph: 需求理解
- DesignSubgraph: 风格设计
- CodeSubgraph: React 项目代码生成（独立子图，LLM + Tool）
- DeliverySubgraph: 交付确认

注: TechSubgraph、FeatureSubgraph 已合并到 DesignSubgraph 内部
"""

from .types import SubgraphType, SubgraphMode, StateT, ConfigT
from .base import BaseSubgraph, SubgraphConfig
from .human_loop import HumanInTheLoopSubgraph
from .debate import DebateVotingSubgraph
from .pipeline import PipelineReflectionSubgraph
from .selection import SelectionSubgraph
from .homepage_generator import HomepageGeneratorSubgraph
from .requirement import RequirementSubgraph
from .design import DesignSubgraph
from .tech import TechSubgraph
from .feature import FeatureSubgraph
from .code import CodeSubgraph
from .delivery import DeliverySubgraph

__all__ = [
    # 类型
    "SubgraphType",
    "SubgraphMode",
    "StateT",
    "ConfigT",
    # 基类
    "BaseSubgraph",
    "SubgraphConfig",
    "HumanInTheLoopSubgraph",
    "DebateVotingSubgraph",
    "PipelineReflectionSubgraph",
    "SelectionSubgraph",
    "HomepageGeneratorSubgraph",
    # 核心子图
    "RequirementSubgraph",
    "DesignSubgraph",
    "CodeSubgraph",
    "DeliverySubgraph",
    # 内部子图（DesignSubgraph 使用）
    "TechSubgraph",
    "FeatureSubgraph",
]
