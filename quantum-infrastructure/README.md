# Quantum Trading Platform - Infrastructure

## 📋 개요

Quantum Trading Platform의 전체 인프라를 Docker Compose로 관리합니다.

## 🏗️ 서비스 구성

### 핵심 인프라
- **Axon Server**: Event Store & CQRS 메시지 버스
- **PostgreSQL**: Query Side 데이터베이스
- **Redis**: 캐싱 레이어
- **Kafka + Zookeeper**: 이벤트 스트리밍 플랫폼

### 브로커 서비스
- **Kiwoom API Server**: 키움증권 OpenAPI 연동 서버
- **KIS Mock API**: 한국투자증권 Mock API 서버

### 애플리케이션
- **API Gateway**: REST API 게이트웨이
- **Batch Processor**: 배치 처리 서비스

### 모니터링 & 관측가능성
- **Prometheus**: 메트릭 수집 및 저장
- **Grafana**: 메트릭 시각화 및 대시보드
- **Loki**: 로그 수집 및 저장
- **Promtail**: 로그 수집 에이전트  
- **Tempo**: 분산 트레이싱
- **AlertManager**: 알림 관리 및 라우팅
- **InfluxDB**: 시계열 데이터 저장

### 메트릭 익스포터
- **PostgreSQL Exporter**: 데이터베이스 메트릭
- **Redis Exporter**: 캐시 메트릭
- **Kafka Exporter**: 메시지 브로커 메트릭
- **cAdvisor**: 컨테이너 리소스 메트릭

### 관리 도구
- **Kafka UI**: Kafka 관리 UI
- **Redis Commander**: Redis 관리 UI

## 🚀 빠른 시작

### 1. 전체 서비스 시작
```bash
cd quantum-infrastructure
./start.sh up all
```

### 2. 단계별 시작
```bash
# 1단계: 인프라 시작
./start.sh up infra

# 2단계: 브로커 서비스 시작
./start.sh up brokers

# 3단계: 애플리케이션 시작
./start.sh up apps

# 4단계: 모니터링 도구 시작
./start.sh up monitoring
```

### 3. 서비스 종료
```bash
./start.sh stop
```

### 4. 모든 데이터 삭제
```bash
./start.sh clean
```

## 📊 서비스 접속 정보

| 서비스 | URL/Port | 용도 | 인증정보 |
|--------|----------|------|----------|
| **핵심 인프라** | | | |
| Axon Server | http://localhost:8024 | Event Store 대시보드 | - |
| PostgreSQL | localhost:5433 | Query DB | quantum/quantum123 |
| Redis | localhost:6379 | 캐시 | - |
| Kafka | localhost:9092 | 메시지 브로커 | - |
| InfluxDB | http://localhost:8086 | 시계열 데이터베이스 | quantum/quantum123 |
| **애플리케이션** | | | |
| Quantum Web API | http://localhost:10101 | Spring Boot API | - |
| Kiwoom Adapter | http://localhost:10201 | 키움증권 API 어댑터 | - |
| Quantum Web Client | http://localhost:10301 | Next.js 웹 클라이언트 | - |
| **모니터링** | | | |
| Prometheus | http://localhost:9090 | 메트릭 수집 | - |
| Grafana | http://localhost:3000 | 모니터링 대시보드 | admin/quantum123 |
| Loki | http://localhost:3100 | 로그 수집 | - |
| Tempo | http://localhost:3200 | 분산 트레이싱 | - |
| AlertManager | http://localhost:9093 | 알림 관리 | - |
| **익스포터** | | | |
| PostgreSQL Exporter | http://localhost:9187 | PostgreSQL 메트릭 | - |
| Redis Exporter | http://localhost:9121 | Redis 메트릭 | - |
| Kafka Exporter | http://localhost:9308 | Kafka 메트릭 | - |
| cAdvisor | http://localhost:8080 | 컨테이너 메트릭 | - |
| **관리 도구** | | | |
| Kafka UI | http://localhost:8090 | Kafka 관리 | - |
| Redis Commander | http://localhost:8091 | Redis 관리 | - |

## 🔧 명령어 사용법

### 서비스 관리
```bash
# 서비스 상태 확인
./start.sh status

# 로그 확인 (전체)
./start.sh logs

# 특정 서비스 로그 확인
./start.sh logs axon-server

# 서비스 재시작
./start.sh restart

# Docker 이미지 빌드
./start.sh build
```

### Docker Compose 직접 사용
```bash
# 환경변수 파일 지정하여 실행
docker-compose --env-file .env.docker up -d

# 특정 서비스만 시작
docker-compose --env-file .env.docker up -d postgres redis

# 로그 스트리밍
docker-compose --env-file .env.docker logs -f

# 서비스 중지
docker-compose --env-file .env.docker down

# 볼륨 포함 삭제
docker-compose --env-file .env.docker down -v
```

## 📁 디렉토리 구조

```
quantum-infrastructure/
├── docker-compose.yml        # Docker Compose 설정
├── .env.docker              # 환경변수 설정
├── start.sh                 # 실행 스크립트
├── README.md               # 이 파일
├── config/                 # 서비스별 설정 파일
│   └── kiwoom/            # 키움증권 설정
├── logs/                   # 애플리케이션 로그
│   ├── api/               # API Gateway 로그
│   └── batch/             # Batch 로그
└── infrastructure/         # 인프라 설정
    ├── prometheus/        # Prometheus 설정
    │   └── prometheus.yml
    └── grafana/          # Grafana 설정
        ├── provisioning/
        └── dashboards/
```

## 🔍 트러블슈팅

### 포트 충돌
```bash
# 사용 중인 포트 확인
lsof -i :8024  # Axon Server
lsof -i :5433  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :9092  # Kafka

# 포트 변경이 필요한 경우 docker-compose.yml 수정
```

### 메모리 부족
```bash
# Docker Desktop 메모리 할당 증가 (최소 8GB 권장)
# Docker Desktop > Preferences > Resources > Memory
```

### 서비스 연결 실패
```bash
# 네트워크 확인
docker network ls
docker network inspect quantum-infrastructure_quantum-network

# 서비스 재시작
./start.sh restart
```

### Tempo TraceQL 오류 해결
```bash
# Tempo 컨테이너 재시작
docker-compose restart tempo

# Tempo 로그 확인
docker-compose logs tempo

# TraceQL 쿼리는 간단한 형태로 시작
# 올바른 예: {service.name="quantum-web-api"}
# 잘못된 예: service.name="quantum-web-api" (중괄호 없음)
```

### 볼륨 권한 문제
```bash
# 볼륨 권한 수정
sudo chown -R $USER:$USER ./logs
sudo chmod -R 755 ./logs
```

## 🔐 보안 주의사항

- 프로덕션 환경에서는 반드시 비밀번호 변경
- `.env.docker` 파일은 git에 커밋하지 않음
- 방화벽 설정으로 불필요한 포트 차단
- SSL/TLS 인증서 적용 권장

## 📈 모니터링 및 알림

### Grafana 대시보드

시스템에서 제공하는 주요 대시보드:

## 🎯 핵심 모니터링 대시보드

1. **핵심 모니터링 대시보드** (`quantum-core-monitoring`) 
   - **시스템 가용성**: 전체 서비스 가용성 실시간 모니터링
   - **응답시간 분석**: 50th, 95th, 99th percentile HTTP 응답시간
   - **처리량 & 에러율**: RPS 및 HTTP 에러율 (4xx/5xx)
   - **시스템 리소스**: 컨테이너 CPU/메모리 사용률
   - **데이터베이스 성능**: PostgreSQL, Redis, Kafka 핵심 메트릭

2. **고급 성능 분석 대시보드** (`quantum-performance-advanced`)
   - **상세 Percentile 분석**: 50th~99.9th percentile 응답시간
   - **HTTP 상태코드별 처리량**: 2xx/4xx/5xx 상세 분석
   - **Apdex Score**: Application Performance Index 계산
   - **리소스 효율성**: CPU 할당 대비 사용률 분석
   - **네트워크 & 디스크 I/O**: 상세 처리량 분석

3. **비즈니스 메트릭 대시보드** (`quantum-business-metrics`)
   - 거래 처리 속도 및 성공률
   - 시장 데이터 처리량 및 지연 시간 (95th/99th percentile)
   - 서비스 가용성 및 에러 발생률
   - 컨테이너 리소스 사용률

4. **인프라 & 리소스 최적화 대시보드** (`quantum-infrastructure`)
   - PostgreSQL 데이터베이스 활동 및 연결 상태
   - Redis 캐시 히트율 및 메모리 사용량
   - Kafka 메시지 처리율 및 Consumer Lag
   - 컨테이너 CPU, 메모리, 네트워크, 디스크 I/O

5. **관측가능성 대시보드** (`observability-dashboard`)
   - 통합 시스템 관측가능성
   - 로그, 메트릭 통합 뷰

### 알림 체계

AlertManager를 통한 다단계 알림 시스템:

#### 심각도별 분류 (95th/99th percentile 기반)
- **Critical**: 
  - 서비스 중단 (가용성 < 99%)
  - 심각한 에러율 (25% 이상)
  - 심각한 응답 지연 (99th percentile > 5초)
  - 메모리 사용률 > 95%
- **Warning**: 
  - 높은 에러율 (10% 이상)
  - 응답 지연 (95th percentile > 2초)
  - 리소스 사용률 높음 (85% 이상)
  - Apdex Score < 0.7
- **Info**: 
  - 서비스 복구
  - 낮은 거래량
  - 성능 개선 알림

#### 알림 채널
- **#quantum-critical**: 심각한 시스템 알림
- **#quantum-alerts**: 일반 경고 알림
- **#quantum-trading**: 비즈니스 관련 알림
- **#quantum-infra**: 인프라 관련 알림
- **#quantum-info**: 정보성 알림

#### 환경 변수 설정
```bash
# Slack 웹훅 URL
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# 이메일 설정 (Critical 알림용)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_FROM=alerts@quantum-trading.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL_TO=admin@quantum-trading.com
```

## 🔧 메트릭 및 로그 수집

### Prometheus 메트릭 수집 대상

1. **애플리케이션 메트릭**
   - Quantum Web API: `/actuator/prometheus`
   - Kiwoom Adapter: `/metrics`
   - Axon Server: `/actuator/prometheus`

2. **인프라 메트릭**
   - PostgreSQL: PostgreSQL Exporter
   - Redis: Redis Exporter  
   - Kafka: Kafka Exporter
   - 컨테이너: cAdvisor

3. **모니터링 시스템**
   - Prometheus, Grafana, Loki, Tempo, AlertManager 자체 메트릭

### 로그 수집 및 분석

- **Loki**: 중앙화된 로그 저장소
- **Promtail**: 컨테이너 로그 자동 수집
- **로그 보존**: 30일 (설정 가능)
- **로그 레이블링**: 서비스명, 환경, 레벨별 자동 태깅

### 분산 트레이싱

- **Tempo**: OpenTelemetry 호환 트레이싱
- **자동 상관관계**: 로그-메트릭-트레이싱 연결
- **성능 분석**: 서비스 간 지연시간 및 병목 구간 식별

## 📚 관련 문서

- [Axon Framework Documentation](https://docs.axoniq.io/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Loki Documentation](https://grafana.com/docs/loki/)
- [Tempo Documentation](https://grafana.com/docs/tempo/)

## 🤝 기여하기

이슈나 개선사항이 있으면 GitHub Issues에 등록해주세요.