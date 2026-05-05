# Mock数据系统使用指南

## 概述

Mock数据系统允许前端在后端服务不可用时继续开发和调试。系统会自动检测后端状态，当后端不可用时自动启用mock模式。

## 启用方式

### 1. 自动启用（推荐）
系统会在开发环境自动检测后端服务状态：
- 如果后端服务不可用，自动启用mock模式
- 如果后端服务恢复，自动禁用mock模式

### 2. 手动启用

#### 通过URL参数：
```
http://localhost:6001/?mock=true
```

#### 通过环境变量：
在 `.env.development` 文件中设置：
```env
VITE_MOCK_MODE=true
```

#### 通过调试面板：
点击右下角的紫色调试按钮，在弹出面板中切换mock模式

#### 通过控制台：
```javascript
// 切换mock模式
mockService.toggle()

// 启用mock模式
mockService.enable()

// 禁用mock模式
mockService.disable()
```

## 预设场景

### 1. React组件生成场景
**触发条件：** 输入包含"计数器"或"counter"

**模拟流程：**
1. 意图识别 → 2. 思维链分析 → 3. 计划制定 → 4. 风格选择 → 5. 代码生成 → 6. 依赖安装 → 7. 预览启动

**示例输入：**
```
帮我创建一个计数器组件，要有增加、减少和重置功能
```

### 2. 简单聊天场景
**触发条件：** 输入包含"你好"或"帮助"

**模拟流程：**
1. 意图识别 → 2. 直接回复

**示例输入：**
```
你好，能帮我做什么？
```

## 调试工具

### 控制台命令

```javascript
// 查看当前状态
mockService.debug.status()

// 列出所有场景
mockService.debug.listScenarios()

// 测试特定场景
mockService.debug.testScenario("react-component")
```

### 调试面板功能

1. **状态显示** - 显示mock模式是否启用
2. **场景列表** - 显示所有可用的测试场景
3. **快速切换** - 一键启用/禁用mock模式
4. **控制台输出** - 快速调用调试命令

## 开发指南

### 添加新场景

1. 在 `src/services/mock/scenarios.ts` 中添加新的场景定义：

```typescript
export const newScenario: MockScenario = {
  id: 'your-scenario-id',
  name: '场景名称',
  userInput: '触发输入',
  events: [
    {
      type: 'event-type',
      delay: 1000, // 延迟时间(ms)
      data: { /* 事件数据 */ }
    }
    // ... 更多事件
  ]
};
```

2. 在 `mockScenarios` 数组中添加新场景：

```typescript
export const mockScenarios: MockScenario[] = [
  reactComponentScenario,
  chatScenario,
  newScenario // 添加新场景
];
```

### 自定义事件类型

支持的事件类型包括：
- `intent:result` - 意图识别结果
- `thinking:start/delta/end` - 思维链
- `plan:start/update/done` - 计划制定
- `style:selected` - 风格选择
- `tool_call:start/end` - 工具调用
- `file:created/updated/deleted` - 文件操作
- `status:*` - 状态更新
- `text:delta/done` - 文本回复

## 注意事项

1. **生产环境** - Mock系统只在开发环境生效，生产环境会自动禁用
2. **性能影响** - Mock系统对性能影响很小，可以安全使用
3. **数据一致性** - Mock数据是预设的，可能与真实后端返回的数据略有不同
4. **调试信息** - 所有mock操作都会在控制台输出日志，便于调试

## 常见问题

### Q: Mock模式没有自动启用？
A: 检查以下几点：
1. 确保在开发环境（`pnpm run dev`）
2. 检查后端是否真的不可用
3. 尝试手动启用：`mockService.enable()`

### Q: 如何测试特定的API端点？
A: 在 `src/services/mock/interceptor.ts` 中添加对应的mock处理器

### Q: Mock数据与真实数据不一致？
A: 可以修改场景定义中的数据，或者添加新的场景来匹配你的需求

### Q: 如何完全移除Mock系统？
A: 删除相关文件并移除App.tsx中的导入语句即可