# PageForge

AI 驱动的全栈代码生成平台。通过自然语言对话，自动完成意图识别 → 思维链 → 计划生成 → 风格选择 → 代码构建的完整流水线，支持单文件 HTML 和 React+Vite 项目两种模式。

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│  React 19 + TypeScript + Vite + Tailwind CSS v4            │
│                                                              │
│  ┌──────────────────┐  ┌────────────────────────────────┐  │
│  │   ChatPanelV2    │  │      PreviewPanel              │  │
│  │  ┌────────────┐  │  │  ┌──────────┬──────────────┐  │  │
│  │  │ThinkingPanel│  │  │  │ 预览 iframe│ 源码查看     │  │  │
│  │  │PlanPanel    │  │  │  │ (html/url) │ FileTree     │  │  │
│  │  │ToolCard     │  │  │  │           │ CodeViewer   │  │  │
│  │  │StatusBar    │  │  │  └──────────┴──────────────┘  │  │
│  │  └────────────┘  │  │                                │  │
│  └────────┬──────────┘  └──────────────┬─────────────────┘  │
│           │ SSE v2 (事件分发器)         │                      │
│           │ SseEventDispatcher          │ WebContainer API     │
├───────────┼─────────────────────────────┼──────────────────────┤
│           │   FastAPI + LangGraph v2    │                      │
│  ┌────────┴────────────────────────────┴──────────────────┐   │
│  │  intent_router → thinking → plan                       │   │
│  │       ↓               ↓          ↓                    │   │
│  │   [chat→reply]   style_picker → code_gen → reply      │   │
│  │                                                      │   │
│  │  Skill 自动加载 / Tool 注册中心 / UI 风格动态生成      │   │
│  └──────────────────────────────────────────────────────┘   │
│  LangChain + OpenAI 兼容 API                                 │
└──────────────────────────────────────────────────────────────┘
```

## 技术栈

| 层     | 技术                                                       |
| ------ | ---------------------------------------------------------- |
| 前端   | React 19, TypeScript, Vite, Tailwind CSS v4, Monaco Editor |
| 后端   | Python 3.13+, FastAPI, LangGraph, LangChain (OpenAI 兼容)  |
| 存储   | 文件系统（JSON 元数据 + HTML/项目文件）                    |
| 通信   | REST API + SSE 流式响应（v2 事件分发器）                   |
| 运行时 | WebContainer（浏览器内 Node.js 环境，可选）                |

## 快速开始

### 环境要求

- Python >= 3.13
- Node.js >= 22
- [uv](https://docs.astral.sh/uv/)（推荐）或 pip
- pnpm（推荐）或 npm

### 后端

```bash
cd backend

# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API 密钥
```

`.env` 配置：

```env
OPENAI_API_KEY=sk-your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
INTENT_MODEL_NAME=gpt-4o-mini
MODEL_NAME=gpt-4o
```

### 前端

```bash
cd frontend
pnpm install
pnpm run dev
```

### 启动服务

```bash
# 后端（端口 9000）
cd backend && uv run uvicorn app.main:app --port 9000 --reload

# 前端（端口 6001）
cd frontend && pnpm run dev
```

打开 http://localhost:6001

## Graph v2 工作流

```
用户输入 → intent_router（意图识别）
                ↓
    ┌─────── chat/explain/debug ──→ reply（直接回复）
    │
    └─────── code_gen/code_edit ─→ thinking（思维链）
                                      ↓
                                   plan（制定步骤）
                                      ↓
                                style_picker（风格选择）
                                      ↓
                                  code_gen（代码生成）
                                      ↓
                                    reply → END
```

**6 个节点**：

| 节点            | 说明                                                        |
| --------------- | ----------------------------------------------------------- |
| `intent_router` | LLM 分类用户意图（7 类），推断推荐风格，推送 SSE 自定义事件 |
| `thinking`      | LLM 思维链输出，支持流式打字机效果                          |
| `plan`          | 将任务拆解为有序步骤，支持进度追踪                          |
| `style_picker`  | 调用 UI_UX CLI 获取风格配置 + 注入设计哲学，三层降级机制    |
| `code_gen`      | 多文件代码生成（React/Vite 项目或单文件 HTML）              |
| `reply`         | 构建最终回复消息                                            |

**条件边路由**：根据 `intent` 字段决定走向——chat 类直接回复，code_gen 类进入完整生成管线。

## 前端组件体系

| 组件          | 文件                           | 功能                                                   |
| ------------- | ------------------------------ | ------------------------------------------------------ |
| ChatPanelV2   | `components/ChatPanelV2.tsx`   | 主聊天面板，按 block 类型渲染不同子组件                |
| ThinkingPanel | `components/ThinkingPanel.tsx` | 思维链展示（流式打字 + Markdown 渲染 + 可折叠）        |
| PlanPanel     | `components/PlanPanel.tsx`     | 垂直时间线计划步骤（pending/active/done 三态）         |
| ToolCard      | `components/ToolCard.tsx`      | 工具调用卡片（running/success/error 三态 + 参数预览）  |
| StatusBar     | `components/StatusBar.tsx`     | 固定底部状态栏（项目类型 + WC 阶段 + Session ID）      |
| PreviewPanel  | `components/PreviewPanel.tsx`  | 预览面板（iframe 预览 + FileTree + CodeViewer 双 Tab） |
| CodeViewer    | `components/CodeViewer.tsx`    | 基于 Monaco Editor 的代码查看器（懒加载 ~3MB）         |
| FileTree      | `components/FileTree.tsx`      | 项目文件树（文件夹展开/折叠 + 语言图标）               |

## SSE 事件分发器（v2）

前端采用三层事件处理架构：

```
useSSEv2 (状态聚合 Hook)
    ↓
SseEventDispatcher（核心分发器：双模式连接 + 自动重连 + HANDLER_MAP 注册表）
    ↓
7 个 Handler（thinking / plan / toolCall / fileEvent / status / intent / style）
```

**核心事件类型**：

| 事件类别 | 事件名                            | 处理器           | 渲染组件                 |
| -------- | --------------------------------- | ---------------- | ------------------------ |
| 思维链   | `thinking_start/delta/end`        | thinkingHandler  | ThinkingPanel            |
| 计划     | `plan_start/update/done`          | planHandler      | PlanPanel                |
| 工具调用 | `tool_call:start/end`             | toolCallHandler  | ToolCard                 |
| 文件操作 | `file_created/update/delete`      | fileEventHandler | FileTree 更新            |
| 状态     | `status:*`（6 种）                | statusHandler    | StatusBar + WebContainer |
| 意图     | `intent:start/result/style_query` | intentHandler    | 意图面板                 |
| 风格     | `style_selected`                  | styleHandler     | 风格标签                 |

## 错误处理

7 类错误统一管理（`services/error/`）：

- **网络错误**：指数退避自动重连（SSE 断线恢复）
- **解析错误**：降级渲染（JSON 解析失败显示原文）
- **LLM 错误**：内联 ErrorCard + Toast 双通道提示
- **超时保护**：WebContainer 30s 启动超时、CLI 15s 查询超时
- **全局兜底**：GlobalErrorBoundary 防止白屏

## Skill 系统

自动扫描 `skills/` 目录，将 Skill 转为 LangChain Tool 或设计哲学注入。

### 已集成 Skills

| Skill                     | 用途                                          |
| ------------------------- | --------------------------------------------- |
| `frontend-design`         | 设计哲学约束（注入 Code Gen Prompt）          |
| `UI_UX`                   | 50+ 风格数据库 + CLI 查询引擎（动态风格生成） |
| `react-code-generation`   | React 代码生成指南                            |
| `react-component-library` | 组件库使用规范                                |
| `style-templates`         | HTML 风格模板库                               |

### 新增 Skill

1. 在 `skills/` 下新建目录
2. 创建 `SKILL.md`（YAML frontmatter + 正文）
3. 重启后端自动生效

## 版本管理

- 每次生成保存新版本（`v1`, `v2`, `v3`...）
- 支持 HTML 和 Project 两种版本类型
- 支持切换基准版本（基于指定版本修改）
- 支持导出下载

## API

| 方法   | 路径                                          | 说明                     |
| ------ | --------------------------------------------- | ------------------------ |
| `POST` | `/api/sessions`                               | 创建新会话               |
| `GET`  | `/api/sessions/{id}/versions`                 | 获取版本列表             |
| `GET`  | `/api/sessions/{id}/html?version=N`           | 获取指定版本 HTML/项目   |
| `POST` | `/api/sessions/{id}/base-version`             | 切换基准版本             |
| `GET`  | `/api/sessions/{id}/export`                   | 导出文件                 |
| `POST` | `/api/sessions/{id}/messages`                 | 发送消息（SSE 流式响应） |
| `GET`  | `/api/projects/{session_id}/files`            | 获取项目文件树           |
| `GET`  | `/api/projects/{session_id}/content?path=...` | 获取文件内容             |
| `POST` | `/api/webcontainer/start`                     | 启动 WebContainer        |
| `GET`  | `/api/health`                                 | 健康检查                 |

## 项目结构

```
pageforge/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI 入口（CORS + 路由注册）
│   │   ├── config.py                # LLM 配置、路径常量
│   │   ├── api/
│   │   │   ├── sessions.py          # 会话/版本 CRUD
│   │   │   ├── messages.py          # SSE 流式消息端点（v1+v2 事件桥接）
│   │   │   ├── projects.py          # 项目文件树/内容 API
│   │   │   ├── templates.py         # 模板 API
│   │   │   └── webcontainer.py      # WebContainer 管理
│   │   ├── graph/
│   │   │   ├── graph_v2.py          # LangGraph v2 图定义 + 条件边路由
│   │   │   ├── state.py             # AgentState TypedDict
│   │   │   └── nodes/               # 6 个独立节点模块
│   │   │       ├── intent_router.py # LLM 意图分类 + 风格推断
│   │   │       ├── thinking.py      # 思维链节点
│   │   │       ├── plan.py          # 步骤规划节点
│   │   │       ├── style_picker.py  # UI 风格选择（CLI + 降级）
│   │   │       ├── code_gen.py      # 代码生成节点
│   │   │       └── reply.py         # 回复生成节点
│   │   ├── core/                    # 注册中心（Tool/Skill）
│   │   ├── models/                  # 数据模型
│   │   ├── services/                # 会话/版本/WebContainer 服务
│   │   ├── tools/                   # 系统 Tool 定义
│   │   └── skills/                  # Skill 加载器
│   └── pyproject.toml
├── frontend/
│   └── src/
│       ├── App.tsx                  # 主应用（路由 + 数据流编排）
│       ├── components/              # UI 组件（11 个）
│       ├── hooks/                   # useSSEv2 / useSession / useWebContainer
│       ├── services/
│       │   ├── sse/                 # SSE 事件分发器（11 个文件）
│       │   ├── error/               # 错误处理模块（6 个文件）
│       │   ├── api.ts               # REST API 客户端
│       │   ├── webcontainer.ts      # WebContainer 封装
│       │   └── webcontainer_api.ts  # WebContainer API 类型
│       └── index.css                # 全局样式
├── skills/                          # Skill 定义目录（5 个）
│   ├── frontend-design/
│   ├── UI_UX/                       # 风格数据 + CLI 查询引擎
│   ├── react-code-generation/
│   ├── react-component-library/
│   └── style-templates/
├── data/                            # 运行时会话数据（gitignore）
├── tests/                           # 单元测试
├── Dockerfile
└── docker-compose.yml
```

## 开发分支策略

| 分支                             | 用途                    |
| -------------------------------- | ----------------------- |
| `main`                           | 稳定发布分支            |
| `feature/streaming-optimization` | Phase 1 新功能开发      |
| `cleanup/legacy-removal`         | 旧架构清理基线          |
| `feature/v2-node-implementation` | v2 节点实现（当前开发） |
