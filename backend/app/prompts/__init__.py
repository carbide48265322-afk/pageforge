"""
PageForge Prompts 加载器
========================

从 backend/app/prompts/*.md 文件加载 prompt 文本。
支持缓存、热重载、全局身份注入和多版本管理。

Usage:
    # 加载单个 prompt（不带全局身份）
    from app.prompts import load_prompt
    system_prompt = load_prompt("01_intent_router")

    # 加载 prompt 并自动拼接全局身份（推荐用于节点 system prompt）
    from app.prompts import load_prompt_with_identity
    system_prompt = load_prompt_with_identity("01_intent_router")

    # 使用 PromptRegistry 进行多版本管理（A/B 测试）
    from app.prompts import prompt_registry
    prompt = prompt_registry.get("02_thinking", version="v2")
"""

from .loader import (
    load_prompt,
    load_prompt_with_identity,
    reload_prompts,
    list_prompts,
    PromptRegistry,
    prompt_registry,
)

__all__ = [
    "load_prompt",
    "load_prompt_with_identity",
    "reload_prompts",
    "list_prompts",
    "PromptRegistry",
    "prompt_registry",
]
