"""키움 주식호가요청(ka10004) 비즈니스 로직"""

import logging
import httpx
from datetime import datetime
from typing import Dict, Any, Optional

# Handle both relative and absolute imports for different execution contexts
try:
    from ..config.settings import settings
    from ..auth.token_manager import token_manager
    from ..models.orderbook import OrderbookResponse, OrderbookData, OrderbookApiResponse
except ImportError:
    import sys
    from pathlib import Path
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    from kiwoom_api.config.settings import settings
    from kiwoom_api.auth.token_manager import token_manager
    from kiwoom_api.models.orderbook import OrderbookResponse, OrderbookData, OrderbookApiResponse

logger = logging.getLogger(__name__)


async def _get_valid_token() -> str:
    """유효한 토큰 획득 (캐시 또는 fn_au10001 호출)"""
    try:
        from ..auth.token_cache import token_cache
        from ..functions.auth import fn_au10001
    except ImportError:
        from kiwoom_api.auth.token_cache import token_cache
        from kiwoom_api.functions.auth import fn_au10001
    
    # 1. 캐시에서 유효한 토큰 확인
    cached_token = await token_cache.get_default_token()
    if cached_token and not cached_token.is_expired():
        logger.info("✅ 캐시된 토큰 사용")
        return cached_token.token
    
    # 2. 새 토큰 발급
    logger.info("🔄 새 토큰 발급 중...")
    auth_result = await fn_au10001()
    
    if auth_result['Code'] == 200 and auth_result['Body'].get('token'):
        token = auth_result['Body']['token']
        logger.info("✅ 새 토큰 발급 성공")
        return token
    else:
        logger.error(f"❌ 토큰 발급 실패: {auth_result}")
        # 실패 시 예외 발생 (실제 데이터만 사용)
        raise Exception(f"토큰 발급 실패: {auth_result}")


async def fn_ka10004(data: Dict[str, Any], cont_yn: str = 'N', next_key: str = '') -> Dict[str, Any]:
    """
    키움 주식호가요청 API (ka10004) 호출
    
    Args:
        data: 요청 데이터 {'stk_cd': '{종목코드}'}
        cont_yn: 연속조회여부 ('N' or 'Y')
        next_key: 연속조회키
    
    Returns:
        키움 API 응답 데이터
    """
    try:
        # 1. 접근 토큰 획득 (fn_au10001 기반)
        access_token = await _get_valid_token()
        logger.info(f"키움 주식호가요청 시작: {data.get('stk_cd')}")
        
        # 2. 요청 URL 및 헤더 구성
        endpoint = '/api/dostk/mrkcond'
        url = settings.kiwoom_base_url + endpoint
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {access_token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'ka10004'
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
                    "api-id": response.headers.get('api-id', 'ka10004')
                },
                "Body": response.json()
            }
            
            logger.info(f"키움 주식호가요청 완료: {data.get('stk_cd')} (응답코드: {response.status_code})")
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
        logger.error(f"키움 주식호가요청 오류: {str(e)}")
        return {
            "Code": 500,
            "Error": str(e),
            "Header": {},
            "Body": {}
        }


def convert_orderbook_data(raw_data: Dict[str, Any]) -> OrderbookData:
    """
    키움 원본 호가 데이터를 구조화된 형태로 변환
    
    Args:
        raw_data: 키움 원본 응답 데이터
    
    Returns:
        구조화된 호가 데이터
    """
    try:
        # 매도호가 리스트 (1-10차)
        ask_prices = [
            raw_data.get('sel_fpr_bid', ''),       # 1차 (최우선)
            raw_data.get('sel_2th_pre_bid', ''),   # 2차
            raw_data.get('sel_3th_pre_bid', ''),   # 3차
            raw_data.get('sel_4th_pre_bid', ''),   # 4차
            raw_data.get('sel_5th_pre_bid', ''),   # 5차
            raw_data.get('sel_6th_pre_bid', ''),   # 6차
            raw_data.get('sel_7th_pre_bid', ''),   # 7차
            raw_data.get('sel_8th_pre_bid', ''),   # 8차
            raw_data.get('sel_9th_pre_bid', ''),   # 9차
            raw_data.get('sel_10th_pre_bid', '')   # 10차
        ]
        
        # 매도잔량 리스트 (1-10차)
        ask_volumes = [
            raw_data.get('sel_fpr_req', ''),       # 1차 (최우선)
            raw_data.get('sel_2th_pre_req', ''),   # 2차
            raw_data.get('sel_3th_pre_req', ''),   # 3차
            raw_data.get('sel_4th_pre_req', ''),   # 4차
            raw_data.get('sel_5th_pre_req', ''),   # 5차
            raw_data.get('sel_6th_pre_req', ''),   # 6차
            raw_data.get('sel_7th_pre_req', ''),   # 7차
            raw_data.get('sel_8th_pre_req', ''),   # 8차
            raw_data.get('sel_9th_pre_req', ''),   # 9차
            raw_data.get('sel_10th_pre_req', '')   # 10차
        ]
        
        # 매도잔량대비 리스트 (1-10차)
        ask_changes = [
            raw_data.get('sel_1th_pre_req_pre', ''), # 1차
            raw_data.get('sel_2th_pre_req_pre', ''), # 2차
            raw_data.get('sel_3th_pre_req_pre', ''), # 3차
            raw_data.get('sel_4th_pre_req_pre', ''), # 4차
            raw_data.get('sel_5th_pre_req_pre', ''), # 5차
            raw_data.get('sel_6th_pre_req_pre', ''), # 6차
            raw_data.get('sel_7th_pre_req_pre', ''), # 7차
            raw_data.get('sel_8th_pre_req_pre', ''), # 8차
            raw_data.get('sel_9th_pre_req_pre', ''), # 9차
            raw_data.get('sel_10th_pre_req_pre', '') # 10차
        ]
        
        # 매수호가 리스트 (1-10차)
        bid_prices = [
            raw_data.get('buy_fpr_bid', ''),       # 1차 (최우선)
            raw_data.get('buy_2th_pre_bid', ''),   # 2차
            raw_data.get('buy_3th_pre_bid', ''),   # 3차
            raw_data.get('buy_4th_pre_bid', ''),   # 4차
            raw_data.get('buy_5th_pre_bid', ''),   # 5차
            raw_data.get('buy_6th_pre_bid', ''),   # 6차
            raw_data.get('buy_7th_pre_bid', ''),   # 7차
            raw_data.get('buy_8th_pre_bid', ''),   # 8차
            raw_data.get('buy_9th_pre_bid', ''),   # 9차
            raw_data.get('buy_10th_pre_bid', '')   # 10차
        ]
        
        # 매수잔량 리스트 (1-10차)
        bid_volumes = [
            raw_data.get('buy_fpr_req', ''),       # 1차 (최우선)
            raw_data.get('buy_2th_pre_req', ''),   # 2차
            raw_data.get('buy_3th_pre_req', ''),   # 3차
            raw_data.get('buy_4th_pre_req', ''),   # 4차
            raw_data.get('buy_5th_pre_req', ''),   # 5차
            raw_data.get('buy_6th_pre_req', ''),   # 6차
            raw_data.get('buy_7th_pre_req', ''),   # 7차
            raw_data.get('buy_8th_pre_req', ''),   # 8차
            raw_data.get('buy_9th_pre_req', ''),   # 9차
            raw_data.get('buy_10th_pre_req', '')   # 10차
        ]
        
        # 매수잔량대비 리스트 (1-10차)
        bid_changes = [
            raw_data.get('buy_1th_pre_req_pre', ''), # 1차
            raw_data.get('buy_2th_pre_req_pre', ''), # 2차
            raw_data.get('buy_3th_pre_req_pre', ''), # 3차
            raw_data.get('buy_4th_pre_req_pre', ''), # 4차
            raw_data.get('buy_5th_pre_req_pre', ''), # 5차
            raw_data.get('buy_6th_pre_req_pre', ''), # 6차
            raw_data.get('buy_7th_pre_req_pre', ''), # 7차
            raw_data.get('buy_8th_pre_req_pre', ''), # 8차
            raw_data.get('buy_9th_pre_req_pre', ''), # 9차
            raw_data.get('buy_10th_pre_req_pre', '') # 10차
        ]
        
        # 구조화된 데이터 반환
        return OrderbookData(
            timestamp=raw_data.get('bid_req_base_tm', datetime.now().strftime('%H%M%S')),
            ask_prices=ask_prices,
            ask_volumes=ask_volumes,
            ask_changes=ask_changes,
            bid_prices=bid_prices,
            bid_volumes=bid_volumes,
            bid_changes=bid_changes,
            total_ask_volume=raw_data.get('tot_sel_req', ''),
            total_bid_volume=raw_data.get('tot_buy_req', ''),
            total_ask_change=raw_data.get('tot_sel_req_jub_pre', ''),
            total_bid_change=raw_data.get('tot_buy_req_jub_pre', ''),
            after_hours_ask_volume=raw_data.get('ovt_sel_req', ''),
            after_hours_bid_volume=raw_data.get('ovt_buy_req', '')
        )
        
    except Exception as e:
        logger.error(f"호가 데이터 변환 오류: {str(e)}")
        # 빈 데이터 반환
        return OrderbookData(
            timestamp=datetime.now().strftime('%H%M%S'),
            ask_prices=[''] * 10,
            ask_volumes=[''] * 10,
            ask_changes=[''] * 10,
            bid_prices=[''] * 10,
            bid_volumes=[''] * 10,
            bid_changes=[''] * 10,
            total_ask_volume='',
            total_bid_volume='',
            total_ask_change='',
            total_bid_change='',
            after_hours_ask_volume='',
            after_hours_bid_volume=''
        )


def get_stock_name_from_code(stock_code: str) -> str:
    """
    종목코드에서 종목명 추출 (간단한 매핑)
    """
    stock_names = {
        # TODO: 실제 API에서 종목명 조회
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


# 테스트용 함수는 제거됨 (실제 데이터만 사용)