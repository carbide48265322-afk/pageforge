## 用户需求
{user_message}

## 计划步骤
{plan_steps}

## UI 风格配置
{ui_style_config}

## 生成要求

### 技术约束
1. React 19 + TypeScript（strict 模式）+ Tailwind CSS + Vite
2. 函数组件 + Hooks（不使用 class 组件）
3. 组件 Props 必须定义 TypeScript interface
4. 副作用放 useEffect，事件处理用 useCallback
5. 样式优先使用 Tailwind CSS 类名，动态值可用 style
6. 不使用 eval()、document.write()、innerHTML、window.parent、window.top

### 输出格式（必须严格遵守）
输出一个 JSON 数组，每个元素代表一个文件：
```json
[
  {
    "path": "src/App.tsx",
    "content": "import React from 'react';\n\ninterface AppProps {}\n\nfunction App() {\n  return <div>Hello</div>;\n}\n\nexport default App;"
  },
  {
    "path": "src/components/Header.tsx",
    "content": "import React from 'react';\n\ninterface HeaderProps {\n  title: string;\n}\n\nexport default function Header({ title }: HeaderProps) {\n  return <header className=\"bg-white shadow\"><h1>{title}</h1></header>;\n}"
  }
]
```

### 文件规范
- 必须包含：package.json、index.html、vite.config.ts、tsconfig.json、src/main.tsx、src/App.tsx、src/index.css
- 根据需求添加组件文件（src/components/*.tsx）
- 每个文件内容必须完整可运行，包含所有 import
- 文件路径使用相对路径（如 src/App.tsx）

### 风格约束
- 严格遵循上方 UI 风格配置中的颜色系统（Tailwind class）
- 遵守反模式约束（禁止事项）
- 设计哲学：简洁有力，避免千篇一律的 AI 生成感

### 注意
- 只返回 JSON 数组，不要包含 markdown 代码块标记
- 文件内容中的换行符用 \n 表示，不要使用真实换行
- 确保 JSON 格式正确，能被 JSON.parse() 解析
