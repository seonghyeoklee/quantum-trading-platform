"""키움 시세표성정보요청(ka10007) 비즈니스 로직"""

import logging
import httpx
from datetime import datetime
from typing import Dict, Any, Optional, List

# Handle both relative and absolute imports for different execution contexts
try:
    from ..config.settings import settings
    from ..auth.token_manager import token_manager
    from ..models.chart import MarketInfoResponse, StructuredMarketInfo, MarketInfoApiResponse, MarketInfoData
except ImportError:
    import sys
    from pathlib import Path
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    from kiwoom_api.config.settings import settings
    from kiwoom_api.auth.token_manager import token_manager
    from kiwoom_api.models.chart import MarketInfoResponse, StructuredMarketInfo, MarketInfoApiResponse, MarketInfoData

logger = logging.getLogger(__name__)


async def fn_ka10007(data: Dict[str, Any], cont_yn: str = 'N', next_key: str = '') -> Dict[str, Any]:
    """
    키움 시세표성정보요청 API (ka10007) 호출
    
    Args:
        data: 요청 데이터 {'stk_cd': '005930'}
        cont_yn: 연속조회여부 ('N' or 'Y')
        next_key: 연속조회키
    
    Returns:
        키움 API 응답 데이터
    """
    try:
        # 1. 접근 토큰 획득
        access_token = await token_manager.get_valid_token()
        logger.info(f"키움 시세표성정보요청 시작: {data.get('stk_cd')}")
        
        # 2. 요청 URL 및 헤더 구성
        endpoint = '/api/dostk/mrkcond'
        url = settings.kiwoom_base_url + endpoint
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {access_token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'ka10007'
        }
        
        # 3. HTTP 요청
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            # 4. 응답 데이터 구성
            result = {
                "Code": response.status_code,
                "Header": {
                    "next-key": response.headers.get('next-key', ''),
                    "cont-yn": response.headers.get('cont-yn', 'N'),
                    "api-id": response.headers.get('api-id', 'ka10007')
                },
                "Body": response.json()
            }
            
            logger.info(f"키움 시세표성정보요청 완료: {data.get('stk_cd')} (응답코드: {response.status_code})")
            return result
            
    except httpx.HTTPStatusError as e:
        logger.error(f"키움 API HTTP 오류: {e.response.status_code} - {e.response.text}")
        return {
            "Code": e.response.status_code,
            "Error": f"HTTP 오류: {e.response.text}",
            "Header": {},
            "Body": {}
        }
    except Exception as e:
        logger.error(f"키움 시세표성정보요청 오류: {str(e)}")
        return {
            "Code": 500,
            "Error": str(e),
            "Header": {},
            "Body": {}
        }


def convert_market_info_data(raw_data: Dict[str, Any]) -> StructuredMarketInfo:
    """
    키움 원본 시세표성정보 데이터를 구조화된 형태로 변환
    
    Args:
        raw_data: 키움 원본 응답 데이터
    
    Returns:
        구조화된 시세표성정보 데이터
    """
    try:
        # 날짜/시간 정보 구성
        date = raw_data.get('date', '')
        time = raw_data.get('time', '')
        timestamp = f"{date}{time}" if date and time else date or time or ''
        
        # 기본 시세 정보 구성
        basic_info = {
            "open": raw_data.get('open_pric', ''),
            "high": raw_data.get('high_pric', ''),
            "low": raw_data.get('low_pric', ''),
            "close": raw_data.get('close_pric', ''),
            "change": raw_data.get('pre', ''),
            "change_rate": raw_data.get('flu_rt', ''),
            "volume": raw_data.get('trde_qty', ''),
            "value": raw_data.get('trde_prica', '')
        }
        
        # 호가 정보 구성 (매도호가)
        ask_orders = []
        for i in range(1, 11):
            price = raw_data.get(f'sale_pric{i}', '')
            quantity = raw_data.get(f'sale_qty{i}', '')
            if price and quantity:
                ask_orders.append({"price": price, "quantity": quantity})
        
        # 호가 정보 구성 (매수호가)
        bid_orders = []
        for i in range(1, 11):
            price = raw_data.get(f'buy_pric{i}', '')
            quantity = raw_data.get(f'buy_qty{i}', '')
            if price and quantity:
                bid_orders.append({"price": price, "quantity": quantity})
        
        orderbook = {
            "ask": ask_orders,
            "bid": bid_orders
        }
        
        # LP 정보 구성 (LP 매도호가)
        lp_ask_orders = []
        for i in range(1, 6):
            price = raw_data.get(f'lp_sale_pric{i}', '')
            quantity = raw_data.get(f'lp_sale_qty{i}', '')
            if price and quantity:
                lp_ask_orders.append({"price": price, "quantity": quantity})
        
        # LP 정보 구성 (LP 매수호가)
        lp_bid_orders = []
        for i in range(1, 6):
            price = raw_data.get(f'lp_buy_pric{i}', '')
            quantity = raw_data.get(f'lp_buy_qty{i}', '')
            if price and quantity:
                lp_bid_orders.append({"price": price, "quantity": quantity})
        
        lp_info = {
            "lp_ask": lp_ask_orders,
            "lp_bid": lp_bid_orders
        }
        
        # 시장 데이터 구성
        market_data = {
            "market_cap": raw_data.get('mrkt_cap', ''),
            "foreign_rate": raw_data.get('for_rate', ''),
            "short_selling_rate": raw_data.get('ssts_rt', ''),
            "strength": raw_data.get('cntr_str', '')
        }
        
        structured_data = StructuredMarketInfo(
            timestamp=timestamp,
            basic_info=basic_info,
            orderbook=orderbook,
            lp_info=lp_info,
            market_data=market_data
        )
        
        return structured_data
        
    except Exception as e:
        logger.error(f"시세표성정보 데이터 변환 오류: {str(e)}")
        # 오류 시 기본 구조 반환
        return StructuredMarketInfo(
            timestamp='',
            basic_info={},
            orderbook={"ask": [], "bid": []},
            lp_info={"lp_ask": [], "lp_bid": []},
            market_data={}
        )


def get_stock_name_from_code(stock_code: str) -> str:
    """
    종목코드에서 종목명 추출 (간단한 매핑)
    """
    stock_names = {
        "005930": "삼성전자",
        "000660": "SK하이닉스",
        "373220": "LG에너지솔루션",
        "207940": "삼성바이오로직스",
        "005380": "현대차",
        "006400": "삼성SDI",
        "051910": "LG화학",
        "035420": "NAVER",
        "068270": "셀트리온",
        "035720": "카카오"
    }
    
    return stock_names.get(stock_code, f"종목{stock_code}")


# 테스트용 함수
async def test_ka10007():
    """ka10007 API 테스트"""
    try:
        # 삼성전자 시세표성정보 조회
        test_data = {"stk_cd": "005930"}
        
        result = await fn_ka10007(test_data)
        
        print("=== ka10007 시세표성정보요청 테스트 ===")
        print(f"응답코드: {result.get('Code')}")
        print(f"헤더: {result.get('Header')}")
        
        if result.get('Code') == 200:
            body = result.get('Body', {})
            print(f"응답 데이터:")
            print(f"  날짜: {body.get('date')}")
            print(f"  시간: {body.get('time')}")
            print(f"  종가: {body.get('close_pric')}")
            print(f"  거래량: {body.get('trde_qty')}")
            print(f"  매도1호가: {body.get('sale_pric1')}")
            print(f"  매수1호가: {body.get('buy_pric1')}")
            print(f"  시가총액: {body.get('mrkt_cap')}")
            print(f"  외국인비율: {body.get('for_rate')}")
            print(f"  체결강도: {body.get('cntr_str')}")
        else:
            print(f"오류: {result.get('Error')}")
            
    except Exception as e:
        print(f"테스트 오류: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_ka10007())