"""자동매매 엔진 로직 테스트"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.config import KISConfig, Settings, TradingConfig
from app.models import ChartData, EngineStatus, Position, SignalType, StockPrice
from app.trading.engine import TradingEngine


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
        engine.order.get_balance = AsyncMock(return_value=[
            Position(
                symbol="005930", name="삼성전자", quantity=10,
                avg_price=70000, current_price=72000,
            )
        ])
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

        engine.order.get_balance = AsyncMock(return_value=[])
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

        engine.order.get_balance = AsyncMock(return_value=[])
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

        engine.order.get_balance = AsyncMock(return_value=[
            Position(
                symbol="005930", name="삼성전자", quantity=10,
                avg_price=70000, current_price=72000,
            ),
        ])
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

        engine.order.get_balance = AsyncMock(return_value=[])
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
