# React 项目转换指南

## 🎯 概述

WebContainer 现在支持将 AI 生成的 HTML 页面转换为完整的 React 项目。这不仅仅是简单的 HTML 到 JSX 转换，而是创建一个功能完整的现代 React 应用，包含：

- ✅ 完整的 React 18 + Vite 项目结构
- ✅ 自动 HTML 到 JSX 转换
- ✅ JavaScript 到 React Hooks 转换
- ✅ 状态管理和数据持久化
- ✅ 现代开发工具链配置

## 🔄 转换流程

### 1. HTML 解析阶段

**输入**: AI 生成的 HTML 页面
```html
<!DOCTYPE html>
<html>
<head>
    <style>/* CSS 样式 */</style>
</head>
<body>
    <div class="app">
        <h1>应用标题</h1>
        <button onclick="handleClick()">点击</button>
    </div>
    <script>
        function handleClick() {
            // JavaScript 逻辑
        }
    </script>
</body>
</html>
```

**解析过程**:
1. 提取 `<style>` 内容 → 转换为 CSS 模块
2. 提取 `<script>` 内容 → 转换为 React Hooks
3. 分析 HTML 结构 → 转换为 JSX 组件
4. 识别交互逻辑 → 转换为状态管理

### 2. 项目结构生成

**输出**: 完整的 React 项目结构
```
react-project/
├── package.json              # 项目配置和依赖
├── vite.config.js            # Vite 构建配置
├── index.html                # 入口 HTML 文件
├── src/
│   ├── main.jsx             # React 入口文件
│   ├── App.jsx              # 主组件 (转换后的 JSX)
│   └── index.css            # 全局样式
└── public/
    └── vite.svg             # 应用图标
```

## 🛠️ 技术实现

### HTML 到 JSX 转换

**转换规则**:

| HTML | JSX |
|------|-----|
| `class="btn"` | `className="btn"` |
| `for="input"` | `htmlFor="input"` |
| `onclick="func()"` | `onClick={func}` |
| `style="color: red"` | `style={{color: 'red'}}` |

**示例转换**:

**HTML**:
```html
<div class="container">
    <button onclick="handleClick()" class="btn">
        点击我
    </button>
</div>
```

**JSX**:
```jsx
<div className="container">
    <button onClick={handleClick} className="btn">
        点击我
    </button>
</div>
```

### JavaScript 到 React Hooks 转换

**状态管理转换**:

| JavaScript | React Hooks |
|------------|-------------|
| `let count = 0;` | `const [count, setCount] = useState(0);` |
| `localStorage.setItem()` | `useEffect(() => localStorage.setItem())` |
| `document.getElementById()` | `useRef()` |

**示例转换**:

**JavaScript**:
```javascript
let todos = JSON.parse(localStorage.getItem('todos') || '[]');

function addTodo(text) {
    todos.push({ id: Date.now(), text, completed: false });
    localStorage.setItem('todos', JSON.stringify(todos));
    renderTodos();
}
```

**React Hooks**:
```jsx
const [todos, setTodos] = useState(() => {
    const saved = localStorage.getItem('todos');
    return saved ? JSON.parse(saved) : [];
});

const addTodo = (text) => {
    const newTodos = [...todos, { id: Date.now(), text, completed: false }];
    setTodos(newTodos);
};

useEffect(() => {
    localStorage.setItem('todos', JSON.stringify(todos));
}, [todos]);
```

## 📦 项目配置

### package.json 配置

```json
{
  "name": "pageforge-react-app",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "lint": "eslint . --ext js,jsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "lucide-react": "^0.344.0"
  },
  "devDependencies": {
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.2.1",
    "eslint": "^8.56.0",
    "eslint-plugin-react": "^7.34.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "vite": "^5.1.0"
  }
}
```

### Vite 配置

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173
  }
})
```

## 🎨 实际转换示例

### 示例 1: 待办事项应用

**输入 HTML**:
```html
<div class="app">
    <h1>📝 待办事项</h1>
    <div class="input-group">
        <input type="text" id="todoInput" placeholder="添加新任务...">
        <button onclick="addTodo()">添加</button>
    </div>
    <ul id="todoList"></ul>
</div>

<script>
    let todos = JSON.parse(localStorage.getItem('todos') || '[]');
    
    function addTodo() {
        const input = document.getElementById('todoInput');
        if (input.value.trim()) {
            todos.push({ id: Date.now(), text: input.value, completed: false });
            input.value = '';
            saveAndRender();
        }
    }
    
    function saveAndRender() {
        localStorage.setItem('todos', JSON.stringify(todos));
        renderTodos();
    }
</script>
```

**输出 React 组件**:
```jsx
import React, { useState, useEffect } from 'react'

function App() {
  const [todos, setTodos] = useState(() => {
    const saved = localStorage.getItem('todos');
    return saved ? JSON.parse(saved) : [];
  })
  const [newTodo, setNewTodo] = useState('')

  const addTodo = () => {
    if (newTodo.trim()) {
      const newTodos = [...todos, { 
        id: Date.now(), 
        text: newTodo, 
        completed: false 
      }];
      setTodos(newTodos);
      setNewTodo('');
    }
  }

  const toggleTodo = (id) => {
    const newTodos = todos.map(todo =>
      todo.id === id ? { ...todo, completed: !todo.completed } : todo
    );
    setTodos(newTodos);
  }

  const deleteTodo = (id) => {
    const newTodos = todos.filter(todo => todo.id !== id);
    setTodos(newTodos);
  }

  useEffect(() => {
    localStorage.setItem('todos', JSON.stringify(todos));
  }, [todos])

  return (
    <div className="app">
      <h1>📝 待办事项</h1>
      <div className="input-group">
        <input 
          type="text" 
          value={newTodo}
          onChange={(e) => setNewTodo(e.target.value)}
          placeholder="添加新任务..."
        />
        <button onClick={addTodo}>添加</button>
      </div>
      <ul className="todo-list">
        {todos.map(todo => (
          <li key={todo.id} className={`todo-item ${todo.completed ? 'completed' : ''}`}>
            <input 
              type="checkbox" 
              checked={todo.completed}
              onChange={() => toggleTodo(todo.id)}
            />
            <span className={todo.completed ? 'completed' : ''}>{todo.text}</span>
            <button onClick={() => deleteTodo(todo.id)}>删除</button>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default App
```

### 示例 2: 计数器应用

**输入 HTML**:
```html
<div class="counter">
    <h1>计数器</h1>
    <div id="count" class="count">0</div>
    <div class="buttons">
        <button onclick="changeCount(-1)">-</button>
        <button onclick="resetCount()">重置</button>
        <button onclick="changeCount(1)">+</button>
    </div>
</div>

<script>
    let count = parseInt(localStorage.getItem('counter') || '0');
    
    function changeCount(delta) {
        count += delta;
        localStorage.setItem('counter', count.toString());
        updateDisplay();
    }
    
    function resetCount() {
        count = 0;
        localStorage.setItem('counter', '0');
        updateDisplay();
    }
</script>
```

**输出 React 组件**:
```jsx
import React, { useState, useEffect } from 'react'

function App() {
  const [count, setCount] = useState(() => {
    return parseInt(localStorage.getItem('counter') || '0');
  })

  const changeCount = (delta) => {
    setCount(prevCount => prevCount + delta);
  }

  const resetCount = () => {
    setCount(0);
  }

  useEffect(() => {
    localStorage.setItem('counter', count.toString());
  }, [count])

  return (
    <div className="counter">
      <h1>计数器</h1>
      <div 
        className="count"
        style={{ transform: count !== 0 ? 'scale(1.1)' : 'scale(1)' }}
      >
        {count}
      </div>
      <div className="buttons">
        <button onClick={() => changeCount(-1)}>-</button>
        <button onClick={resetCount}>重置</button>
        <button onClick={() => changeCount(1)}>+</button>
      </div>
    </div>
  )
}

export default App
```

## 🚀 使用流程

### 1. 创建 React 项目

```bash
# 1. 创建项目
POST /api/webcontainer/projects?session_id=abc123&version=1

# 响应
{
  "project_path": "/tmp/pageforge_webcontainer/abc123/v1",
  "files": ["package.json", "vite.config.js", "index.html", "src/main.jsx", "src/App.jsx", "src/index.css"],
  "status": "created"
}
```

### 2. 安装依赖

```bash
# 安装 React 依赖
POST /api/webcontainer/projects/abc123/1/install

# 响应
{
  "status": "success",
  "message": "依赖安装成功",
  "stdout": "added 245 packages in 12.3s"
}
```

### 3. 启动开发服务器

```bash
# 启动 Vite 开发服务器
POST /api/webcontainer/projects/abc123/1/start

# 响应
{
  "status": "success",
  "message": "开发服务器启动成功",
  "port": 5173,
  "url": "http://localhost:5173",
  "pid": 12345
}
```

### 4. 访问应用

```bash
# 访问 React 应用
GET http://localhost:5173

# 输出
VITE v5.0.0  ready in 1234 ms

➜  Local:   http://localhost:5173/
➜  Network: http://192.168.1.100:5173/
```

## 🎯 优势特点

### 🔧 技术优势
- **现代技术栈**: React 18 + Vite + ES Modules
- **完整工具链**: ESLint + 热重载 + 生产构建
- **类型安全**: TypeScript 支持
- **性能优化**: 代码分割 + 懒加载

### 🚀 开发体验
- **快速启动**: 零配置，开箱即用
- **热重载**: 实时预览修改
- **调试友好**: 完整的开发工具
- **生产就绪**: 优化的构建输出

### 💡 功能特性
- **状态管理**: 自动转换为 React Hooks
- **数据持久化**: localStorage 自动处理
- **响应式设计**: 现代 CSS 支持
- **组件化**: 可复用的组件结构

## 📈 性能对比

| 指标 | 传统 HTML | React 项目 |
|------|-----------|------------|
| 启动时间 | 1-2s | 2-3s |
| 热重载 | 不支持 | ✅ 支持 |
| 状态管理 | 手动 | ✅ 自动 |
| 代码维护 | 困难 | ✅ 容易 |
| 扩展性 | 有限 | ✅ 强大 |

## 🎉 总结

WebContainer 的 React 项目转换功能为 AI 生成的页面提供了：

1. **🚀 现代化升级**: 从静态 HTML 到动态 React 应用
2. **🔧 完整工具链**: 包含开发、构建、部署全流程
3. **📱 优秀体验**: 热重载、状态管理、响应式设计
4. **🛠️ 易于维护**: 组件化、模块化、可复用

这使得 AI 生成的页面不仅仅是静态展示，而是功能完整的现代 Web 应用！