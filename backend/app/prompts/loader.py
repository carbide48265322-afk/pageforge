"""
Prompt 文件加载器
==================

从 prompts/*.md 文件加载 prompt 文本，带 LRU 缓存。
文件内容变更后调用 reload_prompts() 清除缓存即可生效（无需重启服务）。

Usage:
    # 加载单个 prompt（不带全局身份）
    from app.prompts import load_prompt
    system_prompt = load_prompt("01_intent_router")

    # 加载 prompt 并自动拼接全局身份（推荐用于节点 system prompt）
    from app.prompts import load_prompt_with_identity
    system_prompt = load_prompt_with_identity("01_intent_router")

    # 使用 PromptRegistry 进行多版本管理（A/B 测试）
    from app.prompts import prompt_registry
    prompt = prompt_registry.get("thinking", version="v2")
"""

import os
import glob
from functools import lru_cache

PROMPTS_DIR = os.path.dirname(os.path.abspath(__file__))

# 全局身份 prompt 的文件名（不含后缀）
_IDENTITY_PROMPT_NAME = "00_identity"


@lru_cache(maxsize=32)
def load_prompt(name: str) -> str:
    """
    按文件名加载 prompt 文本（带缓存）。

    Args:
        name: prompt 文件名（不含 .md 后缀），如 "01_intent_router"

    Returns:
        prompt 文本内容

    Raises:
        FileNotFoundError: 文件不存在时抛出
    """
    # 支持带或不带 .md 后缀
    if not name.endswith(".md"):
        name = f"{name}.md"

    path = os.path.join(PROMPTS_DIR, name)

    if not os.path.exists(path):
        available = list_prompts()
        raise FileNotFoundError(
            f"Prompt 文件不存在: {path}\n"
            f"可用 prompts: {available}"
        )

    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def load_prompt_with_identity(name: str) -> str:
    """
    加载 prompt 并自动拼接全局身份（00_identity.md）。

    返回格式：
        <identity prompt 内容>

        ---
        <node-specific prompt 内容>

    适用于所有节点的 system prompt 加载，确保全局身份约束被注入。

    Args:
        name: 节点 prompt 文件名（不含 .md 后缀），如 "01_intent_router"

    Returns:
        拼接后的完整 prompt 文本
    """
    identity = load_prompt(_IDENTITY_PROMPT_NAME)
    node_prompt = load_prompt(name)
    return f"{identity}\n\n---\n\n{node_prompt}"


def reload_prompts():
    """清除缓存，强制重新加载所有 prompt（用于热更新）"""
    load_prompt.cache_clear()
    _get_identity.cache_clear()


def list_prompts() -> list[str]:
    """列出所有可用的 prompt 文件名（不含 .md 后缀）"""
    pattern = os.path.join(PROMPTS_DIR, "*.md")
    return sorted([
        os.path.basename(f).replace(".md", "")
        for f in glob.glob(pattern)
    ])


# ─── PromptRegistry：多版本 Prompt 管理（A/B 测试基础）────────────

@lru_cache(maxsize=1)
def _get_identity() -> str:
    """缓存加载全局身份 prompt"""
    return load_prompt(_IDENTITY_PROMPT_NAME)


class PromptRegistry:
    """
    Prompt 注册表，支持多版本管理和 A/B 测试。

    使用方式：
        registry = PromptRegistry()
        # 加载默认版本
        prompt = registry.get("thinking")
        # 加载指定版本
        prompt = registry.get("thinking", version="v2")
        # 列出某节点的所有可用版本
        versions = registry.list_versions("thinking")

    版本文件命名规范：
        02_thinking.md      → 默认版本
        02_thinking_v2.md   → v2 版本
        02_thinking_v3.md   → v3 版本
    """

    def __init__(self, prompts_dir: str = None):
        self._dir = prompts_dir or PROMPTS_DIR

    def get(self, name: str, version: str = None, with_identity: bool = True) -> str:
        """
        加载指定 prompt，可选版本和是否拼接全局身份。

        Args:
            name: prompt 基础名，如 "02_thinking"
            version: 版本号，如 "v2"。None 表示默认版本
            with_identity: 是否拼接全局身份 prompt

        Returns:
            prompt 文本内容
        """
        if version:
            versioned_name = f"{name}_{version}"
            path = os.path.join(self._dir, f"{versioned_name}.md")
            if not os.path.exists(path):
                # 版本不存在，回退到默认版本
                import logging
                logging.getLogger(__name__).warning(
                    f"Prompt 版本不存在: {versioned_name}.md，回退到默认版本"
                )
                versioned_name = name
        else:
            versioned_name = name

        if with_identity:
            return load_prompt_with_identity(versioned_name)
        else:
            return load_prompt(versioned_name)

    def list_versions(self, name: str) -> list[str]:
        """列出某节点的所有可用版本"""
        all_prompts = list_prompts()
        versions = []
        for p in all_prompts:
            if p == name:
                versions.append("default")
            elif p.startswith(f"{name}_v"):
                # 提取版本号
                version = p[len(name) + 1:]  # 去掉 "name_" 前缀
                versions.append(version)
        return sorted(versions)


# 全局单例
prompt_registry = PromptRegistry()
