import json
from pathlib import Path
from app.models.version import PageVersion
from app.config import SESSIONS_DIR


class VersionService:
    """版本管理服务 — HTML 存文件系统，元数据存 JSON"""

    def __init__(self):
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    def _session_dir(self, session_id: str) -> Path:
        """获取会话目录路径"""
        return SESSIONS_DIR / session_id

    def _versions_meta_path(self, session_id: str) -> Path:
        """获取版本元数据列表文件路径"""
        return self._session_dir(session_id) / "versions.json"

    def _html_path(self, session_id: str, version: int) -> Path:
        """获取某个版本 HTML 文件路径（如 v1.html）"""
        return self._session_dir(session_id) / f"v{version}.html"

    def _load_versions_meta(self, session_id: str) -> list[dict]:
        """从 JSON 文件加载版本元数据列表"""
        meta_path = self._versions_meta_path(session_id)
        if not meta_path.exists():
            return []
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_versions_meta(self, session_id: str, versions: list[dict]) -> None:
        """将版本元数据列表写入 JSON 文件"""
        self._session_dir(session_id).mkdir(parents=True, exist_ok=True)
        with open(self._versions_meta_path(session_id), "w", encoding="utf-8") as f:
            json.dump(versions, f, ensure_ascii=False, indent=2)

    def save_version(
        self,
        session_id: str,
        html: str,
        summary: str,
        trigger_message: str,
        parent_version: int | None = None,
    ) -> PageVersion:
        """保存新版本 — HTML 写文件，元数据追加到 JSON 列表"""
        versions = self._load_versions_meta(session_id)
        next_version = len(versions) + 1  # 版本号自增

        # 将 HTML 写入独立文件
        html_path = self._html_path(session_id, next_version)
        html_path.parent.mkdir(parents=True, exist_ok=True)  # 确保目录存在
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        # 创建版本对象
        version = PageVersion(
            version=next_version,
            session_id=session_id,
            html=html,
            summary=summary,
            parent_version=parent_version,
            trigger_message=trigger_message,
        )

        # 追加到元数据列表
        versions.append(version.to_dict())
        self._save_versions_meta(session_id, versions)

        return version

    def get_version(self, session_id: str, version: int) -> PageVersion | None:
        """获取指定版本的完整数据（含 HTML 内容）"""
        versions = self._load_versions_meta(session_id)
        for v in versions:
            if v["version"] == version:
                # 从文件读取 HTML
                html_path = self._html_path(session_id, version)
                with open(html_path, "r", encoding="utf-8") as f:
                    html = f.read()
                return PageVersion.from_dict({**v, "html": html})
        return None

    def get_latest_version(self, session_id: str) -> PageVersion | None:
        """获取最新版本"""
        versions = self._load_versions_meta(session_id)
        if not versions:
            return None
        latest = versions[-1]
        return self.get_version(session_id, latest["version"])

    def get_all_versions(self, session_id: str) -> list[dict]:
        """获取所有版本元数据（不含 HTML 内容，用于版本列表展示）"""
        return self._load_versions_meta(session_id)

    def get_html(self, session_id: str, version: int) -> str | None:
        """仅获取指定版本的 HTML 内容"""
        html_path = self._html_path(session_id, version)
        if not html_path.exists():
            return None
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()