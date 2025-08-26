"""키움 주식시분요청(ka10006) 비즈니스 로직"""

import logging
import httpx
from datetime import datetime
from typing import Dict, Any, Optional, List

# Handle both relative and absolute imports for different execution contexts
try:
    from ..config.settings import settings
    from ..auth.token_manager import token_manager
    from ..models.chart import MinuteChartResponse, StructuredMinuteData, MinuteChartApiResponse, MinuteChartData
except ImportError:
    import sys
    from pathlib import Path
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    from kiwoom_api.config.settings import settings
    from kiwoom_api.auth.token_manager import token_manager
    from kiwoom_api.models.chart import MinuteChartResponse, StructuredMinuteData, MinuteChartApiResponse, MinuteChartData

logger = logging.getLogger(__name__)


async def _get_valid_token() -> str:
    """유효한 토큰 획듍 (캐시 또는 fn_au10001 호출)"""
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
        # 실패 시 환경변수 고정키 사용 (fallback)
        logger.warning("⚠️ fallback으로 환경변수 고정키 사용")
        return settings.KIWOOM_APP_KEY


async def fn_ka10006(data: Dict[str, Any], cont_yn: str = 'N', next_key: str = '') -> Dict[str, Any]:
    """
    키움 주식시분요청 API (ka10006) 호출
    
    Args:
        data: 요청 데이터 {'stk_cd': '005930'}
        cont_yn: 연속조회여부 ('N' or 'Y')
        next_key: 연속조회키
    
    Returns:
        키움 API 응답 데이터
    """
    try:
        # 1. 접근 토큰 획득
        access_token = await _get_valid_token()
        logger.info(f"키움 주식시분요청 시작: {data.get('stk_cd')}")
        
        # 2. 요청 URL 및 헤더 구성
        endpoint = '/api/dostk/mrkcond'
        url = settings.kiwoom_base_url + endpoint
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {access_token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'ka10006'
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
                    "api-id": response.headers.get('api-id', 'ka10006')
                },
                "Body": response.json()
            }
            
            logger.info(f"키움 주식시분요청 완료: {data.get('stk_cd')} (응답코드: {response.status_code})")
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
        logger.error(f"키움 주식시분요청 오류: {str(e)}")
        return {
            "Code": 500,
            "Error": str(e),
            "Header": {},
            "Body": {}
        }


def convert_minute_data(raw_data: Dict[str, Any]) -> List[StructuredMinuteData]:
    """
    키움 원본 시분 데이터를 구조화된 형태로 변환
    
    Args:
        raw_data: 키움 원본 응답 데이터
    
    Returns:
        구조화된 시분 데이터 리스트
    """
    try:
        # ka10006의 응답 구조는 단일 객체이므로 리스트로 래핑
        structured_data = []
        
        # 가격 데이터 구성
        price_data = {
            "open": raw_data.get('open_pric', ''),
            "high": raw_data.get('high_pric', ''),
            "low": raw_data.get('low_pric', ''),
            "close": raw_data.get('close_pric', ''),
            "change": raw_data.get('pre', ''),
            "change_rate": raw_data.get('flu_rt', '')
        }
        
        # 거래량/거래대금 데이터
        volume_data = {
            "volume": raw_data.get('trde_qty', ''),
            "value": raw_data.get('trde_prica', '')
        }
        
        structured_item = StructuredMinuteData(
            timestamp=raw_data.get('date', ''),
            price_data=price_data,
            volume_data=volume_data,
            strength=raw_data.get('cntr_str', '')
        )
        
        structured_data.append(structured_item)
        return structured_data
        
    except Exception as e:
        logger.error(f"시분 데이터 변환 오류: {str(e)}")
        return []


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
async def test_ka10006():
    """ka10006 API 테스트"""
    try:
        # 삼성전자 시분 조회
        test_data = {"stk_cd": "005930"}
        
        result = await fn_ka10006(test_data)
        
        print("=== ka10006 주식시분요청 테스트 ===")
        print(f"응답코드: {result.get('Code')}")
        print(f"헤더: {result.get('Header')}")
        
        if result.get('Code') == 200:
            body = result.get('Body', {})
            print(f"응답 데이터:")
            print(f"  날짜: {body.get('date')}")
            print(f"  종가: {body.get('close_pric')}")
            print(f"  거래량: {body.get('trde_qty')}")
            print(f"  체결강도: {body.get('cntr_str')}")
        else:
            print(f"오류: {result.get('Error')}")
            
    except Exception as e:
        print(f"테스트 오류: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_ka10006())