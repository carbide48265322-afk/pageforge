# Mock URL匹配优先级修复文档

## 问题描述

原始的mock系统存在URL匹配逻辑问题：
- `/api/sessions/session_id/messages` 被错误地匹配到"创建会话"而不是"发送消息"
- 匹配顺序不正确，导致更宽泛的模式优先于更具体的模式

## 解决方案

### 1. 修改匹配机制
将匹配逻辑改为**从上到下的精确匹配优先级**：

```typescript
// 精确匹配优先级：从上到下，越精确的URL模式越在上面
const patterns = [
  // 1. 最精确的匹配：包含session ID和具体操作的URL
  {
    pattern: /\/api\/sessions\/[^/]+\/messages$/,
    method: 'POST',
    handler: () => { /* 发送消息 */ }
  },
  {
    pattern: /\/api\/sessions\/[^/]+\/versions$/,
    method: 'GET',
    handler: () => { /* 获取版本列表 */ }
  },
  {
    pattern: /\/api\/sessions\/[^/]+\/html$/,
    method: 'GET',
    handler: () => { /* 获取HTML内容 */ }
  },
  // 2. 中等精确度的匹配：只包含/sessions路径
  {
    pattern: /\/api\/sessions$/,
    method: 'POST',
    handler: () => { /* 创建会话 */ }
  },
  // 3. 最宽泛的匹配：任何包含/sessions的POST请求
  {
    pattern: /\/api\/sessions/,
    method: 'POST',
    handler: () => { /* 创建会话 */ }
  }
];
```

### 2. 优先级规则

1. **精确匹配优先**：`/api/sessions/{id}/messages` → 发送消息
2. **中等匹配次之**：`/api/sessions` → 创建会话
3. **宽泛匹配最后**：任何包含`/api/sessions`的POST请求 → 创建会话

### 3. 修改的文件

- `src/services/mock/interceptor.ts` - 主拦截器
- `src/services/mock/quick-fix.ts` - 快速修复版本

## 测试验证

### 测试URL匹配

| URL | 方法 | 期望匹配 | 实际匹配 |
|-----|------|----------|----------|
| `/api/sessions/test-123/messages` | POST | 发送消息 | ✅ 发送消息 |
| `/api/sessions/mock_session_123/messages` | POST | 发送消息 | ✅ 发送消息 |
| `/api/sessions` | POST | 创建会话 | ✅ 创建会话 |
| `/api/sessions/extra/path` | POST | 创建会话（宽泛） | ✅ 创建会话 |
| `/api/users` | POST | 无匹配 | ✅ 无匹配 |

### 使用测试工具

1. **模式匹配测试**：`test-pattern-matching.html`
2. **优先级测试**：`test-priority-matching.html`
3. **最终验证**：`final-test.html`

## 验证步骤

1. 访问 `final-test.html?mock=true`
2. 点击"测试URL优先级"验证匹配逻辑
3. 点击"测试创建会话"验证会话创建
4. 点击"测试发送消息"验证消息发送
5. 点击"测试完整流程"验证端到端功能

## 预期结果

- ✅ `/api/sessions/*/messages` 正确匹配到"发送消息"
- ✅ `/api/sessions` 正确匹配到"创建会话"
- ✅ SSE流正确返回对话事件序列
- ✅ 前端能正确处理和显示Mock数据

## 调试技巧

如果匹配不正确：

1. 检查浏览器控制台日志
2. 确认Mock模式已启用（URL参数 `?mock=true`）
3. 使用"检查Mock状态"按钮确认服务状态
4. 查看网络请求确认URL和响应

## 技术细节

### 正则表达式说明

- `/\/api\/sessions\/[^/]+\/messages$/` - 匹配 `/api/sessions/{任意非斜杠字符}/messages`
- `/\/api\/sessions$/` - 精确匹配 `/api/sessions`
- `/\/api\/sessions/` - 匹配任何包含 `/api/sessions` 的URL

### 匹配流程

1. 按数组顺序遍历patterns
2. 对每个pattern，检查URL和HTTP方法是否都匹配
3. 一旦找到匹配，立即执行对应的handler并返回
4. 如果没有匹配，返回404错误

这个修复确保了URL匹配的优先级正确，解决了之前`/messages`接口被错误匹配到`/sessions`的问题。