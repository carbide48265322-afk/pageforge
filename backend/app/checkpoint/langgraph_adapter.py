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
