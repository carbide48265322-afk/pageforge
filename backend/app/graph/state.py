from typing import TypedDict, List, Optional, Dict, Any


# ========== 阶段快照类型 ==========

class RequirementSnapshot(TypedDict):
    """需求阶段确认后的快照"""
    confirmed: bool
    user_input: str
    clarification_qa: List[Dict]  # 澄清问答记录
    prd: str
    confirmed_at: str


class DesignSnapshot(TypedDict):
    """设计阶段确认后的快照"""
    confirmed: bool
    style_options: List[Dict]     # 生成的风格方案
    selected_style: Dict          # 用户选择的风格
    design_spec: Dict             # 设计规范
    confirmed_at: str


class TechSnapshot(TypedDict):
    """技术方案确认后的快照"""
    confirmed: bool
    combined_proposal: Dict       # 综合技术方案
    vote_summary: Dict            # 投票结果摘要
    confirmed_at: str


class FeatureSnapshot(TypedDict):
    """功能选择确认后的快照"""
    confirmed: bool
    project_mode: str             # demo / full
    selected_features: List[str]  # 选中的功能列表
    all_features: List[str]       # 可用功能列表
    confirmed_at: str


class CodeSnapshot(TypedDict):
    """代码生成完成后的快照"""
    api_spec: Dict
    mock_data: Dict
    frontend_code: Dict
    style_code: Dict
    extracted_homepage: str
    completed_at: str


class PhaseTransition(TypedDict):
    """阶段转换记录"""
    from_phase: str
    to_phase: str
    trigger: str                  # user_confirmed / auto / back
    timestamp: str


# ========== 主状态 ==========

class AgentState(TypedDict):
    """LangGraph 工作流状态 — 6 阶段 AI 应用生成器

    分为以下区域：
    - 会话标识
    - 阶段控制
    - 阶段快照（确认后保存）
    - 需求阶段
    - 设计阶段
    - 技术阶段
    - 功能选择阶段
    - 代码生成阶段
    - 交付阶段
    - 人机协作
    - 输出

    注意：旧的 HTML 生成器字段标记为 [DEPRECATED]，暂保留以兼容旧代码，
    后续清理时统一移除。
    """

    # ---- 会话标识 ----
    user_message: str                          # 用户输入消息
    session_id: str                            # 会话ID
    created_at: str                            # 创建时间

    # ---- 阶段控制 ----
    current_phase: str                         # 当前阶段: requirement/design/tech/feature/code/delivery/completed
    phase_status: str                          # 阶段状态: running/waiting_human/completed

    # ---- 阶段快照（确认后保存，用于回退） ----
    requirement_snapshot: Optional[RequirementSnapshot]
    design_snapshot: Optional[DesignSnapshot]
    tech_snapshot: Optional[TechSnapshot]
    feature_snapshot: Optional[FeatureSnapshot]
    code_snapshot: Optional[CodeSnapshot]

    # ---- 阶段历史 ----
    phase_history: List[PhaseTransition]       # 阶段转换记录

    # ---- 需求阶段 ----
    requirements_doc: str                      # 产品需求文档 (PRD)
    requirements_approved: bool                # 需求是否已确认

    # ---- 设计阶段 ----
    design_projects: List[Dict[str, Any]]      # 4套完整项目列表
    selected_style_id: Optional[str]           # 用户选中的风格ID
    selected_design: Optional[Dict[str, Any]]  # 用户选中的完整项目
    design_style: Optional[Dict[str, Any]]     # 选中的风格配置

    # ---- 技术阶段 ----
    tech_spec: Optional[Dict[str, Any]]        # 综合技术方案
    tech_approved: bool                        # 技术方案是否已确认

    # ---- 功能选择阶段 ----
    project_mode: Optional[str]                # demo / full
    selected_features: Optional[List[str]]     # 选中的功能列表
    available_features: Optional[List[str]]    # 可用功能列表
    feature_approved: bool                     # 功能选择是否已确认

    # ---- 代码生成阶段 ----
    api_spec: Optional[Dict[str, Any]]         # API 规范
    mock_data: Optional[Dict[str, Any]]        # Mock 数据
    frontend_code: Optional[Dict[str, Any]]    # 前端代码
    style_code: Optional[Dict[str, Any]]       # 样式代码
    extracted_homepage: Optional[str]          # 提取的首页HTML

    # ---- 交付阶段 ----
    delivery_approved: bool                    # 交付是否已确认
    revision_feedback: Optional[str]           # 修改反馈

    # ---- 人机协作 ----
    human_input_pending: bool                  # 是否等待用户输入
    human_input_checkpoint_id: Optional[str]   # 当前人机协作检查点ID
    human_input_request: Optional[Dict]        # 人机协作请求体

    # ---- 输出 ----
    response_message: str                      # 回复消息
    is_complete: bool                          # 是否完成
    project_config: Optional[Dict[str, Any]]   # 项目配置
    project_files: Optional[Dict[str, str]]    # 生成的项目文件

    # ---- [DEPRECATED] 旧 HTML 生成器字段，待清理 ----
    # 以下字段为旧架构遗留，各子图不应再写入
    base_html: str                             # [DEPRECATED]
    phase: str                                 # [DEPRECATED] 用 current_phase 替代
    stage: str                                 # [DEPRECATED]
    design_concept: str                        # [DEPRECATED] 合并到 requirement_snapshot
    selected_style: str                        # [DEPRECATED] 用 selected_style_id 替代
    available_styles: List[Dict[str, str]]     # [DEPRECATED]
    demo_html: str                             # [DEPRECATED]
    demo_instructions: str                     # [DEPRECATED]
    demo_link: str                             # [DEPRECATED]
    is_demo_ready: bool                        # [DEPRECATED]
    task_list: List[Dict[str, Any]]            # [DEPRECATED]
    current_html: str                          # [DEPRECATED]
    validation_errors: List[str]               # [DEPRECATED]
    iteration_count: int                       # [DEPRECATED]
    fix_count: int                             # [DEPRECATED]
    output_html: str                           # [DEPRECATED]
    output_version: int                        # [DEPRECATED]
    status: Optional[str]                      # [DEPRECATED] 用 phase_status 替代
