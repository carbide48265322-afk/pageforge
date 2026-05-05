import os
from pathlib import Path
from types import SimpleNamespace
from dotenv import load_dotenv

# 项目根目录（pageforge/）
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 加载 .env 文件
load_dotenv(BASE_DIR / ".env")

# 数据目录
DATA_DIR = BASE_DIR / "data"
SESSIONS_DIR = DATA_DIR / "sessions"

# 模板目录
TEMPLATES_DIR = BASE_DIR / "templates"

# Skill 定义目录
SKILLS_DIR = BASE_DIR / "skills"

# 工具目录
TOOLS_DIR = BASE_DIR / "backend" / "app" / "tools" / "v2"

# 确保目录存在
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

# ─── 模型名称配置（保留环境变量名向后兼容） ────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", None)
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
INTENT_MODEL_NAME = os.getenv("INTENT_MODEL_NAME", "gpt-4o-mini")
EXECUTE_MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")

# ─── 智能路由集成 ─────────────────────────────────────────
# 新代码请使用：
#   from app.core.model_router import get_llm_by_tier, get_model_for_node
#
# 以下向后兼容变量保持不变，内部委托给 model_router：

class _LazyLLM:
    """延迟加载的 LLM 代理（兼容旧代码 `from app.config import llm`）"""

    def __init__(self, tier: str):
        self._tier = tier
        self._instance = None

    def _get(self):
        if self._instance is None:
            from app.core.model_router import get_llm_by_tier
            self._instance = get_llm_by_tier(self._tier)
        return self._instance

    def invoke(self, *args, **kwargs):
        return self._get().invoke(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._get(), name)


# 向后兼容：code_gen.py 等旧代码 `from app.config import llm` 仍然有效
llm = _LazyLLM("chat")
intent_llm = _LazyLLM("lite")
