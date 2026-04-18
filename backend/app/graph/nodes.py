from app.graph.state import AgentState


async def intent_node(state: AgentState) -> dict:
    """意图理解节点 — 分析用户消息，拆解为任务列表
    MVP 阶段用关键词匹配，后续 Task 8 会替换为 LLM 分析
    """
    user_message = state["user_message"]
    task_list = []
    msg_lower = user_message.lower()

    # 关键词匹配判断意图
    if any(kw in msg_lower for kw in ["做", "创建", "生成", "新建", "build", "create"]):
        task_list.append({"action": "create", "target": user_message, "details": ""})
    elif any(kw in msg_lower for kw in ["改", "修改", "调整", "换", "change", "modify"]):
        task_list.append({"action": "modify", "target": user_message, "details": ""})
    elif any(kw in msg_lower for kw in ["颜色", "配色", "主题", "风格", "color", "style", "theme"]):
        task_list.append({"action": "style", "target": user_message, "details": ""})
    elif any(kw in msg_lower for kw in ["内容", "文案", "文字", "content", "text", "copy"]):
        task_list.append({"action": "content", "target": user_message, "details": ""})
    else:
        # 默认当作创建
        task_list.append({"action": "create", "target": user_message, "details": ""})

    return {
        "task_list": task_list,
        "iteration_count": 0,
        "fix_count": 0,
    }


async def execute_node(state: AgentState) -> dict:
    """ReAct 执行节点 — 调用 LLM 生成/修改 HTML
    MVP 阶段返回占位 HTML，Task 8 会集成真实 LLM
    """
    task = state["task_list"][0] if state["task_list"] else {}
    action = task.get("action", "create")
    target = task.get("target", "")
    base_html = state.get("base_html", "")

    if action == "create" or not base_html:
        # 首次创建 — 返回占位 HTML
        html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Page</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: system-ui, sans-serif; padding: 2rem; }}
        h1 {{ color: #333; margin-bottom: 1rem; }}
        p {{ color: #666; line-height: 1.6; }}
    </style>
</head>
<body>
    <h1>PageForge MVP</h1>
    <p>需求: {target}</p>
    <p style="margin-top: 1rem; color: #999; font-size: 0.875rem;">
        (LLM 生成将在 Task 8 中实现)
    </p>
</body>
</html>"""
    else:
        # 修改模式 — MVP 暂不改动
        html = base_html

    return {
        "current_html": html,
        "iteration_count": state.get("iteration_count", 0) + 1,
    }


async def validate_node(state: AgentState) -> dict:
    """质量检查节点 — 校验 HTML 结构和安全性"""
    html = state["current_html"]
    errors = []

    # 基础结构检查
    if "<!DOCTYPE html>" not in html and "<html" not in html.lower():
        errors.append("Missing DOCTYPE or html tag")
    if "<head>" not in html:
        errors.append("Missing head tag")
    if "viewport" not in html:
        errors.append("Missing viewport meta tag")

    return {
        "validation_errors": errors,
    }


async def save_node(state: AgentState) -> dict:
    """保存版本节点 — 将 HTML 写入文件系统，更新会话基准版本"""
    from app.services.version_service import VersionService
    from app.services.session_service import SessionService

    session_service = SessionService()
    version_service = VersionService()
    session_id = state["session_id"]

    # 获取会话，确定父版本
    session = session_service.get_session(session_id)
    parent_version = session.current_base_version if session and session.current_base_version > 0 else None

    # 保存新版本
    version = version_service.save_version(
        session_id=session_id,
        html=state["current_html"],
        summary=state["user_message"][:50],
        trigger_message=state["user_message"],
        parent_version=parent_version,
    )

    # 更新会话的基准版本为最新版本
    if session:
        session.current_base_version = version.version
        session_service.save_session(session)

    return {
        "output_html": state["current_html"],
        "output_version": version.version,
    }


async def respond_node(state: AgentState) -> dict:
    """生成回复节点 — 构建返回给用户的最终消息"""
    errors = state.get("validation_errors", [])
    version = state.get("output_version", 0)

    if errors:
        message = f"页面已生成（v{version}），但有 {len(errors)} 个警告：\n" + "\n".join(f"- {e}" for e in errors)
    else:
        message = f"页面已生成完成（v{version}），请查看预览。"

    return {
        "response_message": message,
        "is_complete": True,
    }