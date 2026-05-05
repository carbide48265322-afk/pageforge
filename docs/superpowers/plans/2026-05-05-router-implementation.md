# PageForge 路由架构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 PageForge 前端引入 TanStack Router v1，实现首页和对话页的路由分离，支持通过 URL 直接访问特定会话。

**Architecture:** 采用 TanStack Router 官方推荐的文件命名约定路由结构，使用 `__root.tsx` 作为根布局，`index.tsx` 作为首页，`chat.$sessionId.tsx` 作为对话页，完全移除 App.tsx。

**Tech Stack:** React 18, TanStack Router v1, TypeScript

---

## 文件结构

```
frontend/src/
├── routes/                          # 新增：路由组件目录
│   ├── __root.tsx                   # 新增：根布局（导航栏 + Outlet）
│   ├── index.tsx                    # 新增：首页 /
│   ├── chat.$sessionId.tsx          # 新增：对话页 /chat/:sessionId
│   └── routeTree.ts                 # 新增：路由树配置
├── components/                        # 现有组件（保持不变）
│   ├── ChatPanelV2.tsx
│   ├── PreviewPanel.tsx
│   └── ...
├── hooks/                            # 现有 hooks（保持不变）
│   ├── useSession.ts
│   ├── useSSEv2.ts
│   └── useWebContainer.ts
├── services/                         # 现有服务（保持不变）
├── main.tsx                          # 修改：使用 RouterProvider
├── App.tsx                           # 删除
└── index.css                         # 全局样式（保持不变）
```

---

## 实施任务

### Task 1: 安装 TanStack Router 依赖

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: 安装 @tanstack/react-router**

```bash
cd frontend && npm install @tanstack/react-router
```

- [ ] **Step 2: 验证安装成功**

```bash
npm ls @tanstack/react-router
```
Expected: 显示已安装版本号

---

### Task 2: 创建路由目录结构

**Files:**
- Create: `frontend/src/routes/__root.tsx`
- Create: `frontend/src/routes/index.tsx`
- Create: `frontend/src/routes/chat.$sessionId.tsx`
- Create: `frontend/src/routes/routeTree.ts`

- [ ] **Step 1: 创建 routes 目录**

```bash
mkdir -p frontend/src/routes
```

- [ ] **Step 2: 创建路由树配置文件 routeTree.ts**

```typescript
import { createRootRoute, createRoute, createRouter } from '@tanstack/react-router';
import { RootRoute } from './__root';
import { IndexRoute } from './index';
import { ChatRoute } from './chat.$sessionId';

const routeTree = RootRoute.addChildren([
  IndexRoute,
  ChatRoute,
]);

export const router = createRouter({ routeTree });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
```

- [ ] **Step 3: 创建根布局组件 __root.tsx**

从 App.tsx 提取 Header 部分，作为全局布局：

```typescript
import { Outlet, createRootRoute } from '@tanstack/react-router';
import { Eye, Rocket } from 'lucide-react';

export const RootRoute = createRootRoute({
  component: RootComponent,
});

function RootComponent() {
  return (
    <div className="h-screen flex flex-col bg-white border border-gray-100">
      <header className="flex items-center justify-between border-b border-gray-200 px-4 md:px-6 py-3 shrink-0 bg-white/95 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-black">
            <Rocket size={16} className="text-white" />
          </div>
          <h1 className="text-base font-semibold text-black tracking-tight">PageForge</h1>
          <span className="text-xs text-gray-400 hidden sm:inline">AI 项目生成器</span>
        </div>
        <div className="flex items-center gap-2">
          {/* 版本选择器和预览按钮将在具体页面中添加 */}
        </div>
      </header>
      <Outlet />
    </div>
  );
}
```

- [ ] **Step 4: 创建首页组件 index.tsx**

```typescript
import { createFileRoute, Link } from '@tanstack/react-router';
import { useState, useEffect } from 'react';
import { Plus, MessageSquare } from 'lucide-react';

export const IndexRoute = createFileRoute('/')({
  component: IndexComponent,
});

function IndexComponent() {
  const [sessions, setSessions] = useState<Array<{ id: string; title: string; updatedAt: string }>>([]);
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    // 从 localStorage 或 API 获取会话列表
    const stored = localStorage.getItem('pageforge_sessions');
    if (stored) {
      setSessions(JSON.parse(stored));
    }
  }, []);

  const handleCreateSession = async () => {
    setIsCreating(true);
    try {
      const response = await fetch('/api/sessions', { method: 'POST' });
      const data = await response.json();
      // 跳转到新会话页面
      window.location.href = `/chat/${data.sessionId}`;
    } catch (error) {
      console.error('创建会话失败:', error);
      setIsCreating(false);
    }
  };

  return (
    <div className="flex-1 overflow-auto bg-gray-50/50 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-2xl font-semibold text-gray-900">我的会话</h2>
          <button
            onClick={handleCreateSession}
            disabled={isCreating}
            className="flex items-center gap-2 px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 transition-colors"
          >
            <Plus size={16} />
            {isCreating ? '创建中...' : '新建会话'}
          </button>
        </div>

        {sessions.length === 0 ? (
          <div className="text-center py-16">
            <MessageSquare size={48} className="mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">还没有会话记录</p>
            <p className="text-sm text-gray-400 mt-1">点击上方按钮创建第一个会话</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {sessions.map((session) => (
              <Link
                key={session.id}
                to="/chat/$sessionId"
                params={{ sessionId: session.id }}
                className="block p-4 bg-white rounded-lg border border-gray-200 hover:border-gray-300 hover:shadow-sm transition-all"
              >
                <h3 className="font-medium text-gray-900">{session.title || '未命名会话'}</h3>
                <p className="text-sm text-gray-500 mt-1">
                  最后更新: {new Date(session.updatedAt).toLocaleDateString()}
                </p>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 5: 创建对话页组件 chat.$sessionId.tsx**

```typescript
import { createFileRoute, Link } from '@tanstack/react-router';
import { useState, useEffect, useRef } from 'react';
import { Eye } from 'lucide-react';
import { useSession } from '../hooks/useSession';
import { useSSEv2 } from '../hooks/useSSEv2';
import { useWebContainer } from '../hooks/useWebContainer';
import { ChatPanelV2 } from '../components/ChatPanelV2';
import { PreviewPanel } from '../components/PreviewPanel';
import { ResizableLayout } from '../components/ResizableLayout';
import { VersionSelector } from '../components/VersionSelector';
import { BaseConfirmDialog } from '../components/BaseConfirmDialog';
import type { PageVersion } from '../services/api';
import { MockDebugPanel } from '../components/MockDebugPanel';

export const ChatRoute = createFileRoute('/chat/$sessionId')({
  component: ChatComponent,
});

function ChatComponent() {
  const { sessionId } = Route.useParams();
  const navigate = useNavigate({ from: '/chat/$sessionId' });

  const {
    versions,
    currentBase,
    newSession,
    loadVersions,
    switchBaseVersion,
    loadHtml,
  } = useSession(sessionId);

  const {
    messages,
    isLoading,
    currentBlocks,
    completedTurns,
    previewSource,
    files,
    setPreviewSource,
    sendMessage,
    stopGeneration,
  } = useSSEv2(sessionId);

  const webContainer = useWebContainer(sessionId);

  const [previewOpen, setPreviewOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<string>('');
  const wcStartedRef = useRef(false);
  const [pendingVersion, setPendingVersion] = useState<PageVersion | null>(null);

  useEffect(() => {
    if (previewSource.mode !== 'none' && !previewOpen) {
      setPreviewOpen(true);
    }
  }, [previewSource]);

  useEffect(() => {
    if (!isLoading && sessionId && messages.length > 0) {
      loadVersions();
    }
  }, [isLoading]);

  useEffect(() => {
    if (!sessionId || isLoading) return;

    const lastStatusBlock = [...currentBlocks].reverse().find(b => b.type === "status");
    if (!lastStatusBlock?.status_info?.status) return;

    const status = lastStatusBlock.status_info.status as string;
    const phase = webContainer.phase;

    switch (status) {
      case "init":
        if (phase === "idle") {
          webContainer.startContainer();
          wcStartedRef.current = true;
        }
        break;
      case "generation_done":
        if (wcStartedRef.current &&
          (phase === "waiting_files" || phase === "installing" || phase === "idle")) {
          webContainer.startDevServer();
        }
        break;
    }
  }, [currentBlocks, sessionId, isLoading]);

  useEffect(() => {
    if (!sessionId ||
      (webContainer.phase !== "waiting_files" && webContainer.phase !== "installing")) {
      return;
    }

    const latestFiles = files.filter(f => f.path);
    if (latestFiles.length === 0) return;

    for (const fileInfo of latestFiles) {
      fetch(`http://localhost:9000/api/projects/${sessionId}/content?path=${encodeURIComponent(fileInfo.path)}`)
        .then(res => res.json())
        .then(data => {
          if (data.content) {
            webContainer.writeFile(fileInfo.path, data.content);
          }
        });
    }
  }, [files, sessionId, webContainer.phase]);

  useEffect(() => {
    if (webContainer.previewUrl) {
      setPreviewSource({ mode: 'url', url: webContainer.previewUrl });
      setPreviewOpen(true);
    }
  }, [webContainer.previewUrl]);

  const handleSelectVersion = (version: PageVersion) => {
    setPendingVersion(version);
  };

  const handleConfirmSwitch = async () => {
    if (!pendingVersion) return;
    await switchBaseVersion(pendingVersion.version);
    const res = await loadHtml(pendingVersion.version);
    if ('type' in res && res.type === "html") {
      setPreviewSource({ mode: 'html', html: res.html });
    }
    setPreviewOpen(true);
    setPendingVersion(null);
  };

  const handleFileSelect = (path: string) => {
    setSelectedFile(path);
  };

  return (
    <>
      <header className="flex items-center justify-end border-b border-gray-200 px-4 md:px-6 py-3 shrink-0 bg-white/95 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <VersionSelector
            versions={versions}
            currentBase={currentBase}
            onSelectVersion={handleSelectVersion}
          />
          <button
            onClick={() => setPreviewOpen(!previewOpen)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all duration-200 ${previewOpen
                ? "bg-black text-white"
                : "bg-gray-50 text-gray-700 hover:bg-gray-100"
              }`}
          >
            <Eye size={12} />
            预览
          </button>
          {webContainer.phase !== "idle" && (
            <span className={`ml-2 text-xs px-2.5 py-1 rounded-full ${webContainer.phase === "ready"
                ? "bg-emerald-50 text-emerald-600 border border-emerald-200"
                : webContainer.phase === "error"
                  ? "bg-red-50 text-red-600 border border-red-200"
                  : "bg-blue-50 text-blue-600 border border-blue-200 animate-pulse"
              }`}>
              {webContainer.statusMessage}
            </span>
          )}
        </div>
      </header>

      <main className="flex-1 overflow-hidden bg-gray-50/50">
        <ResizableLayout
          leftPanel={
            <ChatPanelV2
              messages={messages}
              isLoading={isLoading}
              currentBlocks={currentBlocks}
              completedTurns={completedTurns}
              onSendMessage={sendMessage}
              onStopGeneration={stopGeneration}
            />
          }
          rightPanel={
            <PreviewPanel
              previewSource={previewSource}
              files={files as any}
              selectedFile={selectedFile}
              onFileSelect={handleFileSelect}
              isOpen={previewOpen}
              onClose={() => setPreviewOpen(false)}
            />
          }
          isRightOpen={previewOpen}
        />
      </main>

      {pendingVersion && (
        <BaseConfirmDialog
          targetVersion={pendingVersion}
          currentBase={currentBase}
          onConfirm={handleConfirmSwitch}
          onCancel={() => setPendingVersion(null)}
        />
      )}

      <MockDebugPanel />
    </>
  );
}
```

---

### Task 3: 更新入口文件 main.tsx

**Files:**
- Modify: `frontend/src/main.tsx`
- Delete: `frontend/src/App.tsx`

- [ ] **Step 1: 读取当前 main.tsx 内容**

```bash
cat frontend/src/main.tsx
```

Expected: 显示当前的入口文件内容

- [ ] **Step 2: 更新 main.tsx 使用 RouterProvider**

```typescript
import { StrictMode } from 'react';
import ReactDOM from 'react-dom/client';
import { RouterProvider } from '@tanstack/react-router';
import { router } from './routes/routeTree';
import './index.css';

const rootElement = document.getElementById('root')!;
if (!rootElement.innerHTML) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <StrictMode>
      <RouterProvider router={router} />
    </StrictMode>
  );
}
```

- [ ] **Step 3: 删除 App.tsx**

```bash
rm frontend/src/App.tsx
```

---

### Task 4: 添加路由类型定义

**Files:**
- Create: `frontend/src/routes/types.d.ts`

- [ ] **Step 1: 创建路由参数类型定义**

```typescript
import type { Session } from '../services/api';

export interface HomePageLoaderData {
  sessions: Session[];
}

export interface ChatPageLoaderData {
  session: Session;
  messages: any[];
}
```

---

### Task 5: 验证和测试

**Files:**
- Test: 所有路由功能

- [ ] **Step 1: 运行 TypeScript 类型检查**

```bash
cd frontend && npm run build
```

Expected: 无类型错误

- [ ] **Step 2: 启动开发服务器测试**

```bash
cd frontend && npm run dev
```

Expected: 访问 http://localhost:6003/ 显示首页

- [ ] **Step 3: 测试首页路由**

URL: http://localhost:6003/
Expected: 显示会话列表页面

- [ ] **Step 4: 测试对话页路由**

URL: http://localhost:6003/chat/test-session-id
Expected: 显示对话页面，Header 中的预览和版本选择器正常工作

- [ ] **Step 5: 测试路由导航**

在首页点击会话或新建会话
Expected: 正确跳转到 /chat/:sessionId

---

## 验收标准

- [ ] TanStack Router 依赖安装成功
- [ ] routes 目录结构正确
- [ ] 首页 `/` 正常显示会话列表
- [ ] 对话页 `/chat/:sessionId` 正常显示聊天和预览
- [ ] 路由参数 `$sessionId` 正确传递
- [ ] TypeScript 类型检查通过
- [ ] App.tsx 已删除
- [ ] main.tsx 使用 RouterProvider
