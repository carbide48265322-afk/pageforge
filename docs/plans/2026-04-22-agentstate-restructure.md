# AgentState 重构计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 AgentState 从旧的「单文件 HTML 生成器」字段重构为新架构要求的「6 阶段 AI 应用生成器」字段，同时保持向后兼容，确保现有子图不中断。

**Architecture:** 采用渐进式策略——先新增字段（不删旧字段），更新各子图引用，最后清理废弃字段。核心思路：将旧字段标记为 deprecated 但暂不删除，新字段按架构设计的 GlobalState 定义补充。

**Tech Stack:** Python 3.11+, typing.TypedDict, LangGraph StateGraph

---

## 背景：当前状态 vs 目标状态

### 当前 AgentState（24 个旧字段）

```python
class AgentState(TypedDict):
    # 输入
    user_message: str
    session_id: str
    base_html: str              # ❌ 旧架构：修改模式用
    created_at: str
    # 构想阶段
    phase: str
    stage: str
    project_config: Dict[str, Any]
    design_concept: str
    requirements_doc: str
    requirements_approved: bool
    selected_style: str
    available_styles: List[Dict[str, str]]
    # 演示阶段
    demo_html: str              # ❌ 旧架构
    demo_instructions: str      # ❌ 旧架构
    demo_link: str              # ❌ 旧架构
    is_demo_ready: bool         # ❌ 旧架构
    project_files: Dict[str, str]
    # 中间状态
    task_list: List[Dict[str, Any]]
    current_html: str           # ❌ 旧架构
    validation_errors: List[str]
    iteration_count: int
    fix_count: int              # ❌ 旧架构
    # 输出
    response_message: str
    output_html: str            # ❌ 旧架构
    output_version: int         # ❌ 旧架构
    is_complete: bool
```

### 目标 AgentState（架构设计要求）

架构文档定义了 `GlobalState`，需要以下新字段：
- `current_phase` (替代旧的 `phase`)
- `phase_status` (新增)
- `requirement_snapshot`, `design_snapshot`, `tech_snapshot`, `feature_snapshot`, `code_snapshot` (新增)
- `phase_history` (新增)

同时各子图已在使用但 AgentState 未声明的字段：
- `tech_spec`, `tech_approved` (TechSubgraph 写入)
- `project_mode`, `selected_features`, `available_features`, `feature_approved` (FeatureSubgraph 写入)
- `design_projects`, `selected_style_id`, `selected_design`, `design_style`, `api_spec`, `mock_data`, `frontend_code`, `style_code`, `extracted_homepage` (DesignSubgraph/CodeSubgraph 写入)
- `delivery_approved`, `revision_feedback` (DeliverySubgraph 写入)
- `human_input_pending`, `human_input_checkpoint_id`, `human_input_request` (nodes_human.py 写入)
- `status` (nodes_human.py 写入)
- 各子图私有状态键（如 `requirement_subgraph_state`, `tech_subgraph_state` 等）

---

## Task 1: 重构 state.py — 定义新字段 + Snapshot 类型

**Files:**
- Modify: `backend/app/graph/state.py`
- Test: `backend/tests/test_agent_state.py`

**Step 1: 写 Snapshot 类型定义的单元测试**

```python
# backend/tests/test_agent_state.py
import pytest
from app.graph.state import (
    AgentState, RequirementSnapshot, DesignSnapshot,
    TechSnapshot, FeatureSnapshot, CodeSnapshot, PhaseTransition
)

class TestSnapshots:
    def test_requirement_snapshot_fields(self):
        snapshot: RequirementSnapshot = {
            "confirmed": True,
            "user_input": "做一个博客",
            "clarification_qa": [],
            "prd": "# PRD",
            "confirmed_at": "2026-04-22T17:00:00"
        }
        assert snapshot["confirmed"] is True
        assert isinstance(snapshot["prd"], str)

    def test_design_snapshot_fields(self):
        snapshot: DesignSnapshot = {
            "confirmed": True,
            "style_options": [{"id": "modern"}],
            "selected_style": {"id": "modern", "name": "现代简约"},
            "design_spec": {"primary_color": "#333"},
            "confirmed_at": "2026-04-22T17:00:00"
        }
        assert len(snapshot["style_options"]) >= 1

    def test_phase_transition_fields(self):
        transition: PhaseTransition = {
            "from_phase": "requirement",
            "to_phase": "design",
            "trigger": "user_confirmed",
            "timestamp": "2026-04-22T17:00:00"
        }
        assert transition["from_phase"] == "requirement"


class TestAgentStateFields:
    def test_new_fields_exist(self):
        """新架构要求的核心字段都应可访问"""
        state: AgentState = {}  # TypedDict 允许空初始化用于类型检查
        # 以下字段在新 state.py 中必须存在
        from app.graph import state
        expected_fields = [
            "current_phase", "phase_status",
            "requirement_snapshot", "design_snapshot",
            "tech_snapshot", "feature_snapshot", "code_snapshot",
            "phase_history",
            "tech_spec", "tech_approved",
            "project_mode", "selected_features", "available_features", "feature_approved",
            "design_projects", "selected_style_id", "selected_design",
            "delivery_approved", "revision_feedback",
            "human_input_pending", "human_input_checkpoint_id",
        ]
        # 检查 TypedDict 注解中是否包含这些字段
        annotations = state.AgentState.__annotations__
        for field in expected_fields:
            assert field in annotations, f"Missing field: {field}"
```

**Step 2: 运行测试，确认失败**

Run: `cd /Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge && python -m pytest backend/tests/test_agent_state.py -v`
Expected: FAIL — Snapshot 类型不存在，新字段缺失

**Step 3: 实现新的 state.py**

重写 `backend/app/graph/state.py`：

```python
from typing import TypedDict, List, Optional, Dict, Any


# ========== 阶段快照类型 ==========

class RequirementSnapshot(TypedDict):
    """需求阶段确认后的快照"""
    confirmed: bool
    user_input: str
    clarification_qa: List[Dict]  # 澄清问答记录
    prd: str
    confirmed_at: str


class DesignSnapshot(TypedDict):
    """设计阶段确认后的快照"""
    confirmed: bool
    style_options: List[Dict]     # 生成的风格方案
    selected_style: Dict          # 用户选择的风格
    design_spec: Dict             # 设计规范
    confirmed_at: str


class TechSnapshot(TypedDict):
    """技术方案确认后的快照"""
    confirmed: bool
    combined_proposal: Dict       # 综合技术方案
    vote_summary: Dict            # 投票结果摘要
    confirmed_at: str


class FeatureSnapshot(TypedDict):
    """功能选择确认后的快照"""
    confirmed: bool
    project_mode: str             # demo / full
    selected_features: List[str]  # 选中的功能列表
    all_features: List[str]       # 可用功能列表
    confirmed_at: str


class CodeSnapshot(TypedDict):
    """代码生成完成后的快照"""
    api_spec: Dict
    mock_data: Dict
    frontend_code: Dict
    style_code: Dict
    extracted_homepage: str
    completed_at: str


class PhaseTransition(TypedDict):
    """阶段转换记录"""
    from_phase: str
    to_phase: str
    trigger: str                  # user_confirmed / auto / back
    timestamp: str


# ========== 主状态 ==========

class AgentState(TypedDict):
    """LangGraph 工作流状态 — 6 阶段 AI 应用生成器

    分为以下区域：
    - 会话标识
    - 阶段控制
    - 阶段快照（确认后保存）
    - 需求阶段
    - 设计阶段
    - 技术阶段
    - 功能选择阶段
    - 代码生成阶段
    - 交付阶段
    - 人机协作
    - 输出

    注意：旧的 HTML 生成器字段标记为 [DEPRECATED]，暂保留以兼容旧代码，
    后续清理时统一移除。
    """

    # ---- 会话标识 ----
    user_message: str                          # 用户输入消息
    session_id: str                            # 会话ID
    created_at: str                            # 创建时间

    # ---- 阶段控制 ----
    current_phase: str                         # 当前阶段: requirement/design/tech/feature/code/delivery/completed
    phase_status: str                          # 阶段状态: running/waiting_human/completed

    # ---- 阶段快照（确认后保存，用于回退） ----
    requirement_snapshot: Optional[RequirementSnapshot]
    design_snapshot: Optional[DesignSnapshot]
    tech_snapshot: Optional[TechSnapshot]
    feature_snapshot: Optional[FeatureSnapshot]
    code_snapshot: Optional[CodeSnapshot]

    # ---- 阶段历史 ----
    phase_history: List[PhaseTransition]       # 阶段转换记录

    # ---- 需求阶段 ----
    requirements_doc: str                      # 产品需求文档 (PRD)
    requirements_approved: bool                # 需求是否已确认

    # ---- 设计阶段 ----
    design_projects: List[Dict[str, Any]]      # 4套完整项目列表
    selected_style_id: Optional[str]           # 用户选中的风格ID
    selected_design: Optional[Dict[str, Any]]  # 用户选中的完整项目
    design_style: Optional[Dict[str, Any]]     # 选中的风格配置

    # ---- 技术阶段 ----
    tech_spec: Optional[Dict[str, Any]]        # 综合技术方案
    tech_approved: bool                        # 技术方案是否已确认

    # ---- 功能选择阶段 ----
    project_mode: Optional[str]                # demo / full
    selected_features: Optional[List[str]]     # 选中的功能列表
    available_features: Optional[List[str]]    # 可用功能列表
    feature_approved: bool                     # 功能选择是否已确认

    # ---- 代码生成阶段 ----
    api_spec: Optional[Dict[str, Any]]         # API 规范
    mock_data: Optional[Dict[str, Any]]        # Mock 数据
    frontend_code: Optional[Dict[str, Any]]    # 前端代码
    style_code: Optional[Dict[str, Any]]       # 样式代码
    extracted_homepage: Optional[str]          # 提取的首页HTML

    # ---- 交付阶段 ----
    delivery_approved: bool                    # 交付是否已确认
    revision_feedback: Optional[str]           # 修改反馈

    # ---- 人机协作 ----
    human_input_pending: bool                  # 是否等待用户输入
    human_input_checkpoint_id: Optional[str]   # 当前人机协作检查点ID
    human_input_request: Optional[Dict]        # 人机协作请求体

    # ---- 输出 ----
    response_message: str                      # 回复消息
    is_complete: bool                          # 是否完成
    project_config: Optional[Dict[str, Any]]   # 项目配置
    project_files: Optional[Dict[str, str]]    # 生成的项目文件

    # ---- [DEPRECATED] 旧 HTML 生成器字段，待清理 ----
    # 以下字段为旧架构遗留，各子图不应再写入
    base_html: str                             # [DEPRECATED]
    phase: str                                 # [DEPRECATED] 用 current_phase 替代
    stage: str                                 # [DEPRECATED]
    design_concept: str                        # [DEPRECATED] 合并到 requirement_snapshot
    selected_style: str                        # [DEPRECATED] 用 selected_style_id 替代
    available_styles: List[Dict[str, str]]     # [DEPRECATED]
    demo_html: str                             # [DEPRECATED]
    demo_instructions: str                     # [DEPRECATED]
    demo_link: str                             # [DEPRECATED]
    is_demo_ready: bool                        # [DEPRECATED]
    task_list: List[Dict[str, Any]]            # [DEPRECATED]
    current_html: str                          # [DEPRECATED]
    validation_errors: List[str]               # [DEPRECATED]
    iteration_count: int                       # [DEPRECATED]
    fix_count: int                             # [DEPRECATED]
    output_html: str                           # [DEPRECATED]
    output_version: int                        # [DEPRECATED]
    status: Optional[str]                      # [DEPRECATED] 用 phase_status 替代
```

**Step 4: 运行测试确认通过**

Run: `cd /Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge && python -m pytest backend/tests/test_agent_state.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/graph/state.py backend/tests/test_agent_state.py
git commit -m "refactor: restructure AgentState for 6-phase architecture with snapshots"
```

---

## Task 2: 更新各子图引用 — 使用新字段名

**Files:**
- Modify: `backend/app/graph/nodes.py`
- Modify: `backend/app/graph/nodes_human.py`
- Modify: `backend/app/graph/edges.py`
- Modify: `backend/app/graph/subgraphs/requirement.py`
- Modify: `backend/app/graph/subgraphs/design.py`
- Modify: `backend/app/graph/subgraphs/tech.py`
- Modify: `backend/app/graph/subgraphs/feature.py`
- Modify: `backend/app/graph/subgraphs/delivery.py`
- Modify: `backend/app/graph/subgraphs/code.py`
- Test: `backend/tests/test_subgraph_state_fields.py`

**Step 1: 写测试 — 验证子图返回的新字段名正确**

```python
# backend/tests/test_subgraph_state_fields.py
"""验证各子图返回的状态更新使用新字段名"""
import pytest
from app.graph.state import AgentState


class TestRequirementSubgraphState:
    def test_process_response_returns_new_fields(self):
        """RequirementSubgraph.process_response 应使用 current_phase 而非 phase"""
        from app.graph.subgraphs.requirement import RequirementSubgraph
        subgraph = RequirementSubgraph()

        # 模拟确认后的状态更新
        result = subgraph.process_response(
            {"requirements_doc": "# PRD", subgraph.get_state_key(): {"generated_content": {"content": "test"}}},
            {"action": "confirm"}
        )
        # 应写入新字段 current_phase
        assert result.get("current_phase") == "design", f"Expected current_phase=design, got {result}"
        # 不应再写入旧字段 phase
        if "phase" in result:
            assert result["phase"] == "design", "phase should still be set for backward compat"

    def test_process_response_revise(self):
        """revise 应留在 requirement 阶段"""
        from app.graph.subgraphs.requirement import RequirementSubgraph
        subgraph = RequirementSubgraph()

        result = subgraph.process_response(
            {"requirements_doc": "# PRD", subgraph.get_state_key(): {"generated_content": {"content": "test"}}},
            {"action": "revise"}
        )
        assert result.get("current_phase") == "requirement" or result.get("phase") == "requirement"


class TestTechSubgraphState:
    def test_finalize_returns_new_fields(self):
        """TechSubgraph._finalize_node 应写入新字段"""
        from app.graph.subgraphs.tech import TechSubgraph
        from app.graph.subgraphs.debate import VoteResult
        subgraph = TechSubgraph()

        # 模拟有辩论结果的状态
        subgraph_state = {
            "debate_rounds": [],
            "status": "voted",
            "debate_result": VoteResult(
                winner_id="combined",
                winner_proposal={"frontend": {}, "backend": {}, "devops": {}},
                vote_count={},
                total_votes=3
            )
        }

        result = subgraph._finalize_node({subgraph.get_state_key(): subgraph_state})
        assert "tech_spec" in result
        assert "tech_approved" in result
        assert "current_phase" in result or "phase" in result


class TestFeatureSubgraphState:
    def test_validate_returns_new_fields(self):
        """FeatureSubgraph._validate_node 应写入 project_mode 等新字段"""
        from app.graph.subgraphs.feature import FeatureSubgraph
        from app.graph.subgraphs.selection import SelectionResult, Option
        from datetime import datetime

        subgraph = FeatureSubgraph()
        subgraph_state = {
            "user_selection": {"selected_ids": ["full"]},
            "options": [
                Option(id="demo", title="演示版"),
                Option(id="full", title="完整项目版"),
            ],
            "selection_result": None,
            "status": "pending"
        }

        result = subgraph._validate_node({subgraph.get_state_key(): subgraph_state})
        assert result.get("project_mode") == "full"
        assert "selected_features" in result


class TestDeliverySubgraphState:
    def test_process_response_confirm(self):
        """DeliverySubgraph 确认交付应写入 delivery_approved"""
        from app.graph.subgraphs.delivery import DeliverySubgraph
        subgraph = DeliverySubgraph()

        result = subgraph.process_response(
            {subgraph.get_state_key(): {}},
            {"action": "confirm"}
        )
        assert result.get("delivery_approved") is True
        assert "current_phase" in result or "phase" in result
```

**Step 2: 运行测试确认失败**

Run: `cd /Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge && python -m pytest backend/tests/test_subgraph_state_fields.py -v`
Expected: FAIL — 子图还在写旧字段 `phase` 而非 `current_phase`

**Step 3: 更新 RequirementSubgraph.process_response**

文件: `backend/app/graph/subgraphs/requirement.py` 第 137-149 行

将 `process_response` 方法中的 `"phase"` 替换为同时写入 `"current_phase"` 和 `"phase"`（向后兼容）：

```python
    def process_response(self, state: AgentState, response: Dict) -> Dict:
        action = response.get("action", "confirm")
        subgraph_state = state.get(self.get_state_key(), {})
        prd_content = subgraph_state.get("generated_content", {}).get("content", "")

        if action == "confirm":
            return {
                "requirements_doc": prd_content,
                "requirements_approved": True,
                "current_phase": "design",
                "phase": "design",  # [DEPRECATED] 向后兼容
                "phase_status": "running",
            }
        else:
            return {
                "requirements_approved": False,
                "current_phase": "requirement",
                "phase": "requirement",  # [DEPRECATED]
            }
```

**Step 4: 更新 TechSubgraph._finalize_node**

文件: `backend/app/graph/subgraphs/tech.py` 第 262-267 行

```python
    def _finalize_node(self, state: AgentState) -> Dict:
        subgraph_state = self._get_subgraph_state(state)
        if self._result_key not in subgraph_state:
            rounds = subgraph_state.get(self._rounds_key, [])
            if rounds:
                result = self.vote(rounds)
                subgraph_state[self._result_key] = result

        result = subgraph_state.get(self._result_key)
        proposal = result.winner_proposal if result else {}

        subgraph_state[self._status_key] = "completed"

        return {
            self.get_state_key(): subgraph_state,
            "tech_spec": proposal,
            "tech_approved": True,
            "current_phase": "feature",
            "phase": "feature",  # [DEPRECATED]
            "phase_status": "running",
        }
```

**Step 5: 更新 FeatureSubgraph._validate_node**

文件: `backend/app/graph/subgraphs/feature.py` 第 124-132 行

```python
    def _validate_node(self, state: AgentState) -> Dict:
        # ... (前面的逻辑不变) ...
        return {
            self.get_state_key(): subgraph_state,
            "project_mode": selected_mode,
            "selected_features": default_features,
            "available_features": all_features,
            "feature_approved": True,
            "current_phase": "code",
            "phase": "code",  # [DEPRECATED]
            "phase_status": "running",
        }
```

**Step 6: 更新 DeliverySubgraph.process_response**

文件: `backend/app/graph/subgraphs/delivery.py` 第 169-194 行

```python
    def process_response(self, state: AgentState, response: Dict) -> Dict:
        action = response.get("action", "confirm")
        if action == "confirm":
            return {
                "delivery_approved": True,
                "is_complete": True,
                "current_phase": "completed",
                "phase": "completed",  # [DEPRECATED]
                "phase_status": "completed",
            }
        else:
            return {
                "delivery_approved": False,
                "revision_feedback": response.get("feedback", ""),
                "current_phase": "delivery",
                "phase": "delivery",  # [DEPRECATED]
            }
```

**Step 7: 更新 DesignSubgraph.on_enter / on_exit**

文件: `backend/app/graph/subgraphs/design.py`

`on_enter` (第 415-419 行):
```python
    async def on_enter(self, state: Dict) -> Dict:
        state["current_phase"] = "design"
        state["phase_status"] = "running"
        state["phase"] = "design"  # [DEPRECATED]
        return state
```

`on_exit` (第 421-429 行):
```python
    async def on_exit(self, state: Dict) -> Dict:
        from datetime import datetime
        state["design_snapshot"] = {
            "confirmed": True,
            "selected_style": state.get("selected_style_id"),
            "projects_count": state.get("design_aggregate_count", 0),
            "confirmed_at": datetime.now().isoformat()
        }
        return state
```

**Step 8: 更新 CodeSubgraph.on_enter**

文件: `backend/app/graph/subgraphs/code.py` 第 356-361 行

```python
    async def on_enter(self, state: Dict) -> Dict:
        state["current_phase"] = self.name
        state["phase_status"] = "running"
        state[self._prefixed("code_stage_attempts")] = 0
        return state
```

**Step 9: 更新 nodes_human.py — 使用新字段名**

文件: `backend/app/graph/nodes_human.py` 第 7-67 行

关键修改：
- 第 16 行: `phase = state.get("phase", "unknown")` → 同时读 `current_phase` 和 `phase`
- 第 62-67 行: 返回值增加 `current_phase` 和 `phase_status`

```python
    phase = state.get("current_phase") or state.get("phase", "unknown")
    # ...
    return {
        "human_input_pending": True,
        "human_input_checkpoint_id": request["checkpoint_id"],
        "human_input_request": request,
        "phase_status": "waiting_human",
        "phase": phase,  # [DEPRECATED]
    }
```

**Step 10: 更新 graph.py — start_node**

文件: `backend/app/graph/graph.py`（通过 nodes.py 中的 `start_node`）

文件: `backend/app/graph/nodes.py` 第 258-274 行，`start_node` 返回值增加 `current_phase`:

```python
    return {
        "project_config": project_config,
        "stage": "start",
        "task_list": [...],  # [DEPRECATED]
        "current_phase": "requirement",
        "phase": "requirement",  # [DEPRECATED]
        "phase_status": "running",
        "phase_history": [],
    }
```

**Step 11: 运行全部测试**

Run: `cd /Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge && python -m pytest backend/tests/ -v`
Expected: ALL PASS

**Step 12: Commit**

```bash
git add backend/app/graph/nodes.py backend/app/graph/nodes_human.py backend/app/graph/subgraphs/
git add backend/tests/test_subgraph_state_fields.py
git commit -m "refactor: update all subgraphs to use new AgentState field names"
```

---

## Task 3: 添加阶段快照写入逻辑

**Files:**
- Modify: `backend/app/graph/subgraphs/requirement.py`
- Modify: `backend/app/graph/subgraphs/tech.py`
- Modify: `backend/app/graph/subgraphs/feature.py`
- Test: `backend/tests/test_snapshots.py`

**Step 1: 写测试 — 验证各阶段完成后写入快照**

```python
# backend/tests/test_snapshots.py
"""验证各子图在确认后写入对应的阶段快照"""
import pytest
from app.graph.state import AgentState, RequirementSnapshot, TechSnapshot, FeatureSnapshot


class TestRequirementSnapshot:
    def test_confirm_writes_snapshot(self):
        """用户确认 PRD 后应写入 requirement_snapshot"""
        from app.graph.subgraphs.requirement import RequirementSubgraph
        subgraph = RequirementSubgraph()
        subgraph_state = {
            "generated_content": {"content": "# PRD\n\n## 概述\n测试项目"},
            "iteration_count": 1
        }

        result = subgraph.process_response(
            {subgraph.get_state_key(): subgraph_state},
            {"action": "confirm"}
        )

        assert "requirement_snapshot" in result
        snapshot = result["requirement_snapshot"]
        assert snapshot["confirmed"] is True
        assert "prd" in snapshot
        assert "confirmed_at" in snapshot


class TestTechSnapshot:
    def test_finalize_writes_snapshot(self):
        """技术方案确定后应写入 tech_snapshot"""
        from app.graph.subgraphs.tech import TechSubgraph
        from app.graph.subgraphs.debate import VoteResult
        subgraph = TechSubgraph()

        proposal = {"frontend": {"framework": "React"}, "backend": {"language": "Python"}}
        subgraph_state = {
            "debate_rounds": [],
            "debate_result": VoteResult(
                winner_id="combined",
                winner_proposal=proposal,
                vote_count={"frontend_expert": 1, "backend_expert": 1},
                total_votes=2
            ),
            "status": "completed"
        }

        result = subgraph._finalize_node({subgraph.get_state_key(): subgraph_state})

        assert "tech_snapshot" in result
        assert result["tech_snapshot"]["confirmed"] is True
        assert result["tech_snapshot"]["combined_proposal"] == proposal


class TestFeatureSnapshot:
    def test_validate_writes_snapshot(self):
        """功能选择确认后应写入 feature_snapshot"""
        from app.graph.subgraphs.feature import FeatureSubgraph
        from app.graph.subgraphs.selection import Option
        subgraph = FeatureSubgraph()
        subgraph_state = {
            "user_selection": {"selected_ids": ["demo"]},
            "options": [
                Option(id="demo", title="演示版"),
                Option(id="full", title="完整项目版"),
            ],
            "status": "pending"
        }

        result = subgraph._validate_node({subgraph.get_state_key(): subgraph_state})

        assert "feature_snapshot" in result
        assert result["feature_snapshot"]["confirmed"] is True
        assert result["feature_snapshot"]["project_mode"] == "demo"
```

**Step 2: 运行测试确认失败**

Run: `cd /Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge && python -m pytest backend/tests/test_snapshots.py -v`
Expected: FAIL — 子图尚未写入 snapshot

**Step 3: 更新 RequirementSubgraph.process_response — 写入快照**

在确认分支中添加 `requirement_snapshot`:

```python
    def process_response(self, state: AgentState, response: Dict) -> Dict:
        action = response.get("action", "confirm")
        subgraph_state = state.get(self.get_state_key(), {})
        prd_content = subgraph_state.get("generated_content", {}).get("content", "")

        if action == "confirm":
            from datetime import datetime
            return {
                "requirements_doc": prd_content,
                "requirements_approved": True,
                "current_phase": "design",
                "phase": "design",
                "phase_status": "running",
                "requirement_snapshot": {
                    "confirmed": True,
                    "user_input": state.get("user_message", ""),
                    "clarification_qa": [],
                    "prd": prd_content,
                    "confirmed_at": datetime.now().isoformat(),
                },
                "phase_history": state.get("phase_history", []) + [{
                    "from_phase": "requirement",
                    "to_phase": "design",
                    "trigger": "user_confirmed",
                    "timestamp": datetime.now().isoformat(),
                }],
            }
        else:
            return {
                "requirements_approved": False,
                "current_phase": "requirement",
                "phase": "requirement",
            }
```

**Step 4: 更新 TechSubgraph._finalize_node — 写入快照**

```python
    def _finalize_node(self, state: AgentState) -> Dict:
        # ... (现有逻辑不变) ...
        from datetime import datetime
        history = state.get("phase_history", [])
        return {
            self.get_state_key(): subgraph_state,
            "tech_spec": proposal,
            "tech_approved": True,
            "current_phase": "feature",
            "phase": "feature",
            "phase_status": "running",
            "tech_snapshot": {
                "confirmed": True,
                "combined_proposal": proposal,
                "vote_summary": result.vote_count if result else {},
                "confirmed_at": datetime.now().isoformat(),
            },
            "phase_history": history + [{
                "from_phase": "tech",
                "to_phase": "feature",
                "trigger": "auto",
                "timestamp": datetime.now().isoformat(),
            }],
        }
```

**Step 5: 更新 FeatureSubgraph._validate_node — 写入快照**

```python
    def _validate_node(self, state: AgentState) -> Dict:
        # ... (现有逻辑不变) ...
        from datetime import datetime
        history = state.get("phase_history", [])
        return {
            self.get_state_key(): subgraph_state,
            "project_mode": selected_mode,
            "selected_features": default_features,
            "available_features": all_features,
            "feature_approved": True,
            "current_phase": "code",
            "phase": "code",
            "phase_status": "running",
            "feature_snapshot": {
                "confirmed": True,
                "project_mode": selected_mode,
                "selected_features": default_features,
                "all_features": all_features,
                "confirmed_at": datetime.now().isoformat(),
            },
            "phase_history": history + [{
                "from_phase": "feature",
                "to_phase": "code",
                "trigger": "user_confirmed",
                "timestamp": datetime.now().isoformat(),
            }],
        }
```

**Step 6: 运行测试确认通过**

Run: `cd /Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge && python -m pytest backend/tests/test_snapshots.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add backend/app/graph/subgraphs/requirement.py backend/app/graph/subgraphs/tech.py backend/app/graph/subgraphs/feature.py backend/tests/test_snapshots.py
git commit -m "feat: add phase snapshot writing on confirmation"
```

---

## Task 4: 更新 CODE_WIKI.md 文档

**Files:**
- Modify: `CODE_WIKI.md`

**Step 1: 更新 AgentState 字段文档部分**

找到 CODE_WIKI.md 中 `AgentState` 相关章节，更新为新的字段列表和说明。包括：
- 新增 Snapshot 类型说明
- 新增 `current_phase` / `phase_status` 说明
- 标记 DEPRECATED 字段
- 说明各子图写入/读取哪些字段

**Step 2: Commit**

```bash
git add CODE_WIKI.md
git commit -m "docs: update CODE_WIKI with new AgentState structure"
```

---

## 执行注意事项

1. **向后兼容原则**：每个 Task 中，新字段和旧字段同时写入，旧字段标注 `[DEPRECATED]`。这样即使前端或其他代码还在读旧字段，也不会中断。

2. **子图私有状态不受影响**：各子图通过 `self.get_state_key()`（如 `requirement_subgraph_state`）存取的私有状态是动态写入 `Dict` 的，TypedDict 不约束动态键，无需修改。

3. **LangGraph 的 TypedDict 宽松匹配**：LangGraph 的 `StateGraph(AgentState)` 使用 TypedDict 做类型提示，实际运行时不强制校验所有字段。新增字段不会导致运行时错误。

4. **测试策略**：优先验证「字段存在性」和「写入正确性」，不验证运行时行为（LangGraph 需要 Redis/LLM 环境）。
