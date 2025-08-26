"""키움 신주인수권전체시세요청(ka10011) 비즈니스 로직"""

import logging
import httpx
from datetime import datetime
from typing import Dict, Any, Optional, List

# Handle both relative and absolute imports for different execution contexts
try:
    from ..config.settings import settings
    from ..auth.token_manager import token_manager
    from ..models.chart import NewStockRightsResponse, StructuredNewStockRightsData, NewStockRightsApiResponse, NewStockRightsData
except ImportError:
    import sys
    from pathlib import Path
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    from kiwoom_api.config.settings import settings
    from kiwoom_api.auth.token_manager import token_manager
    from kiwoom_api.models.chart import NewStockRightsResponse, StructuredNewStockRightsData, NewStockRightsApiResponse, NewStockRightsData

logger = logging.getLogger(__name__)


async def fn_ka10011(data: Dict[str, Any], cont_yn: str = 'N', next_key: str = '') -> Dict[str, Any]:
    """
    키움 신주인수권전체시세요청 API (ka10011) 호출
    
    Args:
        data: 요청 데이터 {'newstk_recvrht_tp': '00'}
        cont_yn: 연속조회여부 ('N' or 'Y')
        next_key: 연속조회키
    
    Returns:
        키움 API 응답 데이터
    """
    try:
        # 1. 접근 토큰 획득
        access_token = await token_manager.get_valid_token()
        logger.info(f"키움 신주인수권전체시세요청 시작: {data.get('newstk_recvrht_tp')}")
        
        # 2. 요청 URL 및 헤더 구성
        endpoint = '/api/dostk/mrkcond'
        url = settings.kiwoom_base_url + endpoint
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {access_token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'ka10011'
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
                    "api-id": response.headers.get('api-id', 'ka10011')
                },
                "Body": response.json()
            }
            
            logger.info(f"키움 신주인수권전체시세요청 완료: {data.get('newstk_recvrht_tp')} (응답코드: {response.status_code})")
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
        logger.error(f"키움 신주인수권전체시세요청 오류: {str(e)}")
        return {
            "Code": 500,
            "Error": str(e),
            "Header": {},
            "Body": {}
        }


def convert_new_stock_rights_data(raw_data: Dict[str, Any]) -> List[StructuredNewStockRightsData]:
    """
    키움 원본 신주인수권 시세 데이터를 구조화된 형태로 변환
    
    Args:
        raw_data: 키움 원본 응답 데이터
    
    Returns:
        구조화된 신주인수권 시세 데이터 리스트
    """
    try:
        rights_list = raw_data.get('newstk_recvrht_mrpr', [])
        structured_data = []
        
        for item in rights_list:
            if not item:
                continue
                
            # 가격 정보 구성
            price_info = {
                "current": item.get('cur_prc', ''),
                "open": item.get('open_pric', ''),
                "high": item.get('high_pric', ''),
                "low": item.get('low_pric', ''),
                "change": item.get('pred_pre', ''),
                "change_rate": item.get('flu_rt', ''),
                "change_sign": item.get('pred_pre_sig', '')
            }
            
            # 호가 정보 구성
            bid_info = {
                "best_ask": item.get('fpr_sel_bid', ''),  # 최우선매도호가
                "best_bid": item.get('fpr_buy_bid', '')   # 최우선매수호가
            }
            
            # 거래량 정보 구성
            volume_info = {
                "volume": item.get('acc_trde_qty', '')
            }
            
            structured_item = StructuredNewStockRightsData(
                code=item.get('stk_cd', ''),
                name=item.get('stk_nm', ''),
                price_info=price_info,
                bid_info=bid_info,
                volume_info=volume_info
            )
            
            structured_data.append(structured_item)
            
        return structured_data
        
    except Exception as e:
        logger.error(f"신주인수권 시세 데이터 변환 오류: {str(e)}")
        return []


def get_rights_type_name(rights_type: str) -> str:
    """
    신주인수권구분 코드를 한글명으로 변환
    """
    rights_type_names = {
        "00": "전체",
        "05": "신주인수권증권",
        "07": "신주인수권증서"
    }
    
    return rights_type_names.get(rights_type, f"구분{rights_type}")


# 테스트용 함수
async def test_ka10011():
    """ka10011 API 테스트"""
    try:
        # 신주인수권 전체 시세 조회
        test_data = {"newstk_recvrht_tp": "00"}
        
        result = await fn_ka10011(test_data)
        
        print("=== ka10011 신주인수권전체시세요청 테스트 ===")
        print(f"응답코드: {result.get('Code')}")
        print(f"헤더: {result.get('Header')}")
        
        if result.get('Code') == 200:
            body = result.get('Body', {})
            rights_list = body.get('newstk_recvrht_mrpr', [])
            print(f"신주인수권 종목 수: {len(rights_list)}")
            
            if rights_list:
                first_item = rights_list[0]
                print(f"첫 번째 종목:")
                print(f"  종목코드: {first_item.get('stk_cd')}")
                print(f"  종목명: {first_item.get('stk_nm')}")
                print(f"  현재가: {first_item.get('cur_prc')}")
                print(f"  전일대비: {first_item.get('pred_pre')}")
                print(f"  등락율: {first_item.get('flu_rt')}")
                print(f"  거래량: {first_item.get('acc_trde_qty')}")
        else:
            print(f"오류: {result.get('Error')}")
            
    except Exception as e:
        print(f"테스트 오류: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_ka10011())