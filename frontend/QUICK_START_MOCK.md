# Mock数据系统快速开始

## 🚀 5分钟上手

### 1. 启用Mock模式

**方法1：URL参数（推荐）**
```
http://localhost:6001/?mock=true
```

**方法2：环境变量**
```bash
# .env.development
VITE_MOCK_MODE=true
```

**方法3：控制台命令**
```javascript
mockService.enable()  // 启用
mockService.disable() // 禁用
mockService.toggle()  // 切换
```

### 2. 使用预设场景

#### 场景1：React组件生成
**输入：**
```
帮我创建一个计数器组件，要有增加、减少和重置功能
```

**效果：**
- ✅ 意图识别（code_gen）
- 🤔 思维链分析（3步推理）
- 📋 计划制定（5个步骤）
- 🎨 风格选择（modern蓝色主题）
- 🔧 代码生成（Counter.tsx文件）
- 📦 依赖安装
- 🚀 预览启动
- 💬 完成回复

#### 场景2：简单聊天
**输入：**
```
你好，能帮我做什么？
```

**效果：**
- ✅ 意图识别（chat）
- 💬 直接回复（功能介绍）

### 3. 调试面板

点击右下角的 **紫色调试按钮** 🛠️，可以：
- 🔄 快速切换Mock模式
- 📋 查看所有场景
- 🔍 查看当前状态
- ⚡ 快速调试命令

### 4. 控制台调试

```javascript
// 查看状态
mockService.debug.status()

// 列出场景
mockService.debug.listScenarios()

// 测试场景
mockService.debug.testScenario("react-component")

// 性能测试
mockTests.runAll()
```

## 📋 预设场景一览

| 场景ID | 名称 | 触发关键词 | 事件数 | 时长 |
|--------|------|------------|--------|------|
| `react-component` | React组件生成 | 计数器、counter | 17 | ~10s |
| `simple-chat` | 简单聊天 | 你好、帮助 | 4 | ~1s |

## 🎯 常见用例

### 用例1：开发前端界面

```bash
# 1. 启用mock模式
http://localhost:6001/?mock=true

# 2. 测试聊天界面
输入："你好，能帮我做什么？"

# 3. 测试代码生成界面  
输入："帮我创建一个计数器组件"
```

### 用例2：调试特定组件

```javascript
// 1. 打开调试面板
点击右下角紫色按钮

// 2. 选择特定场景测试
mockService.debug.testScenario("react-component")

// 3. 观察组件状态变化
查看ThinkingPanel、PlanPanel等组件的渲染
```

### 用例3：性能优化

```javascript
// 运行性能测试
mockTests.performance()

// 检查内存使用
mockTests.memory()

// 优化建议
// - 减少事件数量
// - 调整延迟时间
// - 优化数据处理
```

## ⚙️ 配置选项

### 环境变量

```env
# 启用Mock模式
VITE_MOCK_MODE=true

# 启用测试套件
VITE_MOCK_TEST=true

# API基础地址（Mock不生效）
VITE_API_BASE=http://localhost:9000/api
```

### 场景配置

在 `src/services/mock/scenarios.ts` 中可以：
- 📝 修改现有场景
- ➕ 添加新场景
- ⏱️ 调整事件延迟
- 🔄 自定义事件顺序

## 🐛 常见问题

### Q: Mock模式没有生效？
**解决方案：**
1. 确保URL包含 `?mock=true`
2. 检查控制台是否有错误
3. 尝试手动启用：`mockService.enable()`

### Q: 事件延迟不准确？
**解决方案：**
1. 在场景定义中调整 `delay` 值
2. 检查浏览器性能
3. 关闭其他占用资源的标签页

### Q: 如何添加新场景？
**解决方案：**
```typescript
// 在 scenarios.ts 中添加
export const newScenario: MockScenario = {
  id: 'your-id',
  name: 'Your Scenario',
  userInput: '触发输入',
  events: [/* 事件数组 */]
};
```

## 📚 进阶学习

- 📖 [完整使用指南](MOCK_GUIDE.md)
- 🔧 [开发文档](src/services/mock/README.md)
- 🧪 [测试文档](src/services/mock/test.ts)

## 🎊 恭喜！

您已经掌握了Mock数据系统的基本使用！现在可以：
- 🚀 在后端不可用时继续开发
- 🧪 测试各种交互场景
- 🔍 调试前端组件
- ⚡ 提升开发效率

**下一步建议：**
1. 尝试不同的预设场景
2. 使用调试面板探索功能
3. 根据需求自定义场景
4. 查看完整文档了解更多高级功能