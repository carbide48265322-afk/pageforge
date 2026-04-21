import re
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from app.config import llm,intent_llm
from app.graph.state import AgentState
from app.graph.tools import AGENT_TOOLS
from app.skills.loader import create_skill_tools
from app.config import SKILLS_DIR
from app.graph.nodes_human import human_input_node
# 工具名到工具对象的映射，用于 ReAct 循环中查找和执行工具
TOOL_MAP = {tool.name: tool for tool in AGENT_TOOLS}

# 意图识别的系统提示
INTENT_PROMPT = """分析用户的消息，判断用户想要对页面做什么操作。

可选操作类型:
- create: 创建新页面（用户要求从头做一个新页面）
- modify: 修改页面（用户要求调整、修改现有页面）
- style: 调整样式（用户要求改颜色、字体、布局、主题等）
- content: 修改内容（用户要求改文字、文案、图片等）

只返回一个 JSON 对象，格式: {"action": "操作类型", "target": "用户原始需求", "details": "补充说明"}"""

# Agent 系统提示 — 定义 Agent 的角色、能力和输出规范
SYSTEM_PROMPT = """你是 PageForge 的页面生成 Agent。你的任务是根据用户需求生成或修改单文件 HTML 页面。

## 严格规则
1. 输出必须是完整的、可直接在浏览器渲染的单文件 HTML
2. 必须包含 <!DOCTYPE html>、<html lang="zh">、<head>、<body>
3. 使用内联 CSS（<style> 标签），不依赖外部 CDN 或资源
4. 必须包含 <meta name="viewport" content="width=device-width, initial-scale=1.0">
5. 确保响应式设计，适配桌面和移动端
6. 生成完成后，调用 validate_html 工具检查质量
7. 如果验证有错误，修复后重新验证，直到通过

## 工作流程
1. 调用可用的 skill 工具获取设计指南（如 skills_frontend_design）
2. 根据指南和用户需求生成页面
3. 调用 validate_html 检查质量
4. 如有错误则修复并重新验证

## 输出格式
最终回复中直接输出完整的 HTML 代码，用 ```html ``` 代码块包裹。"""

async def intent_node(state: AgentState) -> dict:
    """意图理解节点 — 使用轻量 LLM 分析用户消息，拆解为任务列表"""
    user_message = state["user_message"]

    try:
        response = await intent_llm.ainvoke([
            SystemMessage(content=INTENT_PROMPT),
            HumanMessage(content=user_message),
        ])

        import json
        import re
        # 从回复中提取 JSON
        content = response.content.strip()
        # 尝试匹配 JSON 块
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            task = json.loads(match.group())
            task_list = [{
                "action": task.get("action", "create"),
                "target": task.get("target", user_message),
                "details": task.get("details", ""),
            }]
        else:
            # 解析失败，默认创建
            task_list = [{"action": "create", "target": user_message, "details": ""}]
    except Exception:
        # LLM 调用失败，兜底为创建
        task_list = [{"action": "create", "target": user_message, "details": ""}]

    return {
        "task_list": task_list,
        "iteration_count": 0,
        "fix_count": 0,
    }

# 启动时加载所有 Skill 工具
_skill_tools = create_skill_tools(SKILLS_DIR)
print(f"[Skill] 已加载 {len(_skill_tools)} 个 Skill 工具:")
for t in _skill_tools:
    print(f"  - {t.name}: {t.description[:50]}...")
# 合并核心工具 + Skill 工具
ALL_TOOLS = list(AGENT_TOOLS) + _skill_tools
async def execute_node(state: AgentState) -> dict:
    """ReAct 执行节点 — 调用 LLM 生成/修改 HTML

    ReAct 循环流程:
    1. LLM 思考并决定调用哪个工具
    2. 执行工具，获取结果
    3. 将工具结果反馈给 LLM
    4. 重复直到 LLM 给出最终回复（HTML）
    """
    task = state["task_list"][0] if state["task_list"] else {}
    action = task.get("action", "create")
    requirement = task.get("target", state["user_message"])
    base_html = state.get("base_html", "")
    fix_errors = state.get("validation_errors", [])


    if action == "modify" and base_html:
        user_content = f"""用户需求: {requirement}
        请修改以下 HTML 页面。保持原有结构，只按需求调整。
        原始 HTML:
        ```html
        {base_html}
        ```     
        """
    elif fix_errors:
        # 修复模式 — validate_node 发现错误后回到此节点
        user_content = f"""上次生成的 HTML 存在以下问题:
        {chr(10).join(f'- {e}' for e in fix_errors)}
        请修复这些问题，输出修复后的完整 HTML。

        当前 HTML:
        ```html
        {state.get("current_html", "")}
        """
    else:
        # 创建模式
        user_content = f"用户需求: {requirement}\n\n请创建一个全新的 HTML 页面。"

        # 初始化消息列表
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]
        # 绑定工具到 LLM
        llm_with_tools = llm.bind_tools(ALL_TOOLS)
        # ReAct 循环 — 最多 5 轮，防止无限循环
        max_iterations = 5
        html = ""

        for _ in range(max_iterations):
            response = await llm_with_tools.ainvoke(messages)
            messages.append(response)

            if response.tool_calls:
                # LLM 决定调用工具 — 执行并反馈结果
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = dict(tool_call["args"])

                    # modify_html 工具需要注入 base_html
                    if tool_name == "modify_html" and base_html:
                        tool_args["base_html"] = base_html

                    # 查找并执行工具
                    tool_fn = TOOL_MAP.get(tool_name)
                    if tool_fn:
                        result = await tool_fn.ainvoke(tool_args)
                        messages.append(
                            ToolMessage(
                                content=str(result),
                                tool_call_id=tool_call["id"],
                            )
                        )
            else:
                # LLM 没有调用工具 = 给出最终回复，提取 HTML
                html = _extract_html(response.content)
                break

        return {
            "current_html": html,
            "iteration_count": state.get("iteration_count", 0) + 1,
        }

def _extract_html(content: str) -> str:
    """从 LLM 回复中提取 HTML 内容
    
    依次尝试: 代码块 → DOCTYPE 匹配 → 整体返回
    """
    if not content:
        return ""

    # 优先从 ```html ``` 代码块中提取
    match = re.search(r"```html\s*(.*?)\s*```", content, re.DOTALL)
    if match:
        return match.group(1).strip()

    # 尝试匹配 DOCTYPE 开头
    match = re.search(r"(<!DOCTYPE html>.*</html>)", content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # 兜底：返回全部内容
    return content.strip()

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


async def start_node(state: AgentState) -> dict:
    """开始阶段节点 — 初始化项目设置和参数"""
    user_message = state["user_message"]
    
    # 初始化项目配置
    project_config = {
        "project_name": "New Project",
        "description": user_message[:100],
        "created_at": state.get("created_at", None),
        "status": "started"
    }
    
    return {
        "project_config": project_config,
        "stage": "start",
        "task_list": [{"action": "create", "target": user_message, "details": "Initial project setup"}]
    }


async def ideate_node(state: AgentState) -> dict:
    """构想阶段节点 — 生成产品需求文档和设计概念"""
    user_message = state["user_message"]
    project_config = state.get("project_config", {})
    
    # 获取可用的设计风格
    from app.skills.loader import get_design_styles
    available_styles = get_design_styles()
    
    # 生成产品需求文档
    requirements_prompt = f"""基于用户需求生成详细的产品需求文档：{user_message}
    
    请生成以下内容：
    1. 项目概述
    2. 功能需求
    3. 非功能需求
    4. 页面结构设计
    5. 交互设计要点
    
    用清晰的 Markdown 格式输出。"""
    
    response = await llm.ainvoke([
        SystemMessage(content="你是一位专业的产品经理，擅长生成详细的产品需求文档。"),
        HumanMessage(content=requirements_prompt),
    ])
    
    requirements_doc = response.content.strip()
    
    # 生成设计概念
    ideation_prompt = f"""基于用户需求生成设计概念：{user_message}
    
    请生成：
    1. 设计风格建议
    2. 页面结构布局
    3. 色彩方案
    4. 交互元素"""
    
    response = await llm.ainvoke([
        SystemMessage(content="你是一位专业的UI/UX设计师，擅长生成设计概念和方案。"),
        HumanMessage(content=ideation_prompt),
    ])
    
    design_concept = response.content.strip()
    
    return {
        "design_concept": design_concept,
        "requirements_doc": requirements_doc,
        "requirements_approved": False,
        "available_styles": available_styles,
        "selected_style": "modern",  # 默认风格
        "stage": "ideate",
        "phase": "ideation",
        "project_config": {**project_config, "design_concept": design_concept}
    }


async def demo_node(state: AgentState) -> dict:
    """演示阶段节点 — 生成可预览的演示版本"""
    current_html = state.get("current_html", "")
    project_config = state.get("project_config", {})
    
    # 生成演示说明
    demo_instructions = f"""演示版本说明：
    - 项目名称：{project_config.get('project_name', 'New Project')}
    - 设计概念：{project_config.get('design_concept', 'No concept')}
    - 生成时间：{state.get('created_at', 'Unknown')}
    """
    
    # 确保HTML存在
    if not current_html:
        # 如果没有HTML，生成一个基础演示页面
        demo_html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_config.get('project_name', 'Demo Page')}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
        }}
        .demo-info {{
            background-color: #f0f0f0;
            padding: 20px;
            border-radius: 4px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{project_config.get('project_name', 'Demo Page')}</h1>
        <p>这是一个演示版本的页面。</p>
        <div class="demo-info">
            <h3>设计概念</h3>
            <p>{project_config.get('design_concept', 'No concept')}</p>
        </div>
    </div>
</body>
</html>
"""
        current_html = demo_html
    
    return {
        "demo_html": current_html,
        "demo_instructions": demo_instructions,
        "stage": "demo",
        "is_demo_ready": True
    }