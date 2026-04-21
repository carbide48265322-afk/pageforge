from typing import TypedDict, List, Optional, Dict, Any


class AgentState(TypedDict):
    """LangGraph 工作流状态 — 在各节点之间传递的数据结构"""

    # ---- 输入 ----
    user_message: str
    session_id: str
    base_html: str
    created_at: str

    # ---- 构想阶段 ----
    phase: str
    stage: str
    project_config: Dict[str, Any]
    design_concept: str
    requirements_doc: str  # 产品需求文档
    requirements_approved: bool  # 需求是否已确认
    selected_style: str  # 选中的设计风格
    available_styles: List[Dict[str, str]]  # 可用的设计风格列表

    # ---- 演示阶段 ----
    demo_html: str
    demo_instructions: str
    demo_link: str
    is_demo_ready: bool
    project_files: Dict[str, str]  # 生成的项目文件

    # ---- 中间状态 ----
    task_list: List[Dict[str, Any]]
    current_html: str
    validation_errors: List[str]
    iteration_count: int
    fix_count: int

    # ---- 输出 ----
    response_message: str
    output_html: str
    output_version: int
    is_complete: bool
