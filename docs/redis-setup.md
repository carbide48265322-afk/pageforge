# Redis 基础设施使用指南

## 快速开始

### 1. 启动 Redis

```bash
docker-compose up -d redis
```

### 2. 验证连接

```bash
docker exec pageforge-redis redis-cli -a pageforge ping
```

### 3. 在代码中使用

```python
from app.checkpoint import CheckpointManager, CheckpointType

manager = CheckpointManager()

# 保存检查点
checkpoint_id = await manager.save(
    session_id="session-001",
    phase="requirement",
    checkpoint_type=CheckpointType.CLARIFICATION,
    state={"messages": []},
    presentation={"title": "请确认需求"},
    options=[{"id": "confirm", "label": "确认"}]
)

# 恢复检查点
checkpoint = await manager.load(checkpoint_id)
```

## 配置说明

环境变量：
- `REDIS_HOST`: 默认 localhost
- `REDIS_PORT`: 默认 6379
- `REDIS_PASSWORD`: 默认 pageforge
- `CHECKPOINT_TTL`: 检查点过期时间（秒），默认 3600

## 与 LangGraph 集成

```python
from app.checkpoint import RedisCheckpointSaver
from langgraph.graph import StateGraph

builder = StateGraph(...)
# ... 添加节点 ...

checkpointer = RedisCheckpointSaver()
graph = builder.compile(checkpointer=checkpointer)
```
