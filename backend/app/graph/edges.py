from app.graph.state import AgentState


def should_fix(state: AgentState) -> str:
    """质量检查后的路由函数 — 决定下一步走修复还是保存
    
    返回值对应 graph.add_conditional_edges 中定义的 key:
    - "fix": 有错误且修复次数未超限，回到执行节点重新生成
    - "save": 通过检查或修复次数已满，进入保存节点
    """
    errors = state.get("validation_errors", [])
    fix_count = state.get("fix_count", 0)

    if errors and fix_count < 3:
        return "fix"
    return "save"


def should_wait_human(state: AgentState) -> str:
    """人机协作节点后的路由函数 — 决定是否等待用户响应
    
    返回值对应 graph.add_conditional_edges 中定义的 key:
    - "wait": 需要等待用户输入，图结束
    - "continue": 用户已响应，继续执行
    """
    if state.get("human_input_pending"):
        return "wait"
    return "continue"