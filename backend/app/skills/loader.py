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

# create_skill_tools 函数已移除，因为技能现在直接作为内容注入系统提示
# 不再需要转换为 LangChain 工具