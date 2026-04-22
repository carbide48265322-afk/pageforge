import os
from pathlib import Path
from langchain_openai import ChatOpenAI
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
TOOLS_DIR = BASE_DIR / "backend" / "app" / "graph"

# LLM 配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", None)
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")

# 确保目录存在
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

# 意图识别模型 — 轻量快速，不需要 thinking
INTENT_MODEL_NAME = os.getenv("INTENT_MODEL_NAME", "gpt-4o-mini")

# 执行模型 — 需要 thinking 能力（如 DeepSeek-R1、o1 等）
EXECUTE_MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")

# 意图识别 LLM 客户端
intent_llm = ChatOpenAI(
    model=INTENT_MODEL_NAME,
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
    temperature=0.3,
    max_tokens=1024,
)

# 执行 LLM 客户端 — 用于 ReAct 循环生成 HTML
llm = ChatOpenAI(
    model=EXECUTE_MODEL_NAME,
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
    temperature=0.7,
    max_tokens=4096,
)