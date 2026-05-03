# ─── Build stage ────────────────────────────────────────────
FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ─── Final stage ────────────────────────────────────────────
FROM python:3.13-slim

WORKDIR /app

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 后端依赖
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 后端代码
COPY backend/app/ ./app/

# 前端构建产物 → FastAPI 静态文件服务
COPY --from=frontend-builder /app/frontend/dist/ /app/static/

# 运行时数据目录
RUN mkdir -p /app/data/sessions /app/templates /app/skills

EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
