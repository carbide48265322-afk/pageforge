"""人机协作流程端到端测试"""
import pytest
import json
import asyncio
from datetime import datetime

from app.checkpoint.manager import CheckpointManager
from app.checkpoint.models import HumanInputType, CheckpointType


@pytest.mark.asyncio
async def test_create_human_input_checkpoint():
    """测试创建人机协作检查点"""
    manager = CheckpointManager()
    session_id = "test_session_001"
    
    request = await manager.create_human_input_checkpoint(
        session_id=session_id,
        phase="prd_confirm",
        input_type=HumanInputType.CONFIRM,
        title="请确认需求文档",
        description="",
        schema={
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["confirm", "revise"]},
                "feedback": {"type": "string"}
            }
        },
        context={"prd": "测试 PRD 内容"}
    )
    
    assert request["checkpoint_id"] is not None
    assert request["session_id"] == session_id
    assert request["phase"] == "prd_confirm"
    assert request["input_type"] == HumanInputType.CONFIRM.value
    assert request["title"] == "请确认需求文档"
    
    # 清理
    await manager.delete(request["checkpoint_id"])


@pytest.mark.asyncio
async def test_get_waiting_checkpoints():
    """测试获取等待中的检查点"""
    manager = CheckpointManager()
    session_id = "test_session_002"
    
    # 创建检查点
    request = await manager.create_human_input_checkpoint(
        session_id=session_id,
        phase="prd_confirm",
        input_type=HumanInputType.CONFIRM,
        title="请确认",
        description="",
        schema={"type": "object", "properties": {}},
        context={}
    )
    
    # 查询等待中的检查点
    waiting = await manager.get_waiting_checkpoints(session_id)
    assert len(waiting) == 1
    assert waiting[0]["status"] == "waiting_human"
    
    # 清理
    await manager.delete(request["checkpoint_id"])


@pytest.mark.asyncio
async def test_submit_human_response():
    """测试提交人机协作响应"""
    manager = CheckpointManager()
    session_id = "test_session_003"
    
    # 创建检查点
    request = await manager.create_human_input_checkpoint(
        session_id=session_id,
        phase="prd_confirm",
        input_type=HumanInputType.CONFIRM,
        title="请确认",
        description="",
        schema={"type": "object", "properties": {}},
        context={}
    )
    
    checkpoint_id = request["checkpoint_id"]
    
    # 提交确认响应
    response = await manager.submit_human_response(
        checkpoint_id=checkpoint_id,
        action="confirm",
        data={"action": "confirm"}
    )
    
    assert response["checkpoint_id"] == checkpoint_id
    assert response["action"] == "confirm"
    assert response["data"]["action"] == "confirm"
    
    # 验证检查点状态已更新
    checkpoint = await manager.load(checkpoint_id)
    assert checkpoint["status"] == "completed"
    assert checkpoint["human_input_response"]["action"] == "confirm"
    
    # 清理
    await manager.delete(checkpoint_id)


@pytest.mark.asyncio
async def test_prd_revise_flow():
    """测试 PRD 修改流程"""
    manager = CheckpointManager()
    session_id = "test_session_004"
    
    # 创建检查点
    request = await manager.create_human_input_checkpoint(
        session_id=session_id,
        phase="prd_confirm",
        input_type=HumanInputType.CONFIRM,
        title="请确认需求文档",
        description="",
        schema={
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["confirm", "revise"]},
                "feedback": {"type": "string"}
            }
        },
        context={"prd": "原始 PRD 内容"}
    )
    
    checkpoint_id = request["checkpoint_id"]
    
    # 提交修改响应
    response = await manager.submit_human_response(
        checkpoint_id=checkpoint_id,
        action="revise",
        data={"action": "revise", "feedback": "需要添加登录功能"}
    )
    
    assert response["action"] == "revise"
    assert response["data"]["feedback"] == "需要添加登录功能"
    
    # 验证检查点已完成
    waiting = await manager.get_waiting_checkpoints(session_id)
    assert len(waiting) == 0
    
    # 清理
    await manager.delete(checkpoint_id)


@pytest.mark.asyncio
async def test_checkpoint_not_found():
    """测试检查点不存在时的错误处理"""
    manager = CheckpointManager()
    
    with pytest.raises(ValueError, match="Checkpoint non_existent not found"):
        await manager.submit_human_response(
            checkpoint_id="non_existent",
            action="confirm",
            data={}
        )


@pytest.mark.asyncio
async def test_checkpoint_wrong_status():
    """测试检查点状态不正确时的错误处理"""
    manager = CheckpointManager()
    session_id = "test_session_005"
    
    # 创建检查点
    request = await manager.create_human_input_checkpoint(
        session_id=session_id,
        phase="prd_confirm",
        input_type=HumanInputType.CONFIRM,
        title="请确认",
        description="",
        schema={},
        context={}
    )
    
    checkpoint_id = request["checkpoint_id"]
    
    # 先提交一次响应
    await manager.submit_human_response(
        checkpoint_id=checkpoint_id,
        action="confirm",
        data={}
    )
    
    # 再次提交应该报错
    with pytest.raises(ValueError, match="Checkpoint status is completed"):
        await manager.submit_human_response(
            checkpoint_id=checkpoint_id,
            action="confirm",
            data={}
        )
    
    # 清理
    await manager.delete(checkpoint_id)


@pytest.mark.asyncio
async def test_get_checkpoint_by_phase():
    """测试按阶段查询检查点"""
    manager = CheckpointManager()
    session_id = "test_session_006"
    
    # 创建 PRD 确认检查点
    request1 = await manager.create_human_input_checkpoint(
        session_id=session_id,
        phase="prd_confirm",
        input_type=HumanInputType.CONFIRM,
        title="PRD确认",
        description="",
        schema={},
        context={}
    )
    
    # 按阶段查询
    checkpoint = await manager.get_checkpoint_by_phase(session_id, "prd_confirm")
    assert checkpoint is not None
    assert checkpoint["human_input_request"]["phase"] == "prd_confirm"
    
    # 查询不存在的阶段
    checkpoint = await manager.get_checkpoint_by_phase(session_id, "design_select")
    assert checkpoint is None
    
    # 清理
    await manager.delete(request1["checkpoint_id"])
