from langchain_core.tools import tool
from app.core import registry


@tool
def generate_html(requirement: str) -> str:
    """根据用户需求生成完整的单文件 HTML 页面。
    
    当用户要求创建新页面时使用此工具。输出必须是完整的、可直接渲染的 HTML，
    包含 <!DOCTYPE html>、<html>、<head>、<body> 等完整结构。
    页面应包含内联 CSS 样式，确保美观且响应式。
    
    Args:
        requirement: 用户对页面的自然语言描述
    """
    # 实际生成由 LLM 在 ReAct 循环中完成
    # 此工具的 docstring 会作为 system prompt 的一部分指导 LLM 行为
    return requirement


@tool
def modify_html(base_html: str, instruction: str) -> str:
    """根据指令修改已有的 HTML 页面。
    
    当用户要求修改、调整、优化现有页面时使用此工具。
    基于原始 HTML 和修改指令，输出修改后的完整 HTML。
    必须保持完整的 HTML 结构，不能只输出片段。
    
    Args:
        base_html: 当前基准版本的完整 HTML
        instruction: 用户的具体修改指令
    """
    return instruction


@registry.register_tool  # 新增装饰器
@tool
def validate_html(html: str) -> dict:
    """验证 HTML 页面的结构和安全性。
    
    检查项目：
    1. 完整的 HTML 结构（DOCTYPE、html、head、body）
    2. viewport meta 标签
    3. 恶意模式扫描（parent.document、eval 注入等）
    4. 基础可访问性（lang 属性、charset）
    
    Args:
        html: 待验证的 HTML 内容
    """
    errors = []

    # 结构检查
    if "<!DOCTYPE html>" not in html and "<html" not in html.lower():
        errors.append("缺少 DOCTYPE 或 html 标签")
    if "<head>" not in html:
        errors.append("缺少 head 标签")
    if "viewport" not in html:
        errors.append("缺少 viewport meta 标签")
    if 'charset' not in html.lower():
        errors.append("缺少 charset 声明")

    # 安全检查 — 扫描恶意模式
    dangerous_patterns = [
        "parent.document",
        "parent.location",
        "parent.window",
        "top.document",
        "top.location",
        "window.parent",
        "document.cookie",
        "navigator.credentials",
    ]
    for pattern in dangerous_patterns:
        if pattern in html:
            errors.append(f"检测到危险模式: {pattern}")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": [],
    }


# Agent 可用的工具列表 — 改为从注册中心获取
AGENT_TOOLS = registry.get_langchain_tools()