"""子图类型定义"""
from enum import Enum
from typing import TypeVar


class SubgraphType(str, Enum):
    """子图类型 - 决定内部执行模式"""
    HUMAN_IN_THE_LOOP = "human_in_the_loop"      # 人机协作
    DEBATE_VOTING = "debate_voting"              # 辩论投票
    PIPELINE_REFLECTION = "pipeline_reflection"  # 流水线自审
    SELECTION = "selection"                      # 功能选择
    SIMPLE = "simple"                            # 简单流程


class SubgraphMode(str, Enum):
    """子图执行模式"""
    INTERACTIVE = "interactive"      # 交互式（需要用户输入）
    AUTONOMOUS = "autonomous"        # 自主式（AI自运行）
    HYBRID = "hybrid"                # 混合式
    HIERARCHICAL = "hierarchical"    # 层级嵌套（支持子图内嵌子图）


# 泛型类型
StateT = TypeVar('StateT')
ConfigT = TypeVar('ConfigT')
