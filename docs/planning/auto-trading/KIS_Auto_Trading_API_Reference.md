# KIS 자동매매 API 함수 참조서

## 📖 개요

**대상**: Quantum Trading Platform MVP 1.1 자동매매 시스템 개발
**범위**: KIS Open API 자동매매 관련 모든 함수
**업데이트**: 2025-09-03
**담당**: 기획자 (Planner) + 분석가 (Analyst)

## 🔴 핵심 주문 API (매수/매도)

### 1. 현금 주문 (가장 기본)

#### `order_cash/`
**함수**: `order_cash()`  
**목적**: 현금 기반 주식 매수/매도 주문  
**중요도**: ⭐⭐⭐⭐⭐ (필수)

**주요 파라미터**:
- `ord_dv`: 주문구분 (`'buy'` | `'sell'`)
- `symbol`: 종목코드 (예: `'005930'`)  
- `ord_qty`: 주문수량
- `ord_prc`: 주문단가 (시장가: `'0'`)
- `ord_type`: 주문유형 (`'00'` 지정가, `'01'` 시장가)

**자동매매 활용**:
```python
# 매수 주문
result = ka.order_cash(
    ord_dv='buy',
    symbol='005930',
    ord_qty=10,
    ord_prc='71000',
    ord_type='00'  # 지정가
)

# 매도 주문  
result = ka.order_cash(
    ord_dv='sell',
    symbol='005930', 
    ord_qty=10,
    ord_prc='0',     # 시장가
    ord_type='01'
)
```

### 2. 신용 주문

#### `order_credit/`
**함수**: `order_credit()`  
**목적**: 신용거래 매수/매도 주문  
**중요도**: ⭐⭐⭐ (고급 기능)

**특징**:
- 증거금으로 더 큰 금액 거래 가능
- 신용한도 내에서 레버리지 거래
- 금리 비용 발생

### 3. 예약 주문

#### `order_resv/`  
**함수**: `order_resv()`
**목적**: 조건부 예약주문 (목표가 도달 시 자동 실행)
**중요도**: ⭐⭐⭐⭐ (자동매매 핵심)

**자동매매 활용**:
- 손절매 주문 (특정 가격 하락 시 자동 매도)
- 익절 주문 (목표 수익률 도달 시 자동 매도)
- 매수 타이밍 예약 (특정 가격 도달 시 자동 매수)

```python
# 손절매 예약 주문 예시
result = ka.order_resv(
    symbol='005930',
    ord_dv='sell',
    ord_qty=10,
    resv_prc='65000',  # 65,000원 도달시 매도
    ord_type='conditional'
)
```

## 🔵 주문 취소/정정 API

### 주문 취소/정정

#### `order_rvsecncl/`
**함수**: `order_rvsecncl()`  
**목적**: 미체결 주문 취소 또는 수량/가격 정정  
**중요도**: ⭐⭐⭐⭐ (필수)

**자동매매 활용**:
- 시장 상황 변화 시 주문 취소
- 더 나은 가격으로 주문 정정
- 미체결 주문 정리

```python
# 주문 취소
result = ka.order_rvsecncl(
    order_no='12345678',
    action='cancel'
)

# 주문 정정 (가격 변경)
result = ka.order_rvsecncl(
    order_no='12345678',
    action='modify',
    new_prc='72000',
    new_qty=5
)
```

#### `order_resv_rvsecncl/`
**함수**: `order_resv_rvsecncl()`
**목적**: 예약주문 취소
**중요도**: ⭐⭐⭐

## 🟢 잔고/자산 조회 API

### 1. 계좌 잔고

#### `inquire_balance/`
**함수**: `inquire_balance()`  
**목적**: 계좌 보유종목 조회  
**중요도**: ⭐⭐⭐⭐⭐ (필수)

**반환 정보**:
- 보유 종목 리스트
- 종목별 보유수량
- 평균매수가
- 현재 평가금액
- 평가손익

**자동매매 활용**:
```python
# 현재 보유종목 확인
balance = ka.inquire_balance()
for stock in balance['stocks']:
    symbol = stock['symbol']
    qty = stock['quantity']
    avg_price = stock['avg_buy_price']
    current_value = stock['current_value']
    profit_loss = stock['profit_loss']
    
    # 손익률 계산하여 매도 결정
    if profit_loss_rate > 0.1:  # 10% 이상 수익
        ka.order_cash(ord_dv='sell', symbol=symbol, ord_qty=qty)
```

#### `inquire_account_balance/`
**함수**: `inquire_account_balance()`
**목적**: 계좌 예수금 조회
**중요도**: ⭐⭐⭐⭐⭐ (필수)

**반환 정보**:
- 주문가능현금
- 총자산
- 총평가금액
- 예수금

### 2. 손익 조회

#### `inquire_balance_rlz_pl/`
**함수**: `inquire_balance_rlz_pl()`
**목적**: 실현손익 조회 (매도로 확정된 손익)
**중요도**: ⭐⭐⭐

### 3. 매도 가능 수량

#### `inquire_psbl_sell/`
**함수**: `inquire_psbl_sell()`
**목적**: 매도가능 수량 조회
**중요도**: ⭐⭐⭐⭐

**자동매매 활용**:
- 매도 주문 전 실제 매도 가능한 수량 확인
- 신용거래, 대출 등으로 인한 제약 확인

## 🟡 주문 가능 조회 API

### `inquire_psbl_order/`
**함수**: `inquire_psbl_order()`
**목적**: 매수가능 금액/수량 조회  
**중요도**: ⭐⭐⭐⭐⭐ (필수)

**자동매매 핵심 용도**:
```python
# 매수 전 가능 수량 계산
psbl_order = ka.inquire_psbl_order(symbol='005930', ord_prc='71000')
max_qty = psbl_order['max_order_qty']
available_cash = psbl_order['available_cash']

# 자금 관리: 보유 현금의 20%만 사용
target_amount = available_cash * 0.2
order_qty = int(target_amount / 71000)

if order_qty > 0:
    ka.order_cash(ord_dv='buy', symbol='005930', ord_qty=order_qty)
```

### `inquire_psbl_rvsecncl/`
**함수**: `inquire_psbl_rvsecncl()`
**목적**: 정정/취소 가능 조회
**중요도**: ⭐⭐⭐

## 🟣 체결 내역 조회 API

### 1. 당일 체결

#### `inquire_ccnl/`
**함수**: `inquire_ccnl()`
**목적**: 당일 체결 내역 조회
**중요도**: ⭐⭐⭐⭐⭐ (필수)

**자동매매 활용**:
```python
# 체결 확인 및 추가 주문 결정
ccnl_list = ka.inquire_ccnl()
for order in ccnl_list:
    if order['status'] == 'filled':  # 체결 완료
        symbol = order['symbol']
        filled_qty = order['filled_qty']
        filled_price = order['filled_price']
        
        # 체결된 주문에 따른 후속 전략 실행
        if order['ord_dv'] == 'buy':  # 매수 체결시
            # 익절/손절 예약주문 설정
            ka.order_resv(symbol=symbol, ord_dv='sell', 
                         resv_prc=filled_price * 1.05)  # 5% 익절
```

### 2. 체결 통보 (실시간)

#### `ccnl_notice/`
**함수**: `ccnl_notice()`
**목적**: 체결 발생 시 실시간 알림
**중요도**: ⭐⭐⭐⭐ (실시간 자동매매)

**WebSocket 연동**:
```python
# 실시간 체결 통보 수신
def on_ccnl_notice(data):
    symbol = data['symbol']
    filled_qty = data['filled_qty']
    filled_price = data['filled_price']
    
    # 즉시 후속 주문 실행
    if data['ord_dv'] == 'buy':
        # 매수 체결 즉시 손절매 주문
        ka.order_resv(symbol=symbol, ord_dv='sell', 
                     resv_prc=filled_price * 0.95)
```

### 3. 일자별 체결

#### `inquire_daily_ccld/`
**함수**: `inquire_daily_ccld()`
**목적**: 특정 날짜의 체결 내역 조회
**중요도**: ⭐⭐ (분석용)

## ⚪ 자동매매 시나리오 예시

### 기본 플로우 (Golden Cross 전략)

```python
def golden_cross_strategy():
    # 1. 현재 보유종목 확인
    balance = ka.inquire_balance()
    
    # 2. 주문가능 현금 확인  
    account = ka.inquire_account_balance()
    available_cash = account['available_cash']
    
    # 3. 매수 신호 확인 (Golden Cross 발생)
    if detect_golden_cross('005930'):
        # 4. 매수가능 수량 계산
        psbl_order = ka.inquire_psbl_order(symbol='005930', ord_prc='0')  # 시장가
        max_qty = psbl_order['max_order_qty']
        
        # 5. 자금 관리 (총 현금의 10%만 사용)
        target_amount = available_cash * 0.1
        current_price = get_current_price('005930')
        order_qty = min(int(target_amount / current_price), max_qty)
        
        if order_qty > 0:
            # 6. 매수 주문 실행
            order_result = ka.order_cash(
                ord_dv='buy',
                symbol='005930', 
                ord_qty=order_qty,
                ord_prc='0',      # 시장가
                ord_type='01'
            )
            
            # 7. 체결 확인
            time.sleep(1)  # 체결 대기
            ccnl = ka.inquire_ccnl()
            for order in ccnl:
                if order['order_no'] == order_result['order_no'] and order['status'] == 'filled':
                    filled_price = order['filled_price']
                    
                    # 8. 익절/손절 예약주문 설정
                    # 익절: 5% 상승시
                    ka.order_resv(
                        symbol='005930',
                        ord_dv='sell',
                        ord_qty=order_qty,
                        resv_prc=int(filled_price * 1.05)
                    )
                    
                    # 손절: 3% 하락시  
                    ka.order_resv(
                        symbol='005930',
                        ord_dv='sell', 
                        ord_qty=order_qty,
                        resv_prc=int(filled_price * 0.97)
                    )
                    break

def cleanup_strategy():
    """미체결 주문 정리"""
    ccnl = ka.inquire_ccnl()
    for order in ccnl:
        if order['status'] == 'pending':  # 미체결
            # 30분 이상 미체결 주문 취소
            if order['order_time_diff'] > 30:  
                ka.order_rvsecncl(
                    order_no=order['order_no'],
                    action='cancel'
                )
```

## 🔧 해외주식 자동매매 API

### `overseas_stock/`

#### 주요 함수들:
- `order/`: 해외주식 주문
- `order_rvsecncl/`: 해외주식 정정/취소  
- `inquire_balance/`: 해외주식 잔고
- `inquire_psamount/`: 해외주식 주문가능금액
- `inquire_ccnl/`: 해외주식 체결조회

**특징**:
- 미국/일본/홍콩/중국 주식 지원
- 환율 고려 필요
- 시차 고려 필요 (미국: 한국시간 밤 10:30-새벽 5:00)
- 부분체결 가능성 높음

```python
# 미국 주식 자동매매 예시
def us_stock_strategy():
    # 애플 주식 매수
    result = ka.overseas_stock.order(
        exchange='NYS',  # 뉴욕증권거래소
        symbol='AAPL',
        ord_dv='buy',
        ord_qty=10,
        ord_prc='0',     # 시장가
        ord_type='01'
    )
```

## 📍 특수 자동매매 기능

### 조건식 기반 자동매매

#### `order_resv/` (고급 활용)
**목적**: 복잡한 조건 설정으로 자동 주문 실행

**활용 예시**:
```python
# 목표가 도달 + RSI 조건 충족시 자동 매수
ka.order_resv(
    symbol='005930',
    ord_dv='buy',
    ord_qty=10,
    resv_prc='75000',        # 75,000원 도달시
    additional_condition={
        'rsi_below': 30,      # RSI 30 이하일 때
        'volume_surge': 1.5   # 평균 거래량 1.5배 이상
    }
)
```

### 시간외 거래
- `after_hour_balance/`: 시간외 잔고 조회
- `overtime_order/`: 시간외 주문 (장 시작 전/후)

### 연금계좌
- `pension_inquire_balance/`: 연금계좌 잔고
- `pension_inquire_psbl_order/`: 연금계좌 주문가능

## 🛡️ 자동매매 안전장치

### 1. 위험 관리
```python
def risk_management():
    # 일일 손실 한도 체크
    daily_pl = ka.inquire_balance_rlz_pl()
    if daily_pl['total_loss'] > MAX_DAILY_LOSS:
        # 모든 미체결 주문 취소
        cancel_all_pending_orders()
        return False
    
    # 총 투자 금액 한도 체크
    account = ka.inquire_account_balance()
    if account['total_investment'] > MAX_TOTAL_INVESTMENT:
        return False
        
    return True
```

### 2. 에러 처리
```python
def safe_order_execution():
    try:
        result = ka.order_cash(ord_dv='buy', symbol='005930', ord_qty=10)
        if result['rt_cd'] != '0':  # 오류 발생
            log_error(f"Order failed: {result['msg1']}")
            return False
    except Exception as e:
        log_error(f"API call failed: {str(e)}")
        return False
    return True
```

## 📊 자동매매 성능 모니터링

### 주요 지표
1. **체결률**: 주문 중 체결된 비율
2. **평균 체결 시간**: 주문부터 체결까지 소요 시간  
3. **슬리피지**: 예상가와 체결가 차이
4. **일일/월간 손익**: 자동매매 성과 추적

### API 활용 모니터링
```python
def performance_monitoring():
    # 오늘 체결 내역
    ccnl = ka.inquire_ccnl()
    
    total_orders = len(ccnl)
    filled_orders = len([o for o in ccnl if o['status'] == 'filled'])
    fill_rate = filled_orders / total_orders if total_orders > 0 else 0
    
    # 실현손익
    realized_pl = ka.inquire_balance_rlz_pl()
    
    return {
        'fill_rate': fill_rate,
        'total_realized_pl': realized_pl['total_pl'],
        'trade_count': total_orders
    }
```

---

## 🎯 MVP 1.1 구현 우선순위

### Phase 1 (핵심 기능)
1. `inquire_balance()` - 잔고 조회
2. `inquire_account_balance()` - 예수금 조회  
3. `inquire_psbl_order()` - 주문가능 조회
4. `order_cash()` - 현금 주문
5. `inquire_ccnl()` - 체결 확인

### Phase 2 (자동화)
1. `order_resv()` - 예약 주문 (익절/손절)
2. `order_rvsecncl()` - 주문 취소/정정
3. `ccnl_notice()` - 실시간 체결 통보

### Phase 3 (고도화) 
1. 해외주식 API
2. 신용거래 API
3. 연금계좌 API

**이 참조서는 Quantum Trading Platform MVP 1.1 자동매매 시스템 개발의 기술적 기반을 제공합니다.**