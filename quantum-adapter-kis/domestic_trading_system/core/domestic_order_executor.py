"""
국내주식 주문 실행기
KIS API를 통한 실제 주문 실행
"""

import asyncio
import logging
import sys
import os
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from domestic_trading_system.core.domestic_data_types import TradingSignal


class DomesticOrderExecutor:
    """국내주식 실제 주문 실행기"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger("domestic_order_executor")

        # 설정
        self.account_number = config.get('account_number')
        self.account_product_code = config.get('account_product_code', '01')
        self.execution_delay = config.get('execution_delay', 0.1)

        # KIS API 설정 (from main KIS auth)
        self.kis_appkey = None
        self.kis_appsecret = None
        self.access_token = None
        self.environment = config.get('environment', 'prod')

        # API URL 설정
        if self.environment == "prod":
            self.api_base_url = "https://openapi.koreainvestment.com:9443"
        else:
            self.api_base_url = "https://openapivts.koreainvestment.com:29443"

        # 주문 통계
        self.total_orders = 0
        self.successful_orders = 0
        self.failed_orders = 0

    def set_credentials(self, appkey: str, appsecret: str, access_token: str):
        """KIS API 인증 정보 설정"""
        self.kis_appkey = appkey
        self.kis_appsecret = appsecret
        self.access_token = access_token
        self.logger.info("KIS API 인증 정보 설정 완료")

    async def execute_order(self, signal: TradingSignal) -> Dict[str, Any]:
        """주문 실행"""
        try:
            self.total_orders += 1

            # 지연 시간 적용
            if self.execution_delay > 0:
                await asyncio.sleep(self.execution_delay)

            # 주문 타입에 따른 처리
            if signal.signal_type == "BUY":
                result = await self._execute_buy_order(signal)
            elif signal.signal_type == "SELL":
                result = await self._execute_sell_order(signal)
            else:
                return {
                    'success': False,
                    'error': f'지원하지 않는 주문 타입: {signal.signal_type}'
                }

            if result.get('success', False):
                self.successful_orders += 1
                self.logger.info(f"✅ 주문 성공: {signal.symbol} {signal.signal_type} {signal.target_quantity}주")
            else:
                self.failed_orders += 1
                self.logger.error(f"❌ 주문 실패: {signal.symbol} - {result.get('error', 'Unknown error')}")

            return result

        except Exception as e:
            self.failed_orders += 1
            self.logger.error(f"주문 실행 오류: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _execute_buy_order(self, signal: TradingSignal) -> Dict[str, Any]:
        """매수 주문 실행"""
        try:
            # KIS API 매수 주문 (TTTC0802U)
            order_data = {
                "CANO": self.account_number,            # 계좌번호
                "ACNT_PRDT_CD": self.account_product_code,  # 계좌상품코드
                "PDNO": signal.symbol,                  # 종목코드
                "ORD_DVSN": "01",                      # 주문구분 (01: 시장가)
                "ORD_QTY": str(signal.target_quantity), # 주문수량
                "ORD_UNPR": "0",                       # 주문단가 (시장가는 0)
            }

            headers = {
                "Content-Type": "application/json",
                "authorization": f"Bearer {self.access_token}",
                "appkey": self.kis_appkey,
                "appsecret": self.kis_appsecret,
                "tr_id": "TTTC0802U",                  # 주식 현금 매수 주문
                "custtype": "P"                        # 개인
            }

            url = f"{self.api_base_url}/uapi/domestic-stock/v1/trading/order-cash"

            # 주문 실행
            response = requests.post(url, headers=headers, data=json.dumps(order_data))

            if response.status_code == 200:
                result = response.json()
                rt_cd = result.get("rt_cd", "1")

                if rt_cd == "0":  # 성공
                    order_id = result.get("output", {}).get("ODNO", "")
                    return {
                        'success': True,
                        'order_id': order_id,
                        'symbol': signal.symbol,
                        'type': 'BUY',
                        'quantity': signal.target_quantity,
                        'price': signal.price,
                        'timestamp': datetime.now().isoformat(),
                        'response': result
                    }
                else:  # 실패
                    error_msg = result.get("msg1", "주문 실패")
                    return {
                        'success': False,
                        'error': error_msg,
                        'response': result
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }

        except Exception as e:
            self.logger.error(f"매수 주문 실행 오류: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _execute_sell_order(self, signal: TradingSignal) -> Dict[str, Any]:
        """매도 주문 실행"""
        try:
            # KIS API 매도 주문 (TTTC0801U)
            order_data = {
                "CANO": self.account_number,            # 계좌번호
                "ACNT_PRDT_CD": self.account_product_code,  # 계좌상품코드
                "PDNO": signal.symbol,                  # 종목코드
                "ORD_DVSN": "01",                      # 주문구분 (01: 시장가)
                "ORD_QTY": str(signal.target_quantity), # 주문수량
                "ORD_UNPR": "0",                       # 주문단가 (시장가는 0)
            }

            headers = {
                "Content-Type": "application/json",
                "authorization": f"Bearer {self.access_token}",
                "appkey": self.kis_appkey,
                "appsecret": self.kis_appsecret,
                "tr_id": "TTTC0801U",                  # 주식 현금 매도 주문
                "custtype": "P"                        # 개인
            }

            url = f"{self.api_base_url}/uapi/domestic-stock/v1/trading/order-cash"

            # 주문 실행
            response = requests.post(url, headers=headers, data=json.dumps(order_data))

            if response.status_code == 200:
                result = response.json()
                rt_cd = result.get("rt_cd", "1")

                if rt_cd == "0":  # 성공
                    order_id = result.get("output", {}).get("ODNO", "")
                    return {
                        'success': True,
                        'order_id': order_id,
                        'symbol': signal.symbol,
                        'type': 'SELL',
                        'quantity': signal.target_quantity,
                        'price': signal.price,
                        'timestamp': datetime.now().isoformat(),
                        'response': result
                    }
                else:  # 실패
                    error_msg = result.get("msg1", "주문 실패")
                    return {
                        'success': False,
                        'error': error_msg,
                        'response': result
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }

        except Exception as e:
            self.logger.error(f"매도 주문 실행 오류: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """주문 상태 조회"""
        try:
            # KIS API 주문 조회 (TTTC8001R)
            params = {
                "CANO": self.account_number,
                "ACNT_PRDT_CD": self.account_product_code,
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
                "INQR_DVSN": "00",                     # 조회구분 (00: 전체)
                "ODNO": order_id                       # 주문번호
            }

            headers = {
                "Content-Type": "application/json",
                "authorization": f"Bearer {self.access_token}",
                "appkey": self.kis_appkey,
                "appsecret": self.kis_appsecret,
                "tr_id": "TTTC8001R",                  # 주식 주문 조회
                "custtype": "P"
            }

            url = f"{self.api_base_url}/uapi/domestic-stock/v1/trading/inquire-order"

            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'data': result
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }

        except Exception as e:
            self.logger.error(f"주문 상태 조회 오류: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def cancel_order(self, order_id: str, symbol: str, quantity: int) -> Dict[str, Any]:
        """주문 취소"""
        try:
            # KIS API 주문 취소 (TTTC0803U)
            order_data = {
                "CANO": self.account_number,
                "ACNT_PRDT_CD": self.account_product_code,
                "PDNO": symbol,
                "ORGN_ODNO": order_id,                 # 원주문번호
                "ORD_DVSN": "00",                      # 주문구분 (00: 지정가)
                "RVSE_CNCL_DVSN_CD": "02",            # 정정취소구분 (02: 취소)
                "ORD_QTY": "0",                        # 주문수량 (취소시 0)
                "ORD_UNPR": "0",                       # 주문단가 (취소시 0)
                "QTY_ALL_ORD_YN": "Y"                 # 잔량전부주문여부
            }

            headers = {
                "Content-Type": "application/json",
                "authorization": f"Bearer {self.access_token}",
                "appkey": self.kis_appkey,
                "appsecret": self.kis_appsecret,
                "tr_id": "TTTC0803U",                  # 주식 주문 정정취소
                "custtype": "P"
            }

            url = f"{self.api_base_url}/uapi/domestic-stock/v1/trading/order-rvsecncl"

            response = requests.post(url, headers=headers, data=json.dumps(order_data))

            if response.status_code == 200:
                result = response.json()
                rt_cd = result.get("rt_cd", "1")

                if rt_cd == "0":
                    return {
                        'success': True,
                        'message': '주문 취소 성공',
                        'response': result
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get("msg1", "주문 취소 실패"),
                        'response': result
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }

        except Exception as e:
            self.logger.error(f"주문 취소 오류: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_statistics(self) -> Dict[str, Any]:
        """주문 통계 조회"""
        success_rate = 0.0
        if self.total_orders > 0:
            success_rate = self.successful_orders / self.total_orders

        return {
            'total_orders': self.total_orders,
            'successful_orders': self.successful_orders,
            'failed_orders': self.failed_orders,
            'success_rate': success_rate
        }


class MockDomesticOrderExecutor:
    """모의 주문 실행기 (테스트/데모용)"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger("mock_domestic_order_executor")
        self.execution_delay = config.get('execution_delay', 0.1)

        # 통계
        self.total_orders = 0
        self.successful_orders = 0

    async def execute_order(self, signal: TradingSignal) -> Dict[str, Any]:
        """모의 주문 실행"""
        try:
            self.total_orders += 1

            # 지연 시간 적용
            if self.execution_delay > 0:
                await asyncio.sleep(self.execution_delay)

            # 90% 확률로 성공 (실제 상황 시뮬레이션)
            import random
            success = random.random() > 0.1

            if success:
                self.successful_orders += 1
                order_id = f"MOCK_{signal.symbol}_{datetime.now().strftime('%H%M%S')}"

                self.logger.info(f"🎯 모의 주문 성공: {signal.symbol} {signal.signal_type} {signal.target_quantity}주")

                return {
                    'success': True,
                    'order_id': order_id,
                    'symbol': signal.symbol,
                    'type': signal.signal_type,
                    'quantity': signal.target_quantity,
                    'price': signal.price,
                    'timestamp': datetime.now().isoformat(),
                    'mock': True
                }
            else:
                self.logger.warning(f"🎯 모의 주문 실패: {signal.symbol} (시뮬레이션)")
                return {
                    'success': False,
                    'error': '모의 주문 실패 (시뮬레이션)',
                    'mock': True
                }

        except Exception as e:
            self.logger.error(f"모의 주문 오류: {e}")
            return {
                'success': False,
                'error': str(e),
                'mock': True
            }

    def get_statistics(self) -> Dict[str, Any]:
        """주문 통계 조회"""
        success_rate = 0.0
        if self.total_orders > 0:
            success_rate = self.successful_orders / self.total_orders

        return {
            'total_orders': self.total_orders,
            'successful_orders': self.successful_orders,
            'failed_orders': self.total_orders - self.successful_orders,
            'success_rate': success_rate,
            'mock': True
        }


# 테스트 함수
async def test_mock_order_executor():
    """모의 주문 실행기 테스트"""
    print("=== 모의 국내주식 주문 실행기 테스트 ===")

    # 설정
    config = {
        'execution_delay': 0.1
    }

    # 모의 실행기 초기화
    executor = MockDomesticOrderExecutor(config)

    # 테스트 신호 생성
    test_signal = TradingSignal(
        symbol="005930",
        signal_type="BUY",
        confidence=0.85,
        reason="테스트 매수 신호",
        price=75000,
        timestamp=datetime.now(),
        strategy_name="TestStrategy",
        target_quantity=1
    )

    # 주문 실행 테스트
    result = await executor.execute_order(test_signal)
    print(f"주문 결과: {result}")

    # 통계 조회
    stats = executor.get_statistics()
    print(f"주문 통계: {stats}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(test_mock_order_executor())