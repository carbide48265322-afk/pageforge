"""PageForge Subgraph 基类体系

提供4种子图模式：
- HumanInTheLoopSubgraph: 人机协作模式
- DebateVotingSubgraph: 辩论投票模式  
- PipelineReflectionSubgraph: 流水线自审模式
- SelectionSubgraph: 功能选择模式
"""

from .base import BaseSubgraph, SubgraphMode
from .human_loop import HumanInTheLoopSubgraph
from .debate import DebateVotingSubgraph
from .pipeline import PipelineReflectionSubgraph
from .selection import SelectionSubgraph
from .requirement import RequirementSubgraph

__all__ = [
    "BaseSubgraph",
    "SubgraphMode",
    "HumanInTheLoopSubgraph",
    "DebateVotingSubgraph",
    "PipelineReflectionSubgraph",
    "SelectionSubgraph",
    "RequirementSubgraph",
]
