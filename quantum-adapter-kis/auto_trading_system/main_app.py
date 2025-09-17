"""
자동매매 시스템 메인 애플리케이션
종목별 터미널 모니터링과 전략 기반 자동매매 실행
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os

from auto_trading_system.core.trading_engine import AutoTradingEngine
from auto_trading_system.core.order_executor import OrderExecutor
from auto_trading_system.core.data_types import MarketData, Position, PositionType
from auto_trading_system.monitors.terminal_manager import TerminalManager
from auto_trading_system.strategies import create_strategy


class AutoTradingSystem:
    """자동매매 시스템 메인 클래스"""

    def __init__(self, config_file: str = None):
        """
        Args:
            config_file: 설정 파일 경로
        """
        # 설정 로드
        self.config = self._load_config(config_file)

        # 로깅 설정
        self._setup_logging()

        # 핵심 컴포넌트 초기화
        self.trading_engine = AutoTradingEngine(self.config.get('engine', {}))
        self.order_executor = OrderExecutor(self.config.get('executor', {}))
        self.terminal_manager = TerminalManager()

        # 데이터 제공자 (KIS API 연동)
        self.data_providers = {}

        # 시스템 상태
        self.is_running = False

        self.logger = logging.getLogger("auto_trading_system")

        # 이벤트 핸들러 설정
        self._setup_event_handlers()

    def _load_config(self, config_file: str = None) -> Dict[str, Any]:
        """설정 파일 로드"""
        default_config = {
            'engine': {
                'max_positions': 5,
                'default_quantity': 100,
                'execution_delay': 0.1
            },
            'executor': {
                'environment': 'vps',  # vps (모의투자) 또는 prod (실전투자)
                'dry_run': True,
                'execution_delay': 0.5
            },
            'risk_config': {
                'max_daily_trades': 10,
                'max_position_size': 1000000,
                'min_confidence_threshold': 0.6,
                'trading_start_time': '09:00',
                'trading_end_time': '15:30'
            },
            'stocks': [
                {
                    'symbol': '005930',
                    'name': '삼성전자',
                    'strategy': 'golden_cross',
                    'strategy_config': {
                        'fast_period': 5,
                        'slow_period': 20,
                        'min_confidence': 0.7
                    }
                },
                {
                    'symbol': '035420',
                    'name': 'NAVER',
                    'strategy': 'rsi',
                    'strategy_config': {
                        'rsi_period': 14,
                        'oversold_threshold': 30,
                        'overbought_threshold': 70,
                        'min_confidence': 0.6
                    }
                }
            ]
        }

        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    default_config.update(file_config)
            except Exception as e:
                print(f"설정 파일 로드 실패 ({config_file}): {e}")

        return default_config

    def _setup_logging(self):
        """로깅 설정"""
        log_level = self.config.get('log_level', 'INFO')
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        logging.basicConfig(
            level=getattr(logging, log_level),
            format=log_format,
            handlers=[
                logging.FileHandler(
                    f'auto_trading_{datetime.now().strftime("%Y%m%d")}.log',
                    encoding='utf-8'
                ),
                logging.StreamHandler()
            ]
        )

    def _setup_event_handlers(self):
        """이벤트 핸들러 설정"""
        # 주문 실행기 설정
        self.trading_engine.set_order_executor(self.order_executor.execute_order)

        # 이벤트 콜백 등록
        self.trading_engine.add_event_callback('signal_generated', self._on_signal_generated)
        self.trading_engine.add_event_callback('order_placed', self._on_order_placed)
        self.trading_engine.add_event_callback('order_filled', self._on_order_filled)
        self.trading_engine.add_event_callback('position_opened', self._on_position_opened)
        self.trading_engine.add_event_callback('position_closed', self._on_position_closed)

    async def _on_signal_generated(self, symbol: str, signal):
        """신호 생성 이벤트"""
        self.logger.info(f"신호 생성: {symbol} {signal.signal_type.value} (신뢰도: {signal.confidence:.2f})")

    async def _on_order_placed(self, order):
        """주문 생성 이벤트"""
        self.logger.info(f"주문 생성: {order.symbol} {order.signal_type.value} {order.quantity}주")

    async def _on_order_filled(self, order):
        """주문 체결 이벤트"""
        self.logger.info(f"주문 체결: {order.symbol} {order.signal_type.value} {order.filled_quantity}주 @ {order.filled_price:,}원")

    async def _on_position_opened(self, symbol: str, position_type: str):
        """포지션 생성 이벤트"""
        self.logger.info(f"포지션 생성: {symbol} {position_type}")

    async def _on_position_closed(self, symbol: str, pnl: float, reason: str):
        """포지션 청산 이벤트"""
        pnl_str = f"+{pnl:,.0f}" if pnl >= 0 else f"{pnl:,.0f}"
        self.logger.info(f"포지션 청산: {symbol} 손익: {pnl_str}원 ({reason})")

    def add_stock(self, symbol: str, name: str, strategy_name: str, strategy_config: dict = None):
        """종목 추가"""
        try:
            # 전략 생성
            strategy = create_strategy(strategy_name, strategy_config)

            # 트레이딩 엔진에 종목 추가
            self.trading_engine.add_stock(symbol, strategy)

            # 터미널 매니저에 종목 추가
            self.terminal_manager.add_stock(
                symbol=symbol,
                symbol_name=name,
                strategy_name=strategy_name,
                strategy_config=strategy_config,
                data_provider=self._create_data_provider(symbol),
                position_provider=self._create_position_provider(symbol)
            )

            self.logger.info(f"종목 추가 완료: {symbol} ({name}) - {strategy_name}")

        except Exception as e:
            self.logger.error(f"종목 추가 실패 [{symbol}]: {e}")
            raise

    def _create_data_provider(self, symbol: str):
        """데이터 제공자 생성"""
        async def data_provider() -> Optional[MarketData]:
            try:
                # KIS API를 통한 실시간 데이터 조회
                # 실제 구현에서는 기존 KIS API 함수들을 사용
                from examples_llm.domestic_stock.inquire_price.inquire_price import inquire_price

                # 현재가 조회
                price_data = inquire_price(symbol)
                if not price_data:
                    return None

                # MarketData 생성
                market_data = MarketData(
                    symbol=symbol,
                    timestamp=datetime.now(),
                    current_price=float(price_data.get('stck_prpr', 0)),  # 현재가
                    open_price=float(price_data.get('stck_oprc', 0)),     # 시가
                    high_price=float(price_data.get('stck_hgpr', 0)),     # 고가
                    low_price=float(price_data.get('stck_lwpr', 0)),      # 저가
                    volume=int(price_data.get('acml_vol', 0))             # 거래량
                )

                # 트레이딩 엔진에 데이터 전달
                await self.trading_engine.update_market_data(symbol, market_data)

                return market_data

            except Exception as e:
                self.logger.error(f"데이터 제공 오류 [{symbol}]: {e}")
                return None

        return data_provider

    def _create_position_provider(self, symbol: str):
        """포지션 제공자 생성"""
        async def position_provider() -> Optional[Position]:
            try:
                # 트레이딩 엔진에서 포지션 조회
                position = self.trading_engine.get_position(symbol)
                return position

            except Exception as e:
                self.logger.error(f"포지션 조회 오류 [{symbol}]: {e}")
                return None

        return position_provider

    def initialize_stocks(self):
        """설정 파일에서 종목 초기화"""
        stocks_config = self.config.get('stocks', [])

        for stock_config in stocks_config:
            symbol = stock_config['symbol']
            name = stock_config['name']
            strategy_name = stock_config['strategy']
            strategy_config = stock_config.get('strategy_config', {})

            try:
                self.add_stock(symbol, name, strategy_name, strategy_config)
            except Exception as e:
                self.logger.error(f"종목 초기화 실패 [{symbol}]: {e}")

    def change_strategy(self, symbol: str, strategy_name: str, strategy_config: dict = None):
        """종목 전략 변경"""
        try:
            # 새 전략 생성
            strategy = create_strategy(strategy_name, strategy_config)

            # 트레이딩 엔진에서 전략 변경
            self.trading_engine.change_strategy(symbol, strategy)

            # 터미널 매니저에서 전략 변경
            self.terminal_manager.change_strategy(symbol, strategy_name, strategy_config)

            self.logger.info(f"전략 변경 완료: {symbol} -> {strategy_name}")

        except Exception as e:
            self.logger.error(f"전략 변경 실패 [{symbol}]: {e}")

    def enable_trading(self):
        """매매 활성화"""
        self.trading_engine.enable_trading()

    def disable_trading(self):
        """매매 비활성화"""
        self.trading_engine.disable_trading()

    def set_dry_run(self, dry_run: bool):
        """시뮬레이션 모드 설정"""
        self.order_executor.set_dry_run(dry_run)

    def start(self):
        """시스템 시작"""
        try:
            self.logger.info("자동매매 시스템 시작")

            # 종목 초기화
            self.initialize_stocks()

            # 터미널 UI 시작 (블로킹)
            self.terminal_manager.start()

        except KeyboardInterrupt:
            self.logger.info("사용자 중단")
        except Exception as e:
            self.logger.error(f"시스템 시작 오류: {e}")
        finally:
            self.stop()

    def stop(self):
        """시스템 중지"""
        self.logger.info("자동매매 시스템 중지")
        self.terminal_manager.stop()

    def get_status(self) -> Dict[str, Any]:
        """전체 시스템 상태"""
        return {
            'system': {
                'is_running': self.is_running,
                'start_time': datetime.now().isoformat()
            },
            'trading_engine': self.trading_engine.get_status(),
            'order_executor': self.order_executor.get_execution_stats(),
            'terminal_manager': self.terminal_manager.get_status(),
            'positions': {
                symbol: position.to_dict()
                for symbol, position in self.trading_engine.get_positions().items()
            }
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """성과 요약"""
        positions = self.trading_engine.get_positions()
        trading_stats = self.trading_engine.get_trading_stats()

        total_unrealized_pnl = sum(pos.get_unrealized_pnl() for pos in positions.values())
        total_trades = sum(stats.total_trades for stats in trading_stats.values())
        total_realized_pnl = sum(stats.total_pnl for stats in trading_stats.values())

        return {
            'summary': {
                'total_positions': len(positions),
                'total_unrealized_pnl': total_unrealized_pnl,
                'total_realized_pnl': total_realized_pnl,
                'total_pnl': total_unrealized_pnl + total_realized_pnl,
                'total_trades': total_trades
            },
            'by_symbol': {
                symbol: {
                    'position': positions.get(symbol).to_dict() if symbol in positions else None,
                    'stats': trading_stats.get(symbol).to_dict() if symbol in trading_stats else None
                }
                for symbol in set(list(positions.keys()) + list(trading_stats.keys()))
            }
        }


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="자동매매 시스템")
    parser.add_argument('--config', type=str, help='설정 파일 경로')
    parser.add_argument('--dry-run', action='store_true', help='시뮬레이션 모드')
    parser.add_argument('--env', choices=['vps', 'prod'], default='vps', help='KIS 환경 (vps: 모의투자, prod: 실전투자)')

    args = parser.parse_args()

    # 시스템 생성
    system = AutoTradingSystem(args.config)

    # 설정 적용
    if args.dry_run:
        system.set_dry_run(True)

    # 환경 설정
    system.order_executor.environment = args.env

    # 시스템 시작
    system.start()


if __name__ == "__main__":
    main()