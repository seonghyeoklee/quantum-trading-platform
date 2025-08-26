"""키움 일별기관매매종목요청(ka10044) 비즈니스 로직"""

import logging
import httpx
from datetime import datetime
from typing import Dict, Any, Optional, List

# Handle both relative and absolute imports for different execution contexts
try:
    from ..config.settings import settings
    from ..auth.token_manager import token_manager
    from ..models.chart import DailyInstitutionalTradeResponse, StructuredDailyInstitutionalTradeData, DailyInstitutionalTradeApiResponse, DailyInstitutionalTradeData
except ImportError:
    import sys
    from pathlib import Path
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    from kiwoom_api.config.settings import settings
    from kiwoom_api.auth.token_manager import token_manager
    from kiwoom_api.models.chart import DailyInstitutionalTradeResponse, StructuredDailyInstitutionalTradeData, DailyInstitutionalTradeApiResponse, DailyInstitutionalTradeData

logger = logging.getLogger(__name__)


async def fn_ka10044(data: Dict[str, Any], cont_yn: str = 'N', next_key: str = '') -> Dict[str, Any]:
    """
    키움 일별기관매매종목요청 API (ka10044) 호출
    
    Args:
        data: 요청 데이터 {'strt_dt': '20241106', 'end_dt': '20241107', ...}
        cont_yn: 연속조회여부 ('N' or 'Y')
        next_key: 연속조회키
    
    Returns:
        키움 API 응답 데이터
    """
    try:
        # 1. 접근 토큰 획득
        access_token = await token_manager.get_valid_token()
        logger.info(f"키움 일별기관매매종목요청 시작: {data.get('strt_dt')}-{data.get('end_dt')}")
        
        # 2. 요청 URL 및 헤더 구성
        endpoint = '/api/dostk/mrkcond'
        url = settings.kiwoom_base_url + endpoint
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {access_token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'ka10044'
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
                    "api-id": response.headers.get('api-id', 'ka10044')
                },
                "Body": response.json()
            }
            
            logger.info(f"키움 일별기관매매종목요청 완료: {data.get('strt_dt')}-{data.get('end_dt')} (응답코드: {response.status_code})")
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
        logger.error(f"키움 일별기관매매종목요청 오류: {str(e)}")
        return {
            "Code": 500,
            "Error": str(e),
            "Header": {},
            "Body": {}
        }


def convert_daily_institutional_trade_data(raw_data: Dict[str, Any]) -> List[StructuredDailyInstitutionalTradeData]:
    """
    키움 원본 일별기관매매종목 데이터를 구조화된 형태로 변환
    
    Args:
        raw_data: 키움 원본 응답 데이터
    
    Returns:
        구조화된 일별기관매매종목 데이터 리스트
    """
    try:
        trade_list = raw_data.get('daly_orgn_trde_stk', [])
        structured_data = []
        
        for item in trade_list:
            if not item:
                continue
                
            # 매매 정보 구성
            trade_info = {
                "net_quantity": item.get('netprps_qty', ''),  # 순매수수량
                "net_amount": item.get('netprps_amt', '')     # 순매수금액
            }
            
            structured_item = StructuredDailyInstitutionalTradeData(
                code=item.get('stk_cd', ''),
                name=item.get('stk_nm', ''),
                trade_info=trade_info
            )
            
            structured_data.append(structured_item)
            
        return structured_data
        
    except Exception as e:
        logger.error(f"일별기관매매종목 데이터 변환 오류: {str(e)}")
        return []


def get_trade_type_name(trade_type: str) -> str:
    """
    매매구분 코드를 한글명으로 변환
    """
    trade_type_names = {
        "1": "순매도",
        "2": "순매수"
    }
    
    return trade_type_names.get(trade_type, f"구분{trade_type}")


def get_market_type_name(market_type: str) -> str:
    """
    시장구분 코드를 한글명으로 변환
    """
    market_type_names = {
        "001": "코스피",
        "101": "코스닥"
    }
    
    return market_type_names.get(market_type, f"시장{market_type}")


def get_exchange_type_name(exchange_type: str) -> str:
    """
    거래소구분 코드를 한글명으로 변환
    """
    exchange_type_names = {
        "1": "KRX",
        "2": "NXT",
        "3": "통합"
    }
    
    return exchange_type_names.get(exchange_type, f"거래소{exchange_type}")


# 테스트용 함수
async def test_ka10044():
    """ka10044 API 테스트"""
    try:
        # 일별기관매매종목 조회
        test_data = {
            "strt_dt": "20241106",
            "end_dt": "20241107",
            "trde_tp": "1",  # 순매도
            "mrkt_tp": "001",  # 코스피
            "stex_tp": "3"  # 통합
        }
        
        result = await fn_ka10044(test_data)
        
        print("=== ka10044 일별기관매매종목요청 테스트 ===")
        print(f"응답코드: {result.get('Code')}")
        print(f"헤더: {result.get('Header')}")
        
        if result.get('Code') == 200:
            body = result.get('Body', {})
            trade_list = body.get('daly_orgn_trde_stk', [])
            print(f"기관매매종목 수: {len(trade_list)}")
            
            if trade_list:
                first_item = trade_list[0]
                print(f"첫 번째 종목:")
                print(f"  종목코드: {first_item.get('stk_cd')}")
                print(f"  종목명: {first_item.get('stk_nm')}")
                print(f"  순매수수량: {first_item.get('netprps_qty')}")
                print(f"  순매수금액: {first_item.get('netprps_amt')}")
        else:
            print(f"오류: {result.get('Error')}")
            
    except Exception as e:
        print(f"테스트 오류: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_ka10044())