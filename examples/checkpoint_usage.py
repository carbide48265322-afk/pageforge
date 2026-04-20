"""CheckpointManager 使用示例

运行方式:
    cd backend && uv run python ../examples/checkpoint_usage.py
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# 添加 backend 到路径
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

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
        "responded_at": datetime.now(timezone.utc).isoformat()
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
