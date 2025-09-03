# 📋 기획 문서 구조

Quantum Trading Platform의 기획 및 설계 문서들을 체계적으로 정리한 디렉터리입니다.

## 📁 디렉터리 구조

```
docs/planning/
├── core/                           # 핵심 아키텍처 문서
│   ├── MVP_1.0_Authentication_Architecture.md    # 통합 인증 시스템
│   ├── MVP_1.0_Chart_System_Specification.md     # 차트 시스템 설계
│   └── MVP_1.0_DDD_Planning.md                   # 도메인 주도 설계
├── implementation/                 # 구현 가이드 문서
│   ├── KIS_Rate_Limit_Policy.md                  # API 제한 정책
│   ├── KIS_Adapter_Trading_Mode_Implementation.md # 거래모드 구현
│   ├── Domestic_Overseas_Chart_Integration.md     # 차트 통합 가이드
│   └── TRADING_MODE_GUIDE.md                     # 개발자 가이드
└── auto-trading/                   # 자동매매 MVP 1.1
    ├── MVP_1.1_Auto_Trading_Overview.md          # 자동매매 개요
    ├── MVP_1.1_Paper_Trading_Mode.md             # 모의투자 모드
    ├── MVP_1.1_Golden_Cross_Strategy.md          # 골든크로스 전략
    └── MVP_1.1_Minimal_Strategy_Design.md        # 최소 전략 설계
```

## 📖 문서별 설명

### 🏗️ Core (핵심 아키텍처)

**MVP_1.0_Authentication_Architecture.md**
- JWT + KIS 토큰 하이브리드 인증 시스템
- Frontend/Backend 인증 플로우
- 토큰 관리 및 보안 설계

**MVP_1.0_Chart_System_Specification.md**  
- 키움증권 스타일 차트 UI 설계
- 캔들스틱 + 이동평균선 + 거래량 차트
- 반응형 레이아웃 및 컴포넌트 구조

**MVP_1.0_DDD_Planning.md**
- 도메인 주도 설계 접근법
- 애그리게이트 및 바운디드 컨텍스트
- Spring Boot 엔티티 및 서비스 설계

### ⚙️ Implementation (구현 가이드)

**KIS_Rate_Limit_Policy.md**
- KIS API 호출 제한 정책
- Rate Limiting 구현 전략
- 에러 처리 및 백오프 로직

**KIS_Adapter_Trading_Mode_Implementation.md**
- LIVE/SANDBOX 거래 모드 구현
- FastAPI 기반 KIS Adapter 설계
- 환경별 서버 매핑 및 인증

**Domestic_Overseas_Chart_Integration.md**
- 국내/해외 차트 통합 전략
- 시장별 데이터 구조 차이 해결
- 통합 차트 컴포넌트 설계

**TRADING_MODE_GUIDE.md**
- 개발자용 거래모드 사용 가이드
- API 호출 예시 및 에러 처리
- 실무 개발 팁 및 트러블슈팅

### 🤖 Auto-Trading (자동매매 MVP 1.1)

**MVP_1.1_Auto_Trading_Overview.md**
- 자동매매 시스템 전체 개요
- SANDBOX/LIVE 이중 모드 아키텍처
- 사용자 시나리오 및 성공 지표

**MVP_1.1_Paper_Trading_Mode.md**
- 모의투자 구현 설계
- 가상 포트폴리오 관리
- 실전 전환 준비 방안

**MVP_1.1_Golden_Cross_Strategy.md**
- 골든크로스 전략 구현
- 5일선 > 20일선 돌파 신호
- 매매 신호 생성 및 실행

**MVP_1.1_Minimal_Strategy_Design.md**
- 최소 기능 전략 설계
- 확장 가능한 전략 프레임워크
- 플러그인 아키텍처 준비

## 🔄 문서 이력

**2025-09-03**: 기획 문서 구조 개편
- 중복 문서 통합 (KIS 토큰 아키텍처 2개 → 1개)
- core/implementation/auto-trading 3단계 구조로 재편
- 개발 단계별 문서 접근성 향상

## 📌 사용 가이드

1. **개발 시작 전**: core/ 디렉터리 문서로 전체 아키텍처 이해
2. **구현 단계**: implementation/ 디렉터리에서 구체적 가이드 참조
3. **자동매매 개발**: auto-trading/ 디렉터리로 MVP 1.1 준비

---

**관리자**: 기획자 (Planner)  
**최종 업데이트**: 2025-09-03