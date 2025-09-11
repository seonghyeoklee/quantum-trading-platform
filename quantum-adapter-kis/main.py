"""
KIS Adapter FastAPI Server
차트 데이터 제공을 위한 REST API 서버

Author: Quantum Trading Platform
"""
import sys
import logging
from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import pandas as pd
import asyncio
import json
from typing import Set
import jwt
import base64

# 로깅 설정 먼저 초기화
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# examples_llm 경로 추가
sys.path.extend(['examples_llm', '.', 'examples_user'])
import kis_auth as ka

# DB 토큰 관리자 import (PostgreSQL 직접 연결)
try:
    from db_token_manager import get_kis_token_from_db, get_token_status_from_db, is_db_available
    DB_AVAILABLE = is_db_available()
    if DB_AVAILABLE:
        logger.info("✅ DB 토큰 관리자 성공적으로 로드됨 - PostgreSQL 직접 연결 사용")
    else:
        logger.warning("⚠️ DB 연결 실패 - 파일 기반 폴백 사용")
except ImportError as e:
    logger.warning(f"DB 토큰 관리자 import 실패: {e} - 파일 기반 폴백 사용")
    get_kis_token_from_db = None
    get_token_status_from_db = None
    DB_AVAILABLE = False

# 사용하지 않는 backend_client import 제거 (직접 DB 접근 사용)

# 기본 JWT 토큰 (admin 사용자용 - 실제 백엔드에서 발급받은 토큰)
DEFAULT_ADMIN_TOKEN = "Bearer eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJhZG1pbkBxdWFudHVtLmxvY2FsIiwibmFtZSI6IlF1YW50dW0gQWRtaW4iLCJyb2xlcyI6WyJVU0VSIiwiVFJBREVSIiwiQURNSU4iXSwiaWF0IjoxNzU3NDIyOTU4LCJleHAiOjE3NTc1MDkzNTh9.RYMs-UZ0tKQczfUWqZ8oSnMXvKM-yfWoRzGH8OFroGLUq8y0rLKMHrlttaCi8g5AyZ7F6FwDK9aUpf-QdjrOnQ"

def extract_user_id_from_jwt(authorization: str) -> int:
    """
    JWT 토큰에서 사용자 ID를 추출합니다.
    
    Args:
        authorization: "Bearer <jwt_token>" 형식의 인증 헤더
        
    Returns:
        사용자 ID (기본값: 1)
    """
    try:
        if not authorization or not authorization.startswith("Bearer "):
            logger.warning("Invalid authorization header format")
            return 1
            
        token = authorization.replace("Bearer ", "")
        
        # JWT 서명 검증 없이 payload만 디코딩 (백엔드에서 이미 검증된 토큰)
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        user_id = int(decoded.get("sub", 1))
        logger.debug(f"Extracted user_id: {user_id} from JWT")
        return user_id
        
    except Exception as e:
        logger.warning(f"Failed to extract user_id from JWT: {e}, using default user_id=1")
        return 1

# KIS 인증 컨텍스트 설정을 위한 헬퍼 함수
def setup_auth_context(authorization: str = None, environment: str = "prod"):
    """KIS 인증 컨텍스트를 설정합니다."""
    # Authorization이 없으면 기본 admin 토큰 사용
    if not authorization:
        authorization = DEFAULT_ADMIN_TOKEN
        logger.info("No authorization provided, using default admin token for DB access")
    
    # set_auth_context 함수가 있는지 확인하고 호출
    try:
        # 함수 존재 여부 확인 및 호출
        if hasattr(ka, 'set_auth_context'):
            ka.set_auth_context(authorization, environment)
            logger.info(f"✅ Auth context set successfully for environment: {environment}")
            return True
        else:
            # 함수가 없으면 직접 전역 변수 설정 시도
            if hasattr(ka, '_current_authorization'):
                ka._current_authorization = authorization
                ka._current_environment = environment
                logger.info(f"✅ Auth context set directly via global variables for environment: {environment}")
                return True
            else:
                logger.warning("⚠️ Neither set_auth_context function nor global variables available, using file-based fallback")
                return False
    except Exception as e:
        logger.error(f"❌ Error setting auth context: {e}")
        return False
        
def ensure_kis_auth(authorization: str = None, environment: str = "prod"):
    """KIS 인증을 보장합니다 (DB 기반 → 파일 폴백)"""
    setup_auth_context(authorization, environment)
    
    # DB 기반 토큰 조회 시도 (사용자별)
    if DB_AVAILABLE and get_kis_token_from_db:
        user_id = extract_user_id_from_jwt(authorization)
        db_token = get_kis_token_from_db(user_id=user_id, environment=environment)
        if db_token:
            logger.info(f"✅ DB에서 사용자 {user_id}의 토큰 조회 성공 - {environment}")
            return db_token
        else:
            logger.warning(f"⚠️ DB에서 사용자 {user_id}의 토큰 조회 실패 - {environment}")
    
    # 파일 기반 fallback
    token = ka.read_token()
    if not token:
        # 토큰이 없으면 새로 발급
        logger.info(f"No valid token found, requesting new token for {environment}")
        ka.auth(svr=environment, product="01")
        token = ka.read_token()
    else:
        logger.info(f"Valid file-based token found for {environment}")
    return token

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

# 로깅 설정은 상단에서 이미 완료됨

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
    """서버 시작시 KIS API 인증 토큰 발급 (파일 기반 폴백)"""
    try:
        # 서버 시작시에는 authorization header가 없으므로 파일 기반으로 인증
        ka.auth(svr="prod", product="01")  # 실전 계좌 인증
        logger.info("✅ KIS API 파일 기반 인증 성공 (DB 기반 인증은 요청시 처리)")
    except Exception as e:
        logger.error(f"❌ KIS API 파일 기반 인증 실패: {str(e)}")
        logger.info("DB 기반 인증은 각 요청에서 authorization header와 함께 처리됩니다.")

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
async def get_domestic_price(symbol: str, authorization: str = Header(None)):
    """국내 주식 현재가 조회"""
    try:
        # 인증 컨텍스트 설정
        ensure_kis_auth(authorization, "prod")
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
    authorization: str = Header(None),
    period: str = "D",  # D:일봉, W:주봉, M:월봉, Y:년봉
    start_date: str = "20240101",
    end_date: str = None,
    adj_price: str = "1"  # 0:수정주가, 1:원주가
):
    """국내 주식 차트 조회 (일/주/월/년봉 지원, 자동 분할 조회)"""
    try:
        # KIS 인증 컨텍스트 설정 및 토큰 확인
        ensure_kis_auth(authorization, "prod")
        
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
async def get_domestic_index(index_code: str, authorization: str = Header(None)):
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
    authorization: str = Header(None),
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
async def get_domestic_holiday(bass_dt: str, authorization: str = Header(None)):
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
async def get_overseas_price(exchange: str, symbol: str, authorization: str = Header(None)):
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
    authorization: str = Header(None),
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
async def get_overseas_index(exchange: str, index_code: str, authorization: str = Header(None)):
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
    authorization: str = Header(None),
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

# ==================== 디노테스트 API ====================

class DinoTestFinanceResponse(BaseModel):
    """디노테스트 재무 점수 응답 모델"""
    stock_code: str = Field(..., description="종목 코드")
    stock_name: str = Field(default="", description="종목명")
    total_score: int = Field(..., description="총 재무 점수 (0~5점)")
    score_details: Dict[str, Any] = Field(..., description="점수 상세 내역")
    raw_data: Dict[str, Any] = Field(..., description="계산에 사용된 원본 재무 데이터")
    
    class Config:
        schema_extra = {
            "example": {
                "stock_code": "005930",
                "stock_name": "삼성전자",
                "total_score": 3,
                "score_details": {
                    "revenue_growth_score": 1,
                    "operating_profit_score": 0,
                    "operating_margin_score": 1,
                    "retained_earnings_ratio_score": 1,
                    "debt_ratio_score": -1,
                    "revenue_growth_rate": 12.5,
                    "operating_profit_transition": "흑자 지속",
                    "operating_margin_rate": 15.2,
                    "retained_earnings_ratio": 1200.0,
                    "debt_ratio": 85.5
                }
            }
        }

@app.get("/dino-test/finance/{stock_code}", response_model=DinoTestFinanceResponse)
async def calculate_dino_test_finance_score(
    stock_code: str,
    authorization: str = Header(None)
):
    """
    디노테스트 재무 영역 점수 계산
    
    재무 영역 5개 지표를 평가하여 0~5점 범위에서 점수를 산출합니다:
    1. 매출액 증감 (±1점)
    2. 영업이익 상태 (±2점) 
    3. 영업이익률 (+1점)
    4. 유보율 (±1점)
    5. 부채비율 (±1점)
    
    최종 점수: MAX(0, MIN(5, 2 + SUM(개별지표점수들)))
    
    Args:
        stock_code: 종목코드 (예: '005930')
        
    Returns:
        DinoTestFinanceResponse: 재무 점수 계산 결과
    """
    try:
        logger.info(f"=== 디노테스트 재무 점수 계산 시작: {stock_code} ===")
        
        # 종목코드 검증
        if not stock_code or len(stock_code) != 6:
            raise HTTPException(
                status_code=400,
                detail="종목코드는 6자리 숫자여야 합니다 (예: 005930)"
            )
        
        # DB 토큰 확인
        user_id = extract_user_id_from_jwt(authorization or DEFAULT_ADMIN_TOKEN)
        environment = "LIVE"  # 디노테스트는 실제 데이터만 사용
        
        if DB_AVAILABLE:
            token = get_kis_token_from_db(user_id, "prod")
            if not token:
                raise HTTPException(
                    status_code=401,
                    detail="KIS API 토큰이 없습니다. 토큰을 먼저 발급받아주세요."
                )
        
        # KIS API 인증 설정
        ka.auth(svr="prod", product="01")
        logger.info(f"KIS API 인증 완료 - 사용자: {user_id}, 환경: {environment}")
        
        # 재무 데이터 수집
        from dino_test.finance_data_collector import FinanceDataCollector
        data_collector = FinanceDataCollector()
        
        finance_data = data_collector.parse_finance_data(stock_code)
        if finance_data is None:
            raise HTTPException(
                status_code=404,
                detail=f"종목 {stock_code}의 재무 데이터를 찾을 수 없습니다"
            )
        
        # 점수 계산
        from dino_test.finance_scorer import DinoTestFinanceScorer
        scorer = DinoTestFinanceScorer()
        
        score_detail = scorer.calculate_total_finance_score(finance_data)
        
        # 종목명 조회 (optional)
        stock_name = ""
        try:
            # inquire_price API로 종목명 조회
            price_result = inquire_price(
                env_dv="real",
                fid_cond_mrkt_div_code="J",
                fid_input_iscd=stock_code
            )
            if not price_result.empty:
                stock_name = price_result.iloc[0].get("hts_kor_isnm", "")
        except:
            pass  # 종목명 조회 실패해도 점수 계산에는 영향 없음
        
        # 응답 데이터 구성
        response_data = DinoTestFinanceResponse(
            stock_code=stock_code,
            stock_name=stock_name,
            total_score=score_detail.total_score,
            score_details={
                "revenue_growth_score": score_detail.revenue_growth_score,
                "operating_profit_score": score_detail.operating_profit_score,
                "operating_margin_score": score_detail.operating_margin_score,
                "retained_earnings_ratio_score": score_detail.retained_earnings_ratio_score,
                "debt_ratio_score": score_detail.debt_ratio_score,
                "revenue_growth_rate": score_detail.revenue_growth_rate,
                "operating_profit_transition": score_detail.operating_profit_transition,
                "operating_margin_rate": score_detail.operating_margin_rate,
                "retained_earnings_ratio": score_detail.retained_earnings_ratio,
                "debt_ratio": score_detail.debt_ratio
            },
            raw_data={
                "기준기간": f"{score_detail.current_period} vs {score_detail.previous_period}",
                "당년매출액": f"{float(score_detail.current_revenue):,.0f}억원" if score_detail.current_revenue else None,
                "전년매출액": f"{float(score_detail.previous_revenue):,.0f}억원" if score_detail.previous_revenue else None,
                "당년영업이익": f"{float(score_detail.current_operating_profit):,.0f}억원" if score_detail.current_operating_profit else None,
                "전년영업이익": f"{float(score_detail.previous_operating_profit):,.0f}억원" if score_detail.previous_operating_profit else None,
                "총부채": f"{float(score_detail.total_debt):,.0f}억원" if score_detail.total_debt else None,
                "자기자본": f"{float(score_detail.total_equity):,.0f}억원" if score_detail.total_equity else None,
                "이익잉여금": f"{float(score_detail.retained_earnings):,.0f}억원" if score_detail.retained_earnings else None,
                "자본금": f"{float(score_detail.capital_stock):,.0f}억원" if score_detail.capital_stock else None
            }
        )
        
        logger.info(f"=== 디노테스트 재무 점수 계산 완료: {stock_code} - {score_detail.total_score}점 ===")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"디노테스트 재무 점수 계산 오류 - {stock_code}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dino-test/finance-batch")
async def calculate_dino_test_finance_batch(
    stock_codes: str,  # 쉼표로 구분된 종목코드들 (예: "005930,000660,035420")
    authorization: str = Header(None)
):
    """
    디노테스트 재무 점수 배치 계산
    
    여러 종목에 대해 일괄적으로 재무 점수를 계산합니다.
    
    Args:
        stock_codes: 쉼표로 구분된 종목코드들 (예: "005930,000660,035420")
        
    Returns:
        Dict: 배치 계산 결과
    """
    try:
        logger.info(f"=== 디노테스트 재무 점수 배치 계산 시작: {stock_codes} ===")
        
        # 종목코드 파싱
        codes = [code.strip() for code in stock_codes.split(",") if code.strip()]
        if not codes:
            raise HTTPException(status_code=400, detail="종목코드가 제공되지 않았습니다")
        
        if len(codes) > 20:  # 배치 처리 제한
            raise HTTPException(status_code=400, detail="한 번에 최대 20개 종목까지 처리 가능합니다")
        
        results = []
        errors = []
        
        for code in codes:
            try:
                # 개별 종목 점수 계산
                result = await calculate_dino_test_finance_score(code, authorization)
                results.append(result.dict())
                
            except HTTPException as e:
                errors.append({
                    "stock_code": code,
                    "error": e.detail,
                    "status_code": e.status_code
                })
            except Exception as e:
                errors.append({
                    "stock_code": code,
                    "error": str(e),
                    "status_code": 500
                })
        
        # 성공한 결과들에 대한 통계
        if results:
            scores = [r["total_score"] for r in results]
            statistics = {
                "count": len(results),
                "average_score": round(sum(scores) / len(scores), 2),
                "max_score": max(scores),
                "min_score": min(scores),
                "passing_count": len([s for s in scores if s >= 3])  # 3점 이상을 통과로 가정
            }
        else:
            statistics = {"count": 0}
        
        logger.info(f"=== 디노테스트 배치 계산 완료: 성공 {len(results)}건, 실패 {len(errors)}건 ===")
        
        return {
            "success": True,
            "message": f"배치 계산 완료 - 성공: {len(results)}건, 실패: {len(errors)}건",
            "statistics": statistics,
            "results": results,
            "errors": errors,
            "total_requested": len(codes)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"디노테스트 배치 계산 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================================================================================
# 디노테스트 - 기술 영역 API
# ================================================================================================

class DinoTestTechnicalResponse(BaseModel):
    """디노테스트 기술분석 응답 모델"""
    success: bool = Field(..., description="성공 여부")
    stock_code: str = Field(..., description="종목코드")
    stock_name: str = Field(default="", description="종목명")
    total_score: int = Field(..., description="기술분석 총점 (0~5점)")
    obv_score: int = Field(..., description="OBV 점수 (-1, 0, 1)")
    rsi_score: int = Field(..., description="RSI 점수 (-1, 0, 1)")
    sentiment_score: int = Field(..., description="투자심리 점수 (-1, 0, 1)")
    other_indicator_score: int = Field(..., description="기타지표 점수 (-1, 0, 1)")
    obv_status: str = Field(default="", description="OBV 상태")
    rsi_value: float = Field(default=0.0, description="RSI 값")
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="계산 근거 데이터")
    message: str = Field(default="", description="메시지")

@app.get("/dino-test/technical/{stock_code}", response_model=DinoTestTechnicalResponse)
async def calculate_dino_test_technical_score(
    stock_code: str,
    authorization: str = Header(default=DEFAULT_ADMIN_TOKEN)
):
    """
    디노테스트 기술분석 점수 계산
    
    Args:
        stock_code: 종목코드 (예: 005930)
        authorization: JWT 인증 토큰
    
    Returns:
        DinoTestTechnicalResponse: 기술분석 결과
    """
    logger.info(f"=== 디노테스트 기술분석 시작: {stock_code} ===")
    
    try:
        # JWT에서 사용자 ID 추출
        user_id = extract_user_id_from_jwt(authorization)
        logger.info(f"요청 사용자 ID: {user_id}")
        
        # KIS 인증 확인
        if DB_AVAILABLE:
            # DB에서 토큰 조회
            token_info = get_kis_token_from_db(user_id, "LIVE")
            if not token_info:
                logger.warning(f"DB에서 KIS 토큰 조회 실패 - user_id: {user_id}")
                # 파일 기반 폴백
                ka.auth(svr="prod", product="01")
                logger.info("파일 기반 KIS 인증 성공")
            else:
                logger.info(f"DB 기반 KIS 토큰 사용 - expires_at: {token_info.get('expires_at')}")
        else:
            # 파일 기반 인증
            ka.auth(svr="prod", product="01")
            logger.info("파일 기반 KIS 인증 성공")
        
        # 기술분석 데이터 수집 및 점수 계산
        from dino_test.technical_data_collector import TechnicalDataCollector
        from dino_test.technical_analyzer import DinoTestTechnicalAnalyzer
        
        # 데이터 수집
        collector = TechnicalDataCollector()
        technical_data = collector.collect_technical_analysis_data(stock_code)
        
        if technical_data is None:
            raise HTTPException(
                status_code=404,
                detail=f"종목 {stock_code}의 기술분석 데이터를 수집할 수 없습니다"
            )
        
        # 기술분석 점수 계산
        analyzer = DinoTestTechnicalAnalyzer()
        score_detail = analyzer.calculate_total_technical_score(technical_data)
        
        # 응답 데이터 구성 (한글 키 사용)
        raw_data = {
            "데이터기간": f"{technical_data.chart_data['date'].min().strftime('%Y-%m-%d')} ~ {technical_data.chart_data['date'].max().strftime('%Y-%m-%d')}" if technical_data.chart_data is not None else "없음",
            "총데이터건수": f"{len(technical_data.chart_data)}일" if technical_data.chart_data is not None else "0일",
            "OBV변화율": f"{score_detail.obv_change_rate:.2f}%" if score_detail.obv_change_rate is not None else "없음",
            "주가변화율": f"{score_detail.price_change_rate:.2f}%" if score_detail.price_change_rate is not None else "없음",
            "현재RSI": f"{score_detail.rsi_value:.2f}" if score_detail.rsi_value is not None else "없음",
            "투자심리도": f"{score_detail.stochastic_value:.2f}%" if score_detail.stochastic_value is not None else "없음",
            "MACD": f"{score_detail.macd_value:.4f}" if score_detail.macd_value is not None else "없음"
        }
        
        logger.info(f"=== 디노테스트 기술분석 완료: {stock_code} - 총점: {score_detail.total_score}/5점 ===")
        
        return DinoTestTechnicalResponse(
            success=True,
            stock_code=stock_code,
            stock_name="",  # 종목명은 별도 조회 필요
            total_score=score_detail.total_score,
            obv_score=score_detail.obv_score,
            rsi_score=score_detail.rsi_score,
            sentiment_score=score_detail.sentiment_score,
            other_indicator_score=score_detail.other_indicator_score,
            obv_status=score_detail.obv_status or "",
            rsi_value=score_detail.rsi_value or 0.0,
            raw_data=raw_data,
            message=f"기술분석 완료 - 총점: {score_detail.total_score}/5점"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"디노테스트 기술분석 계산 오류 - {stock_code}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"기술분석 계산 중 오류가 발생했습니다: {str(e)}")

# ================================================================================================
# 디노테스트 - 가격 영역 API
# ================================================================================================

class DinoTestPriceResponse(BaseModel):
    """디노테스트 가격분석 응답 모델"""
    success: bool = Field(..., description="성공 여부")
    stock_code: str = Field(..., description="종목코드")
    stock_name: str = Field(default="", description="종목명")
    total_score: int = Field(..., description="가격분석 총점 (0~5점)")
    high_ratio_score: int = Field(..., description="52주 최고가 대비 점수 (0~3)")
    low_ratio_score: int = Field(..., description="52주 최저가 대비 점수 (-3~0)")
    high_ratio_status: str = Field(default="", description="최고가 비율 상태")
    low_ratio_status: str = Field(default="", description="최저가 비율 상태")
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="계산 근거 데이터")
    message: str = Field(default="", description="메시지")

@app.get("/dino-test/price/{stock_code}", response_model=DinoTestPriceResponse)
async def calculate_dino_test_price_score(
    stock_code: str,
    authorization: str = Header(default=DEFAULT_ADMIN_TOKEN)
):
    """
    디노테스트 가격분석 점수 계산
    
    Args:
        stock_code: 종목코드 (예: 005930)
        authorization: JWT 인증 토큰
    
    Returns:
        DinoTestPriceResponse: 가격분석 결과
    """
    logger.info(f"=== 디노테스트 가격분석 시작: {stock_code} ===")
    
    try:
        # JWT에서 사용자 ID 추출
        user_id = extract_user_id_from_jwt(authorization)
        logger.info(f"요청 사용자 ID: {user_id}")
        
        # KIS 인증 확인
        if DB_AVAILABLE:
            # DB에서 토큰 조회
            token_info = get_token_status_from_db(user_id)
            if not token_info or not token_info.get("is_valid", False):
                ka.auth()  # 토큰이 없거나 만료된 경우 새로 발급
        else:
            # 파일 기반 토큰 인증
            ka.auth()
        
        # 가격분석 데이터 수집기 import
        from dino_test.price_data_collector import PriceDataCollector
        from dino_test.price_analyzer import DinoTestPriceAnalyzer
        
        # 데이터 수집 및 분석
        collector = PriceDataCollector()
        analyzer = DinoTestPriceAnalyzer()
        
        # 가격분석 데이터 수집
        price_data = collector.collect_price_analysis_data(stock_code)
        
        if price_data is None:
            logger.error(f"가격분석 데이터 수집 실패 - {stock_code}")
            return DinoTestPriceResponse(
                success=False,
                stock_code=stock_code,
                total_score=0,
                high_ratio_score=0,
                low_ratio_score=0,
                message="가격분석 데이터를 수집할 수 없습니다"
            )
        
        # 가격분석 점수 계산
        score_detail = analyzer.calculate_total_price_score(price_data)
        
        # 한글 키로 된 raw_data 생성 (사용자 친화적)
        raw_data = {
            "현재가": f"{score_detail.current_price:,.0f}원" if score_detail.current_price else "정보 없음",
            "52주 최고가": f"{score_detail.week_52_high:,.0f}원" if score_detail.week_52_high else "정보 없음",
            "52주 최저가": f"{score_detail.week_52_low:,.0f}원" if score_detail.week_52_low else "정보 없음",
            "최고가 대비 비율": f"{score_detail.high_ratio:.2f}%" if score_detail.high_ratio is not None else "계산 불가",
            "최저가 대비 비율": f"{score_detail.low_ratio:.2f}%" if score_detail.low_ratio is not None else "계산 불가",
            "최고가 대비 점수": score_detail.high_ratio_score,
            "최저가 대비 점수": score_detail.low_ratio_score,
            "총점 계산식": f"MAX(0, MIN(5, 2 + {score_detail.high_ratio_score} + {score_detail.low_ratio_score})) = {score_detail.total_score}"
        }
        
        logger.info(f"가격분석 완료 - {stock_code}: 총점 {score_detail.total_score}/5점")
        
        return DinoTestPriceResponse(
            success=True,
            stock_code=stock_code,
            total_score=score_detail.total_score,
            high_ratio_score=score_detail.high_ratio_score,
            low_ratio_score=score_detail.low_ratio_score,
            high_ratio_status=score_detail.high_ratio_status or "",
            low_ratio_status=score_detail.low_ratio_status or "",
            raw_data=raw_data,
            message="가격분석이 성공적으로 완료되었습니다"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"디노테스트 가격분석 계산 오류 - {stock_code}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"가격분석 계산 중 오류가 발생했습니다: {str(e)}")

# ================================================================================================
# 디노테스트 - 소재 영역 API
# ================================================================================================

class DinoTestMaterialResponse(BaseModel):
    """디노테스트 소재분석 응답 모델"""
    success: bool = Field(..., description="성공 여부")
    stock_code: str = Field(..., description="종목코드")
    stock_name: str = Field(default="", description="종목명")
    total_score: int = Field(..., description="소재분석 총점 (0~5점)")
    dividend_score: int = Field(..., description="고배당 점수 (0~1점)")
    institutional_score: int = Field(..., description="기관 수급 점수 (0~1점)")
    foreign_score: int = Field(..., description="외국인 수급 점수 (0~1점)")
    earnings_surprise_score: int = Field(..., description="어닝서프라이즈 점수 (0~1점)")
    dividend_status: str = Field(default="", description="배당 상태")
    institutional_status: str = Field(default="", description="기관 수급 상태")
    foreign_status: str = Field(default="", description="외국인 수급 상태")
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="계산 근거 데이터")
    message: str = Field(default="", description="메시지")

@app.get("/dino-test/material/{stock_code}", response_model=DinoTestMaterialResponse)
async def calculate_dino_test_material_score(
    stock_code: str,
    authorization: str = Header(default=DEFAULT_ADMIN_TOKEN)
):
    """
    디노테스트 소재분석 점수 계산
    
    Args:
        stock_code: 종목코드 (예: 005930)
        authorization: JWT 인증 토큰
    
    Returns:
        DinoTestMaterialResponse: 소재분석 결과
    """
    logger.info(f"=== 디노테스트 소재분석 시작: {stock_code} ===")
    
    try:
        # JWT에서 사용자 ID 추출
        user_id = extract_user_id_from_jwt(authorization)
        logger.info(f"요청 사용자 ID: {user_id}")
        
        # KIS 인증 확인
        if DB_AVAILABLE:
            # DB에서 토큰 조회
            token_info = get_token_status_from_db(user_id)
            if not token_info or not token_info.get("is_valid", False):
                ka.auth()  # 토큰이 없거나 만료된 경우 새로 발급
        else:
            # 파일 기반 토큰 인증
            ka.auth()
        
        # 소재분석 데이터 수집기 import
        from dino_test.material_data_collector import MaterialDataCollector
        from dino_test.material_analyzer import DinoTestMaterialAnalyzer
        
        # 데이터 수집 및 분석
        collector = MaterialDataCollector()
        analyzer = DinoTestMaterialAnalyzer()
        
        # 소재분석 데이터 수집
        material_data = collector.collect_material_analysis_data(stock_code)
        
        if material_data is None:
            logger.error(f"소재분석 데이터 수집 실패 - {stock_code}")
            return DinoTestMaterialResponse(
                success=False,
                stock_code=stock_code,
                total_score=0,
                dividend_score=0,
                institutional_score=0,
                foreign_score=0,
                earnings_surprise_score=0,
                message="소재분석 데이터를 수집할 수 없습니다"
            )
        
        # 소재분석 점수 계산
        score_detail = analyzer.calculate_total_material_score(material_data)
        
        # 한글 키로 된 raw_data 생성 (사용자 친화적)
        raw_data = {
            "배당률": f"{score_detail.dividend_yield:.2f}%" if score_detail.dividend_yield is not None else "정보 없음",
            "기관 보유 비율": f"{score_detail.institutional_ratio:.2f}%" if score_detail.institutional_ratio is not None else "정보 없음",
            "외국인 보유 비율": f"{score_detail.foreign_ratio:.2f}%" if score_detail.foreign_ratio is not None else "정보 없음",
            "기관 변화율": f"{score_detail.institutional_change:.2f}%" if score_detail.institutional_change is not None else "정보 없음",
            "외국인 변화율": f"{score_detail.foreign_change:.2f}%" if score_detail.foreign_change is not None else "정보 없음",
            "고배당 점수": score_detail.dividend_score,
            "기관 수급 점수": score_detail.institutional_score,
            "외국인 수급 점수": score_detail.foreign_score,
            "어닝서프라이즈 점수": score_detail.earnings_surprise_score,
            "총점 계산식": f"MAX(0, MIN(5, 2 + {score_detail.dividend_score} + {score_detail.institutional_score} + {score_detail.foreign_score} + {score_detail.earnings_surprise_score})) = {score_detail.total_score}"
        }
        
        logger.info(f"소재분석 완료 - {stock_code}: 총점 {score_detail.total_score}/5점")
        
        return DinoTestMaterialResponse(
            success=True,
            stock_code=stock_code,
            total_score=score_detail.total_score,
            dividend_score=score_detail.dividend_score,
            institutional_score=score_detail.institutional_score,
            foreign_score=score_detail.foreign_score,
            earnings_surprise_score=score_detail.earnings_surprise_score,
            dividend_status=score_detail.dividend_status or "",
            institutional_status=score_detail.institutional_status or "",
            foreign_status=score_detail.foreign_status or "",
            raw_data=raw_data,
            message="소재분석이 성공적으로 완료되었습니다"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"디노테스트 소재분석 계산 오류 - {stock_code}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"소재분석 계산 중 오류가 발생했습니다: {str(e)}")

# ================================================================================================
# 디노테스트 - D001 구체화된 이벤트/호재 임박 분석 API
# ================================================================================================

class DinoTestEventResponse(BaseModel):
    """D001 구체화된 이벤트/호재 임박 분석 응답 모델"""
    success: bool = Field(..., description="성공 여부")
    stock_code: str = Field(..., description="종목코드")
    company_name: str = Field(default="", description="기업명")
    total_sources: int = Field(default=0, description="분석한 뉴스+공시 수")
    imminent_events_count: int = Field(default=0, description="임박한 호재 이벤트 수")
    event_score: int = Field(..., description="D001 점수 (0 또는 1)")
    detected_events: List[Dict[str, Any]] = Field(default_factory=list, description="감지된 이벤트 목록")
    analysis_summary: str = Field(default="", description="분석 요약")
    message: str = Field(default="", description="메시지")

@app.get("/dino-test/event/{stock_code}", response_model=DinoTestEventResponse)
async def analyze_imminent_events(
    stock_code: str,
    company_name: str = None,
    authorization: str = Header(default=DEFAULT_ADMIN_TOKEN)
):
    """
    D001: 구체화된 이벤트/호재 임박 분석
    
    뉴스와 공시에서 구체적인 날짜가 명시된 호재성 이벤트를 감지합니다.
    - 신제품 출시, 실적 발표/IR, 계약 체결/파트너십, 승인/인증 관련
    - 구체적인 날짜가 포함된 호재 이벤트 발견 시 +1점
    
    Args:
        stock_code: 종목코드 (예: 005930)
        company_name: 기업명 (선택적, 검색 키워드로 활용)
        authorization: JWT 인증 토큰
    
    Returns:
        DinoTestEventResponse: D001 이벤트 분석 결과
    """
    logger.info(f"=== D001 구체화된 이벤트/호재 임박 분석 시작: {stock_code} ===")
    
    try:
        # JWT에서 사용자 ID 추출
        user_id = extract_user_id_from_jwt(authorization)
        logger.info(f"요청 사용자 ID: {user_id}")
        
        # 이벤트 분석기 import
        from dino_test.event_analyzer import EventAnalyzer
        
        # 이벤트 분석 수행
        analyzer = EventAnalyzer()
        result = analyzer.analyze_imminent_events(stock_code, company_name)
        
        if result is None:
            logger.error(f"D001 이벤트 분석 실패 - {stock_code}")
            return DinoTestEventResponse(
                success=False,
                stock_code=stock_code,
                company_name=company_name or stock_code,
                event_score=0,
                message="이벤트 분석을 수행할 수 없습니다"
            )
        
        logger.info(f"D001 이벤트 분석 완료 - {result.company_name}: 점수 {result.event_score}, 이벤트 {result.imminent_events_count}개")
        
        return DinoTestEventResponse(
            success=True,
            stock_code=result.stock_code,
            company_name=result.company_name,
            total_sources=result.total_sources,
            imminent_events_count=result.imminent_events_count,
            event_score=result.event_score,
            detected_events=result.detected_events,
            analysis_summary=result.analysis_summary,
            message="D001 이벤트 분석이 성공적으로 완료되었습니다"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"D001 이벤트 분석 오류 - {stock_code}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"이벤트 분석 중 오류가 발생했습니다: {str(e)}")

# ================================================================================================
# 디노테스트 - D002 확실한 주도 테마 분석 API
# ================================================================================================

class DinoTestThemeResponse(BaseModel):
    """D002 확실한 주도 테마 분석 응답 모델"""
    success: bool = Field(..., description="성공 여부")
    stock_code: str = Field(..., description="종목코드")
    company_name: str = Field(default="", description="기업명")
    is_leading_theme: bool = Field(..., description="주도 테마 여부")
    theme_score: int = Field(..., description="D002 점수 (0 또는 1)")
    detected_theme: str = Field(default="", description="감지된 테마명")
    confidence_score: float = Field(default=0.0, description="신뢰도 (0.0-1.0)")
    theme_evidence: List[str] = Field(default_factory=list, description="테마 근거 목록")
    related_news_count: int = Field(default=0, description="관련 뉴스 수")
    analysis_summary: str = Field(default="", description="분석 요약")
    message: str = Field(default="", description="메시지")

@app.get("/dino-test/theme/{stock_code}", response_model=DinoTestThemeResponse)
async def analyze_leading_theme(
    stock_code: str,
    company_name: str = None,
    authorization: str = Header(default=DEFAULT_ADMIN_TOKEN)
):
    """
    D002: 확실한 주도 테마 분석
    
    뉴스 분석을 통해 해당 종목이 확실한 주도 테마에 속하는지 판단합니다.
    AI 기반으로 테마 집중도, 시장 관심도, 지속성을 분석합니다.
    
    Args:
        stock_code: 종목코드 (예: 005930)
        company_name: 기업명 (선택적, 검색 키워드로 활용)
        authorization: JWT 인증 토큰
    
    Returns:
        DinoTestThemeResponse: D002 테마 분석 결과
    """
    logger.info(f"=== D002 확실한 주도 테마 분석 시작: {stock_code} ===")
    
    try:
        # JWT에서 사용자 ID 추출
        user_id = extract_user_id_from_jwt(authorization)
        logger.info(f"요청 사용자 ID: {user_id}")
        
        # 테마 분석기 import
        from dino_test.theme_analyzer import ThemeAnalyzer
        
        # 테마 분석 수행
        analyzer = ThemeAnalyzer()
        result = analyzer.analyze_leading_theme(stock_code, company_name)
        
        if result is None:
            logger.error(f"D002 테마 분석 실패 - {stock_code}")
            return DinoTestThemeResponse(
                success=False,
                stock_code=stock_code,
                company_name=company_name or stock_code,
                is_leading_theme=False,
                theme_score=0,
                message="테마 분석을 수행할 수 없습니다"
            )
        
        logger.info(f"D002 테마 분석 완료 - {result.company_name}: 점수 {result.theme_score}, 테마: {result.detected_theme}")
        
        return DinoTestThemeResponse(
            success=True,
            stock_code=result.stock_code,
            company_name=result.company_name,
            is_leading_theme=result.is_leading_theme,
            theme_score=result.theme_score,
            detected_theme=result.detected_theme,
            confidence_score=result.confidence_score,
            theme_evidence=result.theme_evidence,
            related_news_count=result.related_news_count,
            analysis_summary=result.analysis_summary,
            message="D002 테마 분석이 성공적으로 완료되었습니다"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"D002 테마 분석 오류 - {stock_code}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"테마 분석 중 오류가 발생했습니다: {str(e)}")

# D008: 호재뉴스 도배 분석 응답 모델
class DinoTestPositiveNewsResponse(BaseModel):
    success: bool = Field(..., description="성공 여부")
    stock_code: str = Field(..., description="종목코드")
    company_name: str = Field(default="", description="기업명")
    total_news_count: int = Field(default=0, description="전체 뉴스 수")
    positive_news_count: int = Field(default=0, description="호재 뉴스 수")
    positive_ratio: float = Field(default=0.0, description="호재 뉴스 비율 (0.0-1.0)")
    hype_score: float = Field(default=0.0, description="과장성 점수 (0.0-1.0)")
    flooding_score: int = Field(..., description="D008 도배 점수 (-1, 0, 1)")
    positive_keywords_found: List[str] = Field(default_factory=list, description="발견된 호재 키워드들")
    hype_expressions: List[str] = Field(default_factory=list, description="과장 표현들")
    analysis_summary: str = Field(default="", description="분석 요약")
    message: str = Field(default="", description="메시지")

@app.get("/dino-test/positive-news/{stock_code}", response_model=DinoTestPositiveNewsResponse)
async def dino_test_positive_news_analysis(
    stock_code: str,
    company_name: str = None,
    authorization: str = Header(default=DEFAULT_ADMIN_TOKEN)
):
    """
    D008: 호재뉴스 도배 분석
    
    Args:
        stock_code: 6자리 종목코드 (예: 005930)
        company_name: 기업명 (선택사항)
        
    Returns:
        DinoTestPositiveNewsResponse: D008 호재뉴스 도배 분석 결과
    """
    try:
        # JWT 토큰 검증
        extract_user_id_from_jwt(authorization)
        
        # 호재뉴스 도배 분석기 초기화 및 실행
        from dino_test.positive_news_analyzer import PositiveNewsAnalyzer
        analyzer = PositiveNewsAnalyzer()
        result = analyzer.analyze_positive_news_flooding(stock_code, company_name)
        
        if result is None:
            logger.error(f"D008 호재뉴스 분석 실패 - {stock_code}")
            return DinoTestPositiveNewsResponse(
                success=False,
                stock_code=stock_code,
                company_name=company_name or stock_code,
                flooding_score=0,
                message="호재뉴스 분석을 수행할 수 없습니다"
            )
        
        logger.info(f"D008 호재뉴스 분석 완료 - {result.company_name}: 점수 {result.flooding_score}, 호재비율 {result.positive_ratio:.1%}")
        
        return DinoTestPositiveNewsResponse(
            success=True,
            stock_code=result.stock_code,
            company_name=result.company_name,
            total_news_count=result.total_news_count,
            positive_news_count=result.positive_news_count,
            positive_ratio=result.positive_ratio,
            hype_score=result.hype_score,
            flooding_score=result.flooding_score,
            positive_keywords_found=result.positive_keywords_found,
            hype_expressions=result.hype_expressions,
            analysis_summary=result.analysis_summary,
            message="D008 호재뉴스 분석이 성공적으로 완료되었습니다"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"D008 호재뉴스 분석 오류 - {stock_code}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"호재뉴스 분석 중 오류가 발생했습니다: {str(e)}")

# D009: 이자보상배율 분석 응답 모델
class DinoTestInterestCoverageResponse(BaseModel):
    success: bool = Field(..., description="성공 여부")
    stock_code: str = Field(..., description="종목코드")
    company_name: str = Field(default="", description="기업명")
    ebit: Optional[float] = Field(default=None, description="EBIT (세전영업이익, 억원)")
    interest_expense: Optional[float] = Field(default=None, description="이자비용 (억원)")
    interest_coverage_ratio: Optional[float] = Field(default=None, description="이자보상배율")
    coverage_score: int = Field(..., description="D009 점수 (-1 또는 0)")
    analysis_summary: str = Field(default="", description="분석 요약")
    fiscal_year: Optional[str] = Field(default=None, description="회계연도")
    data_quality: str = Field(default="", description="데이터 품질")
    message: str = Field(default="", description="메시지")

@app.get("/dino-test/finance/{stock_code}", response_model=DinoTestFinanceResponse)
async def dino_test_finance_data(
    stock_code: str,
    authorization: str = Header(default=DEFAULT_ADMIN_TOKEN)
):
    """
    디노테스트 재무 데이터 조회 API - D009 이자보상배율 분석용
    
    KIS API를 통해 재무제표 데이터를 수집하여 EBIT, 이자비용 등 재무 정보를 제공합니다.
    """
    try:
        logger.info(f"=== 디노테스트 재무 데이터 조회 시작: {stock_code} ===")
        
        # 토큰 검증
        if authorization != DEFAULT_ADMIN_TOKEN:
            logger.warning(f"Unauthorized access attempt for finance data: {stock_code}")
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        # FinanceDataCollector를 통해 재무 데이터 수집
        from dino_test.finance_data_collector import FinanceDataCollector
        
        collector = FinanceDataCollector()
        
        # 손익계산서 데이터 조회 (연간)
        income_statement = collector.fetch_income_statement(stock_code, div_cls_code="0")
        
        if income_statement is None or income_statement.empty:
            logger.warning(f"손익계산서 데이터 없음: {stock_code}")
            return DinoTestFinanceResponse(
                success=False,
                stock_code=stock_code,
                message="재무 데이터를 찾을 수 없습니다",
                raw_financial_data={},
                financial_ratios={}
            )
        
        # 재무 데이터를 딕셔너리로 변환
        financial_dict = {}
        for index, row in income_statement.iterrows():
            for col, value in row.items():
                if pd.notna(value):
                    financial_dict[f"{col}_{index}"] = str(value)
        
        # 주요 재무 지표 추출 (최신 데이터 기준)
        latest_row = income_statement.iloc[0] if not income_statement.empty else {}
        
        # EBIT 관련 필드 추출 (영업이익을 EBIT로 사용)
        ebit_fields = ["영업이익", "operating_income", "영업수익"]
        ebit_value = None
        for field in ebit_fields:
            if field in latest_row and pd.notna(latest_row[field]):
                try:
                    ebit_value = float(latest_row[field])
                    break
                except (ValueError, TypeError):
                    continue
        
        # 이자비용 관련 필드 추출
        interest_fields = ["이자비용", "interest_expense", "금융비용", "이자지급액"]
        interest_expense_value = None
        for field in interest_fields:
            if field in latest_row and pd.notna(latest_row[field]):
                try:
                    interest_expense_value = float(latest_row[field])
                    break
                except (ValueError, TypeError):
                    continue
        
        # 회계연도 정보
        fiscal_year = latest_row.get("stac_yymm", latest_row.get("year", "2024"))
        
        # 재무 비율 계산
        financial_ratios = {}
        if ebit_value is not None:
            financial_ratios["operating_income"] = ebit_value
            financial_ratios["ebit"] = ebit_value
        
        if interest_expense_value is not None:
            financial_ratios["interest_expense"] = interest_expense_value
            financial_ratios["이자비용"] = interest_expense_value
        
        if ebit_value is not None and interest_expense_value is not None and interest_expense_value > 0:
            financial_ratios["interest_coverage_ratio"] = ebit_value / interest_expense_value
        
        financial_ratios["fiscal_year"] = str(fiscal_year)
        
        # 원시 데이터에 주요 필드 포함
        raw_data = financial_dict.copy()
        raw_data.update({
            "operating_income": ebit_value,
            "영업이익": ebit_value,
            "ebit": ebit_value,
            "interest_expense": interest_expense_value,
            "이자비용": interest_expense_value,
            "fiscal_year": fiscal_year
        })
        
        logger.info(f"재무 데이터 조회 성공: {stock_code} - EBIT: {ebit_value}, 이자비용: {interest_expense_value}")
        
        return DinoTestFinanceResponse(
            success=True,
            stock_code=stock_code,
            message="재무 데이터 조회 성공",
            raw_financial_data=raw_data,
            financial_ratios=financial_ratios
        )
        
    except Exception as e:
        error_msg = f"재무 데이터 조회 오류: {str(e)}"
        logger.error(f"finance data error for {stock_code}: {e}")
        
        return DinoTestFinanceResponse(
            success=False,
            stock_code=stock_code,
            message=error_msg,
            raw_financial_data={},
            financial_ratios={}
        )

@app.get("/dino-test/interest-coverage/{stock_code}", response_model=DinoTestInterestCoverageResponse)
async def dino_test_interest_coverage_analysis(
    stock_code: str,
    company_name: str = None,
    authorization: str = Header(default=DEFAULT_ADMIN_TOKEN)
):
    """
    D009: 이자보상배율 분석
    
    Args:
        stock_code: 6자리 종목코드 (예: 005930)
        company_name: 기업명 (선택사항)
        
    Returns:
        DinoTestInterestCoverageResponse: D009 이자보상배율 분석 결과
    """
    try:
        # JWT 토큰 검증
        extract_user_id_from_jwt(authorization)
        
        # 이자보상배율 분석기 초기화 및 실행
        from dino_test.interest_coverage_analyzer import InterestCoverageAnalyzer
        analyzer = InterestCoverageAnalyzer()
        result = analyzer.analyze_interest_coverage(stock_code, company_name)
        
        if result is None:
            logger.error(f"D009 이자보상배율 분석 실패 - {stock_code}")
            return DinoTestInterestCoverageResponse(
                success=False,
                stock_code=stock_code,
                company_name=company_name or stock_code,
                coverage_score=0,
                message="이자보상배율 분석을 수행할 수 없습니다"
            )
        
        logger.info(f"D009 이자보상배율 분석 완료 - {result.company_name}: {result.analysis_summary}")
        
        return DinoTestInterestCoverageResponse(
            success=True,
            stock_code=result.stock_code,
            company_name=result.company_name,
            ebit=result.ebit,
            interest_expense=result.interest_expense,
            interest_coverage_ratio=result.interest_coverage_ratio,
            coverage_score=result.coverage_score,
            analysis_summary=result.analysis_summary,
            fiscal_year=result.fiscal_year,
            data_quality=result.data_quality,
            message="D009 이자보상배율 분석이 성공적으로 완료되었습니다"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"D009 이자보상배율 분석 오류 - {stock_code}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"이자보상배율 분석 중 오류가 발생했습니다: {str(e)}")

# ============================================
# DINO 종합 테스트 엔드포인트
# ============================================

class ComprehensiveDinoRequest(BaseModel):
    stock_code: str = Field(..., description="종목 코드 (예: 005930)")
    company_name: Optional[str] = Field(None, description="회사명 (옵션)")
    force_rerun: bool = Field(False, description="강제 재실행 여부")

class ComprehensiveDinoResponse(BaseModel):
    success: bool
    stock_code: str
    company_name: str
    
    # 9개 분석 영역 점수
    finance_score: int
    technical_score: int
    price_score: int
    material_score: int
    event_score: int
    theme_score: int
    positive_news_score: int
    interest_coverage_score: int
    
    total_score: int
    analysis_grade: str
    analysis_date: str
    status: str
    message: str

class DinoResultsResponse(BaseModel):
    success: bool
    results: List[Dict[str, Any]]
    total_count: int
    message: str

@app.post("/dino-test/comprehensive", response_model=ComprehensiveDinoResponse)
async def run_comprehensive_dino_test(
    request: ComprehensiveDinoRequest,
    authorization: str = Header(None)
):
    """
    종합 DINO 테스트 실행
    
    모든 분석 영역을 실행하고 결과와 Raw 데이터를 저장합니다.
    - 하루 1회 분석 제한 (force_rerun=true로 우회 가능)
    - 모든 Raw 데이터 및 AI 응답 저장
    - 자동 등급 계산 (S/A/B/C/D)
    """
    try:
        # 인증 컨텍스트 설정
        setup_auth_context(authorization)
        
        # 사용자 ID 추출
        user_id = extract_user_id_from_jwt(authorization or DEFAULT_ADMIN_TOKEN)
        
        logger.info(f"🚀 종합 DINO 분석 요청: {request.stock_code}, force_rerun={request.force_rerun}")
        
        # 종합 분석기 초기화
        from dino_test.comprehensive_analyzer import ComprehensiveDinoAnalyzer
        analyzer = ComprehensiveDinoAnalyzer()
        
        # 종합 분석 실행
        result = analyzer.run_comprehensive_analysis(
            stock_code=request.stock_code,
            company_name=request.company_name,
            user_id=user_id,
            force_rerun=request.force_rerun
        )
        
        if not result:
            if not request.force_rerun and analyzer.check_existing_analysis(request.stock_code):
                return ComprehensiveDinoResponse(
                    success=False,
                    stock_code=request.stock_code,
                    company_name=request.company_name or request.stock_code,
                    finance_score=0, technical_score=0, price_score=0, material_score=0,
                    event_score=0, theme_score=0, positive_news_score=0, interest_coverage_score=0,
                    total_score=0, analysis_grade="", analysis_date="", status="SKIPPED",
                    message="오늘 이미 분석된 종목입니다. force_rerun=true로 재실행 가능합니다."
                )
            else:
                raise HTTPException(status_code=500, detail="종합 분석 실행에 실패했습니다")
        
        # 자동 등급 계산 (트리거 함수에 의해 자동 계산됨)
        grade_map = {35: "S", 30: "A", 25: "B", 20: "C"}
        grade = "D"
        for threshold, g in grade_map.items():
            if result.total_score >= threshold:
                grade = g
                break
        
        logger.info(f"🎉 종합 DINO 분석 완료 - {result.company_name}: 총점 {result.total_score}점, 등급 {grade}")
        
        return ComprehensiveDinoResponse(
            success=True,
            stock_code=result.stock_code,
            company_name=result.company_name,
            finance_score=result.finance_score,
            technical_score=result.technical_score,
            price_score=result.price_score,
            material_score=result.material_score,
            event_score=result.event_score,
            theme_score=result.theme_score,
            positive_news_score=result.positive_news_score,
            interest_coverage_score=result.interest_coverage_score,
            total_score=result.total_score,
            analysis_grade=grade,
            analysis_date=result.analysis_date.isoformat(),
            status=result.status,
            message=f"종합 DINO 분석이 성공적으로 완료되었습니다. 총점: {result.total_score}점, 등급: {grade}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"종합 DINO 분석 오류 - {request.stock_code}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"종합 DINO 분석 중 오류가 발생했습니다: {str(e)}")

@app.get("/dino-test/results", response_model=DinoResultsResponse)
async def get_dino_test_results(
    stock_code: Optional[str] = None,
    analysis_date: Optional[str] = None,
    limit: int = 100,
    authorization: str = Header(None)
):
    """
    DINO 테스트 결과 조회
    
    Args:
        stock_code: 종목 코드 필터 (옵션)
        analysis_date: 분석 날짜 필터 (YYYY-MM-DD 형식, 옵션)
        limit: 최대 조회 건수 (기본: 100)
    """
    try:
        # 인증 컨텍스트 설정
        setup_auth_context(authorization)
        
        logger.info(f"📊 DINO 테스트 결과 조회: stock_code={stock_code}, date={analysis_date}, limit={limit}")
        
        # 종합 분석기 초기화
        from dino_test.comprehensive_analyzer import ComprehensiveDinoAnalyzer
        analyzer = ComprehensiveDinoAnalyzer()
        
        # 날짜 파싱
        parsed_date = None
        if analysis_date:
            try:
                from datetime import datetime
                parsed_date = datetime.strptime(analysis_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="날짜 형식이 잘못되었습니다. YYYY-MM-DD 형식을 사용하세요.")
        
        # 결과 조회
        results = analyzer.get_analysis_results(
            stock_code=stock_code,
            analysis_date=parsed_date,
            limit=limit
        )
        
        logger.info(f"✅ DINO 테스트 결과 조회 완료: {len(results)}건")
        
        return DinoResultsResponse(
            success=True,
            results=results,
            total_count=len(results),
            message=f"DINO 테스트 결과 {len(results)}건을 성공적으로 조회했습니다."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DINO 테스트 결과 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DINO 테스트 결과 조회 중 오류가 발생했습니다: {str(e)}")

@app.get("/dino-test/results/{stock_code}/latest")
async def get_latest_dino_result(
    stock_code: str,
    authorization: str = Header(None)
):
    """특정 종목의 최신 DINO 테스트 결과 조회"""
    try:
        # 인증 컨텍스트 설정
        setup_auth_context(authorization)
        
        logger.info(f"📊 최신 DINO 결과 조회: {stock_code}")
        
        # 종합 분석기 초기화
        from dino_test.comprehensive_analyzer import ComprehensiveDinoAnalyzer
        analyzer = ComprehensiveDinoAnalyzer()
        
        # 해당 종목의 최신 결과 1건 조회
        results = analyzer.get_analysis_results(stock_code=stock_code, limit=1)
        
        if not results:
            raise HTTPException(status_code=404, detail=f"종목 {stock_code}의 DINO 테스트 결과를 찾을 수 없습니다.")
        
        latest_result = results[0]
        
        logger.info(f"✅ 최신 DINO 결과 조회 완료: {stock_code} - 총점 {latest_result.get('total_score', 0)}점")
        
        return {
            "success": True,
            "result": latest_result,
            "message": f"종목 {stock_code}의 최신 DINO 테스트 결과입니다."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"최신 DINO 결과 조회 오류 - {stock_code}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"최신 DINO 결과 조회 중 오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )