# Kiwoom Python API Service Dockerfile
FROM python:3.11-slim

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Poetry 설치
RUN pip install --no-cache-dir poetry

# 프로젝트 의존성 파일 복사
COPY pyproject.toml requirements.txt* ./

# Poetry 설정 (가상환경 생성 비활성화)
RUN poetry config virtualenvs.create false

# 의존성 설치 (requirements.txt 사용)
RUN if [ -f "requirements.txt" ]; then \
        pip install --no-cache-dir -r requirements.txt; \
    else \
        echo "No requirements.txt found"; \
    fi

# 애플리케이션 소스 코드 복사
COPY src/ ./src/

# 포트 노출
EXPOSE 8100

# 헬스체크용 엔드포인트를 위한 curl 설치 확인
RUN curl --version

# 애플리케이션 실행
CMD ["python", "-m", "uvicorn", "src.kiwoom_api.main:app", "--host", "0.0.0.0", "--port", "8100", "--reload"]