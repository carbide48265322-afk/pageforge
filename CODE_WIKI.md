# PageForge Code Wiki

## 1. 项目概述

PageForge 是一个基于 LangGraph 的 AI 驱动的应用生成器，提供两种模式：
- **基础模式：通过自然语言对话，自动生成、修改、验证单文件 HTML 页面
- **高级模式**：6 阶段流水线，通过人机协作生成完整的 React 应用

**核心功能**：
- 6 阶段流水线：需求 → 设计 → 技术 → 功能 → 代码 → 交付
- 多专家辩论投票选型
- 多种风格并行生成，用户选择方案
- 人机协作闭环
- 阶段快照与回退机制（Redis持久化）
- 支持技能（Skill）扩展系统
- 单文件 HTML 页面生成与验证

## 2. 技术栈

| 层次 | 技术 | 用途 |
| --- | --- | --- |
| **前端** | React 19 | 用户界面框架 |
| | TypeScript | 类型安全 |
| | Vite 8 | 构建工具 |
| | Tailwind CSS v4 | 样式管理 |
| | react-resizable-panels | 可调整面板 |
| | react-syntax-highlighter | 代码高亮 |
| | lucide-react | 图标库 |
| **后端** | Python 3.13+ | 运行时 |
| | FastAPI | API 框架 |
| | LangGraph | AI 工作流管理 |
| | LangChain | LLM 工具集成 |
| | langchain-openai | OpenAI API 集成 |
| | Pydantic 2.x | 数据验证 |
| | Redis | 检查点持久化 |
| | aiosqlite | 异步 SQLite |
| **通信** | REST API + SSE | 数据传输和流式响应 |

## 3. 整体架构

### 架构图

```
┌─────────────────────────────────────────────────────────┐
│                     前端层 (React + Vite)                    │
│  ┌───────────────────┐    ┌──────────────────────────────┐  │
│  │  ChatPanel    │    │  PreviewPanel (iframe)         │  │
│  │  IdeatePanel  │    │  VersionSelector             │  │
│  │  HumanInput   │    │  响应式尺寸切换            │  │
│  └────────┬──────┘    └──────────────┬──────────────┘  │
│           │ SSE (扁平事件模型)        │                  │
├───────────┼───────────────────────────┼──────────────────┤
│           │    后端层 (FastAPI)         │                  │
│  ┌────────┴───────────────────────────┴───────────────┐ │
│  │  6 阶段 LangGraph 工作流                              │ │
│  │  - 需求子图 → 设计子图 → 代码子图 → 交付子图          │ │
│  │  Skill 自动加载 + 双 LLM 配置                            │ │
│  └───────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Redis Checkpoint Manager (检查点持久化)                  │ │
│  └───────────────────────────────────────────────────────┘ │
│  LangChain + OpenAI API                                    │
└───────────────────────────────────────────────────────────┘
```

## 4. 核心模块

### 4.1 后端核心模块

#### 4.1.1 配置模块 ([backend/app/config.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/config.py)

负责管理应用配置，包括：
- 环境变量加载（.env 文件）
- 目录路径定义
- LLM 客户端配置
- Redis 配置
- 检查点 TTL 配置

**核心配置项**：
- `OPENAI_API_KEY`: OpenAI API 密钥
- `MODEL_NAME`: 主要 LLM 模型（默认 gpt-4o）
- `INTENT_MODEL_NAME`: 意图识别 LLM（默认 gpt-4o-mini）
- Redis host/port/password/db: Redis 连接参数
- `CHECKPOINT_TTL`: 检查点过期时间（默认 3600 秒）
- `CHECKPOINT_RESPONSE_TTL`: 用户响应过期时间（默认 86400 秒）

#### 4.1.2 API 模块

**会话 API** ([backend/app/api/sessions.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/api/sessions.py))：
- 创建新会话
- 获取会话版本列表
- 获取指定版本的 HTML 内容
- 切换基准版本
- 导出 HTML 文件

**消息 API** ([backend/app/api/messages.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/api/messages.py))：
- 处理用户消息
- 实现 SSE 流式响应
- 管理事件流

**检查点 API** ([backend/app/api/checkpoints.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/api/checkpoints.py))：
- 获取会话检查点
- 提交用户响应
- 恢复检查点

**导出 API** ([backend/app/api/export.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/api/export.py))：
- 导出生成的项目

#### 4.1.3 LangGraph 工作流

**主工作流定义** ([backend/app/graph/graph.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/graph.py))：
- 构建完整的 6 阶段工作流
- 集成子图：需求、设计、代码、交付

**状态定义 ([backend/app/graph/state.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/state.py))：
- 定义 `AgentState` 类型，包含工作流中的所有数据
- 阶段快照类型：`RequirementSnapshot`、`DesignSnapshot`、`TechSnapshot`、`FeatureSnapshot`、`CodeSnapshot`
- 阶段转换记录：`PhaseTransition`

**节点实现** ([backend/app/graph/nodes.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/nodes.py))：
- `start_node`: 开始阶段，初始化项目
- `load_skills_and_tools`: 加载 Skill & Tool
- `intent_node`: 意图理解，分析用户需求
- `execute_node`: ReAct 执行，生成/修改 HTML
- `validate_node`: 质量检查，验证 HTML
- `save_node`: 保存版本
- `respond_node`: 生成回复

**工具实现** ([backend/app/graph/tools.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/tools.py))：
- `validate_html`: 验证 HTML 结构和安全性
- 支持 Skill 工具的动态加载

#### 4.1.4 子图模块

**基类** ([backend/app/graph/subgraphs/base.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/subgraphs/base.py))：
- `BaseSubgraph`: 所有子图的基类
- `HumanInTheLoopSubgraph`: 人机协作子图基类
- `PipelineReflectionSubgraph`: 流水线自审子图基类

**子图实现**：
- [requirement.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/subgraphs/requirement.py): 需求理解子图
- [design.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/subgraphs/design.py): 设计子图
- [tech.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/subgraphs/tech.py): 技术选型子图
- [feature.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/subgraphs/feature.py): 功能选择子图
- [code.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/subgraphs/code.py): 代码生成子图
- [delivery.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/subgraphs/delivery.py): 交付确认子图
- [debate.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/subgraphs/debate.py): 专家辩论子图
- [selection.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/subgraphs/selection.py): 选择子图
- [pipeline.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/subgraphs/pipeline.py): 流水线子图
- [human_loop.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/subgraphs/human_loop.py): 人机循环子图
- [homepage_generator.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/subgraphs/homepage_generator.py): 首页生成子图

#### 4.1.5 检查点管理模块

**检查点管理器** ([backend/app/checkpoint/manager.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/checkpoint/manager.py))：
- 保存检查点（人机协作暂停时）
- 恢复检查点（用户响应后）
- 管理检查点过期（默认 1 小时）
- 支持会话级别的检查点列表查询
- 健康检查

**检查点存储** ([backend/app/checkpoint/langgraph_adapter.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/checkpoint/langgraph_adapter.py))：
- LangGraph 检查点适配器

#### 4.1.6 服务模块

**会话服务** ([backend/app/services/session_service.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/services/session_service.py))：
- 管理会话的创建、获取和保存
- 处理会话消息记录

**版本服务** ([backend/app/services/version_service.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/services/version_service.py))：
- 管理版本的保存、获取和查询
- 处理版本之间的关系

**导出服务** ([backend/app/services/export_service.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/services/export_service.py))：
- 导出生成的项目

#### 4.1.7 技能系统

**技能加载器** ([backend/app/skills/loader.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/skills/loader.py))：
- 自动扫描 `skills/` 目录
- 解析 SKILL.md 文件
- 将技能转换为 LangChain 工具

### 4.2 前端核心模块

**主应用** ([frontend/src/App.tsx](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/frontend/src/App.tsx))：
- 组织整体布局
- 管理会话状态
- 处理用户交互

**组件**：
- [ChatPanel.tsx](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/frontend/src/components/ChatPanel.tsx): 聊天面板，显示消息和思考内容
- [PreviewPanel.tsx](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/frontend/src/components/PreviewPanel.tsx): 预览面板，显示生成的 HTML
- [GenerationCard.tsx](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/frontend/src/components/GenerationCard.tsx): 生成卡片，显示 HTML 代码
- [IdeatePanel.tsx](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/frontend/src/components/IdeatePanel.tsx): 构想面板
- [VersionSelector.tsx](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/frontend/src/components/VersionSelector.tsx): 版本选择器
- [StyleSelector.tsx](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/frontend/src/components/StyleSelector.tsx): 风格选择器
- [HumanInputForm.tsx](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/frontend/src/components/HumanInputForm.tsx): 人机协作表单
- [ResizableLayout.tsx](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/frontend/src/components/ResizableLayout.tsx): 可调整大小的布局
- [MessageBubble.tsx](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/frontend/src/components/MessageBubble.tsx): 消息气泡
- [BaseConfirmDialog.tsx](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/frontend/src/components/BaseConfirmDialog.tsx): 确认对话框
- [ExportButton.tsx](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/frontend/src/components/ExportButton.tsx): 导出按钮

**Hooks**：
- [useSSE.ts](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/frontend/src/hooks/useSSE.ts): 处理 SSE 事件流
- [useSession.ts](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/frontend/src/hooks/useSession.ts): 管理会话状态

**服务**：
- [api.ts](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/frontend/src/services/api.ts): API 客户端

## 5. 关键类与函数

### 5.1 后端关键类与函数

#### `build_graph(checkpointer: RedisCheckpointSaver) -> StateGraph
**位置**: [backend/app/graph/graph.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/graph.py#L14-L78)

**功能**: 构建 PageForge LangGraph 工作流

**参数**: `checkpointer` - Redis 检查点存储器（可选）

**返回值**: 编译后的 StateGraph 实例

**说明**: 定义完整的 6 阶段工作流节点和边，包括：开始、加载 Skill/Tool、需求、设计、代码、交付、回复。

---

#### `AgentState` (TypedDict)
**位置**: [backend/app/graph/state.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/state.py#L61-L189)

**功能**: 定义 LangGraph 工作流的状态结构

**核心字段**:
- `session_id`: 会话 ID
- `user_message`: 用户输入消息
- `current_phase`: 当前阶段 (requirement/design/tech/feature/code/delivery/completed)
- `phase_status`: 阶段状态 (running/waiting_human/completed)
- `phase_history`: 阶段转换记录列表
- 各阶段快照 (`requirement_snapshot`, `design_snapshot`, `tech_snapshot`, `feature_snapshot`, `code_snapshot`)
- `requirements_doc`: 产品需求文档
- `requirements_approved`: 需求是否已确认
- `design_projects`: 4 套完整项目列表
- `selected_style_id`: 用户选中的风格 ID
- `tech_spec`: 综合技术方案
- `tech_approved`: 技术方案是否已确认
- `project_mode`: 项目模式 (demo/full)
- `selected_features`: 选中的功能列表
- `project_workdir`: 项目工作目录
- `project_files`: 生成的项目文件
- `delivery_approved`: 交付是否已确认
- `human_input_pending`: 是否等待用户输入
- `loaded_skills`: 已加载的 Skill 名称列表
- `system_prompt`: 合并后的 Skill 系统提示词
- `active_tools`: 已绑定的 Tool 名称列表
- `response_message`: 回复消息
- `is_complete`: 是否完成
- 兼容旧代码的 `[DEPRECATED]` 字段

---

#### `start_node(state: AgentState) -> dict`
**位置**: [backend/app/graph/nodes.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/nodes.py#L258-L278)

**功能**: 开始阶段节点，初始化项目设置和参数

**参数**: `state` - AgentState

**返回值**: 包含项目配置的字典

---

#### `intent_node(state: AgentState) -> dict`
**位置**: [backend/app/graph/nodes.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/nodes.py#L44-L78)

**功能**: 意图理解节点，分析用户需求

**参数**: `state` - AgentState

**返回值**: 包含任务列表的字典

---

#### `execute_node(state: AgentState) -> dict`
**位置**: [backend/app/graph/nodes.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/nodes.py#L87-L168)

**功能**: ReAct 执行节点，生成/修改 HTML

**参数**: `state` - AgentState

**返回值**: 包含当前 HTML 的字典

**说明**: 执行 ReAct 循环，调用 LLM 和工具生成 HTML

---

#### `validate_node(state: AgentState) -> dict`
**位置**: [backend/app/graph/nodes.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/nodes.py#L191-L206)

**功能**: 质量检查节点，验证 HTML 结构和安全性

**参数**: `state` - AgentState

**返回值**: 包含验证错误的字典

---

#### `save_node(state: AgentState) -> dict`
**位置**: [backend/app/graph/nodes.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/nodes.py#L209-L239)

**功能**: 保存版本节点，将 HTML 写入文件系统

**参数**: `state` - AgentState

**返回值**: 包含输出 HTML 和版本的字典

---

#### `respond_node(state: AgentState) -> dict`
**位置**: [backend/app/graph/nodes.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/nodes.py#L242-L255)

**功能**: 生成回复节点，构建返回给用户的最终消息

**参数**: `state` - AgentState

**返回值**: 包含响应消息的字典

---

#### `validate_html(html: str) -> dict`
**位置**: [backend/app/graph/tools.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/graph/tools.py)

**功能**: 验证 HTML 页面的结构和安全性

**参数**: `html` - 待验证的 HTML 内容

**返回值**: 包含验证结果的字典

---

#### `SkillAutoLoader` 类
**位置**: [backend/app/skills/loader.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/skills/loader.py)

**功能**: 自动扫描并加载所有 Skill

**方法**:
- `load_all()`: 扫描目录，发现所有 Skill
- `_parse_skill_md()`: 解析 SKILL.md 的 YAML frontmatter
- `_read_skill_content()`: 读取 SKILL.md 的正文内容

---

#### `create_skill_tools(skills_dir: Path) -> list[Tool]
**位置**: [backend/app/skills/loader.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/skills/loader.py)

**功能**: 将所有 Skill 转换为 LangChain Tools

**参数**: `skills_dir` - 技能目录路径

**返回值**: LangChain 工具列表

---

#### `CheckpointManager` 类
**位置**: [backend/app/checkpoint/manager.py](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/app/checkpoint/manager.py#L13-L406)

**功能**: 检查点管理器，用于人机协作的暂停/恢复

**主要方法**:
- `save()`: 保存检查点
- `load()`: 加载检查点
- `delete()`: 删除检查点
- `list_by_session()`: 获取会话的所有检查点
- `create_human_input_checkpoint()`: 创建人机协作检查点
- `submit_human_response()`: 提交人机协作响应
- `health_check()`: 健康检查

---

### 5.2 前端关键类与函数

#### `useSSE(url: string, options: SSEOptions)
**位置**: [frontend/src/hooks/useSSE.ts](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/frontend/src/hooks/useSSE.ts)

**功能**: 处理 SSE 事件流

**参数**: 
- `url` - SSE 端点 URL
- `options` - 配置选项

**返回值**: 事件状态和数据

---

#### `useSession()`
**位置**: [frontend/src/hooks/useSession.ts](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/frontend/src/hooks/useSession.ts)

**功能**: 管理会话状态

**参数**: 无

**返回值**: 会话状态和操作方法

---

#### `ChatPanel` 组件
**位置**: [frontend/src/components/ChatPanel.tsx](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/frontend/src/components/ChatPanel.tsx)

**功能**: 聊天面板组件

**Props**:
- `messages` - 消息列表
- `onSendMessage` - 发送消息回调

---

#### `PreviewPanel` 组件
**位置**: [frontend/src/components/PreviewPanel.tsx](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/frontend/src/components/PreviewPanel.tsx)

**功能**: 预览面板组件

**Props**:
- `html` - HTML 内容
- `version` - 版本号

---

## 6. 依赖关系

### 6.1 后端依赖

| 依赖 | 版本 | 用途 |
| --- | --- | --- |
| `fastapi` | >= 0.136.0 | API 框架 |
| `uvicorn[standard]` | >= 0.44.0 | ASGI 服务器 |
| `langchain` | >= 1.2.15 | LLM 工具集成 |
| `langchain-openai` | >= 1.1.14 | OpenAI API 集成 |
| `langgraph` | >= 1.1.8 | AI 工作流管理 |
| `langgraph-cli` | >= 0.4.23 | LangGraph CLI |
| `langgraphics` | >= 0.1.0b3 | LangGraph 可视化 |
| `pydantic` | >= 2.13.2 | 数据验证 |
| `pydantic-settings` | >= 2.0.0 | 配置管理 |
| `python-dotenv` | >= 1.2.2 | 环境变量管理 |
| `redis` | >= 5.0.0 | Redis 客户端 |
| `aiosqlite` | >= 0.22.1 | 异步 SQLite |
| `graphviz` | >= 0.21 | 图形可视化 |
| `grandalf` | >= 0.8 | 图形布局 |
| `pydot` | >= 4.0.1 | Graphviz Python 绑定 |

开发依赖:
| 依赖 | 版本 | 用途 |
| --- | --- | --- |
| `mypy` | >= 1.20.1 | 类型检查 |
| `pytest` | >= 9.0.3 | 测试框架 |
| `pytest-asyncio` | >= 0.23.0 | 异步测试 |
| `ruff` | >= 0.15.11 | 代码检查和格式化 |

---

### 6.2 前端依赖

| 依赖 | 版本 | 用途 |
| --- | --- | --- |
| `react` | ^19.2.4 | UI 框架 |
| `react-dom` | ^19.2.4 | DOM 操作 |
| `lucide-react` | ^1.8.0 | 图标库 |
| `react-resizable-panels` | ^4.10.0 | 可调整面板 |
| `react-syntax-highlighter` | ^16.1.1 | 代码高亮 |

开发依赖:
| 依赖 | 版本 | 用途 |
| --- | --- | --- |
| `@types/react` | ^19.2.14 | React 类型定义 |
| `@types/react-dom` | ^19.2.3 | React DOM 类型定义 |
| `@types/react-syntax-highlighter` | ^15.5.13 | 语法高亮类型定义 |
| `@types/node` | ^24.12.2 | Node 类型定义 |
| `@vitejs/plugin-react` | ^6.0.1 | Vite React 插件 |
| `@tailwindcss/vite` | ^4.2.2 | Tailwind Vite 插件 |
| `tailwindcss` | ^4.2.2 | 样式框架 |
| `typescript` | ~6.0.2 | TypeScript |
| `typescript-eslint` | ^8.58.0 | TypeScript ESLint |
| `eslint` | ^9.39.4 | 代码检查 |
| `eslint-plugin-react-hooks` | ^7.0.1 | React Hooks 检查 |
| `eslint-plugin-react-refresh` | ^0.5.2 | React Refresh 检查 |
| `@eslint/js` | ^9.39.4 | ESLint JS 配置 |
| `globals` | ^17.4.0 | 全局变量 |
| `vite` | ^8.0.4 | 构建工具 |

---

## 7. 项目运行方式

### 7.1 环境要求

- Python >= 3.13
- Node.js >= 18
- Redis (用于检查点持久化)

---

### 7.2 后端启动

```bash
# 进入后端目录
cd backend

# 安装依赖 (推荐使用 uv)
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 OPENAI_API_KEY
# 可选: 配置 Redis 连接参数

# 启动 Redis (使用 Docker Compose)
docker-compose up -d redis

# 启动后端服务器
uvicorn app.main:app --reload
```

---

### 7.3 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

---

### 7.4 使用 Docker Compose

项目根目录包含 [docker-compose.yml](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/docker-compose.yml)，可以一键启动 Redis。

---

### 7.5 访问应用

打开浏览器访问 http://localhost:5173

---

## 8. API 接口

### 8.1 会话 API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/sessions` | 创建新会话 |
| `GET` | `/api/sessions/{id}/versions` | 获取版本列表 |
| `GET` | `/api/sessions/{id}/html` | 获取指定版本 HTML |
| `POST` | `/api/sessions/{id}/base-version` | 切换基准版本 |
| `GET` | `/api/sessions/{id}/export` | 导出 HTML 文件 |
| `POST` | `/api/sessions/{id}/messages` | 发送消息 (SSE 流式响应) |

---

### 8.2 检查点 API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/checkpoints/{session_id}` | 获取会话检查点 |
| `POST` | `/api/checkpoints/{checkpoint_id}/response` | 提交用户响应 |

---

### 8.3 其他 API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/health` | 健康检查 |
| `GET` | `/health` | 健康检查 (含 Redis 状态) |

---

## 9. 工作流程

### 9.1 6 阶段流水线工作流

```
用户输入
    ↓
[开始阶段] → 初始化项目配置
    ↓
[加载 Skill/Tool] → 扫描 skills/ 目录，加载技能工具
    ↓
[需求子图] → 生成 PRD，等待用户确认
    ↓ (用户确认)
[设计子图] → 生成 4 套风格，等待用户选择
    ↓ (用户选择)
[代码子图] → 生成完整 React 应用代码
    ↓
[交付子图] → 确认交付，等待用户确认
    ↓ (用户确认)
[回复阶段] → 生成最终回复
    ↓
结束
```

---

### 9.2 单文件 HTML 生成工作流

```
用户输入
    ↓
[intent 节点] → 意图识别
    ↓
[execute 节点] → ReAct 循环，生成/修改 HTML
    ↓
[validate 节点] → 验证 HTML
    ↓ (有错误且修复次数 < 3) → 返回 execute 节点
    ↓
[save 节点] → 保存版本
    ↓
[respond 节点] → 生成回复
    ↓
结束
```

---

### 9.3 SSE 事件模型

采用扁平事件模型，前端按 block 类型分组渲染：

| 事件 | 说明 |
| --- | --- |
| `MESSAGE_START` | 消息开始 |
| `REASONING_CHUNK` | 思考内容增量（合并渲染） |
| `TOOL_CALL` | 工具调用开始 |
| `TOOL_RESULT` | 工具调用结果 |
| `GENERATION_START` | HTML 生成开始（骨架屏） |
| `GENERATION_DONE` | HTML 生成完成（卡片） |
| `CHUNK_DELTA` | 文本增量（打字机效果） |
| `HTML_STREAM` | HTML 源码流式推送（预览面板） |
| `HTML_UPDATE` | 最终 HTML（iframe 渲染） |
| `HUMAN_INPUT_REQUEST` | 人机协作请求 |
| `done` | 消息结束 |

**前端渲染顺序**: Think（合并）→ Tool（按序）→ Content（text + generation 按序）

---

## 10. 版本管理

- 每次生成保存新版本（`v1`, `v2`, `v3`...）
- 支持切换基准版本（基于指定版本修改）
- 支持查看历史版本
- 支持导出下载 HTML 文件

---

## 11. 部署与配置

### 11.1 环境变量配置

`.env` 文件配置：

```env
# OpenAI 配置
OPENAI_API_KEY=sk-your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4o
INTENT_MODEL_NAME=gpt-4o-mini

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=pageforge
REDIS_DB=0

# 检查点配置
CHECKPOINT_TTL=3600
CHECKPOINT_RESPONSE_TTL=86400
```

---

### 11.2 目录结构

```
pageforge/
├── backend/                     # 后端代码
│   ├── app/
│   │   ├── api/              # API 路由
│   │   ├── graph/            # LangGraph 工作流
│   │   │   ├── subgraphs/    # 子图实现
│   │   ├── models/           # 数据模型
│   │   ├── services/         # 业务服务
│   │   ├── skills/           # 技能系统
│   │   ├── checkpoint/       # 检查点管理
│   │   ├── tools/            # 工具
│   │   ├── config.py       # 配置
│   │   └── main.py         # 入口
│   ├── tests/                # 测试
│   └── pyproject.toml       # 依赖管理
│   └── README.md
├── frontend/                   # 前端代码
│   ├── public/              # 静态资源
│   ├── src/
│   │   ├── components/       # UI 组件
│   │   ├── hooks/          # 自定义 hooks
│   │   ├── services/       # 服务
│   │   ├── App.tsx        # 主应用
│   │   └── main.tsx       # 入口
│   └── package.json        # 依赖管理
├── skills/                   # Skill 定义目录
│   └── frontend-design/   # 前端设计技能
│       └── SKILL.md
├── data/                     # 运行时数据 (gitignore)
├── docs/                     # 文档
│   └── plans/             # 计划文档
├── redis/                    # Redis 配置
├── docker-compose.yml        # Docker Compose
├── AGENTS.md               # Agent 约束文档
├── CODE_WIKI.md            # 本文档
├── README.md               # 项目说明
└── UPGRADE_PLAN.md         # 升级计划
```

---

## 12. 技能系统

### 12.1 技能定义

在 `skills/` 目录下创建技能，每个技能包含一个 `SKILL.md` 文件：

```markdown
---
name: my-skill
description: Skill 描述，Agent 根据此描述决定是否调用
---

Skill 的详细指南内容...
```

---

### 12.2 技能加载

- 后端启动时自动扫描 `skills/` 目录
- 解析每个技能的 `SKILL.md` 文件
- 将技能转换为 LangChain 工具
- 在 ReAct 循环中可供 LLM 使用

---

## 13. 开发指南

### 13.1 新增技能

1. 在 `skills/` 下新建目录
2. 创建 `SKILL.md`，包含 YAML frontmatter 和正文内容
3. 重启后端，自动生效

---

### 13.2 新增子图

1. 在 `backend/app/graph/subgraphs/` 下创建新文件
2. 继承 `BaseSubgraph` 或其子类
3. 实现 `build()`、`on_enter()`、`on_exit()` 方法
4. 在 `graph.py` 中注册新子图节点
5. 添加边连接到工作流

---

### 13.3 扩展功能

- **添加新工具**: 在 `backend/app/graph/tools.py` 中添加新的工具函数
- **修改工作流**: 在 `backend/app/graph/graph.py` 中调整节点和边
- **添加新 API**: 在 `backend/app/api/` 中添加新的路由
- **扩展前端组件**: 在 `frontend/src/components/` 中添加新组件

---

### 13.4 测试

后端测试位于 `backend/tests/` 目录：

```bash
cd backend
pytest
```

---

## 14. 安全注意事项

- 验证 HTML 内容，防止恶意代码注入
- 限制 LLM 模型的权限和能力
- 保护 API 密钥和环境变量
- 实现适当的错误处理和日志记录
- Redis 密码安全配置
- 检查点 TTL 设置合理的过期时间

---

## 15. 未来扩展方向

- 支持更多 LLM 模型（Claude、Gemini 等）
- 增加更多技能和工具
- 实现模板系统
- 支持团队协作和分享
- 添加更多验证和测试工具
- 优化性能和用户体验
- 支持导出为 GitHub 仓库
- CI/CD 集成
- 更多项目类型支持（Vue、Svelte 等）

---

## 16. 相关文档

- [README.md](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/README.md) - 项目说明
- [AGENTS.md](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/AGENTS.md) - Agent 约束
- [UPGRADE_PLAN.md](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/UPGRADE_PLAN.md) - 升级计划
- [docs/plans/](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/docs/plans/) - 计划文档
- [backend/README.md](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/backend/README.md) - 后端说明
- [frontend/README.md](file:///Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/frontend/README.md) - 前端说明

---

## 17. 术语表

| 术语 | 说明 |
| --- | --- |
| **LangGraph** | LangChain 团队开发的用于构建状态驱动的 LLM 应用框架 |
| **Checkpoint** | 检查点，用于保存和恢复工作流状态 |
| **Subgraph** | 子图，可复用的工作流模块 |
| **Skill** | 技能，为 LLM 提供领域知识 |
| **SSE** | Server-Sent Events，服务器推送事件 |
| **ReAct** | Reasoning + Acting，推理 + 行动的 LLM 工作模式 |
| **Human-in-the-loop** | 人机协作，AI 生成内容后等待用户确认或修改 |
| **PRD** | Product Requirements Document，产品需求文档 |
