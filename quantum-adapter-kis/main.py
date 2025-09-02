from fastapi import FastAPI, HTTPException, Query, Header, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import sys
import os
import logging

# 경로 설정 - examples_user 폴더 접근을 위해
sys.path.append(os.path.join(os.path.dirname(__file__), 'examples_user'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'examples_user', 'domestic_stock'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'examples_user', 'overseas_stock'))

# KIS 모듈 import
try:
    import kis_auth as ka
    # 국내 주식 함수들
    from domestic_stock_functions import (
        inquire_daily_itemchartprice, inquire_time_itemchartprice, inquire_price, 
        inquire_asking_price_exp_ccn, search_stock_info, search_info, inquire_index_price,
        inquire_daily_indexchartprice, inquire_time_indexchartprice
    )
    # 해외 주식 함수들 (이름 충돌 방지를 위해 별칭 사용)
    from overseas_stock_functions import (
        inquire_daily_chartprice as overseas_daily_chart,
        inquire_time_itemchartprice as overseas_minute_chart,
        price as overseas_price,
        search_info as overseas_search_info,
        inquire_search as overseas_inquire_search,
        inquire_time_indexchartprice as overseas_index_minute_chart
    )
    KIS_MODULE_AVAILABLE = True
    OVERSEAS_MODULE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"KIS 모듈을 불러올 수 없습니다: {e}")
    KIS_MODULE_AVAILABLE = False
    OVERSEAS_MODULE_AVAILABLE = False

app = FastAPI(
    title="Quantum KIS Adapter",
    description="""
    ## 🚀 Korea Investment & Securities API Adapter for Quantum Trading Platform
    
    한국투자증권(KIS) Open API를 활용한 주식 거래 데이터 제공 서비스입니다.
    
    ### ✨ 주요 기능
    - **국내 주식**: 현재가, 차트, 호가정보, 종목정보
    - **해외 주식**: 현재가, 차트 (미국, 홍콩, 중국, 일본 등)
    - **시장 지수**: 코스피, 코스닥, 코스피200
    - **실시간 데이터**: WebSocket 연결 (향후 구현 예정)
    
    ### 🔐 인증
    - **헤더 인증**: `X-KIS-Token` 헤더로 토큰 전달
    - **파일 인증**: kis_devlp.yaml 설정 파일 사용 (개발/테스트용)
    
    ### 📊 데이터 포맷
    모든 API는 일관된 응답 형식을 사용합니다:
    ```json
    {
      "success": true,
      "data": {...},
      "message": "조회 성공",
      "timestamp": "2024-12-31T12:34:56"
    }
    ```
    """,
    version="1.0.0",
    contact={
        "name": "Quantum Trading Platform",
        "url": "https://github.com/your-repo/quantum-trading-platform",
        "email": "dev@quantum-trading.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
)

# CORS 설정 - Spring Boot 연동을 위해
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:3000"],  # Spring Boot, Next.js
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "Quantum KIS Adapter API",
        "status": "running",
        "endpoints": {
            "domestic_daily_chart": "/domestic/chart/daily/{symbol}",
            "domestic_minute_chart": "/domestic/chart/minute/{symbol}",
            "domestic_current_price": "/domestic/price/{symbol}",
            "domestic_orderbook": "/domestic/orderbook/{symbol}",
            "domestic_stock_info": "/domestic/info/{symbol}",
            "domestic_search": "/domestic/search",
            "domestic_indices": "/indices/domestic",
            "overseas_daily_chart": "/overseas/{exchange}/chart/daily/{symbol}",
            "overseas_minute_chart": "/overseas/{exchange}/chart/minute/{symbol}",
            "overseas_current_price": "/overseas/{exchange}/price/{symbol}",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "kis-adapter"}


# Pydantic 모델 정의
class ApiResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str
    timestamp: str

# 인증 확인 함수
def check_auth():
    if not KIS_MODULE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="KIS 모듈을 사용할 수 없습니다. 설정을 확인해주세요."
        )
    return True

# 차트 데이터 조회 엔드포인트
# === 국내 주식 API ===
@app.get("/domestic/chart/daily/{symbol}", 
         tags=["국내 주식 차트"],
         summary="일봉/주봉/월봉 차트 조회",
         description="""
         국내 주식의 일봉, 주봉, 월봉 차트 데이터를 조회합니다.
         
         **반환 데이터:**
         - OHLC (시가, 고가, 저가, 종가)
         - 거래량, 거래대금
         - 최대 100건까지 조회 가능
         
         **예시:** `GET /domestic/chart/daily/005930?period=D&start_date=20241201&end_date=20241231`
         """)
async def get_domestic_daily_chart(
    symbol: str = Path(..., description="종목코드 (예: 005930)", example="005930"),
    period: str = Query("D", description="차트 주기", example="D", regex="^[DWM]$"),
    start_date: Optional[str] = Query(None, description="시작일 (YYYYMMDD)", example="20241201"),
    end_date: Optional[str] = Query(None, description="종료일 (YYYYMMDD)", example="20241231"),
    count: int = Query(100, description="조회 건수 (최대 100)", example=30, le=100),
    x_kis_token: Optional[str] = Header(None, alias="X-KIS-Token", description="KIS API 액세스 토큰")
):
    check_auth()
    
    try:
        # 헤더에서 받은 토큰으로 KIS 인증
        if x_kis_token:
            ka.set_external_token(x_kis_token)
        ka.auth()
        
        # KIS API 호출 - 기본값 설정
        from datetime import datetime, timedelta
        today = datetime.now().strftime("%Y%m%d")
        default_start = (datetime.now() - timedelta(days=100)).strftime("%Y%m%d")
        
        result = inquire_daily_itemchartprice(
            env_dv="real",
            fid_cond_mrkt_div_code="J", 
            fid_input_iscd=symbol,
            fid_input_date_1=start_date or default_start,
            fid_input_date_2=end_date or today,
            fid_period_div_code=period,
            fid_org_adj_prc="0"
        )
        
        # 튜플인 경우 첫 번째 DataFrame 사용, DataFrame을 dictionary로 변환
        if isinstance(result, tuple):
            result = result[0]  # 첫 번째 DataFrame 사용
        data = result.to_dict('records') if hasattr(result, 'to_dict') else result
        
        return ApiResponse(
            success=True,
            data={"records": data} if isinstance(data, list) else data,
            message=f"차트 데이터 조회 성공: {symbol}",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logging.error(f"차트 데이터 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"차트 데이터 조회 실패: {str(e)}"
        )

@app.get("/domestic/chart/minute/{symbol}")
async def get_domestic_minute_chart(
    symbol: str,
    time_div: str = Query("1", description="분봉 단위 (1/3/5/10/15/30/60)"),
    start_time: Optional[str] = Query(None, description="시작시간 (HHMMSS)"),
    end_time: Optional[str] = Query(None, description="종료시간 (HHMMSS)"),
    x_kis_token: Optional[str] = Header(None, alias="X-KIS-Token")
):
    """국내 분봉 차트 데이터 조회"""
    check_auth()
    
    try:
        # 헤더에서 받은 토큰으로 KIS 인증
        if x_kis_token:
            ka.set_external_token(x_kis_token)
        ka.auth()
        
        # KIS API 호출
        result = inquire_time_itemchartprice(
            env_dv="real",
            fid_cond_mrkt_div_code="J",
            fid_input_iscd=symbol,
            fid_input_hour_1=start_time or "090000",
            fid_pw_data_incu_yn="Y",
            fid_etc_cls_code=""
        )
        
        # 튜플인 경우 첫 번째 DataFrame 사용, DataFrame을 dictionary로 변환
        if isinstance(result, tuple):
            result = result[0]  # 첫 번째 DataFrame 사용
        data = result.to_dict('records') if hasattr(result, 'to_dict') else result
        
        return ApiResponse(
            success=True,
            data={"records": data} if isinstance(data, list) else data,
            message=f"분봉 데이터 조회 성공: {symbol}",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logging.error(f"분봉 데이터 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"분봉 데이터 조회 실패: {str(e)}"
        )

@app.get("/domestic/price/{symbol}",
         tags=["국내 주식 시세"],
         summary="현재가 조회", 
         description="""
         국내 주식의 실시간 현재가 정보를 조회합니다.
         
         **반환 데이터:**
         - 현재가, 전일대비, 등락률
         - 시가, 고가, 저가, 상한가, 하한가
         - 거래량, 거래대금
         - PER, PBR, EPS, BPS
         - 52주 고가/저가, 외국인 보유율
         
         **예시:** `GET /domestic/price/005930`
         """)
async def get_domestic_current_price(
    symbol: str = Path(..., description="종목코드", example="005930"),
    market: str = Query("J", description="시장구분", example="J"),
    x_kis_token: Optional[str] = Header(None, alias="X-KIS-Token", description="KIS API 액세스 토큰")
):
    check_auth()
    
    try:
        # 헤더에서 받은 토큰으로 KIS 인증
        if x_kis_token:
            ka.set_external_token(x_kis_token)
        ka.auth()
        
        # KIS API 호출
        result = inquire_price(
            env_dv="real", 
            fid_cond_mrkt_div_code=market,
            fid_input_iscd=symbol
        )
        
        # DataFrame을 dictionary로 변환
        data = result.to_dict('records') if hasattr(result, 'to_dict') else result
        
        return ApiResponse(
            success=True,
            data={"records": data} if isinstance(data, list) else data,
            message=f"현재가 조회 성공: {symbol}",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logging.error(f"현재가 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"현재가 조회 실패: {str(e)}"
        )

@app.get("/domestic/orderbook/{symbol}",
         tags=["국내 주식 시세"],
         summary="호가정보 조회",
         description="""
         국내 주식의 실시간 호가(매수/매도) 정보를 조회합니다.
         
         **반환 데이터:**
         - 매수/매도 10단계 호가와 잔량
         - 총 매수/매도 잔량 및 건수
         - 현재가 대비 호가 비교 정보
         - 시간외 호가 정보 (장외 시간 시)
         
         **활용 예시:**
         - 실시간 주문 체결 현황 모니터링
         - 매매 타이밍 분석
         - 유동성 및 거래심리 파악
         
         **예시:** `GET /domestic/orderbook/005930?market=J`
         """)
async def get_domestic_orderbook(
    symbol: str = Path(..., description="종목코드 (예: 005930)", example="005930"),
    market: str = Query("J", description="시장구분", example="J", regex="^(J|NX|UN)$"),
    x_kis_token: Optional[str] = Header(None, alias="X-KIS-Token", description="KIS API 인증 토큰 (선택사항)")
):
    check_auth()
    
    try:
        # 헤더에서 받은 토큰으로 KIS 인증
        if x_kis_token:
            ka.set_external_token(x_kis_token)
        ka.auth()
        
        # KIS API 호출
        orderbook_data, expected_data = inquire_asking_price_exp_ccn(
            env_dv="real",
            fid_cond_mrkt_div_code=market,
            fid_input_iscd=symbol
        )
        
        # DataFrame을 dictionary로 변환
        orderbook_records = orderbook_data.to_dict('records') if hasattr(orderbook_data, 'to_dict') else []
        expected_records = expected_data.to_dict('records') if hasattr(expected_data, 'to_dict') else []
        
        return ApiResponse(
            success=True,
            data={
                "orderbook": orderbook_records,
                "expected_execution": expected_records
            },
            message=f"호가정보 조회 성공: {symbol}",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logging.error(f"호가정보 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"호가정보 조회 실패: {str(e)}"
        )

@app.get("/domestic/info/{symbol}",
         tags=["국내 주식 기본정보"],
         summary="종목 기본정보 조회",
         description="""
         국내 종목의 기본 정보를 조회합니다.
         
         **반환 데이터:**
         - 종목명, 종목코드, 시장구분
         - 업종분류, 상장주식수, 액면가
         - 자본금, 시가총액, 발행주식수
         - 외국인 한도, 대주주 정보
         - 결산월, 공시구분 등 기업정보
         
         **활용 예시:**
         - 종목 스크리닝 및 기본 분석
         - 투자 대상 기업 정보 파악
         - 포트폴리오 구성 시 기업 기초 데이터 수집
         
         **지원 상품:**
         - 300: 주식/ETF/ETN/ELW (기본값)
         - 301: 선물옵션
         - 302: 채권
         - 306: ELS
         
         **예시:** `GET /domestic/info/005930?product_type=300`
         """)
async def get_domestic_stock_info(
    symbol: str = Path(..., description="종목코드 (예: 005930)", example="005930"),
    product_type: str = Query("300", description="상품유형코드", example="300", regex="^(300|301|302|306)$"),
    x_kis_token: Optional[str] = Header(None, alias="X-KIS-Token", description="KIS API 인증 토큰 (선택사항)")
):
    check_auth()
    
    try:
        # 헤더에서 받은 토큰으로 KIS 인증
        if x_kis_token:
            ka.set_external_token(x_kis_token)
        ka.auth()
        
        # KIS API 호출
        result = search_stock_info(
            prdt_type_cd=product_type,
            pdno=symbol
        )
        
        # DataFrame을 dictionary로 변환
        data = result.to_dict('records') if hasattr(result, 'to_dict') else []
        
        return ApiResponse(
            success=True,
            data={"records": data} if isinstance(data, list) else data,
            message=f"종목정보 조회 성공: {symbol}",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logging.error(f"종목정보 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"종목정보 조회 실패: {str(e)}"
        )

@app.get("/domestic/search",
         tags=["국내 주식 기본정보"],
         summary="종목 검색",
         description="""
         종목코드 또는 심볼을 기반으로 종목 정보를 검색합니다.
         
         **검색 방식:**
         - 종목코드로 검색 (예: 005930)
         - 심볼명으로 검색 (부분 일치)
         - 다중 상품 유형 지원
         
         **반환 데이터:**
         - 종목명, 종목코드, 심볼
         - 시장구분, 상품구분
         - 매칭된 종목들의 기본 정보
         
         **활용 예시:**
         - 종목코드 확인 및 검증
         - 유사 종목명 검색
         - 다양한 금융상품 통합 검색
         
         **지원 상품:**
         - 300: 주식/ETF/ETN/ELW (기본값)
         - 301: 선물옵션
         - 302: 채권
         - 306: ELS
         - 512: 해외주식
         
         **예시:** `GET /domestic/search?symbol=삼성전자&product_type=300`
         """)
async def search_domestic_stock(
    symbol: str = Query(..., description="검색할 종목코드 또는 심볼", example="005930"),
    product_type: str = Query("300", description="상품유형코드", example="300", regex="^(300|301|302|306|512)$"),
    x_kis_token: Optional[str] = Header(None, alias="X-KIS-Token", description="KIS API 인증 토큰 (선택사항)")
):
    check_auth()
    
    try:
        # 헤더에서 받은 토큰으로 KIS 인증
        if x_kis_token:
            ka.set_external_token(x_kis_token)
        ka.auth()
        
        # KIS API 호출
        result = search_info(
            pdno=symbol,
            prdt_type_cd=product_type
        )
        
        # DataFrame을 dictionary로 변환
        data = result.to_dict('records') if hasattr(result, 'to_dict') else []
        
        return ApiResponse(
            success=True,
            data={"records": data} if isinstance(data, list) else data,
            message=f"종목검색 성공: {symbol}",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logging.error(f"종목검색 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"종목검색 실패: {str(e)}"
        )

@app.get("/indices/domestic",
         tags=["국내 시장지수"],
         summary="시장지수 조회",
         description="""
         한국 주요 시장지수의 현재 수준과 등락 정보를 조회합니다.
         
         **반환 데이터:**
         - 현재 지수 값, 전일대비, 등락률
         - 시가, 고가, 저가 지수
         - 거래량, 거래대금
         - 상승/하락 종목수
         - 지수 구성 시가총액 정보
         
         **활용 예시:**
         - 시장 전반 동향 파악
         - 섹터별/시장별 성과 비교
         - 마켓 타이밍 분석
         - 포트폴리오 벤치마킹
         
         **주요 지수 코드:**
         - 0001: KOSPI (코스피)
         - 1001: KOSDAQ (코스닥)
         - 2001: KOSPI200 (코스피200)
         - 기타 섹터/테마 지수 지원
         
         **예시:** `GET /indices/domestic?index_code=0001` (코스피 조회)
         """)
async def get_domestic_indices(
    index_code: str = Query("0001", description="지수코드", example="0001"),
    x_kis_token: Optional[str] = Header(None, alias="X-KIS-Token", description="KIS API 인증 토큰 (선택사항)")
):
    check_auth()
    
    try:
        # 헤더에서 받은 토큰으로 KIS 인증
        if x_kis_token:
            ka.set_external_token(x_kis_token)
        ka.auth()
        
        # KIS API 호출
        result = inquire_index_price(
            fid_cond_mrkt_div_code="U",  # 업종
            fid_input_iscd=index_code
        )
        
        # DataFrame을 dictionary로 변환
        data = result.to_dict('records') if hasattr(result, 'to_dict') else []
        
        return ApiResponse(
            success=True,
            data={"records": data} if isinstance(data, list) else data,
            message=f"시장지수 조회 성공: {index_code}",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logging.error(f"시장지수 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"시장지수 조회 실패: {str(e)}"
        )

# === 해외 주식 API ===
def check_overseas_auth():
    if not OVERSEAS_MODULE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="해외 주식 모듈을 사용할 수 없습니다. 설정을 확인해주세요."
        )
    return True

@app.get("/overseas/{exchange}/chart/daily/{symbol}",
         tags=["해외 주식 차트"],
         summary="해외 주식 일봉/주봉/월봉 차트 조회",
         description="""
         해외 주식의 일봉, 주봉, 월봉 차트 데이터를 조회합니다.
         
         **지원 거래소:**
         - NYS: 뉴욕증권거래소
         - NAS: 나스닥
         - AMS: 아메렉스
         - TSE: 도쿄증권거래소
         - HKS: 홍콩증권거래소
         - SHS: 상하이증권거래소
         - SZS: 선전증권거래소
         - LSE: 런던증권거래소
         
         **반환 데이터:**
         - OHLC (시가, 고가, 저가, 종가) - 현지 통화
         - 거래량
         - 날짜별 히스토리 데이터
         
         **주의사항:**
         - 시작일과 종료일은 필수 파라미터입니다
         - 최대 조회 기간은 거래소별로 제한될 수 있습니다
         - 현지 휴장일은 데이터가 없을 수 있습니다
         
         **예시:** `GET /overseas/NYS/chart/daily/AAPL?start_date=20241201&end_date=20241231&period=D`
         """)
async def get_overseas_daily_chart(
    exchange: str = Path(..., description="거래소 코드", example="NYS"),
    symbol: str = Path(..., description="종목 심볼", example="AAPL"),
    start_date: str = Query(..., description="시작일 (YYYYMMDD)", example="20241201"),
    end_date: str = Query(..., description="종료일 (YYYYMMDD)", example="20241231"),
    period: str = Query("D", description="차트 주기", example="D", regex="^[DWM]$"),
    x_kis_token: Optional[str] = Header(None, alias="X-KIS-Token", description="KIS API 인증 토큰 (선택사항)")
):
    check_overseas_auth()
    
    # 거래소 코드 검증
    valid_exchanges = ["NYS", "NAS", "AMS", "HKS", "SHS", "SZS", "TSE", "HSX", "HNX"]
    if exchange.upper() not in valid_exchanges:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 거래소입니다. 지원 거래소: {', '.join(valid_exchanges)}"
        )
    
    try:
        # 헤더에서 받은 토큰으로 KIS 인증
        if x_kis_token:
            ka.set_external_token(x_kis_token)
        ka.auth()
        
        # KIS API 호출
        result = overseas_daily_chart(
            fid_cond_mrkt_div_code="N",
            fid_input_iscd=symbol,
            fid_input_date_1=start_date,
            fid_input_date_2=end_date,
            fid_period_div_code=period,
            env_dv="real"
        )
        
        # 튜플인 경우 첫 번째 DataFrame 사용, DataFrame을 dictionary로 변환
        if isinstance(result, tuple):
            result = result[0]  # 첫 번째 DataFrame 사용
        data = result.to_dict('records') if hasattr(result, 'to_dict') else result
        
        return ApiResponse(
            success=True,
            data={"records": data} if isinstance(data, list) else data,
            message=f"해외 차트 데이터 조회 성공: {exchange}/{symbol}",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logging.error(f"해외 차트 데이터 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"해외 차트 데이터 조회 실패: {str(e)}"
        )

@app.get("/overseas/{exchange}/chart/minute/{symbol}",
         tags=["해외 주식 차트"],
         summary="해외 주식 분봉 차트 조회",
         description="""
         해외 주식의 분봉 차트 데이터를 조회합니다.
         
         **지원 분봉 단위:**
         - 1분봉, 3분봉, 5분봉, 10분봉
         - 15분봉, 30분봉, 60분봉 (1시간봉)
         
         **지원 거래소:**
         - NYS: 뉴욕증권거래소
         - NAS: 나스닥
         - AMS: 아메렉스
         - TSE: 도쿄증권거래소
         - HKS: 홍콩증권거래소
         - SHS: 상하이증권거래소
         - SZS: 선전증권거래소
         - LSE: 런던증권거래소
         
         **반환 데이터:**
         - OHLC (시가, 고가, 저가, 종가) - 현지 통화
         - 거래량
         - 분봉별 히스토리 데이터
         
         **파라미터 설명:**
         - nmin: 분봉 단위 (1, 3, 5, 10, 15, 30, 60)
         - pinc: 전일 데이터 포함 여부 (0: 미포함, 1: 포함)
         
         **예시:** `GET /overseas/NYS/chart/minute/AAPL?nmin=5&pinc=1` (애플 5분봉, 전일 포함)
         """)
async def get_overseas_minute_chart(
    exchange: str = Path(..., description="거래소 코드", example="NYS"),
    symbol: str = Path(..., description="종목 심볼", example="AAPL"),
    nmin: str = Query("1", description="분봉 단위", example="5", regex="^(1|3|5|10|15|30|60)$"),
    pinc: str = Query("1", description="전일포함여부", example="1", regex="^(0|1)$"),
    x_kis_token: Optional[str] = Header(None, alias="X-KIS-Token", description="KIS API 인증 토큰 (선택사항)")
):
    check_overseas_auth()
    
    # 거래소 코드 검증
    valid_exchanges = ["NYS", "NAS", "AMS", "HKS", "SHS", "SZS", "TSE", "HSX", "HNX"]
    if exchange.upper() not in valid_exchanges:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 거래소입니다. 지원 거래소: {', '.join(valid_exchanges)}"
        )
    
    try:
        # 헤더에서 받은 토큰으로 KIS 인증
        if x_kis_token:
            ka.set_external_token(x_kis_token)
        ka.auth()
        
        # KIS API 호출
        result = overseas_minute_chart(
            auth="",
            excd=exchange.upper(),
            symb=symbol,
            nmin=nmin,
            pinc=pinc,
            next="1",
            nrec="120",
            fill="",
            keyb=""
        )
        
        # 튜플인 경우 첫 번째 DataFrame 사용, DataFrame을 dictionary로 변환
        if isinstance(result, tuple):
            result = result[0]  # 첫 번째 DataFrame 사용
        data = result.to_dict('records') if hasattr(result, 'to_dict') else result
        
        return ApiResponse(
            success=True,
            data={"records": data} if isinstance(data, list) else data,
            message=f"해외 분봉 데이터 조회 성공: {exchange}/{symbol}",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logging.error(f"해외 분봉 데이터 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"해외 분봉 데이터 조회 실패: {str(e)}"
        )

@app.get("/overseas/{exchange}/price/{symbol}",
         tags=["해외 주식 시세"],
         summary="해외 주식 현재가 조회",
         description="""
         해외 주식의 실시간 현재가 정보를 조회합니다.
         
         **지원 거래소:**
         - NYS: 뉴욕증권거래소 (NYSE)
         - NAS: 나스닥 (NASDAQ)
         - AMS: 아메렉스 (AMEX)
         - TSE: 도쿄증권거래소
         - HKS: 홍콩증권거래소
         - SHS: 상하이증권거래소
         - SZS: 선전증권거래소
         - LSE: 런던증권거래소
         
         **반환 데이터:**
         - 현재가, 전일대비, 등락률 (현지 통화)
         - 시가, 고가, 저가
         - 거래량, 거래대금
         - 52주 고가/저가
         - 시가총액 (가능한 경우)
         
         **활용 예시:**
         - 해외 주식 실시간 모니터링
         - 환율을 고려한 투자 수익률 계산
         - 글로벌 포트폴리오 관리
         - 해외 시장 분석
         
         **주의사항:**
         - 가격은 현지 통화로 표시됩니다
         - 시장 휴장 시간에는 전일 종가가 표시될 수 있습니다
         - 실시간 데이터는 지연될 수 있습니다
         
         **예시:** `GET /overseas/NYS/price/AAPL` (애플 현재가 조회)
         """)
async def get_overseas_current_price(
    exchange: str = Path(..., description="거래소 코드", example="NYS"),
    symbol: str = Path(..., description="종목 심볼", example="AAPL"),
    x_kis_token: Optional[str] = Header(None, alias="X-KIS-Token", description="KIS API 인증 토큰 (선택사항)")
):
    check_overseas_auth()
    
    # 거래소 코드 검증
    valid_exchanges = ["NYS", "NAS", "AMS", "HKS", "SHS", "SZS", "TSE", "HSX", "HNX"]
    if exchange.upper() not in valid_exchanges:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 거래소입니다. 지원 거래소: {', '.join(valid_exchanges)}"
        )
    
    try:
        # 헤더에서 받은 토큰으로 KIS 인증
        if x_kis_token:
            ka.set_external_token(x_kis_token)
        ka.auth()
        
        # KIS API 호출
        result = overseas_price(
            auth="",
            excd=exchange.upper(),
            symb=symbol,
            env_dv="real"
        )
        
        # DataFrame을 dictionary로 변환
        data = result.to_dict('records') if hasattr(result, 'to_dict') else result
        
        return ApiResponse(
            success=True,
            data={"records": data} if isinstance(data, list) else data,
            message=f"해외 현재가 조회 성공: {exchange}/{symbol}",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logging.error(f"해외 현재가 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"해외 현재가 조회 실패: {str(e)}"
        )

# === 새로 추가된 해외 주식 API ===

@app.get("/overseas/{exchange}/info/{symbol}",
         tags=["해외 주식 기본정보"],
         summary="해외 주식 기본정보 조회",
         description="""
         해외 주식의 기본 정보를 조회합니다.
         
         **지원 거래소:**
         - NYS: 뉴욕증권거래소 (512: 나스닥, 513: 뉴욕, 529: 아멕스)
         - NAS: 나스닥
         - AMS: 아메렉스
         - TSE: 도쿄증권거래소 (515: 일본)
         - HKS: 홍콩증권거래소 (501: 홍콩)
         - SHS: 상하이증권거래소 (551: 중국 상해A)
         - SZS: 선전증권거래소 (552: 중국 심천A)
         
         **반환 데이터:**
         - 종목명, 기업 기본정보
         - 업종, 섹터 분류
         - 시가총액, 발행주식수
         - 재무 지표 (가능한 경우)
         - 거래소 및 상장 정보
         
         **활용 예시:**
         - 해외 종목 기본 분석
         - 포트폴리오 종목 선정
         - 기업 기초 정보 수집
         - 섹터별 분석
         
         **예시:** `GET /overseas/NYS/info/AAPL` (애플 기본정보)
         """)
async def get_overseas_stock_info(
    exchange: str = Path(..., description="거래소 코드", example="NYS"),
    symbol: str = Path(..., description="종목 심볼", example="AAPL"),
    x_kis_token: Optional[str] = Header(None, alias="X-KIS-Token", description="KIS API 인증 토큰 (선택사항)")
):
    check_overseas_auth()
    
    # 거래소 코드를 상품유형코드로 매핑
    exchange_to_product_type = {
        "NAS": "512",  # 미국 나스닥
        "NYS": "513",  # 미국 뉴욕
        "AMS": "529",  # 미국 아멕스
        "TSE": "515",  # 일본
        "HKS": "501",  # 홍콩
        "SHS": "551",  # 중국 상해A
        "SZS": "552"   # 중국 심천A
    }
    
    exchange_upper = exchange.upper()
    if exchange_upper not in exchange_to_product_type:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 거래소입니다. 지원 거래소: {', '.join(exchange_to_product_type.keys())}"
        )
    
    try:
        # 헤더에서 받은 토큰으로 KIS 인증
        if x_kis_token:
            ka.set_external_token(x_kis_token)
        ka.auth()
        
        # KIS API 호출
        result = overseas_search_info(
            prdt_type_cd=exchange_to_product_type[exchange_upper],
            pdno=symbol.upper()
        )
        
        # DataFrame을 dictionary로 변환
        data = result.to_dict('records') if hasattr(result, 'to_dict') else result
        
        return ApiResponse(
            success=True,
            data={"records": data} if isinstance(data, list) else data,
            message=f"해외 주식 기본정보 조회 성공: {exchange}/{symbol}",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logging.error(f"해외 주식 기본정보 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"해외 주식 기본정보 조회 실패: {str(e)}"
        )

@app.get("/overseas/{exchange}/search",
         tags=["해외 주식 기본정보"],
         summary="해외 주식 조건검색",
         description="""
         조건에 맞는 해외 주식을 검색합니다.
         
         **지원 거래소:**
         - NYS: 뉴욕증권거래소 
         - NAS: 나스닥
         - AMS: 아메렉스
         - TSE: 도쿄증권거래소
         - HKS: 홍콩증권거래소
         
         **검색 조건:**
         - 현재가 범위 (min_price ~ max_price)
         - 등락률 범위 (선택사항)
         - 시가총액 범위 (선택사항)
         - 거래량 범위 (선택사항)
         
         **활용 예시:**
         - 특정 가격대 종목 찾기
         - 고성장 종목 스크리닝
         - 섹터별 종목 탐색
         - 투자 대상 후보 발굴
         
         **예시:** `GET /overseas/NAS/search?min_price=100&max_price=200`
         """)
async def search_overseas_stocks(
    exchange: str = Path(..., description="거래소 코드", example="NAS"),
    min_price: Optional[str] = Query(None, description="최소 현재가", example="100"),
    max_price: Optional[str] = Query(None, description="최대 현재가", example="200"),
    min_change_rate: Optional[str] = Query(None, description="최소 등락률", example="-5"),
    max_change_rate: Optional[str] = Query(None, description="최대 등락률", example="5"),
    min_market_cap: Optional[str] = Query(None, description="최소 시가총액"),
    max_market_cap: Optional[str] = Query(None, description="최대 시가총액"),
    min_volume: Optional[str] = Query(None, description="최소 거래량"),
    max_volume: Optional[str] = Query(None, description="최대 거래량"),
    x_kis_token: Optional[str] = Header(None, alias="X-KIS-Token", description="KIS API 인증 토큰 (선택사항)")
):
    check_overseas_auth()
    
    # 거래소 코드 검증 
    valid_exchanges = ["NYS", "NAS", "AMS", "TSE", "HKS"]
    exchange_upper = exchange.upper()
    if exchange_upper not in valid_exchanges:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 거래소입니다. 지원 거래소: {', '.join(valid_exchanges)}"
        )
    
    try:
        # 헤더에서 받은 토큰으로 KIS 인증
        if x_kis_token:
            ka.set_external_token(x_kis_token)
        ka.auth()
        
        # KIS API 호출 - 조건검색
        result1, result2 = overseas_inquire_search(
            auth="",
            excd=exchange_upper,
            co_yn_pricecur="1" if min_price or max_price else "",
            co_st_pricecur=min_price or "",
            co_en_pricecur=max_price or "",
            co_yn_rate="1" if min_change_rate or max_change_rate else "",
            co_st_rate=min_change_rate or "",
            co_en_rate=max_change_rate or "",
            co_yn_valx="1" if min_market_cap or max_market_cap else "",
            co_st_valx=min_market_cap or "",
            co_en_valx=max_market_cap or "",
            co_yn_shar="",
            co_st_shar="",
            co_en_shar="",
            co_yn_volume="1" if min_volume or max_volume else "",
            co_st_volume=min_volume or "",
            co_en_volume=max_volume or "",
            co_yn_amt="",
            co_st_amt="",
            co_en_amt="",
            co_yn_eps="",
            co_st_eps="",
            co_en_eps="",
            co_yn_per="",
            co_st_per="",
            co_en_per="",
            keyb=""
        )
        
        # DataFrame을 dictionary로 변환
        data1 = result1.to_dict('records') if hasattr(result1, 'to_dict') else result1
        data2 = result2.to_dict('records') if hasattr(result2, 'to_dict') else result2
        
        return ApiResponse(
            success=True,
            data={
                "search_results": data1,
                "summary": data2
            },
            message=f"해외 주식 검색 성공: {exchange}",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logging.error(f"해외 주식 검색 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"해외 주식 검색 실패: {str(e)}"
        )

@app.get("/indices/overseas/{exchange}",
         tags=["해외 시장지수"],
         summary="해외 시장지수 조회",
         description="""
         해외 주요 시장지수의 현재 수준과 등락 정보를 조회합니다.
         
         **지원 거래소 및 지수:**
         - US (미국): SPX (S&P500), DJI (다우존스), NDX (나스닥100)
         - JP (일본): N225 (니케이225), TPX (TOPIX)
         - HK (홍콩): HSI (항셍지수)
         - CN (중국): SHCOMP (상해종합), SZCOMP (심천종합)
         
         **반환 데이터:**
         - 현재 지수 값, 전일대비, 등락률
         - 시가, 고가, 저가 지수
         - 거래량, 거래대금 (가능한 경우)
         - 구성 종목 정보 (요약)
         
         **활용 예시:**
         - 글로벌 시장 동향 파악
         - 지역별/국가별 시장 성과 비교
         - 국제 분산투자 벤치마킹
         - 해외 시장 타이밍 분석
         
         **예시:** `GET /indices/overseas/US?index_code=SPX` (S&P500 지수)
         """)
async def get_overseas_market_indices(
    exchange: str = Path(..., description="국가/지역 코드", example="US"),
    index_code: str = Query("SPX", description="지수 코드", example="SPX"),
    x_kis_token: Optional[str] = Header(None, alias="X-KIS-Token", description="KIS API 인증 토큰 (선택사항)")
):
    check_overseas_auth()
    
    # 지수 코드 검증
    valid_indices = {
        "US": ["SPX", "DJI", "NDX", "RUT"],  # S&P500, 다우존스, 나스닥100, 러셀2000
        "JP": ["N225", "TPX"],              # 니케이225, TOPIX
        "HK": ["HSI"],                      # 항셍지수
        "CN": ["SHCOMP", "SZCOMP"],         # 상해종합, 심천종합
        "EU": ["SX5E", "UKX"]               # 유로스톡스50, FTSE100
    }
    
    exchange_upper = exchange.upper()
    if exchange_upper not in valid_indices:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 국가/지역입니다. 지원: {', '.join(valid_indices.keys())}"
        )
    
    if index_code.upper() not in valid_indices[exchange_upper]:
        raise HTTPException(
            status_code=400,
            detail=f"{exchange_upper} 지원 지수: {', '.join(valid_indices[exchange_upper])}"
        )
    
    try:
        # 헤더에서 받은 토큰으로 KIS 인증
        if x_kis_token:
            ka.set_external_token(x_kis_token)
        ka.auth()
        
        # 해외지수 일봉차트 조회를 통해 현재 지수값 가져오기
        result1, result2 = overseas_daily_chart(
            fid_cond_mrkt_div_code="N",  # N: 해외지수
            fid_input_iscd=index_code.upper(),
            fid_input_date_1="20240101",  # 시작일
            fid_input_date_2="20241231",  # 종료일  
            fid_period_div_code="D"       # D: 일봉
        )
        
        # DataFrame을 dictionary로 변환
        data1 = result1.to_dict('records') if hasattr(result1, 'to_dict') else result1
        data2 = result2.to_dict('records') if hasattr(result2, 'to_dict') else result2
        
        return ApiResponse(
            success=True,
            data={
                "index_data": data1,
                "summary": data2,
                "index_info": {
                    "exchange": exchange_upper,
                    "index_code": index_code.upper(),
                    "index_name": f"{exchange_upper} {index_code.upper()} Index"
                }
            },
            message=f"해외 시장지수 조회 성공: {exchange_upper}/{index_code}",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logging.error(f"해외 시장지수 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"해외 시장지수 조회 실패: {str(e)}"
        )

@app.get("/indices/overseas/{exchange}/chart/daily/{index_code}",
         tags=["해외 지수 차트"],
         summary="해외 지수 일봉 차트 조회", 
         description="""
         해외 주요 지수의 일봉 차트 데이터를 조회합니다.
         
         **지원 지수:**
         - US: SPX, DJI, NDX, RUT
         - JP: N225, TPX
         - HK: HSI
         - CN: SHCOMP, SZCOMP
         - EU: SX5E, UKX
         
         **반환 데이터:**
         - OHLC (시가, 고가, 저가, 종가)
         - 거래량 (가능한 경우)
         - 날짜별 지수 히스토리
         
         **활용 예시:**
         - 해외 지수 기술적 분석
         - 글로벌 시장 트렌드 분석
         - 국가간 시장 성과 비교
         - 국제 분산투자 전략 수립
         
         **예시:** `GET /indices/overseas/US/chart/daily/SPX?start_date=20240101&end_date=20241231`
         """)
async def get_overseas_index_daily_chart(
    exchange: str = Path(..., description="국가/지역 코드", example="US"),
    index_code: str = Path(..., description="지수 코드", example="SPX"),
    start_date: str = Query(..., description="시작일 (YYYYMMDD)", example="20240101"),
    end_date: str = Query(..., description="종료일 (YYYYMMDD)", example="20241231"),
    period: str = Query("D", description="차트 주기", example="D", regex="^[DWM]$"),
    x_kis_token: Optional[str] = Header(None, alias="X-KIS-Token", description="KIS API 인증 토큰 (선택사항)")
):
    check_overseas_auth()
    
    # 지수 코드 검증
    valid_indices = ["SPX", "DJI", "NDX", "RUT", "N225", "TPX", "HSI", "SHCOMP", "SZCOMP", "SX5E", "UKX"]
    if index_code.upper() not in valid_indices:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 지수입니다. 지원 지수: {', '.join(valid_indices)}"
        )
    
    try:
        # 헤더에서 받은 토큰으로 KIS 인증
        if x_kis_token:
            ka.set_external_token(x_kis_token)
        ka.auth()
        
        # KIS API 호출
        result1, result2 = overseas_daily_chart(
            fid_cond_mrkt_div_code="N",  # N: 해외지수
            fid_input_iscd=index_code.upper(),
            fid_input_date_1=start_date,
            fid_input_date_2=end_date,
            fid_period_div_code=period
        )
        
        # DataFrame을 dictionary로 변환
        data1 = result1.to_dict('records') if hasattr(result1, 'to_dict') else result1
        data2 = result2.to_dict('records') if hasattr(result2, 'to_dict') else result2
        
        return ApiResponse(
            success=True,
            data={
                "chart_data": data1,
                "summary": data2
            },
            message=f"해외 지수 일봉 차트 조회 성공: {exchange}/{index_code}",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logging.error(f"해외 지수 일봉 차트 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"해외 지수 일봉 차트 조회 실패: {str(e)}"
        )

@app.get("/indices/overseas/{exchange}/chart/minute/{index_code}",
         tags=["해외 지수 차트"],
         summary="해외 지수 분봉 차트 조회",
         description="""
         해외 주요 지수의 분봉 차트 데이터를 조회합니다.
         
         **지원 지수:**
         - US: SPX, DJI, NDX, RUT  
         - JP: N225, TPX
         - HK: HSI
         - CN: SHCOMP, SZCOMP
         - EU: SX5E, UKX
         
         **반환 데이터:**
         - OHLC (시가, 고가, 저가, 종가)
         - 거래량 (가능한 경우)
         - 분봉별 지수 히스토리
         
         **파라미터 설명:**
         - hour_type: 0=정규장, 1=시간외
         - include_past: Y=과거데이터포함, N=당일만
         
         **활용 예시:**
         - 실시간 지수 모니터링
         - 단기 지수 트레이딩
         - 시장 개장 시간 분석
         - 지수 변동성 추적
         
         **예시:** `GET /indices/overseas/US/chart/minute/SPX?hour_type=0&include_past=Y`
         """)
async def get_overseas_index_minute_chart(
    exchange: str = Path(..., description="국가/지역 코드", example="US"),
    index_code: str = Path(..., description="지수 코드", example="SPX"),
    hour_type: str = Query("0", description="시간 구분", example="0", regex="^[01]$"),
    include_past: str = Query("Y", description="과거 데이터 포함 여부", example="Y", regex="^[YN]$"),
    x_kis_token: Optional[str] = Header(None, alias="X-KIS-Token", description="KIS API 인증 토큰 (선택사항)")
):
    check_overseas_auth()
    
    # 지수 코드 검증
    valid_indices = ["SPX", "DJI", "NDX", "RUT", "N225", "TPX", "HSI", "SHCOMP", "SZCOMP", "SX5E", "UKX"]
    if index_code.upper() not in valid_indices:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 지수입니다. 지원 지수: {', '.join(valid_indices)}"
        )
    
    try:
        # 헤더에서 받은 토큰으로 KIS 인증
        if x_kis_token:
            ka.set_external_token(x_kis_token)
        ka.auth()
        
        # KIS API 호출
        result1, result2 = overseas_index_minute_chart(
            fid_cond_mrkt_div_code="N",  # N: 해외지수
            fid_input_iscd=index_code.upper(),
            fid_hour_cls_code=hour_type,
            fid_pw_data_incu_yn=include_past
        )
        
        # DataFrame을 dictionary로 변환
        data1 = result1.to_dict('records') if hasattr(result1, 'to_dict') else result1
        data2 = result2.to_dict('records') if hasattr(result2, 'to_dict') else result2
        
        return ApiResponse(
            success=True,
            data={
                "chart_data": data1,
                "summary": data2
            },
            message=f"해외 지수 분봉 차트 조회 성공: {exchange}/{index_code}",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logging.error(f"해외 지수 분봉 차트 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"해외 지수 분봉 차트 조회 실패: {str(e)}"
        )

