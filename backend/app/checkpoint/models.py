"""Checkpoint 数据模型"""
from typing import TypedDict, Optional, Any
from datetime import datetime
from enum import Enum


class CheckpointType(str, Enum):
    """检查点类型"""
    CLARIFICATION = "clarification"      # 需求澄清
    PRD_CONFIRMATION = "prd_confirmation"  # PRD 确认
    STYLE_SELECTION = "style_selection"    # 风格选择
    TECH_CONFIRMATION = "tech_confirmation"  # 技术方案确认
    FEATURE_SELECTION = "feature_selection"  # 功能选择
    DELIVERY_CONFIRMATION = "delivery_confirmation"  # 交付确认


class CheckpointData(TypedDict):
    """检查点数据"""
    session_id: str
    checkpoint_id: str
    phase: str                    # 当前阶段
    checkpoint_type: str          # 检查点类型
    state: dict                   # LangGraph 状态快照
    presentation: dict            # 展示给用户的内容
    options: Optional[list]       # 用户可选操作
    created_at: str
    expires_at: Optional[str]     # 过期时间


class HumanInputResponse(TypedDict):
    """用户输入响应"""
    checkpoint_id: str
    action: str                   # confirm / revise / back / cancel
    data: dict                    # 附加数据
    responded_at: str
