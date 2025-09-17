"""
포지션 관리자
포지션의 생성, 수정, 삭제를 관리
"""

from typing import Dict, Optional, List
from datetime import datetime
import logging

from .data_types import Position, PositionType


class PositionManager:
    """포지션 관리자"""

    def __init__(self):
        """초기화"""
        self.positions: Dict[str, Position] = {}  # symbol -> Position
        self.logger = logging.getLogger("position_manager")

    def open_position(
        self,
        symbol: str,
        position_type: PositionType,
        quantity: int,
        entry_price: float,
        entry_time: datetime
    ) -> Position:
        """
        포지션 열기

        Args:
            symbol: 종목 코드
            position_type: 포지션 타입
            quantity: 수량
            entry_price: 진입가
            entry_time: 진입 시간

        Returns:
            생성된 포지션
        """
        # 기존 포지션이 있으면 경고
        if symbol in self.positions:
            self.logger.warning(f"기존 포지션 덮어쓰기: {symbol}")

        position = Position(
            symbol=symbol,
            position_type=position_type,
            quantity=quantity,
            entry_price=entry_price,
            current_price=entry_price,  # 초기값은 진입가
            entry_time=entry_time
        )

        self.positions[symbol] = position

        self.logger.info(
            f"포지션 열기: {symbol} {position_type.value} {quantity}주 @ {entry_price:,}원"
        )

        return position

    def close_position(self, symbol: str) -> Optional[Position]:
        """
        포지션 닫기

        Args:
            symbol: 종목 코드

        Returns:
            닫힌 포지션 (없으면 None)
        """
        if symbol not in self.positions:
            self.logger.warning(f"닫을 포지션이 없음: {symbol}")
            return None

        position = self.positions.pop(symbol)

        self.logger.info(
            f"포지션 닫기: {symbol} {position.position_type.value} "
            f"손익: {position.get_unrealized_pnl():,.0f}원 "
            f"({position.get_unrealized_pnl_percent():.2f}%)"
        )

        return position

    def update_position_price(self, symbol: str, current_price: float):
        """
        포지션 현재가 업데이트

        Args:
            symbol: 종목 코드
            current_price: 현재가
        """
        if symbol in self.positions:
            self.positions[symbol].current_price = current_price

    def update_position_quantity(self, symbol: str, quantity_change: int):
        """
        포지션 수량 변경

        Args:
            symbol: 종목 코드
            quantity_change: 수량 변화 (양수: 추가, 음수: 감소)
        """
        if symbol not in self.positions:
            self.logger.warning(f"수량 변경할 포지션이 없음: {symbol}")
            return

        position = self.positions[symbol]
        new_quantity = position.quantity + quantity_change

        if new_quantity == 0:
            # 수량이 0이 되면 포지션 닫기
            self.close_position(symbol)
        elif (position.quantity > 0 and new_quantity < 0) or (position.quantity < 0 and new_quantity > 0):
            # 포지션 방향이 바뀌는 경우
            self.logger.warning(f"포지션 방향 변경: {symbol} {position.quantity} -> {new_quantity}")
            position.quantity = new_quantity
        else:
            # 일반적인 수량 변경
            position.quantity = new_quantity

        self.logger.info(f"포지션 수량 변경: {symbol} {quantity_change:+d}주 -> 총 {new_quantity}주")

    def get_position(self, symbol: str) -> Optional[Position]:
        """
        포지션 조회

        Args:
            symbol: 종목 코드

        Returns:
            포지션 (없으면 None)
        """
        return self.positions.get(symbol)

    def get_all_positions(self) -> Dict[str, Position]:
        """모든 포지션 조회"""
        return self.positions.copy()

    def get_positions_by_type(self, position_type: PositionType) -> Dict[str, Position]:
        """특정 타입의 포지션들 조회"""
        return {
            symbol: position
            for symbol, position in self.positions.items()
            if position.position_type == position_type
        }

    def get_total_unrealized_pnl(self) -> float:
        """전체 미실현 손익 계산"""
        return sum(position.get_unrealized_pnl() for position in self.positions.values())

    def get_position_count(self) -> int:
        """포지션 개수"""
        return len(self.positions)

    def get_symbols_with_positions(self) -> List[str]:
        """포지션이 있는 종목 목록"""
        return list(self.positions.keys())

    def has_position(self, symbol: str) -> bool:
        """포지션 보유 여부"""
        return symbol in self.positions

    def get_position_summary(self) -> Dict[str, any]:
        """포지션 요약 정보"""
        if not self.positions:
            return {
                'total_positions': 0,
                'long_positions': 0,
                'short_positions': 0,
                'total_unrealized_pnl': 0.0,
                'positions': []
            }

        long_count = len(self.get_positions_by_type(PositionType.LONG))
        short_count = len(self.get_positions_by_type(PositionType.SHORT))

        position_details = []
        for symbol, position in self.positions.items():
            position_details.append({
                'symbol': symbol,
                'position_type': position.position_type.value,
                'quantity': position.quantity,
                'entry_price': position.entry_price,
                'current_price': position.current_price,
                'unrealized_pnl': position.get_unrealized_pnl(),
                'unrealized_pnl_percent': position.get_unrealized_pnl_percent(),
                'entry_time': position.entry_time.isoformat()
            })

        return {
            'total_positions': len(self.positions),
            'long_positions': long_count,
            'short_positions': short_count,
            'total_unrealized_pnl': self.get_total_unrealized_pnl(),
            'positions': position_details
        }