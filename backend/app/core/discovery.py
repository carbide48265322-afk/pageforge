# backend/app/core/discovery.py
from pathlib import Path
import importlib.util
import re
from app.core.registry import ToolRegistry

class AutoDiscover:
    """自动发现并注册工具/技能"""

    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def discover_tools(self, tools_dir: Path) -> None:
        """发现并注册工具"""
        if not tools_dir.exists():
            return

        for py_file in tools_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue

            try:
                module = self._load_module(py_file)
                self._scan_module_for_tools(module)
            except Exception as e:
                print(f"Warning: Failed to load module {py_file}: {e}")

    def discover_skills(self, skills_dir: Path) -> None:
        """发现并注册技能"""
        if not skills_dir.exists():
            return

        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue

            try:
                metadata, content = self._parse_skill_file(skill_md)
                self.registry.register_skill(
                    name=skill_dir.name,
                    content=content,
                    metadata=metadata,
                    path=str(skill_dir)
                )
            except Exception as e:
                print(f"Warning: Failed to parse skill {skill_dir}: {e}")

    def _load_module(self, py_file: Path):
        """动态加载 Python 模块"""
        spec = importlib.util.spec_from_file_location(
            py_file.stem, py_file
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _scan_module_for_tools(self, module):
        """扫描模块中的 LangChain 工具"""
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (hasattr(attr, "name") and
                hasattr(attr, "description") and
                hasattr(attr, "invoke")):
                # 是 LangChain 工具
                self.registry.register_tool(attr)

    def _parse_skill_file(self, skill_path: Path):
        """解析技能文件"""
        content = skill_path.read_text(encoding="utf-8")

        # 解析 YAML frontmatter
        metadata = {}
        match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
        if match:
            try:
                import yaml
                metadata = yaml.safe_load(match.group(1)) or {}
            except ImportError:
                # 没有 pyyaml，简单解析
                metadata = self._simple_parse(match.group(1))

        # 提取正文内容
        body_match = re.search(r"^---\n.*?\n---\n?", content, re.DOTALL)
        if body_match:
            content = content[body_match.end():].strip()
        else:
            content = content.strip()

        return metadata, content

    def _simple_parse(self, text: str) -> dict:
        """简单解析 frontmatter"""
        result = {}
        for line in text.strip().split("\n"):
            if ":" in line:
                key, _, value = line.partition(":")
                result[key.strip()] = value.strip().strip("\"'")
        return result