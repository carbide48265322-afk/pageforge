# 路由架构设计文档

**日期**: 2026-05-05
**作者**: PageForge Team
**状态**: 待审核

## 1. 概述

### 1.1 背景
当前 PageForge 前端是一个单页面应用，所有功能都在一个 App.tsx 组件中。为了更好地管理会话历史和页面导航，需要引入路由系统。

### 1.2 目标
- 分离首页和对话页面
- 支持通过路由访问特定会话
- 保持现有功能完整
- 遵循标准 TanStack Router v1 架构

## 2. 路由设计

### 2.1 路由结构

| 路由 | 组件文件 | 说明 |
|------|----------|------|
| `/` | `index.tsx` | 首页，展示会话列表，可创建新会话 |
| `/chat/:sessionId` | `chat.$sessionId.tsx` | 对话页面，包含 AI 聊天面板和实时预览 |

### 2.2 技术选型

- **路由库**: TanStack Router v1
- **原因**:
  - 类型安全，路由参数自动推断
  - 轻量高性能
  - 现代化 API，与 React 18 良好兼容
  - 遵循官方推荐的项目结构

## 3. 项目结构

```
frontend/src/
├── routes/                     # 路由组件目录（新增）
│   ├── __root.tsx             # 根布局（导航栏、Outlet）
│   ├── index.tsx              # 首页 /
│   └── chat.$sessionId.tsx    # 对话页 /chat/:sessionId
├── components/                 # 业务组件（保持不变）
│   ├── ChatPanelV2.tsx
│   ├── PreviewPanel.tsx
│   └── ...
├── hooks/                      # 现有 hooks（保持不变）
│   ├── useSession.ts
│   ├── useSSEv2.ts
│   └── useWebContainer.ts
├── services/                   # 现有服务（保持不变）
├── main.tsx                    # 入口文件（调整）
├── App.tsx                     # 删除
└── index.css                   # 全局样式（保持不变）
```

## 4. 核心文件设计

### 4.1 根布局 (routes/__root.tsx)

TanStack Router 标准模式：使用 `__root.tsx` 定义全局布局，包含导航栏和 Outlet。

**功能**:
- 全局导航栏（品牌 Logo、状态指示器）
- 全局工具栏（版本选择器、预览开关）
- Outlet 渲染子路由

### 4.2 首页 (routes/index.tsx)

TanStack Router 标准模式：文件名为 `index.tsx`，对应路径 `/`。

**功能**:
- 展示会话列表
- 创建新会话按钮
- 点击会话跳转到 `/chat/:sessionId`

### 4.3 对话页 (routes/chat.$sessionId.tsx)

TanStack Router 标准模式：文件名 `chat.$sessionId.tsx` 自动映射到路由 `/chat/:sessionId`。

**功能**:
- 现有 App.tsx 的业务逻辑完整迁移
- 从路由参数 `$sessionId` 获取会话 ID
- 包含聊天面板和预览面板

### 4.4 入口文件 (main.tsx)

```typescript
import { StrictMode } from 'react'
import ReactDOM from 'react-dom/client'
import { RouterProvider } from '@tanstack/react-router'
import { router } from './routes'

const rootElement = document.getElementById('root')!
if (!rootElement.innerHTML) {
  const root = ReactDOM.createRoot(rootElement)
  root.render(
    <StrictMode>
      <RouterProvider router={router} />
    </StrictMode>
  )
}
```

### 4.5 App.tsx

**变更**: 删除

## 5. 路由配置

路由通过文件命名约定自动生成：

```
routes/
├── __root.tsx          → 根布局
├── index.tsx          → /
├── chat.$sessionId.tsx → /chat/:sessionId
```

TanStack Router 自动从文件名生成路由：
- `index.tsx` → `/`
- `chat.$sessionId.tsx` → `/chat/:sessionId`（`$sessionId` 为动态参数）

## 6. 数据流程

### 6.1 首页流程
1. 用户访问 `/`
2. `index.tsx` 加载会话列表
3. 用户点击「创建新会话」或选择历史会话
4. 使用 `router.navigate()` 跳转到 `/chat/:sessionId`

### 6.2 对话流程
1. 用户访问 `/chat/:sessionId`
2. `chat.$sessionId.tsx` 从路由 hook 获取 `sessionId`
3. 使用 `useSession(sessionId)` 加载会话数据
4. 展示聊天界面和预览

## 7. 实现计划

### 阶段 1: 依赖安装
- 安装 `@tanstack/react-router`

### 阶段 2: 创建路由目录结构
- 创建 `routes/` 目录
- 创建 `routes/__root.tsx`
- 创建 `routes/index.tsx`
- 创建 `routes/chat.$sessionId.tsx`

### 阶段 3: 迁移代码
- 将 App.tsx 的 Header 部分迁移到 `__root.tsx`
- 将 App.tsx 的业务逻辑迁移到 `chat.$sessionId.tsx`
- 实现 `index.tsx` 的会话列表功能

### 阶段 4: 更新入口文件
- 修改 `main.tsx` 使用 RouterProvider
- 删除 `App.tsx`

### 阶段 5: 测试
- 验证路由跳转
- 验证功能完整性
- 类型检查无错误

## 8. 注意事项

- 保持现有业务逻辑完整
- 遵循 TanStack Router 文件命名约定
- 使用 TypeScript 类型安全
- 添加必要的路由守卫（可选）

## 9. 验收标准

- [ ] 可以正常访问首页 `/`
- [ ] 可以创建新会话并跳转到 `/chat/:sessionId`
- [ ] 对话页功能完整可用
- [ ] 路由参数 `$sessionId` 正确传递
- [ ] 类型安全无错误
- [ ] 现有 WebContainer 功能正常
