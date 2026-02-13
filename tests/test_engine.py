"""자동매매 엔진 로직 테스트"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.config import KISConfig, Settings, TradingConfig
from app.models import AccountSummary, ChartData, EngineStatus, Position, SignalType, StockPrice
from app.trading.engine import TradingEngine

_EMPTY_SUMMARY = AccountSummary()


def _make_settings() -> Settings:
    return Settings(
        kis=KISConfig(
            app_key="test",
            app_secret="test",
            account_no="12345678",
        ),
        trading=TradingConfig(
            watch_symbols=["005930"],
            order_amount=500_000,
            short_ma_period=5,
            long_ma_period=20,
            trading_interval=1,
            max_consecutive_errors=3,
        ),
    )


def _make_chart(closes: list[int]) -> list[ChartData]:
    return [
        ChartData(
            date=f"2026{(i // 28 + 1):02d}{(i % 28 + 1):02d}",
            open=c, high=c + 100, low=c - 100, close=c, volume=1000,
        )
        for i, c in enumerate(closes)
    ]


class TestTickSkips:
    """매매 루프가 장외 시간/주말/공휴일에 스킵되는지 테스트"""

    @pytest.fixture
    def engine(self):
        settings = _make_settings()
        eng = TradingEngine(settings)
        eng._watch_symbols = ["005930"]
        eng._status = EngineStatus.RUNNING
        return eng

    @pytest.mark.asyncio
    async def test_skip_weekend(self, engine):
        """주말에 _tick() 스킵"""
        # 2026-02-14 토요일 10:00
        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 14, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_current_price = AsyncMock()
            await engine._tick()

            # 현재가 조회가 호출되지 않아야 함
            engine.market.get_current_price.assert_not_called()

    @pytest.mark.asyncio
    async def test_skip_holiday(self, engine):
        """공휴일(설날)에 _tick() 스킵"""
        # 2026-02-17 화요일 설날
        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 17, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_current_price = AsyncMock()
            await engine._tick()

            engine.market.get_current_price.assert_not_called()

    @pytest.mark.asyncio
    async def test_skip_before_market_open(self, engine):
        """장 시작 전 스킵"""
        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 12, 8, 30, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_current_price = AsyncMock()
            await engine._tick()

            engine.market.get_current_price.assert_not_called()


class TestBuy:
    """매수 테스트 (잔고 직접 조회로 중복 방지)"""

    @pytest.mark.asyncio
    async def test_no_duplicate_buy(self):
        """이미 보유 중인 종목에 대한 매수 시그널은 무시"""
        settings = _make_settings()
        engine = TradingEngine(settings)

        # get_balance()가 이미 보유 중인 포지션 반환
        engine.order.get_balance = AsyncMock(return_value=([
            Position(
                symbol="005930", name="삼성전자", quantity=10,
                avg_price=70000, current_price=72000,
            )
        ], _EMPTY_SUMMARY))
        engine.order.buy = AsyncMock()
        now = datetime(2026, 2, 12, 10, 0, 0)

        await engine._execute_buy("005930", 72000, 500_000, now)

        # 매수 주문이 호출되지 않아야 함
        engine.order.buy.assert_not_called()

    @pytest.mark.asyncio
    async def test_buy_when_not_holding(self):
        """미보유 종목은 정상 매수"""
        settings = _make_settings()
        engine = TradingEngine(settings)

        engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))
        engine.order.buy = AsyncMock(return_value={
            "success": True, "order_no": "0001", "message": "ok",
        })

        now = datetime(2026, 2, 12, 10, 0, 0)
        await engine._execute_buy("005930", 72000, 500_000, now)

        engine.order.buy.assert_called_once_with("005930", 6)  # 500000 // 72000 = 6

    @pytest.mark.asyncio
    async def test_buy_zero_quantity_skip(self):
        """매수 수량이 0이면 스킵"""
        settings = _make_settings()
        engine = TradingEngine(settings)

        engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))
        engine.order.buy = AsyncMock()

        now = datetime(2026, 2, 12, 10, 0, 0)
        # 주문금액 500_000 / 가격 1_000_000 = 0주
        await engine._execute_buy("005930", 1_000_000, 500_000, now)

        engine.order.buy.assert_not_called()


class TestSell:
    """매도 테스트 (잔고 직접 조회)"""

    @pytest.mark.asyncio
    async def test_sell_when_holding(self):
        """보유 종목 전량 매도"""
        settings = _make_settings()
        engine = TradingEngine(settings)

        engine.order.get_balance = AsyncMock(return_value=([
            Position(
                symbol="005930", name="삼성전자", quantity=10,
                avg_price=70000, current_price=72000,
            ),
        ], _EMPTY_SUMMARY))
        engine.order.sell = AsyncMock(return_value={
            "success": True, "order_no": "0002", "message": "ok",
        })

        now = datetime(2026, 2, 12, 10, 0, 0)
        await engine._execute_sell("005930", now)

        engine.order.sell.assert_called_once_with("005930", 10)

    @pytest.mark.asyncio
    async def test_sell_skip_when_not_holding(self):
        """미보유 종목은 매도 생략"""
        settings = _make_settings()
        engine = TradingEngine(settings)

        engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))
        engine.order.sell = AsyncMock()

        now = datetime(2026, 2, 12, 10, 0, 0)
        await engine._execute_sell("005930", now)

        engine.order.sell.assert_not_called()


class TestStartFailure:
    """엔진 시작 실패 테스트"""

    @pytest.mark.asyncio
    async def test_start_fails_on_balance_error(self):
        """잔고 조회 실패 시 엔진 시작 중단"""
        settings = _make_settings()
        engine = TradingEngine(settings)
        engine.order.get_balance = AsyncMock(
            side_effect=RuntimeError("API connection failed")
        )

        with pytest.raises(RuntimeError, match="API connection failed"):
            await engine.start(["005930"])

        assert engine._status == EngineStatus.STOPPED


class TestConsecutiveErrorStop:
    """연속 에러 시 엔진 정지 테스트"""

    @pytest.mark.asyncio
    async def test_consecutive_error_stop(self):
        """연속 max_consecutive_errors회 오류 시 STOPPED로 전환"""
        settings = _make_settings()
        settings.trading.trading_interval = 0
        engine = TradingEngine(settings)
        engine._status = EngineStatus.RUNNING
        engine._watch_symbols = ["005930"]

        # _tick이 항상 예외를 발생시키도록 설정
        async def failing_tick():
            raise RuntimeError("test error")

        engine._tick = failing_tick

        import asyncio

        task = asyncio.create_task(engine._run_loop())
        await asyncio.sleep(0.5)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert engine._status == EngineStatus.STOPPED
        assert engine._consecutive_errors >= 3


class TestPartialFailure:
    """부분 실패 시에도 에러가 전파되는지 테스트"""

    @pytest.mark.asyncio
    async def test_partial_failure_raises(self):
        """2종목 중 1개만 실패해도 예외 발생"""
        settings = _make_settings()
        settings.trading.watch_symbols = ["005930", "000660"]
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930", "000660"]
        engine._status = EngineStatus.RUNNING

        # 골든크로스 차트 데이터 (SMA5 > SMA20)
        chart = _make_chart([100] * 15 + [100, 101, 102, 103, 104, 110, 115, 120, 125, 130])
        price = StockPrice(
            symbol="005930", current_price=130,
            change=0, change_rate=0.0, volume=1000,
            high=130, low=130, opening=130,
        )

        call_count = 0

        async def mock_chart(symbol, days=30):
            nonlocal call_count
            call_count += 1
            if symbol == "000660":
                raise RuntimeError("API error for 000660")
            return chart

        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 12, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_daily_chart = mock_chart
            engine.market.get_current_price = AsyncMock(return_value=price)

            with pytest.raises(RuntimeError, match="종목 처리 실패: 1/2개"):
                await engine._tick()


class TestTickE2E:
    """E2E: 시세조회 → 전략판단 → 주문실행 전체 흐름 테스트"""

    @pytest.mark.asyncio
    async def test_golden_cross_triggers_buy(self):
        """골든크로스 시그널 → 미보유 확인 → 매수 주문까지 전체 흐름"""
        settings = _make_settings()
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        # 골든크로스: 전일 SMA5==SMA20 → 오늘 SMA5 > SMA20
        # 20일 100 유지 후 마지막 1일 급등 → SMA5 올라가고 SMA20 거의 유지
        chart = _make_chart([100] * 20 + [200])
        price = StockPrice(
            symbol="005930", current_price=72000,
            change=1000, change_rate=1.4, volume=10000,
            high=73000, low=71000, opening=71500,
        )

        with patch("app.trading.engine.datetime") as mock_dt:
            # 장 시간 내 평일 (2026-02-12 목요일 10:00)
            mock_dt.now.return_value = datetime(2026, 2, 12, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_daily_chart = AsyncMock(return_value=chart)
            engine.market.get_current_price = AsyncMock(return_value=price)
            engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))
            engine.order.buy = AsyncMock(return_value={
                "success": True, "order_no": "0001", "message": "ok",
            })

            await engine._tick()

        # 시세 조회 확인
        engine.market.get_daily_chart.assert_called_once()
        engine.market.get_current_price.assert_called_once_with("005930")

        # 시그널 기록 확인
        assert len(engine._signals) == 1
        assert engine._signals[0].signal == SignalType.BUY
        assert engine._signals[0].symbol == "005930"

        # 매수 주문 확인 (500_000 // 72_000 = 6주)
        engine.order.buy.assert_called_once_with("005930", 6)

        # 주문 이력 기록 확인
        assert len(engine._orders) == 1
        assert engine._orders[0].side == "buy"
        assert engine._orders[0].success is True

    @pytest.mark.asyncio
    async def test_dead_cross_triggers_sell(self):
        """데드크로스 시그널 → 보유 확인 → 매도 주문까지 전체 흐름"""
        settings = _make_settings()
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        # 데드크로스: 전일 SMA5==SMA20 → 오늘 SMA5 < SMA20
        # 20일 200 유지 후 마지막 1일 급락 → SMA5 떨어지고 SMA20 거의 유지
        chart = _make_chart([200] * 20 + [100])
        price = StockPrice(
            symbol="005930", current_price=68000,
            change=-2000, change_rate=-2.9, volume=15000,
            high=70000, low=67000, opening=69500,
        )

        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 12, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_daily_chart = AsyncMock(return_value=chart)
            engine.market.get_current_price = AsyncMock(return_value=price)
            engine.order.get_balance = AsyncMock(return_value=([
                Position(
                    symbol="005930", name="삼성전자", quantity=10,
                    avg_price=70000, current_price=68000,
                ),
            ], _EMPTY_SUMMARY))
            engine.order.sell = AsyncMock(return_value={
                "success": True, "order_no": "0002", "message": "ok",
            })

            await engine._tick()

        # 시그널 확인
        assert len(engine._signals) == 1
        assert engine._signals[0].signal == SignalType.SELL

        # 전량 매도 확인
        engine.order.sell.assert_called_once_with("005930", 10)

        # 주문 이력 확인
        assert len(engine._orders) == 1
        assert engine._orders[0].side == "sell"
        assert engine._orders[0].success is True

    @pytest.mark.asyncio
    async def test_hold_signal_no_order(self):
        """HOLD 시그널 → 주문 없음 확인"""
        settings = _make_settings()
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        # 변동 없는 플랫 차트 → HOLD
        chart = _make_chart([100] * 30)
        price = StockPrice(
            symbol="005930", current_price=70000,
            change=0, change_rate=0.0, volume=5000,
            high=70500, low=69500, opening=70000,
        )

        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 12, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_daily_chart = AsyncMock(return_value=chart)
            engine.market.get_current_price = AsyncMock(return_value=price)
            engine.order.buy = AsyncMock()
            engine.order.sell = AsyncMock()

            await engine._tick()

        # HOLD 시그널 확인
        assert len(engine._signals) == 1
        assert engine._signals[0].signal == SignalType.HOLD

        # 주문 없음
        engine.order.buy.assert_not_called()
        engine.order.sell.assert_not_called()
