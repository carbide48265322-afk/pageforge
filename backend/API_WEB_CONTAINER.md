# WebContainer API 文档

## 概述

WebContainer API 提供了管理浏览器内项目运行环境的功能，允许在服务器端创建、配置和管理 WebContainer 项目。

## 基础信息

- **基础路径**: `/api/webcontainer`
- **认证**: 无需认证（通过 session_id 和 version 参数识别）
- **数据格式**: JSON

## API 端点

### 1. 创建项目

创建一个新的 WebContainer 项目。

**端点**: `POST /api/webcontainer/projects`

**参数**:
- `session_id` (string, required): 会话 ID
- `version` (int, required): 版本号

**示例请求**:
```bash
curl -X POST "http://localhost:9565/api/webcontainer/projects?session_id=abc123&version=1"
```

**成功响应**:
```json
{
  "project_path": "/tmp/pageforge_webcontainer/abc123/v1",
  "files": ["index.html", "package.json", "src/style.css", "src/main.js"],
  "status": "created"
}
```

### 2. 获取项目状态

获取指定项目的当前状态。

**端点**: `GET /api/webcontainer/projects/{session_id}/{version}/status`

**示例请求**:
```bash
curl "http://localhost:9565/api/webcontainer/projects/abc123/1/status"
```

**成功响应**:
```json
{
  "status": "ready",
  "project_path": "/tmp/pageforge_webcontainer/abc123/v1",
  "existing_files": ["index.html", "package.json", "src/style.css", "src/main.js"],
  "missing_files": [],
  "has_node_modules": true,
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "dev_dependencies": {
    "vite": "^5.0.0"
  }
}
```

### 3. 安装依赖

为项目安装 npm 依赖。

**端点**: `POST /api/webcontainer/projects/{session_id}/{version}/install`

**示例请求**:
```bash
curl -X POST "http://localhost:9565/api/webcontainer/projects/abc123/1/install"
```

**成功响应**:
```json
{
  "status": "success",
  "message": "依赖安装成功",
  "stdout": "added 145 packages in 15.2s"
}
```

**错误响应**:
```json
{
  "status": "error",
  "message": "依赖安装失败",
  "error": "npm ERR! code ERESOLVE\nnpm ERR! ERESOLVE unable to resolve dependency tree"
}
```

### 4. 启动开发服务器

启动项目的开发服务器。

**端点**: `POST /api/webcontainer/projects/{session_id}/{version}/start`

**示例请求**:
```bash
curl -X POST "http://localhost:9565/api/webcontainer/projects/abc123/1/start"
```

**成功响应**:
```json
{
  "status": "success",
  "message": "开发服务器启动成功",
  "port": 6000,
  "url": "http://localhost:6000",
  "pid": 12345
}
```

### 5. 获取项目文件

获取项目的所有文件列表和内容。

**端点**: `GET /api/webcontainer/projects/{session_id}/{version}/files`

**示例请求**:
```bash
curl "http://localhost:9565/api/webcontainer/projects/abc123/1/files"
```

**成功响应**:
```json
{
  "project_path": "/tmp/pageforge_webcontainer/abc123/v1",
  "files": {
    "index.html": {
      "content": "<!DOCTYPE html>...",
      "size": 1024,
      "modified": 1640995200
    },
    "package.json": {
      "content": "{\n  \"name\": \"generated-project\"...",
      "size": 512,
      "modified": 1640995200
    }
  }
}
```

### 6. 构建项目

构建项目生成生产版本。

**端点**: `POST /api/webcontainer/projects/{session_id}/{version}/build`

**示例请求**:
```bash
curl -X POST "http://localhost:9565/api/webcontainer/projects/abc123/1/build"
```

**成功响应**:
```json
{
  "status": "success",
  "message": "构建成功",
  "build_files": ["index.html", "assets/index.js", "assets/style.css"],
  "stdout": "vite v5.0.0 building for production..."
}
```

### 7. 获取预览信息

获取项目的预览相关信息。

**端点**: `GET /api/webcontainer/projects/{session_id}/{version}/preview`

**示例请求**:
```bash
curl "http://localhost:9565/api/webcontainer/projects/abc123/1/preview"
```

**成功响应**:
```json
{
  "session_id": "abc123",
  "version": 1,
  "status": "ready",
  "project_ready": true,
  "files_count": 4
}
```

### 8. 清理项目

清理指定项目的所有文件。

**端点**: `DELETE /api/webcontainer/projects/{session_id}/{version}`

**示例请求**:
```bash
curl -X DELETE "http://localhost:9565/api/webcontainer/projects/abc123/1"
```

**成功响应**:
```json
{
  "status": "success",
  "message": "项目清理完成"
}
```

### 9. 清理会话项目

清理指定会话的所有项目。

**端点**: `DELETE /api/webcontainer/projects/{session_id}`

**示例请求**:
```bash
curl -X DELETE "http://localhost:9565/api/webcontainer/projects/abc123"
```

**成功响应**:
```json
{
  "status": "success",
  "message": "会话清理完成"
}
```

## 使用流程

### 完整的项目生命周期管理

1. **创建项目**
   ```bash
   POST /api/webcontainer/projects?session_id=abc123&version=1
   ```

2. **检查状态**
   ```bash
   GET /api/webcontainer/projects/abc123/1/status
   ```

3. **安装依赖**
   ```bash
   POST /api/webcontainer/projects/abc123/1/install
   ```

4. **启动开发服务器**
   ```bash
   POST /api/webcontainer/projects/abc123/1/start
   ```

5. **查看文件**
   ```bash
   GET /api/webcontainer/projects/abc123/1/files
   ```

6. **构建项目**
   ```bash
   POST /api/webcontainer/projects/abc123/1/build
   ```

7. **清理项目**
   ```bash
   DELETE /api/webcontainer/projects/abc123/1
   ```

## 错误处理

所有 API 端点都可能返回以下错误：

### 400 Bad Request
- 参数验证失败
- 项目配置错误

### 404 Not Found
- 会话不存在
- 版本不存在
- 项目未创建

### 500 Internal Server Error
- 服务器内部错误
- 依赖安装失败
- 进程启动失败

### 错误响应格式
```json
{
  "detail": "错误描述"
}
```

## 状态说明

### 项目状态

- `not_found`: 项目不存在
- `created`: 项目已创建，依赖未安装
- `ready`: 项目就绪，依赖已安装
- `error`: 项目出错

### 操作状态

- `success`: 操作成功
- `error`: 操作失败
- `timeout`: 操作超时

## 文件结构

创建的项目包含以下文件：

```
project/
├── index.html          # 主页面文件
├── package.json        # 项目配置
├── src/
│   ├── style.css       # 提取的样式
│   └── main.js         # 提取的脚本
├── node_modules/       # 安装后生成
└── dist/              # 构建后生成
```

## 性能考虑

### 超时设置
- 依赖安装: 5分钟
- 项目构建: 5分钟
- 服务器启动: 30秒检测

### 资源清理
- 临时文件存储在系统临时目录
- 建议定期清理不再使用的项目
- 支持按会话或版本清理

## 安全考虑

### 文件操作
- 所有文件操作都在临时目录中进行
- 文件名和内容经过安全验证
- 防止路径遍历攻击

### 进程管理
- 子进程有超时限制
- 进程输出有大小限制
- 异常情况下自动清理资源

## 前端集成示例

### JavaScript 示例
```javascript
class WebContainerAPI {
  constructor(baseURL = 'http://localhost:9565') {
    this.baseURL = baseURL;
  }

  async createProject(sessionId, version) {
    const response = await fetch(
      `${this.baseURL}/api/webcontainer/projects?session_id=${sessionId}&version=${version}`,
      { method: 'POST' }
    );
    return response.json();
  }

  async getProjectStatus(sessionId, version) {
    const response = await fetch(
      `${this.baseURL}/api/webcontainer/projects/${sessionId}/${version}/status`
    );
    return response.json();
  }

  async installDependencies(sessionId, version) {
    const response = await fetch(
      `${this.baseURL}/api/webcontainer/projects/${sessionId}/${version}/install`,
      { method: 'POST' }
    );
    return response.json();
  }

  async startDevServer(sessionId, version) {
    const response = await fetch(
      `${this.baseURL}/api/webcontainer/projects/${sessionId}/${version}/start`,
      { method: 'POST' }
    );
    return response.json();
  }
}
```

### 使用示例
```javascript
const api = new WebContainerAPI();

// 创建并启动项目
async function setupProject(sessionId, version) {
  try {
    // 1. 创建项目
    await api.createProject(sessionId, version);
    
    // 2. 安装依赖
    const installResult = await api.installDependencies(sessionId, version);
    if (installResult.status !== 'success') {
      throw new Error(installResult.message);
    }
    
    // 3. 启动服务器
    const serverResult = await api.startDevServer(sessionId, version);
    if (serverResult.status === 'success') {
      console.log('开发服务器已启动:', serverResult.url);
    }
    
    return serverResult;
  } catch (error) {
    console.error('项目设置失败:', error);
  }
}
```

## 注意事项

1. **依赖安装时间**: 首次安装可能需要几分钟时间
2. **端口冲突**: 确保开发服务器端口（默认6000）未被占用
3. **资源清理**: 及时清理不再使用的项目以释放磁盘空间
4. **错误处理**: 所有操作都应包含适当的错误处理逻辑
5. **超时处理**: 长时间操作需要处理超时情况

通过 WebContainer API，您可以完整地管理浏览器内项目的生命周期，从创建到部署的各个环节都提供了相应的接口支持。