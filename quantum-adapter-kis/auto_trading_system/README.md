# 자동매매 시스템

실시간 종목별 터미널 모니터링과 전략 기반 자동매매를 제공하는 시스템입니다.

## 주요 기능

### 🎯 핵심 특징
- **종목별 터미널 모니터링**: 각 종목을 개별 터미널에서 실시간 모니터링
- **전략 패턴 구현**: 런타임에 매매 전략 변경 가능
- **포지션 관리**: 자동화된 포지션 생성/청산 및 손익 추적
- **리스크 관리**: 일일 거래 한도, 포지션 크기 제한 등 종합적 리스크 통제
- **KIS API 연동**: 실제 주문 실행 및 시뮬레이션 모드 지원

### 📊 지원 전략
1. **Golden Cross/Dead Cross**: 단기/장기 이동평균선 교차 신호
2. **RSI 전략**: 과매수/과매도 구간 및 다이버전스 탐지
3. **Volume Breakout**: 거래량 급증과 가격 돌파 조합
4. **Mean Reversion**: 볼린저 밴드 기반 평균회귀 전략

## 시스템 아키텍처

```
auto_trading_system/
├── core/                    # 핵심 엔진 및 관리자
│   ├── data_types.py       # 데이터 구조 정의
│   ├── trading_engine.py   # 메인 트레이딩 엔진
│   ├── position_manager.py # 포지션 관리
│   ├── risk_manager.py     # 리스크 관리
│   └── order_executor.py   # 주문 실행
├── strategies/             # 매매 전략 구현
│   ├── base_strategy.py    # 전략 인터페이스
│   ├── golden_cross_strategy.py
│   ├── rsi_strategy.py
│   ├── volume_breakout_strategy.py
│   └── mean_reversion_strategy.py
├── monitors/               # 터미널 UI
│   ├── stock_monitor.py    # 개별 종목 모니터
│   └── terminal_manager.py # 멀티 터미널 관리
├── config/                 # 설정 파일
│   └── example_config.json
├── main_app.py            # 메인 애플리케이션
├── test_system.py         # 시스템 테스트
└── README.md
```

## 설치 및 실행

### 1. 의존성 설치
```bash
# uv 사용 (권장)
uv sync

# 또는 pip 사용
pip install -r requirements.txt
```

### 2. 설정 파일 준비
```bash
# 예제 설정 파일을 복사하여 수정
cp auto_trading_system/config/example_config.json auto_trading_system/config/my_config.json
```

### 3. 시스템 테스트
```bash
# 시스템 테스트 실행
uv run python auto_trading_system/test_system.py
```

### 4. 메인 시스템 실행
```bash
# 기본 설정으로 실행
uv run python auto_trading_system/main_app.py

# 커스텀 설정으로 실행
uv run python auto_trading_system/main_app.py --config auto_trading_system/config/my_config.json --dry-run

# 실전 모드로 실행 (주의!)
uv run python auto_trading_system/main_app.py --config my_config.json --env prod
```

## 설정 파일 구조

```json
{
  "engine": {
    "max_positions": 5,         // 최대 동시 포지션 수
    "default_quantity": 100,    // 기본 주문 수량
    "execution_delay": 0.1      // 주문 실행 지연 (초)
  },
  "executor": {
    "environment": "vps",       // vps(모의) 또는 prod(실전)
    "dry_run": true,           // 시뮬레이션 모드
    "execution_delay": 0.5     // 실행 지연
  },
  "risk_config": {
    "max_daily_trades": 10,            // 일일 최대 거래 수
    "max_position_size": 1000000,      // 최대 포지션 크기 (원)
    "min_confidence_threshold": 0.6,   // 최소 신뢰도
    "trading_start_time": "09:00",     // 거래 시작 시간
    "trading_end_time": "15:30",       // 거래 종료 시간
    "max_volatility_threshold": 0.05,  // 최대 변동성
    "min_volume_threshold": 1000       // 최소 거래량
  },
  "stocks": [
    {
      "symbol": "005930",
      "name": "삼성전자",
      "strategy": "golden_cross",
      "strategy_config": {
        "fast_period": 5,
        "slow_period": 20,
        "min_confidence": 0.7
      }
    }
  ]
}
```

## 터미널 UI 사용법

### 키보드 단축키
- **Tab**: 다음 종목 탭으로 이동
- **Shift+Tab**: 이전 종목 탭으로 이동
- **1-9**: 종목 번호로 직접 이동
- **s**: 전략 변경 메뉴
- **r**: 화면 새로고침
- **q**: 종료

### 화면 구성
```
┌─ 삼성전자 (005930) - Golden Cross ─┐
│ 💰 75,000원 (+1,000 +1.35%)        │
│                                    │
│ 📈 가격 차트 (ASCII)                │
│ ████████████▲                      │
│                                    │
│ 📊 기술 지표                        │
│ • MA5: 74,500원                    │
│ • MA20: 73,200원                   │
│ • RSI: 65.5                       │
│                                    │
│ 📍 포지션                          │
│ • 상태: LONG 100주                 │
│ • 손익: +50,000원 (+6.7%)          │
│                                    │
│ 🎯 최근 신호                       │
│ • BUY 신호 (신뢰도: 0.75)          │
│ • 이유: Golden Cross 발생          │
└────────────────────────────────────┘
```

## 전략 상세 설명

### 1. Golden Cross 전략
- **신호**: 단기MA > 장기MA (매수), 단기MA < 장기MA (매도)
- **설정**: fast_period (기본 5), slow_period (기본 20)
- **특징**: 트렌드 추종 전략, 안정적이지만 지연성 존재

### 2. RSI 전략
- **신호**: RSI < 30 (매수), RSI > 70 (매도)
- **설정**: rsi_period (기본 14), 임계값 조정 가능
- **특징**: 과매수/과매도 구간 활용, 다이버전스 탐지

### 3. Volume Breakout 전략
- **신호**: 거래량 급증 + 가격 돌파
- **설정**: volume_multiplier (기본 1.5), breakout_threshold (기본 2%)
- **특징**: 강한 추세 시작점 포착

### 4. Mean Reversion 전략
- **신호**: 볼린저 밴드 하단 터치 (매수), 상단 터치 (매도)
- **설정**: bb_period (기본 20), bb_std_dev (기본 2.0)
- **특징**: 횡보장에서 효과적

## 리스크 관리 기능

### 자동 검증 항목
1. **신뢰도 검증**: 최소 신뢰도 미만 신호 거부
2. **거래 시간**: 장 시작/마감 전후 거래 제한
3. **일일 한도**: 종목별/전체 일일 거래 횟수 제한
4. **포지션 크기**: 단일 포지션 최대 크기 제한
5. **변동성 체크**: 과도한 변동성 시 거래 중단
6. **거래량 확인**: 최소 거래량 미만 시 거래 제한

### 긴급 정지 기능
```python
# 긴급 상황 시 모든 거래 차단
system.risk_manager.emergency_stop()
```

## API 연동

### KIS API 설정
1. `kis_devlp.yaml` 파일에서 API 키 설정
2. 환경 변수로 계좌 정보 설정
3. 실전/모의 환경 선택

### 실행기 모드
- **dry_run=True**: 시뮬레이션 모드 (실제 주문 없음)
- **dry_run=False**: 실제 주문 실행 (주의 필요)

## 모니터링 및 로깅

### 로그 레벨
- **INFO**: 일반적인 시스템 동작
- **WARNING**: 리스크 위반 및 주의사항
- **ERROR**: 시스템 오류
- **CRITICAL**: 긴급 정지 등 심각한 상황

### 실시간 모니터링
- 포지션 손익 실시간 업데이트
- 신호 생성 즉시 알림
- 주문 체결 상태 추적
- 리스크 지표 실시간 표시

## 주의사항

### ⚠️ 실전 사용 시 주의점
1. **소액으로 시작**: 처음에는 적은 금액으로 테스트
2. **리스크 설정**: 본인의 투자 성향에 맞게 리스크 파라미터 조정
3. **모니터링**: 시스템 가동 중 정기적인 모니터링 필수
4. **긴급 정지**: 문제 발생 시 즉시 시스템 중단할 수 있도록 준비

### 🔒 보안 고려사항
1. **API 키 보안**: kis_devlp.yaml 파일 보안 관리
2. **로그 파일**: 민감한 정보 포함 가능, 접근 권한 제한
3. **네트워크**: 안전한 네트워크 환경에서 실행

## 문제 해결

### 자주 발생하는 문제
1. **KIS API 연결 실패**: 토큰 만료, 네트워크 문제
2. **전략 실행 오류**: 데이터 부족, 설정 오류
3. **터미널 화면 깨짐**: 터미널 크기 조정 필요

### 디버깅 방법
```bash
# 로그 레벨을 DEBUG로 설정
export LOG_LEVEL=DEBUG

# 테스트 모드로 실행
uv run python auto_trading_system/main_app.py --dry-run --config test_config.json
```

## 개발자 정보

- **전략 패턴**: 새로운 전략 추가 시 BaseStrategy 상속
- **이벤트 시스템**: 커스텀 이벤트 핸들러 추가 가능
- **UI 확장**: Rich 라이브러리 기반 터미널 UI 커스터마이징
- **데이터 소스**: 다양한 데이터 제공자 추가 가능

## 라이선스

이 프로젝트는 교육 및 연구 목적으로 개발되었습니다. 실전 사용 시 발생하는 손실에 대한 책임은 사용자에게 있습니다.