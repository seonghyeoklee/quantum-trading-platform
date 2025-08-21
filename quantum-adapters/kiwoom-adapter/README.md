# 키움증권 Python REST API 클라이언트

키움증권 REST API를 위한 Python FastAPI 서비스

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# Python 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일에서 키움 API 키 설정
```

### 2. 서버 실행
```bash
# 개발 서버 실행
uvicorn src.kiwoom_api.main:app --reload --port 8100

# 프로덕션 서버 실행
uvicorn src.kiwoom_api.main:app --host 0.0.0.0 --port 8100
```

### 3. API 문서 확인
- Swagger UI: http://localhost:8100/docs
- ReDoc: http://localhost:8100/redoc

## 📡 API 엔드포인트

### 인증
- `POST /oauth2/token` - 키움 OAuth 토큰 발급 (au10001)

## 🧪 테스트 실행

```bash
# 전체 테스트 실행
pytest

# 특정 테스트 실행
pytest tests/test_auth.py

# 커버리지 포함 테스트
pytest --cov=src/kiwoom_api
```

## 🔧 개발 도구

```bash
# 코드 포매팅
black src/ tests/
isort src/ tests/

# 린터 실행
flake8 src/ tests/
```

## 📋 환경변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `KIWOOM_APP_KEY` | 키움 API 앱키 | - |
| `KIWOOM_APP_SECRET` | 키움 API 시크릿키 | - |
| `KIWOOM_SANDBOX_MODE` | 키움 샌드박스 모드 | `true` |
| `FASTAPI_HOST` | 서버 호스트 | `0.0.0.0` |
| `FASTAPI_PORT` | 서버 포트 | `8001` |

## 🏗️ 아키텍처

```
src/kiwoom_api/
├── main.py              # FastAPI 메인 애플리케이션
├── config/
│   └── settings.py      # 환경변수 설정
├── auth/
│   ├── oauth_client.py  # OAuth 토큰 클라이언트
│   └── token_cache.py   # 토큰 캐싱
├── models/
│   ├── auth.py         # 인증 관련 모델
│   └── common.py       # 공통 응답 모델
└── api/
    └── auth.py         # 인증 API 라우터
```
