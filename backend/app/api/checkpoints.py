"""Checkpoint API - 处理人机协作的用户响应"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.checkpoint.manager import CheckpointManager

router = APIRouter()
checkpoint_manager = CheckpointManager()


class HumanResponseRequest(BaseModel):
    """用户响应请求"""
    action: str
    data: dict


@router.post("/{checkpoint_id}/respond")
async def respond_to_checkpoint(
    checkpoint_id: str,
    req: HumanResponseRequest
):
    """提交人机协作响应
    
    Args:
        checkpoint_id: 检查点ID
        req: 用户响应数据
        
    Returns:
        提交结果
    """
    try:
        response = await checkpoint_manager.submit_human_response(
            checkpoint_id=checkpoint_id,
            action=req.action,
            data=req.data
        )
        return {
            "status": "success",
            "checkpoint_id": checkpoint_id,
            "action": req.action
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/waiting")
async def get_waiting_checkpoint(session_id: str):
    """获取会话中等待响应的检查点
    
    Args:
        session_id: 会话ID
        
    Returns:
        等待中的检查点信息
    """
    checkpoints = await checkpoint_manager.get_waiting_checkpoints(session_id)
    if not checkpoints:
        return {"status": "none", "checkpoint": None}
    
    return {
        "status": "waiting",
        "checkpoint": checkpoints[0]
    }
