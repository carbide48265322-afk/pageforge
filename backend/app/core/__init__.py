from .registry import ToolRegistry
from .discovery import AutoDiscover

# 全局注册中心实例
registry = ToolRegistry()

# 自动发现器
discoverer = AutoDiscover(registry)

def init_registry():
    """初始化注册中心"""
    from app.config import TOOLS_DIR, SKILLS_DIR
    from pathlib import Path

    discoverer.discover_tools(Path(TOOLS_DIR))
    discoverer.discover_skills(Path(SKILLS_DIR))

    print(f"[Registry] 已注册工具: {registry.list_tools()}")
    print(f"[Registry] 已注册技能: {registry.list_skills()}")