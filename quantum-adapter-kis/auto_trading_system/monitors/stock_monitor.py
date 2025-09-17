"""
종목별 모니터링 화면
Rich 라이브러리를 사용한 실시간 터미널 UI
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from threading import Lock
import time

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.columns import Columns
from rich.progress import Progress, BarColumn, TextColumn
from rich import box

from ..core.data_types import MarketData, Signal, Position, TradingStats, SignalType, PositionType
from ..strategies.base_strategy import BaseStrategy, StrategyContext


class StockMonitor:
    """종목별 실시간 모니터링 화면"""

    def __init__(self, symbol: str, symbol_name: str, strategy: BaseStrategy):
        """
        Args:
            symbol: 종목 코드
            symbol_name: 종목명
            strategy: 매매 전략
        """
        self.symbol = symbol
        self.symbol_name = symbol_name
        self.strategy_context = StrategyContext(strategy)

        # 상태 관리
        self.current_data: Optional[MarketData] = None
        self.current_position: Optional[Position] = None
        self.recent_signals: List[Signal] = []
        self.trading_stats = TradingStats()
        self.trade_logs: List[str] = []

        # 가격 히스토리 (차트용)
        self.price_history: List[float] = []
        self.max_history_size = 50

        # 스레드 안전성
        self.data_lock = Lock()

        # UI 설정
        self.console = Console()
        self.logger = logging.getLogger(f"monitor.{symbol}")

        # 색상 설정
        self.colors = {
            'up': 'red',        # 한국 증시 상승 = 빨강
            'down': 'blue',     # 한국 증시 하락 = 파랑
            'neutral': 'white',
            'profit': 'green',
            'loss': 'red',
            'warning': 'yellow',
            'info': 'cyan'
        }

    def update_market_data(self, market_data: MarketData):
        """시장 데이터 업데이트"""
        with self.data_lock:
            self.current_data = market_data

            # 가격 히스토리 업데이트
            self.price_history.append(market_data.current_price)
            if len(self.price_history) > self.max_history_size:
                self.price_history = self.price_history[-self.max_history_size:]

            # 전략 실행
            signal = self.strategy_context.execute_strategy(market_data)
            if signal:
                self.add_signal(signal)

    def update_position(self, position: Optional[Position]):
        """포지션 업데이트"""
        with self.data_lock:
            self.current_position = position

    def add_signal(self, signal: Signal):
        """신호 추가"""
        with self.data_lock:
            self.recent_signals.append(signal)

            # 최근 20개 신호만 유지
            if len(self.recent_signals) > 20:
                self.recent_signals = self.recent_signals[-20:]

            # 로그 추가
            timestamp = signal.timestamp.strftime("%H:%M:%S")
            log_msg = f"{timestamp} - {signal.signal_type.value} 신호: {signal.reason} (신뢰도: {signal.confidence:.2f})"
            self.add_log(log_msg)

    def add_log(self, message: str):
        """거래 로그 추가"""
        with self.data_lock:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.trade_logs.append(f"{timestamp} - {message}")

            # 최근 10개 로그만 유지
            if len(self.trade_logs) > 10:
                self.trade_logs = self.trade_logs[-10:]

    def change_strategy(self, strategy: BaseStrategy):
        """전략 변경"""
        with self.data_lock:
            old_strategy = self.strategy_context.get_strategy().name
            self.strategy_context.set_strategy(strategy)
            self.add_log(f"전략 변경: {old_strategy} → {strategy.name}")

    def create_layout(self) -> Layout:
        """모니터링 레이아웃 생성"""
        layout = Layout()

        # 메인 분할
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=8)
        )

        # 바디 분할
        layout["body"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=1)
        )

        # 왼쪽 분할
        layout["left"].split(
            Layout(name="price_info", size=6),
            Layout(name="chart", size=12),
            Layout(name="indicators")
        )

        # 오른쪽 분할
        layout["right"].split(
            Layout(name="position"),
            Layout(name="signals")
        )

        return layout

    def render_header(self) -> Panel:
        """헤더 렌더링"""
        if not self.current_data:
            title = f"[bold cyan]{self.symbol}[/] {self.symbol_name} - 데이터 로딩 중..."
            return Panel(title, border_style="cyan")

        # 가격 변화 계산
        current_price = self.current_data.current_price
        if len(self.price_history) >= 2:
            prev_price = self.price_history[-2]
            change = current_price - prev_price
            change_percent = (change / prev_price) * 100 if prev_price > 0 else 0
        else:
            change = 0
            change_percent = 0

        # 색상 결정
        color = self.colors['up'] if change >= 0 else self.colors['down']
        sign = "+" if change >= 0 else ""

        # 전략 정보
        strategy_name = self.strategy_context.get_strategy().name
        strategy_status = "활성" if self.strategy_context.get_strategy().is_active else "비활성"

        title = (
            f"[bold cyan]{self.symbol}[/] {self.symbol_name} - "
            f"[{color}]{current_price:,}원 ({sign}{change:+,.0f}, {change_percent:+.2f}%)[/] | "
            f"전략: [bold yellow]{strategy_name}[/] ({strategy_status})"
        )

        return Panel(title, border_style="cyan")

    def render_price_info(self) -> Panel:
        """가격 정보 렌더링"""
        if not self.current_data:
            return Panel("데이터 없음", title="가격 정보", border_style="white")

        data = self.current_data

        # 테이블 생성
        table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
        table.add_column("항목", style="white", width=8)
        table.add_column("값", style="white", width=12)
        table.add_column("항목", style="white", width=8)
        table.add_column("값", style="white", width=12)

        # 기본 정보
        table.add_row(
            "현재가", f"{data.current_price:,}원",
            "거래량", f"{data.volume:,}주"
        )
        table.add_row(
            "시가", f"{data.open_price:,}원",
            "고가", f"{data.high_price:,}원"
        )
        table.add_row(
            "저가", f"{data.low_price:,}원",
            "시간", data.timestamp.strftime("%H:%M:%S")
        )

        return Panel(table, title="가격 정보", border_style="green")

    def render_chart(self) -> Panel:
        """ASCII 차트 렌더링"""
        if len(self.price_history) < 2:
            return Panel("차트 데이터 부족", title="가격 차트", border_style="white")

        # 가격 정규화
        min_price = min(self.price_history)
        max_price = max(self.price_history)
        price_range = max_price - min_price

        if price_range == 0:
            chart_line = "━" * len(self.price_history)
        else:
            # 차트 높이 (10단계)
            chart_height = 10
            chart_chars = "▁▂▃▄▅▆▇█"

            chart_line = ""
            for price in self.price_history:
                normalized = (price - min_price) / price_range
                char_index = min(int(normalized * len(chart_chars)), len(chart_chars) - 1)
                chart_line += chart_chars[char_index]

        # 가격 범위 표시
        price_info = f"최고: {max_price:,.0f}원 | 최저: {min_price:,.0f}원 | 범위: {price_range:,.0f}원"

        chart_content = f"{chart_line}\n\n{price_info}"

        return Panel(chart_content, title=f"가격 차트 (최근 {len(self.price_history)}개)", border_style="yellow")

    def render_indicators(self) -> Panel:
        """기술적 지표 렌더링"""
        if not self.current_data:
            return Panel("데이터 없음", title="기술적 지표", border_style="white")

        data = self.current_data
        table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
        table.add_column("지표", style="white", width=8)
        table.add_column("값", style="white", width=12)
        table.add_column("상태", style="white", width=10)

        # RSI
        if data.rsi is not None:
            rsi_color = self.colors['down'] if data.rsi <= 30 else (
                self.colors['up'] if data.rsi >= 70 else self.colors['neutral']
            )
            rsi_status = "과매도" if data.rsi <= 30 else ("과매수" if data.rsi >= 70 else "중립")
            table.add_row("RSI", f"[{rsi_color}]{data.rsi:.1f}[/]", f"[{rsi_color}]{rsi_status}[/]")

        # 이동평균선
        if data.ma5 is not None and data.ma20 is not None:
            ma_color = self.colors['up'] if data.ma5 > data.ma20 else self.colors['down']
            ma_status = "골든크로스" if data.ma5 > data.ma20 else "데드크로스"
            table.add_row("MA5", f"{data.ma5:,.0f}원", "")
            table.add_row("MA20", f"{data.ma20:,.0f}원", f"[{ma_color}]{ma_status}[/]")

        # 볼린저 밴드
        if data.bb_upper is not None and data.bb_lower is not None:
            band_position = (data.current_price - data.bb_lower) / (data.bb_upper - data.bb_lower)
            bb_color = self.colors['up'] if band_position > 0.8 else (
                self.colors['down'] if band_position < 0.2 else self.colors['neutral']
            )
            bb_status = "상단" if band_position > 0.8 else ("하단" if band_position < 0.2 else "중간")
            table.add_row("BB 상단", f"{data.bb_upper:,.0f}원", "")
            table.add_row("BB 하단", f"{data.bb_lower:,.0f}원", f"[{bb_color}]{bb_status}[/]")

        return Panel(table, title="기술적 지표", border_style="blue")

    def render_position(self) -> Panel:
        """포지션 정보 렌더링"""
        if not self.current_position:
            content = "[yellow]포지션 없음[/]\n\n현금 보유 상태"
            return Panel(content, title="포지션", border_style="white")

        pos = self.current_position

        # 손익 계산
        unrealized_pnl = pos.get_unrealized_pnl()
        unrealized_pnl_percent = pos.get_unrealized_pnl_percent()

        # 손익 색상
        pnl_color = self.colors['profit'] if unrealized_pnl >= 0 else self.colors['loss']
        pnl_sign = "+" if unrealized_pnl >= 0 else ""

        # 포지션 타입 색상
        pos_color = self.colors['up'] if pos.position_type == PositionType.LONG else self.colors['down']

        content = (
            f"포지션: [{pos_color}]{pos.position_type.value}[/] {pos.quantity:,}주\n"
            f"진입가: {pos.entry_price:,}원\n"
            f"현재가: {pos.current_price:,}원\n"
            f"손익: [{pnl_color}]{pnl_sign}{unrealized_pnl:,.0f}원[/]\n"
            f"수익률: [{pnl_color}]{pnl_sign}{unrealized_pnl_percent:.2f}%[/]\n"
            f"진입시간: {pos.entry_time.strftime('%H:%M:%S')}"
        )

        return Panel(content, title="포지션", border_style=pnl_color)

    def render_signals(self) -> Panel:
        """최근 신호 렌더링"""
        if not self.recent_signals:
            return Panel("신호 없음", title="최근 신호", border_style="white")

        content = ""
        for signal in self.recent_signals[-5:]:  # 최근 5개
            signal_color = self.colors['up'] if signal.signal_type == SignalType.BUY else (
                self.colors['down'] if signal.signal_type == SignalType.SELL else self.colors['neutral']
            )

            confidence_bar = "█" * int(signal.confidence * 10)
            time_str = signal.timestamp.strftime("%H:%M:%S")

            content += (
                f"[{signal_color}]{signal.signal_type.value}[/] "
                f"{time_str} (신뢰도: {confidence_bar})\n"
                f"  {signal.reason}\n\n"
            )

        return Panel(content.strip(), title="최근 신호", border_style="magenta")

    def render_footer(self) -> Panel:
        """푸터 (로그 + 통계) 렌더링"""
        # 왼쪽: 거래 로그
        log_content = ""
        for log in self.trade_logs[-6:]:  # 최근 6개
            log_content += f"{log}\n"

        if not log_content:
            log_content = "로그 없음"

        log_panel = Panel(log_content.strip(), title="거래 로그", border_style="white")

        # 오른쪽: 거래 통계
        stats = self.trading_stats
        stats_content = (
            f"총 거래: {stats.total_trades}회\n"
            f"승률: {stats.win_rate:.1f}% ({stats.winning_trades}승 {stats.losing_trades}패)\n"
            f"총 손익: {stats.total_pnl:,.0f}원\n"
            f"평균 수익: {stats.avg_win:,.0f}원\n"
            f"평균 손실: {stats.avg_loss:,.0f}원\n"
            f"수익 팩터: {stats.profit_factor:.2f}"
        )

        stats_panel = Panel(stats_content, title="거래 통계", border_style="cyan")

        return Columns([log_panel, stats_panel])

    def render(self) -> Layout:
        """전체 화면 렌더링"""
        layout = self.create_layout()

        with self.data_lock:
            layout["header"].update(self.render_header())
            layout["price_info"].update(self.render_price_info())
            layout["chart"].update(self.render_chart())
            layout["indicators"].update(self.render_indicators())
            layout["position"].update(self.render_position())
            layout["signals"].update(self.render_signals())
            layout["footer"].update(self.render_footer())

        return layout

    def get_status(self) -> Dict[str, Any]:
        """모니터 상태 조회"""
        with self.data_lock:
            return {
                'symbol': self.symbol,
                'symbol_name': self.symbol_name,
                'strategy': self.strategy_context.get_status(),
                'current_price': self.current_data.current_price if self.current_data else None,
                'position': self.current_position.to_dict() if self.current_position else None,
                'recent_signals_count': len(self.recent_signals),
                'trading_stats': self.trading_stats.to_dict(),
                'log_count': len(self.trade_logs)
            }