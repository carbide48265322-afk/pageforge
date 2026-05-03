# 前端与后端功能对应关系文档

## 📋 概述

本文档详细说明 PageForge 项目中前端与后端功能的对应关系，确保 WebContainer 的 React 模板功能在前后端之间完全同步。

## 🔄 功能对应总览

### ✅ 已完成的功能对应

| 前端功能 | 后端功能 | 状态 | 说明 |
|---------|---------|------|------|
| `initializeFromTemplate()` | `create_project_from_template()` | ✅ | React 模板初始化 |
| `getTemplates()` | `get_available_templates()` | ✅ | 获取模板列表 |
| `useWebContainer` Hook | WebContainerService | ✅ | 状态管理 |
| API 接口封装 | RESTful API 端点 | ✅ | 完整 API 对应 |
| ReactTemplateDemo 组件 | 7个 React 模板 | ✅ | 演示界面 |
| WebContainerPanel 更新 | 模板选择器集成 | ✅ | UI 界面支持 |

## 🎯 核心功能对应详情

### 1. React 模板创建流程

#### 前端调用链
```typescript
// 1. 用户点击启动 React 演示
// 2. 调用 initializeFromTemplate()
await webContainerAPI.initializeFromTemplate(sessionId, version, 'todo');

// 3. 内部调用 API
const result = await createReactProjectFromTemplate(sessionId, version, templateName);

// 4. 更新状态
setState({ status: 'installing' });
```

#### 后端处理链
```python
# 1. API 端点接收请求
@router.post("/projects/template")
async def create_project_from_template(request: CreateFromTemplateRequest):

# 2. 服务层处理
webcontainer_service.create_project_from_template(session_id, version, template_name)

# 3. 模板生成器
_generate_todo_app(config) -> str
```

### 2. 模板列表获取

#### 前端
```typescript
// API 函数
export async function getAvailableTemplates(): Promise<TemplateList>

// Hook 封装
const { getTemplates } = useWebContainer();
const templates = await getTemplates();

// UI 显示
<select value={selectedTemplate} onChange={...}>
  {Object.entries(availableTemplates).map(([key, template]) => (
    <option value={key}>{template.name}</option>
  ))}
</select>
```

#### 后端
```python
# API 端点
@router.get("/templates")
async def get_available_templates():
    templates = {
        "counter": {"name": "计数器", "description": "...", "features": [...]},
        "todo": {"name": "待办事项", "description": "...", "features": [...]},
        # ... 其他模板
    }
    return templates
```

## 🔧 API 接口对应表

### React 模板相关接口

| 前端 API | 后端端点 | HTTP 方法 | 功能 |
|---------|---------|-----------|------|
| `createReactProjectFromTemplate()` | `/api/webcontainer/projects/template` | POST | 从模板创建项目 |
| `getAvailableTemplates()` | `/api/webcontainer/templates` | GET | 获取模板列表 |
| `getWebContainerStatus()` | `/api/webcontainer/projects/{id}/{v}/status` | GET | 获取项目状态 |
| `installWebContainerDependencies()` | `/api/webcontainer/projects/{id}/{v}/install` | POST | 安装依赖 |
| `startWebContainerServer()` | `/api/webcontainer/projects/{id}/{v}/start` | POST | 启动服务器 |

### 传统 HTML 接口 (保持兼容)

| 前端 API | 后端端点 | HTTP 方法 | 功能 |
|---------|---------|-----------|------|
| `createWebContainerProject()` | `/api/webcontainer/projects` | POST | 创建 HTML 项目 |
| `buildWebContainerProject()` | `/api/webcontainer/projects/{id}/{v}/build` | POST | 构建项目 |
| `getWebContainerFiles()` | `/api/webcontainer/projects/{id}/{v}/files` | GET | 获取文件列表 |

## 🎨 组件功能对应

### WebContainerPanel 组件

#### React 模式功能
- ✅ **模板选择器**: 下拉选择 React 模板
- ✅ **启动按钮**: 调用 `initializeFromTemplate()`
- ✅ **状态显示**: 显示模板初始化进度
- ✅ **iframe 预览**: 显示 React 应用运行效果
- ✅ **控制台输出**: 显示运行日志

#### 传统 HTML 模式功能 (保持兼容)
- ✅ **HTML 预览**: iframe 显示 HTML 内容
- ✅ **源码查看**: 语法高亮的 HTML 源码
- ✅ **响应式切换**: 桌面/平板/手机尺寸
- ✅ **复制下载**: HTML 源码操作

### ReactTemplateDemo 组件
- ✅ **模板展示**: 7个模板的卡片展示
- ✅ **功能介绍**: 每个模板的特点说明
- ✅ **一键启动**: 直接启动 React 演示
- ✅ **弹窗界面**: 独立的演示界面

## 📡 状态管理对应

### useWebContainer Hook

```typescript
interface WebContainerState {
    sessionId: string;
    version: number;
    status: 'idle' | 'creating' | 'installing' | 'starting' | 'running' | 'error';
    projectStatus?: WebContainerStatus;
    installResult?: InstallResult;
    serverResult?: ServerResult;
    error?: string;
}
```

### 后端状态对应

```python
class WebContainerService:
    def get_project_status(self, session_id: str, version: int) -> Dict[str, any]:
        return {
            "status": "ready" if has_node_modules else "created",
            "project_path": str(project_dir),
            "existing_files": existing_files,
            "missing_files": missing_files,
            "has_node_modules": has_node_modules,
            "dependencies": dependencies,
            "dev_dependencies": dev_dependencies
        }
```

## 🔄 数据流对应

### React 模板创建数据流

```
用户操作
   ↓
ReactTemplateDemo 组件
   ↓
initializeFromTemplate(sessionId, version, template)
   ↓
createReactProjectFromTemplate() API 调用
   ↓
POST /api/webcontainer/projects/template
   ↓
WebContainerService.create_project_from_template()
   ↓
_generate_*_app() 模板生成器
   ↓
返回项目文件结构
   ↓
前端状态更新
   ↓
iframe 显示 React 应用
```

## 🎯 模板功能对应

### 7个 React 模板前后端对应

| 模板名称 | 后端生成器 | 前端显示 | 特性 |
|---------|-----------|---------|------|
| `counter` | `_generate_counter_app()` | 计数器界面 | Hooks, localStorage |
| `todo` | `_generate_todo_app()` | 待办事项管理 | CRUD, 过滤 |
| `calculator` | `_generate_calculator_app()` | 计算器界面 | 数学运算 |
| `weather` | `_generate_weather_app()` | 天气查询 | 搜索, 数据展示 |
| `chat` | `_generate_chat_app()` | 聊天界面 | 实时消息, AI |
| `blog` | `_generate_blog_app()` | 博客系统 | 文章管理, 搜索 |
| `charts` | `_generate_charts_app()` | 数据图表 | 可视化, 动画 |

## 🔍 兼容性说明

### 双模式支持
- **React 模式**: 使用新的模板系统，创建完整 React 应用
- **HTML 模式**: 保持原有的 HTML 预览功能
- **无缝切换**: 通过 `reactMode` prop 控制

### 向后兼容
- ✅ 原有 HTML 功能完全保留
- ✅ 现有 API 接口保持不变
- ✅ 用户界面统一体验
- ✅ 状态管理兼容两种模式

## 🧪 测试验证

### 前端测试点
- ✅ 模板选择器正常工作
- ✅ React 模式启动流程
- ✅ iframe 正确显示 React 应用
- ✅ 状态更新和错误处理
- ✅ 与传统 HTML 模式的切换

### 后端测试点
- ✅ 模板 API 返回正确数据
- ✅ 项目创建生成正确文件
- ✅ 依赖安装成功
- ✅ 服务器启动正常
- ✅ 错误处理和清理

## 🚀 部署检查清单

### 前端部署
- ✅ 所有新组件已导入
- ✅ API 接口已更新
- ✅ 状态管理已集成
- ✅ 用户界面已更新
- ✅ 错误处理已添加

### 后端部署
- ✅ 所有模板已实现
- ✅ API 端点已添加
- ✅ 服务逻辑已更新
- ✅ 依赖管理已配置
- ✅ 测试脚本已创建

## 📈 性能考虑

### 前端优化
- ✅ 懒加载 React 演示组件
- ✅ 模板列表缓存
- ✅ 状态更新优化
- ✅ iframe 加载优化

### 后端优化
- ✅ 模板生成缓存
- ✅ 文件操作异步处理
- ✅ 资源清理机制
- ✅ 错误重试机制

## 🔮 未来扩展

### 计划中的功能
1. **自定义模板**: 用户创建和保存模板
2. **模板市场**: 在线模板分享
3. **主题系统**: 多主题支持
4. **部署集成**: 一键部署到云平台

### 扩展性设计
- ✅ 模块化模板系统
- ✅ 插件化架构
- ✅ 配置驱动开发
- ✅ API 版本管理

---

*前后端功能对应文档 v1.0*
*最后更新: 2026年4月29日*
*状态: ✅ 功能完全对应*