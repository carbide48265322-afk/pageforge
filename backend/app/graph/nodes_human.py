"""人机协作节点 - 在关键决策点暂停等待用户输入"""
from app.graph.state import AgentState
from app.checkpoint.manager import CheckpointManager
from app.checkpoint.models import HumanInputType


async def human_input_node(state: AgentState) -> dict:
    """人机协作节点 - 保存检查点并等待用户响应
    
    根据当前阶段生成不同的表单 Schema，保存检查点后返回请求数据。
    图执行到此结束，等待用户通过 API 提交响应后继续。
    """
    
    checkpoint_manager = CheckpointManager()
    session_id = state["session_id"]
    phase = state.get("phase", "unknown")
    
    # 根据阶段生成不同的 Schema
    if phase == "prd_confirm":
        schema = {
            "type": "object",
            "title": "请确认需求文档",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["confirm", "revise"],
                    "title": "操作"
                },
                "feedback": {
                    "type": "string",
                    "title": "修改建议",
                    "description": "如需修改，请描述需要调整的地方"
                }
            },
            "required": ["action"]
        }
        context = {
            "prd": state.get("requirements_doc", ""),
            "design_concept": state.get("design_concept", "")
        }
    else:
        # 默认 Schema
        schema = {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["confirm", "revise"]}
            }
        }
        context = {}
    
    # 创建检查点
    request = await checkpoint_manager.create_human_input_checkpoint(
        session_id=session_id,
        phase=phase,
        input_type=HumanInputType.CONFIRM,
        title=schema.get("title", "请确认"),
        description="",
        schema=schema,
        context=context
    )
    
    return {
        "human_input_pending": True,
        "human_input_checkpoint_id": request["checkpoint_id"],
        "human_input_request": request,
        "status": "waiting_human"
    }
