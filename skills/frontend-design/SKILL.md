---
name: frontend-design
description: React 项目工程规范。定义项目结构、代码风格、组件约定和 Tailwind CSS 使用规范，确保生成的代码可维护、可构建。
---

# frontend-design — React 项目工程规范

本 Skill 定义 PageForge 生成的 React 项目的技术规范，确保代码结构统一、可维护、可构建。

## 技术栈（固定）

- React 18+ 函数组件 + Hooks
- TypeScript（strict 模式）
- Vite 构建
- Tailwind CSS 样式

## 项目结构（固定）

```
src/
├── main.tsx              # 入口，不要修改
├── App.tsx               # 根组件，路由挂载点
├── components/           # 可复用组件（PascalCase 命名）
│   └── *.tsx
├── pages/                # 页面级组件
│   └── *.tsx
├── hooks/                # 自定义 hooks
│   └── use*.ts
├── utils/                # 工具函数
│   └── *.ts
├── types/                # TypeScript 类型定义
│   └── *.ts
└── styles/
    └── global.css        # Tailwind 指令 + CSS 变量
```

## 代码规范

### 组件
- 只使用函数组件 + Hooks，禁止 class 组件
- 每个 .tsx 文件只导出一个主组件
- 组件文件名 PascalCase（Header.tsx、HeroSection.tsx）
- Props 必须定义 TypeScript interface，文件内导出
- 组件必须有默认导出，类型可具名导出

### 样式
- 只使用 Tailwind CSS class，禁止内联 style
- 复杂样式可提取到 CSS Modules（*.module.css）
- 禁止硬编码颜色值，使用 Tailwind 自定义色或 CSS 变量
- 响应式优先使用 Tailwind 断点（sm/md/lg/xl）

### 命名
- 组件文件：PascalCase（Header.tsx）
- hooks 文件：camelCase + use 前缀（useData.ts）
- 工具函数：camelCase（formatDate.ts）
- 类型文件：PascalCase（ApiTypes.ts）

### Import
- 使用相对路径：`import { Header } from '../components/Header'`
- React hooks 从 'react' 导入
- 第三方库从包名直接导入
- 禁止循环依赖

## 脚手架已有文件（禁止生成/覆盖）

以下文件由 `npm create vite` 和 `npx tailwindcss init` 生成，LLM 不得覆盖：

- package.json
- tsconfig.json / tsconfig.app.json / tsconfig.node.json
- vite.config.ts
- tailwind.config.js / tailwind.config.ts
- postcss.config.js
- index.html
- src/main.tsx（除非有特殊需求）
- src/vite-env.d.ts

## 生成流程约束

1. 先调用 get_project_context 获取当前项目文件树
2. 检查已生成文件列表，避免重复和遗漏
3. 生成文件时确保 import 路径与实际文件位置匹配
4. 生成完毕后执行 npm run build 验证
