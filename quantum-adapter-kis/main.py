"""
KIS Adapter FastAPI Server
차트 데이터 제공을 위한 REST API 서버

Author: Quantum Trading Platform
"""
import sys
import logging
from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import pandas as pd

# examples_llm 경로 추가
sys.path.extend(['examples_llm', '.'])
import kis_auth as ka

# KIS API 함수들 import
from domestic_stock.inquire_daily_itemchartprice.inquire_daily_itemchartprice import inquire_daily_itemchartprice
from domestic_stock.inquire_price.inquire_price import inquire_price
from domestic_stock.inquire_index_price.inquire_index_price import inquire_index_price

# 해외주식 API 함수들 import
from overseas_stock.price.price import price as overseas_price
from overseas_stock.inquire_daily_chartprice.inquire_daily_chartprice import inquire_daily_chartprice

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="KIS Adapter API",
    description="""
## 🚀 한국투자증권 OpenAPI 통합 어댑터

**국내 주식과 해외 주식을 동일한 인터페이스로 제공하는 REST API 서비스**

### 📊 주요 기능
- **국내 주식**: 현재가, 차트 데이터 (일/주/월/년봉), 지수
- **해외 주식**: 현재가, 차트 데이터 (일/주/월/년봉), 지수  
- **자동 분할 조회**: 큰 기간 데이터 자동 분할 처리
- **실시간 데이터**: KIS OpenAPI 실전 계좌 연동

### 🌏 지원 시장
- **국내**: KRX (코스피, 코스닥)
- **해외**: NAS(나스닥), NYS(뉴욕), HKS(홍콩), TSE(도쿄), SHS(상해), SZS(심천)

### 📖 사용 가이드
1. **기본 구조**: `/domestic/` 또는 `/overseas/{exchange}/`
2. **데이터 타입**: `price` (현재가), `chart` (차트), `index` (지수)
3. **응답 형식**: KIS OpenAPI 표준 형식 유지
""",
    version="1.0.0",
    contact={
        "name": "Quantum Trading Platform",
        "url": "https://github.com/quantum-trading-platform"
    }
)

# CORS 설정 (모든 도메인 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== 공통 응답 모델 ====================

class KISResponse(BaseModel):
    """KIS API 표준 응답 형식"""
    rt_cd: str = Field(..., description="응답 코드 (0: 성공)")
    msg_cd: str = Field(..., description="메시지 코드") 
    msg1: str = Field(..., description="응답 메시지")
    output: Dict[str, Any] = Field(..., description="응답 데이터")

class KISChartResponse(BaseModel):
    """KIS API 차트 데이터 응답 형식"""
    rt_cd: str = Field(..., description="응답 코드 (0: 성공)")
    msg_cd: str = Field(..., description="메시지 코드")
    msg1: str = Field(..., description="응답 메시지")  
    output1: Dict[str, Any] = Field(..., description="기본 정보")
    output2: List[Dict[str, Any]] = Field(..., description="차트 데이터")
    total_records: int = Field(..., description="총 데이터 건수")
    period: str = Field(..., description="조회 기간 (D/W/M/Y)")
    date_range: str = Field(..., description="조회 날짜 범위")

# ==================== 공통 헬퍼 함수 ====================

def create_success_response(data: Any, message: str = "정상처리 되었습니다") -> Dict[str, Any]:
    """성공 응답 생성 헬퍼 함수"""
    return {
        "rt_cd": "0",
        "msg_cd": "MCA00000",
        "msg1": message,
        "output": data
    }

def create_chart_response(
    output1: pd.DataFrame, 
    output2: pd.DataFrame, 
    period: str,
    date_range: str,
    extra_info: Dict[str, Any] = None
) -> Dict[str, Any]:
    """차트 응답 생성 헬퍼 함수"""
    response = {
        "rt_cd": "0",
        "msg_cd": "MCA00000", 
        "msg1": "정상처리 되었습니다",
        "output1": output1.to_dict(orient="records")[0] if not output1.empty else {},
        "output2": output2.to_dict(orient="records") if not output2.empty else [],
        "total_records": len(output2) if not output2.empty else 0,
        "period": period,
        "date_range": date_range
    }
    
    # 추가 정보가 있으면 병합
    if extra_info:
        response.update(extra_info)
    
    return response

def validate_period(period: str) -> str:
    """기간 파라미터 검증"""
    period_map = {"D": "일봉", "W": "주봉", "M": "월봉", "Y": "년봉"}
    if period not in period_map:
        raise HTTPException(
            status_code=400, 
            detail=f"period는 {', '.join([f'{k}({v})' for k, v in period_map.items()])} 중 하나여야 합니다"
        )
    return period

def get_exchange_info(exchange_code: str) -> Dict[str, str]:
    """거래소 코드 정보 반환"""
    exchanges = {
        "NAS": {"name": "NASDAQ", "korean": "나스닥", "timezone": "EST"},
        "NYS": {"name": "NYSE", "korean": "뉴욕증권거래소", "timezone": "EST"},
        "HKS": {"name": "HKEX", "korean": "홍콩거래소", "timezone": "HKT"},
        "TSE": {"name": "TSE", "korean": "도쿄증권거래소", "timezone": "JST"},
        "SHS": {"name": "SSE", "korean": "상하이거래소", "timezone": "CST"},
        "SZS": {"name": "SZSE", "korean": "심천거래소", "timezone": "CST"},
        "HSX": {"name": "HSX", "korean": "호치민거래소", "timezone": "ICT"},
        "HNX": {"name": "HNX", "korean": "하노이거래소", "timezone": "ICT"}
    }
    return exchanges.get(exchange_code, {"name": exchange_code, "korean": exchange_code, "timezone": "UTC"})

# 서버 시작시 KIS 인증
@app.on_event("startup")
async def startup_event():
    """서버 시작시 KIS API 인증 토큰 발급"""
    try:
        ka.auth(svr="prod", product="01")  # 실전 계좌 인증
        logger.info("✅ KIS API 인증 성공")
    except Exception as e:
        logger.error(f"❌ KIS API 인증 실패: {str(e)}")

# 기본 엔드포인트
@app.get("/")
async def root():
    """서버 상태 확인"""
    return {
        "message": "KIS Adapter FastAPI Server",
        "status": "running",
        "version": "1.0.0"
    }

# 헬스 체크
@app.get("/health")
async def health_check():
    """서버 헬스 체크"""
    return {"status": "healthy"}

# ==================== 국내 주식 API ====================

@app.get("/domestic/price/{symbol}")
async def get_domestic_price(symbol: str):
    """국내 주식 현재가 조회"""
    try:
        result = inquire_price(
            env_dv="real",
            fid_cond_mrkt_div_code="J", 
            fid_input_iscd=symbol
        )
        
        if result.empty:
            raise HTTPException(status_code=404, detail="종목을 찾을 수 없습니다")

        # pandas DataFrame을 dict로 변환
        return {
            "rt_cd": "0",
            "msg_cd": "MCA00000",
            "msg1": "정상처리 되었습니다",
            "output": result.to_dict(orient="records")[0]
        }
        
    except Exception as e:
        logger.error(f"국내 현재가 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def get_date_ranges(start_date: str, end_date: str, max_days: int = 90) -> List[Tuple[str, str]]:
    """큰 기간을 작은 기간들로 분할"""
    start = datetime.strptime(start_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")
    
    ranges = []
    current_start = start
    
    while current_start < end:
        current_end = min(current_start + timedelta(days=max_days), end)
        ranges.append((
            current_start.strftime("%Y%m%d"),
            current_end.strftime("%Y%m%d")
        ))
        current_start = current_end + timedelta(days=1)
    
    return ranges

@app.get("/domestic/chart/{symbol}")
async def get_domestic_chart(
    symbol: str,
    period: str = "D",  # D:일봉, W:주봉, M:월봉, Y:년봉
    start_date: str = "20240101",
    end_date: str = "20250203",
    adj_price: str = "1"  # 0:수정주가, 1:원주가
):
    """국내 주식 차트 조회 (일/주/월/년봉 지원, 자동 분할 조회)"""
    try:
        # 기간 검증
        period_map = {"D": "D", "W": "W", "M": "M", "Y": "Y"}
        if period not in period_map:
            raise HTTPException(status_code=400, detail="period는 D(일봉), W(주봉), M(월봉), Y(년봉) 중 하나여야 합니다")
        
        # 날짜 범위 계산
        start = datetime.strptime(start_date, "%Y%m%d")
        end = datetime.strptime(end_date, "%Y%m%d")
        days_diff = (end - start).days
        
        # 100건 제한을 고려하여 분할 조회 여부 결정
        if period == "D" and days_diff > 90:
            # 일봉이고 90일 이상인 경우 분할 조회
            date_ranges = get_date_ranges(start_date, end_date, 90)
            
            all_output1 = None
            all_output2 = pd.DataFrame()
            
            for range_start, range_end in date_ranges:
                try:
                    output1, output2 = inquire_daily_itemchartprice(
                        env_dv="real",
                        fid_cond_mrkt_div_code="J",
                        fid_input_iscd=symbol,
                        fid_input_date_1=range_start,
                        fid_input_date_2=range_end,
                        fid_period_div_code=period,
                        fid_org_adj_prc=adj_price
                    )
                    
                    # output1은 첫 번째 결과만 사용
                    if all_output1 is None and not output1.empty:
                        all_output1 = output1
                    
                    # output2는 모든 결과를 합침
                    if not output2.empty:
                        all_output2 = pd.concat([all_output2, output2], ignore_index=True)
                    
                    # API 호출 제한을 위한 잠시 대기
                    import time
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"부분 조회 실패 ({range_start}-{range_end}): {str(e)}")
                    continue
            
            if all_output2.empty:
                raise HTTPException(status_code=404, detail="차트 데이터를 찾을 수 없습니다")
            
            # 날짜순 정렬 (오래된 날짜부터)
            if 'stck_bsop_date' in all_output2.columns:
                all_output2 = all_output2.sort_values('stck_bsop_date').reset_index(drop=True)
            
            return {
                "rt_cd": "0",
                "msg_cd": "MCA00000",
                "msg1": "정상처리 되었습니다",
                "output1": all_output1.to_dict(orient="records")[0] if all_output1 is not None else {},
                "output2": all_output2.to_dict(orient="records"),
                "total_records": len(all_output2),
                "period": period,
                "date_range": f"{start_date}~{end_date}"
            }
            
        else:
            # 단일 조회 (주봉/월봉/년봉 또는 90일 이하 일봉)
            output1, output2 = inquire_daily_itemchartprice(
                env_dv="real",
                fid_cond_mrkt_div_code="J",
                fid_input_iscd=symbol,
                fid_input_date_1=start_date,
                fid_input_date_2=end_date,
                fid_period_div_code=period,
                fid_org_adj_prc=adj_price
            )
            
            if output1.empty and output2.empty:
                raise HTTPException(status_code=404, detail="차트 데이터를 찾을 수 없습니다")
            
            return {
                "rt_cd": "0",
                "msg_cd": "MCA00000",
                "msg1": "정상처리 되었습니다",
                "output1": output1.to_dict(orient="records")[0] if not output1.empty else {},
                "output2": output2.to_dict(orient="records") if not output2.empty else [],
                "total_records": len(output2) if not output2.empty else 0,
                "period": period,
                "date_range": f"{start_date}~{end_date}"
            }
        
    except Exception as e:
        logger.error(f"국내 차트 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/domestic/index/{index_code}")
async def get_domestic_index(index_code: str):
    """국내 지수 현재가 조회
    
    Args:
        index_code (str): 지수 코드 (예: 0001=코스피, 1001=코스닥, 2001=코스피200)
    """
    try:
        result = inquire_index_price(
            fid_cond_mrkt_div_code="U",  # 업종 구분
            fid_input_iscd=index_code
        )
        
        if result is None or result.empty:
            raise HTTPException(status_code=404, detail="지수 데이터를 찾을 수 없습니다")
        
        # pandas DataFrame을 dict로 변환
        return {
            "rt_cd": "0",
            "msg_cd": "MCA00000", 
            "msg1": "정상처리 되었습니다",
            "output": result.to_dict(orient="records")
        }
        
    except Exception as e:
        logger.error(f"국내 지수 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 해외 주식 API ====================

@app.get("/overseas/{exchange}/price/{symbol}")
async def get_overseas_price(exchange: str, symbol: str):
    """해외 주식 현재가 조회

    Args:
        exchange (str): 거래소 코드 (NAS=나스닥, NYS=뉴욕, HKS=홍콩, SHS=상해, SZS=심천, TSE=도쿄, HSX=호치민, HNX=하노이)
        symbol (str): 종목 코드 (예: AAPL, TSLA, 00700.HK)
    """
    try:
        result = overseas_price(
            auth="",
            excd=exchange,
            symb=symbol,
            env_dv="real"
        )

        if result is None or result.empty:
            raise HTTPException(status_code=404, detail="해외 주식 데이터를 찾을 수 없습니다")

        # pandas DataFrame을 dict로 변환
        return {
            "rt_cd": "0",
            "msg_cd": "MCA00000",
            "msg1": "정상처리 되었습니다",
            "output": result.to_dict(orient="records")[0]
        }

    except Exception as e:
        logger.error(f"해외 현재가 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/overseas/{exchange}/chart/{symbol}")
async def get_overseas_chart(
    exchange: str,
    symbol: str,
    period: str = "D",  # D:일봉, W:주봉, M:월봉, Y:년봉
    start_date: str = "20240101", 
    end_date: str = "20250203"
):
    """해외 주식 차트 조회 (일/주/월/년봉 지원, 자동 분할 조회)
    
    Args:
        exchange (str): 거래소 코드 (NAS, NYS, HKS, SHS, SZS, TSE, HSX, HNX)
        symbol (str): 종목 코드 (예: AAPL, TSLA, 00700.HK)
        period (str): 기간 구분 (D:일봉, W:주봉, M:월봉, Y:년봉)
        start_date (str): 조회 시작일 (YYYYMMDD)
        end_date (str): 조회 종료일 (YYYYMMDD)
    """
    try:
        # 기간 검증
        period_map = {"D": "D", "W": "W", "M": "M", "Y": "Y"}
        if period not in period_map:
            raise HTTPException(status_code=400, detail="period는 D(일봉), W(주봉), M(월봉), Y(년봉) 중 하나여야 합니다")
        
        # 거래소 코드 검증 (해외주식 종목_지수_환율기간별시세 API의 경우 N으로 고정)
        fid_cond_mrkt_div_code = "N"  # N: 해외지수, 해외주식의 경우 N 사용
        
        # 날짜 범위 계산
        start = datetime.strptime(start_date, "%Y%m%d")
        end = datetime.strptime(end_date, "%Y%m%d")
        days_diff = (end - start).days
        
        # 100건 제한을 고려하여 분할 조회 여부 결정
        if period == "D" and days_diff > 90:
            # 일봉이고 90일 이상인 경우 분할 조회
            date_ranges = get_date_ranges(start_date, end_date, 90)
            
            all_output1 = None
            all_output2 = pd.DataFrame()
            
            for range_start, range_end in date_ranges:
                try:
                    output1, output2 = inquire_daily_chartprice(
                        fid_cond_mrkt_div_code=fid_cond_mrkt_div_code,
                        fid_input_iscd=f"{exchange}.{symbol}" if exchange != "NAS" and exchange != "NYS" else symbol,
                        fid_input_date_1=range_start,
                        fid_input_date_2=range_end,
                        fid_period_div_code=period,
                        env_dv="real"
                    )
                    
                    # output1은 첫 번째 결과만 사용
                    if all_output1 is None and not output1.empty:
                        all_output1 = output1
                    
                    # output2는 모든 결과를 합침
                    if not output2.empty:
                        all_output2 = pd.concat([all_output2, output2], ignore_index=True)
                    
                    # API 호출 제한을 위한 잠시 대기
                    import time
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"부분 조회 실패 ({range_start}-{range_end}): {str(e)}")
                    continue
            
            if all_output2.empty:
                raise HTTPException(status_code=404, detail="해외 차트 데이터를 찾을 수 없습니다")
            
            # 날짜순 정렬 (오래된 날짜부터)
            if 'xymd' in all_output2.columns:
                all_output2 = all_output2.sort_values('xymd').reset_index(drop=True)
            
            return {
                "rt_cd": "0",
                "msg_cd": "MCA00000",
                "msg1": "정상처리 되었습니다",
                "output1": all_output1.to_dict(orient="records")[0] if all_output1 is not None and not all_output1.empty else {},
                "output2": all_output2.to_dict(orient="records"),
                "total_records": len(all_output2),
                "period": period,
                "date_range": f"{start_date}~{end_date}",
                "exchange": exchange
            }
            
        else:
            # 단일 조회 (주봉/월봉/년봉 또는 90일 이하 일봉)
            output1, output2 = inquire_daily_chartprice(
                fid_cond_mrkt_div_code=fid_cond_mrkt_div_code,
                fid_input_iscd=f"{exchange}.{symbol}" if exchange != "NAS" and exchange != "NYS" else symbol,
                fid_input_date_1=start_date,
                fid_input_date_2=end_date,
                fid_period_div_code=period,
                env_dv="real"
            )
            
            if output1.empty and output2.empty:
                raise HTTPException(status_code=404, detail="해외 차트 데이터를 찾을 수 없습니다")
            
            return {
                "rt_cd": "0",
                "msg_cd": "MCA00000",
                "msg1": "정상처리 되었습니다",
                "output1": output1.to_dict(orient="records")[0] if not output1.empty else {},
                "output2": output2.to_dict(orient="records") if not output2.empty else [],
                "total_records": len(output2) if not output2.empty else 0,
                "period": period,
                "date_range": f"{start_date}~{end_date}",
                "exchange": exchange
            }
        
    except Exception as e:
        logger.error(f"해외 차트 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/overseas/{exchange}/index/{index_code}")
async def get_overseas_index(exchange: str, index_code: str):
    """해외 지수 현재가 조회
    
    Args:
        exchange (str): 거래소 코드 (NAS, NYS, etc.)
        index_code (str): 지수 코드 (예: .DJI=다우지수, .IXIC=나스닥지수, .SPX=S&P500)
    
    주요 지수 코드:
    - .DJI: 다우 존스 산업평균지수 (Dow Jones)
    - .IXIC: 나스닥 종합지수 (NASDAQ Composite)  
    - .SPX: S&P 500 지수
    - .HSI: 항셍지수 (홍콩)
    - .N225: 닛케이225 (일본)
    """
    try:
        # 해외 지수는 현재가 API가 별도로 없어서 차트 API의 최신 데이터를 사용
        from datetime import datetime, timedelta
        
        # 최근 5일간의 데이터를 조회해서 최신 지수 정보를 가져옴
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=5)).strftime("%Y%m%d")
        
        output1, output2 = inquire_daily_chartprice(
            fid_cond_mrkt_div_code="N",  # 해외지수
            fid_input_iscd=index_code,
            fid_input_date_1=start_date,
            fid_input_date_2=end_date,
            fid_period_div_code="D",  # 일봉
            env_dv="real"
        )
        
        if output1.empty and output2.empty:
            raise HTTPException(status_code=404, detail="해외 지수 데이터를 찾을 수 없습니다")
        
        # 최신 데이터 선택 (output2의 첫 번째 항목이 최신)
        latest_data = {}
        if not output2.empty:
            latest_row = output2.iloc[0]  # 최신 데이터
            latest_data = {
                "index_code": index_code,
                "exchange": exchange,
                "current_price": latest_row.get("ovrs_nmix_prpr", ""),
                "open_price": latest_row.get("ovrs_nmix_oprc", ""),
                "high_price": latest_row.get("ovrs_nmix_hgpr", ""),
                "low_price": latest_row.get("ovrs_nmix_lwpr", ""),
                "volume": latest_row.get("acml_vol", ""),
                "date": latest_row.get("stck_bsop_date", ""),
                "change": "0.00",  # 지수 변화율은 별도 계산 필요
                "change_rate": "0.00"
            }
            
            # 전일 대비 계산 (2개 이상 데이터가 있을 때)
            if len(output2) > 1:
                current_price = float(latest_row.get("ovrs_nmix_prpr", "0"))
                prev_price = float(output2.iloc[1].get("ovrs_nmix_prpr", "0"))
                if prev_price > 0:
                    change = current_price - prev_price
                    change_rate = (change / prev_price) * 100
                    latest_data["change"] = f"{change:.2f}"
                    latest_data["change_rate"] = f"{change_rate:.2f}"
        
        # output1 정보도 추가
        if not output1.empty:
            info_data = output1.iloc[0]
            latest_data.update({
                "korean_name": info_data.get("hts_kor_isnm", ""),
                "market_cap": info_data.get("acml_vol", "")
            })
        
        return {
            "rt_cd": "0",
            "msg_cd": "MCA00000", 
            "msg1": "정상처리 되었습니다",
            "output": latest_data
        }
        
    except Exception as e:
        logger.error(f"해외 지수 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/overseas/{exchange}/index/{index_code}/chart")
async def get_overseas_index_chart(
    exchange: str,
    index_code: str,
    period: str = "D",
    start_date: str = "20240101", 
    end_date: str = "20250203"
):
    """해외 지수 차트 조회 (일/주/월/년봉 지원)
    
    Args:
        exchange (str): 거래소 코드 (NAS, NYS, etc.)
        index_code (str): 지수 코드 (예: .DJI, .IXIC, .SPX)
        period (str): 기간 구분 (D:일봉, W:주봉, M:월봉, Y:년봉)
        start_date (str): 조회 시작일 (YYYYMMDD)
        end_date (str): 조회 종료일 (YYYYMMDD)
    """
    try:
        # 기간 검증
        period_map = {"D": "D", "W": "W", "M": "M", "Y": "Y"}
        if period not in period_map:
            raise HTTPException(status_code=400, detail="period는 D(일봉), W(주봉), M(월봉), Y(년봉) 중 하나여야 합니다")
        
        # 해외 지수 차트는 기존 차트 API와 동일한 로직
        fid_cond_mrkt_div_code = "N"  # N: 해외지수
        
        # 날짜 범위 계산
        start = datetime.strptime(start_date, "%Y%m%d")
        end = datetime.strptime(end_date, "%Y%m%d")
        days_diff = (end - start).days
        
        # 자동 분할 조회 로직
        if period == "D" and days_diff > 90:
            date_ranges = get_date_ranges(start_date, end_date, 90)
            
            all_output1 = None
            all_output2 = pd.DataFrame()
            
            for range_start, range_end in date_ranges:
                try:
                    output1, output2 = inquire_daily_chartprice(
                        fid_cond_mrkt_div_code=fid_cond_mrkt_div_code,
                        fid_input_iscd=index_code,
                        fid_input_date_1=range_start,
                        fid_input_date_2=range_end,
                        fid_period_div_code=period,
                        env_dv="real"
                    )
                    
                    if all_output1 is None and not output1.empty:
                        all_output1 = output1
                    
                    if not output2.empty:
                        all_output2 = pd.concat([all_output2, output2], ignore_index=True)
                    
                    import time
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"부분 조회 실패 ({range_start}-{range_end}): {str(e)}")
                    continue
            
            if all_output2.empty:
                raise HTTPException(status_code=404, detail="해외 지수 차트 데이터를 찾을 수 없습니다")
            
            # 날짜순 정렬
            if 'stck_bsop_date' in all_output2.columns:
                all_output2 = all_output2.sort_values('stck_bsop_date').reset_index(drop=True)
            
            return {
                "rt_cd": "0",
                "msg_cd": "MCA00000",
                "msg1": "정상처리 되었습니다",
                "output1": all_output1.to_dict(orient="records")[0] if all_output1 is not None and not all_output1.empty else {},
                "output2": all_output2.to_dict(orient="records"),
                "total_records": len(all_output2),
                "period": period,
                "date_range": f"{start_date}~{end_date}",
                "exchange": exchange,
                "index_code": index_code
            }
            
        else:
            # 단일 조회
            output1, output2 = inquire_daily_chartprice(
                fid_cond_mrkt_div_code=fid_cond_mrkt_div_code,
                fid_input_iscd=index_code,
                fid_input_date_1=start_date,
                fid_input_date_2=end_date,
                fid_period_div_code=period,
                env_dv="real"
            )
            
            if output1.empty and output2.empty:
                raise HTTPException(status_code=404, detail="해외 지수 차트 데이터를 찾을 수 없습니다")
            
            return {
                "rt_cd": "0",
                "msg_cd": "MCA00000",
                "msg1": "정상처리 되었습니다",
                "output1": output1.to_dict(orient="records")[0] if not output1.empty else {},
                "output2": output2.to_dict(orient="records") if not output2.empty else [],
                "total_records": len(output2) if not output2.empty else 0,
                "period": period,
                "date_range": f"{start_date}~{end_date}",
                "exchange": exchange,
                "index_code": index_code
            }
        
    except Exception as e:
        logger.error(f"해외 지수 차트 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )