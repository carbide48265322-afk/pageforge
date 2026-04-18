import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# 项目根目录（pageforge/）
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 数据目录
DATA_DIR = BASE_DIR / "data"
SESSIONS_DIR = DATA_DIR / "sessions"

# 模板目录
TEMPLATES_DIR = BASE_DIR / "templates"

# Skill 定义目录
SKILLS_DIR = BASE_DIR / "skills"

# LLM 配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", None)
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")

# 确保目录存在
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)