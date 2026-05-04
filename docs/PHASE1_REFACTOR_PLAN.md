# PageForge Phase 1 改造计划

> **改造项目，非新项目** — 现有代码有 457 行的 `useSSE.ts`、220 行的 `messages.py` SSE 翻译层、渗透全项目的 `latestHtml` 状态。
> 核心原则：**不改旧文件，新建来代替；旧逻辑保留，新逻辑并存；字段加 Optional，数据库兼容。**

---

## 1. 改造目标

### 现状
- 后端输出**单个 HTML 文件**（`output_html: str`）
- 前端通过 `latestHtml` / `streamingHtml` 两个状态渗透全项目
- `useSSE.ts`（457 行）有复杂的双背压缓冲，绑定旧版 4 类 `RenderBlock`
- `messages.py`（220 行）有复杂的 HTML 检测逻辑（`expecting_html` / `in_html_mode` / `html_prefix_buffer`）
- Agent 工作流**黑盒化**，用户只能看到最终结果
- UI 样式**硬编码在模板中**，无法定制

### 目标（Phase 1）
- 后端输出**多文件项目结构**（React + Vite + TS + Tailwind + shadcn/ui）
- 前端**对话 + 展示区双面板**，支持预览/代码切换
- Agent 全工作流**可视化**：意图识别 → 思考 → 计划 → 执行 → 预览就绪
- UI 风格通过 **Skill 可配置**（极简 / 活泼 / 暗色 / 玻璃态）

---

## 2. 固定技术栈

| 层 | 选择 | 说明 |
|----|------|------|
| 框架 | React 18 + Vite | 已有技术栈 |
| 语言 | TypeScript | 类型安全 |
| 样式 | Tailwind CSS v4 | 原子化 CSS |
| 组件库 | shadcn/ui | 高质量、可复制粘贴 |
| 构建工具 | Vite | 快速 HMR |
| 包管理 | pnpm | WebContainer 原生支持 |

> 不做技术栈选择器。参考 meoo，固定一套打磨到极致。

---

## 3. 后端改造

### 3.1 新增 API 接口

#### Files 接口 — 返回文件树结构

```
GET /api/projects/{session_id}/files
```

响应：
```json
{
  "project_id": "sess_abc123",
  "files": [
    {
      "type": "folder",
      "name": "frontend",
      "path": "frontend",
      "children": [
        {"type": "folder", "name": "src", "path": "frontend/src", "children": [
          {"type": "file", "name": "App.tsx", "path": "frontend/src/App.tsx", "language": "typescript"},
          {"type": "file", "name": "main.tsx", "path": "frontend/src/main.tsx", "language": "typescript"}
        ]},
        {"type": "file", "name": "package.json", "path": "frontend/package.json", "language": "json"}
      ]
    }
  ]
}
```

#### Content 接口 — 返回指定文件内容

```
GET /api/projects/{session_id}/content?path=frontend/src/App.tsx
```

响应：
```json
{
  "project_id": "sess_abc123",
  "path": "frontend/src/App.tsx",
  "content": "import React from 'react';...",
  "language": "typescript",
  "size_bytes": 428
}
```

### 3.2 Agent 输出改造

**现状**：`AgentState` 只有 `output_html: str`，Agent 最终输出单 HTML 字符串。

**Phase 1**：Agent 输出多文件 JSON 结构，同时**保留旧字段**（兼容老 session 数据）。

```python
# backend/app/graph/state.py — 改造后
from typing import TypedDict, Optional, List

class AgentState(TypedDict):
    # ---- 旧字段（保留，不能删！老 session 数据还在 SQLite 里） ----
    user_message: str
    session_id: str
    base_html: str            # 旧：当前基准 HTML
    
    task_list: list[dict]
    current_html: str         # 旧：中间生成的 HTML
    validation_errors: list[str]
    iteration_count: int
    fix_count: int
    
    response_message: str
    output_html: Optional[str]   # 旧：最终 HTML（新项目可为 None）
    output_version: int
    is_complete: bool

    # ---- 新字段（全部 Optional，兼容旧数据） ----
    project_type: Optional[str]           # "react-vite-app"
    files: Optional[List[Dict]]         # 新：多文件列表
    project_id: Optional[str]           # WebContainer 项目 ID
    install_status: Optional[str]       # installing / done / failed
    dev_server_url: Optional[str]       # 预览 URL
    ui_style: Optional[str]             # minimal / vibrant / dark / glassmorphism
```

**关键**：所有读取新字段的地方用 `.get()` 或 `or` 兜底：
```python
files = state.get("files") or []
project_id = state.get("project_id")
```

### 3.3 LangGraph 节点编排

**现状**：`graph.py` 有 `execute` 节点输出 HTML。

**改造陷阱**：直接在旧图上加节点，老 session 恢复会失败（状态 schema 变了）。

**对策**：新建 `graph_v2.py`，旧图保留。

```
用户输入
   │
   ▼
┌─────────────┐
│ Intent Router│ ──── intent:start / intent:result ──→ SSE
│ (意图识别)    │     chat → 直接回复结束
└──────┬──────┘     code_gen → 继续
       │
       ▼
┌─────────────┐
│ Think Node  │ ──── thinking_start/delta/end ──→ SSE
│ (思维链)     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Plan Node   │ ──── plan_start/update/done ──→ SSE
│ (制定计划)    │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Style Picker     │ ──── style_query(可选) / style_selected ──→ SSE
│ (设计风格选择)    │     自动推断 or 用户选择 → 加载对应 UI Skill
└──────┬───────────┘
       │
       ▼
┌─────────────┐
│ Code Gen    │ ──── tool_call:start/update/end ──→ SSE
│ (代码生成)    │     file_created/file_updated ──→ SSE
│              │     status:init/installing/install_done/generation_done ──→ SSE
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Reply Node  │ ──── text_start/delta/end ──→ SSE
│ (文本回复)    │
└─────────────┘
```

### 3.4 SSE 翻译层注意事项（messages.py 雷区）

**现状**：`messages.py` 有 220 行复杂逻辑，负责把 LangGraph 底层事件翻译成自定义 SSE 事件：

```python
# backend/app/api/messages.py 现有逻辑
expecting_html = False    # generate_html 工具调用后置 True
in_html_mode = False      # 检测到 ```html 或 <!DOCTYPE 后置 True
html_prefix_buffer = ""   # 跨 chunk 缓冲，防止碎片渲染
```

**改造陷阱**：这个翻译层与 HTML 检测逻辑**高度耦合**。新事件（如 `intent:result`、`plan_update`）不能直接加在旧逻辑里，否则一改就炸 HTML 路径。

**对策**：新事件用 `continue` 跳过旧逻辑：

```python
# messages.py — 新增事件分支，不动 HTML 逻辑
async for event in pageforge_graph.astream_events(...):
    kind = event["event"]
    
    # ---- 新增：意图识别事件 ----
    if kind == "on_intent_recognized":
        yield f"event: INTENT_RESULT\ndata: {json.dumps(...)}\n\n"
        continue  # ← 关键：跳过旧逻辑
    
    # ---- 新增：计划事件 ----
    if kind == "on_plan_update":
        yield f"event: PLAN_UPDATE\ndata: {json.dumps(...)}\n\n"
        continue
    
    # ---- 原有 HTML 翻译逻辑（不动）----
    if kind == "on_chat_model_stream" and node == "execute":
        # ... 220 行旧逻辑保持不变
```

**版本路由**：在 `messages.py` 里根据项目类型选择图：

```python
# messages.py send_message 函数
@router.post("/{session_id}/messages")
async def send_message(session_id: str, req: MessageRequest):
    session = session_service.get_session(session_id)
    # ...
    
    # 根据项目类型选择图（新项目用 v2，旧项目用 v1）
    is_new_project = session.project_type == "react-vite-app"
    
    if is_new_project:
        from app.graph.graph_v2 import pageforge_graph_v2
        async for event in pageforge_graph_v2.astream_events(...):
            # 新事件处理
            ...
    else:
        async for event in pageforge_graph.astream_events(...):
            # 旧事件处理（现有逻辑）
            ...
```

### 3.5 版本接口兼容（VersionService）

**现状**：`loadHtml(version)` 返回 HTML 字符串，版本切换后直接渲染。

**改造陷阱**：新版本是多文件项目，接口要同时支持两种返回格式。

**对策**：改版本接口返回结构，加 `type` 字段区分：

```python
# GET /api/versions/{version_id}
# 旧版本返回
{
  "type": "html",
  "html": "<!DOCTYPE html>...",
  "version": 1
}

# 新版本返回
{
  "type": "project",
  "project_id": "sess_abc123",
  "files": [...],
  "preview_url": "http://localhost:3000",
  "version": 2
}
```

前端根据 `type` 字段决定渲染路径，不做破坏性删除。

---

## 4. 完整 SSE 事件规范

### 4.1 事件分类总览

| # | 阶段 | 事件名 | 说明 | 前端行为 |
|---|------|--------|------|---------|
| 1 | **意图识别** | `intent:start` | 开始识别 | 显示"分析中..." |
| | | `intent:result` | 识别结果 `{intent, confidence, tags, mode}` | 切换布局模式 |
| | | `intent:style_query` | 征询风格偏好（可选） | 展示风格选项卡 |
| | | `intent:style_selected` | 风格已确认 | 加载对应 Skill |
| 2 | **思维链** | `thinking_start` | 开始思考 | 展开思考区域 |
| | | `thinking_delta` | 思考片段 `{content}` | 流式追加（可折叠） |
| | | `thinking_end` | 思考完成 `{summary}` | 收起，保留摘要 |
| 3 | **计划** | `plan_start` | 开始制定计划 | 展示计划面板 |
| | | `plan_update` | 计划更新 `{steps, current}` | 渲染步骤列表+高亮当前 |
| | | `plan_done` | 计划完成 `{steps}` | 锁定最终计划 |
| 4 | **文本回复** | `text_start` | 开始回复 | 创建消息气泡 |
| | | `text_delta` | 文本片段 `{content}` | 流式打字机效果 |
| | | `text_end` | 回复完成 | 消息气泡完成态 |
| 5 | **工具调用** | `tool_call:start` | 开始调用 `{id, name, input}` | 显示工具卡片 |
| | | `tool_call:end` | 调用完成 `{id, status, duration_ms}` | 卡片显示结果状态 |
| 6 | **文件事件** | `file_created` | 文件创建 `{path, language}` | 刷新文件树 + 写入 WebContainer |
| | | `file_updated` | 文件更新 `{path}` | 更新文件树 + WebContainer |
| | | `file_deleted` | 文件删除 `{path}` | 移除文件树节点 |
| 7 | **宏观状态机** | `status:init` | 项目初始化 `{project_id, has_package_json}` | 触发 GET/files + pnpm install 并行 |
| | | `status:installing` | 安装依赖中 `{progress}` | 进度条"安装依赖..." |
| | | `status:install_done` | 依赖安装完成 `{duration_ms}` | 标记完成 |
| | | `status:generation_done` | 文件生成完毕 `{total_files}` | 标记完成，检查可否启动 dev |
| | | `status:starting_dev` | 启动开发服务 `{command}` | 执行 pnpm run dev |
| | | `status:preview_ready` | 预览就绪 `{url}` | 切换到预览标签页 |
| 8 | **错误** | `error` | 错误发生 `{code, message, recoverable, step}` | 错误提示 + 重试按钮 |

### 4.2 完整事件流示例

```
用户: "帮我做一个Todo应用"

1.  intent:start
2.  intent:result {intent:"code_gen", tags:["react","todo"], mode:"fullstack"}
3.  intent:style_query {options:[minimal,vibrant,dark], auto_select:"minimal"}
     → 用户不选，5秒后自动走 minimal
4.  intent:style_selected {style:"minimal"}

5.  thinking_start
6.  thinking_delta "用户需要一个Todo应用..."
7.  thinking_delta "应该包含增删改查功能..."
8.  thinking_end {summary:"规划Todo应用的全栈实现"}

9.  plan_start
10. plan_update {steps:["生成项目结构","编写App组件","编写TodoList组件","添加样式","启动预览"], current:1}
11. plan_done

12. text_start
13. text_delta "好的，我来帮你"
14. text_delta "生成一个极简风格的 Todo 应用"
15. text_end

16. tool_call:start {name:"react-vite-scaffold"}
17. tool_call:end {status:"success"}

18. status:init {project_id:"sess_001", has_package_json:true}
     → 前端并行执行: GET /files + pnpm install

19. file_created {path:"package.json"}        → 文件树新增节点
20. file_created {path:"vite.config.ts"}       → 文件树新增节点
21. file_created {path:"src/main.tsx"}         → 文件树新增节点
22. file_created {path:"src/App.tsx"}          → 文件树新增节点
23. file_created {path:"src/TodoList.tsx"}     → 文件树新增节点
24. file_created {path:"src/index.css"}        → 文件树新增节点

25. status:installing {progress:0.5}           → 进度条
26. status:install_done {duration_ms:3200}

27. tool_call:start {name:"ui-polish-minimal"}
28. tool_call:end {status:"success"}

29. status:generation_done {total_files:6}      → 所有文件生成完毕

30. status:starting_dev {command:"pnpm run dev"}
31. status:preview_ready {url:"http://localhost:3000"} → 自动切到预览标签
```

---

## 5. 前端改造

### 5.1 整体布局

```
┌──────────────────────────────────────────────────────────┐
│                      PageForge                            │
├────────────────┬─────────────────────────────────────────┤
│                │  [ 🖥 预览 ]  [ 📝 代码 ]                │  ← 标签栏
│    对话区       │━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│    Chat Panel  │                                           │
│                │         预览内容 (iframe)                  │
│  ┌──────────┐  │         或                                 │
│  │          │  │  ┌──────────┬──────────────────────────┐  │
│  │  消息流   │  │  │  文件树   │     代码 (Monaco Editor)  │  │
│  │          │  │  │ FileTree │                           │  │
│  │ (含思考/  │  │  │          │                           │  │
│  │  计划/   │  │  │ 📁 src   │                           │  │
│  │  工具卡/  │  │  │  ├ App   │                           │  │
│  │  文件通知) │  │  │  └ Comp  │                           │  │
│  ├──────────┤  │  └──────────┴──────────────────────────┘  │
│  │  输入框   │  │                                           │
│  └──────────┘  │                                           │
├────────────────┴─────────────────────────────────────────┤
│  状态栏: ✅ 已生成 6 个文件  ·  🔧 pnpm run dev 运行中     │
└──────────────────────────────────────────────────────────┘
```

### 5.2 布局规则

| 条件 | 行为 |
|------|------|
| `intent=chat` | 右侧隐藏，对话区占满宽度 |
| `intent=code_gen` / `code_edit` / `explain` | 右侧自动展开 |
| 预览 Tab 激活 | iframe 占满右侧，FileTree **隐藏** |
| 代码 Tab 激活 | 左侧 FileTree + 右侧 Monaco Editor |

### 5.3 组件改造清单（含陷阱说明）

| 组件 | 类型 | 说明 | 改造陷阱 |
|------|------|------|----------|
| `TabBar` | 新增 | 预览/代码切换标签栏 | - |
| `FileTree` | 新增 | 文件树组件（支持文件夹展开/折叠） | - |
| `CodeViewer` | 新增 | 基于 Monaco Editor 的代码查看器（只读） | Monaco 3MB，需懒加载（切到代码 Tab 时才加载） |
| `ThinkingPanel` | 新增 | 思维链展示区域（可折叠） | - |
| `PlanPanel` | 新增 | 计划步骤列表（带进度高亮） | - |
| `ToolCard` | 新增 | 工具调用卡片（名称+参数+状态） | - |
| `StatusBar` | 新增 | 底部状态栏（文件数/服务状态） | - |
| `ChatPanel` | 改造 | 消息类型扩展（支持思考/计划/工具/文件通知） | 注意 `RenderBlock` 类型目前只有 4 种，新事件需新建 `useSSEv2` |
| `ResizableLayout` | 改造 | 支持右侧面板显隐切换 + 组件类型切换 | 右侧需支持三种内部分支：html 预览 / url 预览 / 代码模式 |
| `WebContainerPanel` | **改名** → `HtmlPreviewPanel` | 现状是 iframe srcDoc（没用 WebContainer API） | **命名欺诈**：真正用 WebContainer API 的是 `WebContainerDemo.tsx`，别改错了 |
| `PreviewPanel` | 新增 | 包含 TabBar + FileTree + CodeViewer + WebContainer URL 预览 | - |
| `useSSE.ts` | **不改，新建 `useSSEv2.ts`** | 457 行高度耦合，双背压缓冲 | **重灾区**：`RenderBlock` 类型只有 4 种，直接改会破坏 `ChatPanel` 渲染逻辑。新建 v2，过渡期并存 |
| `latestHtml` / `streamingHtml` | 改造 | 这两个状态渗透全项目 | 改成 `PreviewSource` 联合类型：`{mode:'html',html:string} \| {mode:'url',url:string} \| {mode:'none'}` |

### 5.4 `latestHtml` 渗透问题详解

**现状**：`latestHtml` / `streamingHtml` 被传到：
- `App.tsx` → `previewHtml` state
- `App.tsx` → `WebContainerPanel` 的 `html` prop
- `useSSE.ts` 内部状态（双背压缓冲）
- `ChatPanel` 可能用于展示"正在生成 HTML"

**改造策略**：不要全局替换，给预览源加类型：

```typescript
// 新增类型（types/index.ts 或 hooks/useSSEv2.ts）
export type PreviewSource =
  | { mode: 'html'; html: string }
  | { mode: 'url'; url: string }
  | { mode: 'none' };

// App.tsx
const [previewSource, setPreviewSource] = useState<PreviewSource>({ mode: 'none' });

// 根据项目类型初始化
useEffect(() => {
  if (isNewProject) {
    // 新项目：等待 status:preview_ready 事件设置 url
    setPreviewSource({ mode: 'none' });
  } else {
    // 旧项目：兼容现有逻辑
    setPreviewSource({ mode: 'html', html: latestHtml });
  }
}, [isNewProject]);
```

### 5.5 WebContainer 三阶段无感启动模型

```
阶段1: 项目初始化
  触发条件: 收到 status:init 且 has_package_json=true
  动作:
    - WebContainer.spawn() 创建实例
    - GET /files 拿到完整文件树
    - 将已有文件写入 WebContainer FS
    - 同时启动 pnpm install（与后续文件生成并行）

阶段2: 等待剩余文件（持续接收）
  触发条件: 收到 file_created / file_updated
  动作:
    - GET /content?path=xxx 获取内容
    - 写入 WebContainer FS
    - 刷新 FileTree 节点
    - 循环直到收到 status:generation_done

阶段3: 启动预览
  触发条件: 收到 status:generation_done
  动作:
    - 检查 pnpm install 是否完成（等待如未完成）
    - 执行 pnpm run dev
    - 等待 dev server ready
    - 发送 status:preview_ready
    - iframe 加载 previewUrl
```

**关键优化**: pnpm install 在阶段 1 就开始执行，与文件生成**完全并行**，节省约 40% 等待时间。

---

## 6. UI 风格动态生成系统

### 6.1 设计理念

> 技术栈固定，UI 风格可变。通过调用 `ui-ux-pro-max` 和 `frontend-design` 两个 Skill 动态生成风格配置，约束 LLM 生成的样式代码。

**核心思路**：
- 不预定义静态风格文件，避免重复造轮子和难以维护
- 当需要风格设计时，调用 `ui-ux-pro-max` 查询风格数据（colors、typography、anti-patterns）
- 同时注入 `frontend-design` 的设计哲学（避免 AI 平庸审美、不要 Inter、不要紫渐变）
- 有约束条件时生成符合约束的风格配置，无约束时随机生成合适的风格

### 6.2 风格数据来源

#### ui-ux-pro-max Skill
位置：`skills/UI_UX/`
- 包含 50+ 风格数据（minimal / vibrant / dark / glassmorphism 等）
- 支持 `--design-system` 参数，一次性输出完整 design tokens
- 支持按关键词搜索（如 "minimal"、"dark mode"、"glassmorphism"）
- CLI 调用示例：
  ```bash
  python3 skills/UI_UX/scripts/search.py "minimal" --design-system
  python3 skills/UI_UX/scripts/search.py "dark mode dashboard" --design-system
  ```

#### frontend-design Skill
位置：`skills/frontend-design/`
- 提供设计哲学和反模式约束
- 核心规则：不要 Inter/Roboto 等通用字体，不要用紫渐变，不要 cookie-cutter 设计
- 强调独特的美学方向（brutally minimal, maximalist chaos, retro-futuristic 等）

### 6.3 Style Picker 节点工作流程

```
用户输入
   │
   ▼
Intent Router（识别意图 + 提取风格线索）
   │
   ├─ 有风格线索（如"暗色系"、"极简"）
   │   → 调用 ui-ux-pro-max: search.py "<线索>" --design-system
   │   → 注入 frontend-design 设计哲学
   │   → 生成符合约束的风格配置
   │
   ├─ 无明确线索但可推断（根据项目类型）
   │   → 如：管理后台 → minimal；作品集 → glassmorphism
   │   → 调用 ui-ux-pro-max 获取对应风格数据
   │
   └─ 无线索且无法推断
       → 随机选择合适的风格
       → 或走默认 minimal
       → 可选：发 `intent:style_query` 让用户选择（5秒超时）
```

### 6.4 风格配置注入格式

风格配置最终以结构化文本形式注入后续代码生成节点的 Prompt：

```
## UI 风格配置
- 主色调：<primary_color>
- 背景色：<background_color>
- 字体：<font_family>
- 圆角：<border_radius>
- 阴影：<shadow_style>
- 动效：<animation_rules>
- 反模式（不要做）：<anti_patterns>
- 设计哲学：<frontend-design 核心规则>
```

### 6.5 风格选择的触发策略

| 策略 | 触发条件 | 示例 |
|------|---------|------|
| **自动推断** | 用户描述中隐含风格线索 | "暗色系的个人主页" → 调用 ui-ux-pro-max 获取 dark 风格 |
| **项目类型推断** | 根据项目类型自动选择 | 管理后台 → minimal；创意类 → glassmorphism |
| **默认兜底** | 无法推断时 | 默认 minimal |
| **SSE 征询（可选）** | 多种风格都匹配时 | 发 `intent:style_query`，前端渲染选项卡让用户选（5秒超时不选则走默认） |

---

## 7. 意图识别体系

### 7.1 意图分类

```typescript
type Intent =
  | "chat"             // 纯对话
  | "code_gen"         // 一句话生成应用
  | "code_edit"        // 修改已有代码
  | "explain"          // 解释代码/概念
  | "debug"            // 调试问题
  | "file_operation"   // 文件操作
  | "unknown";
```

### 7.2 意图 → 布局映射

| 意图 | 对话区 | 右侧面板 | 默认 Tab |
|------|--------|---------|----------|
| `chat` | 全宽 | **隐藏** | - |
| `code_gen` | ~40% | **可见** | 预览 |
| `code_edit` | ~40% | **可见** | 代码 |
| `explain` | ~40% | **可见** | 代码 |
| `debug` | ~40% | **可见** | 预览 |
| `file_operation` | ~40% | **可见** | 代码 |

### 7.3 IntentResult 数据结构

```typescript
interface IntentResult {
  intent: Intent;
  confidence: number;       // 0~1
  tags: string[];           // 技术标签 ["react", "todo", "crud"]
  mode?: "frontend" | "backend" | "fullstack";
  complexity?: "simple" | "medium" | "complex";
  suggested_style?: string; // 建议的设计风格关键词（传递给 ui-ux-pro-max 查询，如 "minimal", "dark", "glassmorphism"）
}
```

---

## 8. P1 体验增强详细设计

> P0 完成了核心能力（SSE、文件树、预览面板、WebContainer），P1 负责让 Agent 工作流**可视化**——用户能看到 Agent 在思考什么、计划做什么、用了哪些工具。
> P1 分为三块：前端展示组件（13~16）、后端 Agent 节点（17~19）、前端基础设施（20~21）。

### 8.1 ThinkingPanel — 思维链展示组件（P1.13）

#### 功能定位

接收 SSE 的 `thinking_start` / `thinking_delta` / `thinking_end` 事件，以可折叠卡片的形式展示 Agent 的思考过程。

**为什么需要这个组件？**
- 用户需要知道 Agent 不是在「卡死」，而是在「深度思考」
- 透明化推理过程，增强信任感
- `thinking_end` 带有摘要，折叠后只显示摘要，不占空间

#### 数据流

```
useSSEv2 返回的 thinkingBlocks 数组
   │
   ▼
ChatPanelV2 遍历 blocks
   │  type === 'thinking'
   ▼
渲染 <ThinkingPanel block={block} />
```

#### 类型定义

```typescript
// useSSEv2.ts 中定义
interface ThinkingBlock {
  type: 'thinking';
  id: string;
  status: 'streaming' | 'complete';
  content: string;           // thinking_delta 累积的内容
  summary?: string;          // thinking_end 时填入的摘要
  startedAt: number;         // thinking_start 时间戳
  completedAt?: number;      // thinking_end 时间戳
}
```

#### 组件接口

```tsx
interface ThinkingPanelProps {
  block: ThinkingBlock;
}

export function ThinkingPanel({ block }: ThinkingPanelProps) {
  const [expanded, setExpanded] = useState(true);

  return (
    <div className="thinking-panel">
      {/* 头部：图标 + "正在思考" / "思考完成" + 折叠按钮 */}
      <header onClick={() => setExpanded(!expanded)}>
        <BrainIcon />
        <span>{block.status === 'streaming' ? '正在思考...' : '思考完成'}</span>
        {block.summary && !expanded && (
          <span className="summary">{block.summary}</span>
        )}
        <ChevronIcon expanded={expanded} />
      </header>

      {/* 内容区：流式追加 or 已完成的完整内容 */}
      {expanded && (
        <div className="content">
          {block.status === 'streaming' ? (
            <Typewriter text={block.content} />  /* 流式打字效果 */
          ) : (
            <MarkdownRenderer content={block.content} />
          )}
        </div>
      )}
    </div>
  );
}
```

#### 视觉规范

| 元素 | 样式 | 说明 |
|------|------|------|
| 外层容器 | `border-l-2 border-blue-400 bg-blue-50/50 rounded-r-lg p-4` | 左侧蓝色竖线表示「思考中」，与普通消息区分 |
| 头部 | `flex items-center gap-2 text-sm text-blue-700 font-medium cursor-pointer` | 可点击展开/收起 |
| 图标 | `<Brain size={16} />` from lucide-react | 统一使用 lucide 图标 |
| 内容区 | `text-sm text-slate-600 leading-relaxed mt-2 pl-2 border-l border-blue-200` | 缩进 + 次级竖线，视觉层级 |
| 流式光标 | 闪烁的光标动画 `animate-pulse \|` | 表示还在输出 |
| 折叠态摘要 | `text-xs text-slate-500 italic` | 只显示 summary 字段 |

#### 交互行为

| 行为 | 触发条件 | 效果 |
|------|---------|------|
| 自动展开 | 收到 `thinking_start` | 默认展开，显示流式内容 |
| 流式追加 | 收到 `thinking_delta` | 内容末尾追加，带打字机光标 |
| 显示摘要 | 收到 `thinking_end` | 光标消失，summary 字段出现 |
| 手动折叠 | 用户点击头部 | 收起为单行摘要 |
| 手动展开 | 用户点击折叠态 | 展开完整内容 |

#### 性能注意

- **不要每条 delta 都重新 render 整个内容**：用 `useRef` 存累积字符串，只在最后 render 一次；或用虚拟列表截断超长内容（超过 2000 字符时只显示最近部分，展开查看全部）
- **Markdown 渲染懒加载**：`thinking_end` 之前用纯文本显示，结束后才加载 Markdown 渲染器（避免频繁 re-parse）

---

### 8.2 PlanPanel — 计划步骤组件（P1.14）

#### 功能定位

接收 SSE 的 `plan_start` / `plan_update` / `plan_done` 事件，展示 Agent 执行计划的步骤列表，实时高亮当前步骤。

#### 数据流

```
useSSEv2 返回的 planBlock（单一）
   │
   ▼
ChatPanelV2 遇到 type === 'plan'
   ▼
渲染 <PlanPanel plan={planBlock} />
```

#### 类型定义

```typescript
interface PlanStep {
  id: number;
  label: string;            // 步骤名称，如"生成项目结构"
  status: 'pending' | 'active' | 'done';  // 当前状态
}

interface PlanBlock {
  type: 'plan';
  id: string;
  steps: PlanStep[];
  currentStep: number;      // 当前执行到的步骤索引（0-based）
  isComplete: boolean;       // plan_done 后为 true
}
```

#### 组件接口与实现要点

```tsx
interface PlanPanelProps {
  plan: PlanBlock;
}

export function PlanPanel({ plan }: PlanPanelProps) {
  return (
    <div className="plan-panel">
      {/* 步骤列表：垂直时间线布局 */}
      <div className="steps-timeline">
        {plan.steps.map((step, index) => (
          <div key={step.id} className={`step ${step.status}`}>
            {/* 圆形节点：pending=灰 / active=蓝脉冲 / done=绿勾 */}
            <div className={`step-node step-${step.status}`}>
              {step.status === 'done' && <CheckIcon size={12} />}
              {step.status === 'active' && <PulseDot />}
              {step.status === 'pending' && <span>{index + 1}</span>}
            </div>

            {/* 连接线：最后一个不画 */}
            {index < plan.steps.length - 1 && (
              <div className={`connector connector-${step.status}`} />
            )}

            {/* 文字标签 */}
            <span className="step-label">{step.label}</span>
          </div>
        ))}
      </div>

      {/* 完成标记 */}
      {plan.isComplete && (
        <div className="complete-badge">
          <CheckCircle size={14} /> 计划已完成
        </div>
      )}
    </div>
  );
}
```

#### 视觉规范

| 状态 | 节点样式 | 连接线 | 文字颜色 |
|------|---------|--------|---------|
| `pending` | `w-6 h-6 rounded-full border-2 border-slate-300 bg-white` | `bg-slate-200` | `text-slate-400` |
| `active` | `w-6 h-6 rounded-full border-2 border-indigo-500 bg-indigo-50 animate-pulse` | `bg-indigo-300` | `text-indigo-600 font-medium` |
| `done` | `w-6 h-6 rounded-full border-2 border-green-500 bg-green-500 text-white` | `bg-green-300` | `text-slate-700` |

#### 与 SSE 事件的映射

| SSE 事件 | 组件响应 |
|---------|---------|
| `plan_start` `{steps:[...], current:0}` | 初始化步骤列表，全部 pending，第 0 步 active |
| `plan_update` `{steps:[...], current:N}` | 更新步骤列表，前 N-1 步改为 done，第 N 步 active |
| `plan_done` `{steps:[...]}` | 最后一步改为 done，显示「计划已完成」徽章 |

---

### 8.3 ToolCard — 工具调用卡片（P1.15）

#### 功能定位

接收 SSE 的 `tool_call:start` / `tool_call:end` 事件，以紧凑卡片形式展示 Agent 调用了哪个工具、参数是什么、结果如何。

#### 为什么需要这个组件？

- 让用户知道 Agent **做了什么操作**（调了 API、写了文件、查了数据）
- 出问题时能快速定位是哪个工具调用出错
- 增加透明度，减少「黑盒感」

#### 类型定义

```typescript
interface ToolCallBlock {
  type: 'tool_call';
  id: string;
  name: string;               // 工具名，如 "react-vite-scaffold"
  input?: Record<string, unknown>;  // 输入参数（可选，可能很大）
  status: 'running' | 'success' | 'error';
  durationMs?: number;         // tool_call:end 时填入
  error?: string;              // status === 'error' 时填入
  startedAt: number;
  endedAt?: number;
}
```

#### 组件实现要点

```tsx
interface ToolCardProps {
  tool: ToolCallBlock;
}

export function ToolCard({ tool }: ToolCardProps) {
  const [showDetails, setShowDetails] = useState(false);
  const isRunning = tool.status === 'running';

  return (
    <div className={`tool-card tool-${tool.status}`}>
      {/* 主行：图标 + 名称 + 状态标签 + 展开 */}
      <div className="main-row" onClick={() => setShowDetails(!showDetails)}>
        <Wrench size={14} />
        <code className="font-mono text-sm">{tool.name}</code>

        {/* 状态标签 */}
        {isRunning && <Badge variant="default">运行中...</Badge>}
        {tool.status === 'success' && (
          <Badge variant="success">✓ {tool.durationMs}ms</Badge>
        )}
        {tool.status === 'error' && <Badge variant="destructive">失败</Badge>}

        <ChevronRight size={14} className={`ml-auto transition-transform ${showDetails ? 'rotate-90' : ''}`} />
      </div>

      {/* 展开详情：输入参数 + 错误信息 */}
      {showDetails && (
        <details open>
          {/* 输入 JSON（格式化，可折叠） */}
          {tool.input && (
            <pre className="params-json">
              {JSON.stringify(tool.input, null, 2)}
            </pre>
          )}

          {/* 错误信息 */}
          {tool.error && (
            <div className="error-msg">{tool.error}</div>
          )}
        </details>
      )}
    </div>
  );
}
```

#### 视觉规范

| 状态 | 卡片背景 | 边框 | 特殊元素 |
|------|---------|------|---------|
| `running` | `bg-amber-50` | `border-amber-300` | 「运行中」badge + 微微呼吸动画 |
| `success` | `bg-green-50` | `border-green-300` | ✓ + 耗时 ms |
| `error` | `bg-red-50` | `border-red-300` | ✗ 错误信息可展开 |

**默认折叠**：只显示工具名 + 状态 + 耗时，点击展开查看参数和错误详情。避免大量参数撑爆对话区。

#### 大输入参数的处理

工具输入可能是很大的 JSON（比如文件内容）。策略：
- 默认**截断显示**：只显示 top-level keys 和值类型
- 点击展开后显示完整 JSON
- 超过 2KB 的内容显示 `... (共 N 字符)` 提示

---

### 8.4 StatusBar — 底部状态栏（P1.16）

#### 功能定位

固定在页面底部，全局展示当前项目的关键状态信息。

#### 展示的信息项

| 信息 | 来源 | 格式 |
|------|------|------|
| 项目类型 | AgentState.project_type | `React + Vite` / `HTML 单页` |
| 文件数量 | files 数组长度或 SSE file_created 计数 | `已生成 6 个文件` |
| WebContainer 状态 | useWebContainer.phase | `🔄 初始化中...` / `✅ 就绪` / `⚠️ 未启动` |
| Dev Server | previewSource.mode === 'url' | `🔧 pnpm run dev 运行中` |
| Session ID | 当前 session | 小字号灰色 |

```tsx
interface StatusBarProps {
  projectType?: string;
  fileCount: number;
  webContainerPhase: WebContainerPhase;
  devServerRunning: boolean;
  sessionId: string;
}

export function StatusBar({
  projectType,
  fileCount,
  webContainerPhase,
  devServerRunning,
  sessionId,
}: StatusBarProps) {
  const phaseLabel = {
    idle: '未启动',
    booting: '🔄 启动中...',
    installing: '📦 安装依赖...',
    ready: '✅ WebContainer 就绪',
    running: '▶️ Dev Server 运行中',
    error: '⚠️ 出错',
  };

  return (
    <footer className="status-bar">
      {/* 左侧：项目信息 */}
      <div className="left">
        {projectType && <Badge>{projectType}</Badge>}
        <span className="file-count">📄 {fileCount} 个文件</span>
      </div>

      {/* 中间：服务状态 */}
      <div className="center">
        <span className={`wc-status phase-${webContainerPhase}`}>
          {phaseLabel[webContainerPhase]}
        </span>
        {devServerRunning && <span>· 🔧 Dev Server</span>}
      </div>

      {/* 右侧：Session */}
      <div className="right">
        <code className="text-xs text-slate-400">{sessionId.slice(0, 8)}</code>
      </div>
    </footer>
  );
}
```

#### 视觉规范

| 元素 | 样式 |
|------|------|
| 容器 | `h-8 border-t border-slate-200 px-4 flex items-center justify-between bg-white sticky bottom-0 z-50` |
| 文字 | `text-xs text-slate-500` |
| Badge | `px-2 py-0.5 rounded-full text-xs font-medium`（不同状态不同色） |
| WC 就绪 | `text-green-600 font-medium` |
| WC 运行中 | `text-indigo-600 font-medium` |
| WC 出错 | `text-red-500 font-medium` |

#### 放置位置

StatusBar 应放在 App.tsx 最外层布局的**最底部**，不受 ResizableLayout 影响，始终可见：

```
┌──────────────────────────────────────┐
│         PageForge Header             │
├──────────┬───────────────────────────┤
│ ChatPanel │     PreviewPanel         │
│          │                           │
│          │                           │
├──────────┴───────────────────────────┤
│         StatusBar (始终固定)          │
└──────────────────────────────────────┘
```

---

### 8.5 Intent Router — 意图识别节点（P1.17）

> ⚠️ 这是后端 LangGraph 节点，不是前端组件。前端只需要消费识别结果。

#### 功能定位

作为 `graph_v2.py` 的**第一个节点**，分析用户输入，决定后续走哪条分支。

**关键决策**：意图识别不是独立服务，而是 LangGraph 图中的一个 LLM 节点，利用 LLM 自身的语义理解能力做分类。

#### 节点代码结构

```python
# backend/app/graph/nodes/intent.py

from typing import TypedDict
from langchain_core.messages import SystemMessage, HumanMessage

INTENT_SYSTEM_PROMPT = """你是 PageForge 的意图路由器。分析用户输入，返回以下信息：

## 意图分类
- chat: 纯对话（问候、闲聊、提问概念）
- code_gen: 一句话生成应用（"做个Todo"、"帮我建个博客"）
- code_edit: 修改已有代码（"把按钮改成红色"、"加个搜索功能"）
- explain: 解释代码或概念（"这段代码什么意思"、"什么是闭包"）
- debug: 调试问题（"我的页面报错了"、"样式不对"）
- file_operation: 文件操作（"删除这个文件"、"重命名"）
- unknown: 无法判断

## 输出格式（严格 JSON）
{
  "intent": "<分类>",
  "confidence": 0.0~1.0,
  "tags": ["<技术标签>"],
  "mode": "frontend|backend|fullstack|null",
  "complexity": "simple|medium|complex|null",
  "suggested_style": "<风格关键词，如 minimal/dark/glassmorphism/null>"
}

## 规则
1. confidence < 0.5 时 intent 设为 "unknown"
2. code_gen 类必须提取 suggested_style（从描述中的风格线索推断）
3. tags 尽量提取具体技术词（react/vite/tailwind/todo 等）
"""

def intent_router(state: dict) -> dict:
    """意图识别节点函数"""
    user_message = state.get("user_message", "")

    # 调用 LLM 分类
    response = llm.invoke([
        SystemMessage(content=INTENT_SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ])

    import json
    result = json.loads(response.content)

    # 通过 SSE 推送识别结果
    yield "event: INTENT_RESULT\ndata: " + json.dumps({
        "intent": result["intent"],
        "confidence": result["confidence"],
        "tags": result.get("tags", []),
        "mode": result.get("mode"),
        "suggested_style": result.get("suggested_style"),
    }) + "\n\n"

    # 如果需要征询风格偏好，发送 style_query 事件
    if result["intent"] == "code_gen" and not result.get("suggested_style"):
        yield "event: INTENT_STYLE_QUERY\ndata: " + json.dumps({
            "options": ["minimal", "vibrant", "dark"],
            "auto_select": "minimal",
            "timeout_ms": 5000,
        }) + "\n\n"

    return {
        "intent": result["intent"],
        "confidence": result["confidence"],
        "tags": result.get("tags", []),
        "ui_style": result.get("suggested_style") or "minimal",
    }
```

#### 在 graph_v2.py 中的接入方式

```python
# backend/app/graph/graph_v2.py
from langgraph.graph import StateGraph, START, END

graph = StateGraph(AgentState)

# 添加节点
graph.add_node("intent_router", intent_router)
graph.add_node("think", think_node)
graph.add_node("plan", plan_node)
graph.add_node("style_picker", style_picker_node)
graph.add_node("code_gen", code_gen_node)
graph.add_node("reply", reply_node)

# 条件边：根据 intent 决定下一步
def route_by_intent(state: dict):
    intent = state.get("intent", "unknown")
    if intent == "chat":
        return "reply"           # 直接回复，不走代码生成流程
    elif intent in ("code_gen", "code_edit"):
        return "think"           # 进入思考→计划→代码生成
    elif intent == "explain":
        return "reply"           # 解释类也直接回复
    else:
        return "reply"           # unknown 兜底直接回复

graph.add_conditional_edges(
    START,
    route_by_intent,
    {"chat": "reply", "think": "think", "reply": "reply"}
)

graph.add_edge("think", "plan")
graph.add_edge("plan", "style_picker")
graph.add_edge("style_picker", "code_gen")
graph.add_edge("code_gen", "reply")
graph.add_edge("reply", END)

pageforge_graph_v2 = graph.compile()
```

#### SSE 事件推送时机

| 事件 | 推送时机 | 数据 |
|------|---------|------|
| `intent:start` | 节点开始执行 | `{}` |
| `intent:result` | LLM 返回分类结果 | `{intent, confidence, tags, mode, suggested_style}` |
| `intent:style_query` | code_gen 且无风格线索时 | `{options, auto_select, timeout_ms}` |
| `intent:style_selected` | 用户选择或超时自动选择后 | `{style}` |

#### 注意事项

1. **意图识别必须是轻量级的**：不要在这个节点做复杂推理，只做分类。Prompt 要精炼，控制 token 消耗。
2. **LLM 选择**：可以用小模型做意图识别（如 GPT-4o-mini），不需要大模型。分类任务小模型就够了。
3. **兜底机制**：如果 LLM 返回的 JSON 解析失败或 confidence 太低，一律走 `unknown` → `reply` 分支，不会阻塞主流程。
4. **缓存**：同一个 session 内，如果用户的意图没变（连续追问同一主题），可以跳过重复识别。

---

### 8.6 动态 UI 风格生成（P1.18）— 详细实施

> 第 6 节已经定义了动态风格生成的理念，这里补充具体的代码级实施细节。

#### Style Picker 节点实现

```python
# backend/app/graph/nodes/style_picker.py
import subprocess
import json

def style_picker_node(state: dict) -> dict:
    """
    风格选择节点：
    1. 从 state 取 suggested_style（Intent Router 传入）
    2. 调用 ui-ux-pro-max CLI 获取风格数据
    3. 注入 frontend-design 设计哲学
    4. 生成最终的风格配置文本，存入 state.ui_style_config
    """
    style_keyword = state.get("ui_style", "minimal")  # 默认 minimal
    project_type = state.get("project_type", "react-vite-app")

    # 构造查询关键词
    query_keywords = f"{style_keyword} {project_type}"
    if state.get("tags"):
        query_keywords += " " + " ".join(state["tags"][:3])  # 取前3个 tag

    # 调用 ui-ux-pro-max CLI
    try:
        result = subprocess.run(
            [
                "python3", "skills/UI_UX/scripts/search.py",
                query_keywords,
                "--design-system",
                "-f", "json"  # JSON 格式输出，方便程序解析
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        design_system = json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        # CLI 不可用时降级为内置默认配置
        design_system = _get_fallback_design_system(style_keyword)

    # 读取 frontend-design 设计哲学
    design_philosophy = _load_frontend_design_rules()

    # 合并为最终配置
    final_config = _merge_style_config(design_system, design_philosophy)

    # 通过 SSE 推送风格确认事件
    yield "event: STYLE_SELECTED\ndata: " + json.dumps({
        "style": style_keyword,
        "primary_color": final_config.get("colors", {}).get("primary", "#171717"),
        "description": f"已选择「{style_keyword}」风格",
    }) + "\n\n"

    return {"ui_style_config": final_config}


def _get_fallback_design_system(style: str) -> dict:
    """CLI 不可用时的内置降级方案"""
    fallbacks = {
        "minimal": {
            "colors": {"primary": "#171717", "background": "#ffffff", ...},
            "typography": {"font_family": "'Inter', system-ui, ..."},
            ...
        },
        "dark": {
            "colors": {"primary": "#e2e8f0", "background": "#0a0a0a", ...},
            ...
        },
        "glassmorphism": {...},
        "vibrant": {...},
    }
    return fallbacks.get(style, fallbacks["minimal"])


def _load_frontend_design_rules() -> str:
    """读取 frontend-design SKILL.md 的核心规则"""
    rules_path = Path(__file__).parent.parent.parent / "skills" / "frontend-design" / "SKILL.md"
    try:
        with open(rules_path) as f:
            content = f.read()
        # 提取关键规则段（Frontend Aesthetics Guidelines 部分）
        return _extract_aesthetics_section(content)
    except FileNotFoundError:
        return ""


def _merge_style_config(design_system: dict, philosophy: str) -> str:
    """合并 ui-ux-pro-max 数据 + frontend-design 哲学 → 最终注入 Prompt 的文本"""
    colors = design_system.get("colors", {})
    typography = design_system.get("typography", {})
    anti_patterns = design_system.get("anti_patterns", [])

    config_text = f"""
## UI 风格配置（由 Style Picker 自动生成）
- 主色调：{colors.get('primary', '#171717')}
- 辅助色：{colors.get('secondary', '#52525b')}
- 背景色：{colors.get('background', '#ffffff')}
- 强调色：{colors.get('accent', '#6366f1')}
- 字体族：{typography.get('font_family', "'Inter', system-ui")}
- 标题字重：{typography.get('heading_weight', '600')}
- 正文字号：{typography.get('body_size', '14px')}

## 反模式约束（禁止事项）
{chr(10).join(f'- {p}' for p in anti_patterns[:8])}

## 设计哲学（来自 frontend-design skill）
{philosophy[:1000]}  /* 截断过长的哲学描述 */
"""
    return config_text
```

#### 在 Code Gen 节点中使用风格配置

```python
def code_gen_node(state: dict) -> dict:
    # 获取风格配置
    style_config = state.get("ui_style_config", "")

    # 将风格配置注入 Prompt
    system_prompt = f"""你是一个 React + Vite + Tailwind 专家开发者。

## 用户需求
{state['user_message']}

## UI 风格要求（必须严格遵守）
{style_config}

## 输出要求
- 生成完整的多文件 React + Vite + TypeScript 项目
- 使用 Tailwind CSS v4 进行样式编写
- 使用 shadcn/ui 作为基础组件库
- ...

请开始生成代码...
"""
    # ... 调用 LLM 生成代码
```

#### 风格配置的生命周期

```
Intent Router
  → 输出 suggested_style（如 "dark"）
  → 发送 intent:result {suggested_style:"dark"}
      ↓
Style Picker 节点
  → 接收 suggested_style
  → 调用 ui-ux-pro-max search.py "dark react-vite-app" --design-system
  → 合并 frontend-design 哲学
  → 生成 ui_style_config 文本
  → 发送 style_selected {style:"dark"}
      ↓
Code Gen 节点
  → 读取 ui_style_config
  → 注入 Prompt
  → LLM 生成的代码自动遵循该风格
      ↓
UI Polish（可选，P2）
  → 检查输出是否符合风格配置
  → 不符合则修正
```

---

### 8.7 SSE 事件分发器重构（P1.20）

#### 现状问题

当前 `useSSEv2.ts` 把所有 SSE 事件处理逻辑都写在了一个 Hook 里（13000+ 字节），包括：
- 连接管理（重连、断线检测）
- 事件解析（SSE 格式解析）
- 状态更新（blocks、status、files 等）
- 业务逻辑（previewSource 设置等）

**问题**：职责不清，新增事件类型时要改 Hook 本身，违反开闭原则。

#### 重构目标

拆分为三层：

```
┌─────────────────────────────────┐
│         useSSEv2 (Hook)          │  ← 只管状态聚合，不关心具体事件
│  - 维护 blocks[] 状态数组        │
│  - 暴露 onThinking / onPlan ... │
└──────────────┬──────────────────┘
               │ 调用
┌──────────────▼──────────────────┐
│      SseEventDispatcher         │  ← 事件路由：分发到对应 handler
│  - 解析原始 SSE 文本             │
│  - 按 event name 路由            │
│  - 错误事件统一处理               │
└──────────────┬──────────────────┘
               │ 调用
┌──────────────▼──────────────────┐
│     Event Handlers (独立模块)     │  ← 各自负责一类事件的业务逻辑
│  - thinkingHandler.ts            │
│  - planHandler.ts                │
│  - toolCallHandler.ts            │
│  - fileEventHandler.ts           │
│  - statusHandler.ts              │
│  - intentHandler.ts              │
│  - styleHandler.ts               │
└─────────────────────────────────┘
```

#### 文件结构

```
frontend/src/services/sse/
├── index.ts                 # 导出 SseEventDispatcher
├── SseEventDispatcher.ts    # 核心：连接管理 + 事件路由
├── types.ts                 # 所有 SSE 事件类型的 TypeScript 定义
├── handlers/
│   ├── thinkingHandler.ts   # thinking_start/delta/end → ThinkingBlock
│   ├── planHandler.ts       # plan_start/update/done → PlanBlock
│   ├── toolCallHandler.ts   # tool_call:start/end → ToolCallBlock
│   ├── fileEventHandler.ts  # file_created/updated/deleted → FileNode[]
│   ├── statusHandler.ts     # status:* → 全局状态变更
│   ├── intentHandler.ts     # intent:* → IntentResult
│   └── styleHandler.ts      # style_* → StyleConfig
└── utils/
    ├── parseEvent.ts        # SSE 文本 → 结构化对象
    └── reconnect.ts         # 重连策略（指数退避）
```

#### 核心分发器实现

```typescript
// frontend/src/services/sse/SseEventDispatcher.ts
import type { SSEEvent } from './types';
import { parseSSELine } from './utils/parseEvent';
import { thinkingHandler } from './handlers/thinkingHandler';
import { planHandler } from './handlers/planHandler';
import { toolCallHandler } from './handlers/toolCallHandler';
import { fileEventHandler } from './handlers/fileEventHandler';
import { statusHandler } from './handlers/statusHandler';
import { intentHandler } from './handlers/intentHandler';
import { styleHandler } from './handlers/styleHandler';

// 事件名 → handler 映射表（注册制，新增事件只需加一行）
const HANDLER_MAP: Record<string, (event: SSEEvent) => void> = {
  'thinking_start': thinkingHandler.onStart,
  'thinking_delta': thinkingHandler.onDelta,
  'thinking_end': thinkingHandler.onEnd,
  'plan_start': planHandler.onStart,
  'plan_update': planHandler.onUpdate,
  'plan_done': planHandler.onDone,
  'tool_call:start': toolCallHandler.onStart,
  'tool_call:end': toolCallHandler.onEnd,
  'file_created': fileEventHandler.onCreate,
  'file_updated': fileEventHandler.onUpdate,
  'file_deleted': fileEventHandler.onDelete,
  'status:init': statusHandler.onInit,
  'status:installing': statusHandler.onInstalling,
  'status:install_done': statusHandler.onInstallDone,
  'status:generation_done': statusHandler.onGenerationDone,
  'status:starting_dev': statusHandler.onStartingDev,
  'status:preview_ready': statusHandler.onPreviewReady,
  'intent:start': intentHandler.onStart,
  'intent:result': intentHandler.onResult,
  'intent:style_query': intentHandler.onStyleQuery,
  'intent:style_selected': intentHandler.onStyleSelected,
  'style_selected': styleHandler.onSelected,
  'error': errorHandler,
};

export class SseEventDispatcher {
  private eventSource: EventSource | null = null;
  private listeners = new Map<string, Set<(data: any) => void>>();

  constructor(private url: string) {}

  /** 订阅某类事件的数据变化 */
  on(eventType: string, callback: (data: any) => void): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(callback);
    // 返回取消订阅函数
    return () => this.listeners.get(eventType)?.delete(callback);
  }

  connect() {
    this.eventSource = new EventSource(this.url);

    this.eventSource.onmessage = (event) => {
      const parsed = parseSSELine(event.data);
      if (!parsed) return;

      // 1. 路由到对应的 handler
      const handler = HANDLER_MAP[parsed.event];
      if (handler) {
        handler(parsed.data);
      }

      // 2. 通知所有订阅者
      const subscribers = this.listeners.get(parsed.event);
      if (subscribers) {
        subscribers.forEach(cb => cb(parsed.data));
      }
    };

    this.eventSource.onerror = () => {
      this.handleReconnect();
    };
  }

  disconnect() {
    this.eventSource?.close();
    this.eventSource = null;
  }

  private handleReconnect() {
    // 指数退避重连：1s → 2s → 4s → 8s → 最大 30s
    // 见 utils/reconnect.ts
  }
}
```

#### 新增事件只需做的事

重构后，如果后端新增了一种 SSE 事件（比如 `progress:update`）：

1. 在 `types.ts` 加一个类型定义
2. 在 `handlers/` 下新建 `progressHandler.ts`
3. 在 `HANDLER_MAP` 注册一行

**不用改** `useSSEv2.ts`、**不用改** `SseEventDispatcher.ts`。

#### useSSEv2 简化后的形态

```typescript
// 重构后的 useSSEv2.ts — 只做状态聚合
export function useSSEv2(sessionId: string): UseSSEv2Return {
  const [blocks, setBlocks] = useState<RenderBlock[]>([]);
  const [status, setStatus] = useState<SSEStatus>('idle');
  const [files, setFiles] = useState<FileNode[]>([]);
  const [generationDone, setGenerationDone] = useState(false);
  const [previewSource, setPreviewSource] = useState<PreviewSource>({ mode: 'none' });

  useEffect(() => {
    const dispatcher = new SseEventDispatcher(`/api/${sessionId}/messages`);

    // 订阅各类事件的状态变化
    const unsubThinking = dispatcher.on('thinking_end', (data) => {
      setBlocks(prev => updateOrAppendBlock(prev, data));
    });
    const unsubPlan = dispatcher.on('plan_update', (data) => {
      setBlocks(prev => updateOrAppendBlock(prev, data));
    });
    const unsubTool = dispatcher.on('tool_call:end', (data) => {
      setBlocks(prev => updateOrAppendBlock(prev, data));
    });
    const unsubFile = dispatcher.on('file_created', (data) => {
      setFiles(prev => appendFileNode(prev, data));
    });
    const unsubStatus = dispatcher.on('generation_done', () => {
      setGenerationDone(true);
    });

    dispatcher.connect();

    return () => {
      unsubThinking();
      unsubPlan();
      unsubTool();
      unsubFile();
      unsubStatus();
      dispatcher.disconnect();
    };
  }, [sessionId]);

  return { blocks, status, files, generationDone, previewSource, setPreviewSource };
}
```

---

### 8.8 错误处理 + 重试机制（P1.21）

#### 需要处理的错误场景

| # | 错误场景 | 来源 | 可恢复？ | 用户感知 |
|---|---------|------|---------|---------|
| 1 | SSE 连接断开 | 网络 | ✅ 自动重连 | 底部 toast 提示"连接中断，重连中..." |
| 2 | WebContainer boot 失败 | 浏览器兼容性 | ❌ 降级 | 提示"浏览器不支持 WebContainer，切换到 HTML 预览模式" |
| 3 | pnpm install 超时 | 依赖安装慢 | ✅ 重试 | 进度条 + "安装耗时较长，是否重试？"按钮 |
| 4 | LLM 生成代码报错 | API 错误 / Token 超限 | ✅ 重试 | 错误提示 + "重新生成"按钮 |
| 5 | 文件写入 WebContainer 失败 | FS 错误 | ⚠️ 跳过该文件 | 该文件在文件树上标红，不影响其他文件 |
| 6 | Dev Server 启动失败 | 端口占用 / 依赖缺失 | ✅ 换端口 / 降级 Vite | 提示 + 自动尝试降级方案 |
| 7 | 意图识别失败 | LLM 解析错误 | ✅ 兜底 chat | 静默降级，走通用回复分支 |

#### 统一错误类型

```typescript
// frontend/src/services/error.ts

export enum ErrorCategory {
  NETWORK = 'network',          // 网络相关（SSE 断连、API 超时）
  WEBCONTAINER = 'webcontainer', // WebContainer 相关
  DEPENDENCY = 'dependency',    // 安装依赖相关
  GENERATION = 'generation',    // LLM 代码生成相关
  FILESYSTEM = 'filesystem',    // 文件系统操作
  SERVER = 'server',            // 后端服务错误
  UNKNOWN = 'unknown',
}

export interface AppError {
  id: string;                   // 唯一标识（用于去重和跟踪）
  category: ErrorCategory;
  code: string;                 // 错误码，如 'WC_BOOT_FAILED'
  message: string;              // 用户友好的错误描述
  detail?: string;              // 技术细节（展开后显示）
  recoverable: boolean;         // 是否可恢复
  retryAction?: () => Promise<void>;  // 重试回调
  fallbackAction?: () => void;       // 降级方案回调
  timestamp: number;
  dismissed: boolean;           // 是否被用户关闭
}
```

#### 错误状态管理

```typescript
// 使用简单的 Store（不需要 Redux/Zustand，Context 够用）
interface ErrorState {
  errors: AppError[];
  activeError: AppError | null;  // 当前最严重的未处理错误
}

// 操作
const addError = (error: AppError) => {};
const dismissError = (id: string) => {};     // 关闭错误
const retryError = (id: string) => {};       // 重试
const clearResolvedErrors = () => {};         // 清除已解决的
```

#### 重试策略

```typescript
// 重试配置
const RETRY_CONFIG: Record<ErrorCategory, {
  maxRetries: number;
  backoffMs: number;       // 初始退避时间
  maxBackoffMs: number;    // 最大退避时间
}> = {
  [ErrorCategory.NETWORK]:     { maxRetries: Infinity, backoffMs: 1000, maxBackoffMs: 30000 },
  [ErrorCategory.DEPENDENCY]:  { maxRetries: 3, backoffMs: 2000, maxBackoffMs: 10000 },
  [ErrorCategory.GENERATION]:  { maxRetries: 2, backoffMs: 3000, maxBackoffMs: 10000 },
  [ErrorCategory.WEBCONTAINER]: { maxRetries: 1, backoffMs: 1000, maxBackoffMs: 5000 },
};

async function retryWithBackoff(
  action: () => Promise<void>,
  config: typeof RETRY_CONFIG[keyof typeof RETRY_CONFIG],
): Promise<void> {
  for (let attempt = 0; attempt < config.maxRetries; attempt++) {
    try {
      await action();
      return; // 成功
    } catch (err) {
      const delay = Math.min(config.backoffMs * Math.pow(2, attempt), config.maxBackoffMs);
      await sleep(delay);
    }
  }
  throw new Error(`Retry failed after ${config.maxRetries} attempts`);
}
```

#### 错误 UI 组件

```tsx
// Toast 弹窗（用于网络类瞬时错误）
<ErrorToast error={activeError} onDismiss={dismiss} onRetry={retry} />

// 内联错误卡片（用于生成过程中的错误）
<ErrorCard error={error}>
  {error.recoverable && (
    <Button onClick={() => retryError(error.id)}>
      <RefreshCw size={14} /> 重试
    </Button>
  )}
  {error.fallbackAction && (
    <Button variant="outline" onClick={error.fallbackAction}>
      降级方案
    </Button>
  )}
</ErrorCard>

// 全局错误边界（React Error Boundary 包裹整个应用）
<ErrorBoundary fallback={<GlobalErrorFallback />}>
  <App />
</ErrorBoundary>
```

#### 降级方案矩阵

| 错误 | 降级方案 | 触发条件 |
|------|---------|---------|
| WebContainer 不支持 | 切换到 HTML iframe srcDoc 模式 | 非 Chromium 浏览器 / WebContainer API 不可用 |
| pnpm install 反复失败 | 跳过依赖安装，尝试直接启动（可能会缺包但简单项目能跑） | 3 次重试均失败 |
| Dev Server 端口占用 | 自动换端口（3000→3001→3002） | EADDRINUSE |
| LLM 生成超时 | 返回已有文件的部分预览 + 提示用户可继续 | 单次请求 > 120s |
| Monaco 加载失败 | 用 `<pre>` 代码块代替 | CDN 超时 / 网络问题 |

---

## 9. P1 任务依赖关系

```
                    ┌──────────────┐
                    │ P1.20 SSE    │ ← 基础设施，其他组件依赖它
                    │ 事件分发器   │
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌────────────┐  ┌────────────┐  ┌────────────┐
   │ P1.13 Think│  │ P1.14 Plan │  │ P1.15 Tool │
   │ ingPanel   │  │ Panel      │  │ Card       │
   └────────────┘  └────────────┘  └────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                   ┌────────────┐
                   │ P1.16 Status│
                   │ Bar        │
                   └──────┬─────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
   ┌────────────┐  ┌────────────┐  ┌────────────┐
   │ P1.17      │  │ P1.18+19   │  │ P1.21 错误  │
   │ Intent     │  │ Style 系统 │  │ 处理+重试  │
   │ Router     │  │            │  │            │
   └────────────┘  └────────────┘  └────────────┘
```

**建议实施顺序**：20 → 21 → 13/14/15 → 16 → 17 → 18/19

理由：先搭好基础设施（SSE 分发器 + 错误处理），再建上层组件，最后完成后端节点。

---

## 10. 改造核心陷阱清单（必读）

> 以下陷阱来自对现有代码的真实分析，改造前务必理解。

### 陷阱 1：`useSSE.ts` 是重灾区（457 行，高度耦合）

**现状**：Hook 内部硬编码了 4 类 `RenderBlock`，有复杂的双背压缓冲（文本消费 + 源码消费）。

**爆破点**：`RenderBlock` 类型只有 4 种（`reasoning` / `text` / `tool_call` / `generation`），新 SSE 事件有 25+ 种。

**对策**：不要改 `useSSE.ts`，**新建 `useSSEv2.ts`**。过渡期两个并存，旧项目走 v1，新项目走 v2。

```typescript
// App.tsx 中根据项目类型选择
const isNewProject = projectType === 'react-vite-app';
const sse = isNewProject ? useSSEv2(sessionId) : useSSE(sessionId);
```

### 陷阱 2：`latestHtml` / `streamingHtml` 渗透全项目

**现状**：这两个状态被传到 `App.tsx` → `previewHtml` → `WebContainerPanel html` prop，还有 `ChatPanel`。

**爆破点**：改成 URL 预览后，这些引用会全部变成 `undefined` 或需要条件判断。

**对策**：加 `PreviewSource` 联合类型，不改旧逻辑：

```typescript
type PreviewSource =
  | { mode: 'html'; html: string }
  | { mode: 'url'; url: string }
  | { mode: 'none' };
```

### 陷阱 3：`WebContainerPanel.tsx` 命名欺诈

**现状**：
- `WebContainerPanel.tsx` — 名字带 WebContainer，但实现是 `iframe srcDoc={html}`（没用 WebContainer API）
- `WebContainerDemo.tsx` — **这才是真正用 WebContainer API 的**

**对策**：
```
WebContainerPanel.tsx  → 改名 HtmlPreviewPanel.tsx
新建 PreviewPanel.tsx      → 包含 TabBar + FileTree + CodeViewer + WebContainer URL 预览
```

### 陷阱 4：`messages.py` SSE 翻译层（220 行复杂逻辑）

**现状**：有复杂的 HTML 检测状态机（`expecting_html` / `in_html_mode` / `html_prefix_buffer`）。

**爆破点**：新事件不能直接加在旧逻辑里，否则一改就炸 HTML 路径。

**对策**：新事件用 `continue` 跳过旧逻辑，旧逻辑**完全不动**。

### 陷阱 5：`AgentState` 加字段，但**不能删旧字段**

**现状**：`state.py` 的 `output_html: str` 是必填字段。

**爆破点**：数据库里存的老 session 只有 `output_html`，没有 `files`。直接把 `output_html` 改成 `Optional` 并删了，老 session 加载全炸。

**对策**：新旧字段并存，新字段全 `Optional`，用 `.get()` 安全访问。

### 陷阱 6：LangGraph 图结构改动——**新建，不修改**

**对策**：
```
backend/app/graph/graph.py     → 保留，旧项目用
backend/app/graph/graph_v2.py → 新建，Phase 1 用
```

在 `messages.py` 里根据项目类型路由。

### 陷阱 7：版本系统（VersionSelector + version_service）兼容

**对策**：改版本接口返回结构，加 `type` 字段区分 `html` / `project`，前端根据 `type` 决定渲染路径。**不要删旧逻辑**。

---

## 11. 实施优先级与拆分

### P0 — 核心能力（必须先做）

| # | 任务 | 涉及改动 | 陷阱提醒 |
|---|------|---------|----------|
| 1 | 后端 files / content API | `backend/app/api/` | 注意版本接口兼容 |
| 2 | Agent 输出改为多文件 JSON | `backend/app/graph/nodes/` | 不改旧字段，新字段 Optional |
| 3 | SSE 全生命周期事件 | `backend/app/api/messages.py` | 新事件用 continue 跳过旧逻辑 |
| 4 | 新建 `useSSEv2.ts` | `frontend/src/hooks/` | 不改旧 useSSE.ts |
| 5 | 前端 FileTree 组件 | `frontend/src/components/FileTree.tsx` | - |
| 6 | 前端 CodeViewer 组件 | `frontend/src/components/CodeViewer.tsx` | Monaco 懒加载 |
| 7 | 前端 TabBar + 双模式切换 | `frontend/src/components/TabBar.tsx` | - |
| 8 | ResizableLayout 改造（支持显隐+组件切换） | `frontend/src/components/ResizableLayout.tsx` | 右侧支持三种分支 |
| 9 | ChatPanel 消息类型扩展 | `frontend/src/components/ChatPanel.tsx` | 用 v2 的 RenderBlock |
| 10 | WebContainer 三阶段启动逻辑 | `frontend/src/hooks/useWebContainer.ts` | - |
| 11 | 新建 PreviewPanel.tsx | `frontend/src/components/PreviewPanel.tsx` | 内含 TabBar + FileTree + Code + Preview |
| 12 | WebContainerPanel → HtmlPreviewPanel 改名 | `frontend/src/components/` | 别改错文件 |

### P1 — 体验增强（紧接着做）

| # | 任务 | 涉及改动 |
|---|------|---------|
| 13 | ThinkingPanel 思维链组件 | `frontend/src/components/ThinkingPanel.tsx` |
| 14 | PlanPanel 计划步骤组件 | `frontend/src/components/PlanPanel.tsx` |
| 15 | ToolCard 工具调用卡片 | `frontend/src/components/ToolCard.tsx` |
| 16 | StatusBar 底部状态栏 | `frontend/src/components/StatusBar.tsx` |
| 17 | Intent Router 意图识别节点 | `backend/app/graph/nodes/intent.py` |
| 18 | 动态 UI 风格生成（调用 ui-ux-pro-max + frontend-design） | `skills/UI_UX/`, `skills/frontend-design/` |
| 19 | Style Picker 风格选择节点 | `backend/app/graph/nodes/style_picker.py` |
| 20 | SSE 事件分发器重构 | `frontend/src/services/sse.ts` |
| 21 | 错误处理 + 重试机制 | `frontend/src/services/error.ts` |

### P2 — 打磨（最后做）

| # | 任务 | 说明 |
|---|------|------|
| 22 | UI Polish Agent | 单独的视觉审查节点 |
| 23 | 文件树右键菜单 | 重命名、删除等操作 |
| 24 | Monaco 编辑器增强 | 语法高亮、minimap、搜索 |
| 25 | 预览热更新 | 文件变更自动刷新 iframe |
| 26 | 导出功能 | 下载生成的项目为 zip |
| 27 | 会话持久化 | 刷新页面后恢复对话和文件状态 |

---

## 12. 技术风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| WebContainer 兼容性 | 仅支持 Chromium 内核浏览器 | 降级方案：后端沙箱预览 |
| LLM 生成的 UI 质量不稳定 | 可能产生不可用的界面 | 设计 Skill 强约束 + Anti-patterns 规则 |
| 大量文件的 SSE 推送延迟 | 用户感知卡顿 | 分批推送 + 虚拟滚动文件树 |
| pnpm install 超时 | 依赖安装可能很慢 | 进度回调 + 超时提示 + 可重试 |
| Monaco Editor 包体积 (~3MB) | 首屏加载慢 | 懒加载（切到代码 Tab 时才加载） |
| 旧 session 数据兼容性 | 老数据加载失败 | 新字段全 Optional，用 .get() 访问 |

---

## 13. 验收标准

### 功能验收
- [ ] 用户输入"做个Todo"，能生成多文件 React 项目
- [ ] 文件树正确展示项目目录结构
- [ ] 点击文件能在 Monaco 中查看代码
- [ ] 预览 Tab 能正常加载并运行生成的前端应用
- [ ] pnpm install 无感完成，用户无需手动操作
- [ ] 对话区能看到 Agent 的思考过程和执行计划
- [ ] 不同设计风格生成的 UI 有明显差异
- [ ] 旧项目（单 HTML）还能正常加载和预览（兼容性）

### 性能验收
- [ ] 从输入到预览就绪 < 15s（简单项目）
- [ ] pnpm install 与文件生成真正并行（非串行等待）
- [ ] SSE 事件无丢失、无乱序
- [ ] 文件树 100+ 节点不卡顿

---

## 14. 改造策略口诀

```
不改旧文件，新建来代替。
旧逻辑保留，新逻辑并存。
字段加 Optional，数据库兼容。
命名先理清，再动手不迟。
```

> 文档位置：`pageforge/docs/PHASE1_REFACTOR_PLAN.md`
> 改造前务必阅读第 8 节「改造核心陷阱清单」。
