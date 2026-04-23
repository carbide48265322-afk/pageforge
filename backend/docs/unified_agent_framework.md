# 统一Agent规划框架文档

## 概述

统一Agent规划框架是一个智能的任务处理和规划系统，能够根据任务特征自动选择最佳的规划策略，并提供任务管理约束来确保Agent按预期执行。

## 核心组件

### 1. 任务分析器 (TaskAnalyzer)

**功能**：分析用户需求的特征，包括：
- 任务复杂度 (0-1)
- 结构化程度 (0-1)
- 工具需求 (布尔值)
- 创造性需求 (0-1)
- 结果确定性 (0-1)
- 预估步骤数
- 任务领域
- 分析置信度

**策略推荐逻辑**：
- **混合策略 (hybrid)**: 复杂且结构化 (complexity > 0.7 && structured > 0.6)
- **计划执行 (plan_execute)**: 高度结构化 (structured > 0.7)
- **ReAct策略 (react)**: 需要工具调用或默认策略
- **思维链 (chain_of_thought)**: 高创造性需求 (creativity > 0.6)

### 2. 规划策略

#### ReAct策略
- **适用场景**: 工具调用、探索性任务
- **特点**: 动态思考+行动循环
- **工作流程**: 思考 → 行动 → 观察 → 重复

#### Plan-and-Execute策略
- **适用场景**: 结构化、步骤明确的任务
- **特点**: 预先规划+分步执行
- **工作流程**: 创建计划 → 按步骤执行 → 动态调整

### 3. 统一Agent框架 (UnifiedAgent)

**核心功能**：
- 智能策略选择
- 任务管理约束
- 性能监控
- 错误处理
- 统一接口

**工作流程**：
```
用户请求
   ↓
任务分析 → 特征提取
   ↓
任务约束 → 创建TodoWrite
   ↓
策略选择 → 智能匹配
   ↓
策略执行 → 专业处理
   ↓
结果整合 → 统一输出
```

### 4. TodoWrite任务管理工具

**核心功能**：
- 任务创建和管理
- 依赖关系管理
- 优先级控制
- 状态跟踪
- 统计分析
- 会话隔离

**主要特性**：
- 支持任务分解
- 依赖关系验证
- 进度跟踪
- 时间管理
- 标签分类

## API接口

### 统一处理接口
```
POST /unified-agent/process
{
  "message": "用户消息",
  "session_id": "会话ID"
}
```

### 策略管理接口
```
GET /unified-agent/strategies  # 获取可用策略
GET /unified-agent/performance  # 获取性能报告
POST /unified-agent/strategy/{strategy_name}  # 使用指定策略
```

## 多层控制机制

### 1. 系统提示词控制
- 基于任务特征动态生成系统提示
- 明确策略执行方式和约束

### 2. 工具定义限制
- 只提供当前策略需要的工具
- 限制工具调用范围

### 3. 任务管理约束 (TodoWrite)
- 显式任务分解和依赖管理
- 状态跟踪和验证
- 防止偏离预定路径

### 4. 上下文约束
- 维护执行状态和进度
- 提供上下文相关的指导

### 5. 后处理检查
- 验证结果质量和完整性
- 提供反馈和调整建议

## 使用示例

### 自动策略选择
```python
# 初始化统一Agent
agent = UnifiedAgent()

# 处理用户请求
state = AgentState(
    user_message="创建一个React博客网站",
    session_id="session_123"
)

result = await agent.process(state)
```

### 使用TodoWrite工具
```python
# 创建任务管理器
todo_tool = TodoWriteTool(session_id="session_123")

# 创建任务
todo_tool.create_task(
    title="设计页面结构",
    description="分析需求并设计页面结构",
    priority=1,
    estimated_time=30
)

# 获取任务列表
task_list = todo_tool.get_task_list()
```

## 性能监控

框架提供完整的性能监控功能：
- 策略使用统计
- 任务完成率
- 时间效率分析
- 领域分布统计

## 扩展性

### 添加新策略
```python
class CustomStrategy(PlanningStrategy):
    def get_name(self) -> str:
        return "custom"

    def get_description(self) -> str:
        return "自定义策略描述"

    async def execute(self, state: AgentState, analysis: TaskAnalysis) -> AgentState:
        # 实现自定义逻辑
        pass

# 注册新策略
agent.add_strategy("custom", CustomStrategy())
```

## 测试覆盖

- 任务分析器测试
- 策略实现测试
- TodoWrite工具测试
- 集成测试
- 端到端测试

## 未来改进

1. **更多策略支持**
   - 思维链策略 (Chain-of-Thought)
   - 混合策略 (Hybrid)
   - 自适应策略

2. **增强控制机制**
   - 实时路径验证
   - 动态约束调整
   - 智能干预

3. **性能优化**
   - 策略缓存
   - 并行执行
   - 资源管理

4. **用户体验**
   - 可视化任务管理
   - 交互式调试
   - 详细日志记录