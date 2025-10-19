"""
KIS API 클라이언트

한국투자증권 Open API와의 통신을 담당합니다.
"""

import asyncio
import aiohttp
import json
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from ..config import settings
from ..models import OrderRequest, CandleData, OrderBookData

@dataclass
class KISResponse:
    """KIS API 응답"""
    success: bool
    data: Optional[Dict[str, Any]]
    error_code: Optional[str]
    error_message: Optional[str]

class KISClient:
    """KIS API 클라이언트 메인 클래스"""
    
    def __init__(self):
        # 실제 KIS API 설정 사용
        self.base_url = settings.kis_base_url
        self.app_key = settings.KIS_APPKEY
        self.app_secret = settings.KIS_APPSECRET
        self.account_number = settings.KIS_CANO
        self.account_product_code = settings.KIS_ACNT_PRDT_CD
        
        # 인증 토큰 관리
        self.access_token = None
        self.token_expires_at = None
        
        # HTTP 세션
        self.session = None
        
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.session = aiohttp.ClientSession()
        await self.authenticate()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()
    
    async def authenticate(self) -> bool:
        """KIS API 인증"""
        
        try:
            # 기존 토큰이 유효한지 확인
            if self.access_token and self.token_expires_at:
                if datetime.now() < self.token_expires_at - timedelta(minutes=5):
                    return True
            
            # 실제 KIS API 인증 요청
            auth_url = f"{self.base_url}/oauth2/tokenP"
            
            auth_data = {
                "grant_type": "client_credentials",
                "appkey": self.app_key,
                "appsecret": self.app_secret
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # 실제 API 호출
            async with self.session.post(auth_url, json=auth_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    self.access_token = result.get("access_token")
                    expires_in = result.get("expires_in", 3600)
                    self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                    
                    if self.access_token:
                        print("✅ KIS API 인증 완료")
                        return True
                    else:
                        print("❌ 토큰이 응답에 없습니다")
                        return False
                else:
                    error_text = await response.text()
                    print(f"❌ KIS API 인증 실패: {response.status} - {error_text}")
                    return False
            
        except Exception as e:
            print(f"❌ KIS API 인증 실패: {e}")
            return False
    
    async def get_current_price(self, symbol: str) -> KISResponse:
        """현재가 조회"""
        
        try:
            # 실제 KIS API 호출
            url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
            
            headers = await self._get_headers("FHKST01010100")
            params = {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": symbol
            }
            
            # API 호출 (Rate Limiting 고려하여 1초 대기)
            await asyncio.sleep(1)
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get("rt_cd") == "0":
                        return KISResponse(
                            success=True,
                            data=result,
                            error_code=None,
                            error_message=None
                        )
                    else:
                        return KISResponse(
                            success=False,
                            data=None,
                            error_code=result.get("msg_cd"),
                            error_message=result.get("msg1")
                        )
                else:
                    error_text = await response.text()
                    return KISResponse(
                        success=False,
                        data=None,
                        error_code=f"HTTP_{response.status}",
                        error_message=error_text
                    )
            
        except Exception as e:
            return KISResponse(
                success=False,
                data=None,
                error_code="API_ERROR",
                error_message=str(e)
            )
    
    async def get_order_book(self, symbol: str) -> KISResponse:
        """호가창 조회"""
        
        try:
            # TODO: 실제 KIS API 호출
            url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn"
            
            headers = await self._get_headers("FHKST01010200")
            params = {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": symbol
            }
            
            # 임시 호가창 데이터
            mock_data = {
                "output1": {
                    "askp1": "75100", "askp_rsqn1": "1000",
                    "askp2": "75200", "askp_rsqn2": "1500", 
                    "askp3": "75300", "askp_rsqn3": "2000",
                    "askp4": "75400", "askp_rsqn4": "800",
                    "askp5": "75500", "askp_rsqn5": "1200",
                    "bidp1": "75000", "bidp_rsqn1": "2000",
                    "bidp2": "74900", "bidp_rsqn2": "1800",
                    "bidp3": "74800", "bidp_rsqn3": "1000", 
                    "bidp4": "74700", "bidp_rsqn4": "1500",
                    "bidp5": "74600", "bidp_rsqn5": "900",
                    "total_askp_rsqn": "6500",
                    "total_bidp_rsqn": "7200"
                }
            }
            
            return KISResponse(
                success=True,
                data=mock_data,
                error_code=None,
                error_message=None
            )
            
        except Exception as e:
            return KISResponse(
                success=False,
                data=None,
                error_code="API_ERROR", 
                error_message=str(e)
            )
    
    async def get_candle_data(self, symbol: str, timeframe: str = "D", 
                            period: int = 100) -> KISResponse:
        """캔들 차트 데이터 조회"""
        
        try:
            # TODO: 실제 KIS API 호출
            if timeframe == "D":
                # 일봉 조회
                url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
                tr_id = "FHKST03010100"
            else:
                # 분봉 조회
                url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"
                tr_id = "FHKST03010200"
            
            headers = await self._get_headers(tr_id)
            params = {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": symbol,
                "FID_INPUT_DATE_1": "",
                "FID_INPUT_DATE_2": "",
                "FID_PERIOD_DIV_CODE": timeframe,
                "FID_ORG_ADJ_PRC": "1"
            }
            
            # 임시 캔들 데이터 생성
            candles = []
            base_price = 75000
            
            for i in range(period):
                date_str = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
                price_change = (i % 10 - 5) * 100
                
                open_price = base_price + price_change
                close_price = open_price + ((i % 7 - 3) * 50)
                high_price = max(open_price, close_price) + abs(i % 3) * 50
                low_price = min(open_price, close_price) - abs(i % 2) * 30
                
                candles.append({
                    "stck_bsop_date": date_str,
                    "stck_oprc": str(int(open_price)),
                    "stck_hgpr": str(int(high_price)),
                    "stck_lwpr": str(int(low_price)),
                    "stck_clpr": str(int(close_price)),
                    "acml_vol": str(10000 + (i % 5) * 2000),
                    "acml_tr_pbmn": str((10000 + (i % 5) * 2000) * close_price)
                })
            
            mock_data = {
                "output2": candles
            }
            
            return KISResponse(
                success=True,
                data=mock_data,
                error_code=None,
                error_message=None
            )
            
        except Exception as e:
            return KISResponse(
                success=False,
                data=None,
                error_code="API_ERROR",
                error_message=str(e)
            )
    
    async def place_order(self, order_request: OrderRequest) -> KISResponse:
        """주문 실행"""
        
        try:
            # TODO: 실제 KIS API 주문 요청
            if order_request.side.value == "buy":
                url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"
                tr_id = "TTTC0802U"  # 현금 매수
            else:
                url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"
                tr_id = "TTTC0801U"  # 현금 매도
            
            headers = await self._get_headers(tr_id)
            
            # 주문 구분 코드
            ord_dvsn = "01" if order_request.order_type.value == "market" else "00"
            
            order_data = {
                "CANO": self.account_number,
                "ACNT_PRDT_CD": self.account_product_code,
                "PDNO": order_request.symbol,
                "ORD_DVSN": ord_dvsn,
                "ORD_QTY": str(order_request.quantity),
                "ORD_UNPR": str(int(order_request.price)) if order_request.price else "0"
            }
            
            # 임시로 성공 응답 반환
            mock_data = {
                "output": {
                    "KRX_FWDG_ORD_ORGNO": "91252",
                    "ODNO": "0000117057",
                    "ORD_TMD": "121052"
                },
                "rt_cd": "0",
                "msg_cd": "MCA00000",
                "msg1": "주문이 정상적으로 접수되었습니다."
            }
            
            return KISResponse(
                success=True,
                data=mock_data,
                error_code=None,
                error_message=None
            )
            
        except Exception as e:
            return KISResponse(
                success=False,
                data=None,
                error_code="ORDER_ERROR",
                error_message=str(e)
            )
    
    async def cancel_order(self, order_id: str) -> KISResponse:
        """주문 취소"""
        
        try:
            # TODO: 실제 KIS API 주문 취소 요청
            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-rvsecncl"
            
            headers = await self._get_headers("TTTC0803U")
            
            cancel_data = {
                "CANO": self.account_number,
                "ACNT_PRDT_CD": self.account_product_code,
                "KRX_FWDG_ORD_ORGNO": "",
                "ORGN_ODNO": order_id,
                "ORD_DVSN": "00",
                "RVSE_CNCL_DVSN_CD": "02",  # 취소
                "ORD_QTY": "0",
                "ORD_UNPR": "0",
                "QTY_ALL_ORD_YN": "Y"
            }
            
            # 임시로 성공 응답 반환
            mock_data = {
                "output": {
                    "KRX_FWDG_ORD_ORGNO": "91252",
                    "ODNO": order_id,
                    "ORD_TMD": "121052"
                },
                "rt_cd": "0",
                "msg_cd": "MCA00000", 
                "msg1": "주문이 정상적으로 취소되었습니다."
            }
            
            return KISResponse(
                success=True,
                data=mock_data,
                error_code=None,
                error_message=None
            )
            
        except Exception as e:
            return KISResponse(
                success=False,
                data=None,
                error_code="CANCEL_ERROR",
                error_message=str(e)
            )
    
    async def get_account_balance(self) -> KISResponse:
        """계좌 잔고 조회"""
        
        try:
            # TODO: 실제 KIS API 잔고 조회
            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
            
            headers = await self._get_headers("TTTC8434R")
            params = {
                "CANO": self.account_number,
                "ACNT_PRDT_CD": self.account_product_code,
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "02",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "01",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": ""
            }
            
            # 임시 잔고 데이터
            mock_data = {
                "output1": [
                    {
                        "pdno": "005930",
                        "prdt_name": "삼성전자",
                        "trad_dvsn_name": "현금",
                        "bfdy_buy_qty": "0",
                        "bfdy_sll_qty": "0", 
                        "thdt_buyqty": "10",
                        "thdt_sll_qty": "0",
                        "hldg_qty": "10",
                        "ord_psbl_qty": "10",
                        "pchs_avg_pric": "74500.00",
                        "pchs_amt": "745000",
                        "prpr": "75000",
                        "evlu_amt": "750000",
                        "evlu_pfls_amt": "5000",
                        "evlu_pfls_rt": "0.67"
                    }
                ],
                "output2": [
                    {
                        "dnca_tot_amt": "2500000",  # 예수금총액
                        "nxdy_excc_amt": "2500000", # 익일정산금액
                        "prvs_rcdl_excc_amt": "0",  # 가수도정산금액
                        "cma_evlu_amt": "0",        # CMA평가금액
                        "bfdy_buy_amt": "0",        # 전일매수금액
                        "thdt_buy_amt": "745000",   # 금일매수금액
                        "nxdy_auto_rdpt_amt": "0",  # 익일자동상환금액
                        "bfdy_sll_amt": "0",        # 전일매도금액
                        "thdt_sll_amt": "0",        # 금일매도금액
                        "d2_auto_rdpt_amt": "0",    # D+2자동상환금액
                        "bfdy_tlex_amt": "0",       # 전일제비용금액
                        "thdt_tlex_amt": "0",       # 금일제비용금액
                        "tot_loan_amt": "0",        # 총대출금액
                        "scts_evlu_amt": "750000",  # 유가증권평가금액
                        "tot_evlu_amt": "3250000",  # 총평가금액
                        "nass_amt": "3250000",      # 순자산금액
                        "fncg_gld_auto_rdpt_yn": "N", # 융자금자동상환여부
                        "pchs_amt_smtl_amt": "745000", # 매입금액합계금액
                        "evlu_amt_smtl_amt": "750000", # 평가금액합계금액
                        "evlu_pfls_smtl_amt": "5000",  # 평가손익합계금액
                        "tot_stln_slng_chgs": "0",     # 총대주매각대금
                        "bfdy_tot_asst_evlu_amt": "3245000", # 전일총자산평가금액
                        "asst_icdc_amt": "5000",       # 자산증감액
                        "asst_icdc_erng_rt": "0.15"    # 자산증감수익률
                    }
                ]
            }
            
            return KISResponse(
                success=True,
                data=mock_data,
                error_code=None,
                error_message=None
            )
            
        except Exception as e:
            return KISResponse(
                success=False,
                data=None,
                error_code="BALANCE_ERROR",
                error_message=str(e)
            )
    
    async def get_websocket_token(self) -> Optional[str]:
        """웹소켓 접속 토큰 발급"""
        
        try:
            # TODO: 실제 웹소켓 토큰 발급 API 호출
            url = f"{self.base_url}/oauth2/Approval"
            
            headers = {
                "content-type": "application/json"
            }
            
            token_data = {
                "grant_type": "client_credentials",
                "appkey": self.app_key,
                "secretkey": self.app_secret
            }
            
            # 임시 토큰 반환
            return "mock_websocket_approval_key"
            
        except Exception as e:
            print(f"❌ 웹소켓 토큰 발급 실패: {e}")
            return None
    
    async def _get_headers(self, tr_id: str) -> Dict[str, str]:
        """API 요청 헤더 생성"""
        
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id
        }
        
        # 모의투자 여부에 따른 헤더 추가
        if settings.kis_use_mock:
            headers["tr_cont"] = ""
            headers["custtype"] = "P"
        
        return headers
    
    async def check_connection(self) -> bool:
        """API 연결 상태 확인"""
        
        try:
            # 간단한 API 호출로 연결 상태 확인
            response = await self.get_current_price("005930")
            return response.success
            
        except Exception as e:
            print(f"❌ KIS API 연결 확인 실패: {e}")
            return False
    
    def _generate_hash_key(self, data: Dict[str, Any]) -> str:
        """해시키 생성 (POST 요청용)"""
        
        try:
            # TODO: 실제 해시키 생성 로직
            # KIS API 문서에 따른 해시키 생성
            params = "|".join([f"{k}={v}" for k, v in data.items()])
            hash_key = hashlib.sha256(params.encode()).hexdigest()
            return hash_key
            
        except Exception as e:
            print(f"❌ 해시키 생성 실패: {e}")
            return ""
