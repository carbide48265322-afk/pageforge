# React 模板快速开始指南

## 🚀 快速开始

### 1. 启动服务

```bash
# 启动后端服务
cd backend
python -m uvicorn app.main:app --reload

# 启动前端服务
cd frontend
npm run dev
```

### 2. 使用 API 创建 React 项目

```javascript
// 示例：创建聊天应用
const sessionId = 'session_123';
const version = 1;
const templateName = 'chat';

// 从模板创建项目
const response = await fetch('/api/webcontainer/projects/template', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: sessionId,
    version: version,
    template_name: templateName
  })
});

const result = await response.json();
console.log('项目创建成功:', result.files.length, '个文件');
```

### 3. 使用 React Hook

```jsx
import { useWebContainer } from './services/webcontainer_api';

function MyComponent() {
  const {
    state,
    isReady,
    serverUrl,
    initializeFromTemplate
  } = useWebContainer();

  const createProject = async () => {
    await initializeFromTemplate('session_123', 1, 'todo');
  };

  if (isReady) {
    return (
      <iframe src={serverUrl} style={{ width: '100%', height: '600px' }} />
    );
  }

  return (
    <div>
      <button onClick={createProject}>创建待办事项应用</button>
      <div>状态: {state?.status}</div>
    </div>
  );
}
```

## 📱 可用模板

### 基础模板
- **counter**: 🗂️ 计数器应用
- **todo**: ✅ 待办事项管理
- **calculator**: 🧮 计算器
- **weather**: 🌤️ 天气查询

### 高级模板
- **chat**: 💬 聊天应用 (AI助手)
- **blog**: 📝 博客系统
- **charts**: 📊 数据可视化

## 🎯 常用操作

### 获取模板列表
```javascript
const templates = await fetch('/api/webcontainer/templates').then(r => r.json());
console.log('可用模板:', Object.keys(templates));
```

### 创建项目
```javascript
// 创建博客系统
await initializeFromTemplate(sessionId, version, 'blog');

// 创建聊天应用
await initializeFromTemplate(sessionId, version, 'chat');

// 创建数据图表
await initializeFromTemplate(sessionId, version, 'charts');
```

### 监控进度
```javascript
const { state } = useWebContainer();

// 状态包括:
// - idle: 空闲
// - creating: 创建中
// - installing: 安装依赖中
// - starting: 启动服务器中
// - running: 运行中
// - error: 错误

console.log('当前状态:', state?.status);
```

## 🔧 开发指南

### 添加新模板

1. **在 WebContainerService 中添加模板方法**:
```python
def _generate_my_app(self, config):
    return '''
import React, { useState } from 'react'

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600">
      <h1 className="text-white text-4xl font-bold text-center pt-20">
        我的应用
      </h1>
    </div>
  )
}

export default App
    '''
```

2. **添加模板配置**:
```python
def _get_my_template_config(self):
    return {
        "name": "my-app",
        "template": "my",
        "dependencies": ["react", "react-dom"],
        "features": ["hooks", "responsive"]
    }
```

3. **更新模板路由**:
```python
templates = {
    "my": self._get_my_template_config(),
    # ... 其他模板
}
```

### 自定义样式

所有模板都使用 Tailwind CSS 类名，可以轻松自定义：

```jsx
// 修改背景
<div className="min-h-screen bg-gradient-to-br from-green-400 to-blue-500">

// 修改按钮样式
<button className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg">

// 添加动画
<div className="animate-pulse transition-all duration-300">
```

## 🐛 常见问题

### 1. 项目创建失败
```javascript
// 检查错误信息
const { state } = useWebContainer();
if (state?.status === 'error') {
  console.error('错误详情:', state.error);
}
```

### 2. 依赖安装失败
- 检查网络连接
- 确认 package.json 配置正确
- 查看后端日志获取详细信息

### 3. 服务器启动失败
- 确认端口 6000 未被占用
- 检查 node_modules 是否完整
- 查看浏览器控制台错误信息

## 📋 API 参考

### 端点列表

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/webcontainer/templates` | 获取模板列表 |
| POST | `/api/webcontainer/projects/template` | 从模板创建项目 |
| GET | `/api/webcontainer/projects/{session_id}/{version}/status` | 获取项目状态 |
| POST | `/api/webcontainer/projects/{session_id}/{version}/install` | 安装依赖 |
| POST | `/api/webcontainer/projects/{session_id}/{version}/start` | 启动服务器 |
| GET | `/api/webcontainer/projects/{session_id}/{version}/files` | 获取项目文件 |
| DELETE | `/api/webcontainer/projects/{session_id}/{version}` | 清理项目 |

### 请求示例

```javascript
// 创建项目
fetch('/api/webcontainer/projects/template', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: 'test-session',
    version: 1,
    template_name: 'todo'
  })
});

// 安装依赖
fetch('/api/webcontainer/projects/test-session/1/install', {
  method: 'POST'
});

// 启动服务器
fetch('/api/webcontainer/projects/test-session/1/start', {
  method: 'POST'
});
```

## 🎨 模板定制

### 修改应用名称
```javascript
// 在 package.json 中
{
  "name": "my-custom-app",
  "description": "我的自定义应用"
}
```

### 添加新依赖
```javascript
// 在 package.json 的 dependencies 中添加
{
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "my-library": "^1.0.0"
  }
}
```

### 自定义组件
```jsx
// 在 src/components/ 目录下创建新组件
function MyComponent() {
  return <div className="p-4 bg-white rounded-lg shadow">我的组件</div>;
}

// 在 App.jsx 中使用
import MyComponent from './components/MyComponent';

function App() {
  return (
    <div>
      <MyComponent />
    </div>
  );
}
```

## 🚀 生产部署

### 构建生产版本
```javascript
// 调用构建 API
const buildResult = await webContainerAPI.buildProject();

if (buildResult.status === 'success') {
  console.log('构建成功:', buildResult.build_files);
}
```

### 部署到静态主机
```bash
# 构建后的文件在 dist/ 目录
npm run build

# 部署 dist/ 目录到 Vercel, Netlify 等
```

---

*快速开始指南 v1.0*
*最后更新: 2026年4月29日*