#!/usr/bin/env python3
"""
해외주식 자동매매 시스템 메인 실행 파일
터미널 UI를 통한 다중 종목 실시간 모니터링 및 자동매매
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
import argparse
import json

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from overseas_trading_system.core.overseas_data_provider import OverseasDataProvider
from overseas_trading_system.core.overseas_trading_engine import OverseasTradingEngine
from overseas_trading_system.strategies.momentum_strategy import MomentumStrategy
from overseas_trading_system.monitors.overseas_terminal import OverseasStockMonitor
from overseas_trading_system.core.overseas_data_types import ExchangeType

try:
    from rich.console import Console
    from rich.live import Live
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.columns import Columns
    import keyboard
    RICH_AVAILABLE = True
    KEYBOARD_AVAILABLE = True
except ImportError as e:
    RICH_AVAILABLE = False
    KEYBOARD_AVAILABLE = False
    print(f"Rich 또는 keyboard 라이브러리 없음: {e}")
    print("pip install rich keyboard 실행 필요")


class OverseasTradingSystem:
    """해외주식 자동매매 시스템 메인 클래스"""

    def __init__(self, config_file: str = None):
        self.config = self._load_config(config_file)
        self._setup_logging()

        # 핵심 컴포넌트 초기화
        self.data_provider = OverseasDataProvider()
        self.trading_engine = OverseasTradingEngine(self.config.get('engine', {}))
        self.monitors: dict = {}

        # 시스템 상태
        self.is_running = False
        self.active_monitor_index = 0

        # UI 설정
        if RICH_AVAILABLE:
            self.console = Console()

        self.logger = logging.getLogger("overseas_trading_system")

        # 주문 실행기 설정
        self.trading_engine.set_order_executor(self._simulate_order_executor)

        # 이벤트 콜백 설정
        self._setup_event_handlers()

    def _load_config(self, config_file: str = None) -> dict:
        """설정 파일 로드"""
        default_config = {
            'engine': {
                'max_positions': 10,
                'default_quantity': 1,
                'min_confidence': 0.6,
                'execution_delay': 0.1
            },
            'executor': {
                'dry_run': True,  # 시뮬레이션 모드
                'execution_delay': 0.5
            },
            'stocks': [
                {
                    'symbol': 'TSLA',
                    'name': 'Tesla Inc.',
                    'strategy': 'momentum',
                    'strategy_config': {
                        'rsi_oversold': 30,
                        'rsi_overbought': 70,
                        'volume_spike_threshold': 2.0,
                        'min_confidence': 0.6
                    }
                },
                {
                    'symbol': 'AAPL',
                    'name': 'Apple Inc.',
                    'strategy': 'momentum',
                    'strategy_config': {
                        'rsi_oversold': 25,
                        'rsi_overbought': 75,
                        'volume_spike_threshold': 1.8,
                        'min_confidence': 0.65
                    }
                },
                {
                    'symbol': 'NVDA',
                    'name': 'NVIDIA Corp.',
                    'strategy': 'momentum',
                    'strategy_config': {
                        'rsi_oversold': 35,
                        'rsi_overbought': 65,
                        'volume_spike_threshold': 2.5,
                        'min_confidence': 0.7
                    }
                }
            ],
            'update_interval': 3.0  # 3초마다 업데이트
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
                    f'overseas_trading_{datetime.now().strftime("%Y%m%d")}.log',
                    encoding='utf-8'
                ),
                logging.StreamHandler()
            ]
        )

    def _setup_event_handlers(self):
        """이벤트 핸들러 설정"""
        self.trading_engine.add_event_callback('signal_generated', self._on_signal_generated)
        self.trading_engine.add_event_callback('order_placed', self._on_order_placed)
        self.trading_engine.add_event_callback('order_filled', self._on_order_filled)
        self.trading_engine.add_event_callback('position_opened', self._on_position_opened)
        self.trading_engine.add_event_callback('position_closed', self._on_position_closed)

    async def _simulate_order_executor(self, symbol: str, order) -> bool:
        """주문 실행 시뮬레이터"""
        await asyncio.sleep(0.1)

        # 95% 성공률
        import random
        success = random.random() > 0.05

        if success:
            self.logger.info(f"시뮬레이션 주문 체결: {symbol} {order.signal_type.value} {order.quantity}주")
        else:
            self.logger.warning(f"시뮬레이션 주문 실패: {symbol} {order.signal_type.value}")

        return success

    async def _on_signal_generated(self, symbol: str, signal):
        """신호 생성 이벤트"""
        self.logger.info(f"신호 생성: {symbol} {signal.signal_type.value} (신뢰도: {signal.confidence:.2f})")

    async def _on_order_placed(self, order):
        """주문 생성 이벤트"""
        self.logger.info(f"주문 생성: {order.symbol} {order.signal_type.value} {order.quantity}주")

    async def _on_order_filled(self, order):
        """주문 체결 이벤트"""
        self.logger.info(f"주문 체결: {order.symbol} {order.signal_type.value} {order.filled_quantity}주")

    async def _on_position_opened(self, symbol: str, position_type: str):
        """포지션 생성 이벤트"""
        self.logger.info(f"포지션 생성: {symbol} {position_type}")

    async def _on_position_closed(self, symbol: str, pnl: float, reason: str):
        """포지션 청산 이벤트"""
        self.logger.info(f"포지션 청산: {symbol} 손익: ₩{pnl:+,.0f} ({reason})")

    def add_stock(self, symbol: str, name: str, strategy_name: str, strategy_config: dict = None):
        """종목 추가"""
        try:
            # 전략 생성
            if strategy_name == 'momentum':
                strategy = MomentumStrategy(strategy_config)
            else:
                raise ValueError(f"지원하지 않는 전략: {strategy_name}")

            # 거래 엔진에 추가
            self.trading_engine.add_stock(symbol, strategy)

            # 모니터 생성
            monitor = OverseasStockMonitor(symbol, name, strategy)
            self.monitors[symbol] = monitor

            self.logger.info(f"종목 추가: {symbol} ({name}) - {strategy_name}")

        except Exception as e:
            self.logger.error(f"종목 추가 실패 [{symbol}]: {e}")
            raise

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

    async def update_data_loop(self):
        """데이터 업데이트 루프"""
        update_interval = self.config.get('update_interval', 3.0)

        while self.is_running:
            try:
                for symbol, monitor in self.monitors.items():
                    # 실시간 데이터 조회
                    market_data = await self.data_provider.get_realtime_price(symbol)

                    if market_data:
                        # 모니터 업데이트
                        monitor.update_market_data(market_data)

                        # 거래 엔진 업데이트 (신호 생성 및 자동매매)
                        signal = await self.trading_engine.update_market_data(symbol, market_data)

                        if signal:
                            monitor.update_signal(signal)

                        # 포지션 업데이트
                        position = self.trading_engine.get_position(symbol)
                        monitor.update_position(position)

                await asyncio.sleep(update_interval)

            except Exception as e:
                self.logger.error(f"데이터 업데이트 루프 오류: {e}")
                await asyncio.sleep(1)

    def setup_hotkeys(self):
        """키보드 단축키 설정"""
        if not KEYBOARD_AVAILABLE:
            return

        try:
            # 탭 전환
            keyboard.add_hotkey('tab', self.next_monitor)
            keyboard.add_hotkey('shift+tab', self.prev_monitor)

            # 매매 제어
            keyboard.add_hotkey('ctrl+t', self.toggle_trading)

            # 종료
            keyboard.add_hotkey('ctrl+c', self.stop)
            keyboard.add_hotkey('esc', self.stop)

            self.logger.info("키보드 단축키 설정 완료")
        except Exception as e:
            self.logger.warning(f"키보드 단축키 설정 실패: {e}")

    def next_monitor(self):
        """다음 모니터로 전환"""
        if self.monitors:
            self.active_monitor_index = (self.active_monitor_index + 1) % len(self.monitors)

    def prev_monitor(self):
        """이전 모니터로 전환"""
        if self.monitors:
            self.active_monitor_index = (self.active_monitor_index - 1) % len(self.monitors)

    def toggle_trading(self):
        """매매 활성화/비활성화 토글"""
        if self.trading_engine.is_trading_enabled:
            self.trading_engine.disable_trading()
        else:
            self.trading_engine.enable_trading()

    def render_console_mode(self):
        """콘솔 모드 (Rich 없는 환경)"""
        print("\n" + "="*80)
        print(f"해외주식 자동매매 시스템 - {datetime.now().strftime('%H:%M:%S')}")
        print("="*80)

        for symbol, monitor in self.monitors.items():
            status = monitor.get_status()
            print(f"\n{symbol} ({monitor.symbol_name}):")
            print(f"  가격: ${status['current_price_usd']:.2f} (₩{status['current_price_krw']:,.0f})")
            print(f"  손익: ${status['unrealized_pnl_usd']:+.2f} (₩{status['unrealized_pnl_krw']:+,.0f})")

        # 시스템 상태
        engine_status = self.trading_engine.get_status()
        print(f"\n시스템 상태:")
        print(f"  매매 활성화: {engine_status['is_trading_enabled']}")
        print(f"  활성 포지션: {engine_status['position_count']}")
        print(f"  포트폴리오: ${engine_status['portfolio_value_usd']:.2f}")

    def start(self):
        """시스템 시작"""
        try:
            self.logger.info("해외주식 자동매매 시스템 시작")

            # 종목 초기화
            self.initialize_stocks()

            # 매매 활성화
            self.trading_engine.enable_trading()

            # 키보드 단축키 설정
            self.setup_hotkeys()

            self.is_running = True

            # 데이터 업데이트 루프 시작
            if RICH_AVAILABLE:
                print("Rich UI 모드 지원 예정 - 현재는 콘솔 모드로 실행")

            print(f"\n🚀 해외주식 자동매매 시스템 시작")
            print(f"등록 종목: {', '.join(self.monitors.keys())}")
            print(f"업데이트 간격: {self.config.get('update_interval', 3.0)}초")
            print("Ctrl+C로 종료")

            # 비동기 루프 실행
            asyncio.run(self._run_async())

        except KeyboardInterrupt:
            self.logger.info("사용자 중단")
        except Exception as e:
            self.logger.error(f"시스템 시작 오류: {e}")
        finally:
            self.stop()

    async def _run_async(self):
        """비동기 실행"""
        # 데이터 업데이트 태스크 시작
        update_task = asyncio.create_task(self.update_data_loop())

        try:
            # 콘솔 출력 루프
            while self.is_running:
                self.render_console_mode()
                await asyncio.sleep(5)  # 5초마다 화면 갱신

        except KeyboardInterrupt:
            self.is_running = False
        finally:
            update_task.cancel()
            try:
                await update_task
            except asyncio.CancelledError:
                pass

    def stop(self):
        """시스템 중지"""
        self.is_running = False
        self.logger.info("해외주식 자동매매 시스템 중지")

        # 최종 통계 출력
        stats = self.trading_engine.get_trading_stats()
        print(f"\n📊 최종 거래 통계:")
        print(f"  총 주문: {stats['total_orders']}")
        print(f"  성공률: {stats['success_rate']:.1f}%")
        print(f"  실현 손익: ${stats['total_realized_pnl_usd']:+.2f} (₩{stats['total_realized_pnl_krw']:+,.0f})")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="해외주식 자동매매 시스템")
    parser.add_argument('--config', type=str, help='설정 파일 경로')
    parser.add_argument('--dry-run', action='store_true', help='시뮬레이션 모드')

    args = parser.parse_args()

    # 시스템 생성
    system = OverseasTradingSystem(args.config)

    if args.dry_run:
        system.config['executor']['dry_run'] = True

    # 시스템 시작
    system.start()


if __name__ == "__main__":
    main()