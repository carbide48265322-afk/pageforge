# tests/unit/core/test_discovery.py
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from app.core.discovery import AutoDiscover
from app.core.registry import ToolRegistry

class TestAutoDiscover:
    def test_discover_skills(self, tmp_path):
        # 创建临时技能目录结构
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        skill_dir = skills_dir / "test-skill"
        skill_dir.mkdir()

        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: A test skill
---

Test skill content
""")

        registry = ToolRegistry()
        discoverer = AutoDiscover(registry)

        discoverer.discover_skills(skills_dir)

        assert "test-skill" in registry.list_skills()
        guide = registry.get_skill_guide()
        assert "Test skill content" in guide

    def test_discover_tools(self):
        registry = ToolRegistry()
        discoverer = AutoDiscover(registry)

        # 模拟工具模块
        mock_tool = Mock()
        mock_tool.name = "mock_tool"
        mock_tool.description = "Mock tool"

        with patch('app.core.discovery.Path') as mock_path:
            mock_path.return_value.glob.return_value = []
            discoverer.discover_tools(Path("/fake/tools"))

        # 测试空目录情况
        assert len(registry.list_tools()) == 0