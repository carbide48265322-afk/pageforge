# Redis 基础设施实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 搭建 Redis 基础设施，支持 AI 应用生成器的检查点存储和人机协作暂停/恢复机制。

**Architecture:** 使用 Docker Compose 部署 Redis，封装 CheckpointManager 模块与 LangGraph 集成，支持检查点的保存、恢复、过期清理。

**Tech Stack:** Redis 7.x, Docker Compose, Python redis-py, LangGraph CheckpointSaver

---

## 前置信息

**项目结构：**
- 后端：`backend/` (使用 uv + pyproject.toml)
- 现有依赖：langgraph, fastapi, pydantic 等
- 应用代码：`backend/app/`

**Worktree 路径：**
`/Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/.worktrees/feature/redis-infrastructure`

---

## Task 1: 创建 Docker Compose 配置

**Files:**
- Create: `docker-compose.yml` (项目根目录)
- Create: `redis/redis.conf`
- Create: `redis/.gitignore`

**Step 1: 创建 Redis 配置文件**

File: `redis/redis.conf`

```
# Redis 基础配置
bind 0.0.0.0
port 6379

# 内存限制
maxmemory 256mb
maxmemory-policy allkeys-lru

# 持久化配置
save 60 1000
appendonly yes
appendfsync everysec

# 安全
requirepass pageforge

# 检查点数据过期（1小时）
# 通过代码设置 TTL，不在配置中硬编码
```

**Step 2: 创建 docker-compose.yml**

File: `docker-compose.yml`

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: pageforge-redis
    ports:
      - "6379:6379"
    volumes:
      - ./redis/redis.conf:/usr/local/etc/redis/redis.conf:ro
      - redis-data:/data
    command: redis-server /usr/local/etc/redis/redis.conf
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "pageforge", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

volumes:
  redis-data:
```

**Step 3: 创建 redis/.gitignore**

File: `redis/.gitignore`

```
# Redis 数据目录（运行时生成）
data/
```

**Step 4: 验证配置**

Run:
```bash
cd /Users/fangyan/WorkBuddy/20260416190835/agent-projects-100/projects/pageforge/.worktrees/feature/redis-infrastructure
docker-compose config
```

Expected: 配置验证通过，无错误

**Step 5: 启动 Redis 服务**

Run:
```bash
docker-compose up -d
```

Expected: Redis 容器启动成功

**Step 6: 测试连接**

Run:
```bash
docker exec pageforge-redis redis-cli -a pageforge ping
```

Expected: 输出 `PONG`

**Step 7: Commit**

```bash
git add docker-compose.yml redis/
git commit -m "feat(infra): add Redis service with docker-compose"
```

---

## Task 2: 添加 Python Redis 依赖

**Files:**
- Modify: `backend/pyproject.toml`

**Step 1: 添加 redis 依赖**

在 `dependencies` 列表中添加：

```toml
dependencies = [
    "aiosqlite>=0.22.1",
    "fastapi>=0.136.0",
    "langchain>=1.2.15",
    "langchain-openai>=1.1.14",
    "langgraph>=1.1.8",
    "pydantic>=2.13.2",
    "python-dotenv>=1.2.2",
    "redis>=5.0.0",
    "uvicorn[standard]>=0.44.0",
]
```

**Step 2: 安装依赖**

Run:
```bash
cd backend
uv sync
```

Expected: 依赖安装成功

**Step 3: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock
git commit -m "chore(deps): add redis dependency"
```

---

## Task 3: 创建 CheckpointManager 模块

**Files:**
- Create: `backend/app/checkpoint/__init__.py`
- Create: `backend/app/checkpoint/models.py`
- Create: `backend/app/checkpoint/manager.py`
- Create: `backend/tests/test_checkpoint.py`

**Step 1: 创建模型定义**

File: `backend/app/checkpoint/models.py`

```python
"""Checkpoint 数据模型"""
from typing import TypedDict, Optional, Any
from datetime import datetime
from enum import Enum


class CheckpointType(str, Enum):
    """检查点类型"""
    CLARIFICATION = "clarification"      # 需求澄清
    PRD_CONFIRMATION = "prd_confirmation"  # PRD 确认
    STYLE_SELECTION = "style_selection"    # 风格选择
    TECH_CONFIRMATION = "tech_confirmation"  # 技术方案确认
    FEATURE_SELECTION = "feature_selection"  # 功能选择
    DELIVERY_CONFIRMATION = "delivery_confirmation"  # 交付确认


class CheckpointData(TypedDict):
    """检查点数据"""
    session_id: str
    checkpoint_id: str
    phase: str                    # 当前阶段
    checkpoint_type: str          # 检查点类型
    state: dict                   # LangGraph 状态快照
    presentation: dict            # 展示给用户的内容
    options: Optional[list]       # 用户可选操作
    created_at: str
    expires_at: Optional[str]     # 过期时间


class HumanInputResponse(TypedDict):
    """用户输入响应"""
    checkpoint_id: str
    action: str                   # confirm / revise / back / cancel
    data: dict                    # 附加数据
    responded_at: str
```

**Step 2: 创建 CheckpointManager**

File: `backend/app/checkpoint/manager.py`

```python
"""Checkpoint 管理器 - 用于人机协作的暂停/恢复"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional

import redis
from redis.exceptions import RedisError

from .models import CheckpointData, HumanInputResponse


class CheckpointManager:
    """检查点管理器
    
    职责：
    1. 保存检查点（人机协作暂停时）
    2. 恢复检查点（用户响应后）
    3. 管理检查点过期（默认1小时）
    4. 支持会话级别的检查点列表查询
    """
    
    DEFAULT_TTL = 3600  # 1小时
    KEY_PREFIX = "pageforge:checkpoint"
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: str = "pageforge",
        db: int = 0
    ):
        self._redis = redis.Redis(
            host=host,
            port=port,
            password=password,
            db=db,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
    
    def _make_key(self, checkpoint_id: str) -> str:
        """生成 Redis key"""
        return f"{self.KEY_PREFIX}:{checkpoint_id}"
    
    def _make_session_key(self, session_id: str) -> str:
        """生成会话索引 key"""
        return f"{self.KEY_PREFIX}:session:{session_id}"
    
    async def save(
        self,
        session_id: str,
        phase: str,
        checkpoint_type: str,
        state: dict,
        presentation: dict,
        options: Optional[list] = None,
        ttl: int = DEFAULT_TTL
    ) -> str:
        """保存检查点
        
        Args:
            session_id: 会话ID
            phase: 当前阶段
            checkpoint_type: 检查点类型
            state: LangGraph 状态快照
            presentation: 展示给用户的内容
            options: 用户可选操作
            ttl: 过期时间（秒）
            
        Returns:
            checkpoint_id: 检查点ID
        """
        checkpoint_id = str(uuid.uuid4())
        now = datetime.utcnow()
        expires_at = now + timedelta(seconds=ttl)
        
        checkpoint: CheckpointData = {
            "session_id": session_id,
            "checkpoint_id": checkpoint_id,
            "phase": phase,
            "checkpoint_type": checkpoint_type,
            "state": state,
            "presentation": presentation,
            "options": options or [],
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
        }
        
        key = self._make_key(checkpoint_id)
        session_key = self._make_session_key(session_id)
        
        try:
            # 保存检查点数据
            self._redis.setex(
                key,
                ttl,
                json.dumps(checkpoint, default=str)
            )
            # 添加到会话索引（使用 sorted set，按时间排序）
            self._redis.zadd(session_key, {checkpoint_id: now.timestamp()})
            self._redis.expire(session_key, ttl)
            
            return checkpoint_id
        except RedisError as e:
            raise RuntimeError(f"Failed to save checkpoint: {e}")
    
    async def load(self, checkpoint_id: str) -> Optional[CheckpointData]:
        """加载检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            CheckpointData 或 None（如果不存在或已过期）
        """
        key = self._make_key(checkpoint_id)
        
        try:
            data = self._redis.get(key)
            if not data:
                return None
            return json.loads(data)
        except RedisError as e:
            raise RuntimeError(f"Failed to load checkpoint: {e}")
    
    async def delete(self, checkpoint_id: str) -> bool:
        """删除检查点
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            是否成功删除
        """
        key = self._make_key(checkpoint_id)
        
        try:
            # 先获取会话ID
            data = self._redis.get(key)
            if data:
                checkpoint = json.loads(data)
                session_id = checkpoint.get("session_id")
                if session_id:
                    session_key = self._make_session_key(session_id)
                    self._redis.zrem(session_key, checkpoint_id)
            
            return self._redis.delete(key) > 0
        except RedisError as e:
            raise RuntimeError(f"Failed to delete checkpoint: {e}")
    
    async def list_by_session(
        self,
        session_id: str,
        limit: int = 50
    ) -> list[CheckpointData]:
        """获取会话的所有检查点
        
        Args:
            session_id: 会话ID
            limit: 最大返回数量
            
        Returns:
            检查点列表（按时间倒序）
        """
        session_key = self._make_session_key(session_id)
        
        try:
            # 获取检查点ID列表（按时间倒序）
            checkpoint_ids = self._redis.zrevrange(
                session_key, 0, limit - 1
            )
            
            checkpoints = []
            for cid in checkpoint_ids:
                data = self._redis.get(self._make_key(cid))
                if data:
                    checkpoints.append(json.loads(data))
            
            return checkpoints
        except RedisError as e:
            raise RuntimeError(f"Failed to list checkpoints: {e}")
    
    async def save_response(
        self,
        checkpoint_id: str,
        response: HumanInputResponse,
        ttl: int = 86400  # 1天
    ) -> bool:
        """保存用户响应（用于异步通知机制）
        
        Args:
            checkpoint_id: 检查点ID
            response: 用户响应
            ttl: 过期时间（秒）
            
        Returns:
            是否成功保存
        """
        key = f"{self.KEY_PREFIX}:response:{checkpoint_id}"
        
        try:
            self._redis.setex(
                key,
                ttl,
                json.dumps(response, default=str)
            )
            return True
        except RedisError as e:
            raise RuntimeError(f"Failed to save response: {e}")
    
    async def get_response(
        self,
        checkpoint_id: str
    ) -> Optional[HumanInputResponse]:
        """获取用户响应
        
        Args:
            checkpoint_id: 检查点ID
            
        Returns:
            HumanInputResponse 或 None
        """
        key = f"{self.KEY_PREFIX}:response:{checkpoint_id}"
        
        try:
            data = self._redis.get(key)
            if not data:
                return None
            return json.loads(data)
        except RedisError as e:
            raise RuntimeError(f"Failed to get response: {e}")
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            return self._redis.ping()
        except RedisError:
            return False
```

**Step 3: 创建模块 __init__.py**

File: `backend/app/checkpoint/__init__.py`

```python
"""Checkpoint 模块 - 人机协作状态管理"""
from .manager import CheckpointManager
from .models import CheckpointData, CheckpointType, HumanInputResponse

__all__ = [
    "CheckpointManager",
    "CheckpointData", 
    "CheckpointType",
    "HumanInputResponse",
]
```

**Step 4: 创建测试文件**

File: `backend/tests/test_checkpoint.py`

```python
"""CheckpointManager 测试"""
import pytest
import asyncio
from datetime import datetime

from app.checkpoint import CheckpointManager, CheckpointType


@pytest.fixture
def manager():
    """创建测试用的 CheckpointManager"""
    return CheckpointManager(
        host="localhost",
        port=6379,
        password="pageforge"
    )


@pytest.fixture
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_save_and_load(manager):
    """测试保存和加载检查点"""
    checkpoint_id = await manager.save(
        session_id="test-session-001",
        phase="requirement",
        checkpoint_type=CheckpointType.CHARIFICATION,
        state={"messages": [], "current_intent": "test"},
        presentation={"title": "需求澄清", "content": "请确认..."},
        options=[{"id": "confirm", "label": "确认"}],
        ttl=60
    )
    
    assert checkpoint_id is not None
    
    # 加载检查点
    checkpoint = await manager.load(checkpoint_id)
    assert checkpoint is not None
    assert checkpoint["session_id"] == "test-session-001"
    assert checkpoint["phase"] == "requirement"
    assert checkpoint["checkpoint_type"] == CheckpointType.CHARIFICATION


@pytest.mark.asyncio
async def test_list_by_session(manager):
    """测试按会话列出检查点"""
    session_id = "test-session-002"
    
    # 创建多个检查点
    for i in range(3):
        await manager.save(
            session_id=session_id,
            phase="requirement",
            checkpoint_type=CheckpointType.CHARIFICATION,
            state={"index": i},
            presentation={"index": i},
            ttl=60
        )
    
    # 列出检查点
    checkpoints = await manager.list_by_session(session_id)
    assert len(checkpoints) == 3


@pytest.mark.asyncio
async def test_delete(manager):
    """测试删除检查点"""
    checkpoint_id = await manager.save(
        session_id="test-session-003",
        phase="design",
        checkpoint_type=CheckpointType.STYLE_SELECTION,
        state={},
        presentation={},
        ttl=60
    )
    
    # 删除
    result = await manager.delete(checkpoint_id)
    assert result is True
    
    # 再次加载应返回 None
    checkpoint = await manager.load(checkpoint_id)
    assert checkpoint is None


@pytest.mark.asyncio
async def test_save_and_get_response(manager):
    """测试保存和获取用户响应"""
    checkpoint_id = "test-checkpoint-001"
    
    response = {
        "checkpoint_id": checkpoint_id,
        "action": "confirm",
        "data": {"confirmed": True},
        "responded_at": datetime.utcnow().isoformat()
    }
    
    # 保存响应
    result = await manager.save_response(checkpoint_id, response, ttl=60)
    assert result is True
    
    # 获取响应
    loaded = await manager.get_response(checkpoint_id)
    assert loaded is not None
    assert loaded["action"] == "confirm"


def test_health_check(manager):
    """测试健康检查"""
    assert manager.health_check() is True
```

**Step 5: 创建 tests 目录的 __init__.py**

File: `backend/tests/__init__.py`

```python
"""测试模块"""
```

**Step 6: 运行测试**

Run:
```bash
cd backend
uv run pytest tests/test_checkpoint.py -v
```

Expected: 所有测试通过

**Step 7: Commit**

```bash
git add backend/app/checkpoint/ backend/tests/
git commit -m "feat(checkpoint): add CheckpointManager with Redis backend"
```

---

## Task 4: 集成到应用配置

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/main.py`

**Step 1: 添加 Redis 配置**

File: `backend/app/config.py`

添加以下内容：

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ... 现有配置 ...
    
    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "pageforge"
    REDIS_DB: int = 0
    
    # 检查点配置
    CHECKPOINT_TTL: int = 3600  # 1小时
    CHECKPOINT_RESPONSE_TTL: int = 86400  # 1天
    
    class Config:
        env_file = ".env"


settings = Settings()
```

**Step 2: 添加健康检查端点**

File: `backend/app/main.py`

添加健康检查端点：

```python
from fastapi import FastAPI
from app.checkpoint import CheckpointManager
from app.config import settings

app = FastAPI()

# ... 现有路由 ...

@app.get("/health")
async def health_check():
    """健康检查端点"""
    manager = CheckpointManager(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB
    )
    
    redis_ok = manager.health_check()
    
    return {
        "status": "healthy" if redis_ok else "degraded",
        "redis": "connected" if redis_ok else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }
```

**Step 3: 测试健康检查端点**

Run:
```bash
cd backend
uv run uvicorn app.main:app --reload &
curl http://localhost:8000/health
```

Expected: 返回 `{"status": "healthy", "redis": "connected", ...}`

**Step 4: Commit**

```bash
git add backend/app/config.py backend/app/main.py
git commit -m "feat(api): add Redis health check endpoint"
```

---

## Task 5: 创建 LangGraph CheckpointSaver 适配器

**Files:**
- Create: `backend/app/checkpoint/langgraph_adapter.py`

**Step 1: 创建适配器**

File: `backend/app/checkpoint/langgraph_adapter.py`

```python
"""LangGraph CheckpointSaver 适配器

将 CheckpointManager 包装为 LangGraph 兼容的 CheckpointSaver
"""
from typing import AsyncIterator, Optional
from contextlib import asynccontextmanager

from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint

from .manager import CheckpointManager


class RedisCheckpointSaver(BaseCheckpointSaver):
    """Redis 检查点存储适配器
    
    用法：
        checkpointer = RedisCheckpointSaver()
        graph = builder.compile(checkpointer=checkpointer)
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: str = "pageforge",
        db: int = 0,
        ttl: int = 3600
    ):
        self.manager = CheckpointManager(
            host=host,
            port=port,
            password=password,
            db=db
        )
        self.ttl = ttl
    
    async def aget(self, config: dict) -> Optional[Checkpoint]:
        """获取检查点"""
        checkpoint_id = config.get("configurable", {}).get("checkpoint_id")
        if not checkpoint_id:
            return None
        
        data = await self.manager.load(checkpoint_id)
        if not data:
            return None
        
        return Checkpoint(
            v=data["state"].get("v", 1),
            ts=data["created_at"],
            channel_values=data["state"].get("channel_values", {}),
            channel_versions=data["state"].get("channel_versions", {}),
            versions_seen=data["state"].get("versions_seen", {}),
            pending_sends=data["state"].get("pending_sends", []),
        )
    
    async def aput(
        self,
        config: dict,
        checkpoint: Checkpoint,
        metadata: Optional[dict] = None
    ) -> dict:
        """保存检查点"""
        session_id = config.get("configurable", {}).get("session_id", "default")
        phase = config.get("configurable", {}).get("phase", "unknown")
        checkpoint_type = config.get("configurable", {}).get("checkpoint_type", "unknown")
        
        state = {
            "v": checkpoint.v,
            "channel_values": checkpoint.channel_values,
            "channel_versions": checkpoint.channel_versions,
            "versions_seen": checkpoint.versions_seen,
            "pending_sends": checkpoint.pending_sends,
        }
        
        presentation = metadata.get("presentation", {}) if metadata else {}
        options = metadata.get("options", []) if metadata else []
        
        checkpoint_id = await self.manager.save(
            session_id=session_id,
            phase=phase,
            checkpoint_type=checkpoint_type,
            state=state,
            presentation=presentation,
            options=options,
            ttl=self.ttl
        )
        
        return {
            "configurable": {
                **config.get("configurable", {}),
                "checkpoint_id": checkpoint_id
            }
        }
    
    @asynccontextmanager
    async def alist(self, config: dict) -> AsyncIterator[Checkpoint]:
        """列出检查点（简化实现）"""
        session_id = config.get("configurable", {}).get("session_id")
        if not session_id:
            return
        
        checkpoints = await self.manager.list_by_session(session_id)
        for data in checkpoints:
            yield Checkpoint(
                v=data["state"].get("v", 1),
                ts=data["created_at"],
                channel_values=data["state"].get("channel_values", {}),
                channel_versions=data["state"].get("channel_versions", {}),
                versions_seen=data["state"].get("versions_seen", {}),
                pending_sends=data["state"].get("pending_sends", []),
            )
```

**Step 2: 更新 __init__.py**

File: `backend/app/checkpoint/__init__.py`

```python
"""Checkpoint 模块 - 人机协作状态管理"""
from .manager import CheckpointManager
from .models import CheckpointData, CheckpointType, HumanInputResponse
from .langgraph_adapter import RedisCheckpointSaver

__all__ = [
    "CheckpointManager",
    "CheckpointData", 
    "CheckpointType",
    "HumanInputResponse",
    "RedisCheckpointSaver",
]
```

**Step 3: Commit**

```bash
git add backend/app/checkpoint/
git commit -m "feat(checkpoint): add LangGraph CheckpointSaver adapter"
```

---

## Task 6: 创建使用示例和文档

**Files:**
- Create: `docs/redis-setup.md`
- Create: `examples/checkpoint_usage.py`

**Step 1: 创建文档**

File: `docs/redis-setup.md`

```markdown
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
    checkpoint_type=CheckpointType.CHARIFICATION,
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
```

**Step 2: 创建示例代码**

File: `examples/checkpoint_usage.py`

```python
"""CheckpointManager 使用示例"""
import asyncio
from app.checkpoint import CheckpointManager, CheckpointType


async def main():
    # 创建管理器
    manager = CheckpointManager()
    
    # 检查健康状态
    if not manager.health_check():
        print("Redis 连接失败")
        return
    
    print("Redis 连接成功")
    
    # 示例 1: 保存检查点
    checkpoint_id = await manager.save(
        session_id="demo-session",
        phase="requirement",
        checkpoint_type=CheckpointType.PRD_CONFIRMATION,
        state={
            "messages": [
                {"role": "user", "content": "我想做一个博客系统"}
            ],
            "prd": "# 博客系统 PRD\n\n..."
        },
        presentation={
            "title": "PRD 确认",
            "content": "请确认以下 PRD 是否符合您的需求",
            "prd_summary": "博客系统：文章管理、用户系统、评论功能"
        },
        options=[
            {"id": "confirm", "label": "确认，继续", "type": "primary"},
            {"id": "revise", "label": "需要修改", "type": "secondary"},
            {"id": "back", "label": "返回上一步", "type": "text"}
        ],
        ttl=3600  # 1小时过期
    )
    
    print(f"检查点已保存: {checkpoint_id}")
    
    # 示例 2: 加载检查点
    checkpoint = await manager.load(checkpoint_id)
    print(f"加载检查点: {checkpoint['checkpoint_type']}")
    print(f"展示内容: {checkpoint['presentation']['title']}")
    
    # 示例 3: 模拟用户响应
    response = {
        "checkpoint_id": checkpoint_id,
        "action": "confirm",
        "data": {"confirmed": True, "feedback": ""},
        "responded_at": "2026-04-20T12:00:00Z"
    }
    await manager.save_response(checkpoint_id, response)
    print("用户响应已保存")
    
    # 示例 4: 获取用户响应
    loaded_response = await manager.get_response(checkpoint_id)
    print(f"用户操作: {loaded_response['action']}")
    
    # 示例 5: 列出会话的所有检查点
    checkpoints = await manager.list_by_session("demo-session")
    print(f"会话检查点数量: {len(checkpoints)}")
    
    # 清理
    await manager.delete(checkpoint_id)
    print("检查点已清理")


if __name__ == "__main__":
    asyncio.run(main())
```

**Step 3: Commit**

```bash
git add docs/redis-setup.md examples/checkpoint_usage.py
git commit -m "docs: add Redis setup guide and usage examples"
```

---

## 验证清单

- [ ] Redis 容器运行正常 (`docker ps` 显示 pageforge-redis)
- [ ] 健康检查端点返回正常 (`curl /health`)
- [ ] 所有单元测试通过 (`pytest tests/test_checkpoint.py -v`)
- [ ] 示例代码可正常运行 (`python examples/checkpoint_usage.py`)

---

## 后续步骤

1. 在 LangGraph 中接入 `RedisCheckpointSaver`
2. 实现人机协作节点的暂停/恢复逻辑
3. 前端对接检查点 API
