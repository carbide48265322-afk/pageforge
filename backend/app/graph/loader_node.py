"""Skill & Tool 加载节点

在主图最开始执行，一次性完成：
1. 扫描并加载所有 Skill（SKILL.md + references）
2. 注册并绑定所有 Tool 到 LLM
3. 组装系统提示词
4. 写入 state，后续所有子图直接使用
"""
import os
from pathlib import Path
from typing import Dict, List

from app.graph.state import AgentState
from app.config import llm, SKILLS_DIR
from app.skills.loader import SkillAutoLoader
from app.graph.tools import REACT_PROJECT_TOOLS, ALL_AVAILABLE_TOOLS


async def load_skills_and_tools(state: AgentState) -> dict:
    """Skill & Tool 加载节点 — 主图入口第一个节点

    做一次，全局复用。后续子图从 state 读取：
    - state.system_prompt: 合并后的 Skill 提示词
    - state.loaded_skills: 已加载的 Skill 名称列表
    - state.active_tools: 已绑定的 Tool 名称列表
    """
    user_message = state.get("user_message", "")

    # ====== 1. 加载 Skill 内容 ======
    loader = SkillAutoLoader(SKILLS_DIR)
    skills = loader.load_all()

    skill_names: List[str] = []
    skill_prompts: List[str] = []

    for skill in skills:
        skill_names.append(skill["name"])
        metadata = skill["metadata"]
        content = skill["content"]

        # 组装 Skill 提示词：名称 + 描述 + 内容
        description = metadata.get("description", "")
        prompt_part = f"# Skill: {skill['name']}\n\n"
        if description:
            prompt_part += f"{description}\n\n"
        prompt_part += content
        skill_prompts.append(prompt_part)

        # 检查是否有 references 目录（如 Impeccable）
        refs_dir = Path(skill["path"]) / "references"
        if refs_dir.exists():
            ref_files = sorted(refs_dir.glob("*.md"))
            ref_parts = []
            for ref_file in ref_files:
                try:
                    ref_content = ref_file.read_text(encoding="utf-8").strip()
                    if ref_content:
                        ref_parts.append(f"## Reference: {ref_file.stem}\n\n{ref_content}")
                except Exception:
                    pass
            if ref_parts:
                skill_prompts.append(
                    f"# {skill['name']} References\n\n" + "\n\n---\n\n".join(ref_parts)
                )

    # 合并所有 Skill 为一个 system_prompt
    system_prompt = "\n\n---\n\n".join(skill_prompts) if skill_prompts else ""

    # ====== 2. 绑定 Tool ======
    tool_names = [t.name for t in REACT_PROJECT_TOOLS]

    # ====== 3. 输出到 state ======
    return {
        "loaded_skills": skill_names,
        "system_prompt": system_prompt,
        "active_tools": tool_names,
        "project_type": None,  # 后续由 prepare_context 分析后设置
    }


# Tool 注册表 — 供子图按名称查找 Tool 实例
TOOL_REGISTRY: Dict[str, object] = {t.name: t for t in ALL_AVAILABLE_TOOLS}


def get_tool(name: str):
    """按名称获取 Tool 实例"""
    return TOOL_REGISTRY.get(name)


def get_bound_llm(state: AgentState):
    """获取绑定了 Tool 的 LLM 实例

    子图使用方式：
        from app.graph.loader_node import get_bound_llm
        llm_with_tools = get_bound_llm(state)
    """
    active_tool_names = state.get("active_tools", [])
    tools = []
    for name in active_tool_names:
        tool = TOOL_REGISTRY.get(name)
        if tool:
            tools.append(tool)

    if tools:
        return llm.bind_tools(tools)
    return llm
