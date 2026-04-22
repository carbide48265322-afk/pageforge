# PageForge 项目 Code Wiki

## 1. 项目概述

PageForge 是一个基于 LangGraph 的 6 阶段 AI 应用生成器，通过自然语言对话，经历需求、设计、技术选型、功能选择、代码生成、交付确认 6 个阶段，自动生成完整的 Web 应用。

**核心功能：**
- 6 阶段流水线：需求 → 设计 → 技术 → 功能 → 代码 → 交付
- 多专家辩论投票选型（前端/后端/DevOps 专家辩论）
- 4 种风格并行生成，用户选择方案
- 人机协作闭环（JSON Schema 表单收集数据）
- 阶段快照与回退机制
- 支持技能（Skill）扩展系统

## 2. 技术栈

| 层 | 技术 | 用途 |
| --- | --- | --- |
| 前端 | React 19 | 用户界面框架 |
| 前端 | TypeScript | 类型安全 |
| 前端 | Vite 8 | 构建工具 |
| 前端 | Tailwind CSS v4 | 样式管理 |
| 后端 | FastAPI | API 框架 |
| 后端 | LangGraph | AI 工作流管理 |
| 后端 | LangChain | LLM 工具集成 |
| 后端 | OpenAI API | LLM 服务 |
| 通信 | REST API + SSE | 数据传输和流式响应 |
| 存储 | 文件系统 | 存储会话和版本数据 |

## 3. 整体架构

PageForge 采用前后端分离架构，通过 API 进行通信。后端基于 FastAPI 和 LangGraph 构建 AI 工作流，前端使用 React 构建交互式界面。

### 架构图

```
┌─────────────────────────────────────────────────────┐
│  React 19 + TypeScript + Vite 8 + Tailwind CSS v4   │
│  ┌──────────────┐  ┌──────────────────────────────┐ │
│  │  ChatPanel   │  │  PreviewPanel (iframe)       │ │
│  │  Think/Tool  │  │  预览 / 源码流式输出          │ │
│  │  Content     │  │  响应式尺寸切换              │ │
│  └──────┬───────┘  └──────────────┬───────────────┘ │
│         │ SSE (扁平事件模型)       │                  │
├─────────┼──────────────────────────┼──────────────────┤
│         │    FastAPI + LangGraph   │                  │
│  ┌──────┴──────────────────────────┴───────────────┐ │
│  │  intent → execute(ReAct) → validate → save      │ │
│  │  → respond                                      │ │
│  │  Skill 自动加载 + 双 LLM 配置                    │ │
│  └─────────────────────────────────────────────────┘ │
│  LangChain + OpenAI API                              │
└─────────────────────────────────────────────────────┘
```

## 4. 核心模块

### 4.1 后端模块

#### 4.1.1 配置模块 (`backend/app/config.py`)

负责管理项目配置，包括：
- 环境变量加载
- 目录路径定义
- LLM 客户端配置
- 会话和数据存储路径

**核心配置项：**
- `OPENAI_API_KEY`：OpenAI API 密钥
- `MODEL_NAME`：主要 LLM 模型名称（默认 gpt-4o）
- `INTENT_MODEL_NAME`：意图识别 LLM 模型名称（默认 gpt-4o-mini）
- 数据存储目录：`DATA_DIR`、`SESSIONS_DIR`
- 技能目录：`SKILLS_DIR`

#### 4.1.2 API 模块

**会话 API (`backend/app/api/sessions.py`)**：
- 创建新会话
- 获取会话版本列表
- 获取指定版本的 HTML 内容
- 切换基准版本
- 导出 HTML 文件

**消息 API (`backend/app/api/messages.py`)**：
- 处理用户消息
- 实现 SSE 流式响应
- 管理事件流（思考、工具调用、HTML 生成等）

#### 4.1.3 LangGraph 工作流

**工作流定义 (`backend/app/graph/graph.py`)**：
- 构建状态图，定义节点和边
- 实现从意图识别到响应的完整流程

**状态定义 (`backend/app/graph/state.py`)**：
- 定义 `AgentState` 类型，包含工作流中的所有数据
- 管理输入、中间状态和输出

**节点实现 (`backend/app/graph/nodes.py`)**：
- `intent_node`：意图理解，分析用户需求
- `execute_node`：ReAct 执行，生成/修改 HTML
- `validate_node`：质量检查，验证 HTML 结构和安全性
- `save_node`：保存版本，将 HTML 写入文件系统
- `respond_node`：生成回复，构建最终消息

**工具实现 (`backend/app/graph/tools.py`)**：
- `validate_html`：验证 HTML 结构和安全性
- 支持 Skill 工具的动态加载

#### 4.1.4 服务模块

**会话服务 (`backend/app/services/session_service.py`)**：
- 管理会话的创建、获取和保存
- 处理会话消息记录

**版本服务 (`backend/app/services/version_service.py`)**：
- 管理版本的保存、获取和查询
- 处理版本之间的关系

#### 4.1.5 技能系统

**技能加载器 (`backend/app/skills/loader.py`)**：
- 自动扫描 `skills/` 目录
- 解析 SKILL.md 文件
- 将技能转换为 LangChain 工具

### 4.2 前端模块

**主应用 (`frontend/src/App.tsx`)**：
- 组织整体布局
- 管理会话状态
- 处理用户交互

**组件**：
- `ChatPanel.tsx`：聊天面板，显示消息和思考内容
- `PreviewPanel.tsx`：预览面板，显示生成的 HTML
- `GenerationCard.tsx`：生成卡片，显示 HTML 代码
- `VersionSelector.tsx`：版本选择器，切换历史版本
- `ResizableLayout.tsx`：可调整大小的布局
- `MessageBubble.tsx`：消息气泡，显示用户和助手消息
- `BaseConfirmDialog.tsx`：确认对话框

**Hooks**：
- `useSSE.ts`：处理 SSE 事件流
- `useSession.ts`：管理会话状态

**服务**：
- `api.ts`：API 客户端，处理与后端的通信

## 5. 关键类与函数

### 5.1 后端关键类与函数

#### `build_graph()` (backend/app/graph/graph.py)
- **功能**：构建 PageForge LangGraph 工作流
- **参数**：无
- **返回值**：编译好的 StateGraph 实例
- **说明**：定义工作流节点和边，构建完整的 AI 工作流程

#### `AgentState` (backend/app/graph/state.py)
- **功能**：定义 LangGraph 工作流的状态结构（6 阶段 AI 应用生成器）
- **说明**：采用渐进式重构策略，新字段和旧字段共存，旧字段标记 `[DEPRECATED]`

**阶段快照类型（TypedDict）：**

| 类型 | 用途 |
| --- | --- |
| `RequirementSnapshot` | 需求阶段确认后的快照 |
| `DesignSnapshot` | 设计阶段确认后的快照 |
| `TechSnapshot` | 技术方案确认后的快照 |
| `FeatureSnapshot` | 功能选择确认后的快照 |
| `CodeSnapshot` | 代码生成完成后的快照 |
| `PhaseTransition` | 阶段转换记录 |

**核心新字段：**

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `current_phase` | `str` | 当前阶段: requirement/design/tech/feature/code/delivery/completed |
| `phase_status` | `str` | 阶段状态: running/waiting_human/completed |
| `requirement_snapshot` | `Optional[RequirementSnapshot]` | 需求快照 |
| `design_snapshot` | `Optional[DesignSnapshot]` | 设计快照 |
| `tech_snapshot` | `Optional[TechSnapshot]` | 技术快照 |
| `feature_snapshot` | `Optional[FeatureSnapshot]` | 功能快照 |
| `code_snapshot` | `Optional[CodeSnapshot]` | 代码快照 |
| `phase_history` | `List[PhaseTransition]` | 阶段转换记录 |
| `tech_spec` | `Optional[Dict]` | 综合技术方案 |
| `tech_approved` | `bool` | 技术方案是否已确认 |
| `project_mode` | `Optional[str]` | demo / full |
| `selected_features` | `Optional[List[str]]` | 选中的功能列表 |
| `design_projects` | `List[Dict]` | 4 套风格项目列表 |
| `selected_style_id` | `Optional[str]` | 选中的风格 ID |
| `delivery_approved` | `bool` | 交付是否已确认 |
| `human_input_pending` | `bool` | 是否等待用户输入 |

**各子图读写字段映射：**

| 子图 | 写入字段 | 读取字段 |
| --- | --- | --- |
| `RequirementSubgraph` | requirements_doc, requirements_approved, requirement_snapshot, phase_history | user_message |
| `DesignSubgraph` | design_projects, selected_style_id, selected_design, design_snapshot | requirements_doc |
| `TechSubgraph` | tech_spec, tech_approved, tech_snapshot, phase_history | requirements_doc |
| `FeatureSubgraph` | project_mode, selected_features, feature_snapshot, phase_history | — |
| `CodeSubgraph` | api_spec, mock_data, frontend_code, style_code, extracted_homepage | requirements_doc |
| `DeliverySubgraph` | delivery_approved, revision_feedback | api_spec, mock_data, frontend_code, style_code |

#### `intent_node()` (backend/app/graph/nodes.py)
- **功能**：意图理解节点，分析用户需求
- **参数**：`state`：AgentState
- **返回值**：包含任务列表的字典
- **说明**：使用轻量 LLM 分析用户消息，拆解为具体任务

#### `execute_node()` (backend/app/graph/nodes.py)
- **功能**：ReAct 执行节点，生成/修改 HTML
- **参数**：`state`：AgentState
- **返回值**：包含当前 HTML 的字典
- **说明**：执行 ReAct 循环，调用 LLM 和工具生成 HTML

#### `validate_node()` (backend/app/graph/nodes.py)
- **功能**：质量检查节点，验证 HTML 结构和安全性
- **参数**：`state`：AgentState
- **返回值**：包含验证错误的字典
- **说明**：检查 HTML 结构完整性和安全性

#### `save_node()` (backend/app/graph/nodes.py)
- **功能**：保存版本节点，将 HTML 写入文件系统
- **参数**：`state`：AgentState
- **返回值**：包含输出 HTML 和版本的字典
- **说明**：保存新版本并更新会话基准版本

#### `respond_node()` (backend/app/graph/nodes.py)
- **功能**：生成回复节点，构建最终消息
- **参数**：`state`：AgentState
- **返回值**：包含响应消息的字典
- **说明**：根据执行结果构建最终回复消息

#### `validate_html()` (backend/app/graph/tools.py)
- **功能**：验证 HTML 页面的结构和安全性
- **参数**：`html`：待验证的 HTML 内容
- **返回值**：包含验证结果的字典
- **说明**：检查 HTML 结构、viewport 标签和安全问题

#### `SkillAutoLoader` (backend/app/skills/loader.py)
- **功能**：自动扫描并加载所有 Skill
- **方法**：
  - `load_all()`：扫描目录，发现所有 Skill
  - `_parse_skill_md()`：解析 SKILL.md 的 YAML frontmatter
  - `_read_skill_content()`：读取 SKILL.md 的正文内容

#### `create_skill_tools()` (backend/app/skills/loader.py)
- **功能**：将所有 Skill 转换为 LangChain Tools
- **参数**：`skills_dir`：技能目录路径
- **返回值**：LangChain 工具列表
- **说明**：扫描技能目录，将每个技能转换为工具

### 5.2 前端关键类与函数

#### `useSSE` (frontend/src/hooks/useSSE.ts)
- **功能**：处理 SSE 事件流
- **参数**：`url`：SSE 端点 URL，`options`：配置选项
- **返回值**：事件状态和数据
- **说明**：管理 SSE 连接，处理事件流，更新 UI

#### `useSession` (frontend/src/hooks/useSession.ts)
- **功能**：管理会话状态
- **参数**：无
- **返回值**：会话状态和操作方法
- **说明**：处理会话的创建、获取和管理

#### `ChatPanel` (frontend/src/components/ChatPanel.tsx)
- **功能**：聊天面板组件
- **props**：`messages`：消息列表，`onSendMessage`：发送消息回调
- **说明**：显示聊天消息，处理用户输入

#### `PreviewPanel` (frontend/src/components/PreviewPanel.tsx)
- **功能**：预览面板组件
- **props**：`html`：HTML 内容，`version`：版本号
- **说明**：在 iframe 中预览生成的 HTML

## 6. 依赖关系

### 6.1 后端依赖

| 依赖 | 版本 | 用途 |
| --- | --- | --- |
| fastapi | ^0.104.1 | API 框架 |
| uvicorn | ^0.24.0 | ASGI 服务器 |
| langgraph | ^0.1.0 | AI 工作流管理 |
| langchain | ^0.1.0 | LLM 工具集成 |
| langchain-openai | ^0.1.0 | OpenAI API 集成 |
| python-dotenv | ^1.0.0 | 环境变量管理 |
| pyyaml | ^6.0 | YAML 解析（可选） |

### 6.2 前端依赖

| 依赖 | 版本 | 用途 |
| --- | --- | --- |
| react | ^19.0.0 | UI 框架 |
| react-dom | ^19.0.0 | DOM 操作 |
| typescript | ^5.0.0 | 类型安全 |
| vite | ^8.0.0 | 构建工具 |
| tailwindcss | ^4.0.0 | 样式管理 |
| @types/react | ^19.0.0 | React 类型定义 |
| @types/react-dom | ^19.0.0 | React DOM 类型定义 |

## 7. 项目运行方式

### 7.1 环境要求

- Python >= 3.13
- Node.js >= 18

### 7.2 后端启动

```bash
# 安装依赖
cd backend
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 OPENAI_API_KEY

# 启动服务器
uvicorn app.main:app --reload
```

### 7.3 前端启动

```bash
# 安装依赖
cd frontend
npm install

# 启动开发服务器
npm run dev
```

### 7.4 访问应用

打开 http://localhost:5173

## 8. API 接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/sessions` | 创建新会话 |
| `GET` | `/api/sessions/{id}/versions` | 获取版本列表 |
| `GET` | `/api/sessions/{id}/html?version=N` | 获取指定版本 HTML |
| `POST` | `/api/sessions/{id}/base-version` | 切换基准版本 |
| `GET` | `/api/sessions/{id}/export` | 导出 HTML 文件 |
| `POST` | `/api/sessions/{id}/messages` | 发送消息（SSE 流式响应） |
| `GET` | `/api/health` | 健康检查 |

## 9. 工作流程

### 9.1 AI 工作流

```
用户输入 → 意图识别(intent_llm) → ReAct 执行(llm + tools) → 质量检查 → 保存版本 → 回复
                                    ↑                              │
                                    └──── 有错误且修复<3次 ──────────┘
```

### 9.2 SSE 事件模型

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
| `done` | 消息结束 |

**前端渲染顺序**：Think（合并）→ Tool（按序）→ Content（text + generation 按序）

## 10. 版本管理

- 每次生成保存新版本（`v1`, `v2`, `v3`...）
- 支持切换基准版本（基于指定版本修改）
- 支持查看历史版本
- 支持导出下载 HTML 文件

## 11. 部署与配置

### 11.1 环境变量配置

`.env` 文件配置：

```env
OPENAI_API_KEY=sk-your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
INTENT_MODEL_NAME=gpt-4o-mini
MODEL_NAME=gpt-4o
```

### 11.2 目录结构

```
pageforge/
├── backend/            # 后端代码
│   ├── app/            # 应用代码
│   │   ├── api/        # API 路由
│   │   ├── graph/      # LangGraph 工作流
│   │   ├── models/     # 数据模型
│   │   ├── services/   # 业务服务
│   │   ├── skills/     # 技能系统
│   │   ├── tools/      # 工具
│   │   ├── config.py   # 配置
│   │   └── main.py     # 入口
│   └── pyproject.toml  # 依赖管理
├── frontend/           # 前端代码
│   ├── public/         # 静态资源
│   ├── src/            # 源代码
│   │   ├── components/ # UI 组件
│   │   ├── hooks/      # 自定义 hooks
│   │   ├── services/   # 服务
│   │   ├── App.tsx     # 主应用
│   │   └── main.tsx    # 入口
│   └── package.json    # 依赖管理
├── skills/             # Skill 定义目录
│   └── frontend-design/ # 前端设计技能
│       └── SKILL.md    # 技能定义
├── data/               # 运行时数据（gitignore）
└── README.md           # 项目说明
```

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

### 12.2 技能加载

- 后端启动时自动扫描 `skills/` 目录
- 解析每个技能的 `SKILL.md` 文件
- 将技能转换为 LangChain 工具
- 在 ReAct 循环中可供 LLM 使用

## 13. 开发指南

### 13.1 新增技能

1. 在 `skills/` 下新建目录
2. 创建 `SKILL.md`，包含 YAML frontmatter 和正文内容
3. 重启后端，自动生效

### 13.2 扩展功能

- **添加新工具**：在 `backend/app/graph/tools.py` 中添加新的工具函数
- **修改工作流**：在 `backend/app/graph/graph.py` 中调整节点和边
- **添加新 API**：在 `backend/app/api/` 中添加新的路由
- **扩展前端组件**：在 `frontend/src/components/` 中添加新组件

## 14. 安全注意事项

- 验证 HTML 内容，防止恶意代码注入
- 限制 LLM 模型的权限和能力
- 保护 API 密钥和环境变量
- 实现适当的错误处理和日志记录

## 15. 未来扩展方向

- 支持更多 LLM 模型
- 增加更多技能和工具
- 实现模板系统
- 支持团队协作和分享
- 添加更多验证和测试工具
- 优化性能和用户体验
