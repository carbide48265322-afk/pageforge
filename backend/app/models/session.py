from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Message:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    role: str = "user"  # "user" | "assistant"
    content: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    tool_calls: list[dict] = field(default_factory=list)
    html_version: int | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "tool_calls": self.tool_calls,
            "html_version": self.html_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        return cls(**data)


@dataclass
class Session:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    messages: list[Message] = field(default_factory=list)
    current_base_version: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": [m.to_dict() for m in self.messages],
            "current_base_version": self.current_base_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        data["messages"] = [Message.from_dict(m) for m in data.get("messages", [])]
        return cls(**data)