from typing import TypedDict


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
    output_html: str        # 最终输出的 HTML
    output_version: int     # 最终保存的版本号
    is_complete: bool       # 工作流是否完成