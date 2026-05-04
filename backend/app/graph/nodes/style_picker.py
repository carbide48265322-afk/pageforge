"""
Style Picker Node — P1.18
==========================

风格选择节点：
1. 从 state 取 ui_style（Intent Router 传入）
2. 调用 ui-ux-pro-max CLI 获取风格数据（--design-system 模式）
3. 加载 frontend-design 设计哲学约束
4. 合并为最终风格配置文本，存入 state.ui_style_config
5. 通过 SSE 推送 style_selected 事件

降级策略：
- CLI 不可用时 → 使用内置 _FALLBACK_STYLES（与 intent_router.py 共享）
- frontend-design 不可用时 → 跳过哲学注入
- 合并失败时 → 使用最小化配置
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Optional

from langgraph.config import get_stream_writer

from app.graph.nodes.intent_router import (
    _FALLBACK_STYLES,
    get_fallback_style_config,
)

logger = logging.getLogger(__name__)


# ========== 主节点函数 ==========

def style_picker_node(state: dict) -> dict:
    """
    风格选择节点函数
    
    输入: state["ui_style"], state["project_type"], state.get("tags", [])
    输出: state + ui_style_config (str, 用于注入后续 Prompt)
    """
    style_keyword = state.get("ui_style", "minimal")
    project_type = state.get("project_type", "react-vite-app")
    tags = state.get("tags", [])

    logger.info(f"[StylePicker] 开始处理风格: {style_keyword} (项目类型: {project_type})")

    # 构造查询关键词
    query_keywords = f"{style_keyword} {project_type}"
    if tags:
        query_keywords += " " + " ".join(tags[:3])  # 取前3个 tag

    # ---- 步骤1: 调用 ui-ux-pro-max CLI ----
    design_system = _fetch_design_system(query_keywords, style_keyword)

    # ---- 步骤2: 加载 frontend-design 设计哲学 ----
    design_philosophy = _load_frontend_design_rules()

    # ---- 步骤3: 合并为最终配置文本 ----
    final_config = _merge_style_config(design_system, design_philosophy, style_keyword)

    # ---- 步骤4: 通过 SSE 推送风格确认事件 ----
    try:
        writer = get_stream_writer()
        writer({
            "event": "style_selected",
            "data": {
                "style": style_keyword,
                "primary_color": (design_system.get("colors") or {}).get("primary", "#171717"),
                "description": f"已选择「{style_keyword}」风格",
            }
        })
    except Exception as e:
        logger.debug(f"[StylePicker] SSE 推送失败（非流式模式）: {e}")

    logger.info(f"[StylePicker] 风格配置完成: {style_keyword}")

    # 返回更新后的 state
    return {
        **state,
        "ui_style_config": final_config,
    }


# ========== 获取设计系统数据 ==========

def _fetch_design_system(query: str, fallback_style: str) -> dict:
    """
    调用 ui-ux-pro-max CLI 获取风格数据
    
    该 CLI 位于 skills/UI_UX/scripts/search.py
    参数: <query> --design-system -f json
    
    降级: CLI 不可用时使用内置配置
    """
    # 尝试定位 CLI 脚本
    # 路径相对于 backend/ 目录
    backend_dir = Path(__file__).parent.parent.parent
    cli_path = backend_dir / "skills" / "UI_UX" / "scripts" / "search.py"

    if not cli_path.exists():
        logger.warning(f"[StylePicker] CLI 不存在: {cli_path}，使用降级配置")
        return get_fallback_style_config(fallback_style)

    try:
        logger.debug(f"[StylePicker] 调用 CLI: {cli_path} {query}")
        result = subprocess.run(
            ["python3", str(cli_path), query, "--design-system", "-f", "json"],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(backend_dir),
        )

        if result.returncode != 0:
            logger.warning(f"[StylePicker] CLI 返回非零: {result.stderr[:200]}")
            return get_fallback_style_config(fallback_style)

        # 解析 JSON 输出
        output = result.stdout.strip()
        if not output:
            return get_fallback_style_config(fallback_style)

        design_system = json.loads(output)
        logger.info(f"[StylePicker] CLI 成功获取设计系统数据")
        return design_system

    except subprocess.TimeoutExpired:
        logger.warning("[StylePicker] CLI 超时（15s），使用降级配置")
    except json.JSONDecodeError as e:
        logger.warning(f"[StylePicker] CLI 输出 JSON 解析失败: {e}")
    except FileNotFoundError:
        logger.warning("[StylePicker] python3 未找到，使用降级配置")
    except Exception as e:
        logger.warning(f"[StylePicker] CLI 调用异常: {e}")

    return get_fallback_style_config(fallback_style)


# ========== 加载设计哲学 ==========

def _load_frontend_design_rules() -> str:
    """
    读取 frontend-design SKILL.md 的核心规则（Frontend Aesthetics Guidelines 部分）
    
    返回截断后的哲学文本（最多 1000 字符，避免 Prompt 过长）
    """
    backend_dir = Path(__file__).parent.parent.parent
    rules_path = backend_dir / "skills" / "frontend-design" / "SKILL.md"

    if not rules_path.exists():
        logger.debug(f"[StylePicker] frontend-design SKILL.md 不存在: {rules_path}")
        return ""

    try:
        content = rules_path.read_text(encoding="utf-8")

        # 尝试提取 Frontend Aesthetics Guidelines 部分
        # 查找关键段落并提取
        lines = content.split("\n")
        extracted = []
        in_section = False
        for line in lines:
            if "Aesthetic" in line or "美学" in line or "Design Philosophy" in line:
                in_section = True
                extracted.append(line)
                continue
            if in_section:
                if line.startswith("#") and len(extracted) > 0:
                    # 遇到下一个标题，结束提取
                    break
                extracted.append(line)

        if extracted:
            philosophy = "\n".join(extracted[:30])  # 最多取 30 行
        else:
            # 未找到特定段落，取前 30 行
            philosophy = "\n".join(lines[:30])

        # 截断过长内容
        if len(philosophy) > 1000:
            philosophy = philosophy[:1000] + "\n...(设计哲学已截断)"

        logger.debug(f"[StylePicker] 成功加载 frontend-design 哲学 ({len(philosophy)} 字符)")
        return philosophy

    except Exception as e:
        logger.warning(f"[StylePicker] 读取 frontend-design 失败: {e}")
        return ""


# ========== 合并风格配置 ==========

def _merge_style_config(design_system: dict, philosophy: str, style_keyword: str) -> str:
    """
    合并 ui-ux-pro-max 数据 + frontend-design 哲学 → 最终注入 Prompt 的文本
    
    返回格式化的配置文本（用于直接注入 LLM Prompt）
    """
    colors = design_system.get("colors", {})
    typography = design_system.get("typography", {})
    anti_patterns = design_system.get("anti_patterns", [])
    shadows = design_system.get("shadows", {})
    border_radius = design_system.get("border_radius", "0.375rem")

    # 构建配置文本
    config_lines = [
        "## UI 风格配置（由 Style Picker 自动生成）",
        "",
        f"- 主色调：{colors.get('primary', '#171717')}",
        f"- 辅助色：{colors.get('secondary', '#52525b')}",
        f"- 背景色：{colors.get('background', '#ffffff')}",
        f"- 强调色：{colors.get('accent', '#6366f1')}",
        f"- 字体族：{typography.get('font_family', "'Inter', system-ui, sans-serif")}",
        f"- 标题字重：{typography.get('heading_weight', '600')}",
        f"- 正文字号：{typography.get('body_size', '14px')}",
        f"- 圆角：{border_radius}",
        f"- 阴影：{json.dumps(shadows.get('sm', {}))}",
        "",
        "## 反模式约束（禁止事项，必须严格遵守）",
    ]

    # 添加反模式（最多 8 条）
    if anti_patterns:
        for p in anti_patterns[:8]:
            config_lines.append(f"- {p}")
    else:
        config_lines.append("- 不要用紫渐变")
        config_lines.append("- 不要用 Inter 之外的通用字体")
        config_lines.append("- 避免千篇一律的 AI 生成设计")

    # 添加设计哲学（如果有）
    if philosophy:
        config_lines.extend([
            "",
            "## 设计哲学（来自 frontend-design skill）",
            philosophy,
        ])

    config_lines.extend([
        "",
        f"## 风格关键词：{style_keyword}",
        "请严格遵循以上配置生成 UI 代码，不要偏离风格设定。",
    ])

    return "\n".join(config_lines)
