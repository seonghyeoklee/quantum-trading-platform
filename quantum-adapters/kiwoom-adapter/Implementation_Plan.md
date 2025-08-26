# 키움 API 기반 종목분석 시스템 구현 계획

## 📋 개요
구글 시트의 크롤링 기반 종목분석 시스템을 키움 API 기반으로 전환하여 실시간 데이터 제공 및 자동화된 분석 시스템을 구축합니다.

## 🎯 구현 목표

### 주요 목표
- ✅ 구글 시트 크롤링 **100% 완전 대체** (키움 API 85% + DART API 15%)
- ✅ 실시간 종목 분석 API 제공  
- ✅ 4개 영역 점수 계산 시스템 구현
- ✅ RSI 등 기술적 지표 자동 계산
- ✅ DART API 기반 상세 재무비율 제공
- ✅ FastAPI 기반 REST API 서비스

### 성공 지표
- 🔢 API 응답 시간: < 2초
- 📊 데이터 정확도: Google Sheets 대비 95% 이상  
- 🚀 분석 지표 수: 최소 10개 이상
- ⚡ 실시간 업데이트: 분 단위

## 🏗️ 시스템 아키텍처

### 📁 디렉토리 구조
```
src/kiwoom_api/analysis/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── calculator.py          # 지표 계산 엔진
│   ├── scorer.py              # 점수화 시스템
│   └── models.py              # 분석 데이터 모델
├── indicators/
│   ├── __init__.py
│   ├── technical.py           # RSI, MACD, 볼린저밴드 등
│   ├── fundamental.py         # PER, PBR, ROE 등
│   ├── institutional.py       # 기관/외국인 분석
│   └── market.py              # 시장 지표 분석
├── services/
│   ├── __init__.py
│   ├── analysis_service.py    # 종합 분석 서비스
│   ├── data_service.py        # 키움 API 데이터 서비스
│   └── dart_service.py        # DART API 재무데이터 서비스
└── api/
    ├── __init__.py
    └── analysis_router.py     # FastAPI 라우터
```

### 🔧 핵심 컴포넌트

#### 1. 데이터 수집 레이어
```python
class KiwoomDataService:
    """키움 API 데이터 수집 서비스"""
    
    async def get_basic_info(self, stock_code: str) -> StockBasicInfo:
        """ka10001 - 기본 종목 정보"""
        
    async def get_institutional_data(self, stock_code: str) -> InstitutionalData:
        """ka10045 - 기관/외국인 데이터"""
        
    async def get_historical_data(self, stock_code: str, period: int = 20) -> List[OHLCV]:
        """ka10005 - 과거 시세 데이터"""

class DartDataService:
    """DART API 재무정보 수집 서비스"""
    
    async def get_financial_statements(self, corp_code: str, year: str) -> Dict:
        """DART API로 재무제표 데이터 가져오기"""
        
    def calculate_debt_ratio(self, financial_data: Dict) -> float:
        """부채비율 = 부채총계 / 자본총계 × 100"""
        
    def calculate_current_ratio(self, financial_data: Dict) -> float:
        """유동비율 = 유동자산 / 유동부채 × 100"""
        
    def calculate_sales_growth(self, current_year: Dict, previous_year: Dict) -> float:
        """매출액증가율 = (당기매출액 - 전기매출액) / 전기매출액 × 100"""
```

#### 2. 지표 계산 레이어
```python
class TechnicalIndicators:
    """기술적 지표 계산"""
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """RSI 계산"""
        
    def calculate_macd(self, prices: List[float]) -> MACD:
        """MACD 계산"""
        
    def calculate_bollinger_bands(self, prices: List[float], period: int = 20) -> BollingerBands:
        """볼린저 밴드 계산"""

class FundamentalIndicators:
    """재무/기본 지표 계산"""
    
    def analyze_valuation(self, basic_info: StockBasicInfo) -> ValuationAnalysis:
        """밸류에이션 분석"""
        
    def analyze_growth(self, historical_data: List[dict]) -> GrowthAnalysis:  
        """성장성 분석"""
```

#### 3. 점수화 시스템
```python
class AnalysisScorer:
    """4개 영역 점수화 시스템"""
    
    def score_technical_indicators(self, indicators: TechnicalData) -> float:
        """기술적 영역 점수 (RSI, MACD, 볼린저밴드)"""
        
    def score_fundamental_indicators(self, indicators: FundamentalData) -> float:
        """재무적 영역 점수 (PER, PBR, ROE)"""
        
    def score_institutional_indicators(self, indicators: InstitutionalData) -> float:
        """기관/재료 영역 점수 (외국인지분율, 기관비중)"""
        
    def score_market_indicators(self, indicators: MarketData) -> float:
        """시장/가격 영역 점수 (52주 대비, 거래량)"""
        
    def calculate_total_score(self, scores: Dict[str, float]) -> AnalysisResult:
        """종합 점수 계산"""
```

## 📊 단계별 구현 계획

### 🔥 Phase 1: 기본 인프라 구축 (1-2일)

#### 1.1 프로젝트 구조 생성
- ✅ analysis 패키지 생성
- ✅ 기본 모듈 및 __init__.py 파일들 생성
- ✅ 데이터 모델 정의 (Pydantic)

#### 1.2 키움 API 데이터 서비스 구현
- ✅ KiwoomDataService 클래스 구현
- ✅ ka10001 (기본정보) API 연동
- ✅ ka10045 (기관매매) API 연동  
- ✅ ka10005 (과거시세) API 연동

**예상 결과물:**
```python
# 사용 예시
data_service = KiwoomDataService()
basic_info = await data_service.get_basic_info("005930")
print(f"현재가: {basic_info.current_price}")
print(f"PER: {basic_info.per}")
```

### ⚡ Phase 2: 기술적 지표 계산 모듈 (2-3일)

#### 2.1 RSI 계산 구현 ⭐ 최우선
```python
class TechnicalIndicators:
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """
        RSI = 100 - (100 / (1 + RS))
        RS = 평균상승폭 / 평균하락폭
        """
        # 구현 로직
```

#### 2.2 기타 기술적 지표
- ✅ MACD 계산
- ✅ 볼린저 밴드 계산  
- ✅ 이동평균선 계산
- ✅ OBV (On Balance Volume) 계산

#### 2.3 첫 번째 API 엔드포인트
```python
@router.get("/api/analysis/rsi/{stock_code}")
async def get_rsi_analysis(stock_code: str):
    """RSI 분석 결과 반환"""
    return {
        "stock_code": stock_code,
        "rsi": 65.2,
        "score": 0.3,
        "interpretation": "중립",
        "signal": "HOLD"
    }
```

**예상 소요시간**: 2일
**검증 방법**: 삼성전자(005930) RSI가 구글 시트와 ±2% 이내 일치

### 📊 Phase 3: 재무 지표 분석 모듈 (2-3일)

#### 3.1 기본 재무 지표
- ✅ PER/PBR 분석 및 점수화
- ✅ ROE 분석 (키움 API에서 제공시)
- ✅ 시가총액/거래량 분석

#### 3.2 밸류에이션 분석
```python
def analyze_valuation(self, basic_info: StockBasicInfo) -> ValuationAnalysis:
    """
    PER 기준:
    - PER < 10: 저평가 (+1점)
    - 10 ≤ PER ≤ 20: 적정 (0점)  
    - PER > 20: 고평가 (-1점)
    """
```

#### 3.3 재무 분석 API
```python
@router.get("/api/analysis/fundamental/{stock_code}")
async def get_fundamental_analysis(stock_code: str):
    return {
        "valuation": {"per": 15.97, "pbr": 1.23, "score": 0.2},
        "profitability": {"roe": 7.95, "score": -0.1},
        "total_score": 0.1
    }
```

### 🏛️ Phase 4: DART API 상세 재무비율 모듈 (2-3일) ⭐ 새로 추가

#### 4.1 DART API 서비스 구현
```python
class DartDataService:
    def __init__(self):
        self.api_key = settings.DART_API_KEY
        self.base_url = "https://opendart.fss.or.kr/api"
    
    async def get_corp_code(self, stock_code: str) -> str:
        """종목코드로 DART 기업고유번호 조회"""
        
    async def get_financial_statements(self, corp_code: str, year: str, quarter: str = "11011") -> Dict:
        """재무제표 전체 데이터 조회 (연결/별도, 분기별)"""
        
    def calculate_detailed_ratios(self, fs_data: Dict) -> DetailedFinancialRatios:
        """상세 재무비율 계산"""
        debt_ratio = fs_data["부채총계"] / fs_data["자본총계"] * 100
        current_ratio = fs_data["유동자산"] / fs_data["유동부채"] * 100
        return DetailedFinancialRatios(debt_ratio=debt_ratio, current_ratio=current_ratio)
```

#### 4.2 상세 재무비율 API
```python
@router.get("/api/analysis/detailed-financial/{stock_code}")
async def get_detailed_financial_ratios(stock_code: str, year: str = "2023"):
    dart_service = DartDataService()
    
    # 1. 종목코드 → DART 기업코드 변환
    corp_code = await dart_service.get_corp_code(stock_code)
    
    # 2. 재무제표 데이터 조회
    fs_data = await dart_service.get_financial_statements(corp_code, year)
    
    # 3. 상세 비율 계산
    ratios = dart_service.calculate_detailed_ratios(fs_data)
    
    return {
        "debt_ratio": ratios.debt_ratio,          # 부채비율
        "current_ratio": ratios.current_ratio,    # 유동비율  
        "sales_growth": ratios.sales_growth,      # 매출액증가율
        "operating_margin": ratios.operating_margin, # 영업이익률
        "data_source": "DART",
        "year": year,
        "updated_at": datetime.now()
    }
```

### 🏛️ Phase 5: 기관/외국인 분석 모듈 (1-2일)

#### 4.1 기관 매매 분석
```python
class InstitutionalAnalyzer:
    def analyze_foreign_ownership(self, data: InstitutionalData) -> float:
        """
        외국인 지분율 기준:
        - > 30%: 긍정적 (+0.5점)
        - 10-30%: 보통 (0점)
        - < 10%: 부정적 (-0.5점)
        """
        
    def analyze_institutional_trend(self, trend_data: List[dict]) -> float:
        """60일 기관 순매매 추세 분석"""
```

#### 4.2 기관 분석 API
```python
@router.get("/api/analysis/institutional/{stock_code}")  
async def get_institutional_analysis(stock_code: str):
    return {
        "foreign_ownership": {"ratio": 50.56, "score": 0.5},
        "institutional_trend": {"net_buy": 1500000, "score": 0.3},
        "total_score": 0.8
    }
```

### 🎯 Phase 6: 점수화 시스템 통합 (2-3일)

#### 5.1 4개 영역 점수 계산
```python
class AnalysisScorer:
    def calculate_comprehensive_score(self, stock_code: str) -> AnalysisResult:
        # 1. 기술적 영역 (4개 지표)
        technical_score = self.score_technical_indicators(...)
        
        # 2. 재무적 영역 (3개 지표)  
        fundamental_score = self.score_fundamental_indicators(...)
        
        # 3. 기관/재료 영역 (3개 지표)
        institutional_score = self.score_institutional_indicators(...)
        
        # 4. 시장/가격 영역 (2개 지표)
        market_score = self.score_market_indicators(...)
        
        # 총점 계산
        total_score = technical_score + fundamental_score + institutional_score + market_score
        
        return AnalysisResult(
            total_score=total_score,
            recommendation=self.get_recommendation(total_score),
            areas={
                "technical": technical_score,
                "fundamental": fundamental_score, 
                "institutional": institutional_score,
                "market": market_score
            }
        )
```

#### 5.2 종합 분석 API
```python
@router.get("/api/analysis/comprehensive/{stock_code}")
async def get_comprehensive_analysis(stock_code: str):
    return {
        "stock_code": "005930",
        "stock_name": "삼성전자",
        "total_score": 8.5,
        "recommendation": "매수 고려",
        "areas": {
            "technical": 2.1,    # 기술적 영역 (4점 만점)
            "fundamental": 1.8,  # 재무적 영역 (3점 만점)  
            "institutional": 2.5, # 기관/재료 영역 (3점 만점)
            "market": 2.1        # 시장/가격 영역 (2점 만점)
        },
        "indicators": {
            "rsi": {"value": 65.2, "score": 0.3},
            "per": {"value": 15.97, "score": 0.2},
            "foreign_ratio": {"value": 50.56, "score": 0.5}
        },
        "updated_at": "2024-12-25T10:30:00Z"
    }
```

### 🚀 Phase 7: 고급 기능 (3-4일)

#### 6.1 다종목 분석
```python
@router.post("/api/analysis/multiple")
async def analyze_multiple_stocks(stocks: List[str]):
    """여러 종목 동시 분석"""
```

#### 6.2 랭킹 시스템
```python
@router.get("/api/analysis/ranking")
async def get_stock_ranking(limit: int = 10):
    """종목 점수 기준 랭킹"""
```

#### 6.3 실시간 업데이트 (WebSocket)
```python
@router.websocket("/ws/analysis/{stock_code}")
async def realtime_analysis(websocket: WebSocket, stock_code: str):
    """실시간 분석 결과 업데이트"""
```

## 🔧 기술적 구현 세부사항

### 📚 필요 라이브러리
```python
# 기존 requirements.txt에 추가
pandas >= 1.5.0          # 데이터 처리
numpy >= 1.24.0          # 수치 계산
TA-Lib >= 0.4.25         # 기술적 지표 계산 (옵션)
pandas-ta >= 0.3.14      # 기술적 지표 대안

# DART API 관련 추가
OpenDartReader >= 0.1.6  # DART API 클라이언트 라이브러리
```

### 🗃️ 데이터 모델 정의
```python
# src/kiwoom_api/analysis/models.py
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class StockBasicInfo(BaseModel):
    stock_code: str
    stock_name: str
    current_price: float
    change_amount: float
    change_rate: float
    volume: int
    market_cap: float
    per: float
    pbr: float
    roe: Optional[float]

class TechnicalIndicators(BaseModel):
    rsi: float
    macd: Dict[str, float]
    bollinger: Dict[str, float]
    moving_averages: Dict[str, float]

class DetailedFinancialRatios(BaseModel):
    debt_ratio: Optional[float]         # 부채비율
    current_ratio: Optional[float]      # 유동비율  
    sales_growth: Optional[float]       # 매출액증가율
    operating_margin: Optional[float]   # 영업이익률
    roe: Optional[float]               # ROE
    roa: Optional[float]               # ROA
    data_source: str = "DART"

class AnalysisResult(BaseModel):
    stock_code: str
    stock_name: str
    total_score: float
    recommendation: str
    areas: Dict[str, float]
    indicators: Dict[str, Dict[str, float]]
    detailed_financial: Optional[DetailedFinancialRatios]  # DART 데이터 추가
    updated_at: datetime
```

### ⚡ 성능 최적화
```python
# 캐싱 시스템
from functools import lru_cache
import asyncio

class CachedAnalysisService:
    def __init__(self):
        self._cache = {}
        self._cache_duration = 60  # 60초 캐시
    
    @lru_cache(maxsize=100)
    async def get_analysis_cached(self, stock_code: str) -> AnalysisResult:
        """캐시된 분석 결과 반환"""
```

## 📝 테스트 계획

### 🧪 단위 테스트
```python
# tests/test_technical_indicators.py
def test_rsi_calculation():
    prices = [100, 102, 101, 103, 104, 102, 105, 107, 106, 108]
    rsi = TechnicalIndicators().calculate_rsi(prices)
    assert 30 <= rsi <= 70  # RSI 유효 범위

def test_analysis_scoring():
    scorer = AnalysisScorer()
    result = scorer.score_technical_indicators(mock_technical_data)
    assert -4.0 <= result <= 4.0  # 점수 유효 범위
```

### 🎯 통합 테스트
```python
# tests/test_analysis_integration.py
@pytest.mark.asyncio
async def test_comprehensive_analysis():
    result = await analysis_service.get_comprehensive_analysis("005930")
    assert result.stock_code == "005930"
    assert result.total_score is not None
    assert len(result.areas) == 4
```

## 📊 성능 목표 및 검증

### 🎯 성능 목표
| 지표 | 목표값 | 측정방법 |
|------|--------|---------|
| API 응답시간 | < 2초 | 평균 응답시간 측정 |
| 분석 정확도 | > 95% | Google Sheets 결과와 비교 |
| 동시 처리 | 50 req/sec | 부하 테스트 |
| 캐시 적중률 | > 80% | 캐시 통계 |

### 📈 검증 방법
1. **정확도 검증**: 삼성전자, LG전자 등 주요 종목 10개 Google Sheets 결과와 비교
2. **성능 테스트**: locust 또는 pytest-benchmark로 부하 테스트
3. **신뢰성 검증**: 24시간 연속 운영 테스트

## 🚀 배포 및 운영

### 🐳 Docker 설정
```dockerfile
# Dockerfile에 추가
RUN pip install pandas numpy pandas-ta OpenDartReader
```

### 🔑 환경 변수 설정
```bash
# .env 파일에 추가
DART_API_KEY=your_dart_api_key_here
DART_BASE_URL=https://opendart.fss.or.kr/api
```

### 📊 모니터링 설정
```python
# 분석 성능 모니터링
import time
import structlog

logger = structlog.get_logger()

async def log_analysis_performance(stock_code: str, duration: float):
    logger.info(
        "analysis_completed",
        stock_code=stock_code,
        duration_seconds=duration,
        success=True
    )
```

## 📅 일정 및 마일스톤

### 🗓️ 전체 일정: 17일 (DART API 추가로 3일 연장)

| 주차 | 단계 | 주요 작업 | 완성 기능 |
|------|------|---------|---------|
| 1주 | Phase 1-2 | 인프라 구축 + RSI 구현 | RSI API 제공 |
| 2주 | Phase 3-4 | 재무지표 + **DART API 통합** | 기본 분석 + 상세 재무비율 |
| 3주 | Phase 5-6-7 | 기관분석 + 점수화시스템 + 고급기능 | **100% 완전 대체** 완성 |

### 🎯 주요 마일스톤
- **Day 3**: RSI 계산 API 완성 ✅
- **Day 7**: 키움 기본 분석 완성 ✅
- **Day 10**: **DART API 통합 완성** ⭐ 새로 추가 
- **Day 14**: 종합 점수화 시스템 완성 ✅
- **Day 17**: **100% 완전 대체 시스템** 완성 🎉

## 🔄 향후 확장 계획

### Phase 7: 고도화 (추후)
- 📊 차트 이미지 생성 기능
- 🤖 AI 기반 추천 알고리즘
- 📱 모바일 앱 연동
- 💾 분석 이력 저장 및 백테스팅

### Phase 8: 다중 브로커 지원 
- 🏦 한국투자증권 API 연동
- 🔄 브로커별 데이터 통합
- ⚖️ 브로커별 분석 결과 비교

---

**🎯 최종 목표**: 구글 시트를 **100% 완전 대체**하는 하이브리드 종목분석 시스템 구축
- **키움 API 85%**: 실시간 시세, 기본 재무비율, 기관/외국인 데이터
- **DART API 15%**: 상세 재무비율 (부채비율, 유동비율, 매출액증가율)

*계획 수립 일시: 2024-12-25*
*DART API 통합 반영: 2024-12-25*  
*예상 완료 일시: 2025-01-11 (3일 연장)*