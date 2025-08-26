"""키움 종목별기관매매추이요청(ka10045) 비즈니스 로직"""

import logging
import httpx
from datetime import datetime
from typing import Dict, Any, Optional, List

# Handle both relative and absolute imports for different execution contexts
try:
    from ..config.settings import settings
    from ..auth.token_manager import token_manager
    from ..models.chart import StockInstitutionalTrendResponse, StructuredStockInstitutionalTrendData, StockInstitutionalTrendApiResponse, StockInstitutionalTrendData
except ImportError:
    import sys
    from pathlib import Path
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    from kiwoom_api.config.settings import settings
    from kiwoom_api.auth.token_manager import token_manager
    from kiwoom_api.models.chart import StockInstitutionalTrendResponse, StructuredStockInstitutionalTrendData, StockInstitutionalTrendApiResponse, StockInstitutionalTrendData

logger = logging.getLogger(__name__)


async def fn_ka10045(data: Dict[str, Any], cont_yn: str = 'N', next_key: str = '') -> Dict[str, Any]:
    """
    키움 종목별기관매매추이요청 API (ka10045) 호출
    
    Args:
        data: 요청 데이터 {'stk_cd': '005930', 'strt_dt': '20241201', 'end_dt': '20241225'}
        cont_yn: 연속조회여부 ('N' or 'Y')
        next_key: 연속조회키
    
    Returns:
        키움 API 응답 데이터
    """
    try:
        # 1. 접근 토큰 획득
        access_token = await token_manager.get_valid_token()
        logger.info(f"키움 종목별기관매매추이요청 시작: {data.get('stk_cd')} ({data.get('strt_dt')}-{data.get('end_dt')})")
        
        # 2. 요청 URL 및 헤더 구성
        endpoint = '/api/dostk/mrkcond'
        url = settings.kiwoom_base_url + endpoint
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {access_token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'ka10045'
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
                    "api-id": response.headers.get('api-id', 'ka10045')
                },
                "Body": response.json()
            }
            
            logger.info(f"키움 종목별기관매매추이요청 완료: {data.get('stk_cd')} ({data.get('strt_dt')}-{data.get('end_dt')}) (응답코드: {response.status_code})")
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
        logger.error(f"키움 종목별기관매매추이요청 오류: {str(e)}")
        return {
            "Code": 500,
            "Error": str(e),
            "Header": {},
            "Body": {}
        }


def convert_stock_institutional_trend_data(raw_data: Dict[str, Any]) -> List[StructuredStockInstitutionalTrendData]:
    """
    키움 원본 종목별기관매매추이 데이터를 구조화된 형태로 변환
    
    Args:
        raw_data: 키움 원본 응답 데이터
    
    Returns:
        구조화된 종목별기관매매추이 데이터 리스트
    """
    try:
        trend_list = raw_data.get('stk_orgn_trde_trd', [])
        structured_data = []
        
        for item in trend_list:
            if not item:
                continue
                
            # 기관 정보 구성
            institutional_info = {
                "holding_quantity": item.get('orgn_whld_shqty', ''),  # 기관보유수량
                "weight": item.get('orgn_wght', ''),  # 기관비중
                "estimated_avg_price": item.get('orgn_esti_avrg_pric', ''),  # 기관추정평균가
                "net_purchase_quantity": item.get('orgn_netprps_qty', ''),  # 기관순매수수량
                "net_purchase_amount": item.get('orgn_netprps_amt', ''),  # 기관순매수금액
                "buy_quantity": item.get('orgn_buy_qty', ''),  # 기관매수수량
                "sell_quantity": item.get('orgn_sel_qty', '')  # 기관매도수량
            }
            
            # 외국인 정보 구성
            foreign_info = {
                "holding_quantity": item.get('for_whld_shqty', ''),  # 외국인보유수량
                "weight": item.get('for_wght', ''),  # 외국인비중
                "estimated_avg_price": item.get('for_esti_avrg_pric', ''),  # 외국인추정평균가
                "net_purchase_quantity": item.get('for_netprps_qty', ''),  # 외국인순매수수량
                "net_purchase_amount": item.get('for_netprps_amt', ''),  # 외국인순매수금액
                "buy_quantity": item.get('for_buy_qty', ''),  # 외국인매수수량
                "sell_quantity": item.get('for_sel_qty', '')  # 외국인매도수량
            }
            
            # 개인 정보 구성
            individual_info = {
                "net_purchase_quantity": item.get('ind_netprps_qty', ''),  # 개인순매수수량
                "net_purchase_amount": item.get('ind_netprps_amt', ''),  # 개인순매수금액
                "buy_quantity": item.get('ind_buy_qty', ''),  # 개인매수수량
                "sell_quantity": item.get('ind_sel_qty', '')  # 개인매도수량
            }
            
            # 주가 정보 구성
            price_info = {
                "current_price": item.get('cur_pric', ''),  # 현재가
                "previous_day_change": item.get('prdy_ctrt', ''),  # 전일대비
                "previous_day_change_sign": item.get('prdy_ctrt_sign', ''),  # 전일대비부호
                "previous_volume_ratio": item.get('prdy_vrss_vol_rt', '')  # 전일대비거래량비율
            }
            
            structured_item = StructuredStockInstitutionalTrendData(
                trade_date=item.get('trd_dd', ''),
                stock_code=item.get('stk_cd', ''),
                stock_name=item.get('stk_nm', ''),
                institutional_info=institutional_info,
                foreign_info=foreign_info,
                individual_info=individual_info,
                price_info=price_info
            )
            
            structured_data.append(structured_item)
            
        return structured_data
        
    except Exception as e:
        logger.error(f"종목별기관매매추이 데이터 변환 오류: {str(e)}")
        return []


def get_change_sign_name(sign: str) -> str:
    """
    전일대비부호를 한글명으로 변환
    """
    sign_names = {
        "1": "상한",
        "2": "상승",
        "3": "보합",
        "4": "하한",
        "5": "하락"
    }
    
    return sign_names.get(sign, f"부호{sign}")


# 테스트용 함수
async def test_ka10045():
    """ka10045 API 테스트"""
    try:
        # 종목별기관매매추이 조회 (삼성전자)
        test_data = {
            "stk_cd": "005930",
            "strt_dt": "20241201",
            "end_dt": "20241225"
        }
        
        result = await fn_ka10045(test_data)
        
        print("=== ka10045 종목별기관매매추이요청 테스트 ===")
        print(f"응답코드: {result.get('Code')}")
        print(f"헤더: {result.get('Header')}")
        
        if result.get('Code') == 200:
            body = result.get('Body', {})
            trend_list = body.get('stk_orgn_trde_trd', [])
            print(f"기관매매추이 데이터 수: {len(trend_list)}")
            
            if trend_list:
                first_item = trend_list[0]
                print(f"첫 번째 데이터:")
                print(f"  거래일자: {first_item.get('trd_dd')}")
                print(f"  종목코드: {first_item.get('stk_cd')}")
                print(f"  종목명: {first_item.get('stk_nm')}")
                print(f"  기관보유수량: {first_item.get('orgn_whld_shqty')}")
                print(f"  기관비중: {first_item.get('orgn_wght')}")
                print(f"  기관추정평균가: {first_item.get('orgn_esti_avrg_pric')}")
                print(f"  기관순매수수량: {first_item.get('orgn_netprps_qty')}")
                print(f"  외국인보유수량: {first_item.get('for_whld_shqty')}")
                print(f"  외국인비중: {first_item.get('for_wght')}")
                print(f"  외국인추정평균가: {first_item.get('for_esti_avrg_pric')}")
                print(f"  외국인순매수수량: {first_item.get('for_netprps_qty')}")
                print(f"  현재가: {first_item.get('cur_pric')}")
        else:
            print(f"오류: {result.get('Error')}")
            
    except Exception as e:
        print(f"테스트 오류: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_ka10045())