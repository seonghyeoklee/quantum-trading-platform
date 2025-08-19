# Quantum Trading Platform

Axon Framework 기반 Event-Driven 주식 자동매매 플랫폼

## 🎯 프로젝트 개요

Axon Framework를 활용한 CQRS/Event Sourcing 기반의 주식 자동매매 플랫폼입니다. 한국투자증권, 키움증권 등 다중 증권사 API를 지원하며, 마이크로서비스 아키텍처로 설계되었습니다.

## 🏗️ 아키텍처

### 모듈 구조

```
quantum-trading-platform/
├── platform-core/              # Axon 기반 핵심 도메인
│   ├── shared-kernel/          # 공통 도메인 (Value Objects, Events)
│   ├── trading-command/        # Command Side (Aggregate, Command Handler)
│   ├── trading-query/          # Query Side (Projection, Query Handler)
│   └── platform-infrastructure/# Axon 설정 & 인프라
├── broker-integration/         # 다중 증권사 연동
│   ├── broker-common/          # 공통 증권사 인터페이스
│   ├── kis-adapter/           # 한국투자증권 구현체
│   ├── kiwoom-adapter/        # 키움증권 구현체
│   └── integration-saga/      # 증권사 연동 Saga
├── client-api/                # 클라이언트 API
│   ├── web-api/              # REST API Gateway
│   ├── websocket-api/        # 실시간 WebSocket
│   └── mobile-api/           # 모바일 API
└── data-platform/            # 데이터 처리
    ├── market-collector/     # 시세 수집
    ├── data-processor/       # 실시간 데이터 처리
    └── analytics-engine/     # 분석 엔진
```

### 기술 스택

- **Framework**: Axon Framework 4.9.1
- **Language**: Java 21
- **Build**: Gradle 8.x
- **Database**: PostgreSQL 15 (Query Side), Axon Server (Event Store)
- **Caching**: Redis 7
- **Messaging**: Kafka 7.4 (외부 통합)
- **Monitoring**: Prometheus + Grafana
- **Container**: Docker + Docker Compose

## 🚀 빠른 시작

### 1. 인프라 시작

```bash
# Docker Compose로 전체 인프라 시작
docker-compose up -d

# 서비스 상태 확인
docker-compose ps
```

### 2. 접속 정보

- **Axon Server UI**: http://localhost:8024
- **Grafana**: http://localhost:3000 (admin/quantum123)
- **Prometheus**: http://localhost:9090
- **PostgreSQL**: localhost:5432 (quantum/quantum123)
- **Redis**: localhost:6379

### 3. 애플리케이션 빌드 & 실행

```bash
# 전체 프로젝트 빌드
./gradlew build

# 특정 모듈 실행
./gradlew :platform-core:trading-command:bootRun
./gradlew :client-api:web-api:bootRun
```

## 🎯 핵심 기능

### Event-Driven 주문 처리

1. **주문 생성**: Web API → CreateOrderCommand → TradingOrder Aggregate
2. **검증**: OrderCreatedEvent → BrokerIntegrationSaga → Portfolio 검증
3. **증권사 전송**: 검증 완료 → 증권사 API 호출
4. **결과 처리**: 체결/실패 → Event 발행 → 상태 업데이트

### 다중 증권사 지원

- **공통 인터페이스**: BrokerApiClient
- **KIS Adapter**: 한국투자증권 구현체
- **Kiwoom Adapter**: 키움증권 구현체 (향후)
- **동적 선택**: 사용자 설정/수수료/가용성 기반

### CQRS/Event Sourcing

- **Command Side**: 비즈니스 로직 처리, Event 발행
- **Query Side**: 조회 최적화 Projection
- **Event Store**: 모든 상태 변경 이벤트 저장
- **Replay**: 이벤트 재생을 통한 상태 복원

## 📊 모니터링

### Grafana 대시보드

- **시스템 메트릭**: CPU, Memory, Disk
- **애플리케이션 메트릭**: Request Rate, Response Time, Error Rate
- **비즈니스 메트릭**: 주문 처리량, 체결률, 수익률
- **Axon 메트릭**: Command 처리량, Event 처리량, Saga 상태

### 로그 수집

- **구조화된 로깅**: JSON 형태 로그
- **분산 추적**: Trace ID를 통한 요청 추적
- **에러 모니터링**: 실시간 에러 알림

## 🛡️ 보안

### API 보안

- **JWT 인증**: Stateless 토큰 기반 인증
- **RBAC**: 역할 기반 접근 제어
- **Rate Limiting**: API 호출 제한

### 증권사 API 보안

- **토큰 관리**: 자동 갱신 및 안전한 저장
- **API Key 암호화**: 환경변수 + 암호화 저장
- **접근 제한**: IP 화이트리스트

## 🧪 테스트

### Test Fixtures

```bash
# Axon Test Fixtures 활용
./gradlew test

# 통합 테스트 (TestContainers)
./gradlew integrationTest

# E2E 테스트
./gradlew e2eTest
```

### Test 전략

- **Unit Test**: Aggregate, Command Handler 단위 테스트
- **Integration Test**: Saga, Projection 통합 테스트
- **E2E Test**: 전체 플로우 테스트

## 📚 학습 자료

### Axon Framework

- [공식 문서](https://docs.axoniq.io/reference-guide/)
- [Event Sourcing 가이드](https://martinfowler.com/eaaDev/EventSourcing.html)
- [CQRS 패턴](https://docs.microsoft.com/en-us/azure/architecture/patterns/cqrs)

### 주식 자동매매

- [한국투자증권 API](https://apiportal.koreainvestment.com/)
- [키움증권 API](https://www3.kiwoom.com/nkw.templateFrameSet.do?m=m1408000000)

## 🤝 기여

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이센스

이 프로젝트는 학습 목적으로 제작되었습니다. 실제 거래에 사용 시 발생하는 손실에 대해 책임지지 않습니다.

## 🔗 관련 링크

- [Legacy 프로젝트](./legacy/README.md)
- [API 문서](./docs/api.md)
- [배포 가이드](./docs/deployment.md)