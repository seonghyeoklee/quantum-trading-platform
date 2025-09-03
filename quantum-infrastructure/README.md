# Quantum Trading Platform - 인프라 & 모니터링

Grafana + Loki + Prometheus + Promtail을 사용한 통합 로그 모니터링 시스템

## 🚀 시작하기

### 1. 모니터링 시스템 실행

```bash
cd quantum-infrastructure
docker-compose -f docker-compose.monitoring.yml up -d
```

### 2. 웹 UI 접근

- **Grafana**: http://localhost:3001 (admin/quantum2024)
- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100

### 3. 서비스 실행 (로그 생성용)

```bash
# Spring Boot API (터미널 1)
cd quantum-web-api
./gradlew bootRun --args='--spring.profiles.active=docker'

# FastAPI KIS Adapter (터미널 2)  
cd quantum-adapter-kis
uv run python main.py

# Next.js Frontend (터미널 3)
cd quantum-web-client
npm run dev
```

## 📊 대시보드 기능

### 🔍 통합 로그 모니터링
- **실시간 로그 스트림**: 3개 서비스 통합 로그 확인
- **서비스별 로그 분포**: 파이 차트로 서비스별 로그 비중
- **로그 레벨별 추이**: ERROR, WARN, INFO 레벨 시간별 변화
- **에러 로그 필터링**: 에러와 경고 로그만 별도 표시

### ⚡ API 성능 모니터링
- **응답시간 분석**: P95, P50 응답시간 추이
- **HTTP 상태코드**: 2xx, 4xx, 5xx 요청 분포
- **API 엔드포인트별**: 특정 API 성능 추적

### 🎯 KIS API 모니터링
- **KIS API 호출 성공률**: 성공/실패 비율
- **거래소별 API 사용량**: 국내/해외 API 호출 분포
- **토큰 사용 추이**: 인증 토큰 사용 패턴

## 🛠️ 설정 및 구성

### 로그 수집 방식
```
서비스 → 로그 파일 (JSON) → Promtail → Loki → Grafana
```

### 로그 파일 위치
- **Spring Boot**: `quantum-web-api/logs/*.log`
- **FastAPI**: `quantum-adapter-kis/logs/*.log`
- **Next.js**: `quantum-web-client/logs/*.log`

### 로그 보존 정책
- **로그 보존기간**: 7일
- **최대 저장용량**: 1GB
- **로그 로테이션**: 일별 자동 로테이션

## 🔧 고급 설정

### Grafana 알림 설정

1. **에러율 임계값 알림**
```bash
# 5분간 에러율이 5% 초과 시 알림
sum(rate({job="quantum-web-api", level="ERROR"}[5m])) 
/ sum(rate({job="quantum-web-api"}[5m])) > 0.05
```

2. **API 응답시간 알림**
```bash
# P95 응답시간이 3초 초과 시 알림
quantile_over_time(0.95, {job="quantum-web-api"} 
| json | unwrap response_time_ms [5m]) > 3000
```

### Loki 쿼리 예시

1. **특정 심볼 관련 로그 검색**
```bash
{job="quantum-adapter-kis"} |= "005930"
```

2. **API 에러만 필터링**
```bash
{job="quantum-web-api", level="ERROR", event_type="api_request"}
```

3. **응답시간이 긴 API 요청**
```bash
{job="quantum-web-api"} | json | response_time_ms > 1000
```

## 🚨 트러블슈팅

### 로그가 수집되지 않는 경우

1. **로그 파일 경로 확인**
```bash
ls -la quantum-*/logs/
```

2. **Promtail 컨테이너 로그 확인**
```bash
docker logs quantum-promtail
```

3. **권한 문제 해결**
```bash
chmod 755 quantum-*/logs/
chmod 644 quantum-*/logs/*.log
```

### Grafana 대시보드 복원

```bash
# 대시보드 JSON 파일 위치
ls monitoring/grafana/dashboards/

# 컨테이너 재시작
docker-compose -f docker-compose.monitoring.yml restart grafana
```

## 📈 성능 모니터링 지표

### 시스템 리소스
- **메모리 사용량**: JVM 힙 메모리, Python 프로세스 메모리
- **CPU 사용률**: 각 서비스별 CPU 점유율
- **디스크 I/O**: 로그 파일 쓰기 성능

### 애플리케이션 메트릭
- **동시 연결수**: WebSocket 연결, HTTP 세션
- **처리량**: 초당 API 요청 수, 초당 로그 생성 수
- **에러율**: 서비스별 에러 발생 비율

## 🎛️ 환경별 설정

### 개발 환경 (Development)
- 모든 로그 레벨 수집 (DEBUG 포함)
- 실시간 로그 스트리밍 활성화
- 상세한 API 응답시간 추적

### 운영 환경 (Production)
- INFO 레벨 이상만 수집
- 성능 최적화된 로그 수집
- 알림 및 모니터링 강화

## 🔐 보안 고려사항

### 민감정보 마스킹
- KIS API 토큰 자동 마스킹
- 사용자 비밀번호 로그 제외
- JWT 토큰 부분 마스킹

### 접근 제어
- Grafana 관리자 계정 변경 필수
- 로그 접근 권한 제한
- 네트워크 방화벽 설정 권장