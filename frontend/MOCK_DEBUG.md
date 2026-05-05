# Mock系统问题诊断指南

## 🔍 常见问题排查

### 问题1: Mock模式没有自动启用

**可能原因：**
1. URL参数未设置
2. 环境变量未配置
3. 后端检测逻辑有问题
4. 初始化时机不对

**解决方案：**
```javascript
// 1. 检查URL参数
// 访问: http://localhost:6001/?mock=true

// 2. 检查环境变量
// .env.development 文件中添加: VITE_MOCK_MODE=true

// 3. 手动启用
simpleMock.enable(); // 或 mockService.enable()

// 4. 检查状态
console.log('Mock状态:', simpleMock.status);
```

### 问题2: API请求没有被拦截

**可能原因：**
1. fetch拦截器未正确安装
2. 请求URL不匹配
3. Mock服务未启用

**解决方案：**
```javascript
// 1. 确认mock已启用
console.log('Mock启用状态:', simpleMock.status.enabled);

// 2. 检查请求URL
// 确保请求包含 '/api/' 路径
fetch('/api/sessions', { method: 'POST' })
  .then(response => console.log('响应状态:', response.status))
  .catch(error => console.log('错误:', error));

// 3. 检查控制台日志
// 查看是否有 '[SimpleMock] 拦截API请求' 日志
```

### 问题3: SSE事件没有触发

**可能原因：**
1. SSE流格式不正确
2. 事件处理器未正确注册
3. 延迟时间设置不合理

**解决方案：**
```javascript
// 1. 手动测试SSE流
fetch('/api/sessions/test/messages', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: '测试计数器组件' })
})
.then(response => {
  console.log('SSE响应:', response);
  // 检查响应头是否为 text/event-stream
  console.log('Content-Type:', response.headers.get('Content-Type'));
});

// 2. 检查事件格式
// 正确的SSE格式: event: event_name\ndata: {...}\n\n
// 3. 调整延迟时间
// 在simple.ts中修改delay值
```

## 🛠️ 诊断工具

### 1. 快速测试脚本
```javascript
// 在控制台运行
const script = document.createElement('script');
script.src = '/test-mock.js';
document.head.appendChild(script);
```

### 2. 状态检查命令
```javascript
// 检查所有mock服务状态
console.log('=== Mock服务状态 ===');
console.log('简化版:', window.simpleMock?.status);
console.log('完整版:', window.mockService?.status);

// 检查环境
console.log('=== 环境信息 ===');
console.log('URL参数:', new URLSearchParams(window.location.search).get('mock'));
console.log('环境变量:', import.meta.env.VITE_MOCK_MODE);
console.log('开发环境:', import.meta.env.DEV);
```

### 3. API测试命令
```javascript
// 测试会话创建
fetch('/api/sessions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' }
})
.then(r => r.json())
.then(data => console.log('会话创建:', data));

// 测试消息发送
fetch('/api/sessions/test/messages', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: '创建计数器组件' })
})
.then(r => console.log('消息发送响应:', r));
```

## 📋 检查清单

### ✅ 环境配置检查
- [ ] URL包含 `?mock=true` 参数
- [ ] `.env.development` 包含 `VITE_MOCK_MODE=true`
- [ ] 在开发环境运行 (`pnpm run dev`)

### ✅ 服务加载检查
- [ ] 控制台显示 `[SimpleMock] 简化版Mock服务已加载`
- [ ] `window.simpleMock` 对象存在
- [ ] `simpleMock.status.enabled` 为 true

### ✅ API拦截检查
- [ ] 控制台显示 `[SimpleMock] 拦截API请求`
- [ ] API请求返回200状态码
- [ ] 响应数据符合预期格式

### ✅ SSE流检查
- [ ] SSE响应头为 `text/event-stream`
- [ ] 事件格式正确 (`event: xxx\ndata: {...}\n\n`)
- [ ] 事件按预期延迟发送

## 🔧 修复步骤

### 步骤1: 基础修复
```javascript
// 1. 确保mock服务加载
if (!window.simpleMock) {
  console.error('Mock服务未加载，检查导入语句');
}

// 2. 手动启用mock
window.simpleMock?.enable();

// 3. 验证状态
console.log('当前状态:', window.simpleMock?.status);
```

### 步骤2: API修复
```javascript
// 1. 测试基础API
fetch('/api/health')
  .then(r => console.log('健康检查:', r.status))
  .catch(e => console.log('健康检查失败:', e));

// 2. 检查fetch是否被拦截
const originalFetch = window.fetch;
console.log('Fetch函数:', typeof originalFetch);
```

### 步骤3: 事件修复
```javascript
// 1. 测试SSE连接
const response = await fetch('/api/sessions/test/messages', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: '测试' })
});

// 2. 读取SSE流
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  console.log('SSE数据:', decoder.decode(value));
}
```

## 🚨 紧急恢复

如果mock系统完全无法工作，可以临时禁用：

1. **移除导入语句**
```typescript
// 在 App.tsx 中注释掉
// import "./services/mock/simple";
```

2. **恢复原始fetch**
```javascript
// 在控制台运行
window.fetch = window.originalFetch || window.fetch;
```

3. **重启开发服务器**
```bash
pnpm run dev
```

## 📞 寻求帮助

如果以上方法都无法解决问题，请提供以下信息：

1. **浏览器控制台完整日志**
2. **当前URL**
3. **环境变量配置**
4. **package.json中的依赖版本**
5. **具体的错误信息或异常行为**

这将帮助更快定位和解决问题。