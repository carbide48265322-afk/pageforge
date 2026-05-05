"""
PageForge Smart Model Router — 集中式智能模型路由

根据意图识别结果（intent + complexity），为每个执行节点分配最优模型。

模型分级：
  lite    — 意图分类、简单闲聊（快速、省钱）
  chat    — 一般对话、计划制定、风格选择（均衡）
  pro     — 代码生成、复杂推理（高质量）
  reason  — 深度思考、复杂调试（最强推理）

路由规则：
  - chat 意图 → 全部用 lite
  - code_gen + simple → thinking/plan 用 chat，code_gen 用 pro
  - code_gen + medium → thinking/plan 用 chat，code_gen 用 pro
  - code_gen + complex → 全部用 pro（thinking 可选 reason）
  - code_edit → thinking 用 pro，其余用 chat
  - explain/debug → thinking 用 reason，reply 用 pro
  - file_operation → 全部用 chat
  - unknown → 全部用 chat（安全降级）
"""

from __future__ import annotations

import os
import logging
from typing import Optional
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

# ─── 加载 .env ───────────────────────────────────────────
# __file__ = backend/app/core/model_router.py
# .env 位于项目根目录 pageforge/.env
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(BASE_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", None)

# ─── 模型名称配置（全部从 .env 读取，带默认值） ────────────
MODEL_LITE = os.getenv("MODEL_LITE", os.getenv("INTENT_MODEL_NAME", "gpt-4o-mini"))
MODEL_CHAT = os.getenv("MODEL_CHAT", os.getenv("MODEL_NAME", "gpt-4o"))
MODEL_PRO = os.getenv("MODEL_PRO", os.getenv("MODEL_NAME", "gpt-4o"))
MODEL_REASON = os.getenv("MODEL_REASON", os.getenv("MODEL_NAME", "o3"))

# ─── 各模型默认参数 ───────────────────────────────────────
_MODEL_PARAMS: dict[str, dict] = {
    "lite": {
        "temperature": 0.1,
        "max_tokens": 1024,
        "request_timeout": 15,
        "max_retries": 1,
    },
    "chat": {
        "temperature": 0.3,
        "max_tokens": 2048,
        "request_timeout": 15,
        "max_retries": 1,
    },
    "pro": {
        "temperature": 0.7,
        "max_tokens": 8192,
        "request_timeout": 120,
        "max_retries": 2,
    },
    "reason": {
        "temperature": 0.7,
        "max_tokens": 8192,
        "request_timeout": 60,
        "max_retries": 2,
    },
    "code_gen": {
        "temperature": 0.7,
        "max_tokens": 16384,
        "request_timeout": 180,
        "max_retries": 2,
    },
}


# ─── 路由策略表 ────────────────────────────────────────────
# key: (intent, complexity) → value: {node_name: model_tier}
# complexity 为 None 表示通配（匹配任意复杂度）

ROUTING_TABLE: dict[tuple[str, Optional[str]], dict[str, str]] = {
    # ── chat ──
    ("chat", None): {
        "thinking": "lite",
        "plan": "lite",
        "style_picker": "lite",
        "code_gen": "lite",
        "reply": "lite",
    },

    # ── code_gen ──
    ("code_gen", "simple"): {
        "thinking": "chat",
        "plan": "chat",
        "style_picker": "chat",
        "code_gen": "pro",
        "reply": "chat",
    },
    ("code_gen", "medium"): {
        "thinking": "chat",
        "plan": "chat",
        "style_picker": "chat",
        "code_gen": "pro",
        "reply": "chat",
    },
    ("code_gen", "complex"): {
        "thinking": "pro",
        "plan": "pro",
        "style_picker": "chat",
        "code_gen": "pro",
        "reply": "pro",
    },

    # ── code_edit ──
    ("code_edit", None): {
        "thinking": "pro",
        "plan": "chat",
        "style_picker": "chat",
        "code_gen": "pro",
        "reply": "chat",
    },

    # ── explain ──
    ("explain", None): {
        "thinking": "reason",
        "plan": "chat",
        "style_picker": "chat",
        "code_gen": "chat",
        "reply": "pro",
    },

    # ── debug ──
    ("debug", None): {
        "thinking": "reason",
        "plan": "pro",
        "style_picker": "chat",
        "code_gen": "pro",
        "reply": "pro",
    },

    # ── file_operation ──
    ("file_operation", None): {
        "thinking": "chat",
        "plan": "chat",
        "style_picker": "chat",
        "code_gen": "chat",
        "reply": "chat",
    },

    # ── unknown（安全降级） ──
    ("unknown", None): {
        "thinking": "chat",
        "plan": "chat",
        "style_picker": "chat",
        "code_gen": "chat",
        "reply": "chat",
    },
}


# ─── 公共 API ─────────────────────────────────────────────

def get_global_strategy(intent: str, complexity: Optional[str] = None) -> dict[str, str]:
    """
    根据意图 + 复杂度，返回全局模型策略。

    返回格式：
      {"thinking": "chat", "plan": "chat", "style_picker": "chat", "code_gen": "pro", "reply": "chat"}

    匹配逻辑：
      1. 精确匹配 (intent, complexity)
      2. 降级匹配 (intent, None) — 忽略复杂度
      3. 安全降级到 unknown
    """
    # 精确匹配
    key = (intent, complexity)
    if key in ROUTING_TABLE:
        strategy = ROUTING_TABLE[key]
        logger.info(f"[ModelRouter] 精确匹配: {key} → {strategy}")
        return dict(strategy)

    # 降级匹配（忽略复杂度）
    key_fallback = (intent, None)
    if key_fallback in ROUTING_TABLE:
        strategy = ROUTING_TABLE[key_fallback]
        logger.info(f"[ModelRouter] 降级匹配: {intent} (complexity={complexity}) → {strategy}")
        return dict(strategy)

    # 最终降级到 unknown
    logger.warning(f"[ModelRouter] 未找到路由: intent={intent}, complexity={complexity}，降级到 unknown")
    return dict(ROUTING_TABLE[("unknown", None)])


def get_model_for_node(node_name: str, state: dict) -> ChatOpenAI:
    """
    根据节点名称和当前 state，返回对应的 LLM 客户端。

    这是各节点统一调用的入口：
      llm = get_model_for_node("thinking", state)
    """
    strategy = state.get("model_strategy", {})
    tier = strategy.get(node_name, "chat")  # 默认 chat 级别
    return get_llm_by_tier(tier)


def get_llm_by_tier(tier: str) -> ChatOpenAI:
    """
    根据模型等级返回对应的 ChatOpenAI 实例。

    tier: "lite" | "chat" | "pro" | "reason"
    """
    tier = tier.lower().strip()

    tier_to_model = {
        "lite": MODEL_LITE,
        "chat": MODEL_CHAT,
        "pro": MODEL_PRO,
        "reason": MODEL_REASON,
        "code_gen": MODEL_PRO,  # 复用 pro 模型，但使用 code_gen 专属参数（max_tokens=16384, timeout=180s）
    }

    model_name = tier_to_model.get(tier, MODEL_CHAT)
    params = _MODEL_PARAMS.get(tier, _MODEL_PARAMS["chat"])

    logger.debug(f"[ModelRouter] 创建 LLM: tier={tier}, model={model_name}")

    return ChatOpenAI(
        model=model_name,
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
        **params,
    )


# ─── 便捷函数（兼容旧代码） ────────────────────────────────

@lru_cache(maxsize=1)
def get_intent_llm() -> ChatOpenAI:
    """意图识别专用 LLM（轻量快速）"""
    return get_llm_by_tier("lite")


@lru_cache(maxsize=1)
def get_execute_llm() -> ChatOpenAI:
    """执行专用 LLM（默认 chat 级别，兼容旧 config.llm）"""
    return get_llm_by_tier("chat")
