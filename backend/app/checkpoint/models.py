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
    HUMAN_INPUT = "human_input"          # 通用人工输入


class HumanInputType(str, Enum):
    """人机协作输入类型"""
    CONFIRM = "confirm"              # 确认/拒绝
    SELECT = "select"                # 单选
    MULTI_SELECT = "multi_select"    # 多选
    TEXT = "text"                    # 文本输入
    FORM = "form"                    # 复合表单


class HumanInputRequest(TypedDict):
    """人机协作请求 - 需要用户输入时创建"""
    checkpoint_id: str
    session_id: str
    phase: str                       # 当前阶段：prd_confirm, design_select 等
    input_type: str                  # HumanInputType 的值
    title: str                       # 表单标题
    description: str                 # 说明文字
    schema: dict                     # JSON Schema 定义表单结构
    context: dict                    # 上下文数据（如 PRD 内容）
    created_at: str
    expires_at: str                  # 过期时间


class HumanInputResponse(TypedDict):
    """用户输入响应"""
    checkpoint_id: str
    action: str                      # confirm / revise / back / cancel
    data: dict                       # 附加数据
    responded_at: str


class CheckpointData(TypedDict):
    """检查点数据"""
    session_id: str
    checkpoint_id: str
    phase: str                       # 当前阶段
    checkpoint_type: str             # 检查点类型
    status: str                      # pending, waiting_human, completed, expired
    state: dict                      # LangGraph 状态快照
    presentation: dict               # 展示给用户的内容
    options: Optional[list]          # 用户可选操作
    
    # 人机协作专用字段
    human_input_request: Optional[HumanInputRequest]   # 人机协作请求
    human_input_response: Optional[HumanInputResponse] # 人机协作响应
    
    created_at: str
    expires_at: Optional[str]        # 过期时间
