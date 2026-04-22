# backend/app/core/registry.py
from typing import Dict, List, Any, Callable
from dataclasses import dataclass
import inspect

@dataclass
class ToolInfo:
    """工具信息"""
    name: str
    function: Callable
    description: str
    parameters: Dict[str, Any]

@dataclass
class SkillInfo:
    """技能信息"""
    name: str
    content: str
    metadata: Dict[str, Any]
    path: str

class ToolRegistry:
    """统一工具注册中心"""

    def __init__(self):
        self._tools: Dict[str, ToolInfo] = {}
        self._skills: Dict[str, SkillInfo] = {}

    def register_tool(self, tool_fn: Callable) -> Callable:
        """注册工具（装饰器方式）"""
        tool_info = ToolInfo(
            name=tool_fn.name,
            function=tool_fn,
            description=tool_fn.description,
            parameters=self._extract_parameters(tool_fn)
        )
        self._tools[tool_info.name] = tool_info
        return tool_fn

    def register_skill(self, name: str, content: str,
                      metadata: Dict[str, Any] = None,
                      path: str = "") -> None:
        """注册技能"""
        skill_info = SkillInfo(
            name=name,
            content=content,
            metadata=metadata or {},
            path=path
        )
        self._skills[name] = skill_info

    def get_langchain_tools(self) -> List:
        """获取 LangChain 工具列表"""
        return [info.function for info in self._tools.values()]

    def get_skill_guide(self) -> str:
        """获取合并的技能指南"""
        if not self._skills:
            return ""

        guide_parts = []
        for skill in self._skills.values():
            guide_parts.append(f"\n{'='*60}")
            guide_parts.append(f"技能: {skill.name}")
            guide_parts.append(f"{'='*60}")
            guide_parts.append(skill.content)

        return "\n".join(guide_parts)

    def get_tool_info(self, name: str) -> ToolInfo:
        """获取工具信息"""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """列出所有工具名称"""
        return list(self._tools.keys())

    def list_skills(self) -> List[str]:
        """列出所有技能名称"""
        return list(self._skills.keys())

    def _extract_parameters(self, tool_fn: Callable) -> Dict[str, Any]:
        """提取工具参数信息"""
        # 简化实现，实际可以从工具 schema 中提取
        return {}