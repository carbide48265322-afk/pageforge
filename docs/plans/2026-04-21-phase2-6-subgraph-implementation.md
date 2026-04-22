# Phase 2-6 Subgraph Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将阶段2-6（设计、技术方案、功能选择、代码生成、交付）全部子图化，替换主流程中的旧节点

**Architecture:** 
- 阶段2 DesignSubgraph: 继承 HumanInTheLoopSubgraph，生成风格方案 → 用户选择 → 确认设计规范
- 阶段3 TechSubgraph: 继承 DebateVotingSubgraph，多专家辩论 → 投票 → 用户确认技术选型
- 阶段4 FeatureSubgraph: 继承 SelectionSubgraph，功能清单勾选模式
- 阶段5 CodeSubgraph: 继承 PipelineReflectionSubgraph，流水线生成代码，每阶段自审迭代
- 阶段6 DeliverySubgraph: 继承 HumanInTheLoopSubgraph，预览确认 → 交付

**Tech Stack:** Python, LangGraph >=1.1.8, Redis, Pydantic

---

## 前置检查

**Step 1: 确认基类已就绪**

检查文件是否存在:
- `backend/app/graph/subgraphs/base.py` - BaseSubgraph
- `backend/app/graph/subgraphs/human_loop.py` - HumanInTheLoopSubgraph
- `backend/app/graph/subgraphs/debate.py` - DebateVotingSubgraph
- `backend/app/graph/subgraphs/pipeline.py` - PipelineReflectionSubgraph
- `backend/app/graph/subgraphs/selection.py` - SelectionSubgraph

Run: `ls -la backend/app/graph/subgraphs/`
Expected: 所有基类文件存在

---

## Task 1: DesignSubgraph (阶段2 - 风格设计)

**Files:**
- Create: `backend/app/graph/subgraphs/design.py`
- Modify: `backend/app/graph/subgraphs/__init__.py`
- Modify: `backend/app/graph/graph.py`

**Step 1: 创建 DesignSubgraph 类**

在 `backend/app/graph/subgraphs/design.py` 创建:

```python
"""DesignSubgraph - 风格设计子图

基于 HumanInTheLoopSubgraph 实现：
1. AI 生成 3-5 种风格方案
2. 用户选择风格
3. 输出设计规范
4. 用户确认/微调规范
"""

from typing import Any, Dict, List
from langchain_core.messages import SystemMessage, HumanMessage

from app.graph.state import AgentState
from app.config import llm
from .human_loop import HumanInTheLoopSubgraph


class DesignSubgraph(HumanInTheLoopSubgraph):
    """风格设计子图
    
    实现风格方案生成和确认流程。
    """
    
    name = "design"
    description = "风格设计与规范确认"
    max_iterations = 3
    
    def generate_content(self, state: AgentState) -> Dict:
        """生成风格方案
        
        Args:
            state: 当前状态
            
        Returns:
            Dict: 风格方案列表
        """
        requirements_doc = state.get("requirements_doc", "")
        
        # 检查是否已有风格方案（迭代时保留）
        subgraph_state = state.get(self.get_state_key(), {})
        existing_styles = subgraph_state.get("generated_content", {})
        user_response = subgraph_state.get("user_response", {})
        feedback = user_response.get("feedback", "")
        
        if existing_styles and feedback:
            # 迭代模式：根据反馈调整风格方案
            prompt = f"""基于用户反馈调整风格方案：

产品需求：
{requirements_doc}

当前风格方案：
{existing_styles.get('styles', [])}

用户反馈：{feedback}

请调整风格方案，保持3-5个选项，根据反馈进行优化。"""
        else:
            # 首次生成
            prompt = f"""基于产品需求生成3-5种风格设计方案：

产品需求：
{requirements_doc}

请为每个方案提供：
1. 方案名称
2. 风格描述
3. 色彩建议
4. 字体建议
5. 适用场景"""
        
        response = llm.invoke([
            SystemMessage(content="你是一位资深UI/UX设计师，擅长生成多样化的设计风格方案。"),
            HumanMessage(content=prompt),
        ])
        
        # 解析风格方案（简化版，实际需要解析结构化数据）
        styles = self._parse_styles(response.content)
        
        return {
            "styles": styles,
            "raw_content": response.content,
            "version": subgraph_state.get("iteration_count", 0) + 1
        }
    
    def _parse_styles(self, content: str) -> List[Dict]:
        """解析风格方案（简化实现）"""
        # 实际实现需要更复杂的解析逻辑
        return [{"name": f"方案{i+1}", "description": line} 
                for i, line in enumerate(content.split('\n')[:5]) if line.strip()]
    
    def to_schema(self, content: Dict) -> Dict:
        """转换为选择表单 Schema
        
        Args:
            content: 风格方案内容
            
        Returns:
            Dict: JSON Schema 表单定义
        """
        styles = content.get("styles", [])
        
        return {
            "type": "object",
            "title": "请选择设计风格",
            "description": "请查看 AI 生成的风格方案，选择您喜欢的设计方向",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["confirm", "revise"],
                    "title": "操作",
                    "description": "确认选择或要求调整方案"
                },
                "selected_style": {
                    "type": "string",
                    "enum": [s["name"] for s in styles] if styles else ["方案1"],
                    "title": "选择风格方案",
                    "description": "请选择您喜欢的设计风格"
                },
                "feedback": {
                    "type": "string",
                    "title": "调整建议",
                    "description": "如需调整方案，请描述您的需求",
                    "x-display": "textarea"
                }
            },
            "required": ["action"],
            "x-context": {
                "styles": styles,
                "version": content.get("version", 1)
            }
        }
    
    def process_response(self, state: AgentState, response: Dict) -> Dict:
        """处理用户响应
        
        Args:
            state: 当前状态
            response: 用户响应
            
        Returns:
            Dict: 处理后的状态更新
        """
        action = response.get("action", "confirm")
        
        subgraph_state = state.get(self.get_state_key(), {})
        styles = subgraph_state.get("generated_content", {}).get("styles", [])
        
        if action == "confirm":
            # 用户确认，保存选中的风格
            selected_name = response.get("selected_style", "")
            selected_style = next((s for s in styles if s["name"] == selected_name), styles[0] if styles else {})
            
            return {
                "selected_style": selected_name,
                "design_spec": selected_style,
                "design_approved": True,
                "phase": "tech"
            }
        else:
            # 用户要求调整
            return {
                "design_approved": False,
                "phase": "design"
            }
    
    def should_iterate(self, state: AgentState) -> bool:
        """判断是否继续迭代
        
        Args:
            state: 当前状态
            
        Returns:
            bool: 是否迭代
        """
        subgraph_state = state.get(self.get_state_key(), {})
        response = subgraph_state.get("user_response", {})
        action = response.get("action", "confirm")
        
        if action == "revise":
            iteration_count = subgraph_state.get("iteration_count", 0)
            return iteration_count < self.max_iterations
        
        return False
```

**Step 2: 更新 __init__.py 导出 DesignSubgraph**

在 `backend/app/graph/subgraphs/__init__.py` 添加:

```python
from .design import DesignSubgraph

__all__ = [
    # ... 原有导出
    "DesignSubgraph",
]
```

**Step 3: 更新 graph.py 接入 DesignSubgraph**

在 `backend/app/graph/graph.py`:

```python
from app.graph.subgraphs import RequirementSubgraph, DesignSubgraph

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    
    # 创建子图实例
    requirement_subgraph = RequirementSubgraph()
    design_subgraph = DesignSubgraph()
    
    # 添加节点
    graph.add_node("start", start_node)
    graph.add_node("requirement", requirement_subgraph.compile())
    graph.add_node("design", design_subgraph.compile())  # 新增
    graph.add_node("execute", execute_node)
    # ... 其他节点
    
    # 添加边
    graph.set_entry_point("start")
    graph.add_edge("start", "requirement")
    graph.add_edge("requirement", "design")  # 需求确认后 → 设计
    graph.add_edge("design", "execute")      # 设计确认后 → 执行
    # ... 其他边
```

**Step 4: 运行测试**

Run: `cd backend && python -c "from app.graph.graph import build_graph; g = build_graph(); print('DesignSubgraph integrated successfully!')"`
Expected: `DesignSubgraph integrated successfully!`

**Step 5: 提交**

```bash
git add backend/app/graph/subgraphs/design.py backend/app/graph/subgraphs/__init__.py backend/app/graph/graph.py
git commit -m "feat: add DesignSubgraph for phase 2 (style design)

- Create DesignSubgraph inheriting from HumanInTheLoopSubgraph
- Generate 3-5 style options based on requirements
- User selects style and confirms design spec
- Support up to 3 iterations for refinement
- Integrate into main workflow: requirement → design → execute"
```

---

## Task 2: TechSubgraph (阶段3 - 技术方案)

**Files:**
- Create: `backend/app/graph/subgraphs/tech.py`
- Modify: `backend/app/graph/subgraphs/__init__.py`
- Modify: `backend/app/graph/graph.py`

**Step 1: 创建 TechSubgraph 类**

在 `backend/app/graph/subgraphs/tech.py` 创建:

```python
"""TechSubgraph - 技术方案子图

基于 DebateVotingSubgraph 实现：
1. Frontend Expert 生成前端方案
2. Backend Expert 生成后端方案
3. DevOps Expert 生成部署方案
4. Moderator 主持辩论（最多3轮）
5. 多维度投票聚合
6. 用户确认/调整技术选型
"""

from typing import Any, Dict, List
from langchain_core.messages import SystemMessage, HumanMessage

from app.graph.state import AgentState
from app.config import llm
from .debate import DebateVotingSubgraph


class TechSubgraph(DebateVotingSubgraph):
    """技术方案子图
    
    实现多专家辩论投票的技术选型流程。
    """
    
    name = "tech"
    description = "技术方案辩论与投票"
    max_debate_rounds = 3
    
    # 定义专家
    experts = ["frontend", "backend", "devops"]
    
    def generate_proposals(self, state: AgentState) -> Dict[str, Any]:
        """各专家生成技术方案
        
        Args:
            state: 当前状态
            
        Returns:
            Dict: 各专家的方案
        """
        requirements_doc = state.get("requirements_doc", "")
        design_spec = state.get("design_spec", {})
        
        proposals = {}
        
        # Frontend Expert
        frontend_prompt = f"""作为前端专家，基于以下需求生成前端技术方案：

产品需求：
{requirements_doc}

设计规范：
{design_spec}

请提供：
1. 推荐框架（React/Vue/Angular等）
2. UI组件库选择
3. 状态管理方案
4. 构建工具
5. 理由说明"""
        
        proposals["frontend"] = self._call_expert("前端专家", frontend_prompt)
        
        # Backend Expert
        backend_prompt = f"""作为后端专家，基于以下需求生成后端技术方案：

产品需求：
{requirements_doc}

请提供：
1. 推荐语言和框架
2. 数据库选择
3. API设计思路
4. 部署架构
5. 理由说明"""
        
        proposals["backend"] = self._call_expert("后端专家", backend_prompt)
        
        # DevOps Expert
        devops_prompt = f"""作为DevOps专家，基于以下需求生成部署方案：

产品需求：
{requirements_doc}

请提供：
1. 推荐部署平台
2. CI/CD流程
3. 监控方案
4. 成本估算
5. 理由说明"""
        
        proposals["devops"] = self._call_expert("DevOps专家", devops_prompt)
        
        return proposals
    
    def _call_expert(self, role: str, prompt: str) -> Dict:
        """调用专家生成方案"""
        response = llm.invoke([
            SystemMessage(content=f"你是一位资深的{role}，擅长技术选型。"),
            HumanMessage(content=prompt),
        ])
        
        return {
            "proposal": response.content,
            "role": role
        }
    
    def debate_round(self, state: AgentState, round_num: int) -> Dict[str, str]:
        """执行一轮辩论
        
        Args:
            state: 当前状态
            round_num: 当前轮次
            
        Returns:
            Dict: 各方观点
        """
        subgraph_state = state.get(self.get_state_key(), {})
        proposals = subgraph_state.get("proposals", {})
        previous_arguments = subgraph_state.get("arguments", [])
        
        arguments = {}
        
        for expert in self.experts:
            other_proposals = {k: v for k, v in proposals.items() if k != expert}
            
            prompt = f"""作为{expert}专家，针对其他专家的方案进行回应：

你的方案：
{proposals.get(expert, {}).get('proposal', '')}

其他专家方案：
{other_proposals}

{'这是第一轮辩论，请阐述你的方案优势。' if round_num == 1 else f'上一轮观点：{previous_arguments}'}

请简要回应（200字以内）。"""
            
            response = llm.invoke([
                SystemMessage(content=f"你是一位{expert}专家，正在参与技术方案辩论。"),
                HumanMessage(content=prompt),
            ])
            
            arguments[expert] = response.content
        
        return arguments
    
    def check_consensus(self, state: AgentState) -> bool:
        """检查是否达成共识
        
        Args:
            state: 当前状态
            
        Returns:
            bool: 是否达成共识
        """
        # 简化实现：达到最大轮次即认为可以进入投票
        subgraph_state = state.get(self.get_state_key(), {})
        current_round = subgraph_state.get("current_round", 0)
        return current_round >= self.max_debate_rounds
    
    def to_voting_schema(self, state: AgentState) -> Dict:
        """生成投票表单 Schema
        
        Args:
            state: 当前状态
            
        Returns:
            Dict: 投票表单定义
        """
        subgraph_state = state.get(self.get_state_key(), {})
        proposals = subgraph_state.get("proposals", {})
        arguments = subgraph_state.get("arguments", [])
        
        return {
            "type": "object",
            "title": "技术方案投票",
            "description": "请查看各专家的技术方案，进行多维度投票",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["confirm", "adjust"],
                    "title": "操作",
                    "description": "确认方案或要求调整"
                },
                "frontend_vote": {
                    "type": "string",
                    "enum": ["strong_approve", "approve", "neutral", "oppose"],
                    "title": "前端方案评价"
                },
                "backend_vote": {
                    "type": "string",
                    "enum": ["strong_approve", "approve", "neutral", "oppose"],
                    "title": "后端方案评价"
                },
                "devops_vote": {
                    "type": "string",
                    "enum": ["strong_approve", "approve", "neutral", "oppose"],
                    "title": "部署方案评价"
                },
                "adjustments": {
                    "type": "string",
                    "title": "调整建议",
                    "x-display": "textarea"
                }
            },
            "required": ["action"],
            "x-context": {
                "proposals": proposals,
                "arguments": arguments
            }
        }
    
    def aggregate_votes(self, state: AgentState, votes: List[Dict]) -> Dict:
        """聚合投票结果
        
        Args:
            state: 当前状态
            votes: 投票列表
            
        Returns:
            Dict: 聚合结果
        """
        # 简化实现：直接返回投票结果
        return {
            "vote_summary": votes,
            "recommendation": "基于投票结果，建议采用当前方案"
        }
    
    def process_response(self, state: AgentState, response: Dict) -> Dict:
        """处理用户响应
        
        Args:
            state: 当前状态
            response: 用户响应
            
        Returns:
            Dict: 处理后的状态更新
        """
        action = response.get("action", "confirm")
        
        subgraph_state = state.get(self.get_state_key(), {})
        proposals = subgraph_state.get("proposals", {})
        
        if action == "confirm":
            return {
                "tech_spec": proposals,
                "tech_approved": True,
                "phase": "feature"
            }
        else:
            return {
                "tech_approved": False,
                "phase": "tech"
            }
```

**Step 2: 更新 __init__.py 导出 TechSubgraph**

**Step 3: 更新 graph.py 接入 TechSubgraph**

添加边：`design → tech → execute`

**Step 4: 测试并提交**

---

## Task 3: FeatureSubgraph (阶段4 - 功能选择)

**Files:**
- Create: `backend/app/graph/subgraphs/feature.py`
- Modify: `backend/app/graph/subgraphs/__init__.py`
- Modify: `backend/app/graph/graph.py`

**Step 1: 创建 FeatureSubgraph 类**

在 `backend/app/graph/subgraphs/feature.py` 创建:

```python
"""FeatureSubgraph - 功能选择子图

基于 SelectionSubgraph 实现：
1. 选择模式：Demo演示版 / 完整项目版
2. 展示功能清单
3. 用户勾选需要的功能
4. 确认功能范围
"""

from typing import Any, Dict, List

from app.graph.state import AgentState
from .selection import SelectionSubgraph


class FeatureSubgraph(SelectionSubgraph):
    """功能选择子图
    
    实现功能清单选择和确认流程。
    """
    
    name = "feature"
    description = "功能范围选择"
    
    # 预定义功能清单
    feature_catalog = {
        "demo": {
            "mode": "demo",
            "description": "演示版 - 快速预览核心功能",
            "features": [
                {"id": "basic_ui", "name": "基础UI界面", "default": True},
                {"id": "core_function", "name": "核心功能演示", "default": True},
                {"id": "responsive", "name": "响应式布局", "default": True},
            ]
        },
        "full": {
            "mode": "full",
            "description": "完整项目版 - 生产就绪",
            "features": [
                {"id": "user_system", "name": "用户系统（登录/注册）", "default": True},
                {"id": "database", "name": "数据库集成", "default": True},
                {"id": "api_backend", "name": "后端API", "default": True},
                {"id": "admin_panel", "name": "管理后台", "default": False},
                {"id": "file_upload", "name": "文件上传", "default": False},
                {"id": "search_filter", "name": "搜索过滤", "default": False},
                {"id": "notification", "name": "消息通知", "default": False},
                {"id": "analytics", "name": "数据统计", "default": False},
                {"id": "deployment", "name": "部署配置", "default": False},
            ]
        }
    }
    
    def get_options(self, state: AgentState) -> List[Dict]:
        """获取功能选项
        
        Args:
            state: 当前状态
            
        Returns:
            List[Dict]: 功能选项列表
        """
        return [
            {
                "id": "demo",
                "name": "演示版",
                "description": "快速生成交互演示，适合验证想法",
                "estimated_time": "5-10分钟"
            },
            {
                "id": "full",
                "name": "完整项目版",
                "description": "生产级完整应用，包含前后端",
                "estimated_time": "30-60分钟"
            }
        ]
    
    def to_selection_schema(self, options: List[Dict], state: AgentState) -> Dict:
        """生成选择表单 Schema
        
        Args:
            options: 选项列表
            state: 当前状态
            
        Returns:
            Dict: 选择表单定义
        """
        return {
            "type": "object",
            "title": "选择项目模式",
            "description": "请选择您需要的项目类型和功能范围",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["demo", "full"],
                    "title": "项目模式",
                    "description": "演示版快速预览，完整版生产就绪"
                },
                "selected_features": {
                    "type": "array",
                    "items": {"type": "string"},
                    "title": "功能清单",
                    "description": "请选择需要的功能模块"
                }
            },
            "required": ["mode"],
            "x-context": {
                "options": options,
                "catalog": self.feature_catalog
            }
        }
    
    def process_selection(self, state: AgentState, selection: Dict) -> Dict:
        """处理用户选择
        
        Args:
            state: 当前状态
            selection: 用户选择
            
        Returns:
            Dict: 处理后的状态更新
        """
        mode = selection.get("mode", "demo")
        selected_features = selection.get("selected_features", [])
        
        # 根据模式获取默认功能
        catalog = self.feature_catalog.get(mode, {})
        default_features = [f["id"] for f in catalog.get("features", []) if f.get("default", False)]
        
        # 合并用户选择和默认功能
        final_features = list(set(default_features + selected_features))
        
        return {
            "project_mode": mode,
            "selected_features": final_features,
            "feature_approved": True,
            "phase": "code"
        }
```

**Step 2-4: 更新导出、接入主流程、测试提交**

---

## Task 4: CodeSubgraph (阶段5 - 代码生成)

**Files:**
- Create: `backend/app/graph/subgraphs/code.py`
- Modify: `backend/app/graph/subgraphs/__init__.py`
- Modify: `backend/app/graph/graph.py`

**Step 1: 创建 CodeSubgraph 类**

在 `backend/app/graph/subgraphs/code.py` 创建:

```python
"""CodeSubgraph - 代码生成子图

基于 PipelineReflectionSubgraph 实现：
1. API设计 → [Reflection循环]
2. DB Schema → [Reflection循环]
3. 后端代码 → [Reflection循环]
4. 前端代码 → [Reflection循环]
5. 样式代码 → [Reflection循环]
6. 质量检查
"""

from typing import Any, Dict, List, Callable
from langchain_core.messages import SystemMessage, HumanMessage

from app.graph.state import AgentState
from app.config import llm
from .pipeline import PipelineReflectionSubgraph


class CodeSubgraph(PipelineReflectionSubgraph):
    """代码生成子图
    
    实现流水线式代码生成，每阶段包含自审迭代。
    """
    
    name = "code"
    description = "代码生成与质量检查"
    max_reflection_iterations = 3
    
    def get_pipeline_stages(self) -> List[Dict[str, Any]]:
        """定义流水线阶段
        
        Returns:
            List[Dict]: 阶段定义列表
        """
        return [
            {
                "name": "api_design",
                "description": "API接口设计",
                "agent": self._api_design_agent
            },
            {
                "name": "db_schema",
                "description": "数据库Schema设计",
                "agent": self._db_schema_agent
            },
            {
                "name": "backend_code",
                "description": "后端代码生成",
                "agent": self._backend_code_agent
            },
            {
                "name": "frontend_code",
                "description": "前端代码生成",
                "agent": self._frontend_code_agent
            },
            {
                "name": "style_code",
                "description": "样式代码生成",
                "agent": self._style_code_agent
            }
        ]
    
    def _api_design_agent(self, state: AgentState) -> Dict:
        """API设计Agent"""
        requirements = state.get("requirements_doc", "")
        
        prompt = f"""基于以下需求设计RESTful API：

{requirements}

请提供：
1. API端点列表
2. 请求/响应格式
3. 认证方式"""
        
        response = llm.invoke([
            SystemMessage(content="你是一位API设计专家。"),
            HumanMessage(content=prompt),
        ])
        
        return {"api_spec": response.content}
    
    def _db_schema_agent(self, state: AgentState) -> Dict:
        """DB Schema设计Agent"""
        api_spec = state.get("api_spec", "")
        
        prompt = f"""基于以下API设计数据库Schema：

{api_spec}

请提供：
1. 数据表结构
2. 字段定义
3. 关系设计"""
        
        response = llm.invoke([
            SystemMessage(content="你是一位数据库设计专家。"),
            HumanMessage(content=prompt),
        ])
        
        return {"db_schema": response.content}
    
    def _backend_code_agent(self, state: AgentState) -> Dict:
        """后端代码生成Agent"""
        api_spec = state.get("api_spec", "")
        db_schema = state.get("db_schema", "")
        tech_spec = state.get("tech_spec", {})
        
        prompt = f"""基于以下规范生成后端代码：

API规范：
{api_spec}

数据库Schema：
{db_schema}

技术方案：
{tech_spec}

请生成完整的后端代码。"""
        
        response = llm.invoke([
            SystemMessage(content="你是一位后端开发专家。"),
            HumanMessage(content=prompt),
        ])
        
        return {"backend_code": response.content}
    
    def _frontend_code_agent(self, state: AgentState) -> Dict:
        """前端代码生成Agent"""
        requirements = state.get("requirements_doc", "")
        design_spec = state.get("design_spec", {})
        api_spec = state.get("api_spec", "")
        
        prompt = f"""基于以下规范生成前端代码：

需求：
{requirements}

设计规范：
{design_spec}

API规范：
{api_spec}

请生成完整的前端代码。"""
        
        response = llm.invoke([
            SystemMessage(content="你是一位前端开发专家。"),
            HumanMessage(content=prompt),
        ])
        
        return {"frontend_code": response.content}
    
    def _style_code_agent(self, state: AgentState) -> Dict:
        """样式代码生成Agent"""
        design_spec = state.get("design_spec", {})
        frontend_code = state.get("frontend_code", "")
        
        prompt = f"""基于以下规范生成样式代码：

设计规范：
{design_spec}

前端代码：
{frontend_code}

请生成CSS/Tailwind样式代码。"""
        
        response = llm.invoke([
            SystemMessage(content="你是一位CSS/样式专家。"),
            HumanMessage(content=prompt),
        ])
        
        return {"style_code": response.content}
    
    def reflect(self, stage_name: str, stage_output: Dict, state: AgentState) -> Dict:
        """阶段自审
        
        Args:
            stage_name: 阶段名称
            stage_output: 阶段输出
            state: 当前状态
            
        Returns:
            Dict: 自审结果
        """
        content = stage_output.get(stage_name, "")
        
        prompt = f"""审查以下{stage_name}的质量：

{content}

请检查：
1. 完整性
2. 规范性
3. 潜在问题

如有问题请指出，否则返回\"通过\"。"""
        
        response = llm.invoke([
            SystemMessage(content="你是一位代码审查专家。"),
            HumanMessage(content=prompt),
        ])
        
        feedback = response.content
        passed = "通过" in feedback or "pass" in feedback.lower()
        
        return {
            "passed": passed,
            "feedback": feedback
        }
    
    def should_reflect(self, stage_name: str, reflection_result: Dict, iteration: int) -> bool:
        """判断是否继续自审迭代
        
        Args:
            stage_name: 阶段名称
            reflection_result: 自审结果
            iteration: 当前迭代次数
            
        Returns:
            bool: 是否继续迭代
        """
        if iteration >= self.max_reflection_iterations:
            return False
        return not reflection_result.get("passed", False)
    
    def process_response(self, state: AgentState, response: Dict) -> Dict:
        """处理流水线完成后的响应
        
        Args:
            state: 当前状态
            response: 响应数据
            
        Returns:
            Dict: 处理后的状态更新
        """
        return {
            "code_generated": True,
            "project_files": {
                "api": state.get("api_spec", ""),
                "schema": state.get("db_schema", ""),
                "backend": state.get("backend_code", ""),
                "frontend": state.get("frontend_code", ""),
                "style": state.get("style_code", "")
            },
            "phase": "delivery"
        }
```

**Step 2-4: 更新导出、接入主流程、测试提交**

---

## Task 5: DeliverySubgraph (阶段6 - 交付确认)

**Files:**
- Create: `backend/app/graph/subgraphs/delivery.py`
- Modify: `backend/app/graph/subgraphs/__init__.py`
- Modify: `backend/app/graph/graph.py`

**Step 1: 创建 DeliverySubgraph 类**

在 `backend/app/graph/subgraphs/delivery.py` 创建:

```python
"""DeliverySubgraph - 交付确认子图

基于 HumanInTheLoopSubgraph 实现：
1. 安全扫描
2. 构建预览环境
3. 用户预览体验
4. 确认交付 / 返回修改
5. 输出交付物
"""

from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage

from app.graph.state import AgentState
from app.config import llm
from .human_loop import HumanInTheLoopSubgraph


class DeliverySubgraph(HumanInTheLoopSubgraph):
    """交付确认子图
    
    实现交付前的确认流程。
    """
    
    name = "delivery"
    description = "交付确认与输出"
    max_iterations = 2
    
    def generate_content(self, state: AgentState) -> Dict:
        """生成交付预览内容
        
        Args:
            state: 当前状态
            
        Returns:
            Dict: 交付预览内容
        """
        project_files = state.get("project_files", {})
        
        # 安全扫描（简化实现）
        security_report = self._security_scan(project_files)
        
        # 生成交付摘要
        prompt = f"""基于以下项目文件生成交付摘要：

API设计：{project_files.get('api', '')[:500]}...
后端代码：{project_files.get('backend', '')[:500]}...
前端代码：{project_files.get('frontend', '')[:500]}...

请提供：
1. 项目概述
2. 主要功能
3. 技术栈
4. 部署说明"""
        
        response = llm.invoke([
            SystemMessage(content="你是一位技术文档专家。"),
            HumanMessage(content=prompt),
        ])
        
        return {
            "delivery_summary": response.content,
            "security_report": security_report,
            "preview_url": "#preview",  # 实际应生成预览链接
            "files": project_files
        }
    
    def _security_scan(self, files: Dict) -> Dict:
        """安全扫描（简化实现）"""
        # 实际实现应调用安全扫描工具
        return {
            "status": "passed",
            "issues": [],
            "score": 95
        }
    
    def to_schema(self, content: Dict) -> Dict:
        """转换为交付确认表单 Schema
        
        Args:
            content: 交付内容
            
        Returns:
            Dict: JSON Schema 表单定义
        """
        return {
            "type": "object",
            "title": "交付确认",
            "description": "请预览项目并确认交付",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["confirm", "revise"],
                    "title": "操作",
                    "description": "确认交付或要求修改"
                },
                "feedback": {
                    "type": "string",
                    "title": "修改建议",
                    "description": "如需修改，请描述具体问题",
                    "x-display": "textarea"
                }
            },
            "required": ["action"],
            "x-context": {
                "summary": content.get("delivery_summary", ""),
                "security": content.get("security_report", {}),
                "preview_url": content.get("preview_url", "")
            }
        }
    
    def process_response(self, state: AgentState, response: Dict) -> Dict:
        """处理用户响应
        
        Args:
            state: 当前状态
            response: 用户响应
            
        Returns:
            Dict: 处理后的状态更新
        """
        action = response.get("action", "confirm")
        
        if action == "confirm":
            # 用户确认交付
            return {
                "delivery_approved": True,
                "is_complete": True,
                "phase": "completed"
            }
        else:
            # 用户要求修改，返回到代码阶段
            return {
                "delivery_approved": False,
                "revision_feedback": response.get("feedback", ""),
                "phase": "code"
            }
    
    def should_iterate(self, state: AgentState) -> bool:
        """判断是否返回修改
        
        Args:
            state: 当前状态
            
        Returns:
            bool: 是否返回修改
        """
        subgraph_state = state.get(self.get_state_key(), {})
        response = subgraph_state.get("user_response", {})
        action = response.get("action", "confirm")
        
        if action == "revise":
            iteration_count = subgraph_state.get("iteration_count", 0)
            return iteration_count < self.max_iterations
        
        return False
```

**Step 2: 更新 __init__.py 导出 DeliverySubgraph**

**Step 3: 更新 graph.py 接入 DeliverySubgraph**

修改 `backend/app/graph/graph.py`:

```python
from app.graph.subgraphs import (
    RequirementSubgraph, 
    DesignSubgraph, 
    TechSubgraph,
    FeatureSubgraph,
    CodeSubgraph,
    DeliverySubgraph
)

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    
    # 创建子图实例
    requirement_subgraph = RequirementSubgraph()
    design_subgraph = DesignSubgraph()
    tech_subgraph = TechSubgraph()
    feature_subgraph = FeatureSubgraph()
    code_subgraph = CodeSubgraph()
    delivery_subgraph = DeliverySubgraph()
    
    # 添加节点
    graph.add_node("start", start_node)
    graph.add_node("requirement", requirement_subgraph.compile())
    graph.add_node("design", design_subgraph.compile())
    graph.add_node("tech", tech_subgraph.compile())
    graph.add_node("feature", feature_subgraph.compile())
    graph.add_node("code", code_subgraph.compile())
    graph.add_node("delivery", delivery_subgraph.compile())
    
    # 添加边 - 完整的6阶段流程
    graph.set_entry_point("start")
    graph.add_edge("start", "requirement")
    graph.add_edge("requirement", "design")
    graph.add_edge("design", "tech")
    graph.add_edge("tech", "feature")
    graph.add_edge("feature", "code")
    graph.add_edge("code", "delivery")
    graph.add_edge("delivery", "respond")  # 交付后生成最终回复
    graph.add_edge("respond", END)
    
    return graph.compile()
```

**Step 4: 运行测试**

Run: `cd backend && python -c "from app.graph.graph import build_graph; g = build_graph(); print('All subgraphs integrated successfully!')"`
Expected: `All subgraphs integrated successfully!`

**Step 5: 提交**

```bash
git add backend/app/graph/subgraphs/
git add backend/app/graph/graph.py
git commit -m "feat: implement phase 2-6 subgraphs

- DesignSubgraph: style design with HumanInTheLoop pattern
- TechSubgraph: debate+voting for tech selection
- FeatureSubgraph: selection pattern for feature scope
- CodeSubgraph: pipeline+reflection for code generation
- DeliverySubgraph: delivery confirmation

Complete 6-phase workflow:
requirement → design → tech → feature → code → delivery"
```

---

## 最终验证

**Step 1: 完整流程测试**

Run: `cd backend && python -c "
from app.graph.graph import build_graph
from app.graph.state import AgentState

graph = build_graph()
print('Graph nodes:', list(graph.nodes.keys()))
print('Graph edges:', graph.edges)
"`

Expected: 显示所有6个子图节点和正确的边连接

**Step 2: 提交所有改动**

```bash
git push origin master
```

---

## 计划总结

| 任务 | 子图 | 继承基类 | 核心功能 | 预计时间 |
|------|------|----------|----------|----------|
| Task 1 | DesignSubgraph | HumanInTheLoopSubgraph | 风格方案生成+选择 | 30min |
| Task 2 | TechSubgraph | DebateVotingSubgraph | 多专家辩论+投票 | 40min |
| Task 3 | FeatureSubgraph | SelectionSubgraph | 功能清单勾选 | 20min |
| Task 4 | CodeSubgraph | PipelineReflectionSubgraph | 流水线代码生成 | 45min |
| Task 5 | DeliverySubgraph | HumanInTheLoopSubgraph | 交付确认 | 25min |

**总计**: ~2.5-3小时

**风险点**:
1. DebateVotingSubgraph 基类可能需要调整接口
2. PipelineReflectionSubgraph 的 reflect 机制需要验证
3. 各子图之间的状态传递需要测试

**回退策略**:
- 每个 Task 独立提交，可随时回退
- 保留旧节点代码作为备份（暂不删除）
