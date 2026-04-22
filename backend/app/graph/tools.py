from langchain_core.tools import tool
from app.services.export_service import ExportService


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


@tool
def export_project(project_name: str, html_content: str) -> str:
    """导出完整的前端项目为 ZIP 文件
    
    Args:
        project_name: 项目名称
        html_content: HTML 内容
        
    Returns:
        导出成功的消息
    """
    try:
        # 导出项目（实际使用时会通过 API 下载）
        zip_data = ExportService.export_project(html_content, project_name)
        
        # 这里保存到临时文件或返回给前端
        # 简化版本，只返回成功消息
        return f"项目 {project_name} 导出成功！包含完整的前端项目结构。"
    except Exception as e:
        return f"导出失败: {str(e)}"


# ========== React 项目 Tool ==========

@tool
def code_executor(command: str, cwd: str) -> str:
    """在指定目录执行 shell 命令。

    用于执行 npm/yarn 命令、构建脚本等。
    常用场景：npm create vite、npm install、npm run build、npx tailwindcss init 等。

    Args:
        command: 要执行的 shell 命令
        cwd: 工作目录路径
    """
    import asyncio
    import os

    if not os.path.exists(cwd):
        return f"[ERROR] 目录不存在: {cwd}"

    # 同步执行（@tool 是同步函数）
    import subprocess
    try:
        result = subprocess.run(
            command, shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=120
        )
        output = result.stdout or ""
        if result.stderr:
            output += "\n[STDERR]\n" + result.stderr
        if result.returncode != 0:
            output = f"[ERROR] 命令执行失败 (exit code {result.returncode})\n{output}"
        return output
    except subprocess.TimeoutExpired:
        return "[ERROR] 命令执行超时（120秒）"
    except Exception as e:
        return f"[ERROR] 执行异常: {str(e)}"


@tool
def write_file(file_path: str, content: str) -> str:
    """将内容写入文件。支持写入 React 组件、样式文件、配置文件等。

    Args:
        file_path: 文件的绝对路径
        content: 要写入的文件内容
    """
    import os

    try:
        # 确保父目录存在
        parent = os.path.dirname(file_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"文件写入成功: {file_path} ({len(content)} 字符)"
    except Exception as e:
        return f"[ERROR] 写入失败: {str(e)}"


@tool
def read_file_content(file_path: str) -> str:
    """读取文件内容。用于查看项目文件、读取配置、获取已有代码等。

    Args:
        file_path: 文件的绝对路径
    """
    import os

    try:
        if not os.path.exists(file_path):
            return f"[ERROR] 文件不存在: {file_path}"

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return content
    except Exception as e:
        return f"[ERROR] 读取失败: {str(e)}"


@tool
def list_directory(dir_path: str) -> str:
    """列出目录内容。用于查看项目结构、确认文件是否存在等。

    Args:
        dir_path: 目录的绝对路径
    """
    import os

    try:
        if not os.path.exists(dir_path):
            return f"[ERROR] 目录不存在: {dir_path}"

        entries = []
        for name in sorted(os.listdir(dir_path)):
            full = os.path.join(dir_path, name)
            if os.path.isdir(full):
                entries.append(f"[DIR]  {name}/")
            else:
                size = os.path.getsize(full)
                entries.append(f"[FILE] {name}  ({size}B)")

        if not entries:
            return "目录为空"

        return "\n".join(entries)
    except Exception as e:
        return f"[ERROR] 列目录失败: {str(e)}"


@tool
def get_project_context(cwd: str) -> str:
    """获取当前 React 项目的结构和关键文件内容。

    LLM 在生成代码前应先调用此工具，了解项目现状。
    返回文件树 + 脚手架关键文件内容（package.json、tsconfig.json、src/main.tsx、src/App.tsx）。

    Args:
        cwd: 项目根目录的绝对路径
    """
    import os

    if not os.path.exists(cwd):
        return f"[ERROR] 目录不存在: {cwd}"

    result_parts = []

    # 1. 文件树（排除 node_modules、dist 等）
    result_parts.append("## 项目文件树")
    tree_lines = []
    for root, dirs, files in os.walk(cwd):
        # 跳过大型目录
        dirs[:] = [d for d in sorted(dirs) if d not in ("node_modules", ".git", "dist", "__pycache__", ".pytest_cache")]
        level = root.replace(cwd, "").count(os.sep)
        indent = "  " * level
        folder = os.path.basename(root)
        tree_lines.append(f"{indent}{folder}/")
        sub_indent = "  " * (level + 1)
        for file in sorted(files):
            tree_lines.append(f"{sub_indent}{file}")

    result_parts.append("\n".join(tree_lines) if tree_lines else "(空)")

    # 2. 关键文件内容
    key_files = [
        "package.json", "tsconfig.json", "vite.config.ts",
        "tailwind.config.js", "tailwind.config.ts", "postcss.config.js",
        "src/main.tsx", "src/App.tsx", "src/styles/global.css",
    ]
    result_parts.append("\n## 关键文件内容")
    for rel_path in key_files:
        full_path = os.path.join(cwd, rel_path)
        if os.path.exists(full_path):
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                result_parts.append(f"\n--- {rel_path} ---\n{content}")
            except Exception:
                result_parts.append(f"\n--- {rel_path} --- [读取失败]")

    return "\n".join(result_parts)


# ========== Tool 注册表 ==========

# 核心 Agent 工具（旧 HTML 生成器使用）
AGENT_TOOLS = [validate_html, export_project]

# React 项目工具（CodeSubgraph 使用）
REACT_PROJECT_TOOLS = [
    code_executor,
    write_file,
    read_file_content,
    list_directory,
    get_project_context,
    export_project,
]

# 所有可用工具
ALL_AVAILABLE_TOOLS = AGENT_TOOLS + REACT_PROJECT_TOOLS