# Quantum Trading Platform - 통합 Infrastructure

모니터링, 데이터 파이프라인, 로깅을 위한 완전한 infrastructure 스택

## 🏗️ 포함된 서비스

### 📊 모니터링 스택
- **Grafana**: 시각화 대시보드 (포트 3001)
- **Prometheus**: 메트릭 수집 및 저장 (포트 9090)  
- **Loki**: 로그 집계 및 저장 (포트 3100)
- **Promtail**: 로그 수집 에이전트

### 🔧 데이터 파이프라인  
- **Apache Airflow**: 워크플로우 관리 (포트 8081)
- **PostgreSQL**: 통합 데이터베이스 (포트 5432)

### 🌐 네트워킹
- **quantum-network**: 모든 서비스가 동일한 Docker 네트워크에서 실행

## 🚀 빠른 시작

### 1. Infrastructure 시작
```bash
cd quantum-infrastructure
./start-infrastructure.sh
```

### 2. Infrastructure 중지
```bash
./stop-infrastructure.sh
```

### 3. 수동 실행 (고급 사용자)
```bash
# 전체 스택 시작
docker-compose up -d

# 특정 서비스만 시작
docker-compose up -d grafana prometheus
docker-compose up -d airflow-webserver airflow-scheduler
```

## 🌐 서비스 URL

| 서비스 | URL | 인증 정보 |
|--------|-----|----------|
| 📈 Grafana | http://localhost:3001 | admin / quantum2024 |
| 🔧 Airflow | http://localhost:8081 | admin / quantum123 |
| 🔍 Prometheus | http://localhost:9090 | 없음 |
| 📝 Loki | http://localhost:3100 | 없음 |

## 💾 데이터베이스

| 목적 | 포트 | 인증 정보 | 사용처 |
|------|------|----------|--------|
| PostgreSQL | 5432 | quantum / quantum123 | 트레이딩 플랫폼 & Airflow 통합 |

## 📋 DAG 관리

### KIS 휴장일 수집 DAG
- **스케줄**: 매일 오전 6시
- **목적**: KIS API에서 국내 휴장일 데이터 수집
- **저장소**: `kis_domestic_holidays` 테이블

### DAG 수동 실행
```bash
# REST API로 DAG 트리거
TIMESTAMP=$(date +%s)
curl -X POST "http://localhost:8081/api/v1/dags/kis_holiday_sync/dagRuns" \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n 'admin:quantum123' | base64)" \
  -d "{\"dag_run_id\": \"manual_${TIMESTAMP}\"}"
```

## 🔧 구성 파일

- **docker-compose.yml**: 통합 infrastructure 정의
- **.env**: 환경 변수 설정
- **monitoring/**: Grafana, Prometheus, Loki 설정
- **airflow/**: Airflow DAG 및 설정

## 🐛 문제 해결

### 네트워크 문제
```bash
# quantum-network 재생성
docker network rm quantum-network
docker network create quantum-network
```

### 데이터 초기화
```bash
# 모든 데이터 볼륨 삭제 (주의!)
docker-compose down -v
```

### 서비스 로그 확인
```bash
# 특정 서비스 로그
docker logs airflow-scheduler
docker logs quantum-grafana

# 모든 서비스 로그
docker-compose logs
```

## 📈 모니터링

### Grafana 대시보드
- **Spring Boot Metrics**: 애플리케이션 성능
- **PostgreSQL Metrics**: 데이터베이스 성능  
- **System Metrics**: 서버 리소스
- **Custom Dashboards**: 비즈니스 메트릭

### 알림 설정
- **Slack Integration**: 중요 이벤트 알림
- **Email Alerts**: 시스템 장애 알림
- **Webhook Notifications**: 사용자 정의 통합

## 🛡️ 보안

### 기본 인증
- 모든 웹 UI는 기본 인증 사용
- 프로덕션에서는 강력한 비밀번호로 변경 필요

### 네트워크 보안
- 내부 통신은 Docker 네트워크 사용
- 필요한 포트만 호스트에 노출

### 데이터 보안
- 모든 데이터베이스 연결은 암호화
- 볼륨은 호스트에 안전하게 저장