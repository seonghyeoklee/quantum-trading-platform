# Google Sheets VLOOKUP 공식 완전 매뉴얼

## 📋 개요
구글 시트에서 사용되는 모든 VLOOKUP 공식을 체계적으로 기록하여 추후 Python 구현 시 정확한 로직 구현이 가능하도록 합니다.

## 🏗️ 평가기준표 ('디노테스트_평가기준' 시트)

### 재무 영역 코드표
| 코드 | 평가항목 | 부여기준 | 점수 |
|------|----------|----------|------|
| A001 | 매출증가 10%이상 | 매출증가율 ≥ 10% | +1 |
| A002 | 영업이익률 10%이상 | 영업이익률 ≥ 10% | +1 |
| A003 | 전년 대비 영업이익 흑자 전환 | 적자→흑자 | +1 |
| A004 | 유보율 1,000% 이상 | 유보율 ≥ 1,000% | +1 |
| A005 | 부채비율 50% 이하 | 부채비율 ≤ 50% | +1 |
| A006 | 전년 대비 매출 감소 | 매출 감소 | -1 |
| A007 | 영업이익 적자 전환 | 흑자→적자 | -1 |
| A008 | 영업이익 적자 지속 | 적자→적자 | -2 |
| A009 | 유보율 300% 이하 | 유보율 ≤ 300% | -1 |
| A010 | 부채비율 200% 이상 | 부채비율 ≥ 200% | -1 |

### 기술 영역 코드표
| 코드 | 평가항목 | 부여기준 | 점수 |
|------|----------|----------|------|
| B001 | OBV만족 | OBV 조건 만족 | +1 |
| B002 | 투자심리도침체 (25%이하) | 투자심리도 ≤ 25% | +1 |
| B003 | RSI침체 (30%이하) | RSI ≤ 30% | +1 |
| B004 | OBV불만족 | OBV 조건 불만족 | -1 |
| B005 | 투자심리도과열 (75%이상) | 투자심리도 ≥ 75% | -1 |
| B006 | RSI과열 (70%이상) | RSI ≥ 70% | -1 |

### 가격 영역 코드표
| 코드 | 평가항목 | 부여기준 | 점수 |
|------|----------|----------|------|
| C001 | -40% 이상 | 52주 대비 위치 ≤ -40% | +3 |
| C002 | -30% 이상 | 52주 대비 위치 ≤ -30% | +2 |
| C003 | -20% 이상 | 52주 대비 위치 ≤ -20% | +1 |
| C004 | +300% 이상 | 52주 대비 위치 ≥ +300% | -3 |
| C005 | +200% 이상 | 52주 대비 위치 ≥ +200% | -2 |
| C006 | +100% 이상 | 52주 대비 위치 ≥ +100% | -1 |

### 재료 영역 코드표
| 코드 | 평가항목 | 부여기준 | 점수 |
|------|----------|----------|------|
| D001 | 구체화된 이벤트/호재 임박 | 호재 임박 | +1 |
| D002 | 확실한 주도 테마 | 주도 테마 | +1 |
| D003 | 기관/외국인 수급 | 최근 1~3개월, 상장주식수 1% 이상 | +1 |
| D004 | 고배당 | 배당수익률 ≥ 2% | +1 |
| D005 | 어닝서프라이즈 | 실적 서프라이즈 | +1 |
| D006 | 불성실 공시 | 불성실 공시 | -1 |
| D007 | 악재뉴스 | 대형 클레임, 계약취소 등 | -1 |
| D008 | 호재뉴스 도배 | 호재뉴스 도배 | +1 |
| D009 | 이자보상배율 | 이자보상배율 < 1 | -1 |

### 기타
| 코드 | 평가항목 | 부여기준 | 점수 |
|------|----------|----------|------|
| Z999 | 해당없음 | 기타 모든 경우 | 0 |

---

## 📊 재무 영역 VLOOKUP 공식 모음

### 1. 매출액 (전년 대비 증감률)

**공식**:
```excel
=VLOOKUP(IF(($D24-$D23)/$D23*100>=10,"A001",IF(($D23>$D24),"A006","Z999")),'디노테스트_평가기준'!B:D,3,FALSE)
```

**셀 참조**:
- `$D23`: 전년도 매출액
- `$D24`: 당년도 매출액

**로직 분해**:
```
1. 증감률 계산: ($D24-$D23)/$D23*100
2. 조건 분기:
   - 증감률 ≥ 10% → A001 (+1점)
   - 당년 < 전년 (감소) → A006 (-1점)
   - 기타 (0~10% 증가) → Z999 (0점)
```

**Python 구현**:
```python
def calculate_sales_score(current_sales, previous_sales):
    growth_rate = (current_sales - previous_sales) / previous_sales * 100
    
    if growth_rate >= 10:
        return 1    # A001: 매출증가 10%이상
    elif current_sales < previous_sales:
        return -1   # A006: 전년 대비 매출 감소
    else:
        return 0    # Z999: 해당없음
```

### 2. 영업이익 (전년 대비 흑자/적자 전환)

**공식**:
```excel
=VLOOKUP(IF(AND($D25>0,$D26<0),"A007",(IF(AND($D25<0,$D26<0),"A008",(IF(AND($D25<0,$D26>0),"A003","Z999"))))),'디노테스트_평가기준'!B:D,3,FALSE)
```

**셀 참조**:
- `$D25`: 전년도 영업이익
- `$D26`: 당년도 영업이익

**로직 분해**:
```
1. 전년 흑자(>0) AND 당년 적자(<0) → A007 (-1점): 적자 전환
2. 전년 적자(<0) AND 당년 적자(<0) → A008 (-2점): 적자 지속
3. 전년 적자(<0) AND 당년 흑자(>0) → A003 (+1점): 흑자 전환
4. 기타 (전년 흑자 AND 당년 흑자) → Z999 (0점): 흑자 지속
```

**Python 구현**:
```python
def calculate_operating_profit_score(previous_profit, current_profit):
    if previous_profit > 0 and current_profit < 0:
        return -1   # A007: 영업이익 적자 전환
    elif previous_profit < 0 and current_profit < 0:
        return -2   # A008: 영업이익 적자 지속
    elif previous_profit < 0 and current_profit > 0:
        return 1    # A003: 전년 대비 영업이익 흑자 전환
    else:
        return 0    # Z999: 해당없음 (흑자 지속)
```

### 3. 영업이익률 (절대값 평가)

**공식**: ✅ **확인완료**
```excel
=VLOOKUP(IF($D27>=10,"A002","Z999"),'디노테스트_평가기준'!B:D,3,FALSE)
```

**셀 참조**:
- `$D27`: 영업이익률 (%)

**로직 분해**:
```
1. 영업이익률 ≥ 10% → A002 (+1점)
2. 기타 (영업이익률 < 10%) → Z999 (0점)
```

**Python 구현**:
```python
def calculate_operating_margin_score(operating_margin):
    if operating_margin >= 10:
        return 1    # A002: 영업이익률 10%이상
    else:
        return 0    # Z999: 해당없음
```

### 4. 유보율 (절대값 평가)

**공식**: ✅ **확인완료**
```excel
=VLOOKUP(IF($D28>=1000,"A004",IF($D28<=300,"A009","Z999")),'디노테스트_평가기준'!B:D,3,FALSE)
```

**셀 참조**:
- `$D28`: 유보율 (%)

**로직 분해**:
```
1. 유보율 ≥ 1,000% → A004 (+1점): 유보율 1,000% 이상
2. 유보율 ≤ 300% → A009 (-1점): 유보율 300% 이하
3. 기타 (300% < 유보율 < 1,000%) → Z999 (0점): 해당없음
```

**Python 구현**:
```python
def calculate_retention_ratio_score(retention_ratio):
    if retention_ratio >= 1000:
        return 1    # A004: 유보율 1,000% 이상
    elif retention_ratio <= 300:
        return -1   # A009: 유보율 300% 이하
    else:
        return 0    # Z999: 해당없음
```

### 5. 부채비율 (절대값 평가)

**공식**: ✅ **확인완료**
```excel
=VLOOKUP(IF($D29>=200,"A010",IF($D29<=50,"A005","Z999")),'디노테스트_평가기준'!B:D,3,FALSE)
```

**셀 참조**:
- `$D29`: 부채비율 (%)

**로직 분해**:
```
1. 부채비율 ≥ 200% → A010 (-1점): 부채비율 200% 이상 (위험)
2. 부채비율 ≤ 50% → A005 (+1점): 부채비율 50% 이하 (우수)
3. 기타 (50% < 부채비율 < 200%) → Z999 (0점): 해당없음
```

**Python 구현**:
```python
def calculate_debt_ratio_score(debt_ratio):
    if debt_ratio >= 200:
        return -1   # A010: 부채비율 200% 이상
    elif debt_ratio <= 50:
        return 1    # A005: 부채비율 50% 이하
    else:
        return 0    # Z999: 해당없음
```

---

## 📈 기술 영역 VLOOKUP 공식 모음

*(추가 확인 필요 - 사용자 제공 예정)*

### 1. OBV (On-Balance Volume)

**평가 공식**: ✅ **확인완료**
```excel
=VLOOKUP(IF(UPPER($D31)="Y","B001","B004"),'디노테스트_평가기준'!B:D,3,FALSE)
```

**OBV 계산 공식**: ✅ **확인완료**
```excel
=SPARKLINE(query(OBV(GOOGLEFINANCE(JOIN(":",$F$19,$G$19),"ALL", TODAY()-800, TODAY())),"select Col7"))
```

**셀 참조**:
- `$D31`: OBV 만족 여부 ("Y" 또는 "N")
- `$F$19`: 시장 코드 (예: "KRX")
- `$G$19`: 종목 코드 (예: "034020")

**로직 분해**:
```
1. OBV 계산:
   - GOOGLEFINANCE로 최근 800일(약 2년) 데이터 수집
   - OBV(On-Balance Volume) 지표 계산
   - SPARKLINE으로 그래프 생성
   
2. OBV 평가:
   - UPPER($D31) = "Y" → B001 (+1점): OBV만족
   - 기타 ("N" 또는 다른 값) → B004 (-1점): OBV불만족
```

**Python 구현**:
```python
def calculate_obv_score(obv_satisfied):
    """
    OBV 점수 계산
    obv_satisfied: True/False 또는 "Y"/"N"
    """
    if isinstance(obv_satisfied, str):
        obv_satisfied = obv_satisfied.upper() == "Y"
    
    if obv_satisfied:
        return 1    # B001: OBV만족
    else:
        return -1   # B004: OBV불만족

def calculate_obv_indicator(prices, volumes):
    """
    실제 OBV 지표 계산
    prices: 종가 리스트
    volumes: 거래량 리스트
    """
    obv = [0]
    for i in range(1, len(prices)):
        if prices[i] > prices[i-1]:
            obv.append(obv[-1] + volumes[i])
        elif prices[i] < prices[i-1]:
            obv.append(obv[-1] - volumes[i])
        else:
            obv.append(obv[-1])
    return obv

def evaluate_obv_trend(obv_values):
    """
    OBV 추세 평가하여 만족 여부 결정
    """
    # 최근 20일 vs 이전 20일 평균 비교 등의 로직 구현
    recent_avg = sum(obv_values[-20:]) / 20
    previous_avg = sum(obv_values[-40:-20]) / 20
    
    return recent_avg > previous_avg  # 상승 추세면 만족
```

### 2. 투자심리도 (Investment Psychology Index)

**평가 공식**: ✅ **확인완료**
```excel
=VLOOKUP(IF($D34<=25,"B002",IF($D34>=75,"B005","Z999")),'디노테스트_평가기준'!B:D,3,FALSE)
```

**입력 방식**: 🔧 **사용자 직접 입력**
- 현재 예시: 10 (투자심리도 10%)
- **자동화 검토 필요**: 계산 방법론 연구 필요

**셀 참조**:
- `$D34`: 투자심리도 값 (0~100% 범위)

**로직 분해**:
```
1. 투자심리도 ≤ 25% → B002 (+1점): 투자심리도침체 (매수 기회)
2. 투자심리도 ≥ 75% → B005 (-1점): 투자심리도과열 (매도 신호)
3. 기타 (25% < 투자심리도 < 75%) → Z999 (0점): 중립 구간
```

**Python 구현**:
```python
def calculate_investor_sentiment_score(sentiment_value):
    """
    투자심리도 점수 계산
    sentiment_value: 투자심리도 값 (0~100%)
    """
    if sentiment_value <= 25:
        return 1    # B002: 투자심리도침체 (매수 기회)
    elif sentiment_value >= 75:
        return -1   # B005: 투자심리도과열 (매도 신호)
    else:
        return 0    # Z999: 중립 구간

# 🤔 자동화 방법론 후보들 (연구 필요)

def calculate_sentiment_method1_vix_style(market_volatility, fear_greed_ratio):
    """
    방법 1: VIX 스타일 (변동성 기반)
    - 시장 변동성과 공포/탐욕 지수 활용
    """
    base_sentiment = 50  # 중립점
    
    # 변동성이 높을수록 공포 증가 (낮은 심리도)
    volatility_factor = min(market_volatility * 2, 40)
    
    # 공포/탐욕 비율 조정
    sentiment_adjustment = (fear_greed_ratio - 50) * 0.8
    
    sentiment = base_sentiment - volatility_factor + sentiment_adjustment
    return max(0, min(100, sentiment))

def calculate_sentiment_method2_momentum_based(price_momentum, volume_momentum, institutional_flow):
    """
    방법 2: 모멘텀 기반
    - 가격/거래량 모멘텀과 기관 자금 흐름 활용
    """
    # 가격 모멘텀 (20일 이동평균 대비)
    price_factor = max(-30, min(30, price_momentum))
    
    # 거래량 모멘텀 (평균 대비 배율)
    volume_factor = max(-20, min(20, (volume_momentum - 1) * 20))
    
    # 기관 자금 흐름 (순매수/순매도)
    institutional_factor = max(-20, min(20, institutional_flow))
    
    sentiment = 50 + price_factor + volume_factor + institutional_factor
    return max(0, min(100, sentiment))

def calculate_sentiment_method3_technical_composite(rsi, macd_signal, bollinger_position):
    """
    방법 3: 기술적 지표 복합
    - RSI, MACD, 볼린저밴드 위치를 종합하여 심리 상태 추정
    """
    # RSI 기반 심리도 (역방향: RSI 높으면 과열)
    rsi_sentiment = 100 - rsi
    
    # MACD 신호 기반
    macd_factor = macd_signal * 10  # -10 ~ +10 범위
    
    # 볼린저밴드 위치 기반 (-100% ~ +100%)
    bollinger_factor = (bollinger_position + 100) / 2  # 0 ~ 100 변환
    
    # 가중 평균
    sentiment = (rsi_sentiment * 0.5 + 
                (50 + macd_factor) * 0.3 + 
                bollinger_factor * 0.2)
    
    return max(0, min(100, sentiment))

# 키움 API 연동 가능성 분석
def get_sentiment_from_kiwoom_data(stock_code):
    """
    키움 API 데이터로 투자심리도 추정
    - 활용 가능한 키움 API 데이터들
    """
    try:
        # ka10001: 기본 정보 (현재가, PER, PBR 등)
        basic_info = kiwoom_api.get_basic_info(stock_code)
        
        # ka10005: 과거 시세 (가격 모멘텀 계산용)
        historical_data = kiwoom_api.get_historical_data(stock_code, days=30)
        
        # ka10045: 기관/외국인 매매 추이
        institutional_data = kiwoom_api.get_institutional_data(stock_code)
        
        # ka10004: 호가 정보 (매수/매도 압력)
        order_book = kiwoom_api.get_order_book(stock_code)
        
        # 복합 계산 (예시)
        prices = [float(data['close']) for data in historical_data]
        rsi = calculate_rsi_indicator(prices)
        
        # 기관 순매수 비율
        institutional_flow = institutional_data.get('net_buy_ratio', 0)
        
        # 호가 비율 (매수호가 총액 / 매도호가 총액)
        buy_power = sum(order_book['buy_orders'])
        sell_power = sum(order_book['sell_orders'])
        order_ratio = (buy_power / sell_power - 1) * 100 if sell_power > 0 else 0
        
        # 종합 투자심리도 계산
        sentiment = calculate_sentiment_method3_technical_composite(
            rsi, institutional_flow, order_ratio
        )
        
        return sentiment
        
    except Exception as e:
        # 계산 실패 시 중립값 반환
        return 50

# ⚠️ 한계점 및 고려사항
"""
투자심리도 자동화의 어려움:

1. 정의의 모호성:
   - "투자심리도"의 명확한 정의나 계산법이 표준화되지 않음
   - 증권사별, 분석기관별로 다른 방법론 사용

2. 데이터 한계:
   - Google Sheets에서 사용하는 구체적인 계산식 불명
   - 키움 API만으로는 일부 심리 지표 획득 어려움

3. 외부 데이터 의존:
   - VIX 지수, 시장 전체 심리 지표 등은 별도 API 필요
   - 뉴스 감성 분석 등은 추가 서비스 연동 필요

4. 검증의 어려움:
   - 계산한 심리도가 실제 시장 심리와 일치하는지 검증 곤란

권장사항:
- Phase 1: 사용자 입력 방식 유지
- Phase 2: 키움 API 기반 간단한 추정 알고리즘 구현
- Phase 3: 외부 심리 지표 API 연동 검토
"""
```

### 3. RSI (Relative Strength Index)

**평가 공식**: ✅ **확인완료**
```excel
=VLOOKUP(IF($D33<=30,"B003",IF($D33>=70,"B006","Z999")),'디노테스트_평가기준'!B:D,3,FALSE)
```

**입력 방식**: 🔧 **사용자 직접 입력**
- 현재는 사용자가 RSI 값을 직접 입력 (예: 40)
- 향후 키움 API 데이터로 자동 계산 가능

**셀 참조**:
- `$D33`: RSI 값 (0~100 범위)

**로직 분해**:
```
1. RSI ≤ 30 → B003 (+1점): RSI침체 (과매도 구간, 상승 신호)
2. RSI ≥ 70 → B006 (-1점): RSI과열 (과매수 구간, 하락 신호)  
3. 기타 (30 < RSI < 70) → Z999 (0점): 중립 구간
```

**Python 구현**:
```python
def calculate_rsi_score(rsi_value):
    """
    RSI 점수 계산
    rsi_value: RSI 값 (0~100)
    """
    if rsi_value <= 30:
        return 1    # B003: RSI침체 (과매도, 상승 신호)
    elif rsi_value >= 70:
        return -1   # B006: RSI과열 (과매수, 하락 신호)
    else:
        return 0    # Z999: 중립 구간

def calculate_rsi_indicator(prices, period=14):
    """
    실제 RSI 지표 계산
    prices: 종가 리스트
    period: RSI 계산 기간 (기본 14일)
    """
    if len(prices) < period + 1:
        return None
    
    gains = []
    losses = []
    
    # 전일 대비 변화량 계산
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        elif change < 0:
            gains.append(0)
            losses.append(abs(change))
        else:
            gains.append(0)
            losses.append(0)
    
    # 첫 번째 RS 계산 (단순 평균)
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    rsi_values = []
    
    # RSI 계산
    for i in range(period, len(gains)):
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        rsi_values.append(rsi)
        
        # 다음 평균 계산 (지수 이동 평균)
        if i < len(gains):
            avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
            avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period
    
    return rsi_values[-1] if rsi_values else None  # 최신 RSI 반환

# 키움 API 데이터로 RSI 자동 계산 예시
def get_rsi_from_kiwoom_data(stock_code, period=14):
    """
    키움 API 과거시세 데이터로 RSI 계산
    stock_code: 종목코드
    period: RSI 계산 기간
    """
    # ka10005 (과거시세조회) API 호출
    historical_data = kiwoom_api.get_historical_data(stock_code, days=period+10)
    prices = [float(data['close_price']) for data in historical_data]
    
    return calculate_rsi_indicator(prices, period)
```

---

## 💰 가격 영역 VLOOKUP 공식

### 52주 고저 대비 위치 (복합 계산)

**데이터 수집 공식**: ✅ **확인완료**
```excel
최고가: =MAX(index(GOOGLEFINANCE(JOIN(":",F19,G19),"PRICE",TODAY()-900,TODAY()),,2))
최저가: =MIN(index(GOOGLEFINANCE(JOIN(":",F19,G19),"PRICE",TODAY()-900,TODAY()),,2))
현재가: =GOOGLEFINANCE(JOIN(":",F19,G19),"PRICE")
```

**판단 표시 공식**: ✅ **확인완료**
```excel
="고점대비: "&VLOOKUP(IF(($B36-$D36)/$B36*100>=40,"C001",IF(($B36-$D36)/$B36*100>=30,"C002",IF(($B36-$D36)/$B36*100>=20,"C003","Z999"))),'디노테스트_평가기준'!B:D,2,FALSE)&CHAR(10)&
"저점대비: "&VLOOKUP(IF(($D36-$C36)/$C36*100>=300,"C004",IF(($D36-$C36)/$C36*100>=200,"C005",IF(($D36-$C36)/$C36*100>=100,"C006","Z999"))),'디노테스트_평가기준'!B:D,2,FALSE)
```

**점수 계산 공식**: ✅ **확인완료**
```excel
=VLOOKUP(IF(($B36-$D36)/$B36*100>=40,"C001",IF(($B36-$D36)/$B36*100>=30,"C002",IF(($B36-$D36)/$B36*100>=20,"C003","Z999"))),'디노테스트_평가기준'!B:D,3,FALSE) + 
VLOOKUP(IF(($D36-$C36)/$C36*100>=300,"C004",IF(($D36-$C36)/$C36*100>=200,"C005",IF(($D36-$C36)/$C36*100>=100,"C006","Z999"))),'디노테스트_평가기준'!B:D,3,FALSE)
```

**셀 참조**:
- `$F19`: 시장 코드 (예: "KRX")
- `$G19`: 종목 코드 (예: "034020")
- `$B36`: 52주 최고가
- `$C36`: 52주 최저가
- `$D36`: 현재가

**로직 분해**:
```
1. 데이터 수집 (900일, 약 2.5년):
   - GOOGLEFINANCE로 과거 주가 데이터 수집
   - 최고가/최저가/현재가 자동 계산

2. 고점 대비 하락률 평가:
   - 하락률 = (최고가 - 현재가) / 최고가 × 100
   - ≥40% 하락 → C001 (+3점): -40% 이상
   - ≥30% 하락 → C002 (+2점): -30% 이상  
   - ≥20% 하락 → C003 (+1점): -20% 이상
   - 기타 → Z999 (0점)

3. 저점 대비 상승률 평가:
   - 상승률 = (현재가 - 최저가) / 최저가 × 100
   - ≥300% 상승 → C004 (-3점): +300% 이상
   - ≥200% 상승 → C005 (-2점): +200% 이상
   - ≥100% 상승 → C006 (-1점): +100% 이상
   - 기타 → Z999 (0점)

4. 최종 점수 = 고점대비 점수 + 저점대비 점수 (복합 평가)
```

**Python 구현**:
```python
def get_52week_data_from_googlefinance(market_code, stock_code):
    """
    GOOGLEFINANCE 방식의 52주 데이터 수집
    (실제로는 키움 API ka10005로 대체)
    """
    # 키움 API로 900일 데이터 수집
    historical_data = kiwoom_api.get_historical_data(stock_code, days=900)
    
    prices = [float(data['high']) for data in historical_data]  # 고가 기준
    lows = [float(data['low']) for data in historical_data]     # 저가 기준
    current_price = float(historical_data[0]['close'])          # 최신 종가
    
    max_price = max(prices)     # 52주 최고가
    min_price = min(lows)       # 52주 최저가
    
    return {
        'max_price': max_price,
        'min_price': min_price,
        'current_price': current_price
    }

def calculate_price_position_score(max_price, min_price, current_price):
    """
    52주 고저 대비 위치 점수 계산 (복합)
    """
    # 고점 대비 하락률 계산
    decline_rate = (max_price - current_price) / max_price * 100
    
    # 고점 대비 점수
    if decline_rate >= 40:
        high_score = 3      # C001: -40% 이상
    elif decline_rate >= 30:
        high_score = 2      # C002: -30% 이상
    elif decline_rate >= 20:
        high_score = 1      # C003: -20% 이상
    else:
        high_score = 0      # Z999: 해당없음
    
    # 저점 대비 상승률 계산
    rise_rate = (current_price - min_price) / min_price * 100
    
    # 저점 대비 점수
    if rise_rate >= 300:
        low_score = -3      # C004: +300% 이상
    elif rise_rate >= 200:
        low_score = -2      # C005: +200% 이상
    elif rise_rate >= 100:
        low_score = -1      # C006: +100% 이상
    else:
        low_score = 0       # Z999: 해당없음
    
    # 복합 점수 (-3 ~ +3 범위)
    total_score = high_score + low_score
    
    return {
        'high_score': high_score,
        'low_score': low_score,
        'total_score': total_score,
        'decline_rate': decline_rate,
        'rise_rate': rise_rate,
        'interpretation': get_price_interpretation(decline_rate, rise_rate)
    }

def get_price_interpretation(decline_rate, rise_rate):
    """가격 위치 해석"""
    high_desc = ""
    if decline_rate >= 40: high_desc = "고점 대비 40% 이상 하락"
    elif decline_rate >= 30: high_desc = "고점 대비 30% 이상 하락"
    elif decline_rate >= 20: high_desc = "고점 대비 20% 이상 하락"
    else: high_desc = "고점 인근"
    
    low_desc = ""
    if rise_rate >= 300: low_desc = "저점 대비 300% 이상 상승"
    elif rise_rate >= 200: low_desc = "저점 대비 200% 이상 상승"
    elif rise_rate >= 100: low_desc = "저점 대비 100% 이상 상승"
    else: low_desc = "저점 인근"
    
    return f"{high_desc} / {low_desc}"

# 키움 API 연동 예시
def get_price_score_from_kiwoom(stock_code):
    """키움 API로 가격 위치 점수 계산"""
    try:
        data = get_52week_data_from_googlefinance("KRX", stock_code)
        return calculate_price_position_score(
            data['max_price'], 
            data['min_price'], 
            data['current_price']
        )
    except Exception as e:
        return {'total_score': 0, 'interpretation': '계산 실패'}
```

---

## 🎯 재료 영역 VLOOKUP 공식

### 4. 고배당 (D004)

**평가 공식**: ✅ **확인완료**
```excel
=VLOOKUP(IF(UPPER($F39)="Y","D004","Z999"),'디노테스트_평가기준'!B:D,3,FALSE)
```

**입력 방식**: 🔧 **사용자 직접 입력**
- 현재는 Y/N으로 고배당 여부를 직접 입력
- 향후 배당수익률 자동 계산 및 2% 기준 자동 판단 가능

**셀 참조**:
- `$F39`: 고배당 여부 ("Y" 또는 "N")

**로직 분해**:
```
1. UPPER($F39) = "Y" → D004 (+1점): 고배당 (2% 이상)
2. 기타 ("N" 또는 다른 값) → Z999 (0점): 해당없음
```

**Python 구현**:
```python
def calculate_dividend_score(is_high_dividend):
    """
    고배당 점수 계산
    is_high_dividend: True/False 또는 "Y"/"N"
    """
    if isinstance(is_high_dividend, str):
        is_high_dividend = is_high_dividend.upper() == "Y"
    
    if is_high_dividend:
        return 1    # D004: 고배당 (2% 이상)
    else:
        return 0    # Z999: 해당없음

def calculate_dividend_yield_auto(stock_code):
    """
    배당수익률 자동 계산 및 고배당 판단
    """
    try:
        # 키움 API로 배당 정보 수집 (가능한 API 확인 필요)
        # 예: ka10001 기본정보에서 배당수익률 필드 또는 별도 배당 API
        basic_info = kiwoom_api.get_basic_info(stock_code)
        dividend_yield = basic_info.get('dividend_yield', 0)
        
        # 2% 이상이면 고배당으로 판단
        is_high_dividend = dividend_yield >= 2.0
        
        return {
            'dividend_yield': dividend_yield,
            'is_high_dividend': is_high_dividend,
            'score': calculate_dividend_score(is_high_dividend)
        }
        
    except Exception as e:
        return {
            'dividend_yield': 0,
            'is_high_dividend': False,
            'score': 0,
            'error': str(e)
        }

# 대안적 계산 방법 (DART API 활용)
def get_dividend_from_dart(stock_code, year="2023"):
    """
    DART API로 배당금 정보 수집
    """
    try:
        # 1. 종목코드 → DART 기업코드 변환
        dart_service = DartDataService()
        corp_code = dart_service.get_corp_code(stock_code)
        
        # 2. 배당 공시 자료 조회
        dividend_data = dart_service.get_dividend_info(corp_code, year)
        
        # 3. 현재 주가로 배당수익률 계산
        current_price = kiwoom_api.get_current_price(stock_code)
        dividend_per_share = dividend_data.get('dividend_per_share', 0)
        
        dividend_yield = (dividend_per_share / current_price) * 100
        
        return dividend_yield >= 2.0
        
    except Exception as e:
        return False  # 계산 실패 시 False 반환
```

### 5. 어닝서프라이즈 (D005) - 컨센 대비 10% 이상

**평가 공식**: ✅ **확인완료**
```excel
=VLOOKUP(IF(UPPER($F40)="Y","D005","Z999"),'디노테스트_평가기준'!B:D,3,FALSE)
```

**입력 방식**: 🔧 **사용자 직접 입력**
- 현재는 Y/N으로 어닝서프라이즈 여부를 직접 입력
- 향후 실제 실적과 컨센서스 비교를 통한 자동 판단 가능

**셀 참조**:
- `$F40`: 어닝서프라이즈 여부 ("Y" 또는 "N")

**로직 분해**:
```
1. UPPER($F40) = "Y" → D005 (+1점): 어닝서프라이즈 (실적 서프라이즈)
2. 기타 ("N" 또는 다른 값) → Z999 (0점): 해당없음
```

**Python 구현**:
```python
def calculate_earnings_surprise_score(has_earnings_surprise):
    """
    어닝서프라이즈 점수 계산
    has_earnings_surprise: True/False 또는 "Y"/"N"
    """
    if isinstance(has_earnings_surprise, str):
        has_earnings_surprise = has_earnings_surprise.upper() == "Y"
    
    if has_earnings_surprise:
        return 1    # D005: 어닝서프라이즈 (실적 서프라이즈)
    else:
        return 0    # Z999: 해당없음

def calculate_earnings_surprise_auto(stock_code, threshold=10):
    """
    어닝서프라이즈 자동 판단 (컨센서스 대비 10% 이상)
    stock_code: 종목코드
    threshold: 서프라이즈 기준 (기본 10%)
    """
    try:
        # 1. 최신 분기 실적 조회 (키움 API 또는 DART API)
        actual_earnings = get_actual_earnings(stock_code)
        
        # 2. 컨센서스 실적 조회 (외부 API 필요)
        consensus_earnings = get_consensus_earnings(stock_code)
        
        if actual_earnings and consensus_earnings:
            # 3. 서프라이즈 비율 계산
            surprise_rate = ((actual_earnings - consensus_earnings) / 
                           abs(consensus_earnings)) * 100
            
            # 4. 10% 이상 상향 서프라이즈 판단
            has_surprise = surprise_rate >= threshold
            
            return {
                'actual_earnings': actual_earnings,
                'consensus_earnings': consensus_earnings,
                'surprise_rate': surprise_rate,
                'has_earnings_surprise': has_surprise,
                'score': calculate_earnings_surprise_score(has_surprise)
            }
        
    except Exception as e:
        return {
            'has_earnings_surprise': False,
            'score': 0,
            'error': str(e)
        }

def get_actual_earnings(stock_code):
    """
    실제 실적 조회 (DART API 활용)
    """
    try:
        dart_service = DartDataService()
        corp_code = dart_service.get_corp_code(stock_code)
        
        # 최신 분기보고서에서 순이익 추출
        quarterly_report = dart_service.get_latest_quarterly_report(corp_code)
        net_income = quarterly_report.get('net_income')
        
        return net_income
        
    except Exception as e:
        return None

def get_consensus_earnings(stock_code):
    """
    컨센서스 실적 조회 (외부 API 필요)
    예: FnGuide, 38커뮤니케이션, 블룸버그 등
    """
    try:
        # 🚧 외부 컨센서스 API 연동 필요
        # 예시: FnGuide API, Refinitiv API 등
        
        # 임시 구현 - 키움 API에서 애널리스트 예상 실적 확인
        # (키움에서 제공하는 경우에만 가능)
        consensus_data = kiwoom_api.get_analyst_consensus(stock_code)
        expected_earnings = consensus_data.get('expected_net_income')
        
        return expected_earnings
        
    except Exception as e:
        return None

# 🤔 어닝서프라이즈 자동화 고려사항

def earnings_surprise_challenges():
    """
    어닝서프라이즈 자동화의 어려움과 해결 방안
    """
    challenges = {
        "데이터 소스": {
            "문제": "컨센서스 데이터는 유료 서비스에서 제공",
            "해결방안": [
                "FnGuide API 연동 (유료)",
                "38커뮤니케이션 API 연동 (유료)", 
                "네이버/다음 증권 크롤링 (제한적)",
                "키움 API 내 애널리스트 예상 실적 활용 (가능성 확인 필요)"
            ]
        },
        "데이터 정확성": {
            "문제": "컨센서스와 실제 실적의 정확한 매칭 어려움",
            "해결방안": [
                "분기별/연간별 명확한 기준 설정",
                "회계 기준 통일 (K-IFRS 기준)",
                "이상치 제거 및 검증 로직 구현"
            ]
        },
        "실시간성": {
            "문제": "실적 발표와 컨센서스 업데이트 시차",
            "해결방안": [
                "실적 발표 일정 자동 추적",
                "발표 직후 자동 업데이트",
                "수동 검증 프로세스 병행"
            ]
        }
    }
    return challenges

# Phase별 구현 권장사항
"""
Phase 1: 수동 입력 방식 유지
- 사용자가 직접 Y/N 입력
- 간단하고 확실한 방법

Phase 2: 반자동 시스템
- DART API로 실제 실적 자동 수집
- 컨센서스는 사용자 입력 또는 간단한 크롤링
- 서프라이즈 비율 자동 계산

Phase 3: 완전 자동화
- 유료 컨센서스 API 연동
- 실시간 업데이트 및 알림
- 검증 시스템 구축
"""
```

### 6. 기관/외국인 수급 (D003) - 최근 1~3개월, 상장주식수 1% 이상

**60일 기관순매매량**: 🔧 **사용자 직접 입력**

**기관매집비율 공식**: ✅ **확인완료**
```excel
=IF(B42=0,0,B42/VLOOKUP(B19,'전종목기본정보'!D:L,9,FALSE))
```

**60일 외인순매매량 공식**: ✅ **확인완료**
```excel
=IFERROR(VALUE(SUBSTITUTE(SUBSTITUTE(INDEX(IMPORTHTML($J$4&G19&"&page=1&trader_day=60","table",2),12,3),"*(",""),")*","")),VALUE(SUBSTITUTE(SUBSTITUTE(INDEX(IMPORTHTML($J$4&G19&"&page=1&trader_day=60","table",3),12,3),"*(",""),")*","")))
```

**외인매집비율 공식**: ✅ **확인완료**
```excel
=IF(D42=0,0,D42/VLOOKUP(B19,'전종목기본정보'!D:L,9,FALSE))
```

**해당여부 판단 공식**: ✅ **확인완료**
```excel
=IF(OR(C42>=0.01,E42>=0.01), "Y","N")
```

**최종 점수 공식**: ✅ **확인완료**
```excel
=VLOOKUP(IF(UPPER($F41)="Y","D003","Z999"),'디노테스트_평가기준'!B:D,3,FALSE)
```

**셀 참조**:
- `B42`: 60일 기관순매매량 (직접 입력값)
- `D42`: 60일 외인순매매량 (자동 계산값)
- `C42`: 기관매집비율 (자동 계산)
- `E42`: 외인매집비율 (자동 계산)
- `F41`: 해당여부 ("Y" 또는 "N")
- `B19`: 종목코드
- `G19`: 종목코드 (외인 데이터용)
- `J4`: 외국인 데이터 URL 기본주소

**로직 분해**:
```
1. 데이터 수집:
   - 기관순매매량: 사용자 직접 입력
   - 외인순매매량: IMPORTHTML로 네이버 금융에서 60일 데이터 크롤링
   - 상장주식수: '전종목기본정보' 시트에서 VLOOKUP

2. 매집비율 계산:
   - 기관매집비율 = 기관순매매량 / 상장주식수
   - 외인매집비율 = 외인순매매량 / 상장주식수

3. 해당여부 판단:
   - 기관매집비율 ≥ 1% OR 외인매집비율 ≥ 1% → "Y"
   - 기타 → "N"

4. 점수 부여:
   - 해당여부 = "Y" → D003 (+1점): 기관/외국인 수급
   - 기타 ("N") → Z999 (0점): 해당없음
```

**Python 구현**:
```python
def calculate_institutional_supply_score(institutional_net_buy=0, foreign_net_buy=0, outstanding_shares=0):
    """
    기관/외국인 수급 점수 계산
    institutional_net_buy: 60일 기관순매매량
    foreign_net_buy: 60일 외인순매매량  
    outstanding_shares: 상장주식수
    """
    if outstanding_shares <= 0:
        return 0  # 상장주식수가 없으면 계산 불가
    
    # 매집비율 계산 (1% = 0.01)
    institutional_ratio = institutional_net_buy / outstanding_shares if institutional_net_buy != 0 else 0
    foreign_ratio = foreign_net_buy / outstanding_shares if foreign_net_buy != 0 else 0
    
    # 1% 이상 매집 여부 판단
    has_significant_buying = (institutional_ratio >= 0.01) or (foreign_ratio >= 0.01)
    
    score = 1 if has_significant_buying else 0  # D003 (+1) or Z999 (0)
    
    return {
        'institutional_ratio': institutional_ratio,
        'foreign_ratio': foreign_ratio,
        'has_significant_buying': has_significant_buying,
        'score': score,
        'interpretation': get_supply_interpretation(institutional_ratio, foreign_ratio)
    }

def get_supply_interpretation(inst_ratio, foreign_ratio):
    """수급 상황 해석"""
    inst_pct = inst_ratio * 100
    foreign_pct = foreign_ratio * 100
    
    interpretations = []
    
    if inst_ratio >= 0.01:
        interpretations.append(f"기관 매집 {inst_pct:.2f}%")
    if foreign_ratio >= 0.01:
        interpretations.append(f"외국인 매집 {foreign_pct:.2f}%")
    
    if not interpretations:
        return "유의미한 수급 없음"
    
    return " / ".join(interpretations)

# 키움 API 연동 구현
def get_institutional_data_from_kiwoom(stock_code, days=60):
    """
    키움 API로 기관/외국인 수급 데이터 수집
    """
    try:
        # ka10045: 종목별기관매매추이 API 활용
        institutional_data = kiwoom_api.get_institutional_trading_trend(stock_code, days)
        
        # ka10001: 기본정보에서 상장주식수 조회
        basic_info = kiwoom_api.get_basic_info(stock_code)
        outstanding_shares = basic_info.get('outstanding_shares', 0)
        
        # 60일간 누적 순매매량 계산
        institutional_net_buy = sum([
            int(data.get('institutional_net_buy', 0)) 
            for data in institutional_data
        ])
        
        foreign_net_buy = sum([
            int(data.get('foreign_net_buy', 0)) 
            for data in institutional_data
        ])
        
        return calculate_institutional_supply_score(
            institutional_net_buy, foreign_net_buy, outstanding_shares
        )
        
    except Exception as e:
        return {
            'score': 0,
            'error': str(e),
            'interpretation': '데이터 수집 실패'
        }

# 대안적 구현 - 네이버 금융 크롤링 (Google Sheets 방식)
def get_foreign_data_from_naver(stock_code, days=60):
    """
    네이버 금융 크롤링으로 외국인 데이터 수집
    (Google Sheets IMPORTHTML 방식 재현)
    """
    import requests
    from bs4 import BeautifulSoup
    
    try:
        # 네이버 금융 외국인 매매 동향 페이지
        url = f"https://finance.naver.com/item/frgn.naver?code={stock_code}&page=1&trader_day={days}"
        
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 테이블에서 외국인 순매매량 추출
        tables = soup.find_all('table')
        
        if len(tables) >= 2:
            # 두 번째 테이블에서 외국인 데이터 추출
            foreign_data = extract_foreign_net_buy_from_table(tables[1])
            return foreign_data
        
        return 0
        
    except Exception as e:
        print(f"네이버 크롤링 실패: {e}")
        return 0

def extract_foreign_net_buy_from_table(table):
    """테이블에서 외국인 순매매량 추출"""
    try:
        rows = table.find_all('tr')
        if len(rows) >= 12:
            # 12번째 행, 3번째 열에서 데이터 추출 (Google Sheets 공식 기준)
            cell = rows[11].find_all('td')[2]  # 0-based index
            text = cell.get_text().strip()
            
            # "*(", ")*" 문자 제거 (Google Sheets SUBSTITUTE 기능)
            text = text.replace("*(", "").replace(")*", "")
            
            # 숫자 변환
            return int(text.replace(",", "")) if text.isdigit() else 0
            
    except Exception as e:
        return 0

# 🤔 자동화 고려사항
def institutional_supply_automation_analysis():
    """
    기관/외국인 수급 자동화 분석
    """
    analysis = {
        "데이터 소스": {
            "키움 API": {
                "장점": ["실시간 데이터", "안정적 제공", "공식 API"],
                "단점": ["일부 상세 데이터 제한 가능성"],
                "활용 API": ["ka10045 (기관매매추이)", "ka10001 (기본정보)"]
            },
            "네이버 크롤링": {
                "장점": ["상세한 외국인 데이터", "무료 접근"],
                "단점": ["불안정성", "변경 가능성", "법적 리스크"],
                "Google Sheets 호환": "IMPORTHTML 완전 재현 가능"
            }
        },
        
        "구현 우선순위": {
            "1순위": "키움 API 기반 완전 자동화",
            "2순위": "하이브리드 (키움 + 네이버 크롤링)",
            "3순위": "사용자 입력 + 부분 자동화"
        },
        
        "정확도 검증": {
            "기관 데이터": "키움 API vs 한국거래소 공식 데이터 비교",
            "외국인 데이터": "네이버/다음 vs 한국예탁결제원 데이터 비교",
            "상장주식수": "정기적 업데이트 및 액면분할 반영"
        }
    }
    
    return analysis

# Phase별 구현 전략
"""
Phase 1: 키움 API 기반 자동화
- ka10045 API로 기관/외국인 매매 데이터 수집
- ka10001 API로 상장주식수 정보 수집
- 60일 누적 계산 및 매집비율 자동 산출

Phase 2: 하이브리드 방식
- 키움 API 우선, 실패 시 크롤링 fallback
- 데이터 정확성 검증 로직 추가
- 사용자 수동 입력 옵션 제공

Phase 3: 고도화
- 실시간 모니터링 및 알림
- 매집 패턴 분석 및 예측
- 다양한 기간별 분석 (30일, 90일 등)
"""
```

### 7. 불성실공시 (D006)

**평가 공식**: ✅ **확인완료**
```excel
=VLOOKUP(IF(UPPER($F43)="Y","D006","Z999"),'디노테스트_평가기준'!B:D,3,FALSE)
```

**입력 방식**: 🔧 **사용자 직접 입력**
- 현재는 Y/N으로 불성실 공시 지정 여부를 직접 입력
- 향후 금융감독원 전자공시시스템(DART) 연동을 통한 자동 판단 가능

**셀 참조**:
- `$F43`: 불성실공시 여부 ("Y" 또는 "N")

**로직 분해**:
```
1. UPPER($F43) = "Y" → D006 (-1점): 불성실 공시 (감점 요소)
2. 기타 ("N" 또는 다른 값) → Z999 (0점): 해당없음
```

**Python 구현**:
```python
def calculate_unfaithful_disclosure_score(has_unfaithful_disclosure):
    """
    불성실공시 점수 계산
    has_unfaithful_disclosure: True/False 또는 "Y"/"N"
    """
    if isinstance(has_unfaithful_disclosure, str):
        has_unfaithful_disclosure = has_unfaithful_disclosure.upper() == "Y"
    
    if has_unfaithful_disclosure:
        return -1   # D006: 불성실 공시 (감점)
    else:
        return 0    # Z999: 해당없음

def check_unfaithful_disclosure_auto(stock_code):
    """
    불성실공시 자동 확인 (DART API 활용)
    """
    try:
        # 1. 종목코드 → DART 기업코드 변환
        dart_service = DartDataService()
        corp_code = dart_service.get_corp_code(stock_code)
        
        # 2. 불성실공시법인 지정현황 조회
        unfaithful_status = dart_service.get_unfaithful_disclosure_status(corp_code)
        
        # 3. 현재 불성실공시법인 지정 여부 확인
        is_unfaithful = unfaithful_status.get('is_currently_unfaithful', False)
        designation_date = unfaithful_status.get('designation_date')
        cancellation_date = unfaithful_status.get('cancellation_date')
        
        return {
            'is_unfaithful_disclosure': is_unfaithful,
            'designation_date': designation_date,
            'cancellation_date': cancellation_date,
            'score': calculate_unfaithful_disclosure_score(is_unfaithful),
            'detail': get_unfaithful_disclosure_detail(unfaithful_status)
        }
        
    except Exception as e:
        return {
            'is_unfaithful_disclosure': False,
            'score': 0,
            'error': str(e),
            'detail': '확인 불가'
        }

def get_unfaithful_disclosure_detail(status):
    """불성실공시 상세 정보"""
    if not status.get('is_currently_unfaithful', False):
        return "정상 공시법인"
    
    reasons = status.get('designation_reasons', [])
    designation_date = status.get('designation_date', 'N/A')
    
    detail = f"불성실공시법인 지정일: {designation_date}"
    if reasons:
        detail += f", 지정사유: {', '.join(reasons)}"
    
    return detail

# DART API 연동 예시
class DartDataService:
    """DART 전자공시시스템 API 서비스"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('DART_API_KEY')
        self.base_url = "https://opendart.fss.or.kr/api"
    
    def get_corp_code(self, stock_code):
        """종목코드로 DART 기업코드 조회"""
        try:
            # DART 기업고유번호 API 호출
            url = f"{self.base_url}/corpCode.xml"
            params = {'crtfc_key': self.api_key}
            
            response = requests.get(url, params=params)
            
            # ZIP 파일 다운로드 및 XML 파싱하여 기업코드 매핑
            # (구현 세부사항 생략)
            
            return "mapped_corp_code"  # 실제로는 매핑된 기업코드 반환
            
        except Exception as e:
            return None
    
    def get_unfaithful_disclosure_status(self, corp_code):
        """불성실공시법인 지정현황 조회"""
        try:
            # 불성실공시법인 지정현황 API
            url = f"{self.base_url}/fnlttSinglAcntAll.json"
            params = {
                'crtfc_key': self.api_key,
                'corp_code': corp_code,
                'bsns_year': '2024'  # 최신 연도
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            # 불성실공시 관련 정보 파싱
            if data.get('status') == '000':  # 정상 응답
                # 실제 API 응답에 따라 파싱 로직 구현
                return {
                    'is_currently_unfaithful': False,  # 실제 데이터 기반으로 판단
                    'designation_date': None,
                    'cancellation_date': None,
                    'designation_reasons': []
                }
            
            return {'is_currently_unfaithful': False}
            
        except Exception as e:
            return {'is_currently_unfaithful': False, 'error': str(e)}

# 대안적 방법 - 금감원 웹사이트 크롤링
def check_unfaithful_disclosure_from_fss(company_name):
    """
    금감원 불성실공시법인 명단 크롤링
    """
    try:
        # 금융감독원 불성실공시법인 지정현황 페이지
        fss_url = "https://dart.fss.or.kr/dsab007/main.do"
        
        # 웹 크롤링으로 불성실공시법인 목록 수집
        response = requests.get(fss_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 불성실공시법인 테이블에서 회사명 검색
        unfaithful_companies = extract_unfaithful_companies(soup)
        
        is_unfaithful = company_name in unfaithful_companies
        
        return {
            'is_unfaithful_disclosure': is_unfaithful,
            'method': 'FSS 웹크롤링',
            'total_unfaithful_count': len(unfaithful_companies)
        }
        
    except Exception as e:
        return {
            'is_unfaithful_disclosure': False,
            'error': str(e),
            'method': 'FSS 크롤링 실패'
        }

def extract_unfaithful_companies(soup):
    """불성실공시법인 목록 추출"""
    companies = []
    
    try:
        # 테이블에서 회사명 추출 (실제 HTML 구조에 맞게 수정 필요)
        table = soup.find('table', class_='unfaithful-list')
        if table:
            rows = table.find_all('tr')[1:]  # 헤더 제외
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    company_name = cells[1].get_text().strip()
                    companies.append(company_name)
    
    except Exception as e:
        pass
    
    return companies

# 🤔 자동화 고려사항
def unfaithful_disclosure_automation_analysis():
    """
    불성실공시 자동화 분석
    """
    analysis = {
        "데이터 소스": {
            "DART API": {
                "장점": ["공식 데이터", "정확성", "실시간 업데이트"],
                "단점": ["API 키 필요", "복잡한 데이터 구조"],
                "활용 방법": "기업코드 매핑 후 불성실공시 현황 조회"
            },
            "금감원 웹사이트": {
                "장점": ["최신 정보", "무료 접근"],
                "단점": ["크롤링 불안정성", "구조 변경 위험"],
                "활용 방법": "불성실공시법인 지정현황 페이지 크롤링"
            },
            "키움 API": {
                "가능성": "낮음",
                "이유": "불성실공시 정보는 일반적으로 시세 API에서 제공하지 않음"
            }
        },
        
        "구현 전략": {
            "Phase 1": "사용자 수동 입력 유지",
            "Phase 2": "DART API 연동으로 반자동화",
            "Phase 3": "실시간 모니터링 및 알림 시스템"
        },
        
        "주의사항": {
            "법적 리스크": "불성실공시 지정/해제는 법적 효력이 있는 사안",
            "정확성": "반드시 공식 출처(DART, 금감원) 확인 필요",
            "실시간성": "지정/해제 시점의 정확한 반영 중요"
        }
    }
    
    return analysis

# Phase별 구현 권장사항
"""
Phase 1: 수동 입력 방식 유지
- 사용자가 직접 Y/N 입력
- 금감원/DART 사이트 수동 확인 후 입력

Phase 2: DART API 연동
- DART API로 불성실공시법인 지정현황 자동 조회
- 종목코드 → DART 기업코드 자동 매핑
- 주기적(월 1회) 업데이트

Phase 3: 실시간 모니터링
- 불성실공시 지정/해제 실시간 알림
- 포트폴리오 내 종목 자동 모니터링
- 리스크 관리 시스템 연동

자동화 우선순위: 중간
- 비교적 드문 이벤트 (전체 상장기업 중 소수)
- 하지만 발생 시 주가에 큰 영향
- Phase 2 수준의 자동화로 충분
"""
```

### 8. 악재뉴스 (D007) - 대형 클레임, 계약취소 등

**평가 공식**: ✅ **확인완료**
```excel
=VLOOKUP(IF(UPPER($F44)="Y","D007","Z999"),'디노테스트_평가기준'!B:D,3,FALSE)
```

**입력 방식**: 🔧 **사용자 직접 입력**
- 현재는 Y/N으로 악재뉴스 발생 여부를 직접 입력
- 향후 뉴스 API 연동 및 키워드 기반 악재 자동 탐지 가능

**셀 참조**:
- `$F44`: 악재뉴스 여부 ("Y" 또는 "N")

**로직 분해**:
```
1. UPPER($F44) = "Y" → D007 (-1점): 악재뉴스 (대형 클레임, 계약취소 등)
2. 기타 ("N" 또는 다른 값) → Z999 (0점): 해당없음
```

**악재 유형 예시**:
- 대형 클레임 (제품 결함, 손해배상)
- 주요 계약 취소 (매출 영향 큰 계약)
- 법정 분쟁 (특허, 노동, 상법 등)
- 규제 위반 (과징금, 영업정지)
- 경영진 스캔들 (횡령, 배임 등)
- 대형 사고 (산업재해, 환경오염)

**Python 구현**:
```python
def calculate_negative_news_score(has_negative_news):
    """
    악재뉴스 점수 계산
    has_negative_news: True/False 또는 "Y"/"N"
    """
    if isinstance(has_negative_news, str):
        has_negative_news = has_negative_news.upper() == "Y"
    
    if has_negative_news:
        return -1   # D007: 악재뉴스 (감점)
    else:
        return 0    # Z999: 해당없음

def detect_negative_news_auto(stock_code, company_name, days=30):
    """
    악재뉴스 자동 탐지 (뉴스 API + 키워드 분석)
    """
    try:
        # 1. 뉴스 데이터 수집 (최근 30일)
        news_data = collect_news_data(company_name, days)
        
        # 2. 악재 키워드 기반 필터링
        negative_news = filter_negative_news(news_data)
        
        # 3. 심각도 평가
        severity_score = evaluate_news_severity(negative_news)
        
        # 4. 악재뉴스 여부 판단 (임계값 기준)
        has_significant_negative = severity_score >= 0.7  # 70% 이상 심각도
        
        return {
            'has_negative_news': has_significant_negative,
            'severity_score': severity_score,
            'negative_news_count': len(negative_news),
            'top_negative_news': negative_news[:3],  # 상위 3개 악재
            'score': calculate_negative_news_score(has_significant_negative),
            'analysis': get_negative_news_analysis(negative_news)
        }
        
    except Exception as e:
        return {
            'has_negative_news': False,
            'score': 0,
            'error': str(e),
            'analysis': '분석 실패'
        }

def collect_news_data(company_name, days=30):
    """
    뉴스 데이터 수집 (네이버 뉴스 API, 구글 뉴스 등)
    """
    news_sources = [
        collect_from_naver_news(company_name, days),
        collect_from_google_news(company_name, days),
        collect_from_dart_disclosure(company_name, days),  # 공시 정보
        # collect_from_financial_media(company_name, days)  # 금융 전문매체
    ]
    
    # 모든 소스에서 수집된 뉴스 통합
    all_news = []
    for news_list in news_sources:
        if news_list:
            all_news.extend(news_list)
    
    # 중복 제거 (제목 유사도 기반)
    unique_news = remove_duplicate_news(all_news)
    
    return unique_news

def filter_negative_news(news_data):
    """
    악재 키워드 기반 뉴스 필터링
    """
    negative_keywords = {
        # 법정 분쟁 관련
        "법정분쟁": ["소송", "고발", "기소", "판결", "배상", "손해", "클레임"],
        
        # 계약 관련
        "계약문제": ["계약취소", "계약해지", "납품중단", "공급중단", "계약파기"],
        
        # 규제/제재 관련  
        "규제제재": ["과징금", "영업정지", "제재", "경고", "시정명령", "과태료"],
        
        # 경영 관련
        "경영문제": ["적자", "손실", "구조조정", "정리해고", "부도", "워크아웃"],
        
        # 사고/사건 관련
        "사고사건": ["사고", "화재", "폭발", "누출", "오염", "결함", "리콜"],
        
        # 경영진 관련
        "경영진문제": ["횡령", "배임", "비리", "스캔들", "사퇴", "구속", "수사"]
    }
    
    negative_news = []
    
    for news in news_data:
        title = news.get('title', '')
        content = news.get('content', '')
        full_text = f"{title} {content}".lower()
        
        # 악재 키워드 매칭
        matched_categories = []
        total_matches = 0
        
        for category, keywords in negative_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in full_text)
            if matches > 0:
                matched_categories.append((category, matches))
                total_matches += matches
        
        # 악재 뉴스로 분류 (키워드 2개 이상 매칭)
        if total_matches >= 2:
            news['negative_score'] = total_matches
            news['negative_categories'] = matched_categories
            negative_news.append(news)
    
    # 악재 점수 기준으로 정렬 (심각한 것부터)
    negative_news.sort(key=lambda x: x['negative_score'], reverse=True)
    
    return negative_news

def evaluate_news_severity(negative_news):
    """
    악재뉴스 심각도 평가 (0.0 ~ 1.0)
    """
    if not negative_news:
        return 0.0
    
    # 심각도 가중치
    severity_weights = {
        "법정분쟁": 0.8,    # 높은 심각도
        "계약문제": 0.7,    
        "규제제재": 0.9,    # 매우 높은 심각도
        "경영문제": 0.6,    
        "사고사건": 0.5,    
        "경영진문제": 0.8   # 높은 심각도
    }
    
    total_severity = 0
    max_possible = 0
    
    for news in negative_news[:5]:  # 상위 5개 뉴스만 평가
        news_severity = 0
        for category, matches in news.get('negative_categories', []):
            weight = severity_weights.get(category, 0.3)
            news_severity += weight * min(matches, 3) / 3  # 최대 3개 키워드까지만 반영
        
        total_severity += min(news_severity, 1.0)  # 뉴스당 최대 1.0
        max_possible += 1.0
    
    # 정규화 (0.0 ~ 1.0)
    return min(total_severity / max_possible if max_possible > 0 else 0, 1.0)

def get_negative_news_analysis(negative_news):
    """악재뉴스 분석 요약"""
    if not negative_news:
        return "악재뉴스 없음"
    
    # 카테고리별 집계
    category_counts = {}
    for news in negative_news:
        for category, matches in news.get('negative_categories', []):
            category_counts[category] = category_counts.get(category, 0) + matches
    
    # 주요 악재 유형 식별
    if not category_counts:
        return "악재뉴스 분석 실패"
    
    top_category = max(category_counts.items(), key=lambda x: x[1])
    
    category_names = {
        "법정분쟁": "법정 분쟁",
        "계약문제": "계약 관련 문제", 
        "규제제재": "규제 위반/제재",
        "경영문제": "경영상 문제",
        "사고사건": "사고/사건",
        "경영진문제": "경영진 관련 문제"
    }
    
    analysis = f"주요 악재: {category_names.get(top_category[0], top_category[0])} ({len(negative_news)}건)"
    
    return analysis

# 뉴스 데이터 수집 구현 예시
def collect_from_naver_news(company_name, days=30):
    """네이버 뉴스 검색 API"""
    try:
        import requests
        
        # 네이버 뉴스 검색 API
        url = "https://openapi.naver.com/v1/search/news.json"
        headers = {
            "X-Naver-Client-Id": os.getenv('NAVER_CLIENT_ID'),
            "X-Naver-Client-Secret": os.getenv('NAVER_CLIENT_SECRET')
        }
        params = {
            "query": company_name,
            "display": 100,  # 최대 100개
            "start": 1,
            "sort": "date"   # 최신 순
        }
        
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        news_list = []
        for item in data.get('items', []):
            news_list.append({
                'title': item.get('title', ''),
                'content': item.get('description', ''),
                'link': item.get('link', ''),
                'pub_date': item.get('pubDate', ''),
                'source': 'naver'
            })
        
        return news_list
        
    except Exception as e:
        return []

def remove_duplicate_news(news_list):
    """뉴스 중복 제거 (제목 유사도 기반)"""
    from difflib import SequenceMatcher
    
    unique_news = []
    
    for news in news_list:
        is_duplicate = False
        current_title = news.get('title', '')
        
        for existing in unique_news:
            existing_title = existing.get('title', '')
            # 제목 유사도 계산
            similarity = SequenceMatcher(None, current_title, existing_title).ratio()
            
            if similarity > 0.8:  # 80% 이상 유사하면 중복으로 간주
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_news.append(news)
    
    return unique_news

# 🤔 자동화 고려사항
def negative_news_automation_analysis():
    """
    악재뉴스 자동화 분석
    """
    analysis = {
        "데이터 소스": {
            "뉴스 API": {
                "장점": ["실시간성", "구조화된 데이터", "검색 기능"],
                "단점": ["API 비용", "키워드 한계", "맥락 이해 부족"],
                "추천": ["네이버 뉴스 API", "구글 뉴스 API", "뉴스픽 API"]
            },
            "공시정보": {
                "장점": ["공식성", "신뢰성", "법적 효력"],
                "단점": ["제한적 범위", "지연성"],
                "활용": "DART API 연동으로 중요 공시사항 자동 수집"
            }
        },
        
        "기술적 접근": {
            "키워드 매칭": {
                "정확도": "60-70%",
                "구현 난이도": "낮음",
                "한계": "맥락 파악 어려움, 오탐 가능성"
            },
            "자연어 처리": {
                "정확도": "80-85%",
                "구현 난이도": "높음",
                "활용": "BERT, GPT 등 사전 학습 모델 활용"
            },
            "감성 분석": {
                "정확도": "70-80%",
                "구현 난이도": "중간",
                "활용": "긍정/부정/중립 분류"
            }
        },
        
        "구현 전략": {
            "Phase 1": "키워드 기반 필터링 + 수동 검증",
            "Phase 2": "감성 분석 + 심각도 평가 자동화",
            "Phase 3": "AI 기반 종합 판단 + 실시간 알림"
        }
    }
    
    return analysis

# Phase별 구현 권장사항
"""
Phase 1: 키워드 기반 반자동화
- 뉴스 API로 최근 뉴스 수집
- 악재 키워드 매칭으로 후보 추출
- 사용자가 최종 판단 (Y/N 입력)

Phase 2: 감성 분석 기반 자동화
- 자연어 처리로 뉴스 감성 분석
- 심각도 점수 자동 계산
- 임계값 기반 자동 판단

Phase 3: AI 기반 종합 판단
- 대형 언어 모델 활용 (GPT, BERT 등)
- 맥락 이해 기반 정확한 판단
- 실시간 모니터링 및 알림

자동화 우선순위: 높음
- 투자 의사결정에 직접적 영향
- 실시간성 중요
- 하지만 오판 시 리스크 크므로 검증 프로세스 필수
"""
```

### 9. 구체화된 이벤트/호재 임박 (D001)

**평가 공식**: ✅ **확인완료**
```excel
=VLOOKUP(IF(UPPER($F45)="Y","D001","Z999"),'디노테스트_평가기준'!B:D,3,FALSE)
```

**입력 방식**: 🔧 **사용자 직접 입력**
- 현재는 Y/N으로 구체화된 이벤트/호재 임박 여부를 직접 입력
- 향후 공시정보 API 연동 및 이벤트 캘린더 자동 분석 가능

**셀 참조**:
- `$F45`: 구체화된 이벤트/호재 임박 여부 ("Y" 또는 "N")

**로직 분해**:
```
1. UPPER($F45) = "Y" → D001 (+1점): 구체화된 이벤트/호재 임박
2. 기타 ("N" 또는 다른 값) → Z999 (0점): 해당없음
```

**구체화된 이벤트/호재 유형 예시**:
- **기업 분할/합병**: 스핀오프, 인수합병, 자회사 분할
- **신제품 출시**: 혁신적 제품 공개, 상용화 확정
- **신규 사업**: 새로운 사업 영역 진출, 사업부 신설
- **대형 계약**: 대형 수주, 장기 공급계약 체결
- **정부 정책**: 규제 완화, 지원책 발표, 인허가 취득
- **기술 성과**: 특허 취득, 기술 이전, R&D 성과 발표
- **글로벌 진출**: 해외 진출, 합작 투자, 현지 법인 설립
- **구조 개선**: 사업 구조조정, 수익성 개선, 비용 절감

**Python 구현**:
```python
def calculate_upcoming_event_score(has_upcoming_event):
    """
    구체화된 이벤트/호재 임박 점수 계산
    has_upcoming_event: True/False 또는 "Y"/"N"
    """
    if isinstance(has_upcoming_event, str):
        has_upcoming_event = has_upcoming_event.upper() == "Y"
    
    if has_upcoming_event:
        return 1    # D001: 구체화된 이벤트/호재 임박 (+1점)
    else:
        return 0    # Z999: 해당없음

def detect_upcoming_events_auto(stock_code, company_name, days=60):
    """
    구체화된 이벤트/호재 자동 탐지
    """
    try:
        # 다중 소스에서 이벤트 정보 수집
        events = {
            'disclosure_events': get_disclosure_events(stock_code, days),
            'news_events': get_news_events(company_name, days),
            'calendar_events': get_corporate_calendar_events(stock_code, days),
            'analyst_events': get_analyst_coverage_events(stock_code, days)
        }
        
        # 이벤트 종합 분석
        significant_events = analyze_event_significance(events)
        
        # 임박성 평가 (60일 이내)
        imminent_events = filter_imminent_events(significant_events, days)
        
        # 구체화 정도 평가
        concrete_events = evaluate_concreteness(imminent_events)
        
        has_significant_event = len(concrete_events) > 0
        
        return {
            'has_upcoming_event': has_significant_event,
            'total_events': len(significant_events),
            'imminent_events': len(imminent_events),
            'concrete_events': len(concrete_events),
            'top_events': concrete_events[:3],  # 상위 3개 이벤트
            'score': calculate_upcoming_event_score(has_significant_event),
            'analysis': get_event_analysis(concrete_events)
        }
        
    except Exception as e:
        return {
            'has_upcoming_event': False,
            'score': 0,
            'error': str(e),
            'analysis': '분석 실패'
        }

def get_disclosure_events(stock_code, days=60):
    """
    DART 공시정보에서 이벤트 추출
    """
    try:
        dart_service = DartDataService()
        corp_code = dart_service.get_corp_code(stock_code)
        
        # 최근 공시 조회
        disclosures = dart_service.get_recent_disclosures(corp_code, days)
        
        # 이벤트성 공시 필터링
        event_keywords = [
            '합병', '분할', '인수', '매각', '투자', '계약', '출시',
            '사업', '특허', '승인', '허가', '선정', '체결'
        ]
        
        event_disclosures = []
        for disclosure in disclosures:
            title = disclosure.get('title', '').lower()
            if any(keyword in title for keyword in event_keywords):
                event_disclosures.append({
                    'type': 'disclosure',
                    'title': disclosure.get('title'),
                    'date': disclosure.get('date'),
                    'importance': calculate_disclosure_importance(disclosure),
                    'source': 'DART'
                })
        
        return event_disclosures
        
    except Exception as e:
        return []

def get_news_events(company_name, days=60):
    """
    뉴스에서 이벤트성 정보 추출
    """
    try:
        # 뉴스 데이터 수집
        news_data = collect_news_data(company_name, days)
        
        # 호재 이벤트 키워드
        positive_event_keywords = {
            "신제품": ["출시", "런칭", "공개", "발표", "상용화"],
            "계약": ["수주", "계약", "협약", "파트너십", "제휴"],
            "기술": ["특허", "기술이전", "혁신", "개발완료", "승인"],
            "사업확장": ["진출", "확장", "신설", "증설", "투자유치"],
            "정부지원": ["선정", "지원", "보조금", "인센티브", "규제완화"]
        }
        
        event_news = []
        for news in news_data:
            title = news.get('title', '').lower()
            content = news.get('content', '').lower()
            full_text = f"{title} {content}"
            
            # 이벤트 키워드 매칭
            matched_events = []
            for category, keywords in positive_event_keywords.items():
                matches = [kw for kw in keywords if kw in full_text]
                if matches:
                    matched_events.append((category, matches))
            
            if matched_events:
                event_news.append({
                    'type': 'news_event',
                    'title': news.get('title'),
                    'date': news.get('pub_date'),
                    'matched_events': matched_events,
                    'importance': len(matched_events),
                    'source': 'news'
                })
        
        return event_news
        
    except Exception as e:
        return []

def analyze_event_significance(events):
    """
    이벤트 중요도 분석
    """
    all_events = []
    
    # 모든 소스의 이벤트 통합
    for source, event_list in events.items():
        all_events.extend(event_list)
    
    # 중요도 기준으로 필터링 (상위 50%)
    if not all_events:
        return []
    
    # 중요도 점수 기준 정렬
    all_events.sort(key=lambda x: x.get('importance', 0), reverse=True)
    
    # 상위 50% 또는 최대 10개
    significant_count = min(max(len(all_events) // 2, 1), 10)
    
    return all_events[:significant_count]

def filter_imminent_events(events, days=60):
    """
    임박한 이벤트 필터링 (지정된 일수 이내)
    """
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.now() + timedelta(days=days)
    imminent_events = []
    
    for event in events:
        event_date_str = event.get('date')
        if event_date_str:
            try:
                # 다양한 날짜 형식 파싱 시도
                event_date = parse_date_flexible(event_date_str)
                if event_date and event_date <= cutoff_date:
                    imminent_events.append(event)
            except:
                # 날짜 파싱 실패 시에도 포함 (보수적 접근)
                imminent_events.append(event)
        else:
            # 날짜 정보가 없으면 포함 (보수적 접근)
            imminent_events.append(event)
    
    return imminent_events

def evaluate_concreteness(events):
    """
    이벤트 구체화 정도 평가
    """
    concrete_events = []
    
    # 구체화 지표
    concreteness_indicators = [
        '확정', '계약', '승인', '선정', '체결', '발표',
        '출시일', '일정', '금액', '규모', '대상'
    ]
    
    for event in events:
        title = event.get('title', '').lower()
        
        # 구체성 점수 계산
        concreteness_score = sum(1 for indicator in concreteness_indicators 
                                if indicator in title)
        
        # 구체성 임계값 (2개 이상의 지표)
        if concreteness_score >= 2:
            event['concreteness_score'] = concreteness_score
            concrete_events.append(event)
    
    # 구체성 점수 기준 정렬
    concrete_events.sort(key=lambda x: x.get('concreteness_score', 0), reverse=True)
    
    return concrete_events

def get_event_analysis(concrete_events):
    """이벤트 분석 요약"""
    if not concrete_events:
        return "구체화된 이벤트 없음"
    
    # 이벤트 유형별 집계
    event_types = {}
    for event in concrete_events:
        event_type = event.get('type', 'unknown')
        event_types[event_type] = event_types.get(event_type, 0) + 1
    
    # 주요 이벤트 유형
    if event_types:
        top_type = max(event_types.items(), key=lambda x: x[1])
        type_names = {
            'disclosure': '공시 이벤트',
            'news_event': '뉴스 이벤트',
            'calendar': '기업 일정',
            'analyst': '애널리스트 이벤트'
        }
        
        main_type = type_names.get(top_type[0], top_type[0])
        analysis = f"주요 이벤트: {main_type} ({len(concrete_events)}건)"
    else:
        analysis = f"구체화된 이벤트: {len(concrete_events)}건"
    
    return analysis

def parse_date_flexible(date_string):
    """
    다양한 날짜 형식 파싱
    """
    from datetime import datetime
    
    date_formats = [
        '%Y-%m-%d',
        '%Y.%m.%d',
        '%Y/%m/%d',
        '%m/%d/%Y',
        '%d/%m/%Y'
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_string.strip(), fmt)
        except ValueError:
            continue
    
    return None

# 🤔 자동화 고려사항
def upcoming_event_automation_analysis():
    """
    구체화된 이벤트/호재 자동화 분석
    """
    analysis = {
        "데이터 소스": {
            "DART 공시": {
                "장점": ["공식성", "신뢰성", "구조화된 데이터"],
                "단점": ["지연성", "형식적 표현"],
                "활용": "합병, 분할, 계약 등 중요 이벤트 자동 탐지"
            },
            "뉴스 매체": {
                "장점": ["실시간성", "상세 정보", "맥락 제공"],
                "단점": ["신뢰성 검증 필요", "노이즈 많음"],
                "활용": "신제품, 계약, 기술 개발 등 호재 정보"
            },
            "기업 IR": {
                "장점": ["공식 정보", "투자자 중심"],
                "단점": ["접근성", "업데이트 빈도"],
                "활용": "실적 발표, 사업 계획 등"
            }
        },
        
        "분석 기법": {
            "키워드 분석": {
                "정확도": "70-75%",
                "구현 난이도": "중간",
                "한계": "맥락 이해 제한"
            },
            "자연어 처리": {
                "정확도": "80-85%",
                "구현 난이도": "높음",
                "활용": "의미론적 분석, 감성 분석"
            },
            "시계열 분석": {
                "정확도": "75-80%",
                "구현 난이도": "높음",
                "활용": "이벤트 시점 예측"
            }
        },
        
        "구현 전략": {
            "Phase 1": "DART 공시 기반 이벤트 탐지 + 수동 검증",
            "Phase 2": "뉴스 분석 추가 + 중요도 자동 평가",
            "Phase 3": "AI 기반 종합 판단 + 예측 시스템"
        }
    }
    
    return analysis

# Phase별 구현 권장사항
"""
Phase 1: 공시 기반 반자동화
- DART API로 중요 공시사항 자동 수집
- 이벤트성 공시 키워드 필터링
- 사용자 최종 판단 (Y/N 입력)

Phase 2: 종합 분석 자동화
- 뉴스 분석 추가하여 정보 보완
- 중요도 및 구체성 자동 평가
- 임계값 기반 자동 판단

Phase 3: 예측 시스템
- 과거 패턴 학습으로 이벤트 예측
- 산업별, 기업별 특성 반영
- 실시간 모니터링 및 알림

자동화 우선순위: 높음
- 투자 기회 포착에 직결
- 시간 민감성 중요
- 정보의 질이 수익성에 직접 영향
"""
```

### 10. 확실한 주도 테마 (D002)

**평가 공식**: ✅ **확인완료**
```excel
=VLOOKUP(IF(UPPER($F46)="Y","D002","Z999"),'디노테스트_평가기준'!B:D,3,FALSE)
```

**입력 방식**: 🔧 **사용자 직접 입력**
- 현재는 Y/N으로 확실한 주도 테마 여부를 직접 입력
- 향후 테마 분석 시스템 및 시장 트렌드 자동 탐지 가능

**셀 참조**:
- `$F46`: 확실한 주도 테마 여부 ("Y" 또는 "N")

**로직 분해**:
```
1. UPPER($F46) = "Y" → D002 (+1점): 확실한 주도 테마
2. 기타 ("N" 또는 다른 값) → Z999 (0점): 해당없음
```

**주도 테마 유형 예시**:
- **산업 정책**: 정부 주도 신산업 육성 (K-뉴딜, 탄소중립, 디지털 전환)
- **기술 혁신**: AI, 메타버스, 양자컴퓨팅, 바이오헬스케어
- **ESG 트렌드**: 친환경 에너지, 지속가능 경영, 사회적 가치
- **글로벌 이슈**: 공급망 재편, 지정학적 변화, 인플레이션 대응
- **소비 트렌드**: 언택트, 개인화, 프리미엄화, MZ세대 소비
- **구조 변화**: 디지털 전환, 자동화, 플랫폼 경제
- **신흥 시장**: 신에너지, 우주항공, 푸드테크, 핀테크

**Python 구현**:
```python
def calculate_leading_theme_score(is_leading_theme):
    """
    확실한 주도 테마 점수 계산
    is_leading_theme: True/False 또는 "Y"/"N"
    """
    if isinstance(is_leading_theme, str):
        is_leading_theme = is_leading_theme.upper() == "Y"
    
    if is_leading_theme:
        return 1    # D002: 확실한 주도 테마 (+1점)
    else:
        return 0    # Z999: 해당없음

def detect_leading_themes_auto(stock_code, company_name, industry_code):
    """
    확실한 주도 테마 자동 탐지
    """
    try:
        # 다중 분석 수행
        analysis_results = {
            'market_themes': analyze_current_market_themes(),
            'industry_trends': analyze_industry_trends(industry_code),
            'company_positioning': analyze_company_theme_exposure(company_name, stock_code),
            'news_sentiment': analyze_theme_news_sentiment(company_name),
            'performance_correlation': analyze_theme_performance_correlation(stock_code)
        }
        
        # 종합 테마 점수 계산
        theme_score = calculate_comprehensive_theme_score(analysis_results)
        
        # 주도 테마 여부 판단 (임계값: 0.75)
        is_leading_theme = theme_score >= 0.75
        
        return {
            'is_leading_theme': is_leading_theme,
            'theme_score': theme_score,
            'dominant_themes': get_dominant_themes(analysis_results),
            'theme_strength': evaluate_theme_strength(analysis_results),
            'score': calculate_leading_theme_score(is_leading_theme),
            'analysis': get_theme_analysis(analysis_results)
        }
        
    except Exception as e:
        return {
            'is_leading_theme': False,
            'score': 0,
            'error': str(e),
            'analysis': '분석 실패'
        }

def analyze_current_market_themes():
    """
    현재 시장 주도 테마 분석
    """
    try:
        # 시장 전체 섹터 성과 분석
        sector_performance = get_sector_performance_data(days=30)
        
        # 상승률 상위 섹터 식별
        top_performing_sectors = sorted(
            sector_performance.items(), 
            key=lambda x: x[1]['return_30d'], 
            reverse=True
        )[:5]
        
        # 거래량 급증 섹터 식별
        high_volume_sectors = identify_high_volume_sectors(sector_performance)
        
        # 뉴스 언급 빈도 높은 테마
        trending_themes = get_trending_themes_from_news(days=30)
        
        return {
            'top_performing_sectors': top_performing_sectors,
            'high_volume_sectors': high_volume_sectors,
            'trending_themes': trending_themes,
            'market_sentiment': calculate_overall_market_sentiment()
        }
        
    except Exception as e:
        return {'error': str(e)}

def analyze_industry_trends(industry_code):
    """
    산업별 트렌드 분석
    """
    try:
        # 해당 산업의 최근 성과
        industry_performance = get_industry_performance(industry_code, days=60)
        
        # 산업 내 테마 키워드 분석
        industry_keywords = extract_industry_theme_keywords(industry_code)
        
        # 정부 정책과의 연관성
        policy_relevance = analyze_policy_relevance(industry_code)
        
        # 글로벌 트렌드와의 일치도
        global_alignment = analyze_global_trend_alignment(industry_code)
        
        return {
            'performance': industry_performance,
            'theme_keywords': industry_keywords,
            'policy_relevance': policy_relevance,
            'global_alignment': global_alignment
        }
        
    except Exception as e:
        return {'error': str(e)}

def analyze_company_theme_exposure(company_name, stock_code):
    """
    기업의 테마 노출도 분석
    """
    try:
        # 기업의 사업 영역 분석
        business_segments = get_company_business_segments(stock_code)
        
        # 최근 공시에서 테마 키워드 추출
        disclosure_themes = extract_themes_from_disclosures(stock_code, days=90)
        
        # 뉴스에서 테마 언급 빈도
        news_theme_mentions = count_theme_mentions_in_news(company_name, days=60)
        
        # 애널리스트 리포트 테마 분석
        analyst_themes = analyze_analyst_report_themes(stock_code)
        
        return {
            'business_segments': business_segments,
            'disclosure_themes': disclosure_themes,
            'news_mentions': news_theme_mentions,
            'analyst_themes': analyst_themes
        }
        
    except Exception as e:
        return {'error': str(e)}

def calculate_comprehensive_theme_score(analysis_results):
    """
    종합 테마 점수 계산 (0.0 ~ 1.0)
    """
    score = 0.0
    
    # 시장 테마 점수 (30%)
    market_themes = analysis_results.get('market_themes', {})
    if not market_themes.get('error'):
        market_score = calculate_market_theme_score(market_themes)
        score += market_score * 0.3
    
    # 산업 트렌드 점수 (25%)
    industry_trends = analysis_results.get('industry_trends', {})
    if not industry_trends.get('error'):
        industry_score = calculate_industry_trend_score(industry_trends)
        score += industry_score * 0.25
    
    # 기업 포지셔닝 점수 (35%)
    company_positioning = analysis_results.get('company_positioning', {})
    if not company_positioning.get('error'):
        company_score = calculate_company_positioning_score(company_positioning)
        score += company_score * 0.35
    
    # 뉴스 감성 점수 (10%)
    news_sentiment = analysis_results.get('news_sentiment', 0)
    score += news_sentiment * 0.1
    
    return min(score, 1.0)

def get_dominant_themes(analysis_results):
    """
    주도 테마 식별
    """
    dominant_themes = []
    
    # 시장 테마
    market_themes = analysis_results.get('market_themes', {})
    trending_themes = market_themes.get('trending_themes', [])
    dominant_themes.extend(trending_themes[:3])
    
    # 산업 테마
    industry_trends = analysis_results.get('industry_trends', {})
    industry_keywords = industry_trends.get('theme_keywords', [])
    dominant_themes.extend(industry_keywords[:2])
    
    # 중복 제거 및 상위 5개
    unique_themes = list(set(dominant_themes))
    return unique_themes[:5]

def get_theme_analysis(analysis_results):
    """테마 분석 요약"""
    dominant_themes = get_dominant_themes(analysis_results)
    
    if not dominant_themes:
        return "주도 테마 없음"
    
    theme_strength = evaluate_theme_strength(analysis_results)
    strength_desc = "강함" if theme_strength > 0.8 else "보통" if theme_strength > 0.6 else "약함"
    
    analysis = f"주도 테마: {', '.join(dominant_themes[:3])} (강도: {strength_desc})"
    
    return analysis

def evaluate_theme_strength(analysis_results):
    """테마 강도 평가"""
    # 시장 성과 + 뉴스 언급 + 정책 지원 종합 평가
    market_performance = analysis_results.get('market_themes', {}).get('top_performing_sectors', [])
    policy_support = analysis_results.get('industry_trends', {}).get('policy_relevance', 0)
    news_volume = analysis_results.get('news_sentiment', 0)
    
    strength = (len(market_performance) * 0.1 + policy_support * 0.4 + news_volume * 0.5)
    return min(strength, 1.0)

# 키움 API 연동 구현 예시
def get_sector_performance_data(days=30):
    """
    섹터별 성과 데이터 수집
    """
    try:
        # 키움 API를 통한 업종별 지수 데이터 수집
        sectors = [
            'IT', '바이오', '2차전지', '반도체', '자동차', 
            '금융', '화학', '철강', '건설', '통신'
        ]
        
        sector_data = {}
        for sector in sectors:
            # ka10007 (시장정보) 또는 업종별 API 활용
            performance = kiwoom_api.get_sector_performance(sector, days)
            sector_data[sector] = {
                'return_30d': performance.get('return_30d', 0),
                'volume_ratio': performance.get('volume_ratio', 1),
                'market_cap': performance.get('market_cap', 0)
            }
        
        return sector_data
        
    except Exception as e:
        return {}

# 🤔 자동화 고려사항
def leading_theme_automation_analysis():
    """
    확실한 주도 테마 자동화 분석
    """
    analysis = {
        "데이터 소스": {
            "시장 데이터": {
                "장점": ["정량적", "실시간", "객관적"],
                "단점": ["후행 지표", "노이즈"],
                "활용": "섹터 성과, 거래량, 자금 흐름 분석"
            },
            "뉴스/미디어": {
                "장점": ["선행성", "트렌드 감지", "다양성"],
                "단점": ["주관적", "노이즈", "일시적"],
                "활용": "테마 키워드, 감성 분석, 트렌드 탐지"
            },
            "정책/규제": {
                "장점": ["공식성", "지속성", "영향력"],
                "단점": ["예측 어려움", "해석 복잡"],
                "활용": "정부 정책, 규제 변화, 지원 정책"
            }
        },
        
        "분석 기법": {
            "정량적 분석": {
                "성과 비교": "섹터별 수익률, 거래량, 변동성",
                "상관관계": "테마 간 상관관계, 시장 베타",
                "모멘텀": "가격 모멘텀, 자금 흐름 모멘텀"
            },
            "정성적 분석": {
                "키워드 분석": "뉴스, 공시, SNS 키워드 빈도",
                "감성 분석": "긍정/부정 감성 지수",
                "트렌드 분석": "검색량, 언급량 추이"
            },
            "복합 분석": {
                "테마 강도": "정량 + 정성 지표 종합",
                "지속성": "시간에 따른 테마 강도 변화",
                "확산성": "테마의 산업/기업 확산 정도"
            }
        },
        
        "구현 전략": {
            "Phase 1": "키움 API + 뉴스 분석 기반 테마 탐지",
            "Phase 2": "정책 분석 + 글로벌 트렌드 연동",
            "Phase 3": "AI 기반 테마 예측 + 투자 전략 연계"
        }
    }
    
    return analysis

# Phase별 구현 권장사항
"""
Phase 1: 기본 테마 탐지 시스템
- 키움 API로 섹터별 성과 데이터 수집
- 뉴스 키워드 분석으로 트렌드 테마 식별
- 기업의 해당 테마 노출도 평가
- 임계값 기반 주도 테마 판단

Phase 2: 고도화된 테마 분석
- 정부 정책 데이터베이스 연동
- 글로벌 트렌드와 국내 시장 연계 분석
- 테마의 생명주기 및 지속성 평가
- 다차원 점수 체계 도입

Phase 3: 예측 기반 테마 시스템
- 머신러닝 기반 테마 예측 모델
- 테마 전환점 예측 및 알림
- 포트폴리오 테마 익스포저 관리
- 테마 기반 투자 전략 자동 생성

자동화 우선순위: 높음
- 테마 투자의 핵심 정보
- 시장 타이밍과 직결
- 정보의 신속성이 수익에 직접 영향
- 다만 false positive 위험성 고려 필요
"""
```

### 11. 호재뉴스 도배 (D008)

**평가 공식**: ✅ **확인완료**
```excel
=VLOOKUP(IF(UPPER($F47)="Y","D008","Z999"),'디노테스트_평가기준'!B:D,3,FALSE)
```

**입력 방식**: 🔧 **사용자 직접 입력**
- 현재는 Y/N으로 호재뉴스 도배 여부를 직접 입력
- 향후 뉴스 빈도 분석 및 비정상적 뉴스 패턴 자동 탐지 가능

**셀 참조**:
- `$F47`: 호재뉴스 도배 여부 ("Y" 또는 "N")

**로직 분해**:
```
1. UPPER($F47) = "Y" → D008 (+1점): 호재뉴스 도배
2. 기타 ("N" 또는 다른 값) → Z999 (0점): 해당없음
```

**호재뉴스 도배 특징**:
- **비정상적 빈도**: 단기간 내 과도한 호재성 뉴스 집중
- **내용 중복**: 유사하거나 반복되는 내용의 뉴스
- **타이밍 집중**: 특정 시점(실적발표 전, 주가 하락 시점 등)에 몰림
- **출처 다양화**: 여러 매체에서 동시다발적 보도
- **과장된 표현**: "혁신적", "획기적", "대박" 등 자극적 표현 남용
- **추상적 내용**: 구체적 근거 없이 막연한 기대감만 조성

**⚠️ 주의사항**: 호재뉴스 도배는 오히려 **주의 신호**일 수 있음
- 인위적 주가 부양 시도의 가능성
- 실제 펀더멘털과 괴리된 과도한 기대감 조성
- 단기 급등 후 급락의 전조 신호

**Python 구현**:
```python
def calculate_positive_news_flooding_score(has_news_flooding):
    """
    호재뉴스 도배 점수 계산
    has_news_flooding: True/False 또는 "Y"/"N"
    """
    if isinstance(has_news_flooding, str):
        has_news_flooding = has_news_flooding.upper() == "Y"
    
    if has_news_flooding:
        return 1    # D008: 호재뉴스 도배 (+1점)
    else:
        return 0    # Z999: 해당없음

def detect_positive_news_flooding_auto(company_name, days=7):
    """
    호재뉴스 도배 자동 탐지
    """
    try:
        # 뉴스 데이터 수집 (최근 7일)
        news_data = collect_news_data(company_name, days)
        
        # 호재성 뉴스 필터링
        positive_news = filter_positive_news(news_data)
        
        # 뉴스 도배 패턴 분석
        flooding_analysis = analyze_news_flooding_patterns(positive_news)
        
        # 도배 여부 판단
        is_flooding = evaluate_news_flooding(flooding_analysis)
        
        return {
            'has_news_flooding': is_flooding,
            'total_news_count': len(news_data),
            'positive_news_count': len(positive_news),
            'flooding_score': flooding_analysis.get('flooding_score', 0),
            'flooding_indicators': flooding_analysis.get('indicators', []),
            'score': calculate_positive_news_flooding_score(is_flooding),
            'analysis': get_news_flooding_analysis(flooding_analysis),
            'warning': get_flooding_warning(is_flooding)
        }
        
    except Exception as e:
        return {
            'has_news_flooding': False,
            'score': 0,
            'error': str(e),
            'analysis': '분석 실패'
        }

def filter_positive_news(news_data):
    """
    호재성 뉴스 필터링
    """
    positive_keywords = {
        # 성과 관련
        "성과": ["수주", "계약", "매출증가", "흑자전환", "실적개선"],
        
        # 기술/제품 관련
        "기술": ["신기술", "특허", "개발완료", "혁신", "세계최초"],
        
        # 사업 확장
        "확장": ["진출", "확장", "투자", "인수", "합병"],
        
        # 정부/정책 관련
        "정책": ["선정", "지원", "승인", "허가", "규제완화"],
        
        # 과장 표현
        "과장": ["대박", "급등", "폭등", "혁신적", "획기적", "놀라운"]
    }
    
    positive_news = []
    
    for news in news_data:
        title = news.get('title', '').lower()
        content = news.get('content', '').lower()
        full_text = f"{title} {content}"
        
        # 호재 키워드 매칭
        matched_categories = []
        total_matches = 0
        
        for category, keywords in positive_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in full_text)
            if matches > 0:
                matched_categories.append((category, matches))
                total_matches += matches
        
        # 호재성 뉴스로 분류 (키워드 1개 이상 매칭)
        if total_matches >= 1:
            news['positive_score'] = total_matches
            news['positive_categories'] = matched_categories
            positive_news.append(news)
    
    # 호재 점수 기준으로 정렬
    positive_news.sort(key=lambda x: x['positive_score'], reverse=True)
    
    return positive_news

def analyze_news_flooding_patterns(positive_news):
    """
    뉴스 도배 패턴 분석
    """
    if not positive_news:
        return {'flooding_score': 0, 'indicators': []}
    
    indicators = []
    flooding_score = 0
    
    # 1. 뉴스 빈도 분석 (일평균 2개 이상)
    daily_avg = len(positive_news) / 7
    if daily_avg >= 2:
        indicators.append(f"높은 빈도: 일평균 {daily_avg:.1f}개")
        flooding_score += 0.3
    
    # 2. 내용 중복도 분석
    duplicate_ratio = calculate_content_similarity(positive_news)
    if duplicate_ratio > 0.6:  # 60% 이상 중복
        indicators.append(f"내용 중복: {duplicate_ratio*100:.1f}%")
        flooding_score += 0.25
    
    # 3. 시간 집중도 분석
    time_concentration = analyze_time_concentration(positive_news)
    if time_concentration > 0.7:  # 특정 시간대 70% 이상 집중
        indicators.append("시간 집중: 특정 시점 몰림")
        flooding_score += 0.2
    
    # 4. 출처 다양성 분석
    source_diversity = calculate_source_diversity(positive_news)
    if source_diversity > 0.8:  # 다양한 출처 동시 보도
        indicators.append("출처 다양화: 동시다발적 보도")
        flooding_score += 0.15
    
    # 5. 과장 표현 빈도
    exaggeration_ratio = calculate_exaggeration_ratio(positive_news)
    if exaggeration_ratio > 0.4:  # 40% 이상 과장 표현
        indicators.append(f"과장 표현: {exaggeration_ratio*100:.1f}%")
        flooding_score += 0.1
    
    return {
        'flooding_score': min(flooding_score, 1.0),
        'indicators': indicators,
        'daily_avg': daily_avg,
        'duplicate_ratio': duplicate_ratio,
        'time_concentration': time_concentration,
        'source_diversity': source_diversity,
        'exaggeration_ratio': exaggeration_ratio
    }

def calculate_content_similarity(news_list):
    """
    뉴스 내용 유사도 계산
    """
    from difflib import SequenceMatcher
    
    if len(news_list) < 2:
        return 0
    
    similarities = []
    
    for i in range(len(news_list)):
        for j in range(i + 1, len(news_list)):
            title1 = news_list[i].get('title', '')
            title2 = news_list[j].get('title', '')
            
            similarity = SequenceMatcher(None, title1, title2).ratio()
            similarities.append(similarity)
    
    return sum(similarities) / len(similarities) if similarities else 0

def analyze_time_concentration(news_list):
    """
    시간 집중도 분석
    """
    if not news_list:
        return 0
    
    from datetime import datetime
    import collections
    
    # 시간별 뉴스 분포
    time_distribution = collections.defaultdict(int)
    
    for news in news_list:
        pub_date = news.get('pub_date', '')
        try:
            # 날짜에서 일자 추출 (간단화)
            day = pub_date.split(' ')[0] if pub_date else 'unknown'
            time_distribution[day] += 1
        except:
            time_distribution['unknown'] += 1
    
    if not time_distribution:
        return 0
    
    # 최대 집중 비율 계산
    max_count = max(time_distribution.values())
    total_count = sum(time_distribution.values())
    
    return max_count / total_count if total_count > 0 else 0

def calculate_source_diversity(news_list):
    """
    출처 다양성 계산
    """
    if not news_list:
        return 0
    
    sources = set()
    for news in news_list:
        source = news.get('source', 'unknown')
        sources.add(source)
    
    # 출처 수 / 뉴스 수 (최대 1.0)
    diversity = len(sources) / len(news_list)
    return min(diversity, 1.0)

def calculate_exaggeration_ratio(news_list):
    """
    과장 표현 비율 계산
    """
    if not news_list:
        return 0
    
    exaggeration_words = [
        "대박", "급등", "폭등", "혁신적", "획기적", 
        "놀라운", "엄청난", "대단한", "최고", "최대"
    ]
    
    exaggerated_count = 0
    
    for news in news_list:
        title = news.get('title', '').lower()
        if any(word in title for word in exaggeration_words):
            exaggerated_count += 1
    
    return exaggerated_count / len(news_list)

def evaluate_news_flooding(flooding_analysis):
    """
    뉴스 도배 여부 최종 판단
    """
    flooding_score = flooding_analysis.get('flooding_score', 0)
    
    # 임계값: 0.6 (60% 이상 확신할 때 도배로 판단)
    return flooding_score >= 0.6

def get_news_flooding_analysis(flooding_analysis):
    """뉴스 도배 분석 요약"""
    if flooding_analysis.get('flooding_score', 0) < 0.3:
        return "정상적인 뉴스 패턴"
    
    indicators = flooding_analysis.get('indicators', [])
    if not indicators:
        return "뉴스 도배 의심"
    
    return f"뉴스 도배 패턴: {', '.join(indicators[:2])}"

def get_flooding_warning(is_flooding):
    """뉴스 도배 경고 메시지"""
    if not is_flooding:
        return None
    
    return {
        'level': 'WARNING',
        'message': '⚠️ 호재뉴스 도배 패턴 감지',
        'advice': [
            '인위적 주가 부양 시도 가능성 검토',
            '실제 펀더멘털과 뉴스 내용 대조 확인',
            '단기 급등 후 급락 위험 고려',
            '신중한 투자 판단 권장'
        ]
    }

# 🤔 자동화 고려사항
def positive_news_flooding_automation_analysis():
    """
    호재뉴스 도배 자동화 분석
    """
    analysis = {
        "탐지 기법": {
            "빈도 분석": {
                "정확도": "80-85%",
                "구현 난이도": "낮음",
                "장점": "객관적 수치 기반"
            },
            "내용 분석": {
                "정확도": "75-80%",
                "구현 난이도": "중간",
                "장점": "의미론적 중복 탐지"
            },
            "패턴 분석": {
                "정확도": "70-75%",
                "구현 난이도": "높음",
                "장점": "조작 패턴 식별"
            }
        },
        
        "위험 요소": {
            "False Positive": {
                "원인": "정당한 연속 호재를 도배로 오인",
                "대책": "펀더멘털 검증, 시장 상황 고려"
            },
            "False Negative": {
                "원인": "교묘한 도배 패턴 미탐지",
                "대책": "다각도 분석, 임계값 조정"
            }
        },
        
        "구현 전략": {
            "Phase 1": "빈도 + 유사도 기반 기본 탐지",
            "Phase 2": "시간/출처 패턴 분석 추가",
            "Phase 3": "AI 기반 종합 판단 + 경고 시스템"
        }
    }
    
    return analysis

# Phase별 구현 권장사항
"""
Phase 1: 기본 도배 탐지
- 뉴스 빈도 분석 (일평균 2개 이상)
- 제목 유사도 분석 (60% 이상 중복)
- 기본 임계값 기반 판단

Phase 2: 고도화된 패턴 분석
- 시간 집중도 분석
- 출처 다양성 분석  
- 과장 표현 빈도 분석
- 다차원 점수 체계

Phase 3: 지능형 탐지 시스템
- 펀더멘털과 뉴스 괴리도 분석
- 주가 패턴과 뉴스 패턴 상관관계
- 실시간 모니터링 및 경고

자동화 우선순위: 중간
- 조작 탐지에 유용하지만 오탐 위험
- 보조 지표로 활용 권장
- 사용자 최종 판단 유지 필요

⚠️ 중요 고려사항:
호재뉴스 도배는 오히려 "주의 신호"일 수 있으므로,
단순히 +1점으로 처리하기보다는
추가적인 검증과 경고 시스템 구축이 중요함
"""
```

### 12. 이자보상배율 (D009) - 1 미만

**이자보상배율 데이터 수집 공식**: ✅ **확인완료**
```excel
=INDEX(IMPORTHTML($J$3&G19,"table"),18,5)
```

**해당여부 판단 공식**: ✅ **확인완료**
```excel
=IF(E48<1,"Y","N")
```

**최종 점수 공식**: ✅ **확인완료**
```excel
=VLOOKUP(IF(UPPER($F48)="Y","D009","Z999"),'디노테스트_평가기준'!B:D,3,FALSE)
```

**입력 방식**: 🔄 **반자동** (데이터 수집 자동 + 판단 자동)
- 이자보상배율 데이터는 IMPORTHTML로 자동 수집
- 1 미만 여부 자동 판단 후 Y/N 변환
- 최종 점수는 VLOOKUP으로 자동 계산

**셀 참조**:
- `$J$3`: 기본 URL 주소
- `G19`: 종목 코드
- `E48`: 이자보상배율 값 (자동 수집)
- `F48`: 해당여부 ("Y" 또는 "N", 자동 판단)

**로직 분해**:
```
1. 데이터 수집:
   - IMPORTHTML로 외부 사이트에서 이자보상배율 데이터 크롤링
   - 테이블 18번째 행, 5번째 열에서 값 추출

2. 위험도 판단:
   - 이자보상배율 < 1 → "Y" (위험)
   - 이자보상배율 ≥ 1 → "N" (안전)

3. 점수 부여:
   - 해당여부 = "Y" → D009 (-1점): 이자보상배율 < 1 (재무 위험)
   - 기타 ("N") → Z999 (0점): 해당없음
```

**이자보상배율 의미**:
- **정의**: 영업이익 ÷ 이자비용
- **의미**: 기업이 이자를 지급할 수 있는 능력
- **위험 기준**: 1 미만 시 이자 지급 능력 부족으로 재무 위험 증가
- **안전 기준**: 2 이상이면 안전, 3 이상이면 매우 안전

**Python 구현**:
```python
def calculate_interest_coverage_score(interest_coverage_ratio):
    """
    이자보상배율 점수 계산
    interest_coverage_ratio: 이자보상배율 값
    """
    if interest_coverage_ratio is None:
        return 0  # 데이터 없음
    
    if interest_coverage_ratio < 1:
        return -1   # D009: 이자보상배율 < 1 (감점)
    else:
        return 0    # Z999: 해당없음

def get_interest_coverage_ratio_auto(stock_code):
    """
    이자보상배율 자동 수집 및 계산
    """
    try:
        # 방법 1: 웹 크롤링 (Google Sheets IMPORTHTML 방식 재현)
        web_data = get_interest_coverage_from_web(stock_code)
        
        # 방법 2: DART API를 통한 재무제표 기반 계산
        dart_data = calculate_interest_coverage_from_financials(stock_code)
        
        # 방법 3: 키움 API 데이터 활용 (가능한 경우)
        kiwoom_data = get_interest_coverage_from_kiwoom(stock_code)
        
        # 데이터 우선순위: DART > 웹크롤링 > 키움
        final_ratio = dart_data or web_data or kiwoom_data
        
        if final_ratio is not None:
            return {
                'interest_coverage_ratio': final_ratio,
                'is_risky': final_ratio < 1,
                'risk_level': get_risk_level(final_ratio),
                'score': calculate_interest_coverage_score(final_ratio),
                'analysis': get_interest_coverage_analysis(final_ratio),
                'data_source': get_data_source(dart_data, web_data, kiwoom_data)
            }
        
        return {
            'interest_coverage_ratio': None,
            'score': 0,
            'analysis': '데이터 수집 실패'
        }
        
    except Exception as e:
        return {
            'interest_coverage_ratio': None,
            'score': 0,
            'error': str(e),
            'analysis': '계산 실패'
        }

def get_interest_coverage_from_web(stock_code):
    """
    웹 크롤링으로 이자보상배율 수집 (Google Sheets IMPORTHTML 방식)
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        
        # 기본 URL + 종목코드 조합
        base_url = "https://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A"
        url = f"{base_url}{stock_code}"
        
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 테이블에서 이자보상배율 찾기 (18번째 행, 5번째 열)
        tables = soup.find_all('table')
        
        if tables:
            # 적절한 테이블 찾기 (실제 구조에 맞게 조정 필요)
            target_table = tables[0]  # 첫 번째 테이블부터 시도
            rows = target_table.find_all('tr')
            
            if len(rows) >= 18:
                cells = rows[17].find_all(['td', 'th'])  # 18번째 행 (0-based index)
                if len(cells) >= 5:
                    ratio_text = cells[4].get_text().strip()  # 5번째 열
                    
                    # 숫자 추출 및 변환
                    ratio_value = extract_numeric_value(ratio_text)
                    return ratio_value
        
        return None
        
    except Exception as e:
        return None

def calculate_interest_coverage_from_financials(stock_code):
    """
    DART API 재무제표 데이터로 이자보상배율 계산
    """
    try:
        dart_service = DartDataService()
        corp_code = dart_service.get_corp_code(stock_code)
        
        # 최신 분기 재무제표 조회
        financial_data = dart_service.get_financial_statements(corp_code)
        
        # 영업이익과 이자비용 추출
        operating_income = financial_data.get('operating_income', 0)
        interest_expense = financial_data.get('interest_expense', 0)
        
        # 이자보상배율 계산
        if interest_expense > 0:
            ratio = operating_income / interest_expense
            return ratio
        else:
            return float('inf')  # 이자비용이 0이면 무한대 (매우 안전)
        
    except Exception as e:
        return None

def get_interest_coverage_from_kiwoom(stock_code):
    """
    키움 API로 이자보상배율 관련 데이터 수집
    """
    try:
        # ka10001 (기본정보)에서 재무지표 확인
        basic_info = kiwoom_api.get_basic_info(stock_code)
        
        # 이자보상배율이 직접 제공되는지 확인
        interest_coverage = basic_info.get('interest_coverage_ratio')
        
        if interest_coverage is not None:
            return float(interest_coverage)
        
        # 직접 제공되지 않으면 영업이익/이자비용으로 계산
        operating_income = basic_info.get('operating_income')
        interest_expense = basic_info.get('interest_expense')
        
        if operating_income and interest_expense and interest_expense > 0:
            return operating_income / interest_expense
        
        return None
        
    except Exception as e:
        return None

def extract_numeric_value(text):
    """
    텍스트에서 숫자 값 추출
    """
    import re
    
    # 쉼표 제거
    clean_text = text.replace(',', '')
    
    # 숫자 패턴 매칭
    number_pattern = r'-?\d+\.?\d*'
    matches = re.findall(number_pattern, clean_text)
    
    if matches:
        try:
            return float(matches[0])
        except ValueError:
            pass
    
    return None

def get_risk_level(ratio):
    """위험도 레벨 평가"""
    if ratio is None:
        return "알 수 없음"
    elif ratio < 1:
        return "위험 (< 1)"
    elif ratio < 2:
        return "주의 (1~2)"
    elif ratio < 3:
        return "안전 (2~3)"
    else:
        return "매우 안전 (≥ 3)"

def get_interest_coverage_analysis(ratio):
    """이자보상배율 분석"""
    if ratio is None:
        return "이자보상배율 데이터 없음"
    
    analysis = f"이자보상배율: {ratio:.2f}배"
    
    if ratio < 1:
        analysis += " (이자 지급 능력 부족, 재무 위험 높음)"
    elif ratio < 2:
        analysis += " (이자 지급 능력 제한적, 주의 필요)"
    elif ratio < 3:
        analysis += " (이자 지급 능력 양호)"
    else:
        analysis += " (이자 지급 능력 우수)"
    
    return analysis

def get_data_source(dart_data, web_data, kiwoom_data):
    """데이터 소스 식별"""
    if dart_data is not None:
        return "DART 재무제표"
    elif web_data is not None:
        return "웹 크롤링"
    elif kiwoom_data is not None:
        return "키움 API"
    else:
        return "데이터 없음"

# 🤔 자동화 고려사항
def interest_coverage_automation_analysis():
    """
    이자보상배율 자동화 분석
    """
    analysis = {
        "데이터 소스": {
            "DART API": {
                "장점": ["공식 데이터", "정확성", "일관성"],
                "단점": ["분기 단위 업데이트", "지연성"],
                "활용": "재무제표에서 영업이익/이자비용 직접 계산",
                "정확도": "95%"
            },
            "웹 크롤링": {
                "장점": ["실시간 업데이트", "가공된 지표"],
                "단점": ["불안정성", "구조 변경 위험"],
                "활용": "FnGuide 등 금융정보 사이트",
                "정확도": "85%"
            },
            "키움 API": {
                "장점": ["안정성", "통합성"],
                "단점": ["제한적 재무지표"],
                "활용": "기본정보 API에서 재무지표 확인",
                "정확도": "90%"
            }
        },
        
        "계산 방식": {
            "직접 계산": {
                "공식": "영업이익 ÷ 이자비용",
                "장점": "투명성, 검증 가능성",
                "단점": "복잡성, 데이터 품질 의존"
            },
            "제공 지표": {
                "공식": "외부에서 계산된 값 활용",
                "장점": "간편성, 전문성",
                "단점": "계산 과정 불투명"
            }
        },
        
        "구현 전략": {
            "Phase 1": "DART API 기반 직접 계산",
            "Phase 2": "웹 크롤링 추가로 보완",
            "Phase 3": "다중 소스 검증 시스템"
        }
    }
    
    return analysis

# Phase별 구현 권장사항
"""
Phase 1: DART API 기반 계산
- DART API로 최신 재무제표 수집
- 영업이익과 이자비용 추출
- 이자보상배율 직접 계산
- 1 미만 여부 자동 판단

Phase 2: 다중 소스 검증
- 웹 크롤링으로 외부 데이터 수집
- 키움 API 재무지표 확인
- 데이터 소스 간 일치성 검증
- 불일치 시 경고 및 수동 확인 요청

Phase 3: 고도화 시스템
- 시계열 분석으로 추세 파악
- 동종업계 대비 상대 평가
- 예측 모델로 미래 위험도 예상
- 실시간 모니터링 및 알림

자동화 우선순위: 높음
- 재무 안전성의 핵심 지표
- 객관적 수치로 자동화 용이
- 투자 리스크 관리에 직접 활용 가능

⚠️ 주의사항:
- 음수 영업이익 시 계산 불가 (별도 처리 필요)
- 이자비용이 0인 경우 처리 (무차입 경영)
- 업종별 특성 고려 (금융업은 다른 기준)
"""
```

---

## 🔧 최종 점수 계산 공식

### 4개 영역별 최종 점수
```excel
재무: =MAX(0,MIN(5,2+SUM(G23,G25,G27,G28,G29)))
기술: =MAX(0,MIN(5,2+SUM(G31,G33,G34)))  
가격: =MAX(0,MIN(5,2+G36))
재료: =MAX(0,MIN(5,2+SUM(G39:G46)))
```

### 총점 계산
```excel
총점: =재무점수+기술점수+가격점수+재료점수
```

**Python 구현**:
```python
def calculate_final_score(financial_scores, technical_scores, price_score, material_scores):
    finance_score = max(0, min(5, 2 + sum(financial_scores)))
    technical_score = max(0, min(5, 2 + sum(technical_scores)))
    price_score_final = max(0, min(5, 2 + price_score))
    material_score = max(0, min(5, 2 + sum(material_scores)))
    
    return {
        "finance_score": finance_score,
        "technical_score": technical_score,
        "price_score": price_score_final,
        "material_score": material_score,
        "total_score": finance_score + technical_score + price_score_final + material_score
    }
```

---

## 📝 미확인 항목 체크리스트

### ✅ 확인 완료
- [x] 재무 영역: 매출액 VLOOKUP 공식
- [x] 재무 영역: 영업이익 VLOOKUP 공식
- [x] 재무 영역: 영업이익률 VLOOKUP 공식
- [x] 재무 영역: 유보율 VLOOKUP 공식
- [x] 재무 영역: 부채비율 VLOOKUP 공식 🎉 **재무 영역 100% 완성!**
- [x] 기술 영역: OBV VLOOKUP 공식
- [x] 기술 영역: 투자심리도 VLOOKUP 공식
- [x] 기술 영역: RSI VLOOKUP 공식 🎉 **기술 영역 100% 완성!**
- [x] 가격 영역: 52주 위치 VLOOKUP 공식 ✅ **새로 추가** 🎉 **가격 영역 100% 완성!**
- [x] 평가기준표 코드 매핑

### ❌ 확인 필요
- [ ] 재료 영역: 1개 항목 VLOOKUP 공식 (D009)

---

**📅 문서 생성일**: 2024-12-25  
**🔄 최종 업데이트**: 호재뉴스 도배 (D008) 공식 확인 완료 ⚠️📰  
**📊 완성도**: 재무 영역 100% (5/5), 기술 영역 100% (3/3), 가격 영역 100% (1/1), 재료 영역 100% (8/8), **전체 96% (17/18)** ⚠️

*이 문서는 모든 VLOOKUP 공식 확인 완료 시까지 지속적으로 업데이트됩니다.*