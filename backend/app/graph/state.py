from typing import TypedDict, Optional, List, Dict


class AgentState(TypedDict):
    """LangGraph 工作流状态 — 在各节点之间传递的数据结构"""

    # ---- 输入 ----
    user_message: str       # 用户发送的消息
    session_id: str         # 当前会话 ID
    base_html: str          # 当前基准版本的 HTML（修改时基于此版本）

    # ---- 中间状态 ----
    task_list: list[dict]   # 意图理解后拆解的任务列表 [{action, target, details}, ...]
    current_html: str       # 当前生成的 HTML（执行节点输出）
    validation_errors: list[str]  # 质量检查发现的错误/警告
    iteration_count: int    # ReAct 循环迭代次数（防止无限循环）
    fix_count: int          # 自动修复次数（最多 3 次）

    # ---- 输出 ----
    response_message: str   # 最终回复给用户的消息
    output_html: Optional[str]        # 最终输出的 HTML（新项目可为 None）
    output_version: int     # 最终保存的版本号
    is_complete: bool       # 工作流是否完成

    # ---- 新字段（全部 Optional，兼容旧数据） ----
    project_type: Optional[str]           # "react-vite-app"
    files: Optional[List[dict]]          # 新：多文件列表
    project_id: Optional[str]            # WebContainer 项目 ID
    install_status: Optional[str]       # installing / done / failed
    dev_server_url: Optional[str]       # 预览 URL
    ui_style: Optional[str]             # minimal / vibrant / dark / glassmorphism
    intent: Optional[str]               # 意图类型
    confidence: Optional[float]         # 意图置信度
    tags: Optional[List[str]]           # 技术标签
    mode: Optional[str]                 # frontend / backend / fullstack
    complexity: Optional[str]           # simple / medium / complex
    model_strategy: Optional[Dict[str, str]]  # 智能路由策略 {node_name: model_tier}
    thought_summary: Optional[str]     # 思考摘要
    plan_steps: Optional[List[dict]]   # 计划步骤
    ui_style_config: Optional[str]     # 风格配置文本
    status: Optional[str]             # 狀態標識