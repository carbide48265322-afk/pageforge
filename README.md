# PageForge

AI 驱动的单文件 HTML 页面生成器。通过自然语言对话，自动生成、修改、验证完整的 HTML 页面。

## 架构

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

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | React 19, TypeScript, Vite 8, Tailwind CSS v4 |
| 后端 | FastAPI, LangGraph, LangChain, OpenAI API |
| 存储 | 文件系统（JSON 元数据 + HTML 文件） |
| 通信 | REST API + SSE 流式响应 |

## 快速开始

### 环境要求

- Python >= 3.13
- Node.js >= 18

### 后端

```bash
cd backend

# 安装依赖（推荐 uv）
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 OPENAI_API_KEY
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
npm install
npm run dev
```

### 启动

```bash
# 后端（端口 8000）
cd backend && uvicorn app.main:app --reload

# 前端（端口 5173）
cd frontend && npm run dev
```

打开 http://localhost:5173

## AI 工作流

```
用户输入 → 意图识别(intent_llm) → ReAct 执行(llm + tools) → 质量检查 → 保存版本 → 回复
                                    ↑                              │
                                    └──── 有错误且修复<3次 ──────────┘
```

**5 个节点**：

| 节点 | 说明 |
|------|------|
| `intent` | 轻量 LLM 分析用户意图（create/modify/style/content） |
| `execute` | ReAct 循环：LLM 思考 → 调用工具 → 反馈结果 → 重复，最多 5 轮 |
| `validate` | 检查 HTML 结构完整性 + 安全扫描 |
| `save` | 保存 HTML 到文件系统，更新版本号 |
| `respond` | 生成最终回复消息 |

## SSE 事件模型

采用扁平事件模型（参考豆包），前端按 block 类型分组渲染：

| 事件 | 说明 |
|------|------|
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

## Skill 系统

自动扫描 `skills/` 目录，将每个 Skill 转为 LangChain Tool 并注入 system_prompt。

### 目录结构

```
skills/
└── frontend-design/
    └── SKILL.md
```

### 新增 Skill

1. 在 `skills/` 下新建目录
2. 创建 `SKILL.md`，包含 YAML frontmatter 和正文内容

```markdown
---
name: my-skill
description: Skill 描述，Agent 根据此描述决定是否调用
---

Skill 的详细指南内容...
```

3. 重启后端，自动生效

## 版本管理

- 每次生成保存新版本（`v1`, `v2`, `v3`...）
- 支持切换基准版本（基于指定版本修改）
- 支持查看历史版本
- 支持导出下载 HTML 文件

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/sessions` | 创建新会话 |
| `GET` | `/api/sessions/{id}/versions` | 获取版本列表 |
| `GET` | `/api/sessions/{id}/html?version=N` | 获取指定版本 HTML |
| `POST` | `/api/sessions/{id}/base-version` | 切换基准版本 |
| `GET` | `/api/sessions/{id}/export` | 导出 HTML 文件 |
| `POST` | `/api/sessions/{id}/messages` | 发送消息（SSE 流式响应） |
| `GET` | `/api/health` | 健康检查 |

## 项目结构

```
pageforge/
├── backend/
│   ├── app/
│   │   ├── config.py           # 配置（LLM、路径、环境变量）
│   │   ├── main.py             # FastAPI 入口
│   │   ├── api/
│   │   │   ├── sessions.py     # 会话/版本 API
│   │   │   └── messages.py     # SSE 流式消息
│   │   ├── graph/
│   │   │   ├── graph.py        # LangGraph 工作流
│   │   │   ├── state.py        # AgentState 定义
│   │   │   ├── nodes.py        # 5 个节点实现
│   │   │   ├── edges.py        # 条件路由
│   │   │   └── tools.py        # Agent 工具
│   │   ├── models/             # 数据模型
│   │   ├── services/           # 会话/版本服务
│   │   └── skills/
│   │       └── loader.py       # Skill 自动加载器
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # 主应用
│   │   ├── components/         # UI 组件
│   │   ├── hooks/              # useSSE, useSession
│   │   └── services/           # API 服务层
│   └── package.json
├── skills/                     # Skill 定义目录
│   └── frontend-design/
│       └── SKILL.md
└── data/                       # 运行时数据（gitignore）
```
