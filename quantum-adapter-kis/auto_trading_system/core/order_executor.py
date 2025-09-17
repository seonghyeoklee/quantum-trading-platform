"""
주문 실행기
KIS API를 통한 실제 주문 실행
"""

from typing import Dict, Any, Optional, Callable
import asyncio
import logging
from datetime import datetime
import sys
import os

# 기존 KIS API 임포트
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from .data_types import Order, OrderStatus, SignalType


class OrderExecutor:
    """주문 실행기"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Args:
            config: 실행기 설정
        """
        self.config = config or {}

        # 로거 초기화 (먼저)
        self.logger = logging.getLogger("order_executor")

        # 설정
        self.environment = self.config.get('environment', 'vps')  # vps (모의투자) 또는 prod (실전투자)
        self.account_number = self.config.get('account_number', '')
        self.dry_run = self.config.get('dry_run', True)  # 시뮬레이션 모드
        self.execution_delay = self.config.get('execution_delay', 0.5)  # 실행 지연 (초)

        # 상태 관리
        self.is_connected = False
        self.execution_stats = {
            'total_orders': 0,
            'successful_orders': 0,
            'failed_orders': 0,
            'last_execution_time': None
        }

        # KIS API 초기화
        self.kis_client = None
        self._initialize_kis_client()

    def _initialize_kis_client(self):
        """KIS API 클라이언트 초기화"""
        try:
            # 기존 KIS 인증 모듈 사용
            from examples_llm.kis_auth import auth

            # 토큰 발급 (auth 함수는 자동으로 토큰을 처리함)
            auth(svr=self.environment, product="01")
            self.is_connected = True
            self.logger.info(f"KIS API 연결 성공 ({self.environment})")

        except Exception as e:
            self.logger.error(f"KIS API 초기화 실패: {e}")
            # 오류가 발생해도 시뮬레이션 모드에서는 계속 실행
            if self.dry_run:
                self.logger.info("시뮬레이션 모드로 계속 실행")

    async def execute_order(self, symbol: str, order: Order) -> bool:
        """
        주문 실행

        Args:
            symbol: 종목 코드
            order: 주문 정보

        Returns:
            실행 성공 여부
        """
        try:
            # 통계 업데이트
            self.execution_stats['total_orders'] += 1
            self.execution_stats['last_execution_time'] = datetime.now()

            # 드라이런 모드 확인
            if self.dry_run:
                return await self._simulate_order(symbol, order)

            # 실제 주문 실행
            if not self.is_connected:
                self.logger.error("KIS API 연결되지 않음")
                self.execution_stats['failed_orders'] += 1
                return False

            # 실행 지연
            if self.execution_delay > 0:
                await asyncio.sleep(self.execution_delay)

            # 주문 타입에 따른 실행
            if order.signal_type == SignalType.BUY:
                success = await self._execute_buy_order(symbol, order)
            elif order.signal_type == SignalType.SELL:
                success = await self._execute_sell_order(symbol, order)
            else:
                self.logger.error(f"지원하지 않는 주문 타입: {order.signal_type}")
                success = False

            # 통계 업데이트
            if success:
                self.execution_stats['successful_orders'] += 1
            else:
                self.execution_stats['failed_orders'] += 1

            return success

        except Exception as e:
            self.logger.error(f"주문 실행 오류 [{symbol}]: {e}")
            self.execution_stats['failed_orders'] += 1
            return False

    async def _simulate_order(self, symbol: str, order: Order) -> bool:
        """주문 시뮬레이션"""
        # 시뮬레이션 지연
        await asyncio.sleep(0.1)

        # 임의의 실패율 (5%)
        import random
        if random.random() < 0.05:
            self.logger.info(f"시뮬레이션 주문 실패: {symbol} {order.signal_type.value}")
            return False

        self.logger.info(
            f"시뮬레이션 주문 성공: {symbol} {order.signal_type.value} "
            f"{order.quantity}주 @ {order.price:,}원"
        )
        return True

    async def _execute_buy_order(self, symbol: str, order: Order) -> bool:
        """매수 주문 실행"""
        try:
            # KIS API 매수 주문 (실제 구현 시 기존 주문 API 사용)
            from examples_llm.domestic_stock.order_cash import order_cash

            # 주문 파라미터 구성
            order_params = {
                'symbol': symbol,
                'quantity': str(order.quantity),
                'price': str(int(order.price)),
                'order_type': '01',  # 지정가
                'order_side': 'buy'
            }

            # KIS API 호출 (여기서는 시뮬레이션)
            self.logger.info(f"KIS 매수 주문: {symbol} {order.quantity}주 @ {order.price:,}원")

            # 실제로는 order_cash 함수를 호출하여 주문 실행
            # result = await order_cash(**order_params)
            # return result.get('success', False)

            # 임시 시뮬레이션
            return True

        except Exception as e:
            self.logger.error(f"매수 주문 실행 오류 [{symbol}]: {e}")
            return False

    async def _execute_sell_order(self, symbol: str, order: Order) -> bool:
        """매도 주문 실행"""
        try:
            # KIS API 매도 주문 (실제 구현 시 기존 주문 API 사용)
            self.logger.info(f"KIS 매도 주문: {symbol} {order.quantity}주 @ {order.price:,}원")

            # 실제로는 order_cash 함수를 호출하여 주문 실행 (매도)
            # order_params = {
            #     'symbol': symbol,
            #     'quantity': str(order.quantity),
            #     'price': str(int(order.price)),
            #     'order_type': '01',  # 지정가
            #     'order_side': 'sell'
            # }
            # result = await order_cash(**order_params)
            # return result.get('success', False)

            # 임시 시뮬레이션
            return True

        except Exception as e:
            self.logger.error(f"매도 주문 실행 오류 [{symbol}]: {e}")
            return False

    def get_account_balance(self) -> Dict[str, Any]:
        """계좌 잔고 조회"""
        try:
            # KIS API 잔고 조회 (실제 구현 시 기존 잔고 API 사용)
            # from examples_llm.domestic_stock.inquire_balance import inquire_balance
            # balance_result = inquire_balance()

            # 임시 시뮬레이션 데이터
            return {
                'cash_balance': 10000000,  # 현금 잔고
                'total_balance': 10000000,  # 총 평가금액
                'available_cash': 10000000,  # 매수 가능 현금
                'positions': []  # 보유 종목 목록
            }

        except Exception as e:
            self.logger.error(f"잔고 조회 오류: {e}")
            return {}

    def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """주문 상태 조회"""
        try:
            # KIS API 주문 조회 (실제 구현 시 기존 주문 조회 API 사용)
            # 임시 시뮬레이션
            return {
                'order_id': order_id,
                'status': 'FILLED',
                'filled_quantity': 100,
                'filled_price': 50000,
                'filled_time': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"주문 상태 조회 오류 [{order_id}]: {e}")
            return None

    def cancel_order(self, order_id: str) -> bool:
        """주문 취소"""
        try:
            # KIS API 주문 취소 (실제 구현 시 기존 주문 취소 API 사용)
            self.logger.info(f"주문 취소: {order_id}")

            # 임시 시뮬레이션
            return True

        except Exception as e:
            self.logger.error(f"주문 취소 오류 [{order_id}]: {e}")
            return False

    def set_dry_run(self, dry_run: bool):
        """시뮬레이션 모드 설정"""
        self.dry_run = dry_run
        mode = "시뮬레이션" if dry_run else "실제"
        self.logger.info(f"주문 실행 모드 변경: {mode}")

    def get_execution_stats(self) -> Dict[str, Any]:
        """실행 통계 조회"""
        total = self.execution_stats['total_orders']
        success_rate = (self.execution_stats['successful_orders'] / total * 100) if total > 0 else 0

        return {
            'total_orders': total,
            'successful_orders': self.execution_stats['successful_orders'],
            'failed_orders': self.execution_stats['failed_orders'],
            'success_rate': success_rate,
            'last_execution_time': self.execution_stats['last_execution_time'].isoformat() if self.execution_stats['last_execution_time'] else None,
            'is_connected': self.is_connected,
            'environment': self.environment,
            'dry_run': self.dry_run
        }

    def reconnect(self):
        """KIS API 재연결"""
        self.logger.info("KIS API 재연결 시도")
        self._initialize_kis_client()

    def health_check(self) -> bool:
        """연결 상태 확인"""
        try:
            # KIS API 상태 확인 (실제 구현 시 ping 등 사용)
            return self.is_connected

        except Exception as e:
            self.logger.error(f"상태 확인 오류: {e}")
            return False