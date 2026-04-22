import json
from pathlib import Path
from app.models.session import Session, Message
from app.config import SESSIONS_DIR


class SessionService:
    """会话管理服务 — 使用文件系统存储会话元数据"""

    def __init__(self):
        # 确保数据目录存在
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    def _session_dir(self, session_id: str) -> Path:
        """获取会话目录路径"""
        return SESSIONS_DIR / session_id

    def _meta_path(self, session_id: str) -> Path:
        """获取会话元数据文件路径"""
        return self._session_dir(session_id) / "meta.json"

    def create_session(self) -> Session:
        """创建新会话，自动生成 UUID"""
        session = Session()
        self._save(session)
        return session

    def get_session(self, session_id: str) -> Session | None:
        """根据 ID 获取会话，不存在返回 None"""
        meta_path = self._meta_path(session_id)
        if not meta_path.exists():
            return None
        with open(meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Session.from_dict(data)

    def save_session(self, session: Session) -> None:
        """保存会话到文件"""
        self._save(session)

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_calls: list[dict] | None = None,
        html_version: int | None = None,
    ) -> Session:
        """向会话添加一条消息，并自动更新 updated_at"""
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        msg = Message(
            session_id=session_id,
            role=role,
            content=content,
            tool_calls=tool_calls or [],
            html_version=html_version,
        )
        session.messages.append(msg)
        session.updated_at = msg.timestamp
        self._save(session)
        return session

    def _save(self, session: Session) -> None:
        """内部方法：将会话序列化为 JSON 写入文件"""
        session_dir = self._session_dir(session.id)
        session_dir.mkdir(parents=True, exist_ok=True)
        with open(self._meta_path(session.id), "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)