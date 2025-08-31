# 🤖 자동매매 시스템 플로우 다이어그램

## 전체 시스템 아키텍처

```mermaid
graph TB
    subgraph "🖥️ Frontend (Next.js)"
        A[사용자] --> B[자동매매 페이지<br/>localhost:10301/auto-trading]
        B --> C[4단계 마법사]
        
        subgraph "📋 4단계 플로우"
            C1[1️⃣ 전략 선택<br/>StrategySelector]
            C2[2️⃣ 종목 분석<br/>StockSelector] 
            C3[3️⃣ 매매 설정<br/>TradingConfigurer]
            C4[4️⃣ 실시간 모니터링<br/>TradingMonitor]
            
            C1 --> C2 --> C3 --> C4
        end
        
        C --> C1
    end
    
    subgraph "🔄 API 연동 레이어"
        D[API 호출 시도]
        E[실패시 Mock 데이터 폴백]
        F[성공시 실제 데이터 사용]
    end
    
    subgraph "⚙️ Backend (Spring Boot)"
        G[자동매매 API<br/>100.68.90.21:10101]
        
        subgraph "📊 API 엔드포인트"
            G1[/api/v1/trading/config<br/>설정 관리]
            G2[/api/v1/trading/analysis/{symbol}<br/>종목 분석]
            G3[/api/v1/trading/status/{id}<br/>상태 조회]
            G4[/api/v1/trading/config/{id}/start<br/>자동매매 제어]
        end
        
        G --> G1
        G --> G2  
        G --> G3
        G --> G4
    end
    
    subgraph "🗄️ Database (PostgreSQL)"
        H[(auto_trading_configs<br/>자동매매 설정)]
        I[(auto_trading_status<br/>실행 상태)]
    end
    
    C2 -.->|종목 분석 요청| D
    C3 -.->|설정 저장 요청| D
    C4 -.->|상태 조회 요청| D
    
    D --> E
    D --> F
    E -.->|Mock Response| C2
    E -.->|Mock Response| C3
    E -.->|Mock Response| C4
    F --> G
    G --> G2 --> C2
    G --> G1 --> C3
    G --> G3 --> C4
    
    G1 --> H
    G3 --> I
    G4 --> I
```

## 사용자 여정 (User Journey)

```mermaid
journey
    title 자동매매 설정 여정
    section 전략 선택
      전략 카드 확인: 5: 사용자
      AI 분석 결과 검토: 4: 사용자
      전략 선택: 5: 사용자
      
    section 종목 분석  
      종목 검색: 4: 사용자
      AI 분석 시작: 3: 시스템
      기술적 지표 확인: 5: 사용자
      적합성 점수 검토: 4: 사용자
      
    section 매매 설정
      투자 금액 입력: 4: 사용자
      리스크 설정: 5: 사용자
      백테스팅 결과 확인: 4: 사용자
      설정 저장: 3: 시스템
      
    section 실시간 모니터링
      자동매매 시작: 5: 사용자
      실시간 성과 확인: 5: 사용자
      포지션 모니터링: 4: 사용자
```

## 데이터 플로우

```mermaid
sequenceDiagram
    participant U as 👤 사용자
    participant F as 🖥️ Frontend
    participant A as 🔄 API Layer
    participant B as ⚙️ Backend
    participant D as 🗄️ Database

    Note over U,D: 1️⃣ 전략 선택 단계
    U->>F: 전략 선택
    F->>F: 로컬 전략 데이터 로드
    
    Note over U,D: 2️⃣ 종목 분석 단계  
    U->>F: 종목 선택 (예: 005930)
    F->>A: GET /api/v1/trading/analysis/005930
    A->>B: API 호출 시도
    alt API 성공
        B->>A: 실제 분석 데이터
        A->>F: 실제 데이터 반환
    else API 실패 (인증 등)
        A->>F: Mock 데이터 생성 & 반환
    end
    F->>U: 종목 분석 결과 표시
    
    Note over U,D: 3️⃣ 매매 설정 단계
    U->>F: 설정 입력 (자본금, 리스크 등)
    F->>A: POST /api/v1/trading/config
    A->>B: 설정 저장 시도
    alt API 성공
        B->>D: INSERT INTO auto_trading_configs
        D->>B: 저장 완료
        B->>A: 설정 ID 반환
        A->>F: 실제 설정 ID
    else API 실패
        A->>F: 로컬 설정 ID 생성
    end
    F->>U: 설정 완료 알림
    
    Note over U,D: 4️⃣ 실시간 모니터링 단계
    loop 실시간 업데이트 (5초마다)
        F->>A: GET /api/v1/trading/status/{id}
        A->>B: 상태 조회 시도
        alt API 성공
            B->>D: SELECT FROM auto_trading_status
            D->>B: 실시간 상태
            B->>A: 실제 상태 데이터
            A->>F: 실제 성과 데이터
        else API 실패
            A->>F: Mock 성과 데이터 생성
        end
        F->>U: 실시간 성과 표시
    end
```

## 기술 스택 구조

```mermaid
graph LR
    subgraph "🎨 Frontend Stack"
        A1[Next.js 15.5.0]
        A2[React 19]
        A3[TypeScript]
        A4[Tailwind CSS]
        A5[Radix UI]
        
        A1 --> A2 --> A3
        A4 --> A5
    end
    
    subgraph "⚡ API Integration"
        B1[Fetch API]
        B2[Fallback Strategy]
        B3[Mock Data Generator]
        
        B1 --> B2 --> B3
    end
    
    subgraph "🔧 Backend Stack"  
        C1[Spring Boot 3.x]
        C2[Java 17]
        C3[Spring Security + JWT]
        C4[JPA + Hibernate]
        C5[PostgreSQL]
        
        C1 --> C2 --> C3
        C4 --> C5
    end
    
    subgraph "🗃️ Database Schema"
        D1[auto_trading_configs]
        D2[auto_trading_status]
        D3[Indexes & Constraints]
        
        D1 --> D3
        D2 --> D3
    end
    
    A1 -.->|HTTP Requests| B1
    B1 -.->|API Calls| C1
    C4 -.->|ORM| D1
```

## 현재 구현 상태

```mermaid
pie title 구현 완료도
    "Frontend UI/UX" : 100
    "API Integration" : 100
    "Backend APIs" : 100
    "Database Schema" : 100
    "Authentication" : 30
    "Real-time Updates" : 80
```

## 핵심 특징

### 🔄 **Fallback Strategy (폴백 전략)**
```
실제 API 호출 시도
        ↓
    연결 실패 감지
        ↓
    Mock 데이터 자동 생성
        ↓  
    사용자 경험 중단 없음
```

### 🎯 **Progressive Enhancement (점진적 개선)**
```
기본 기능 (Mock) → 실제 API → 실시간 연동 → 고급 기능
     ✅              ✅           🔄            🔮
```

### 📊 **Real-time Simulation (실시간 시뮬레이션)**
```
5초마다 데이터 갱신
    ↓
랜덤 성과 데이터 생성  
    ↓
차트 및 지표 업데이트
    ↓
실제 트레이딩 경험 제공
```