# PageForge Phase1 — 节点实装计划

> **For Claude:** REQUIRED SUB-TOOL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 PageForge v2 的 remaining 4 个节点（reply/thinking/plan/code_gen-bugfix）从占位实现升级为真实 LLM 调用，完成整个 Phase1 闭环。

**Architecture:** 每个节点通过 `model_router.get_model_for_node(node_name, state)` 获取 LLM，使用 `llm.stream()` 流式输出并通过 SSE 事件推送到前端。公共流式逻辑抽取为 `_stream_llm` helper 消除重复代码。`event_emitter.py` 函数签名修正为节点实际需要的参数形式。

**Tech Stack:** Python 3.13 / LangGraph v2 / LangChain ChatOpenAI / SSE / FastAPI

**前提条件:**
- model_router.py 已完成，提供 `get_model_for_node(task_node, state)` / `get_global_strategy()`
- event_emitter.py 提供各事件推送函数（签名需修正，见 Task 1）
- state.py AgentState 已包含所有需要的 Optional 字段
- `.env` 已配置 MODEL_LITE/CHAT/PRO/REASON
- 本计划独立于 intent_router 和 style_picker（已完成）

---

## Task 1: 修正 event_emitter.py 函数签名

**Files:**
- Modify: `backend/app/graph/nodes/event_emitter.py:78-135`

> **背景:** 当前 event_emitter 函数的参数签名与节点实际使用方式不一致。大多数调用方已经自己构造了完整 dict 传入 `data`，但函数签名还在尝试二次包装 `_emit(event_type, data)` 时丢失字段的事经常发生。本次修改保持简单：保留现有签名不变（向后兼容），但把部分事件的参数字段补全到与节点调用匹配。

**Step 1: 修正 `emit_thinking_start`**

节点调用方式：`emit_thinking_start(id=thinking_id)` — 需要接受 `id` 参数。

```python
def emit_thinking_start(id: str):
    """发送思考开始事件"""
    _emit("thinking:start", {
        "id": id,
        "timestamp": __import__('time').time()
    })
```

**Step 2: 修正 `emit_thinking_delta`**

节点调用方式：`emit_thinking_delta(id=thinking_id, delta=thought_content)` — 需要接受 `delta` 参数而非 `content`。

```python
def emit_thinking_delta(id: str, delta: str):
    """发送思考内容增量事件"""
    _emit("thinking:delta", {
        "id": id,
        "delta": delta,
        "timestamp": __import__('time').time()
    })
```

**Step 3: 修正 `emit_thinking_end`**

节点调用方式：`emit_thinking_end(id=thinking_id, content=..., summary=...)` — 需要接受 `content` 和 `summary` 参数。

```python
def emit_thinking_end(id: str, content: str, summary: str):
    """发送思考结束事件"""
    _emit("thinking:end", {
        "id": id,
        "content": content,
        "summary": summary,
        "timestamp": __import__('time').time()
    })
```

**Step 4: 修正 `emit_plan_start`**

节点调用方式：`emit_plan_start(steps=plan_steps, current=0, id=plan_id)` — 需要接受完整步骤列表和当前进度。

```python
def emit_plan_start(id: str, steps: list, current: int = 0):
    """发送计划开始事件"""
    _emit("plan:start", {
        "id": id,
        "steps": steps,
        "current": current,
        "timestamp": __import__('time').time()
    })
```

**Step 5: 修正 `emit_plan_update`**

节点调用方式：`emit_plan_update(steps=plan_steps, is_complete=True)` — 传入完整步骤和完成标志。

```python
def emit_plan_update(steps: list, is_complete: bool = False):
    """发送计划更新事件"""
    _emit("plan:update", {
        "steps": steps,
        "is_complete": is_complete,
        "timestamp": __import__('time').time()
    })
```

**Step 6: 修正 `emit_plan_done`**

```python
def emit_plan_done(steps: list):
    """发送计划完成事件"""
    _emit("plan:done", {
        "steps": steps,
        "timestamp": __import__('time').time()
    })
```

**Step 7: 修正 `emit_text_delta`**

节点调用方式：`emit_text_delta(id=text_id, content=response)` — 需要接受 `id` 参数。

```python
def emit_text_delta(id: str, content: str):
    """发送文本增量事件"""
    _emit("text:delta", {
        "id": id,
        "content": content,
        "timestamp": __import__('time').time()
    })
```

**Step 8: 修正 `emit_text_done`**

```python
def emit_text_done(id: str, content: str):
    """发送文本完成事件"""
    _emit("text:done", {
        "id": id,
        "content": content,
        "timestamp": __import__('time').time()
    })
```

**Step 9: 确认无 lint 错误**

```bash
cd /Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend
python -m py_compile app/graph/nodes/event_emitter.py && echo "OK"
```

**Step 10: Commit**

```bash
git add backend/app/graph/nodes/event_emitter.py
git commit m "fix: 修正 event_emitter 函数签名匹配节点调用方式"
```

---

## Task 2: 抽取 _stream_llm 公共 helper

**Files:**
- Create: `backend/app/graph/nodes/llm_utils.py`
- Test: `tests/test_llm_utils.py`

> **背景:** reply/thinking/plan 三个节点都需要"获取 LLM → 流式调用 → 推送 SSE 事件"的流程，只有推送的 event 类型不同。抽取公共 helper 消除重复代码。

**Step 1: 创建 llm_utils.py**

```python
"""
PageForge LLM 流式调用公共工具

为 thinking/plan/reply 等节点提供统一的流式 LLM 调用模板。
"""

import logging
from typing import Callable
from langchain_core.messages import BaseMessage
from app.core.model_router import get_model_for_node

logger = logging.getLogger(__name__)


def stream_llm(
    node_name: str,
    state: dict,
    messages: list[BaseMessage],
    emit_start: Callable,
    emit_delta: Callable[[str], None],
    emit_end: Callable[[str], None],
) -> str:
    """
    统一流式 LLM 调用模板。

    各节点使用示例:
        full_text = stream_llm(
            node_name="reply",
            state=state,
            messages=[SystemMessage(prompt), HumanMessage(msg)],
            emit_start=lambda: emit_text_start(id=text_id),
            emit_delta=lambda chunk: emit_text_delta(id=text_id, content=chunk),
            emit_end=lambda full: emit_text_done(id=text_id, content=full),
        )

    Args:
        node_name: 节点名称（用于路由选择模型）
        state: 当前 AgentState
        messages: 发送给 LLM 的消息列表
        emit_start: 推送开始事件（无参回调）
        emit_delta: 推送增量事件（接收 chunk 文本）
        emit_end: 推送结束事件（接收完整文本）

    Returns:
        完整响应文本
    """
    llm = get_model_for_node(node_name, state)
    logger.debug(f"[stream_llm] node={node_name}, model={getattr(llm, 'model_name', '?')}")

    emit_start()

    chunks: list[str] = []
    try:
        for chunk in llm.stream(messages):
            text = getattr(chunk, "content", str(chunk))
            if text:
                chunks.append(text)
                emit_delta(text)
    except Exception as e:
        logger.error(f"[stream_llm] LLM 调用失败 node={node_name}: {e}", exc_info=True)
        # 降级：返回已收集内容
        if not chunks:
            chunks.append(f"[生成失败: {e}]")

    full_text = "".join(chunks)
    emit_end(full_text)
    return full_text
```

**Step 2: 编写测试（不依赖真实 LLM，mock 即可）**

```python
# tests/test_llm_utils.py
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage

from app.graph.nodes.llm_utils import stream_llm


def _make_mock_llm(chunks):
    """创建一个模拟流式 LLM，每次 yield 一个 chunk"""
    mock_llm = MagicMock()
    mock_llm.model_name = "test-model"

    def _stream(messages):
        for c in chunks:
            m = MagicMock()
            m.content = c
            yield m

    mock_llm.stream = _stream
    return mock_llm


class TestStreamLlm:
    def test_basic_streaming(self):
        """正常流式调用：所有 emit 回调都被触发"""
        with patch("app.graph.nodes.llm_utils.get_model_for_node", return_value=_make_mock_llm(["Hello", " World"])):
            events = {"start": 0, "deltas": [], "end": None}
            result = stream_llm(
                node_name="reply",
                state={"model_strategy": {"reply": "chat"}},
                messages=[HumanMessage("hi")],
                emit_start=lambda: events.__setitem__("start", events["start"] + 1),
                emit_delta=lambda c: events["deltas"].append(c),
                emit_end=lambda f: events.__setitem__("end", f),
            )
        assert result == "Hello World"
        assert events["start"] == 1
        assert events["deltas"] == ["Hello", " World"]
        assert events["end"] == "Hello World"

    def test_empty_response(self):
        """LLM 返回空：emit_start 和 emit_end 仍触发，emit_delta 不触发"""
        with patch("app.graph.nodes.llm_utils.get_model_for_node", return_value=_make_mock_llm([])):
            events = {"start": 0, "deltas": [], "end": None}
            result = stream_llm(
                node_name="reply",
                state={},
                messages=[HumanMessage("hi")],
                emit_start=lambda: events.__setitem__("start", events["start"] + 1),
                emit_delta=lambda c: events["deltas"].append(c),
                emit_end=lambda f: events.__setitem__("end", f),
            )
        assert result == ""
        assert events["start"] == 1
        assert events["deltas"] == []
        assert events["end"] == ""

    def test_exception_fallback(self):
        """LLM 抛异常：不崩溃，返回错误占位文本"""
        mock_llm = MagicMock()
        mock_llm.model_name = "test-model"
        mock_llm.stream.side_effect = RuntimeError("API Error")

        with patch("app.graph.nodes.llm_utils.get_model_for_node", return_value=mock_llm):
            events = {"start": 0, "deltas": [], "end": None}
            result = stream_llm(
                node_name="reply",
                state={},
                messages=[HumanMessage("hi")],
                emit_start=lambda: events.__setitem__("start", events["start"] + 1),
                emit_delta=lambda c: events["deltas"].append(c),
                emit_end=lambda f: events.__setitem__("end", f),
            )
        assert "[生成失败" in result
        assert events["start"] == 1
        assert events["end"] == result
```

**Step 3: 运行测试**

```bash
cd /Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend
python -m pytest ../tests/test_llm_utils.py -v
```

预期：3 tests PASS

**Step 4: Commit**

```bash
git add backend/app/graph/nodes/llm_utils.py tests/test_llm_utils.py
git commit m "feat: 抽取 stream_llm 公共 helper"
```

---

## Task 3: P1 — reply 节点实装

**Files:**
- Modify: `backend/app/graph/nodes/reply.py`

> **Background:** 当前 reply 是 if-else 硬编码，返回"你好！我是 PageForge"等内容。需要接入真实 LLM + SSE 流式推送 + model_strategy。

**Step 1: 修改——完整替换 reply 实现**

```python
"""
Reply Node — 文本回复节点

处理 chat/unknown 意图的直接回复，以及 code_gen 完成后的总结回复。
通过 SSE 推送 text_delta / text_done 事件。
"""

import logging
import time
from langchain_core.messages import SystemMessage, HumanMessage
from .event_emitter import (
    emit_text_delta,
    emit_text_done,
)
from .llm_utils import stream_llm

logger = logging.getLogger(__name__)


REPLY_SYSTEM_PROMPT = """\
你是一个友好的 AI 助手 PageForge，专注于帮助用户生成和管理前端项目。

## 回复要求
- 简洁明了，不要太长（100 字以内）
- 技术类问题要准确
- 如果是代码生成完成，简要说明生成了什么文件
- 合理使用 markdown 格式（加粗、列表）
- 中文回复
"""


def _build_reply_context(state: dict) -> str:
    """根据 intent 和 state 构建上下文信息注入 prompt"""
    intent = state.get("intent", "unknown")
    parts = [f"[意图: {intent}]"]

    if intent == "code_gen":
        files = state.get("files", [])
        if files:
            file_list = "\n".join(f"- {f.get('path', '?')} ({f.get('language', '?')})" for f in files)
            parts.append(f"已生成 {len(files)} 个文件：\n{file_list}")
        install_status = state.get("install_status", "")
        if install_status:
            parts.append(f"依赖安装状态: {install_status}")
    elif intent == "code_edit":
        parts.append("已完成代码修改")
    elif intent == "explain":
        summary = state.get("thought_summary", "")
        if summary:
            parts.append(f"思考摘要: {summary}")

    parts.append(f"\n用户原始消息: {state.get('user_message', '')}")
    return "\n".join(parts)


def reply_node(state: dict) -> dict:
    """
    回复节点函数

    输入: state["user_message"], state.get("intent"), state.get("files")
    输出: state + response_message + is_complete
    """
    user_message = state.get("user_message", "")
    intent = state.get("intent", "unknown")

    logger.info(f"[Reply] 开始生成回复（intent={intent}）")

    text_id = f"text_{int(time.time() * 1000)}"

    # 构建 prompt
    context = _build_reply_context(state)
    messages = [
        SystemMessage(content=REPLY_SYSTEM_PROMPT),
        HumanMessage(content=context),
    ]

    # 通过 stream_llm 流式调用
    response = stream_llm(
        node_name="reply",
        state=state,
        messages=messages,
        emit_start=lambda: None,  # text 不推 start，只有 delta/done
        emit_delta=lambda chunk: emit_text_delta(id=text_id, content=chunk),
        emit_end=lambda full: emit_text_done(id=text_id, content=full),
    )

    if not response:
        response = "已完成处理，但没有生成具体内容。"

    logger.info(f"[Reply] 完成，长度={len(response)}")

    return {
        **state,
        "response_message": response,
        "is_complete": True,
    }
```

**Step 2: 验证语法**

```bash
python -m py_compile app/graph/nodes/reply.py && echo "OK"
```

**Step 3: Commit**

```bash
git add backend/app/graph/nodes/reply.py
git commit m "feat: reply 节点接入真实 LLM + SSE 流式推送"
```

---

## Task 4: P2 — thinking 节点实装

**Files:**
- Modify: `backend/app/graph/nodes/thinking.py`

> **Background:** 当前 thinking 是硬编码 4 行文本。需要流式调用 LLM 展现 AI 思考过程，给前端推送 thinking_start/delta/end 事件。

**Step 1: 修改——完整替换 thinking 实现**

```python
"""
Thinking Node — 思维链节点

LLM 思考过程，通过 SSE 推送 thinking_start / thinking_delta / thinking_end 事件。
"""

import logging
import time
from langchain_core.messages import SystemMessage, HumanMessage
from .event_emitter import (
    emit_thinking_start,
    emit_thinking_delta,
    emit_thinking_end,
)
from .llm_utils import stream_llm

logger = logging.getLogger(__name__)


THINKING_SYSTEM_PROMPT = """\
你是一个资深软件架构师，正在分析用户需求并思考实现方案。

请按以下结构进行思考：
1. 需求理解：用户想要什么？核心功能点是什么？
2. 技术选型：需要哪些技术栈？为什么？
3. 架构设计：如何组织项目结构？有哪些关键组件？
4. 实现步骤：分几步完成？每一步的产出是什么？

保持思考专注，每个部分 2-3 句话即可。用中文思考。
"""


def thinking_node(state: dict) -> dict:
    """
    思维链节点函数

    输入: state["user_message"], state.get("intent"), state.get("tags")
    输出: state + thought_summary（思考内容通过 SSE 事件推送）
    """
    user_message = state.get("user_message", "")
    intent = state.get("intent", "unknown")
    tags = state.get("tags", [])

    logger.info(f"[Thinking] 开始思考（intent={intent}）")

    thinking_id = f"thinking_{int(time.time() * 1000)}"

    # 构建思考上下文
    context_parts = [f"用户想要: {user_message}"]
    if intent and intent != "unknown":
        context_parts.append(f"意图类型: {intent}")
    if tags:
        context_parts.append(f"技术标签: {', '.join(tags)}")
    context = "\n".join(context_parts)

    full_content = stream_llm(
        node_name="thinking",
        state=state,
        messages=[
            SystemMessage(content=THINKING_SYSTEM_PROMPT),
            HumanMessage(content=context),
        ],
        emit_start=lambda: emit_thinking_start(id=thinking_id),
        emit_delta=lambda chunk: emit_thinking_delta(id=thinking_id, delta=chunk),
        emit_end=lambda full: emit_thinking_end(
            id=thinking_id,
            content=full,
            summary=f"为 {intent} 需求分析了实现方案",
        ),
    )

    thought_summary = full_content[:200] if full_content else "已完成分析"

    logger.info(f"[Thinking] 思考完成，摘要: {thought_summary[:50]}...")

    return {
        **state,
        "thought_summary": thought_summary,
    }
```

**Step 2: 验证语法**

```bash
python -m py_compile app/graph/nodes/thinking.py && echo "OK"
```

**Step 3: Commit**

```bash
git add backend/app/graph/nodes/thinking.py
git commit m "feat: thinking 节点接入真实 LLM 流式思考"
```

---

## Task 5: P3 — plan 节点实装

**Files:**
- Modify: `backend/app/graph/nodes/plan.py`

> **Background:** 当前 plan 是硬编码 4 步（初始化→组件→样式→启动）。需要 LLM 根据意图+思考摘要生成真实执行计划，JSON 解析后逐 step 推送 plan_update 事件。

**Step 1: 修改——完整替换 plan 实现**

```python
"""
Plan Node — 计划制定节点

根据意图和思考结果，制定具体的执行计划。
通过 SSE 推送 plan_start / plan_update / plan_done 事件。
"""

import json
import logging
import time
from langchain_core.messages import SystemMessage, HumanMessage
from .event_emitter import (
    emit_plan_start,
    emit_plan_update,
    emit_plan_done,
)
from .llm_utils import stream_llm

logger = logging.getLogger(__name__)


PLAN_SYSTEM_PROMPT = """\
你是一个项目规划师，负责将用户需求拆解为可执行的步骤列表。

## 输出格式（严格 JSON，不要包含其他文字）
{
  "steps": [
    {"id": 1, "label": "步骤描述", "type": "init|component|style|test|deploy"},
    ...
  ]
}

## 要求
- 步骤数量 3~8 个
- 每个步骤描述清晰、可验证
- 按照依赖顺序排列（先做的基础步骤在前）
- type 字段表示步骤类型：init(初始化)、component(组件)、style(样式)、test(测试)、deploy(部署)
- 保持步骤粒度适中（不要太细也不要太粗）
"""


def _parse_plan_steps(raw_text: str, intent: str) -> list[dict]:
    """
    从 LLM 返回的文本中解析 plan steps。
    解析失败时返回基于 intent 的内置降级方案。
    """
    # 尝试提取 JSON
    text = raw_text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    try:
        data = json.loads(text)
        steps = data.get("steps", [])
        if isinstance(steps, list) and len(steps) >= 2:
            logger.debug(f"[Plan] LLM 解析成功，{len(steps)} 个步骤")
            return steps
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        logger.warning(f"[Plan] LLM 输出 JSON 解析失败: {e}，使用降级方案")

    # 降级方案
    return _fallback_steps(intent)


def _fallback_steps(intent: str) -> list[dict]:
    """内置降级计划"""
    fallbacks = {
        "code_gen": [
            {"id": 1, "label": "初始化项目结构", "type": "init"},
            {"id": 2, "label": "生成核心组件", "type": "component"},
            {"id": 3, "label": "添加样式和交互", "type": "style"},
            {"id": 4, "label": "安装依赖并校验", "type": "deploy"},
        ],
        "code_edit": [
            {"id": 1, "label": "分析现有代码结构", "type": "init"},
            {"id": 2, "label": "执行代码修改", "type": "component"},
            {"id": 3, "label": "验证修改结果", "type": "test"},
        ],
    }
    return fallbacks.get(intent, [
        {"id": 1, "label": "分析需求", "type": "init"},
        {"id": 2, "label": "制定方案", "type": "component"},
        {"id": 3, "label": "执行完成", "type": "deploy"},
    ])


def plan_node(state: dict) -> dict:
    """
    计划节点函数

    输入: state["user_message"], state.get("thought_summary"), state.get("tags")
    输出: state + plan_steps (供后续节点使用)
    """
    user_message = state.get("user_message", "")
    intent = state.get("intent", "unknown")
    thought_summary = state.get("thought_summary", "")
    tags = state.get("tags", [])

    logger.info(f"[Plan] 开始制定计划（intent={intent}）")

    # ── 仅对 code_gen 和 code_edit 走 LLM 计划，其他意图直接用降级 ──
    if intent in ("code_gen", "code_edit"):
        plan_id = f"plan_{int(time.time() * 1000)}"

        context = (
            f"用户需求: {user_message}\n"
            f"意图: {intent}\n"
            f"思考结论: {thought_summary}\n"
            f"技术标签: {', '.join(tags)}"
        )

        full_text = stream_llm(
            node_name="plan",
            state=state,
            messages=[
                SystemMessage(content=PLAN_SYSTEM_PROMPT),
                HumanMessage(content=context),
            ],
            emit_start=lambda: emit_plan_start(id=plan_id, steps=[], current=0),
            emit_delta=lambda chunk: emit_plan_update(
                steps=_parse_plan_steps(chunk, intent),
                is_complete=False,
            ),
            emit_end=lambda full: emit_plan_done(
                steps=_parse_plan_steps(full, intent),
            ),
        )

        plan_steps = _parse_plan_steps(full_text, intent)
    else:
        # 非代码生成意图：直接降级
        plan_steps = _fallback_steps(intent)

    logger.info(f"[Plan] 计划制定完成，共 {len(plan_steps)} 个步骤")

    return {
        **state,
        "plan_steps": plan_steps,
    }
```

**Step 2: 验证语法**

```bash
python -m py_compile app/graph/nodes/plan.py && echo "OK"
```

**Step 3: Commit**

```bash
git add backend/app/graph/nodes/plan.py
git commit m "feat: plan 节点接入真实 LLM 计划生成 + JSON 解析"
```

---

## Task 6: P0 — code_gen 修复

**Files:**
- Modify: `backend/app/graph/nodes/code_gen.py`

> **Background:** code_gen 整体骨架已有，但存在三个 bug：① `install_result` 在 except 分支可能未定义 ② try 块外有不可达 `return` 死代码 ③ emit_file_created 事件未调用，推送给前端的事件不完整。

**Step 1: 修复 install_result 未定义风险 + 死代码**

在 `try` 块开头初始化 `install_result`，并删除函数尾部的死 `return`：

```diff
  generated_files = []
+ install_result = {"success": False, "output": "skipped"}

  try:
      # ... 现有代码不变 ...
```

删除文件末尾第 349-354 行的死代码：

```python
-    return {
-        **state,
-        "files": files,
-        "project_id": session_id,
-        "status": "generation_done",
-    }
```

**Step 2: 补充 emit_file_created 事件**

在每个文件成功写入后推送事件：

```diff
  if result["success"]:
      generated_files.append({"path": "package.json", "type": "file", "language": "json"})
+     emit_file_created(file_path="package.json", name="package.json", language="json")
```

对每个文件（vite.config.ts / tsconfig.json / App.tsx / main.tsx / index.css）都做同样处理。

**Step 3: 补充 index.html（Vite 入口，WebContainer 起不来）**

在生成 `package.json` 之后、`vite.config.ts` 之前添加：

```python
  # 生成 index.html（Vite SPA 入口）
  index_html = _generate_index_html()
  result = write_file_tool.invoke({"path": "index.html", "content": index_html, "session_id": session_id})
  if result["success"]:
      generated_files.append({"path": "index.html", "type": "file", "language": "html"})
      emit_file_created(file_path="index.html", name="index.html", language="html")
```

添加 `_generate_index_html()` 函数：

```python
def _generate_index_html() -> str:
    """生成 Vite SPA 入口 HTML"""
    return '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>PageForge App</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>'''
```

**Step 4: 补充 tool_call SSE 事件**

在 `_generate_app_component` 调用前后包 tool_call 事件：

```diff
+ emit_tool_call_start(tool_id="code_gen_llm", name="generate_component", input={"file": "src/App.tsx"})
  app_component_content = _generate_app_component(user_message, plan_steps, ui_style_config, state)
+ emit_tool_call_end(tool_id="code_gen_llm", status="success")
```

**Step 5: 验证语法**

```bash
python -m py_compile app/graph/nodes/code_gen.py && echo "OK"
```

**Step 6: Commit**

```bash
git add backend/app/graph/nodes/code_gen.py
git commit m "fix: code_gen 修复 install_result 未定义/死代码/补充 SSE 事件"
```

---

## 验收标准

完成所有 Task 后，执行以下验证：

```bash
# 1. 语法检查（所有节点文件无编译错误）
cd backend/app/graph/nodes
for f in event_emitter.py llm_utils.py reply.py thinking.py plan.py code_gen.py; do
    python -m py_compile "$f" && echo "✅ $f" || echo "❌ $f"
done

# 2. 测试通过
python -m pytest ../tests/test_llm_utils.py -v

# 3. 图编译无报错
python -c "from app.graph.graph_v2 import pageforge_graph_v2; print('✅ graph_v2 compiled OK')"
```

预期所有节点都能正确编译，`pageforge_graph_v2` 正常实例化。

---

## 实施顺序总结

| Task | 内容 | 预计时间 | 依赖 |
|------|------|---------|------|
| 1 | event_emitter 签名修正 | 15 min | 无 |
| 2 | 抽取 stream_llm helper + 测试 | 20 min | Task 1（llm_utils import 需要 event_emitter 先就绪） |
| 3 | P1 — reply 节点实装 | 15 min | Task 2（依赖 stream_llm） |
| 4 | P2 — thinking 节点实装 | 15 min | Task 2 |
| 5 | P3 — plan 节点实装 | 20 min | Task 2 |
| 6 | P0 — code_gen 修复 | 20 min | 无（独立修复，不依赖 stream_llm） |

> **执行建议：** Task 6（code_gen bug 修复）优先级最高且无依赖，可以跟 Task 1 并行，甚至先做。Task 2 是 Task 3/4/5 的前置依赖，完成后 3/4/5 可以任意顺序甚至并行推进。

---

## 注意事项

- **所有 commit 都需要手动确认 diff** 后再执行 commit 命令
- `code_gen.py` 修改时保留原有的 `_generate_*` 系列辅助函数，只做增量修改
- `plan.py` 的 `_parse_plan_steps` 在流式 delta 阶段会有不完整的 JSON，**不需要在 delta 阶段解析**，仅在 `emit_end` 时解析最终完整文本即可。上面的 plan 代码在 delta 阶段会反复尝试解析会失败降级，这是预期行为——前端在 delta 阶段不需要显示部分计划
- `intent_router.py` 和 `style_picker.py` 不在本计划范围内，不动这两个文件