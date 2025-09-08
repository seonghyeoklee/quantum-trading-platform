"""
KIS Adapter FastAPI Server
차트 데이터 제공을 위한 REST API 서버

Author: Quantum Trading Platform
"""
import sys
import logging
from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Any
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import pandas as pd
import asyncio
import json
from typing import Set

# examples_llm 경로 추가
sys.path.extend(['examples_llm', '.', 'examples_user'])
import kis_auth as ka

# KIS API 함수들 import
from domestic_stock.inquire_daily_itemchartprice.inquire_daily_itemchartprice import inquire_daily_itemchartprice
from domestic_stock.inquire_price.inquire_price import inquire_price
from domestic_stock.inquire_index_price.inquire_index_price import inquire_index_price
from domestic_stock.top_interest_stock.top_interest_stock import top_interest_stock
from domestic_stock.chk_holiday.chk_holiday import chk_holiday

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

def validate_real_data(data: Any, data_type: str = "stock") -> bool:
    """
    실제 데이터인지 검증하는 함수
    더미/Mock 데이터 생성을 절대 방지
    """
    if data is None:
        return False
    
    if isinstance(data, pd.DataFrame):
        if data.empty:
            return False
        
        # 주식 데이터의 경우 필수 필드 존재 확인
        if data_type == "stock":
            required_fields = ['stck_prpr']  # 현재가
            if not all(field in data.columns for field in required_fields):
                return False
                
        # 데이터 타입별 값 검증
        if data_type == "stock":
            # 현재가가 0보다 커야 함
            if 'stck_prpr' in data.columns:
                current_price = pd.to_numeric(data['stck_prpr'].iloc[0], errors='coerce')
                if pd.isna(current_price) or current_price <= 0:
                    return False
        
        elif data_type == "overseas_price":
            # 해외 주식 현재가 필드 확인 (KIS API 기준)
            price_fields = ['last', 'curr', 'price', 'pvol', 'base', 'ovrs_nmix_prpr']  # 가능한 가격 필드들
            has_price_field = any(field in data.columns for field in price_fields)
            
            if not has_price_field:
                return False
                
            # 첫 번째로 발견되는 가격 필드 검증
            for field in price_fields:
                if field in data.columns:
                    price_value = pd.to_numeric(data[field].iloc[0], errors='coerce')
                    if pd.isna(price_value) or price_value <= 0:
                        return False
                    break  # 하나라도 유효하면 통과
                    
        elif data_type == "chart":
            # OHLC 데이터 기본 검증
            ohlc_fields = ['open', 'high', 'low', 'close', 'stck_oprc', 'stck_hgpr', 'stck_lwpr', 'stck_clpr']
            has_ohlc = any(field in data.columns for field in ohlc_fields)
            
            if not has_ohlc:
                return False
                
            # 가격 데이터가 양수인지 확인
            for field in ohlc_fields:
                if field in data.columns:
                    price_value = pd.to_numeric(data[field].iloc[0], errors='coerce')
                    if pd.isna(price_value) or price_value <= 0:
                        return False
    
    elif isinstance(data, dict):
        # 응답 코드가 성공인지 확인
        if 'rt_cd' in data and data['rt_cd'] != '0':
            return False
    
    return True

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

# 토큰 재발행 API
@app.post("/auth/refresh-token")
async def refresh_token(
    environment: str = "prod"  # prod(실전) 또는 vps(모의)
):
    """KIS API 토큰 재발행
    
    Args:
        environment (str): 환경 설정 (prod: 실전, vps: 모의)
    
    Returns:
        Dict: 토큰 재발행 결과
    """
    import os
    from datetime import datetime
    
    try:
        # 기존 토큰 캐시 파일 삭제
        token_file = os.path.join(
            os.path.expanduser("~"), 
            "KIS", 
            "config", 
            f"KIS{datetime.today().strftime('%Y%m%d')}"
        )
        if os.path.exists(token_file):
            os.remove(token_file)
            logger.info(f"기존 토큰 캐시 파일 삭제: {token_file}")
        
        # 새 토큰 발행
        if environment.lower() == "prod":
            ka.auth(svr="prod", product="01")
            env_name = "실전(LIVE)"
        elif environment.lower() == "vps":
            ka.auth(svr="vps", product="01")
            env_name = "모의(SANDBOX)"
        else:
            raise HTTPException(
                status_code=400, 
                detail="environment는 'prod' 또는 'vps'만 가능합니다"
            )
        
        logger.info(f"✅ {env_name} 토큰 재발행 성공")
        
        # 토큰 유효기간 확인
        valid_date = None
        if os.path.exists(token_file):
            with open(token_file, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if 'valid-date' in line:
                        valid_date = line.split(':')[1].strip()
                        break
        
        return {
            "status": "success",
            "message": f"{env_name} 토큰 재발행 완료",
            "environment": environment,
            "valid_until": valid_date,
            "note": "토큰은 6시간 유효, 1분당 1회만 발급 가능"
        }
        
    except Exception as e:
        logger.error(f"토큰 재발행 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"토큰 재발행 실패: {str(e)}")

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
        
        # 실제 데이터 검증 - 절대 가짜 데이터를 생성하지 않음
        if not validate_real_data(result, "stock"):
            logger.error(f"Invalid or empty data received for symbol: {symbol}")
            raise HTTPException(
                status_code=502, 
                detail=f"외부 API에서 유효하지 않은 데이터를 받았습니다. 종목코드: {symbol}"
            )

        # pandas DataFrame을 dict로 변환
        return {
            "rt_cd": "0",
            "msg_cd": "MCA00000",
            "msg1": "정상처리 되었습니다",
            "output": result.to_dict(orient="records")[0],
            "data_source": "KIS_API_REAL",  # 데이터 출처 명시
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        # HTTPException은 그대로 전달
        raise
    except Exception as e:
        logger.error(f"국내 현재가 조회 오류: {str(e)}")
        # 절대 성공으로 위장하거나 더미 데이터를 반환하지 않음
        raise HTTPException(status_code=500, detail=f"KIS API 호출 실패: {str(e)}")

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
    end_date: str = None,
    adj_price: str = "1"  # 0:수정주가, 1:원주가
):
    """국내 주식 차트 조회 (일/주/월/년봉 지원, 자동 분할 조회)"""
    try:
        # end_date가 None이면 오늘 날짜로 설정
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
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

@app.get("/domestic/ranking/top-interest-stock")
async def get_top_interest_stock(
    market_code: str = "0000",  # 0000:전체, 0001:거래소, 1001:코스닥, 2001:코스피200
    div_cls_code: str = "0",    # 0:전체, 1:관리종목, 2:투자주의, 3:투자경고, 4:투자위험예고, 5:투자위험, 6:보통주, 7:우선주
    start_rank: str = "1"       # 순위검색 시작값 (1:1위부터, 10:10위부터)
):
    """국내 주식 관심종목 등록 상위 조회
    
    Args:
        market_code (str): 시장 구분 (0000:전체, 0001:거래소, 1001:코스닥, 2001:코스피200)
        div_cls_code (str): 분류 구분 (0:전체, 1:관리종목, 2:투자주의, 3:투자경고, 4:투자위험예고, 5:투자위험, 6:보통주, 7:우선주)
        start_rank (str): 순위 시작값 (1:1위부터, 10:10위부터)
    
    Returns:
        Dict: 관심종목 등록 상위 데이터
    """
    try:
        logger.info(f"관심종목 조회 시작 - market_code: {market_code}")
        
        # API 호출
        logger.info("top_interest_stock API 호출 시작")
        result = top_interest_stock(
            fid_input_iscd_2="000000",  # 필수값
            fid_cond_mrkt_div_code="J",  # 조건 시장 분류 코드 (주식: J)
            fid_cond_scr_div_code="20180",  # 조건 화면 분류 코드 (Unique key)
            fid_input_iscd=market_code,  # 입력 종목코드
            fid_trgt_cls_code="0",  # 대상 구분 코드 (전체)
            fid_trgt_exls_cls_code="0",  # 대상 제외 구분 코드 (전체)
            fid_input_price_1="0",  # 입력 가격1 (전체)
            fid_input_price_2="0",  # 입력 가격2 (전체)
            fid_vol_cnt="0",  # 거래량 수 (전체)
            fid_div_cls_code=div_cls_code,  # 분류 구분 코드
            fid_input_cnt_1=start_rank  # 입력 수1
        )
        
        logger.info(f"API 호출 완료 - result type: {type(result)}, empty: {result is None or (hasattr(result, 'empty') and result.empty)}")
        
        if result is None or result.empty:
            logger.warning("조회된 관심종목 데이터가 없습니다.")
            return create_success_response(
                data=[],
                message="조회된 관심종목 데이터가 없습니다."
            )
        
        logger.info(f"조회 성공 - 데이터 건수: {len(result)}")
        return create_success_response(
            data=result.to_dict(orient="records"),
            message="관심종목 등록 상위 조회 완료"
        )
        
    except ValueError as ve:
        logger.error(f"파라미터 오류: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"관심종목 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/domestic/holiday")
async def get_domestic_holiday(bass_dt: str):
    """국내 휴장일 조회
    
    Args:
        bass_dt (str): 기준일자 (YYYYMMDD)
        
    Returns:
        Dict: 국내 휴장일 정보
        
    Note:
        KIS API 원장서비스와 연관되어 1일 1회 호출 권장
        영업일, 거래일, 개장일, 결제일 여부를 포함한 정보 반환
    """
    try:
        logger.info(f"국내 휴장일 조회 시작 - bass_dt: {bass_dt}")
        
        # 날짜 형식 검증
        if not bass_dt or len(bass_dt) != 8:
            raise HTTPException(status_code=400, detail="bass_dt는 YYYYMMDD 형식(8자리)이어야 합니다")
        
        try:
            # 날짜 유효성 검사
            datetime.strptime(bass_dt, "%Y%m%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="유효하지 않은 날짜 형식입니다. YYYYMMDD 형식으로 입력해주세요")
        
        # API 호출
        logger.info("chk_holiday API 호출 시작")
        result = chk_holiday(bass_dt=bass_dt)
        
        logger.info(f"API 호출 완료 - result type: {type(result)}")
        
        if result is None or result.empty:
            logger.warning(f"조회된 휴장일 데이터가 없습니다. bass_dt: {bass_dt}")
            return create_success_response(
                data=[],
                message="조회된 휴장일 데이터가 없습니다."
            )
        
        logger.info(f"휴장일 조회 성공 - 데이터 건수: {len(result)}")
        return create_success_response(
            data=result.to_dict(orient="records"),
            message="국내 휴장일 조회 완료"
        )
        
    except HTTPException:
        raise
    except ValueError as ve:
        logger.error(f"파라미터 오류: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"국내 휴장일 조회 오류: {str(e)}")
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
    end_date: str = None
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
        # end_date가 None이면 오늘 날짜로 설정
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
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
    end_date: str = None
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
        # end_date가 None이면 오늘 날짜로 설정
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
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

# WebSocket 연결 관리
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.kis_ws = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket 연결됨: {len(self.active_connections)}개 활성")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket 연결해제: {len(self.active_connections)}개 활성")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        
        message_str = json.dumps(message, ensure_ascii=False)
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except:
                disconnected.add(connection)
        
        for connection in disconnected:
            self.disconnect(connection)

    async def start_kis_realtime_polling(self):
        """KIS REST API를 통한 실시간 데이터 폴링 (하이브리드 방식)"""
        if hasattr(self, 'polling_task') and self.polling_task is not None:
            return
            
        try:
            async def poll_kis_data():
                """KIS REST API에서 실시간 데이터 폴링"""
                # 모니터링할 종목 리스트 (국내 주식)
                domestic_symbols = {
                    "005930": "삼성전자",
                    "000660": "SK하이닉스", 
                    "035420": "NAVER",
                    "035720": "카카오",
                    "051910": "LG화학",
                    "006400": "삼성SDI"
                }
                
                while True:
                    try:
                        for symbol, name in domestic_symbols.items():
                            # 현재가 조회
                            try:
                                result = inquire_price(
                                    env_dv="real",
                                    fid_cond_mrkt_div_code="J",
                                    fid_input_iscd=symbol
                                )
                                
                                if not result.empty:
                                    row = result.iloc[0]
                                    
                                    # 실시간 호가 데이터 포맷
                                    quote_data = {
                                        "type": "realtime_data",
                                        "tr_id": "HDFSASP0",  # 실시간 호가
                                        "data": {
                                            "symb": symbol,
                                            "name": name,
                                            "pbid1": str(row.get('stck_bspr', 0)),  # 매수호가
                                            "pask1": str(row.get('stck_sdpr', 0)),  # 매도호가
                                            "vbid1": str(row.get('bidp_rsqn', 0)),  # 매수잔량
                                            "vask1": str(row.get('askp_rsqn', 0)),  # 매도잔량
                                            "prpr": str(row.get('stck_prpr', 0)),   # 현재가
                                            "prdy_vrss": str(row.get('prdy_vrss', 0)), # 전일대비
                                            "prdy_vrss_sign": str(row.get('prdy_vrss_sign', 0)), # 전일대비부호
                                            "prdy_ctrt": str(row.get('prdy_ctrt', 0)), # 전일대비율
                                            "acml_vol": str(row.get('acml_vol', 0)),   # 누적거래량
                                            "acml_tr_pbmn": str(row.get('acml_tr_pbmn', 0)) # 누적거래대금
                                        },
                                        "timestamp": datetime.now().isoformat()
                                    }
                                    
                                    # 브로드캐스트
                                    await self.broadcast(quote_data)
                                    
                                    logger.info(f"📊 실시간 데이터 전송: {name}({symbol}) - 현재가: {row.get('stck_prpr', 0)}")
                                    
                            except Exception as e:
                                logger.error(f"종목 {symbol} 조회 실패: {str(e)}")
                            
                            await asyncio.sleep(0.2)  # API 호출 제한 고려
                        
                        # 1초마다 전체 종목 갱신
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"실시간 데이터 폴링 오류: {str(e)}")
                        await asyncio.sleep(1)
            
            # 백그라운드 태스크로 실행
            self.polling_task = asyncio.create_task(poll_kis_data())
            logger.info("✅ KIS 실시간 데이터 폴링 시작")
            
        except Exception as e:
            logger.error(f"실시간 데이터 폴링 시작 오류: {str(e)}")
    
    # 가짜 데이터 생성 함수 제거됨 - 데이터 무결성 보장을 위해 완전히 제거
    # 오직 실제 KIS API 데이터만 사용하도록 강제

manager = ConnectionManager()

@app.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """실시간 데이터 WebSocket 엔드포인트"""
    await manager.connect(websocket)
    
    # KIS 실시간 데이터 폴링 시작 (실제 데이터만 사용)
    if not hasattr(manager, 'polling_task') or manager.polling_task is None:
        asyncio.create_task(manager.start_kis_realtime_polling())
    
    # 가짜 데이터 생성 함수는 완전히 제거됨 - 데이터 무결성 보장
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신 (연결 유지용)
            data = await websocket.receive_text()
            
            # 핑/퐁 또는 구독 요청 처리
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                elif message.get("type") == "subscribe":
                    # 구독 요청 처리 (데모에서는 로그만 출력)
                    symbol = message.get("symbol", "")
                    logger.info(f"📊 종목 구독 요청: {symbol}")
                elif message.get("type") == "unsubscribe":
                    # 구독 해제 요청 처리
                    symbol = message.get("symbol", "")
                    logger.info(f"📊 종목 구독 해제: {symbol}")
            except:
                pass  # JSON이 아닌 메시지는 무시
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )