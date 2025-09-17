# 로그 디렉토리 구조

## 디렉토리 설명

### `trading/signals/`
- 실시간 매매 신호 로그
- 파일명 형식: `{symbols}_signals_{YYYYMMDD_HHMMSS}.log`
- 예시: `AAPL_TSLA_NVDA_signals_20250918_120000.log`

### `trading/orders/`
- 실제 주문 실행 로그
- 파일명 형식: `{symbols}_orders_{YYYYMMDD_HHMMSS}.log`
- 예시: `AAPL_TSLA_NVDA_orders_20250918_120000.log`

### `trading/daily/`
- 일별 거래 요약 로그
- 파일명 형식: `daily_summary_{YYYYMMDD}.log`
- 예시: `daily_summary_20250918.log`

## 로그 보존 정책
- 신호 로그: 30일 보존
- 주문 로그: 90일 보존
- 일별 요약: 1년 보존