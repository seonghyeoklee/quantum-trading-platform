FROM python:3.13-slim

WORKDIR /app

# curl 설치 (healthcheck용)
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 의존성 먼저 복사 (캐시 레이어)
COPY pyproject.toml .

# 의존성 설치
RUN uv sync --no-dev --no-install-project

# 소스 복사
COPY app/ app/

# 프로젝트 설치
RUN uv sync --no-dev

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
