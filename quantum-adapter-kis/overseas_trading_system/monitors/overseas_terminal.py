"""
해외주식 개별 터미널 모니터
USD/KRW 동시 표시, 환율 영향, 세금 계산 등 해외시장 특화 UI
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from collections import deque

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.align import Align

from overseas_trading_system.core.overseas_data_types import (
    OverseasMarketData, OverseasPosition, OverseasTradingSignal,
    TradingSession, PositionType, SignalType, TaxInfo
)


class OverseasStockMonitor:
    """해외주식 개별 터미널 모니터"""

    def __init__(self, symbol: str, symbol_name: str, strategy: Any = None):
        self.symbol = symbol
        self.symbol_name = symbol_name
        self.strategy = strategy
        self.logger = logging.getLogger(f"overseas_monitor_{symbol}")

        # 데이터 저장
        self.current_data: Optional[OverseasMarketData] = None
        self.current_position: Optional[OverseasPosition] = None
        self.current_signal: Optional[OverseasTradingSignal] = None

        # 가격 히스토리 (차트용)
        self.price_history: deque = deque(maxlen=50)
        self.price_history_krw: deque = deque(maxlen=50)

        # 거래 이력
        self.trade_history: List[Dict] = []

        # 세금 계산기
        self.tax_info = TaxInfo()

        # UI 설정
        self.console = Console()

    def update_market_data(self, market_data: OverseasMarketData):
        """시장 데이터 업데이트"""
        self.current_data = market_data

        # 가격 히스토리 업데이트
        self.price_history.append(market_data.current_price)
        if market_data.exchange_rate:
            self.price_history_krw.append(market_data.get_price_krw())

        self.logger.debug(f"시장 데이터 업데이트: {self.symbol} ${market_data.current_price:.2f}")

    def update_position(self, position: Optional[OverseasPosition]):
        """포지션 업데이트"""
        self.current_position = position

    def update_signal(self, signal: Optional[OverseasTradingSignal]):
        """신호 업데이트"""
        self.current_signal = signal

    def add_trade(self, trade_info: Dict):
        """거래 이력 추가"""
        self.trade_history.append(trade_info)

    def render(self) -> Layout:
        """터미널 화면 렌더링"""
        layout = Layout()

        # 메인 레이아웃 구성
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=7),
            Layout(name="footer", size=5)
        )

        # 헤더 (종목명과 거래소)
        layout["header"].update(self._render_header())

        # 메인 영역을 좌우로 분할
        layout["main"].split_row(
            Layout(name="left", ratio=6),
            Layout(name="right", ratio=4)
        )

        # 좌측: 가격 정보와 차트
        layout["left"].split(
            Layout(name="price", size=8),
            Layout(name="chart", ratio=1)
        )

        layout["left"]["price"].update(self._render_price_info())
        layout["left"]["chart"].update(self._render_price_chart())

        # 우측: 포지션과 전략
        layout["right"].split(
            Layout(name="position", ratio=1),
            Layout(name="strategy", ratio=1)
        )

        layout["right"]["position"].update(self._render_position_info())
        layout["right"]["strategy"].update(self._render_strategy_info())

        # 푸터: 거래 이력
        layout["footer"].update(self._render_trade_history())

        return layout

    def _render_header(self) -> Panel:
        """헤더 렌더링"""
        if not self.current_data:
            return Panel("연결 대기 중...", title="해외주식 모니터", border_style="yellow")

        exchange_name = {
            "NAS": "NASDAQ",
            "NYS": "NYSE",
            "AMS": "AMEX",
            "HKS": "HKEX",
            "TSE": "TSE"
        }.get(self.current_data.exchange.value, self.current_data.exchange.value)

        # 거래시간 표시
        session_colors = {
            TradingSession.PRE_MARKET: "yellow",
            TradingSession.REGULAR: "green",
            TradingSession.AFTER_HOURS: "blue",
            TradingSession.CLOSED: "red"
        }

        session_names = {
            TradingSession.PRE_MARKET: "프리마켓",
            TradingSession.REGULAR: "정규장",
            TradingSession.AFTER_HOURS: "애프터아워스",
            TradingSession.CLOSED: "장 마감"
        }

        session_color = session_colors.get(self.current_data.trading_session, "white")
        session_name = session_names.get(self.current_data.trading_session, "알 수 없음")

        header_text = f"[bold]{self.symbol}[/] ({self.symbol_name}) - {exchange_name} | [{session_color}]{session_name}[/]"

        return Panel(
            Align.center(header_text),
            border_style="cyan"
        )

    def _render_price_info(self) -> Panel:
        """가격 정보 렌더링"""
        if not self.current_data:
            return Panel("데이터 없음", title="가격 정보", border_style="yellow")

        # 변동률에 따른 색상 결정 (한국과 반대: 빨강=상승, 파랑=하락)
        change_color = "red" if self.current_data.change >= 0 else "blue"
        change_sign = "+" if self.current_data.change >= 0 else ""

        # 환율 정보
        exchange_rate = self.current_data.exchange_rate.rate if self.current_data.exchange_rate else 1300.0

        # 가격 테이블 생성
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("항목", style="bold", width=12)
        table.add_column("USD", justify="right", width=12)
        table.add_column("KRW", justify="right", width=15)

        # 현재가
        table.add_row(
            "현재가",
            f"[{change_color}]${self.current_data.current_price:.2f}[/]",
            f"[{change_color}]₩{self.current_data.get_price_krw():,.0f}[/]"
        )

        # 변동액/변동률
        table.add_row(
            "변동",
            f"[{change_color}]{change_sign}${self.current_data.change:.2f}[/]",
            f"[{change_color}]{change_sign}₩{self.current_data.get_change_krw():,.0f}[/]"
        )

        table.add_row(
            "변동률",
            f"[{change_color}]{change_sign}{self.current_data.change_percent:.2f}%[/]",
            f"[{change_color}]{change_sign}{self.current_data.change_percent:.2f}%[/]"
        )

        # 구분선
        table.add_row("", "", "")

        # OHLC
        table.add_row("시가", f"${self.current_data.open_price:.2f}", f"₩{self.current_data.open_price * exchange_rate:,.0f}")
        table.add_row("고가", f"${self.current_data.high_price:.2f}", f"₩{self.current_data.high_price * exchange_rate:,.0f}")
        table.add_row("저가", f"${self.current_data.low_price:.2f}", f"₩{self.current_data.low_price * exchange_rate:,.0f}")
        table.add_row("전일종가", f"${self.current_data.previous_close:.2f}", f"₩{self.current_data.previous_close * exchange_rate:,.0f}")

        # 거래량
        volume_str = f"{self.current_data.volume:,}" if self.current_data.volume > 0 else "N/A"
        table.add_row("거래량", volume_str, "")

        # 환율 정보
        table.add_row("", "", "")
        table.add_row("환율", f"1 USD", f"₩{exchange_rate:.2f}")

        return Panel(table, title="가격 정보", border_style="green")

    def _render_price_chart(self) -> Panel:
        """가격 차트 렌더링 (ASCII)"""
        if len(self.price_history) < 2:
            return Panel("차트 데이터 부족", title="가격 차트", border_style="yellow")

        try:
            # 간단한 ASCII 차트 생성
            prices = list(self.price_history)
            min_price = min(prices)
            max_price = max(prices)

            if max_price == min_price:
                chart_lines = ["─" * 40]
            else:
                chart_height = 8
                chart_width = min(len(prices), 40)

                chart_lines = []
                for row in range(chart_height):
                    line = ""
                    threshold = min_price + (max_price - min_price) * (chart_height - row - 1) / (chart_height - 1)

                    for i in range(chart_width):
                        if i < len(prices):
                            price_idx = len(prices) - chart_width + i
                            if price_idx >= 0 and prices[price_idx] >= threshold:
                                if i > 0:
                                    prev_idx = len(prices) - chart_width + i - 1
                                    if prev_idx >= 0 and prices[prev_idx] < threshold:
                                        line += "▲"  # 상승
                                    elif prev_idx >= 0 and prices[prev_idx] > threshold:
                                        line += "▼"  # 하락
                                    else:
                                        line += "■"  # 유지
                                else:
                                    line += "■"
                            else:
                                line += " "
                        else:
                            line += " "
                    chart_lines.append(line)

            chart_content = "\n".join(chart_lines)

            # 현재가와 범위 표시
            if self.current_data:
                range_info = f"H: ${max_price:.2f} | L: ${min_price:.2f} | C: ${self.current_data.current_price:.2f}"
            else:
                range_info = f"H: ${max_price:.2f} | L: ${min_price:.2f}"

            chart_content += "\n" + "─" * 40 + "\n" + range_info

            return Panel(chart_content, title="가격 차트 (50분봉)", border_style="cyan")

        except Exception as e:
            return Panel(f"차트 오류: {e}", title="가격 차트", border_style="red")

    def _render_position_info(self) -> Panel:
        """포지션 정보 렌더링"""
        if not self.current_position:
            return Panel("포지션 없음", title="포지션 정보", border_style="yellow")

        position = self.current_position

        # 손익 색상
        pnl_usd = position.get_unrealized_pnl_usd()
        pnl_color = "red" if pnl_usd >= 0 else "blue"

        # 포지션 테이블
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("항목", style="bold", width=10)
        table.add_column("값", justify="right")

        table.add_row("타입", position.position_type.value)
        table.add_row("수량", f"{position.quantity:,}주")

        # 진입가
        table.add_row("진입가", f"${position.entry_price:.2f}")
        table.add_row("진입환율", f"₩{position.entry_rate:.2f}")

        # 현재가
        table.add_row("현재가", f"${position.current_price:.2f}")
        table.add_row("현재환율", f"₩{position.current_rate:.2f}")

        # 구분선
        table.add_row("", "")

        # 평가 금액
        table.add_row("평가금액", f"${position.get_market_value_usd():,.2f}")
        table.add_row("", f"₩{position.get_market_value_krw():,.0f}")

        # 미실현 손익
        pnl_percent = position.get_unrealized_pnl_percent()
        table.add_row("미실현손익", f"[{pnl_color}]{pnl_usd:+,.2f} USD[/]")
        table.add_row("", f"[{pnl_color}]₩{position.get_unrealized_pnl_krw():+,.0f}[/]")
        table.add_row("손익률", f"[{pnl_color}]{pnl_percent:+.2f}%[/]")

        # 환율 영향
        currency_impact = position.get_currency_impact()
        currency_color = "red" if currency_impact >= 0 else "blue"
        table.add_row("환율영향", f"[{currency_color}]₩{currency_impact:+,.0f}[/]")

        # 세금 계산 (매도시 예상)
        if pnl_usd > 0:
            realized_pnl_krw = pnl_usd * position.current_rate
            tax_calc = self.tax_info.calculate_tax(realized_pnl_krw)
            if tax_calc['total_tax'] > 0:
                table.add_row("", "")
                table.add_row("예상세금", f"₩{tax_calc['total_tax']:,.0f}")
                table.add_row("세후손익", f"₩{realized_pnl_krw - tax_calc['total_tax']:+,.0f}")

        return Panel(table, title="포지션 정보", border_style="blue")

    def _render_strategy_info(self) -> Panel:
        """전략 정보 렌더링"""
        if not self.strategy:
            return Panel("전략 없음", title="전략 정보", border_style="yellow")

        # 전략 테이블
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("항목", style="bold")
        table.add_column("값", justify="right")

        table.add_row("전략명", self.strategy.name)

        # 현재 신호
        if self.current_signal:
            signal_colors = {
                SignalType.BUY: "green",
                SignalType.SELL: "red",
                SignalType.HOLD: "yellow",
                SignalType.NONE: "white"
            }

            signal_color = signal_colors.get(self.current_signal.signal_type, "white")
            signal_text = f"[{signal_color}]{self.current_signal.signal_type.value}[/]"

            table.add_row("신호", signal_text)
            table.add_row("신뢰도", f"{self.current_signal.confidence:.2f}")
            table.add_row("이유", self.current_signal.reason[:20] + "..." if len(self.current_signal.reason) > 20 else self.current_signal.reason)

            if self.current_signal.price > 0:
                table.add_row("제안가격", f"${self.current_signal.price:.2f}")
            if self.current_signal.quantity > 0:
                table.add_row("제안수량", f"{self.current_signal.quantity}주")
        else:
            table.add_row("신호", "대기중")

        # 전략 설정 정보
        if hasattr(self.strategy, 'get_info'):
            info = self.strategy.get_info()
            table.add_row("", "")
            for key, value in info.items():
                table.add_row(key, str(value))

        return Panel(table, title="전략 정보", border_style="magenta")

    def _render_trade_history(self) -> Panel:
        """거래 이력 렌더링"""
        if not self.trade_history:
            return Panel("거래 이력 없음", title="거래 이력", border_style="yellow")

        # 최근 5개 거래만 표시
        recent_trades = self.trade_history[-5:]

        table = Table(show_header=True, box=None)
        table.add_column("시간", style="dim", width=8)
        table.add_column("타입", width=4)
        table.add_column("수량", justify="right", width=6)
        table.add_column("가격", justify="right", width=10)
        table.add_column("손익", justify="right", width=12)

        for trade in recent_trades:
            time_str = trade.get('time', datetime.now()).strftime('%H:%M')
            trade_type = trade.get('type', 'N/A')
            quantity = trade.get('quantity', 0)
            price = trade.get('price', 0.0)
            pnl = trade.get('pnl', 0.0)

            type_color = "green" if trade_type == "BUY" else "red"
            pnl_color = "red" if pnl >= 0 else "blue"

            table.add_row(
                time_str,
                f"[{type_color}]{trade_type}[/]",
                f"{quantity:,}",
                f"${price:.2f}",
                f"[{pnl_color}]₩{pnl:+,.0f}[/]" if pnl != 0 else "─"
            )

        return Panel(table, title="거래 이력", border_style="green")

    def change_strategy(self, new_strategy: Any):
        """전략 변경"""
        old_name = self.strategy.name if self.strategy else "없음"
        self.strategy = new_strategy
        self.logger.info(f"전략 변경: {old_name} -> {new_strategy.name}")

    def get_status(self) -> Dict[str, Any]:
        """모니터 상태 조회"""
        return {
            'symbol': self.symbol,
            'symbol_name': self.symbol_name,
            'strategy': self.strategy.name if self.strategy else None,
            'has_data': self.current_data is not None,
            'has_position': self.current_position is not None,
            'current_price_usd': self.current_data.current_price if self.current_data else 0.0,
            'current_price_krw': self.current_data.get_price_krw() if self.current_data else 0.0,
            'unrealized_pnl_usd': self.current_position.get_unrealized_pnl_usd() if self.current_position else 0.0,
            'unrealized_pnl_krw': self.current_position.get_unrealized_pnl_krw() if self.current_position else 0.0,
            'trade_count': len(self.trade_history),
            'last_update': self.current_data.timestamp.isoformat() if self.current_data else None
        }