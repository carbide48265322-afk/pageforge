"""
Style Picker Node — P1.18
==========================

风格选择节点：
1. 从 state 取 ui_style（Intent Router 传入）
2. 调用 【Meooo】高级UI_UX 设计智能系统_v3 获取风格 tokens
   - 读取 database.yaml 按产品类型/品牌调性/受众打分 → 选 Top 风格
   - 读取 styles/<slug>.md 获取完整 design tokens
3. 加载 frontend-design 设计哲学约束
4. 合并为最终风格配置文本，存入 state.ui_style_config
5. 通过 SSE 推送 style_selected 事件

降级策略：
- Meooo skill 不可用时 → 使用 intent_router 共享的 _FALLBACK_STYLES
- frontend-design 不可用时 → 跳过哲学注入
- 合并失败时 → 使用最小化配置
"""

import json
import logging
from pathlib import Path
from typing import Optional

import yaml
from langgraph.config import get_stream_writer

logger = logging.getLogger(__name__)

# ─── Meooo skill 路径 ────────────────────────────────────
# __file__ = backend/app/graph/nodes/style_picker.py
# skills/ 目录位于项目根 pageforge/（5 级 parent）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_MEOOO_DIR = _PROJECT_ROOT / "skills" / "【Meoo】高级UI_UX 设计智能系统_v3"
_MEOOO_DB = _MEOOO_DIR / "database.yaml"
_MEOOO_STYLES_DIR = _MEOOO_DIR / "styles"
_FRONTEND_DESIGN_SKILL = _PROJECT_ROOT / "skills" / "frontend-design" / "SKILL.md"

# ─── Fallback 风格配置（与 intent_router 共享同一份 JSON）──
import json as _json
_FALLBACK_STYLES_PATH = _PROJECT_ROOT / "backend" / "app" / "prompts" / "fallback_styles.json"
with open(_FALLBACK_STYLES_PATH, "r", encoding="utf-8") as _f:
    _FALLBACK_STYLES: dict = _json.load(_f)


def get_fallback_style_config(style: str) -> dict:
    """获取内置降级风格配置（当 Meooo skill 不可用时使用）"""
    return _FALLBACK_STYLES.get(style, _FALLBACK_STYLES["minimal"])


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

    # ---- 步骤1: 从 Meooo skill 获取设计系统数据 ----
    design_system = _fetch_from_meooo(style_keyword, project_type, tags)

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

    return {
        **state,
        "ui_style_config": final_config,
    }


# ========== 从 Meooo skill 获取设计数据 ==========

def _slugify(style_name: str) -> str:
    """把风格名转为 slug 格式（lower-case, 空格替换为连字符）"""
    return style_name.strip().lower().replace(" ", "-")


def _fetch_from_meooo(style_keyword: str, project_type: str, tags: list) -> dict:
    """
    从 【Meooo】高级UI_UX 设计智能系统_v3 获取风格数据。

    流程：
    1. 读取 database.yaml，按产品类型打分选 Top 风格
    2. 读取对应的 styles/<slug>.md 获取完整 tokens
    3. 若 Meooo 不可用则降级到 _FALLBACK_STYLES
    """
    # ── 降级：Meooo skill 不存在 ──
    if not _MEOOO_DB.exists():
        logger.warning(f"[StylePicker] Meooo skill 不存在: {_MEOOO_DB}，使用降级配置")
        return get_fallback_style_config(style_keyword)

    try:
        db = yaml.safe_load(_MEOOO_DB.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"[StylePicker] database.yaml 解析失败: {e}，使用降级配置")
        return get_fallback_style_config(style_keyword)

    # ── 步骤1: 查询匹配的风格 slug ──
    matched_slug = _query_matched_style(db, style_keyword, project_type, tags)

    # ── 步骤2: 读取风格文件 ──
    if matched_slug:
        style_data = _load_style_file(matched_slug)
        if style_data:
            logger.info(f"[StylePicker] Meooo 匹配风格: {matched_slug} → {style_data.get('name', matched_slug)}")
            return style_data

    # ── 降级：未找到匹配 ──
    logger.info(f"[StylePicker] Meooo 未匹配到风格，使用降级配置")
    return get_fallback_style_config(style_keyword)


def _query_matched_style(db: dict, style_keyword: str, project_type: str, tags: list) -> Optional[str]:
    """
    基于 database.yaml 查询最匹配的风格 slug。

    优先级：
    1. style_keyword 直接匹配某个 slug
    2. database.yaml product_types 按项目类型推荐
    3. tags 中的关键词辅助匹配
    """
    product_types = db.get("product_types", {})

    # 尝试将 project_type 映射到 database.yaml 的 key
    # project_type 可能是 "react-vite-app" / "saas" 等
    pt_key = _map_project_type(project_type)

    if pt_key and pt_key in product_types:
        pt_entry = product_types[pt_key]
        primary = pt_entry.get("primary", [])
        if primary:
            return primary[0]  # 取第一个 primary 推荐

    # 回退：遍历所有 product_types 找 keyword 匹配
    for pt_key, entry in product_types.items():
        if pt_key in style_keyword or style_keyword in pt_key:
            primary = entry.get("primary", [])
            if primary:
                return primary[0]

    # 最后尝试：style_keyword 本身作为 slug
    candidate = _slugify(style_keyword)
    if (_MEOOO_STYLES_DIR / f"{candidate}.md").exists():
        return candidate

    return None


def _map_project_type(project_type: str) -> Optional[str]:
    """将 project_type 映射到 database.yaml 的产品类型 key"""
    mapping = {
        "react-vite-app": "saas",
        "saas": "saas",
        "micro-saas": "micro-saas",
        "ecommerce": "ecommerce",
        "fintech": "fintech",
        "healthcare": "healthcare",
        "edtech": "edtech",
        "devtools": "devtools",
        "ai-ml": "ai-ml",
        "web3": "web3",
        "gaming": "gaming",
        "productivity": "productivity",
        "design-tools": "design-tools",
        "media-streaming": "media-streaming",
        "automotive": "automotive",
    }
    pt_lower = project_type.lower().strip()
    return mapping.get(pt_lower, pt_lower if pt_lower in mapping else None)


def _load_style_file(slug: str) -> Optional[dict]:
    """
    读取 styles/<slug>.md 并解析为 design_system dict。

    Meooo 风格文件格式：
    - frontmatter: name/version/description/keywords/style_type（无结构化颜色字段）
    - body: ## Design Tokens（Colors/Typography/Border/Shadow）+ ## Component Recipes
    """
    style_path = _MEOOO_STYLES_DIR / f"{slug}.md"
    if not style_path.exists():
        return None

    try:
        content = style_path.read_text(encoding="utf-8")

        # 分离 frontmatter 和 body
        if content.startswith("---"):
            parts = content.split("---", 2)
            frontmatter = yaml.safe_load(parts[1]) if len(parts) >= 3 else {}
            body = parts[2].strip() if len(parts) >= 3 else content
        else:
            frontmatter = {}
            body = content

        # 从 body 中提取 Design Tokens
        tokens = _extract_tokens_from_body(body)

        return {
            "name": frontmatter.get("name", slug),
            "slug": slug,
            "description": frontmatter.get("description", ""),
            "colors": tokens.get("colors", {}),
            "typography": tokens.get("typography", {}),
            "border_radius": tokens.get("border_radius", "0.375rem"),
            "shadows": tokens.get("shadows", {}),
            "anti_patterns": tokens.get("anti_patterns", []),
            "component_recipes": tokens.get("component_recipes", {}),
            # 保留 Design Tokens 原始文本供 _merge 使用
            "_tokens_text": tokens.get("raw_text", "")[:1200],
            "source": f"meooo/{slug}.md",
        }

    except Exception as e:
        logger.warning(f"[StylePicker] 读取风格文件失败 {style_path}: {e}")
        return None


def _extract_tokens_from_body(body: str) -> dict:
    """
    从风格文件 body 中提取 Design Tokens。

    解析 ## Design Tokens 下的 Colors / Typography / Border / Shadow 等子段落，
    以及 ## Forbidden / Anti-patterns 段落。
    """
    result = {
        "colors": {},
        "typography": {},
        "border_radius": "0.375rem",
        "shadows": {},
        "anti_patterns": [],
        "component_recipes": {},
        "raw_text": "",
    }

    lines = body.split("\n")
    current_section = None  # e.g. "colors", "typography", "shadow", "anti_patterns"
    token_lines = []

    for line in lines:
        stripped = line.strip()

        # 检测 ## Design Tokens 开始
        if stripped == "## Design Tokens":
            current_section = "tokens"
            continue

        # 检测其他 ## 标题（结束 Design Tokens 区域）
        # 注意：只有从 tokens 层级遇到 ## 才退出；子章节内不退出
        if current_section == "tokens" and stripped.startswith("## ") and stripped != "## Design Tokens":
            current_section = None
            break
        # 子章节中遇到 ## 也退出（如 ## Component Recipes）
        if current_section in ("colors", "typography", "border", "shadow", "other") and stripped.startswith("## "):
            current_section = None
            break

        # 检测 ### 子标题（在 Design Tokens 区域内）
        if current_section in ("tokens", "colors", "typography", "border", "shadow", "other") and stripped.startswith("### "):
            sub = stripped[4:].lower()
            if "color" in sub:
                current_section = "colors"
            elif "typography" in sub or "font" in sub:
                current_section = "typography"
            elif "border" in sub or "radius" in sub:
                current_section = "border"
            elif "shadow" in sub:
                current_section = "shadow"
            else:
                current_section = "other"
            continue

        # 收集 token 行
        if current_section in ("colors", "typography", "border", "shadow") and stripped.startswith("- "):
            token_lines.append(stripped)
            item = stripped[2:].strip()

            # 解析 "Key: `value`" 格式
            if ":" in item:
                key, _, value = item.partition(":")
                key = key.strip().lower()
                # 去掉反引号
                value = value.strip().strip("`")

                if current_section == "colors":
                    # Meooo 风格使用 Tailwind class 描述颜色
                    # 通用 key → field 映射，覆盖所有 140 个风格文件的 key 变体
                    # key 已在第 306 行转为小写
                    field = None
                    if "primary" in key and "bg" in key:
                        field = "bg_primary"
                    elif "primary" in key and "text" in key:
                        field = "text_primary"
                    elif "primary" in key and "button" in key:
                        field = "button_primary"
                    elif "secondary" in key and "bg" in key:
                        field = "bg_secondary"
                    elif "secondary" in key and "text" in key:
                        field = "text_secondary"
                    elif "dark" in key and "bg" in key:
                        field = "bg_dark"
                    elif "muted" in key:
                        field = "text_muted"
                    elif "border" in key:
                        field = "border"
                    elif "accent" in key and "hover" in key:
                        field = "accent_hover"
                    elif "accent" in key:
                        field = "accent"
                    elif "elevated" in key and "bg" in key:
                        field = "bg_elevated"
                    elif "warm" in key and "bg" in key:
                        field = "bg_warm"
                    elif "surface" in key:
                        field = "surface"
                    elif "primary" in key:
                        field = "primary"
                    elif "secondary" in key:
                        field = "secondary"
                    if field:
                        result["colors"].setdefault(field, value)
                    else:
                        # 其他未预见的 key 以原始 key 存入
                        result["colors"].setdefault(key.replace(" ", "_"), value)

                elif current_section == "typography":
                    if "font" in key and ("family" in key or "font_family" in key.replace(" ", "_")):
                        result["typography"]["font_family"] = value
                    elif "heading" in key and "weight" not in key:
                        result["typography"]["heading_class"] = value
                    elif "body" in key and "size" not in key:
                        result["typography"]["body_class"] = value
                    elif "weight" in key:
                        result["typography"]["heading_weight"] = value

                elif current_section == "border":
                    if "radius" in key:
                        result["border_radius"] = value

                elif current_section == "shadow":
                    result["shadows"].setdefault("sm", value)

    # 收集 anti-patterns（在 body 其他位置）
    # 匹配 "## Forbidden Patterns" 或 "## Anti-patterns" 标题
    in_forbidden = False
    for line in lines:
        stripped = line.strip()
        # 精确匹配 ## 级别的 Forbidden/Anti-pattern 标题
        if stripped.startswith("## ") and ("forbidden" in stripped.lower() or "anti-pattern" in stripped.lower()):
            in_forbidden = True
            continue
        if in_forbidden:
            if stripped.startswith("## "):
                in_forbidden = False
                continue
            if stripped.startswith("- "):
                result["anti_patterns"].append(stripped[2:].strip())
            elif stripped.startswith("Pattern:"):
                # 正则模式形式的禁止项，如 "Pattern: `^bg-gradient`"
                pattern_val = stripped[len("Pattern:"):].strip().strip("`")
                result["anti_patterns"].append(f"禁止匹配模式: {pattern_val}")

    result["raw_text"] = "\n".join(token_lines[:20])
    return result


def _looks_like_color(value: str) -> bool:
    """判断字符串是否像颜色值（hex / rgb / Tailwind class）"""
    v = value.lower()
    if v.startswith("#") or v.startswith("rgb") or v.startswith("hsl"):
        return True
    # Tailwind 颜色类如 bg-black, text-white
    color_keywords = ["black", "white", "gray", "slate", "zinc", "red", "blue", "green",
                      "yellow", "purple", "pink", "indigo", "violet", "cyan", "teal", "orange"]
    return any(kw in v for kw in color_keywords)


# ========== 加载设计哲学 ==========

def _load_frontend_design_rules() -> str:
    """
    读取 frontend-design SKILL.md 的核心规则（Frontend Aesthetics Guidelines 部分）

    返回截断后的哲学文本（最多 1000 字符，避免 Prompt 过长）
    """
    if not _FRONTEND_DESIGN_SKILL.exists():
        logger.debug(f"[StylePicker] frontend-design SKILL.md 不存在: {_FRONTEND_DESIGN_SKILL}")
        return ""

    try:
        content = _FRONTEND_DESIGN_SKILL.read_text(encoding="utf-8")

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
                    break
                extracted.append(line)

        if extracted:
            philosophy = "\n".join(extracted[:30])
        else:
            philosophy = "\n".join(lines[:30])

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
    合并 Meooo 数据 + frontend-design 哲学 → 最终注入 Prompt 的文本

    Meooo 风格使用 Tailwind CSS class（而非 hex 值）描述颜色，
    输出时直接列出这些 class，供 LLM 在生成代码时使用。
    """
    colors = design_system.get("colors", {})
    typography = design_system.get("typography", {})
    anti_patterns = design_system.get("anti_patterns", [])
    shadows = design_system.get("shadows", {})
    border_radius = design_system.get("border_radius", "0.375rem")
    source = design_system.get("source", "fallback")
    tokens_text = design_system.get("_tokens_text", "")
    description = design_system.get("description", "")

    config_lines = [
        "## UI 风格配置（由 Style Picker + 设计 Kungfu 生成）",
        f"- 风格来源：{source}",
    ]

    if description:
        config_lines.append(f"- 风格描述：{description}")

    config_lines.append("")

    # ── 颜色（Tailwind class 格式）──
    config_lines.append("## 颜色系统（Tailwind CSS class）")
    color_items = [
        ("主背景色", colors.get("bg_primary", "")),
        ("次背景色", colors.get("bg_secondary", "")),
        ("深色背景", colors.get("bg_dark", "")),
        ("主文字色", colors.get("text_primary", "")),
        ("次文字色", colors.get("text_secondary", "")),
        ("弱化文字", colors.get("text_muted", "")),
        ("主按钮", colors.get("button_primary", "")),
        ("边框色", colors.get("border", "")),
        ("强调色", colors.get("accent", "")),
    ]
    for label, value in color_items:
        if value:
            config_lines.append(f"- {label}：`{value}`")

    config_lines.append("")

    # ── 字体 ──
    config_lines.append("## 字体系统")
    if typography.get("font_family"):
        config_lines.append(f"- 字体族：`{typography['font_family']}`")
    if typography.get("heading_class"):
        config_lines.append(f"- 标题样式：`{typography['heading_class']}`")
    if typography.get("body_class"):
        config_lines.append(f"- 正文样式：`{typography['body_class']}`")
    if typography.get("heading_weight"):
        config_lines.append(f"- 标题字重：`{typography['heading_weight']}`")

    config_lines.append("")

    # ── 圆角 & 阴影 ──
    config_lines.append("## 圆角 & 阴影")
    config_lines.append(f"- 圆角：`{border_radius}`")
    if shadows.get("sm"):
        config_lines.append(f"- 小阴影：`{shadows['sm']}`")

    config_lines.append("")

    # ── 反模式 ──
    config_lines.append("## 反模式约束（禁止事项，必须严格遵守）")
    if anti_patterns:
        for p in anti_patterns[:10]:
            config_lines.append(f"- {p}")
    else:
        config_lines.append("- 不要用紫渐变")
        config_lines.append("- 不要用 Inter 之外的通用字体")
        config_lines.append("- 避免千篇一律的 AI 生成设计")

    # ── 设计哲学 ──
    if philosophy:
        config_lines.extend([
            "",
            "## 设计哲学（来自 frontend-design skill）",
            philosophy,
        ])

    # ── 风格 tokens 原文 ──
    if tokens_text:
        config_lines.extend([
            "",
            "## 完整 Design Tokens（来自 设计 Kungfu）",
            tokens_text,
        ])

    config_lines.extend([
        "",
        f"## 风格关键词：{style_keyword}",
        "请严格遵循以上配置生成 UI 代码，不要偏离风格设定。",
        "优先使用上述 Tailwind CSS class，不要替换为其他值。",
    ])

    return "\n".join(config_lines)
