# Quantum Trading Platform - MVP 1.0 DDD 기획서

**📋 기획 히스토리 #005 - MVP 1.0 도메인 주도 설계 적용**

## 프로젝트 개요
- **버전**: MVP 1.0 (최초 출시 버전)
- **목적**: 한국투자증권 API 기반 자동매매 플랫폼 
- **환경**: 내부망 + VPN (보안 환경)
- **사용자**: 단일 사용자 (개발자 본인)
- **설계 철학**: Domain-Driven Design (DDD) 적용

## 버전별 기획 히스토리

### v1.0 (MVP - 최초 출시)
**목표**: 최소한의 로그인 + KIS API 연동 기반
**특징**: 
- 내부망 보안 환경 활용
- PostgreSQL 프로덕션 데이터베이스
- DDD 패턴 기반 확장 가능한 구조

### 향후 버전 로드맵
- **v1.1**: 포트폴리오 도메인, 계좌 관리 도메인 추가
- **v1.2**: 트레이딩 전략 도메인, 리스크 관리 도메인
- **v2.0**: 멀티 테넌트, 사용자 권한 도메인

---

## API 설계 (CURL 예제)

### 로그인 API
```bash
# 로그인
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@quantum.local",
    "password": "admin123"
  }'

# 응답
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "expires_in": 86400,
  "user": {
    "id": 1,
    "email": "admin@quantum.local", 
    "name": "Quantum Admin"
  }
}
```

### 인증된 요청
```bash
# 사용자 정보 조회
curl -X GET http://localhost:8080/api/v1/auth/me \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

# 응답
{
  "id": 1,
  "email": "admin@quantum.local",
  "name": "Quantum Admin",
  "last_login_at": "2025-09-01T10:30:00"
}
```

### 로그아웃
```bash
# 로그아웃
curl -X POST http://localhost:8080/api/v1/auth/logout \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

# 응답
{
  "message": "로그아웃 완료"
}
```

## 품질 속성 및 제약사항

### 비기능적 요구사항
- **성능**: 로그인 응답 시간 < 500ms
- **보안**: JWT 토큰 24시간 만료, 내부망 환경
- **가용성**: 99.9% (내부 사용)
- **확장성**: 추가 도메인 쉬운 통합
- **유지보수성**: DDD 패턴으로 도메인 로직 분리

### 기술적 제약사항
- PostgreSQL 15+ 필수
- JVM 21+ 환경
- 내부망 전용 (외부 접근 불가)
- 단일 인스턴스 배포

---

이 DDD 기반 MVP 1.0 설계는 향후 트레이딩 도메인, 포트폴리오 도메인 등을 쉽게 추가할 수 있는 확장 가능한 구조를 제공합니다.