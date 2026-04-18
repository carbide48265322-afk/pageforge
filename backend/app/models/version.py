from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class PageVersion:
    """页面版本数据模型 — 每次生成/修改保存一个版本"""
    
    version: int = 0              # 版本号（自增）
    session_id: str = ""          # 所属会话 ID
    html: str = ""                # HTML 内容
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())  # 生成时间
    summary: str = ""             # 变更摘要（来自用户消息）
    parent_version: int|None = None  # 父版本号（None = 首次生成）
    trigger_message: str = ""     # 触发此版本的用户原始消息

    def to_dict(self) -> dict:
        """序列化为字典（不含 HTML 内容，用于版本列表展示）"""
        return {
            "version": self.version,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "summary": self.summary,
            "parent_version": self.parent_version,
            "trigger_message": self.trigger_message,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PageVersion":
        """从字典反序列化"""
        return cls(**data)