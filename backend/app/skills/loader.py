import os
import re
from pathlib import Path
from typing import Any


class SkillAutoLoader:
    """自动扫描并加载所有 Skill,转换为 LangChain Tools"""

    def __init__(self, skills_dir: str | Path):
        self.skills_dir = Path(skills_dir)

    def load_all(self) -> list[dict[str, Any]]:
        """扫描目录，自动发现所有 Skill"""
        skills = []

        if not self.skills_dir.exists():
            return skills

        for skill_name in sorted(self.skills_dir.iterdir()):
            if not skill_name.is_dir():
                continue

            skill_md = skill_name / "SKILL.md"
            if not skill_md.exists():
                continue

            metadata = self._parse_skill_md(skill_md)
            content = self._read_skill_content(skill_md)

            skills.append({
                "name": skill_name.name,
                "metadata": metadata,
                "content": content,
                "path": str(skill_name),
            })

        return skills

    def _parse_skill_md(self, path: Path) -> dict:
        """解析 SKILL.md 的 YAML frontmatter"""
        with open(path, encoding="utf-8") as f:
            raw = f.read()

        match = re.search(r"^---\n(.*?)\n---", raw, re.DOTALL)
        if match:
            try:
                import yaml
                return yaml.safe_load(match.group(1)) or {}
            except ImportError:
                # 没有 pyyaml，简单解析
                return self._simple_parse(match.group(1))
        return {}

    def _simple_parse(self, text: str) -> dict:
        """无 yaml 依赖时的简单 frontmatter 解析"""
        result = {}
        for line in text.strip().split("\n"):
            if ":" in line:
                key, _, value = line.partition(":")
                result[key.strip()] = value.strip().strip("\"'")
        return result

    def _read_skill_content(self, path: Path) -> str:
        """读取 SKILL.md 的正文内容（去掉 frontmatter）"""
        with open(path, encoding="utf-8") as f:
            raw = f.read()

        # 去掉 frontmatter
        match = re.search(r"^---\n.*?\n---\n?", raw, re.DOTALL)
        if match:
            return raw[match.end():].strip()
        return raw.strip()

from langchain_core.tools import tool


def create_skill_tools(skills_dir: str | Path) -> list:
    """将所有 Skill 转换为 LangChain Tools"""

    loader = SkillAutoLoader(skills_dir)
    skills = loader.load_all()

    tools = []

    for skill in skills:
        # 每个 skill 的内容缓存（闭包捕获）
        skill_content = skill["content"]
        skill_name = skill["name"]
        description = skill["metadata"].get("description", f"获取 {skill_name} 的设计指南")

        @tool
        def get_skill_guide(skill_name: str = skill_name, design_style: str = "modern") -> str:
            """{description}

            Args:
                skill_name: Skill 名称，如 "{skill_name}"
                design_style: 设计风格，可选值: modern（现代风格）, classic（经典风格）
            """
            # 根据设计风格调整内容
            style_prefix = """## 设计风格：{style_name}

"""
            if design_style == "modern":
                style_content = style_prefix.format(style_name="现代风格") + "采用简洁、扁平化的设计语言，强调空间感和层次感，使用鲜明的色彩对比和简约的线条。\n\n"
            elif design_style == "classic":
                style_content = style_prefix.format(style_name="经典风格") + "采用传统、优雅的设计语言，强调对称性和平衡感，使用柔和的色彩和精致的装饰元素。\n\n"
            else:
                style_content = style_prefix.format(style_name="现代风格") + "采用简洁、扁平化的设计语言，强调空间感和层次感，使用鲜明的色彩对比和简约的线条。\n\n"

            # 组合内容
            full_content = style_content + skill_content
            
            # 截断过长内容
            if len(full_content) > 4000:
                return full_content[:4000] + "\n\n...(内容过长，已截断)"
            return full_content

        # 修正 tool name 避免冲突
        get_skill_guide.name = f"skill_{skill_name.replace('-', '_')}"
        # 重新设置 description（docstring 会被 LangChain 解析）
        get_skill_guide.description = description

        tools.append(get_skill_guide)

    # 添加设计风格选择工具
    @tool
    def get_design_styles() -> str:
        """获取可用的设计风格选项"""
        return """## 可用设计风格

### modern（现代风格）
- 简洁、扁平化的设计语言
- 强调空间感和层次感
- 使用鲜明的色彩对比
- 简约的线条和几何形状
- 适合现代、科技感强的应用

### classic（经典风格）
- 传统、优雅的设计语言
- 强调对称性和平衡感
- 使用柔和的色彩
- 精致的装饰元素
- 适合正式、专业的应用"""

    get_design_styles.name = "get_design_styles"
    tools.append(get_design_styles)

    return tools