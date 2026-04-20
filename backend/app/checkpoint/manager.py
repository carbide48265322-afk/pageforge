"""Checkpoint 管理器 - 用于人机协作的暂停/恢复"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional

import redis
from redis.exceptions import RedisError

from .models import CheckpointData, HumanInputResponse, HumanInputRequest, HumanInputType, CheckpointType


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
    
    # ---- 人机协作专用方法 ----
    
    async def create_human_input_checkpoint(
        self,
        session_id: str,
        phase: str,
        input_type: HumanInputType,
        title: str,
        description: str,
        schema: dict,
        context: dict,
        ttl: int = DEFAULT_TTL
    ) -> HumanInputRequest:
        """创建人机协作检查点
        
        Args:
            session_id: 会话ID
            phase: 当前阶段
            input_type: 输入类型
            title: 表单标题
            description: 说明文字
            schema: JSON Schema 定义表单结构
            context: 上下文数据
            ttl: 过期时间（秒）
            
        Returns:
            HumanInputRequest: 人机协作请求
        """
        checkpoint_id = f"human_{session_id}_{phase}_{int(datetime.utcnow().timestamp())}"
        now = datetime.utcnow()
        expires_at = now + timedelta(seconds=ttl)
        
        request: HumanInputRequest = {
            "checkpoint_id": checkpoint_id,
            "session_id": session_id,
            "phase": phase,
            "input_type": input_type.value,
            "title": title,
            "description": description,
            "schema": schema,
            "context": context,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat()
        }
        
        checkpoint: CheckpointData = {
            "session_id": session_id,
            "checkpoint_id": checkpoint_id,
            "phase": phase,
            "checkpoint_type": CheckpointType.HUMAN_INPUT.value,
            "status": "waiting_human",
            "state": {},
            "presentation": {"title": title, "description": description},
            "options": [],
            "human_input_request": request,
            "human_input_response": None,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat()
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
            # 添加到会话索引
            self._redis.zadd(session_key, {checkpoint_id: now.timestamp()})
            self._redis.expire(session_key, ttl)
            
            return request
        except RedisError as e:
            raise RuntimeError(f"Failed to create human input checkpoint: {e}")
    
    async def submit_human_response(
        self,
        checkpoint_id: str,
        action: str,
        data: dict,
        ttl: int = 86400  # 1天
    ) -> HumanInputResponse:
        """提交人机协作响应
        
        Args:
            checkpoint_id: 检查点ID
            action: 用户操作
            data: 用户填写的数据
            ttl: 过期时间（秒）
            
        Returns:
            HumanInputResponse: 用户响应
            
        Raises:
            ValueError: 检查点不存在或状态不正确
        """
        checkpoint = await self.load(checkpoint_id)
        if not checkpoint:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")
        
        if checkpoint.get("status") != "waiting_human":
            raise ValueError(f"Checkpoint status is {checkpoint.get('status')}, expected waiting_human")
        
        now = datetime.utcnow()
        response: HumanInputResponse = {
            "checkpoint_id": checkpoint_id,
            "action": action,
            "data": data,
            "responded_at": now.isoformat()
        }
        
        # 更新检查点状态
        checkpoint["human_input_response"] = response
        checkpoint["status"] = "completed"
        
        key = self._make_key(checkpoint_id)
        
        try:
            self._redis.setex(
                key,
                ttl,
                json.dumps(checkpoint, default=str)
            )
            
            return response
        except RedisError as e:
            raise RuntimeError(f"Failed to submit human response: {e}")
    
    async def get_waiting_checkpoints(
        self,
        session_id: str
    ) -> list[CheckpointData]:
        """获取会话中等待用户响应的检查点
        
        Args:
            session_id: 会话ID
            
        Returns:
            等待中的检查点列表
        """
        checkpoints = await self.list_by_session(session_id)
        return [cp for cp in checkpoints if cp.get("status") == "waiting_human"]
    
    async def get_checkpoint_by_phase(
        self,
        session_id: str,
        phase: str
    ) -> Optional[CheckpointData]:
        """获取指定阶段的检查点
        
        Args:
            session_id: 会话ID
            phase: 阶段名称
            
        Returns:
            检查点数据或 None
        """
        checkpoints = await self.list_by_session(session_id)
        for cp in checkpoints:
            request = cp.get("human_input_request")
            if request and request.get("phase") == phase:
                return cp
        return None
