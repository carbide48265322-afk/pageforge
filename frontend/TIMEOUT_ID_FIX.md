# TimeoutId 修复文档

## 问题描述

在Mock系统的SSE流实现中，存在`timeoutId`变量作用域问题：

```
SseEventDispatcher.ts:161 SSE POST error: ReferenceError: timeoutId is not defined
at MockInterceptor._sendNextEvent (interceptor.ts:243:5)
```

## 根本原因

在`interceptor.ts`文件的`_createMockSSEStream`方法中：

1. `timeoutId`变量在`_createMockSSEStream`方法中定义
2. 但在`_sendNextEvent`方法中尝试使用这个变量
3. 由于作用域限制，`_sendNextEvent`无法访问`timeoutId`变量
4. 导致`ReferenceError: timeoutId is not defined`错误

## 解决方案

### 修改前（有问题的代码）

```typescript
private _createMockSSEStream(scenario: MockScenario): ReadableStream {
  let eventIndex = 0;
  let timeoutId: NodeJS.Timeout; // 在这里定义

  return new ReadableStream({
    start: (controller) => {
      this._sendNextEvent(controller, scenario.events, eventIndex);
    },
    cancel: () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    }
  });
}

private _sendNextEvent(
  controller: ReadableStreamDefaultController,
  events: MockEvent[],
  index: number
): void {
  // ...
  timeoutId = setTimeout(() => { // 这里无法访问timeoutId
    // ...
  }, event.delay);
}
```

### 修改后（修复的代码）

```typescript
private _createMockSSEStream(scenario: MockScenario): ReadableStream {
  let eventIndex = 0;
  let timeoutId: NodeJS.Timeout | null = null;

  // 将sendNextEvent定义在同一个作用域内
  const sendNextEvent = (
    controller: ReadableStreamDefaultController,
    events: MockEvent[],
    index: number
  ): void => {
    if (index >= events.length) {
      controller.close();
      return;
    }

    const event = events[index];

    // 现在timeoutId在同一个作用域内，可以正常访问
    timeoutId = setTimeout(() => {
      const eventData = `event: ${event.type}\ndata: ${JSON.stringify(event.data)}\n\n`;
      controller.enqueue(new TextEncoder().encode(eventData));

      sendNextEvent(controller, events, index + 1);
    }, event.delay);
  };

  return new ReadableStream({
    start: (controller) => {
      sendNextEvent(controller, scenario.events, eventIndex);
    },
    cancel: () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    }
  });
}
```

## 修复的关键点

1. **作用域统一**：将`sendNextEvent`函数定义移到与`timeoutId`相同的`_createMockSSEStream`方法作用域内
2. **变量访问**：现在`sendNextEvent`可以正常访问和修改`timeoutId`变量
3. **内存管理**：`cancel`方法可以正确清理timeout，避免内存泄漏
4. **递归调用**：使用函数表达式而不是方法调用，确保递归正常工作

## 验证方法

### 1. 使用测试页面

访问 `test-timeout-fix.html?mock=true` 并运行以下测试：

- **测试SSE流**：验证基本的SSE流创建和读取
- **测试创建会话**：验证会话创建API
- **测试发送消息**：验证完整的SSE流响应

### 2. 预期结果

- ✅ 没有`timeoutId is not defined`错误
- ✅ SSE流正常创建和发送事件
- ✅ 事件按正确的时间间隔发送
- ✅ 流可以正常关闭和清理

### 3. 控制台检查

检查浏览器控制台，确保：

```
[Timeout Fix Test] ✅ SSE流创建成功
[Timeout Fix Test] 收到事件: event: intent:result
data: {"intent":"code_gen","confidence":0.95}

[Timeout Fix Test] ✅ SSE流读取完成，共收到X个事件
```

## 影响范围

- **修复的文件**：`src/services/mock/interceptor.ts`
- **影响的功能**：所有使用SSE流的Mock API响应
- **相关组件**：`useSSEv2`, `SseEventDispatcher`, `ChatPanelV2`

## 测试建议

1. **单元测试**：验证SSE流创建和事件发送
2. **集成测试**：验证完整的API调用流程
3. **压力测试**：验证长时间运行的SSE流稳定性
4. **错误处理**：验证网络中断和超时情况

## 后续优化

- 考虑添加更完善的错误处理和重试机制
- 优化事件发送的时间控制精度
- 添加SSE流的状态监控和调试信息