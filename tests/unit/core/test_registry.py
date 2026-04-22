# tests/unit/core/test_registry.py
import pytest
from unittest.mock import Mock
from app.core.registry import ToolRegistry, ToolInfo, SkillInfo

class TestToolRegistry:
    def test_register_tool(self):
        registry = ToolRegistry()

        # 模拟 LangChain 工具
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.description = "A test tool"

        registry.register_tool(mock_tool)

        assert "test_tool" in registry.list_tools()
        tool_info = registry.get_tool_info("test_tool")
        assert tool_info.name == "test_tool"

    def test_register_skill(self):
        registry = ToolRegistry()

        registry.register_skill(
            name="test_skill",
            content="Test skill content",
            metadata={"description": "Test skill"}
        )

        assert "test_skill" in registry.list_skills()
        assert "Test skill content" in registry.get_skill_guide()

    def test_get_langchain_tools(self):
        registry = ToolRegistry()

        # 模拟工具
        mock_tool = Mock()
        mock_tool.name = "tool1"
        mock_tool.description = "Tool 1"

        registry.register_tool(mock_tool)
        tools = registry.get_langchain_tools()

        assert len(tools) == 1
        assert tools[0] == mock_tool