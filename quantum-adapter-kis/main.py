from fastapi import FastAPI, HTTPException, Query, Header
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
    from domestic_stock_functions import inquire_daily_itemchartprice, inquire_time_itemchartprice, inquire_price, inquire_asking_price_exp_ccn, search_stock_info, search_info, inquire_index_price
    # 해외 주식 함수들 (이름 충돌 방지를 위해 별칭 사용)
    from overseas_stock_functions import (
        inquire_daily_chartprice as overseas_daily_chart,
        inquire_time_itemchartprice as overseas_minute_chart,
        price as overseas_price
    )
    KIS_MODULE_AVAILABLE = True
    OVERSEAS_MODULE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"KIS 모듈을 불러올 수 없습니다: {e}")
    KIS_MODULE_AVAILABLE = False
    OVERSEAS_MODULE_AVAILABLE = False

app = FastAPI(
    title="Quantum KIS Adapter",
    description="Korea Investment & Securities API Adapter for Quantum Trading Platform",
    version="1.0.0"
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
@app.get("/domestic/chart/daily/{symbol}")
async def get_domestic_daily_chart(
    symbol: str,
    period: str = Query("D", description="차트 주기 (D/W/M)"),
    start_date: Optional[str] = Query(None, description="시작일 (YYYYMMDD)"),
    end_date: Optional[str] = Query(None, description="종료일 (YYYYMMDD)"),
    count: int = Query(100, description="조회 건수"),
    x_kis_token: Optional[str] = Header(None, alias="X-KIS-Token")
):
    """국내 일봉/주봉/월봉 차트 데이터 조회"""
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

@app.get("/domestic/price/{symbol}")
async def get_domestic_current_price(
    symbol: str,
    market: str = Query("J", description="시장구분 (J:주식, ETF 등)"),
    x_kis_token: Optional[str] = Header(None, alias="X-KIS-Token")
):
    """국내 현재가 조회"""
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

@app.get("/domestic/orderbook/{symbol}")
async def get_domestic_orderbook(
    symbol: str,
    market: str = Query("J", description="시장구분 (J:KRX, NX:NXT, UN:통합)"),
    x_kis_token: Optional[str] = Header(None, alias="X-KIS-Token")
):
    """국내 주식 호가정보 조회"""
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

@app.get("/domestic/info/{symbol}")
async def get_domestic_stock_info(
    symbol: str,
    product_type: str = Query("300", description="상품유형코드 (300: 주식/ETF/ETN/ELW, 301: 선물옵션, 302: 채권, 306: ELS)"),
    x_kis_token: Optional[str] = Header(None, alias="X-KIS-Token")
):
    """국내 종목 기본정보 조회"""
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

@app.get("/domestic/search")
async def search_domestic_stock(
    symbol: str = Query(..., description="검색할 종목코드 또는 심볼"),
    product_type: str = Query("300", description="상품유형코드 (300: 주식/ETF/ETN/ELW, 301: 선물옵션, 302: 채권, 306: ELS, 512: 해외주식)"),
    x_kis_token: Optional[str] = Header(None, alias="X-KIS-Token")
):
    """종목 검색 (종목코드/심볼 기반)"""
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

@app.get("/indices/domestic")
async def get_domestic_indices(
    index_code: str = Query("0001", description="지수코드 (0001:코스피, 1001:코스닥, 2001:코스피200)"),
    x_kis_token: Optional[str] = Header(None, alias="X-KIS-Token")
):
    """국내 시장지수 조회"""
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

@app.get("/overseas/{exchange}/chart/daily/{symbol}")
async def get_overseas_daily_chart(
    exchange: str,
    symbol: str,
    start_date: str = Query(..., description="시작일 (YYYYMMDD) - 필수"),
    end_date: str = Query(..., description="종료일 (YYYYMMDD) - 필수"),
    period: str = Query("D", description="차트 주기 (D/W/M)"),
    x_kis_token: Optional[str] = Header(None, alias="X-KIS-Token")
):
    """해외 일봉/주봉/월봉 차트 데이터 조회"""
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

@app.get("/overseas/{exchange}/chart/minute/{symbol}")
async def get_overseas_minute_chart(
    exchange: str,
    symbol: str,
    nmin: str = Query("1", description="분봉 단위 (1, 3, 5, 10, 15, 30, 60)"),
    pinc: str = Query("1", description="전일포함여부 (0: 미포함, 1: 포함)"),
    x_kis_token: Optional[str] = Header(None, alias="X-KIS-Token")
):
    """해외 분봉 차트 데이터 조회"""
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

@app.get("/overseas/{exchange}/price/{symbol}")
async def get_overseas_current_price(
    exchange: str,
    symbol: str,
    x_kis_token: Optional[str] = Header(None, alias="X-KIS-Token")
):
    """해외 현재가 조회"""
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

