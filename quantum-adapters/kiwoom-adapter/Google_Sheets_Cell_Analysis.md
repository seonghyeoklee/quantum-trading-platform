# 구글 시트 A19:G48 표 구조 및 계산식 분석

## 📊 개요
구글 시트 종목분석 시스템의 A19:G48 범위 표에서 실제 점수 계산 공식과 구조를 상세 분석하여 Python 구현의 정확한 스펙을 도출합니다.

## 🎯 분석 목표
- 각 셀의 계산 공식 파악
- 4개 영역별 실제 점수 범위 확인
- 총점 계산 로직 역추적
- 가중치 및 점수화 알고리즘 분석

## 📋 A19:G48 표 구조 분석 (실제 확인 완료)

### 🎯 **실제 표 구조** (두산에너빌리티 034020 기준)

#### **총점 시스템**
```
평가점수    총점  재무  기술  가격  재료
           7     0     4     0     3
```
**✅ 핵심 발견**: 총 7점 = 재무 0점 + 기술 4점 + 가격 0점 + 재료 3점

#### **1. 재무 영역 (0점)**
| 항목 | 기준연도 | 값 | 판단 | 점수 |
|------|---------|-----|------|------|
| 매출액 | 2023: 175,899<br>2024: 162,331 | - | 전년 대비 매출 감소 | **-1** |
| 영업이익 | 2023: 14,673<br>2024: 10,176 | - | 해당없음 | **0** |  
| 영업이익률 | 2024 | 6.27 | 해당없음 | **0** |
| 유보율 | 2024 | 90.79 | 유보율 300% 이하 | **-1** |
| 부채비율 | 2024 | 125.66 | 해당없음 | **0** |

**재무 영역 총점**: -1 + 0 + 0 + (-1) + 0 = **-2점** → 최종 표시 **0점**

#### **2. 기술 영역 (4점)**
| 항목 | 기간 | 값 | 판단 | 점수 |
|------|------|-----|------|------|
| OBV | 2년 | Y | OBV만족 | **1** |
| RSI | 현재 | 40 | 해당없음 | **0** |
| 투자심리도 | 현재 | 10 | 투자심리도침체 (25%이하) | **1** |

**❓ 의문점**: 기술 영역 계산값은 1+0+1=2점인데 최종 표시는 **4점**
→ **다른 숨겨진 기술 지표가 있거나 가중치가 적용된 것으로 추정**

#### **3. 가격 영역 (0점)**  
| 최고가 | 최저가 | 현재가 | 판단 | 점수 |
|--------|--------|--------|------|------|
| 69,400 | 13,420 | 65,900 | 고점대비: 해당없음<br>저점대비: +300% 이상 | **-3** |

**❓ 의문점**: 가격 영역 계산값은 -3점인데 최종 표시는 **0점**
→ **음수 점수가 0점으로 처리되는 로직 추정**

#### **4. 재료 영역 (3점)**
| 평가항목 | 해당여부 | 점수 |
|----------|----------|------|
| 배당률(2%이상) | N | **0** |
| 어닝서프라이즈 | N | **0** |
| 기관순매매량 (60일) | N (0.0%, -16,366,218) | **0** |
| 외인순매매량 (60일) | N (-2.6%) | **0** |
| 불성실공시 | N | **0** |
| 악재뉴스 | N | **0** |
| 구체화된 이벤트/호재 | N | **0** |
| 확실한 주도 테마 | Y | **1** |
| 호재뉴스 도배 | N | **0** |
| 이자보상배율(1 미만) | N (3.10) | **0** |

**❓ 의문점**: 재료 영역 계산값은 1점인데 최종 표시는 **3점**
→ **숨겨진 재료 지표가 있거나 가중치 시스템 존재**

## 🔍 **핵심 분석 결과**

### ⚠️ **중요 발견사항**
1. **표시된 총점과 개별 계산값이 일치하지 않음**
2. **음수 점수의 처리 로직 존재** (가격 영역: -3점 → 0점)
3. **숨겨진 지표나 가중치 시스템 존재** (기술 2점 → 4점, 재료 1점 → 3점)
4. **영역별 최소값 제한** (0점 이하는 0점으로 표시)

### 📊 **점수화 로직 추론**

#### **1. 재무 영역 로직**
```python
def calculate_finance_score(revenue_growth, operating_profit, operating_margin, retention_rate, debt_ratio):
    score = 0
    
    # 매출액 증감 (-1 ~ +1)
    if revenue_growth < 0:
        score += -1
    elif revenue_growth > 0.1:  # 10% 이상 증가
        score += 1
    
    # 영업이익 관련 로직 (상세 기준 불명)
    
    # 유보율 (300% 기준)
    if retention_rate < 300:
        score += -1
    elif retention_rate > 500:  # 추정
        score += 1
    
    # 부채비율 관련 로직 (상세 기준 불명)
    
    return max(0, score)  # 음수는 0으로 처리
```

#### **2. 기술 영역 로직** 
```python
def calculate_technical_score(obv_satisfied, rsi, investor_sentiment):
    score = 0
    
    # OBV 만족 여부
    if obv_satisfied:
        score += 1
    
    # RSI (30-70 기준 추정)
    if rsi <= 30:
        score += 1
    elif rsi >= 70:
        score += -1
    
    # 투자심리도 (25% 이하)
    if investor_sentiment <= 25:
        score += 1
    
    # 숨겨진 기술 지표들 (MACD, 볼린저밴드 등) 추정
    # hidden_score = calculate_hidden_technical_indicators()
    # score += hidden_score
    
    return max(0, score * 2)  # 가중치 2배 적용 추정
```

#### **3. 가격 영역 로직**
```python
def calculate_price_score(high_price, low_price, current_price):
    score = 0
    
    # 고점 대비 위치
    high_ratio = (current_price / high_price - 1) * 100
    
    # 저점 대비 위치  
    low_ratio = (current_price / low_price - 1) * 100
    
    # 저점 대비 300% 이상 상승 시 과열 판단
    if low_ratio > 300:
        score += -3
    elif low_ratio > 100:
        score += -1
    elif low_ratio < 50:
        score += 1
    
    return max(0, score)  # 음수는 0으로 처리
```

#### **4. 재료 영역 로직**
```python  
def calculate_material_score(dividend_yield, earnings_surprise, institutional_buy, 
                           foreign_buy, disclosure_issues, negative_news, 
                           positive_events, theme_stock, news_coverage, 
                           interest_coverage):
    score = 0
    
    # 각 재료별 점수 (+1 또는 0)
    if dividend_yield >= 2.0:
        score += 1
    if earnings_surprise:
        score += 1
    if institutional_buy:
        score += 1
    if foreign_buy:
        score += 1
    if not disclosure_issues:
        score += 0  # 불성실공시 없음
    if not negative_news:
        score += 0  # 악재뉴스 없음
    if positive_events:
        score += 1
    if theme_stock:
        score += 1  # 확실한 주도 테마
    if news_coverage:
        score += 1
    if interest_coverage < 1.0:
        score += -1
    
    # 숨겨진 재료 지표들 추정 (추가 +2점 어디서 왔는지)
    # hidden_material_score = calculate_hidden_material_factors()
    # score += hidden_material_score
    
    return max(0, score)
```

## 🎯 **정확한 점수 계산 공식 확인!** ✅

### 📊 **실제 구글 시트 공식**
```javascript
재무: =MAX(0,MIN(5,2+SUM(G23,G25,G27,G28,G29)))
기술: =MAX(0,MIN(5,2+SUM(G31,G33,G34)))  
가격: =MAX(0,MIN(5,2+G36))
재료: =MAX(0,MIN(5,2+SUM(G39:G46)))
```

### 🧮 **공식 해석**
모든 영역이 동일한 패턴: **MAX(0, MIN(5, 2 + 개별점수합계))**

**구성 요소:**
- **기본점수 2점**: 모든 영역에서 시작점
- **개별지표 점수**: 각 지표별 계산된 점수 합계
- **MIN(5, ...)**: 최대 5점 제한
- **MAX(0, ...)**: 최소 0점 제한

### ✅ **두산에너빌리티 검증**

#### **1. 재무 영역 (0점)**
```
계산: MAX(0, MIN(5, 2 + SUM(G23,G25,G27,G28,G29)))
G23 (매출액): -1
G25 (영업이익): 0  
G27 (영업이익률): 0
G28 (유보율): -1
G29 (부채비율): 0

= MAX(0, MIN(5, 2 + (-1+0+0+(-1)+0)))
= MAX(0, MIN(5, 2 + (-2)))  
= MAX(0, MIN(5, 0))
= MAX(0, 0)
= 0점 ✅
```

#### **2. 기술 영역 (4점)**
```
계산: MAX(0, MIN(5, 2 + SUM(G31,G33,G34)))
G31 (OBV): 1
G33 (RSI): 0
G34 (투자심리도): 1

= MAX(0, MIN(5, 2 + (1+0+1)))
= MAX(0, MIN(5, 2 + 2))
= MAX(0, MIN(5, 4))
= MAX(0, 4)
= 4점 ✅
```

#### **3. 가격 영역 (0점)**
```
계산: MAX(0, MIN(5, 2 + G36))
G36 (가격분석): -3

= MAX(0, MIN(5, 2 + (-3)))
= MAX(0, MIN(5, -1))
= MAX(0, -1)
= 0점 ✅
```

#### **4. 재료 영역 (3점)**
```
계산: MAX(0, MIN(5, 2 + SUM(G39:G46)))
G39~G46 중 확실한주도테마(G45): 1
나머지: 0

= MAX(0, MIN(5, 2 + 1))
= MAX(0, MIN(5, 3))
= MAX(0, 3)  
= 3점 ✅
```

### 🎯 **완벽한 공식 발견!**

**핵심 원리:**
1. **기본 2점 시작**: 모든 영역이 2점에서 시작
2. **개별 지표 가감**: 각 지표별 점수를 더하거나 뺌
3. **0-5점 범위**: 최소 0점, 최대 5점으로 제한
4. **총점 = 재무 + 기술 + 가격 + 재료**: 0점 + 4점 + 0점 + 3점 = 7점

## 🐍 **Python 구현 코드**

### 정확한 점수 계산 함수
```python
def calculate_google_sheets_score(financial_scores, technical_scores, price_score, material_scores):
    """
    구글 시트와 동일한 점수 계산 공식
    
    Args:
        financial_scores: [매출액점수, 영업이익점수, 영업이익률점수, 유보율점수, 부채비율점수]
        technical_scores: [OBV점수, RSI점수, 투자심리도점수]  
        price_score: 가격분석점수 (단일값)
        material_scores: [배당률점수, 어닝서프라이즈점수, ...] (8개 항목)
    
    Returns:
        Dict with area scores and total
    """
    # 각 영역별 점수 계산: MAX(0, MIN(5, 2 + 개별점수합))
    finance_score = max(0, min(5, 2 + sum(financial_scores)))
    technical_score = max(0, min(5, 2 + sum(technical_scores)))  
    price_score_final = max(0, min(5, 2 + price_score))
    material_score = max(0, min(5, 2 + sum(material_scores)))
    
    total_score = finance_score + technical_score + price_score_final + material_score
    
    return {
        "total": total_score,
        "finance": finance_score,
        "technical": technical_score,
        "price": price_score_final,
        "material": material_score,
        "max_possible": 20  # 각 영역 최대 5점 × 4영역
    }

# 두산에너빌리티 검증
def test_doosan_calculation():
    financial = [-1, 0, 0, -1, 0]  # 매출액감소(-1) + 유보율문제(-1)
    technical = [1, 0, 1]           # OBV만족(1) + 투자심리도침체(1)
    price = -3                      # 저점대비 300%이상 상승 과열
    material = [0, 0, 0, 0, 0, 0, 0, 1, 0, 0]  # 확실한주도테마(1)만 해당
    
    result = calculate_google_sheets_score(financial, technical, price, material)
    
    print(f"총점: {result['total']}점")  # 7점
    print(f"재무: {result['finance']}점")  # 0점  
    print(f"기술: {result['technical']}점")  # 4점
    print(f"가격: {result['price']}점")  # 0점
    print(f"재료: {result['material']}점")  # 3점
    
    return result

# 검증 실행
test_result = test_doosan_calculation()
# 출력: 총점: 7점, 재무: 0점, 기술: 4점, 가격: 0점, 재료: 3점 ✅
```

### 개별 지표 점수화 함수 예시
```python
def calculate_financial_indicators(revenue_2023, revenue_2024, operating_profit_2023, 
                                 operating_profit_2024, operating_margin, retention_rate, debt_ratio):
    """재무 지표별 점수 계산"""
    scores = []
    
    # 매출액 증감률
    revenue_growth = (revenue_2024 - revenue_2023) / revenue_2023
    if revenue_growth < 0:
        scores.append(-1)  # 매출 감소
    elif revenue_growth > 0.1:  # 10% 이상 증가
        scores.append(1)
    else:
        scores.append(0)
    
    # 영업이익 관련 (구체적 기준 필요)
    scores.append(0)  # 임시
    
    # 영업이익률 (구체적 기준 필요)  
    scores.append(0)  # 임시
    
    # 유보율 (300% 기준)
    if retention_rate < 300:
        scores.append(-1)
    elif retention_rate > 500:  # 추정 기준
        scores.append(1)
    else:
        scores.append(0)
        
    # 부채비율 (구체적 기준 필요)
    scores.append(0)  # 임시
    
    return scores

def calculate_technical_indicators(obv_satisfied, rsi, investor_sentiment):
    """기술 지표별 점수 계산"""
    scores = []
    
    # OBV 만족 여부
    scores.append(1 if obv_satisfied else 0)
    
    # RSI (30-70 기준)
    if rsi <= 30:
        scores.append(1)  # 과매도
    elif rsi >= 70:
        scores.append(-1)  # 과매수
    else:
        scores.append(0)  # 중립
        
    # 투자심리도 (25% 이하 침체)
    if investor_sentiment <= 25:
        scores.append(1)  # 침체시 매수기회
    else:
        scores.append(0)
        
    return scores

def calculate_price_score(high_52w, low_52w, current_price):
    """가격 분석 점수 계산"""
    # 저점 대비 상승률
    low_ratio = (current_price / low_52w - 1) * 100
    
    if low_ratio > 300:
        return -3  # 과열 위험
    elif low_ratio > 100:
        return -1  # 주의
    elif low_ratio < 50:
        return 1   # 매수 기회
    else:
        return 0   # 중립

def calculate_material_scores(dividend_yield, earnings_surprise, institutional_buy_60d,
                            foreign_buy_60d, disclosure_issues, negative_news, 
                            positive_events, theme_stock, news_coverage, interest_coverage):
    """재료 분석 점수 계산 (10개 항목)"""
    scores = []
    
    scores.append(1 if dividend_yield >= 2.0 else 0)  # 배당률 2% 이상
    scores.append(1 if earnings_surprise else 0)      # 어닝서프라이즈
    scores.append(1 if institutional_buy_60d else 0)  # 60일 기관순매수
    scores.append(1 if foreign_buy_60d else 0)        # 60일 외인순매수  
    scores.append(0 if disclosure_issues else 0)      # 불성실공시 (없어야 0점)
    scores.append(0 if negative_news else 0)          # 악재뉴스 (없어야 0점)
    scores.append(1 if positive_events else 0)        # 구체화된 이벤트/호재
    scores.append(1 if theme_stock else 0)            # 확실한 주도 테마
    scores.append(1 if news_coverage else 0)          # 호재뉴스 도배
    scores.append(-1 if interest_coverage < 1.0 else 0)  # 이자보상배율 1 미만
    
    return scores
```

## 🔍 분석 단계

### 1단계: 구글 시트 접근 및 구조 파악
- [ ] 구글 시트 URL 확인 및 접근
- [ ] A19:G48 범위의 실제 데이터 확인
- [ ] 헤더 구조 및 열별 의미 파악

### 2단계: 계산 공식 분석
- [ ] 각 셀의 실제 공식 확인
- [ ] 참조하는 데이터 소스 파악 (A1:K17 등)
- [ ] 조건부 계산 로직 분석

### 3단계: 점수화 시스템 분석
- [ ] 각 지표별 점수 산출 방식
- [ ] -1~+1 점수 범위 확인
- [ ] 영역별 가중치 시스템

### 4단계: 총점 계산 로직
- [ ] 4개 영역 점수 합산 방식
- [ ] 최종 추천 신호 생성 로직

## 📊 예상 영역별 구조

### 재무 영역 (예상 행: A19:G25)
- PER (Price Earnings Ratio)
- PBR (Price Book Ratio) 
- ROE (Return on Equity)
- 부채비율
- 유보율

### 기술 영역 (예상 행: A26:G33)
- RSI (Relative Strength Index)
- OBV (On Balance Volume)
- 투자심리도
- 이동평균선

### 가격 영역 (예상 행: A34:G38)
- 최고가 대비
- 최저가 대비

### 재료 영역 (예상 행: A39:G48)
- 배당률
- 외국인 보유율
- 기관 순매매
- 거래량
- 이자보상배율

## 🔧 분석 방법

### 구글 시트 접근 방식
1. **직접 접근**: 구글 시트 URL을 통한 웹 인터페이스
2. **API 접근**: Google Sheets API를 통한 데이터 추출
3. **크롤링**: 웹 스크래핑을 통한 계산식 분석

### 분석할 정보
- **공식 (Formula)**: 각 셀의 실제 계산 공식
- **참조 (Reference)**: 다른 셀 참조 관계
- **조건 (Condition)**: IF, SWITCH 등 조건부 로직
- **함수 (Function)**: 사용된 구글 시트 함수들

## 📈 예상 발견 내용

### 점수 계산 공식 예시
```javascript
// RSI 점수화 예상 공식
=IF(C21<=30, 1, IF(C21>=70, -1, (50-C21)/20))

// PER 점수화 예상 공식  
=IF(C20<10, 1, IF(C20>20, -1, (15-C20)/10))
```

### 영역별 가중치 예상
```javascript
// 총점 계산 예상 공식
=SUM(F20:F25) + SUM(F26:F33) + SUM(F34:F38) + SUM(F39:F48)
```

## 🎯 분석 결과 활용

### Python 구현을 위한 스펙
1. **정확한 계산 공식**: 각 지표별 점수화 알고리즘
2. **조건부 로직**: IF/SWITCH 조건의 Python 변환
3. **참조 관계**: 데이터 소스와 계산 흐름
4. **가중치 시스템**: 영역별/지표별 가중치

### 검증 방법
1. **삼성전자 테스트**: 005930 종목으로 계산 결과 비교
2. **다종목 검증**: 여러 종목의 점수 일치 확인
3. **극값 테스트**: 최고/최저 점수 케이스 검증

---

## 📝 다음 단계
1. 구글 시트 A19:G48 범위 실제 확인
2. 각 셀 공식 상세 분석
3. Python 구현 스펙 작성
4. 검증 테스트 케이스 구성

*분석 시작일: 2024-12-25*
*예상 완료일: 2024-12-26*