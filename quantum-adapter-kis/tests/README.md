# Tests Directory

정리된 테스트 파일들의 구조와 용도입니다.

## 📁 Directory Structure

### `/tests/dino/` - DINO 분석 시스템 테스트
- **`test_dino_finance.py`** - 재무분석 테스트 (D001)
- **`test_dino_material.py`** - 소재분석 테스트 (D003)
- **`test_dino_price.py`** - 가격분석 테스트 (D005)

### `/tests/trading/` - 실시간 매매 시스템 테스트
- **`test_realtime_trading.py`** - 완전한 실시간 자동매매 시스템 테스트
- **`test_simple_realtime.py`** - 간단한 실시간 매매 테스트

### `/tests/order/` - 주문 실행 테스트
- **`test_prod_order.py`** - 실전모드 주문 테스트

## 🚀 Test Execution

### DINO 분석 테스트
```bash
# 재무분석 테스트
uv run python tests/dino/test_dino_finance.py

# 소재분석 테스트
uv run python tests/dino/test_dino_material.py

# 가격분석 테스트
uv run python tests/dino/test_dino_price.py
```

### 실시간 매매 테스트
```bash
# 완전한 실시간 매매 시스템
uv run python tests/trading/test_realtime_trading.py

# 간단한 실시간 테스트
uv run python tests/trading/test_simple_realtime.py
```

### 주문 실행 테스트
```bash
# 실전모드 주문 테스트 (주의: 실제 계좌 사용)
uv run python tests/order/test_prod_order.py
```

## ⚠️ 주의사항

- **실전모드 테스트**: `tests/order/test_prod_order.py`는 실제 KIS 계좌를 사용합니다
- **인증 필요**: 모든 테스트는 KIS API 인증이 필요합니다 (`kis_devlp.yaml` 설정 필요)
- **환경 설정**: 실전투자(`prod`) vs 모의투자(`vps`) 환경을 구분하여 사용하세요

## 🗑️ 제거된 파일들

다음 파일들은 중복되거나 더 이상 필요하지 않아 제거되었습니다:
- `test_db_priority.py` - DB 우선순위 테스트
- `test_db_token.py` - DB 토큰 테스트 (파일 기반으로 전환)
- `test_main_db.py` - DB 메인 테스트
- `test_comprehensive_dino.py` - 중복된 DINO 테스트
- `test_technical_analysis.py` - 오래된 기술분석 테스트
- `test_insufficient_funds.py` - 임시 테스트 (목적 달성)