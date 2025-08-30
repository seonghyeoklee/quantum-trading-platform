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

### 모니터링
- **Prometheus**: 메트릭 수집
- **Grafana**: 메트릭 시각화
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
| Axon Server | http://localhost:8024 | Event Store 대시보드 | - |
| PostgreSQL | localhost:5433 | Query DB | quantum/quantum123 |
| Redis | localhost:6379 | 캐시 | - |
| Kafka | localhost:9092 | 메시지 브로커 | - |
| Prometheus | http://localhost:9090 | 메트릭 수집 | - |
| Grafana | http://localhost:3000 | 모니터링 대시보드 | admin/quantum123 |
| Kiwoom API | http://localhost:10201 | 키움증권 API | - |
| KIS Mock API | http://localhost:8200 | 한투 Mock API | - |
| API Gateway | http://localhost:8080 | REST API | - |
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

## 📚 관련 문서

- [Axon Framework Documentation](https://docs.axoniq.io/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [Grafana Documentation](https://grafana.com/docs/)

## 🤝 기여하기

이슈나 개선사항이 있으면 GitHub Issues에 등록해주세요.