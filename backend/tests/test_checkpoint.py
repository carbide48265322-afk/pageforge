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
        checkpoint_type=CheckpointType.CLARIFICATION,
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
    assert checkpoint["checkpoint_type"] == CheckpointType.CLARIFICATION


@pytest.mark.asyncio
async def test_list_by_session(manager):
    """测试按会话列出检查点"""
    session_id = "test-session-002"
    
    # 创建多个检查点
    for i in range(3):
        await manager.save(
            session_id=session_id,
            phase="requirement",
            checkpoint_type=CheckpointType.CLARIFICATION,
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
