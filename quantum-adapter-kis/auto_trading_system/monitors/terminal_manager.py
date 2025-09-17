"""
터미널 매니저
여러 종목의 모니터링 터미널을 관리하는 시스템
"""

from typing import Dict, List, Optional, Callable
import asyncio
import threading
import time
from datetime import datetime
import logging

from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except (ImportError, OSError) as e:
    KEYBOARD_AVAILABLE = False
    keyboard = None

from .stock_monitor import StockMonitor
from ..core.data_types import MarketData, Position
from ..strategies.base_strategy import BaseStrategy
from ..strategies import create_strategy, get_available_strategies


class TerminalManager:
    """멀티 터미널 관리자"""

    def __init__(self):
        """초기화"""
        self.monitors: Dict[str, StockMonitor] = {}  # symbol -> StockMonitor
        self.active_monitor_index = 0
        self.is_running = False
        self.update_interval = 1.0  # 1초마다 업데이트

        # 이벤트 루프 관리
        self.loop = None
        self.thread = None

        # 콜백 함수들
        self.data_providers: Dict[str, Callable] = {}  # symbol -> data_provider_func
        self.position_providers: Dict[str, Callable] = {}  # symbol -> position_provider_func

        # UI 관리
        self.console = Console()
        self.live: Optional[Live] = None
        self.logger = logging.getLogger("terminal_manager")

        # 키보드 단축키 설정
        self.setup_hotkeys()

    def add_stock(
        self,
        symbol: str,
        symbol_name: str,
        strategy_name: str,
        strategy_config: dict = None,
        data_provider: Callable = None,
        position_provider: Callable = None
    ):
        """
        종목 추가

        Args:
            symbol: 종목 코드
            symbol_name: 종목명
            strategy_name: 전략명
            strategy_config: 전략 설정
            data_provider: 데이터 제공자 함수
            position_provider: 포지션 제공자 함수
        """
        try:
            # 전략 생성
            strategy = create_strategy(strategy_name, strategy_config)

            # 모니터 생성
            monitor = StockMonitor(symbol, symbol_name, strategy)
            self.monitors[symbol] = monitor

            # 데이터/포지션 제공자 등록
            if data_provider:
                self.data_providers[symbol] = data_provider
            if position_provider:
                self.position_providers[symbol] = position_provider

            self.logger.info(f"종목 추가: {symbol} ({symbol_name}) - {strategy_name} 전략")

        except Exception as e:
            self.logger.error(f"종목 추가 실패 [{symbol}]: {e}")
            raise

    def remove_stock(self, symbol: str):
        """종목 제거"""
        if symbol in self.monitors:
            del self.monitors[symbol]
            self.data_providers.pop(symbol, None)
            self.position_providers.pop(symbol, None)
            self.logger.info(f"종목 제거: {symbol}")
        else:
            self.logger.warning(f"존재하지 않는 종목: {symbol}")

    def change_strategy(self, symbol: str, strategy_name: str, strategy_config: dict = None):
        """종목 전략 변경"""
        if symbol not in self.monitors:
            self.logger.error(f"존재하지 않는 종목: {symbol}")
            return

        try:
            new_strategy = create_strategy(strategy_name, strategy_config)
            self.monitors[symbol].change_strategy(new_strategy)
            self.logger.info(f"전략 변경 [{symbol}]: {strategy_name}")
        except Exception as e:
            self.logger.error(f"전략 변경 실패 [{symbol}]: {e}")

    def get_monitor_list(self) -> List[str]:
        """모니터 목록 반환"""
        return list(self.monitors.keys())

    def get_active_monitor(self) -> Optional[StockMonitor]:
        """현재 활성 모니터 반환"""
        monitor_list = self.get_monitor_list()
        if monitor_list and 0 <= self.active_monitor_index < len(monitor_list):
            symbol = monitor_list[self.active_monitor_index]
            return self.monitors[symbol]
        return None

    def next_monitor(self):
        """다음 모니터로 전환"""
        monitor_list = self.get_monitor_list()
        if monitor_list:
            self.active_monitor_index = (self.active_monitor_index + 1) % len(monitor_list)
            active_symbol = monitor_list[self.active_monitor_index]
            self.logger.info(f"모니터 전환: {active_symbol}")

    def prev_monitor(self):
        """이전 모니터로 전환"""
        monitor_list = self.get_monitor_list()
        if monitor_list:
            self.active_monitor_index = (self.active_monitor_index - 1) % len(monitor_list)
            active_symbol = monitor_list[self.active_monitor_index]
            self.logger.info(f"모니터 전환: {active_symbol}")

    def setup_hotkeys(self):
        """키보드 단축키 설정"""
        if not KEYBOARD_AVAILABLE:
            self.logger.info("키보드 라이브러리 사용 불가 (관리자 권한 필요)")
            return

        try:
            # 탭 전환
            keyboard.add_hotkey('tab', self.next_monitor)
            keyboard.add_hotkey('shift+tab', self.prev_monitor)

            # 전략 변경 (숫자키)
            strategies = get_available_strategies()
            for i, strategy_name in enumerate(strategies[:9]):  # 1-9키
                keyboard.add_hotkey(f'{i+1}', lambda s=strategy_name: self.change_active_strategy(s))

            # 종료
            keyboard.add_hotkey('ctrl+c', self.stop)
            keyboard.add_hotkey('esc', self.stop)

            self.logger.info("키보드 단축키 설정 완료")
        except Exception as e:
            self.logger.warning(f"키보드 단축키 설정 실패: {e}")

    def change_active_strategy(self, strategy_name: str):
        """활성 모니터의 전략 변경"""
        monitor_list = self.get_monitor_list()
        if monitor_list and 0 <= self.active_monitor_index < len(monitor_list):
            symbol = monitor_list[self.active_monitor_index]
            self.change_strategy(symbol, strategy_name)

    async def update_data(self):
        """데이터 업데이트 루프"""
        while self.is_running:
            try:
                # 각 종목별 데이터 업데이트
                for symbol, monitor in self.monitors.items():
                    # 시장 데이터 업데이트
                    if symbol in self.data_providers:
                        try:
                            market_data = await self.data_providers[symbol]()
                            if market_data:
                                monitor.update_market_data(market_data)
                        except Exception as e:
                            self.logger.error(f"데이터 업데이트 실패 [{symbol}]: {e}")

                    # 포지션 데이터 업데이트
                    if symbol in self.position_providers:
                        try:
                            position = await self.position_providers[symbol]()
                            monitor.update_position(position)
                        except Exception as e:
                            self.logger.error(f"포지션 업데이트 실패 [{symbol}]: {e}")

                await asyncio.sleep(self.update_interval)

            except Exception as e:
                self.logger.error(f"데이터 업데이트 루프 오류: {e}")
                await asyncio.sleep(1)

    def create_main_layout(self) -> Layout:
        """메인 레이아웃 생성"""
        layout = Layout()

        layout.split(
            Layout(name="main", ratio=10),
            Layout(name="status", size=3)
        )

        return layout

    def render_status_bar(self) -> Panel:
        """상태바 렌더링"""
        monitor_list = self.get_monitor_list()

        if not monitor_list:
            content = "[yellow]등록된 종목이 없습니다.[/]"
        else:
            # 탭 형태로 종목 목록 표시
            tabs = []
            for i, symbol in enumerate(monitor_list):
                monitor = self.monitors[symbol]
                is_active = (i == self.active_monitor_index)

                # 현재가 및 변화 표시
                if monitor.current_data:
                    price = monitor.current_data.current_price
                    if len(monitor.price_history) >= 2:
                        change = price - monitor.price_history[-2]
                        color = 'red' if change >= 0 else 'blue'  # 한국 증시 색상
                        sign = '+' if change >= 0 else ''
                    else:
                        color = 'white'
                        sign = ''
                        change = 0

                    price_text = f"{price:,.0f}({sign}{change:+.0f})"
                else:
                    color = 'white'
                    price_text = "N/A"

                # 활성 탭 표시
                if is_active:
                    tab_text = f"[bold reverse][{color}] {symbol} {price_text} [/]"
                else:
                    tab_text = f"[{color}] {symbol} {price_text} [/]"

                tabs.append(tab_text)

            content = " | ".join(tabs)

        # 단축키 도움말
        help_text = (
            "\n[dim]단축키: [Tab] 다음 종목 | [Shift+Tab] 이전 종목 | "
            "[1-9] 전략 변경 | [Ctrl+C/Esc] 종료[/]"
        )

        content += help_text

        return Panel(content, title="종목 모니터링", border_style="cyan")

    def render(self) -> Layout:
        """전체 화면 렌더링"""
        layout = self.create_main_layout()

        # 활성 모니터 렌더링
        active_monitor = self.get_active_monitor()
        if active_monitor:
            layout["main"].update(active_monitor.render())
        else:
            empty_panel = Panel(
                "[yellow]등록된 종목이 없습니다.\n\n"
                "add_stock() 메서드를 사용해서 종목을 추가하세요.[/]",
                title="자동매매 시스템",
                border_style="yellow"
            )
            layout["main"].update(empty_panel)

        # 상태바 렌더링
        layout["status"].update(self.render_status_bar())

        return layout

    def start(self):
        """터미널 매니저 시작"""
        if self.is_running:
            self.logger.warning("이미 실행 중입니다")
            return

        self.is_running = True
        self.logger.info("터미널 매니저 시작")

        # 이벤트 루프 스레드 시작
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()

        # Live UI 시작
        try:
            with Live(self.render(), refresh_per_second=2, screen=True) as live:
                self.live = live
                while self.is_running:
                    live.update(self.render())
                    time.sleep(0.5)
        except KeyboardInterrupt:
            self.logger.info("사용자 중단")
        finally:
            self.stop()

    def _run_event_loop(self):
        """이벤트 루프 실행"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            self.loop.run_until_complete(self.update_data())
        except Exception as e:
            self.logger.error(f"이벤트 루프 오류: {e}")
        finally:
            self.loop.close()

    def stop(self):
        """터미널 매니저 중지"""
        if not self.is_running:
            return

        self.is_running = False
        self.logger.info("터미널 매니저 중지")

        # 이벤트 루프 중지
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)

        # 스레드 종료 대기
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)

    def get_status(self) -> Dict:
        """전체 상태 조회"""
        return {
            'is_running': self.is_running,
            'monitor_count': len(self.monitors),
            'active_monitor_index': self.active_monitor_index,
            'monitors': {
                symbol: monitor.get_status()
                for symbol, monitor in self.monitors.items()
            }
        }