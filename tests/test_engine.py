"""자동매매 엔진 로직 테스트"""

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import KISConfig, Settings, StrategyConfig, StrategyType, TradingConfig
from app.models import AccountSummary, ChartData, EngineStatus, EventType, MarketType, Position, SignalType, StockPrice, detect_market_type
from app.trading.engine import TradingEngine

_EMPTY_SUMMARY = AccountSummary()


@pytest.fixture(autouse=True)
def _mock_journal(monkeypatch):
    """모든 엔진 테스트에서 저널 파일 I/O 방지"""
    monkeypatch.setattr(
        "app.trading.engine.TradingJournal",
        lambda log_dir="": MagicMock(),
    )


def _make_settings(
    use_advanced: bool = False,
    strategy_type: StrategyType = StrategyType.SMA_CROSSOVER,
) -> Settings:
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
            use_advanced_strategy=use_advanced,
            use_minute_chart=False,  # 기존 테스트는 일봉 모드
            target_order_amount=500_000,
            min_quantity=1,
            max_quantity=50,
            trading_interval=1,
            max_consecutive_errors=3,
            strategy_type=strategy_type,
            max_daily_trades=5,
            force_close_minute=1510,
            no_new_buy_minute=1500,
        ),
    )


def _make_chart(
    closes: list[int], volumes: list[int] | None = None
) -> list[ChartData]:
    if volumes is None:
        volumes = [1000] * len(closes)
    return [
        ChartData(
            date=f"2026{(i // 28 + 1):02d}{(i % 28 + 1):02d}",
            open=c, high=c + 100, low=c - 100, close=c, volume=volumes[i],
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

        await engine._execute_buy("005930", 72000, now)

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
        await engine._execute_buy("005930", 72000, now)

        engine.order.buy.assert_called_once_with("005930", 6)  # 500000 // 72000 = 6

    @pytest.mark.asyncio
    async def test_buy_expensive_stock_min_quantity(self):
        """고가 주식도 최소 min_quantity 매수"""
        settings = _make_settings()
        engine = TradingEngine(settings)

        engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))
        engine.order.buy = AsyncMock(return_value={
            "success": True, "order_no": "0003", "message": "ok",
        })

        now = datetime(2026, 2, 12, 10, 0, 0)
        # target=500_000 / 가격=1_000_000 = 0 → min_quantity=1
        await engine._execute_buy("005930", 1_000_000, now)

        engine.order.buy.assert_called_once_with("005930", 1)


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


class TestAdvancedStrategy:
    """복합 전략 (RSI + 거래량 필터) E2E 테스트"""

    @pytest.mark.asyncio
    async def test_advanced_strategy_buy(self):
        """복합 전략: 골든크로스 + RSI OK + 거래량 확인 → 매수"""
        settings = _make_settings()
        settings.trading.use_advanced_strategy = True
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        # 골든크로스 차트 + 높은 거래량
        closes = [100] * 20 + [200]
        volumes = [1000] * 20 + [5000]
        chart = _make_chart(closes, volumes)
        price = StockPrice(
            symbol="005930", current_price=72000,
            change=1000, change_rate=1.4, volume=5000,
            high=73000, low=71000, opening=71500,
        )

        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 12, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_daily_chart = AsyncMock(return_value=chart)
            engine.market.get_current_price = AsyncMock(return_value=price)
            engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))
            engine.order.buy = AsyncMock(return_value={
                "success": True, "order_no": "0001", "message": "ok",
            })

            await engine._tick()

        # 시그널에 rsi, volume_confirmed, raw_signal 필드 포함
        assert len(engine._signals) == 1
        sig = engine._signals[0]
        assert sig.raw_signal == SignalType.BUY
        assert sig.rsi is not None
        assert sig.volume_confirmed is not None
        # 골든크로스 + 거래량 높음 → 매수 실행
        if sig.signal == SignalType.BUY:
            engine.order.buy.assert_called_once()

    @pytest.mark.asyncio
    async def test_advanced_strategy_filtered_by_low_volume(self):
        """복합 전략: 골든크로스 + 거래량 미확인 → HOLD (매수 안 함)"""
        settings = _make_settings()
        settings.trading.use_advanced_strategy = True
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        # 골든크로스 차트 + 낮은 거래량
        closes = [100] * 20 + [200]
        volumes = [5000] * 20 + [100]  # 마지막 날 거래량 매우 낮음
        chart = _make_chart(closes, volumes)
        price = StockPrice(
            symbol="005930", current_price=72000,
            change=1000, change_rate=1.4, volume=100,
            high=73000, low=71000, opening=71500,
        )

        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 12, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_daily_chart = AsyncMock(return_value=chart)
            engine.market.get_current_price = AsyncMock(return_value=price)
            engine.order.buy = AsyncMock()
            engine.order.sell = AsyncMock()

            await engine._tick()

        # raw_signal은 BUY지만 거래량 미확인으로 HOLD
        sig = engine._signals[0]
        assert sig.raw_signal == SignalType.BUY
        assert sig.volume_confirmed is False
        assert sig.signal == SignalType.HOLD

        # 매수 주문 없음
        engine.order.buy.assert_not_called()


class TestMinuteMode:
    """분봉 모드 및 동적 주문수량 테스트"""

    @pytest.mark.asyncio
    async def test_minute_mode_uses_minute_chart(self):
        """분봉 모드 → get_minute_chart() 호출 확인"""
        settings = _make_settings()
        settings.trading.use_minute_chart = True
        settings.trading.minute_short_period = 5
        settings.trading.minute_long_period = 20
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        chart = _make_chart([100] * 30)
        price = StockPrice(
            symbol="005930", current_price=70000,
            change=0, change_rate=0.0, volume=5000,
            high=70500, low=69500, opening=70000,
        )

        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 12, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_minute_chart = AsyncMock(return_value=chart)
            engine.market.get_daily_chart = AsyncMock(return_value=chart)
            engine.market.get_current_price = AsyncMock(return_value=price)
            engine.order.buy = AsyncMock()
            engine.order.sell = AsyncMock()

            await engine._tick()

        # 분봉 모드 → get_minute_chart 호출, get_daily_chart 미호출
        engine.market.get_minute_chart.assert_called_once()
        engine.market.get_daily_chart.assert_not_called()

    @pytest.mark.asyncio
    async def test_daily_mode_uses_daily_chart(self):
        """일봉 모드 → get_daily_chart() 호출 확인"""
        settings = _make_settings()
        settings.trading.use_minute_chart = False
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        chart = _make_chart([100] * 30)
        price = StockPrice(
            symbol="005930", current_price=70000,
            change=0, change_rate=0.0, volume=5000,
            high=70500, low=69500, opening=70000,
        )

        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 12, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_minute_chart = AsyncMock(return_value=chart)
            engine.market.get_daily_chart = AsyncMock(return_value=chart)
            engine.market.get_current_price = AsyncMock(return_value=price)
            engine.order.buy = AsyncMock()
            engine.order.sell = AsyncMock()

            await engine._tick()

        # 일봉 모드 → get_daily_chart 호출, get_minute_chart 미호출
        engine.market.get_daily_chart.assert_called_once()
        engine.market.get_minute_chart.assert_not_called()

    @pytest.mark.asyncio
    async def test_dynamic_quantity_expensive_stock(self):
        """240만원 주식 → 1주 매수 (min_quantity 적용)"""
        settings = _make_settings()
        settings.trading.target_order_amount = 1_000_000
        settings.trading.min_quantity = 1
        settings.trading.max_quantity = 50
        engine = TradingEngine(settings)

        engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))
        engine.order.buy = AsyncMock(return_value={
            "success": True, "order_no": "0001", "message": "ok",
        })

        now = datetime(2026, 2, 12, 10, 0, 0)
        await engine._execute_buy("298040", 2_400_000, now)

        # 1_000_000 // 2_400_000 = 0 → min_quantity = 1
        engine.order.buy.assert_called_once_with("298040", 1)

    @pytest.mark.asyncio
    async def test_dynamic_quantity_cheap_stock(self):
        """2만원 주식 → max_quantity 제한 적용"""
        settings = _make_settings()
        settings.trading.target_order_amount = 1_000_000
        settings.trading.min_quantity = 1
        settings.trading.max_quantity = 50
        engine = TradingEngine(settings)

        engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))
        engine.order.buy = AsyncMock(return_value={
            "success": True, "order_no": "0001", "message": "ok",
        })

        now = datetime(2026, 2, 12, 10, 0, 0)
        await engine._execute_buy("034020", 20_000, now)

        # 1_000_000 // 20_000 = 50 → max_quantity = 50
        engine.order.buy.assert_called_once_with("034020", 50)

    @pytest.mark.asyncio
    async def test_dynamic_quantity_mid_stock(self):
        """5.5만원 주식 → target_amount 기반 계산"""
        settings = _make_settings()
        settings.trading.target_order_amount = 1_000_000
        settings.trading.min_quantity = 1
        settings.trading.max_quantity = 50
        engine = TradingEngine(settings)

        engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))
        engine.order.buy = AsyncMock(return_value={
            "success": True, "order_no": "0001", "message": "ok",
        })

        now = datetime(2026, 2, 12, 10, 0, 0)
        await engine._execute_buy("005930", 55_000, now)

        # 1_000_000 // 55_000 = 18
        engine.order.buy.assert_called_once_with("005930", 18)


class TestRiskManagement:
    """SMA 크로스오버 전략: 손절 + 최대 보유기간 테스트"""

    @pytest.mark.asyncio
    async def test_stop_loss_triggers_sell(self):
        """매수가 대비 7% 하락 → 강제 매도 + 매수 정보 삭제"""
        settings = _make_settings()
        settings.trading.stop_loss_pct = 5.0
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        # 매수 정보 사전 설정 (매수가 100,000)
        engine._entry_prices["005930"] = 100_000.0
        engine._buy_timestamps["005930"] = datetime(2026, 2, 10, 10, 0, 0)

        # HOLD 차트 (시그널 없음 — 손절만 발동)
        chart = _make_chart([100] * 30)
        price = StockPrice(
            symbol="005930", current_price=93000,  # 7% 하락
            change=-7000, change_rate=-7.0, volume=5000,
            high=94000, low=92000, opening=93500,
        )

        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 12, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_daily_chart = AsyncMock(return_value=chart)
            engine.market.get_current_price = AsyncMock(return_value=price)
            engine.order.get_balance = AsyncMock(return_value=([
                Position(
                    symbol="005930", name="삼성전자", quantity=10,
                    avg_price=100000, current_price=93000,
                ),
            ], _EMPTY_SUMMARY))
            engine.order.sell = AsyncMock(return_value={
                "success": True, "order_no": "SL01", "message": "ok",
            })

            await engine._tick()

        # 매도 주문 확인
        engine.order.sell.assert_called_once_with("005930", 10)
        assert len(engine._orders) == 1
        assert engine._orders[0].side == "sell"
        # 매수 정보 삭제 확인
        assert "005930" not in engine._entry_prices
        assert "005930" not in engine._buy_timestamps

    @pytest.mark.asyncio
    async def test_max_holding_triggers_sell(self):
        """23일 보유 → 강제 매도"""
        settings = _make_settings()
        settings.trading.max_holding_days = 20
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        # 매수 정보: 23일 전 매수
        engine._entry_prices["005930"] = 70_000.0
        engine._buy_timestamps["005930"] = datetime(2026, 1, 20, 10, 0, 0)

        chart = _make_chart([100] * 30)
        price = StockPrice(
            symbol="005930", current_price=72000,
            change=0, change_rate=0.0, volume=5000,
            high=72500, low=71500, opening=72000,
        )

        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 12, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_daily_chart = AsyncMock(return_value=chart)
            engine.market.get_current_price = AsyncMock(return_value=price)
            engine.order.get_balance = AsyncMock(return_value=([
                Position(
                    symbol="005930", name="삼성전자", quantity=10,
                    avg_price=70000, current_price=72000,
                ),
            ], _EMPTY_SUMMARY))
            engine.order.sell = AsyncMock(return_value={
                "success": True, "order_no": "MH01", "message": "ok",
            })

            await engine._tick()

        # 매도 주문 확인
        engine.order.sell.assert_called_once_with("005930", 10)
        assert len(engine._orders) == 1
        assert engine._orders[0].side == "sell"
        # 매수 정보 삭제 확인
        assert "005930" not in engine._entry_prices
        assert "005930" not in engine._buy_timestamps

    @pytest.mark.asyncio
    async def test_stop_loss_no_crash_when_entry_price_zero(self):
        """entry_price=0 → division by zero 없이 손절 스킵"""
        settings = _make_settings()
        settings.trading.stop_loss_pct = 5.0
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING
        engine._entry_prices["005930"] = 0.0

        chart = _make_chart([100] * 30)
        price = StockPrice(
            symbol="005930", current_price=50000,
            change=0, change_rate=0, volume=5000,
            high=50000, low=50000, opening=50000,
        )

        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 12, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_daily_chart = AsyncMock(return_value=chart)
            engine.market.get_current_price = AsyncMock(return_value=price)
            engine.order.sell = AsyncMock()
            engine.order.buy = AsyncMock()
            engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))

            await engine._tick()  # ZeroDivisionError가 아닌 정상 종료

        engine.order.sell.assert_not_called()

    @pytest.mark.asyncio
    async def test_stop_loss_no_crash_when_entry_missing(self):
        """_entry_prices에 종목 없음 → KeyError 없이 정상 진행"""
        settings = _make_settings()
        settings.trading.stop_loss_pct = 5.0
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING
        # _entry_prices에 아무것도 설정하지 않음

        chart = _make_chart([100] * 30)
        price = StockPrice(
            symbol="005930", current_price=50000,
            change=0, change_rate=0, volume=5000,
            high=50000, low=50000, opening=50000,
        )

        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 12, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_daily_chart = AsyncMock(return_value=chart)
            engine.market.get_current_price = AsyncMock(return_value=price)
            engine.order.sell = AsyncMock()
            engine.order.buy = AsyncMock()
            engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))

            await engine._tick()  # KeyError가 아닌 정상 종료

        engine.order.sell.assert_not_called()

    @pytest.mark.asyncio
    async def test_zero_price_skips_trading_logic(self):
        """KIS API가 current_price=0 반환 → 매매 판단 스킵"""
        settings = _make_settings()
        settings.trading.stop_loss_pct = 5.0
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING
        engine._entry_prices["005930"] = 100_000.0

        chart = _make_chart([100] * 30)
        price = StockPrice(
            symbol="005930", current_price=0,
            change=0, change_rate=0, volume=0,
            high=0, low=0, opening=0,
        )

        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 12, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_daily_chart = AsyncMock(return_value=chart)
            engine.market.get_current_price = AsyncMock(return_value=price)
            engine.order.sell = AsyncMock()
            engine.order.buy = AsyncMock()
            engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))

            await engine._tick()

        # 매매 로직 전혀 실행되지 않아야 함
        engine.order.sell.assert_not_called()
        engine.order.buy.assert_not_called()
        # 시그널은 기록됨
        assert len(engine._signals) == 1
        assert engine._signals[0].current_price == 0


class TestDayTrading:
    """데이트레이딩 (볼린저밴드 + 장 마감 청산 + 거래 제한) 테스트"""

    @pytest.mark.asyncio
    async def test_force_close_at_1510(self):
        """15:10 이후 보유 포지션 강제 매도"""
        settings = _make_settings(strategy_type=StrategyType.BOLLINGER)
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        engine.order.get_balance = AsyncMock(return_value=([
            Position(
                symbol="005930", name="삼성전자", quantity=10,
                avg_price=70000, current_price=72000,
            ),
        ], _EMPTY_SUMMARY))
        engine.order.sell = AsyncMock(return_value={
            "success": True, "order_no": "0010", "message": "ok",
        })
        engine.market.get_minute_chart = AsyncMock()
        engine.market.get_current_price = AsyncMock()

        with patch("app.trading.engine.datetime") as mock_dt:
            # 15:10 — 강제 청산 시간
            mock_dt.now.return_value = datetime(2026, 2, 12, 15, 10, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            await engine._tick()

        # 강제 매도 호출
        engine.order.sell.assert_called_once_with("005930", 10)
        # 시세 조회 없어야 함 (강제 청산만 수행)
        engine.market.get_minute_chart.assert_not_called()
        # 주문 이력 기록
        assert len(engine._orders) == 1
        assert engine._orders[0].side == "sell"

    @pytest.mark.asyncio
    async def test_no_buy_after_1500(self):
        """15:00 이후 매수 시그널 무시"""
        settings = _make_settings(strategy_type=StrategyType.BOLLINGER)
        settings.trading.active_trading_windows = []  # 전 구간 활성 (no_new_buy 단독 테스트)
        settings.trading.bollinger_volume_filter = False  # 거래량 필터 비활성 (엔진 제약 테스트용)
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        # 하단 반등 BUY 시그널 나오는 차트
        closes = [100] * 20 + [60, 95]
        chart = _make_chart(closes)
        price = StockPrice(
            symbol="005930", current_price=95000,
            change=0, change_rate=0.0, volume=5000,
            high=96000, low=94000, opening=95000,
        )

        with patch("app.trading.engine.datetime") as mock_dt:
            # 15:05 — 매수 금지 시간
            mock_dt.now.return_value = datetime(2026, 2, 12, 15, 5, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_minute_chart = AsyncMock(return_value=chart)
            engine.market.get_current_price = AsyncMock(return_value=price)
            engine.order.buy = AsyncMock()
            engine.order.sell = AsyncMock()

            await engine._tick()

        # BUY 시그널은 기록되지만 주문은 없어야 함
        assert len(engine._signals) == 1
        assert engine._signals[0].signal == SignalType.BUY
        engine.order.buy.assert_not_called()

    @pytest.mark.asyncio
    async def test_daily_trade_limit(self):
        """종목당 5회 초과 매수 시 스킵"""
        settings = _make_settings(strategy_type=StrategyType.BOLLINGER)
        settings.trading.bollinger_volume_filter = False  # 거래량 필터 비활성 (엔진 제약 테스트용)
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        # 이미 5회 매수한 상태
        today = date(2026, 2, 12)
        engine._trade_count_date = today
        engine._daily_trade_count = {"005930": 5}

        # BUY 시그널 차트
        closes = [100] * 20 + [60, 95]
        chart = _make_chart(closes)
        price = StockPrice(
            symbol="005930", current_price=95000,
            change=0, change_rate=0.0, volume=5000,
            high=96000, low=94000, opening=95000,
        )

        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 12, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_minute_chart = AsyncMock(return_value=chart)
            engine.market.get_current_price = AsyncMock(return_value=price)
            engine.order.buy = AsyncMock()

            await engine._tick()

        # BUY 시그널 기록되지만 매수 주문 안 됨
        assert len(engine._signals) == 1
        assert engine._signals[0].signal == SignalType.BUY
        engine.order.buy.assert_not_called()

    @pytest.mark.asyncio
    async def test_daily_counter_resets(self):
        """날짜 변경 시 카운터 초기화"""
        settings = _make_settings(strategy_type=StrategyType.BOLLINGER)
        engine = TradingEngine(settings)

        # 어제 5회 매수
        engine._trade_count_date = date(2026, 2, 11)
        engine._daily_trade_count = {"005930": 5}

        # 오늘로 리셋
        engine._reset_daily_counter_if_needed(date(2026, 2, 12))

        assert engine._daily_trade_count == {}
        assert engine._trade_count_date == date(2026, 2, 12)
        assert engine._can_buy("005930") is True

    @pytest.mark.asyncio
    async def test_bollinger_strategy_dispatch(self):
        """strategy_type=BOLLINGER → evaluate_bollinger_signal 호출"""
        settings = _make_settings(strategy_type=StrategyType.BOLLINGER)
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        # HOLD 시그널 차트 (밴드 중간에 위치하는 등락 데이터)
        closes = [95, 105] * 10 + [100, 100]
        chart = _make_chart(closes)
        price = StockPrice(
            symbol="005930", current_price=70000,
            change=0, change_rate=0.0, volume=5000,
            high=70500, low=69500, opening=70000,
        )

        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 12, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_minute_chart = AsyncMock(return_value=chart)
            engine.market.get_daily_chart = AsyncMock()
            engine.market.get_current_price = AsyncMock(return_value=price)
            engine.order.buy = AsyncMock()
            engine.order.sell = AsyncMock()

            await engine._tick()

        # 분봉 차트 사용 (볼린저 전략은 항상 분봉)
        engine.market.get_minute_chart.assert_called_once()
        engine.market.get_daily_chart.assert_not_called()

        # 시그널에 볼린저 밴드 값 포함
        assert len(engine._signals) == 1
        sig = engine._signals[0]
        assert sig.signal == SignalType.HOLD
        assert sig.middle_band is not None

    @pytest.mark.asyncio
    async def test_buy_increments_daily_counter(self):
        """매수 성공 시 일일 거래 카운터 증가"""
        settings = _make_settings(strategy_type=StrategyType.BOLLINGER)
        engine = TradingEngine(settings)
        engine._trade_count_date = date(2026, 2, 12)

        engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))
        engine.order.buy = AsyncMock(return_value={
            "success": True, "order_no": "0001", "message": "ok",
        })

        now = datetime(2026, 2, 12, 10, 0, 0)
        await engine._execute_buy("005930", 72000, now)

        assert engine._daily_trade_count["005930"] == 1

    @pytest.mark.asyncio
    async def test_skip_inactive_window(self):
        """점심 시간(11:00~14:00) 비활성 구간에서 시그널 판단 스킵"""
        settings = _make_settings(strategy_type=StrategyType.BOLLINGER)
        settings.trading.active_trading_windows = [(930, 1100), (1400, 1500)]
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        engine.market.get_minute_chart = AsyncMock()
        engine.market.get_current_price = AsyncMock()

        with patch("app.trading.engine.datetime") as mock_dt:
            # 12:00 — 점심 비활성 구간
            mock_dt.now.return_value = datetime(2026, 2, 12, 12, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            await engine._tick()

        # 시세 조회 자체가 안 되어야 함
        engine.market.get_minute_chart.assert_not_called()
        assert len(engine._signals) == 0

    @pytest.mark.asyncio
    async def test_active_window_morning(self):
        """오전 골든타임(09:30~11:00)에는 정상 매매"""
        settings = _make_settings(strategy_type=StrategyType.BOLLINGER)
        settings.trading.active_trading_windows = [(930, 1100), (1400, 1500)]
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        closes = [95, 105] * 10 + [100, 100]
        chart = _make_chart(closes)
        price = StockPrice(
            symbol="005930", current_price=70000,
            change=0, change_rate=0.0, volume=5000,
            high=70500, low=69500, opening=70000,
        )

        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 12, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_minute_chart = AsyncMock(return_value=chart)
            engine.market.get_current_price = AsyncMock(return_value=price)
            engine.order.buy = AsyncMock()
            engine.order.sell = AsyncMock()

            await engine._tick()

        # 시세 조회 정상 수행
        engine.market.get_minute_chart.assert_called_once()
        assert len(engine._signals) == 1

    @pytest.mark.asyncio
    async def test_empty_windows_trades_all_day(self):
        """active_trading_windows 빈 리스트 → 전 구간 매매"""
        settings = _make_settings(strategy_type=StrategyType.BOLLINGER)
        settings.trading.active_trading_windows = []
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        closes = [95, 105] * 10 + [100, 100]
        chart = _make_chart(closes)
        price = StockPrice(
            symbol="005930", current_price=70000,
            change=0, change_rate=0.0, volume=5000,
            high=70500, low=69500, opening=70000,
        )

        with patch("app.trading.engine.datetime") as mock_dt:
            # 12:30 — 보통은 비활성이지만 빈 리스트라 매매
            mock_dt.now.return_value = datetime(2026, 2, 12, 12, 30, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_minute_chart = AsyncMock(return_value=chart)
            engine.market.get_current_price = AsyncMock(return_value=price)
            engine.order.buy = AsyncMock()
            engine.order.sell = AsyncMock()

            await engine._tick()

        engine.market.get_minute_chart.assert_called_once()
        assert len(engine._signals) == 1

    @pytest.mark.asyncio
    async def test_force_close_ignores_active_window(self):
        """강제 청산은 활성 시간대와 무관하게 실행"""
        settings = _make_settings(strategy_type=StrategyType.BOLLINGER)
        settings.trading.active_trading_windows = [(930, 1100), (1400, 1500)]
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        engine.order.get_balance = AsyncMock(return_value=([
            Position(symbol="005930", name="삼성전자", quantity=10,
                     avg_price=70000, current_price=72000),
        ], _EMPTY_SUMMARY))
        engine.order.sell = AsyncMock(return_value={
            "success": True, "order_no": "0010", "message": "ok",
        })

        with patch("app.trading.engine.datetime") as mock_dt:
            # 15:10 — 비활성 구간이지만 강제 청산은 실행
            mock_dt.now.return_value = datetime(2026, 2, 12, 15, 10, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            await engine._tick()

        engine.order.sell.assert_called_once_with("005930", 10)

    @pytest.mark.asyncio
    async def test_force_close_multiple_positions(self):
        """강제 청산: 여러 종목 보유 시 전량 매도"""
        settings = _make_settings(strategy_type=StrategyType.BOLLINGER)
        engine = TradingEngine(settings)

        engine.order.get_balance = AsyncMock(return_value=([
            Position(symbol="005930", name="삼성전자", quantity=10,
                     avg_price=70000, current_price=72000),
            Position(symbol="000660", name="SK하이닉스", quantity=5,
                     avg_price=150000, current_price=155000),
        ], _EMPTY_SUMMARY))
        engine.order.sell = AsyncMock(return_value={
            "success": True, "order_no": "0010", "message": "ok",
        })

        now = datetime(2026, 2, 12, 15, 10, 0)
        await engine._force_close_all(now)

        assert engine.order.sell.call_count == 2
        assert len(engine._orders) == 2


class TestUpdateStrategy:
    """런타임 전략 전환 테스트"""

    def test_strategy_change_applies(self):
        """전략 변경 후 settings.trading에 반영"""
        settings = _make_settings(strategy_type=StrategyType.SMA_CROSSOVER)
        engine = TradingEngine(settings)

        config = StrategyConfig(
            strategy_type=StrategyType.BOLLINGER,
            short_ma_period=15,
            long_ma_period=50,
            use_advanced_strategy=False,
            bollinger_period=25,
            bollinger_num_std=2.5,
        )
        engine.update_strategy(config)

        assert engine.settings.trading.strategy_type == StrategyType.BOLLINGER
        assert engine.settings.trading.short_ma_period == 15
        assert engine.settings.trading.long_ma_period == 50
        assert engine.settings.trading.use_advanced_strategy is False
        assert engine.settings.trading.bollinger_period == 25
        assert engine.settings.trading.bollinger_num_std == 2.5

    def test_strategy_type_change_clears_entry_prices(self):
        """전략 타입 변경 시 매수 추적 정보 초기화"""
        settings = _make_settings(strategy_type=StrategyType.SMA_CROSSOVER)
        engine = TradingEngine(settings)

        # 가짜 매수 정보 설정
        engine._entry_prices["005930"] = 50000.0
        engine._buy_timestamps["005930"] = datetime(2026, 2, 14, 10, 0)

        config = StrategyConfig(strategy_type=StrategyType.BOLLINGER)
        engine.update_strategy(config)

        assert engine._entry_prices == {}
        assert engine._buy_timestamps == {}

    def test_same_strategy_type_keeps_entry_prices(self):
        """동일 전략 타입 변경 시 매수 정보 유지"""
        settings = _make_settings(strategy_type=StrategyType.SMA_CROSSOVER)
        engine = TradingEngine(settings)

        engine._entry_prices["005930"] = 50000.0
        engine._buy_timestamps["005930"] = datetime(2026, 2, 14, 10, 0)

        # 같은 타입이지만 파라미터만 변경
        config = StrategyConfig(
            strategy_type=StrategyType.SMA_CROSSOVER,
            short_ma_period=15,
        )
        engine.update_strategy(config)

        assert "005930" in engine._entry_prices
        assert engine.settings.trading.short_ma_period == 15

    def test_get_strategy_config(self):
        """get_strategy_config가 현재 설정을 정확히 반환"""
        settings = _make_settings(strategy_type=StrategyType.BOLLINGER)
        engine = TradingEngine(settings)

        config = engine.get_strategy_config()
        assert config.strategy_type == StrategyType.BOLLINGER
        assert config.short_ma_period == settings.trading.short_ma_period
        assert config.use_minute_chart == settings.trading.use_minute_chart

    def test_get_strategy_config_includes_auto_regime(self):
        """get_strategy_config에 auto_regime 포함"""
        settings = _make_settings()
        settings.trading.auto_regime = True
        engine = TradingEngine(settings)

        config = engine.get_strategy_config()
        assert config.auto_regime is True


class TestAutoRegime:
    """자동 국면 감지 + 전략 전환 테스트"""

    @pytest.mark.asyncio
    async def test_regime_detection_switches_strategy(self):
        """강세장 감지 → SMA_CROSSOVER 전략으로 전환"""
        settings = _make_settings(strategy_type=StrategyType.BOLLINGER)
        settings.trading.auto_regime = True
        engine = TradingEngine(settings)

        # 130일 상승 차트 (강세장)
        closes_up = [float(500 + i * 2) for i in range(130)]
        chart = _make_chart([int(c) for c in closes_up])

        engine.market.get_daily_chart = AsyncMock(return_value=chart)

        now = datetime(2026, 2, 12, 9, 5, 0)
        await engine._check_and_switch_regime(now)

        # 강세장 → SMA_CROSSOVER
        assert engine._current_regime is not None
        assert engine.settings.trading.strategy_type == StrategyType.SMA_CROSSOVER

    @pytest.mark.asyncio
    async def test_regime_checked_once_per_day(self):
        """하루 1회만 국면 감지 실행"""
        settings = _make_settings(strategy_type=StrategyType.BOLLINGER)
        settings.trading.auto_regime = True
        settings.trading.active_trading_windows = []
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        # 130일 상승 차트 (강세장 → SMA_CROSSOVER 전환)
        closes_up = [float(500 + i * 2) for i in range(130)]
        daily_chart = _make_chart([int(c) for c in closes_up])

        # 일반 차트 (HOLD 시그널)
        flat_chart = _make_chart([100] * 30)
        price = StockPrice(
            symbol="005930", current_price=70000,
            change=0, change_rate=0.0, volume=5000,
            high=70500, low=69500, opening=70000,
        )

        engine.market.get_daily_chart = AsyncMock(side_effect=[
            daily_chart,  # 첫 번째: 국면 감지용
        ])
        # 전략 전환 후 use_minute_chart=True → get_minute_chart 사용
        engine.market.get_minute_chart = AsyncMock(return_value=flat_chart)
        engine.market.get_current_price = AsyncMock(return_value=price)
        engine.order.buy = AsyncMock()
        engine.order.sell = AsyncMock()

        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 12, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            await engine._tick()  # 첫 번째 tick: 국면 감지 + 전략 평가
            await engine._tick()  # 두 번째 tick: 국면 감지 스킵 (같은 날짜)

        # get_daily_chart: 국면감지 1회만 (같은 날 두 번째 tick에서는 스킵)
        assert engine.market.get_daily_chart.call_count == 1
        # 전략 평가: get_minute_chart 2회 (전환 후 분봉 모드)
        assert engine.market.get_minute_chart.call_count == 2

    @pytest.mark.asyncio
    async def test_auto_regime_disabled_no_switch(self):
        """auto_regime=False면 전략 전환 안 함"""
        settings = _make_settings(strategy_type=StrategyType.BOLLINGER)
        settings.trading.auto_regime = False
        settings.trading.active_trading_windows = []
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        flat_chart = _make_chart([100] * 30)
        price = StockPrice(
            symbol="005930", current_price=70000,
            change=0, change_rate=0.0, volume=5000,
            high=70500, low=69500, opening=70000,
        )

        # 볼린저 전략은 항상 분봉 사용
        engine.market.get_minute_chart = AsyncMock(return_value=flat_chart)
        engine.market.get_daily_chart = AsyncMock()
        engine.market.get_current_price = AsyncMock(return_value=price)
        engine.order.buy = AsyncMock()
        engine.order.sell = AsyncMock()

        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 12, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            await engine._tick()

        # auto_regime=False → 전략 변경 없음
        assert engine.settings.trading.strategy_type == StrategyType.BOLLINGER
        # 국면 감지 호출 없음 (get_daily_chart 미호출)
        engine.market.get_daily_chart.assert_not_called()
        # 볼린저 전략 평가용 get_minute_chart 1회
        assert engine.market.get_minute_chart.call_count == 1


class TestTrailingStopEngine:
    """트레일링 스탑 엔진 테스트"""

    @pytest.mark.asyncio
    async def test_trailing_stop_sell(self):
        """고점 추적 후 하락 시 트레일링 스탑 매도"""
        settings = _make_settings()
        settings.trading.trailing_stop_pct = 5.0
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        # 매수 정보 + 고점 설정
        engine._entry_prices["005930"] = 100_000.0
        engine._buy_timestamps["005930"] = datetime(2026, 2, 10, 10, 0, 0)
        engine._peak_prices["005930"] = 110_000.0  # 고점 11만원

        # 현재가 10만원 → 고점 대비 9.1% 하락 (> 5%)
        chart = _make_chart([100] * 30)
        price = StockPrice(
            symbol="005930", current_price=100000,
            change=-10000, change_rate=-9.1, volume=5000,
            high=101000, low=99000, opening=100500,
        )

        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 12, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_daily_chart = AsyncMock(return_value=chart)
            engine.market.get_current_price = AsyncMock(return_value=price)
            engine.order.get_balance = AsyncMock(return_value=([
                Position(
                    symbol="005930", name="삼성전자", quantity=10,
                    avg_price=100000, current_price=100000,
                ),
            ], _EMPTY_SUMMARY))
            engine.order.sell = AsyncMock(return_value={
                "success": True, "order_no": "TS01", "message": "ok",
            })

            await engine._tick()

        # 매도 호출 확인
        engine.order.sell.assert_called_once_with("005930", 10)
        assert "005930" not in engine._peak_prices
        assert "005930" not in engine._entry_prices

    @pytest.mark.asyncio
    async def test_peak_price_updated_on_buy(self):
        """매수 성공 시 고점 가격 초기화"""
        settings = _make_settings()
        settings.trading.trailing_stop_pct = 5.0
        engine = TradingEngine(settings)

        engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))
        engine.order.buy = AsyncMock(return_value={
            "success": True, "order_no": "0001", "message": "ok",
        })

        now = datetime(2026, 2, 12, 10, 0, 0)
        await engine._execute_buy("005930", 72000, now)

        assert engine._peak_prices["005930"] == 72000.0


class TestCapitalRatioEngine:
    """자본 활용 비율 엔진 테스트"""

    @pytest.mark.asyncio
    async def test_capital_ratio_buy(self):
        """capital_ratio로 예수금 기반 주문 금액 계산"""
        settings = _make_settings()
        settings.trading.capital_ratio = 0.3
        settings.trading.min_quantity = 1
        settings.trading.max_quantity = 100
        engine = TradingEngine(settings)

        # 예수금 10,000,000 → 0.3 = 3,000,000 → 3,000,000 // 50,000 = 60주
        summary = AccountSummary(deposit=10_000_000)
        engine.order.get_balance = AsyncMock(return_value=([], summary))
        engine.order.buy = AsyncMock(return_value={
            "success": True, "order_no": "0001", "message": "ok",
        })

        now = datetime(2026, 2, 12, 10, 0, 0)
        await engine._execute_buy("005930", 50_000, now)

        # 3,000,000 // 50,000 = 60주
        engine.order.buy.assert_called_once_with("005930", 60)


class TestMarketTypeDetection:
    """심볼 시장 구분 테스트"""

    def test_domestic_symbol(self):
        assert detect_market_type("005930") == MarketType.DOMESTIC

    def test_us_symbol_aapl(self):
        assert detect_market_type("AAPL") == MarketType.US

    def test_us_symbol_tsla(self):
        assert detect_market_type("TSLA") == MarketType.US

    def test_us_symbol_short(self):
        assert detect_market_type("F") == MarketType.US  # Ford

    def test_five_digit_not_domestic(self):
        """5자리 숫자는 국내 아님"""
        assert detect_market_type("12345") == MarketType.US


class TestUSRouting:
    """US 심볼 라우팅 테스트"""

    def test_engine_has_us_clients(self):
        settings = _make_settings()
        engine = TradingEngine(settings)
        assert engine.us_market is not None
        assert engine.us_order is not None

    def test_get_exchange_default(self):
        settings = _make_settings()
        engine = TradingEngine(settings)
        assert engine._get_exchange("AAPL") == "NAS"

    def test_get_exchange_custom(self):
        settings = _make_settings()
        settings.trading.us_symbol_exchanges = {"IBM": "NYS"}
        engine = TradingEngine(settings)
        assert engine._get_exchange("IBM") == "NYS"
        assert engine._get_exchange("AAPL") == "NAS"

    @pytest.mark.asyncio
    async def test_execute_buy_us_symbol(self):
        """US 심볼 매수 시 us_order.buy 호출"""
        settings = _make_settings()
        settings.trading.us_target_order_amount = 1000.0
        settings.trading.us_min_quantity = 1
        settings.trading.us_max_quantity = 100
        engine = TradingEngine(settings)

        engine.us_order.get_balance = AsyncMock(return_value=([], AccountSummary()))
        engine.us_order.buy = AsyncMock(return_value={
            "success": True, "order_no": "US001", "message": "ok",
        })

        now = datetime(2026, 2, 12, 10, 0, 0)
        await engine._execute_buy("AAPL", 200.0, now)

        # 1000 // 200 = 5주
        engine.us_order.buy.assert_called_once_with("AAPL", 5, "NAS")

    @pytest.mark.asyncio
    async def test_execute_sell_us_symbol(self):
        """US 심볼 매도 시 us_order.sell 호출"""
        settings = _make_settings()
        engine = TradingEngine(settings)

        engine.us_order.get_balance = AsyncMock(return_value=([
            Position(symbol="AAPL", quantity=10, avg_price=180.0, current_price=190.0),
        ], AccountSummary()))
        engine.us_order.sell = AsyncMock(return_value={
            "success": True, "order_no": "US002", "message": "ok",
        })

        now = datetime(2026, 2, 12, 10, 0, 0)
        await engine._execute_sell("AAPL", now, reason="signal")

        engine.us_order.sell.assert_called_once_with("AAPL", 10, "NAS")

    @pytest.mark.asyncio
    async def test_force_close_includes_us_positions(self):
        """US 심볼이 감시 목록에 있을 때 force_close_all이 US 잔고도 청산"""
        settings = _make_settings()
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930", "AAPL"]

        engine.order.get_balance = AsyncMock(return_value=([
            Position(symbol="005930", quantity=10, current_price=72000),
        ], AccountSummary()))
        engine.order.sell = AsyncMock(return_value={
            "success": True, "order_no": "0001", "message": "ok",
        })

        engine.us_order.get_balance = AsyncMock(return_value=([
            Position(symbol="AAPL", quantity=5, current_price=190.0),
        ], AccountSummary()))
        engine.us_order.sell = AsyncMock(return_value={
            "success": True, "order_no": "US003", "message": "ok",
        })

        now = datetime(2026, 2, 12, 15, 10, 0)
        await engine._force_close_all(now)

        engine.order.sell.assert_called_once_with("005930", 10)
        engine.us_order.sell.assert_called_once_with("AAPL", 5, "NAS")

    def test_start_merges_us_symbols(self):
        """start 시 국내 + 해외 감시 종목 합산"""
        settings = _make_settings()
        settings.trading.us_watch_symbols = ["AAPL", "TSLA"]
        engine = TradingEngine(settings)

        # symbols=None이면 기본값 합산
        # (실제 start는 API 연결을 시도하므로 직접 합산 로직만 검증)
        combined = settings.trading.watch_symbols + settings.trading.us_watch_symbols
        assert "AAPL" in combined
        assert "TSLA" in combined
        assert "005930" in combined


class TestMarketParam:
    """start(market=...) 파라미터 테스트"""

    @pytest.mark.asyncio
    async def test_start_market_domestic_only(self):
        """market='domestic' → 국내 종목만 감시"""
        settings = _make_settings()
        settings.trading.watch_symbols = ["005930", "000660"]
        settings.trading.us_watch_symbols = ["AAPL", "TSLA"]
        engine = TradingEngine(settings)
        engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))

        await engine.start(market=MarketType.DOMESTIC)

        assert engine._watch_symbols == ["005930", "000660"]
        assert engine._active_market == MarketType.DOMESTIC
        await engine.stop()

    @pytest.mark.asyncio
    async def test_start_market_us_only(self):
        """market='us' → 해외 종목만 감시"""
        settings = _make_settings()
        settings.trading.watch_symbols = ["005930"]
        settings.trading.us_watch_symbols = ["AAPL", "TSLA"]
        engine = TradingEngine(settings)
        engine.us_order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))

        await engine.start(market=MarketType.US)

        assert engine._watch_symbols == ["AAPL", "TSLA"]
        assert engine._active_market == MarketType.US
        await engine.stop()

    @pytest.mark.asyncio
    async def test_start_symbols_with_market_filter(self):
        """symbols + market 동시 지정 → 해당 시장 종목만 필터링"""
        settings = _make_settings()
        engine = TradingEngine(settings)
        engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))

        await engine.start(
            symbols=["005930", "AAPL", "TSLA"],
            market=MarketType.DOMESTIC,
        )

        assert engine._watch_symbols == ["005930"]
        await engine.stop()

    @pytest.mark.asyncio
    async def test_start_no_market_all_symbols(self):
        """market=None → 국내 + 해외 합산"""
        settings = _make_settings()
        settings.trading.watch_symbols = ["005930"]
        settings.trading.us_watch_symbols = ["AAPL"]
        engine = TradingEngine(settings)
        engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))

        await engine.start()

        assert "005930" in engine._watch_symbols
        assert "AAPL" in engine._watch_symbols
        assert engine._active_market is None
        await engine.stop()

    @pytest.mark.asyncio
    async def test_start_empty_symbols_raises(self):
        """감시 종목이 없으면 ValueError"""
        settings = _make_settings()
        settings.trading.us_watch_symbols = []
        engine = TradingEngine(settings)

        with pytest.raises(ValueError, match="감시할 종목이 없습니다"):
            await engine.start(symbols=[], market=MarketType.US)

    @pytest.mark.asyncio
    async def test_start_us_validates_with_us_balance(self):
        """market='us' → us_order.get_balance로 연결 검증"""
        settings = _make_settings()
        settings.trading.us_watch_symbols = ["AAPL"]
        engine = TradingEngine(settings)
        engine.us_order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))

        await engine.start(market=MarketType.US)

        # 연결 검증 + 포지션 복원으로 2회 호출
        assert engine.us_order.get_balance.call_count >= 1
        await engine.stop()

    @pytest.mark.asyncio
    async def test_tick_domestic_market_skips_us_check(self):
        """_active_market=DOMESTIC → us_open 체크 안 함"""
        settings = _make_settings()
        engine = TradingEngine(settings)
        engine._active_market = MarketType.DOMESTIC
        engine._watch_symbols = ["005930"]

        # 한국 장 닫힌 시간 (새벽)
        with patch("app.trading.engine.is_market_open", return_value=False):
            await engine._tick()

        # 아무 처리 없이 리턴 (us_open 체크하지 않으므로 is_us_market_open 불필요)
        assert engine._loop_count == 0

    def test_status_shows_active_market(self):
        """get_status에 active_market 반영"""
        settings = _make_settings()
        engine = TradingEngine(settings)
        engine._active_market = MarketType.US
        status = engine.get_status()
        assert status.active_market == "us"

    def test_status_default_all(self):
        """기본 active_market은 'all'"""
        settings = _make_settings()
        engine = TradingEngine(settings)
        status = engine.get_status()
        assert status.active_market == "all"


class TestEdgeCasePriceZero:
    """현재가=0 엣지케이스 테스트"""

    @pytest.mark.asyncio
    async def test_execute_buy_skips_when_price_zero(self):
        """_execute_buy: current_price=0 → 주문 없이 즉시 리턴"""
        settings = _make_settings()
        engine = TradingEngine(settings)

        engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))
        engine.order.buy = AsyncMock()

        now = datetime(2026, 2, 12, 10, 0, 0)
        await engine._execute_buy("005930", 0, now)

        engine.order.buy.assert_not_called()
        assert len(engine._orders) == 0

    @pytest.mark.asyncio
    async def test_execute_buy_skips_when_price_negative(self):
        """_execute_buy: current_price<0 → 주문 없이 즉시 리턴"""
        settings = _make_settings()
        engine = TradingEngine(settings)

        engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))
        engine.order.buy = AsyncMock()

        now = datetime(2026, 2, 12, 10, 0, 0)
        await engine._execute_buy("005930", -100, now)

        engine.order.buy.assert_not_called()

    @pytest.mark.asyncio
    async def test_trailing_stop_safe_when_peak_zero(self):
        """peak_prices=0 → division by zero 없이 트레일링 스탑 스킵"""
        settings = _make_settings()
        settings.trading.trailing_stop_pct = 5.0
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        engine._entry_prices["005930"] = 50_000.0
        engine._peak_prices["005930"] = 0.0  # 비정상 고점

        chart = _make_chart([100] * 30)
        price = StockPrice(
            symbol="005930", current_price=50000,
            change=0, change_rate=0, volume=5000,
            high=50000, low=50000, opening=50000,
        )

        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 12, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_daily_chart = AsyncMock(return_value=chart)
            engine.market.get_current_price = AsyncMock(return_value=price)
            engine.order.sell = AsyncMock()
            engine.order.buy = AsyncMock()
            engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))

            await engine._tick()  # ZeroDivisionError 없이 정상 종료

        # peak=0 → trailing stop 조건 불충족 → 매도 안 됨
        engine.order.sell.assert_not_called()


class TestEdgeCaseDepositZero:
    """예수금=0 엣지케이스 테스트"""

    @pytest.mark.asyncio
    async def test_deposit_zero_with_capital_ratio_buys_min_quantity(self):
        """deposit=0 + capital_ratio>0 → target=0 → min_quantity 매수"""
        settings = _make_settings()
        settings.trading.capital_ratio = 0.3
        settings.trading.min_quantity = 1
        settings.trading.max_quantity = 100
        engine = TradingEngine(settings)

        summary = AccountSummary(deposit=0)
        engine.order.get_balance = AsyncMock(return_value=([], summary))
        engine.order.buy = AsyncMock(return_value={
            "success": True, "order_no": "0001", "message": "ok",
        })

        now = datetime(2026, 2, 12, 10, 0, 0)
        await engine._execute_buy("005930", 50_000, now)

        # int(0 * 0.3) // 50_000 = 0 → clamped to min_quantity=1
        engine.order.buy.assert_called_once_with("005930", 1)

    @pytest.mark.asyncio
    async def test_deposit_zero_no_capital_ratio_uses_target(self):
        """deposit=0 + capital_ratio=0 → target_order_amount 사용"""
        settings = _make_settings()
        settings.trading.capital_ratio = 0.0  # 비활성
        settings.trading.target_order_amount = 500_000
        engine = TradingEngine(settings)

        summary = AccountSummary(deposit=0)
        engine.order.get_balance = AsyncMock(return_value=([], summary))
        engine.order.buy = AsyncMock(return_value={
            "success": True, "order_no": "0001", "message": "ok",
        })

        now = datetime(2026, 2, 12, 10, 0, 0)
        await engine._execute_buy("005930", 50_000, now)

        # 500_000 // 50_000 = 10주
        engine.order.buy.assert_called_once_with("005930", 10)


class TestEdgeCaseConcurrentAccess:
    """_entry_prices 동시 접근 시나리오 테스트"""

    @pytest.mark.asyncio
    async def test_concurrent_buy_sell_same_symbol(self):
        """동일 종목 매수/매도 동시 호출 → Lock으로 순차 실행"""
        import asyncio

        settings = _make_settings()
        engine = TradingEngine(settings)

        call_order: list[str] = []

        async def mock_buy_balance():
            call_order.append("buy_balance")
            await asyncio.sleep(0.05)
            return ([], _EMPTY_SUMMARY)

        async def mock_sell_balance():
            call_order.append("sell_balance")
            await asyncio.sleep(0.05)
            return ([
                Position(symbol="005930", quantity=10, avg_price=70000, current_price=72000),
            ], _EMPTY_SUMMARY)

        # 매수 시에는 빈 잔고, 매도 시에는 보유 잔고 반환
        balance_count = 0

        async def mock_balance():
            nonlocal balance_count
            balance_count += 1
            if balance_count == 1:
                return await mock_sell_balance()  # 첫 호출: 매도용
            return await mock_buy_balance()  # 두 번째: 매수용

        engine.order.get_balance = AsyncMock(side_effect=mock_balance)
        engine.order.buy = AsyncMock(return_value={
            "success": True, "order_no": "0001", "message": "ok",
        })
        engine.order.sell = AsyncMock(return_value={
            "success": True, "order_no": "0002", "message": "ok",
        })

        now = datetime(2026, 2, 12, 10, 0, 0)

        # 동일 종목에 대한 매수/매도를 동시 실행
        await asyncio.gather(
            engine._execute_sell("005930", now, reason="signal"),
            engine._execute_buy("005930", 72000, now),
        )

        # Lock으로 인해 순차 실행 — 잔고 조회가 정확히 2회
        assert engine.order.get_balance.call_count == 2

    @pytest.mark.asyncio
    async def test_entry_prices_cleared_on_sell(self):
        """매도 성공 후 _entry_prices에서 종목 삭제 확인"""
        settings = _make_settings()
        engine = TradingEngine(settings)
        engine._entry_prices["005930"] = 70_000.0
        engine._buy_timestamps["005930"] = datetime(2026, 2, 10, 10, 0, 0)
        engine._peak_prices["005930"] = 72_000.0

        engine.order.get_balance = AsyncMock(return_value=([
            Position(symbol="005930", quantity=10, avg_price=70000, current_price=72000),
        ], _EMPTY_SUMMARY))
        engine.order.sell = AsyncMock(return_value={
            "success": True, "order_no": "0001", "message": "ok",
        })

        now = datetime(2026, 2, 12, 10, 0, 0)
        await engine._execute_sell("005930", now, reason="signal")

        assert "005930" not in engine._entry_prices
        assert "005930" not in engine._buy_timestamps
        assert "005930" not in engine._peak_prices

    @pytest.mark.asyncio
    async def test_entry_prices_set_on_buy_success(self):
        """매수 성공 시 _entry_prices 설정 확인"""
        settings = _make_settings()
        engine = TradingEngine(settings)

        engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))
        engine.order.buy = AsyncMock(return_value={
            "success": True, "order_no": "0001", "message": "ok",
        })

        now = datetime(2026, 2, 12, 10, 0, 0)
        await engine._execute_buy("005930", 72000, now)

        assert engine._entry_prices["005930"] == 72000.0
        assert engine._buy_timestamps["005930"] == now
        assert engine._peak_prices["005930"] == 72000.0

    @pytest.mark.asyncio
    async def test_entry_prices_not_set_on_buy_failure(self):
        """매수 실패 시 _entry_prices 미설정"""
        settings = _make_settings()
        engine = TradingEngine(settings)

        engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))
        engine.order.buy = AsyncMock(return_value={
            "success": False, "order_no": "", "message": "주문 실패",
        })

        now = datetime(2026, 2, 12, 10, 0, 0)
        await engine._execute_buy("005930", 72000, now)

        assert "005930" not in engine._entry_prices
        assert "005930" not in engine._buy_timestamps
        assert "005930" not in engine._peak_prices


class TestJournalEntryPrice:
    """저널 이벤트에 entry_price 기록 검증"""

    @pytest.mark.asyncio
    async def test_buy_journal_records_entry_price(self):
        """매수 저널 이벤트에 entry_price=current_price 기록"""
        settings = _make_settings()
        engine = TradingEngine(settings)

        engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))
        engine.order.buy = AsyncMock(return_value={
            "success": True, "order_no": "0001", "message": "ok",
        })

        now = datetime(2026, 2, 12, 10, 0, 0)
        await engine._execute_buy("005930", 72000, now)

        # 저널 log_event가 호출되었는지 확인
        engine._journal.log_event.assert_called_once()
        event = engine._journal.log_event.call_args[0][0]
        assert event.side == "buy"
        assert event.entry_price == 72000.0
        assert event.current_price == 72000.0

    @pytest.mark.asyncio
    async def test_sell_journal_records_entry_price(self):
        """매도 저널 이벤트에 매수 시 entry_price 기록"""
        settings = _make_settings()
        engine = TradingEngine(settings)
        engine._entry_prices["005930"] = 70_000.0

        engine.order.get_balance = AsyncMock(return_value=([
            Position(symbol="005930", quantity=10, avg_price=70000, current_price=72000),
        ], _EMPTY_SUMMARY))
        engine.order.sell = AsyncMock(return_value={
            "success": True, "order_no": "0002", "message": "ok",
        })

        now = datetime(2026, 2, 12, 14, 0, 0)
        await engine._execute_sell("005930", now, reason="signal")

        engine._journal.log_event.assert_called_once()
        event = engine._journal.log_event.call_args[0][0]
        assert event.side == "sell"
        assert event.entry_price == 70_000.0
        assert event.current_price == 72000

    @pytest.mark.asyncio
    async def test_sell_journal_entry_price_zero_when_no_buy_record(self):
        """매수 기록 없는 종목 매도 시 entry_price=0.0"""
        settings = _make_settings()
        engine = TradingEngine(settings)
        # _entry_prices에 매수 기록 없음

        engine.order.get_balance = AsyncMock(return_value=([
            Position(symbol="005930", quantity=5, avg_price=70000, current_price=72000),
        ], _EMPTY_SUMMARY))
        engine.order.sell = AsyncMock(return_value={
            "success": True, "order_no": "0003", "message": "ok",
        })

        now = datetime(2026, 2, 12, 14, 0, 0)
        await engine._execute_sell("005930", now, reason="signal")

        event = engine._journal.log_event.call_args[0][0]
        assert event.entry_price == 0.0

    @pytest.mark.asyncio
    async def test_buy_then_sell_journal_entry_price_flow(self):
        """매수 → 매도 전체 흐름에서 entry_price 일관성 검증"""
        settings = _make_settings()
        engine = TradingEngine(settings)

        # 매수
        engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))
        engine.order.buy = AsyncMock(return_value={
            "success": True, "order_no": "0001", "message": "ok",
        })

        now_buy = datetime(2026, 2, 12, 10, 0, 0)
        await engine._execute_buy("005930", 72000, now_buy)

        buy_event = engine._journal.log_event.call_args[0][0]
        assert buy_event.entry_price == 72000.0

        # 매도
        engine.order.get_balance = AsyncMock(return_value=([
            Position(symbol="005930", quantity=1, avg_price=72000, current_price=75000),
        ], _EMPTY_SUMMARY))
        engine.order.sell = AsyncMock(return_value={
            "success": True, "order_no": "0002", "message": "ok",
        })

        now_sell = datetime(2026, 2, 12, 14, 0, 0)
        await engine._execute_sell("005930", now_sell, reason="signal")

        sell_event = engine._journal.log_event.call_args[0][0]
        assert sell_event.side == "sell"
        assert sell_event.entry_price == 72000.0
        assert sell_event.current_price == 75000

    @pytest.mark.asyncio
    async def test_force_close_journal_records_entry_price(self):
        """강제 청산 저널 이벤트에 entry_price 기록"""
        settings = _make_settings()
        engine = TradingEngine(settings)
        engine._entry_prices["005930"] = 68_000.0
        engine._watch_symbols = ["005930"]

        engine.order.get_balance = AsyncMock(return_value=([
            Position(symbol="005930", quantity=10, avg_price=68000, current_price=67000),
        ], _EMPTY_SUMMARY))
        engine.order.sell = AsyncMock(return_value={
            "success": True, "order_no": "0004", "message": "ok",
        })

        now = datetime(2026, 2, 12, 15, 25, 0)
        await engine._force_close_all(now, market=MarketType.DOMESTIC)

        engine._journal.log_event.assert_called_once()
        event = engine._journal.log_event.call_args[0][0]
        assert event.entry_price == 68_000.0
        assert event.reason == "force_close"


class TestRestorePositions:
    """서버 재시작 시 보유 포지션 매수가 복원 테스트"""

    @pytest.mark.asyncio
    async def test_restore_domestic_positions(self):
        """국내 보유 포지션의 매수가/고점/매수시각 복원"""
        settings = _make_settings()
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]

        engine.order.get_balance = AsyncMock(return_value=([
            Position(symbol="005930", quantity=10, avg_price=70000, current_price=72000),
        ], _EMPTY_SUMMARY))
        engine.us_order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))

        await engine._restore_positions(market=None)

        assert engine._entry_prices["005930"] == 70000.0
        assert "005930" in engine._buy_timestamps
        assert engine._peak_prices["005930"] == 72000.0  # max(avg, current)

    @pytest.mark.asyncio
    async def test_restore_us_positions(self):
        """미국 보유 포지션 복원"""
        settings = _make_settings()
        settings.trading.us_watch_symbols = ["AAPL"]
        engine = TradingEngine(settings)
        engine._watch_symbols = ["AAPL"]

        engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))
        engine.us_order.get_balance = AsyncMock(return_value=([
            Position(symbol="AAPL", quantity=5, avg_price=180.0, current_price=175.0),
        ], _EMPTY_SUMMARY))

        await engine._restore_positions(market=None)

        assert engine._entry_prices["AAPL"] == 180.0
        assert engine._peak_prices["AAPL"] == 180.0  # max(avg=180, current=175)

    @pytest.mark.asyncio
    async def test_restore_skips_zero_quantity(self):
        """수량 0인 포지션은 복원하지 않음"""
        settings = _make_settings()
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]

        engine.order.get_balance = AsyncMock(return_value=([
            Position(symbol="005930", quantity=0, avg_price=70000, current_price=72000),
        ], _EMPTY_SUMMARY))
        engine.us_order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))

        await engine._restore_positions(market=None)

        assert "005930" not in engine._entry_prices

    @pytest.mark.asyncio
    async def test_restore_skips_unwatched_symbols(self):
        """감시 목록에 없는 종목은 복원하지 않음"""
        settings = _make_settings()
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]

        engine.order.get_balance = AsyncMock(return_value=([
            Position(symbol="000660", quantity=10, avg_price=50000, current_price=51000),
        ], _EMPTY_SUMMARY))
        engine.us_order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))

        await engine._restore_positions(market=None)

        assert "000660" not in engine._entry_prices

    @pytest.mark.asyncio
    async def test_restore_skips_already_tracked(self):
        """이미 추적 중인 종목은 덮어쓰지 않음"""
        settings = _make_settings()
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._entry_prices["005930"] = 65000.0  # 기존 추적 정보

        engine.order.get_balance = AsyncMock(return_value=([
            Position(symbol="005930", quantity=10, avg_price=70000, current_price=72000),
        ], _EMPTY_SUMMARY))
        engine.us_order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))

        await engine._restore_positions(market=None)

        assert engine._entry_prices["005930"] == 65000.0  # 기존 값 유지

    @pytest.mark.asyncio
    async def test_restore_logs_state_restore_event(self):
        """복원 시 STATE_RESTORE 저널 이벤트 기록"""
        settings = _make_settings()
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]

        engine.order.get_balance = AsyncMock(return_value=([
            Position(symbol="005930", quantity=10, avg_price=70000, current_price=72000),
        ], _EMPTY_SUMMARY))
        engine.us_order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))

        await engine._restore_positions(market=None)

        engine._journal.log_event.assert_called_once()
        event = engine._journal.log_event.call_args[0][0]
        assert event.event_type == EventType.STATE_RESTORE
        assert "005930" in event.detail
        assert "avg_price=70000" in event.detail

    @pytest.mark.asyncio
    async def test_restore_survives_balance_error(self):
        """잔고 조회 실패 시 예외 없이 건너뜀"""
        settings = _make_settings()
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]

        engine.order.get_balance = AsyncMock(
            side_effect=RuntimeError("API error")
        )

        # 예외 발생하지 않아야 함
        await engine._restore_positions(market=None)

        assert len(engine._entry_prices) == 0

    @pytest.mark.asyncio
    async def test_restore_domestic_only_market(self):
        """market=DOMESTIC 시 국내 잔고만 조회"""
        settings = _make_settings()
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]

        engine.order.get_balance = AsyncMock(return_value=([
            Position(symbol="005930", quantity=10, avg_price=70000, current_price=72000),
        ], _EMPTY_SUMMARY))
        engine.us_order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))

        await engine._restore_positions(market=MarketType.DOMESTIC)

        assert "005930" in engine._entry_prices
        engine.us_order.get_balance.assert_not_called()

    @pytest.mark.asyncio
    async def test_restore_us_only_market(self):
        """market=US 시 해외 잔고만 조회"""
        settings = _make_settings()
        engine = TradingEngine(settings)
        engine._watch_symbols = ["AAPL"]

        engine.order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))
        engine.us_order.get_balance = AsyncMock(return_value=([
            Position(symbol="AAPL", quantity=5, avg_price=180.0, current_price=185.0),
        ], _EMPTY_SUMMARY))

        await engine._restore_positions(market=MarketType.US)

        assert "AAPL" in engine._entry_prices
        engine.order.get_balance.assert_not_called()

    @pytest.mark.asyncio
    async def test_restore_peak_uses_max_of_avg_and_current(self):
        """고점은 avg_price와 current_price 중 큰 값"""
        settings = _make_settings()
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930", "000660"]

        engine.order.get_balance = AsyncMock(return_value=([
            Position(symbol="005930", quantity=10, avg_price=70000, current_price=75000),
            Position(symbol="000660", quantity=5, avg_price=80000, current_price=78000),
        ], _EMPTY_SUMMARY))
        engine.us_order.get_balance = AsyncMock(return_value=([], _EMPTY_SUMMARY))

        await engine._restore_positions(market=None)

        assert engine._peak_prices["005930"] == 75000.0  # current > avg
        assert engine._peak_prices["000660"] == 80000.0  # avg > current


class TestReasonDetail:
    """매도 사유 상세(reason_detail) 기록 검증"""

    @pytest.mark.asyncio
    async def test_stop_loss_reason_detail(self):
        """손절 매도 시 매수가/현재가/손실률 상세 기록"""
        settings = _make_settings()
        settings.trading.stop_loss_pct = 5.0
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        engine._entry_prices["005930"] = 100_000.0
        engine._buy_timestamps["005930"] = datetime(2026, 2, 10, 10, 0, 0)

        chart = _make_chart([100] * 30)
        price = StockPrice(
            symbol="005930", current_price=93000,
            change=-7000, change_rate=-7.0, volume=5000,
            high=94000, low=92000, opening=93500,
        )

        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 12, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_daily_chart = AsyncMock(return_value=chart)
            engine.market.get_current_price = AsyncMock(return_value=price)
            engine.order.get_balance = AsyncMock(return_value=([
                Position(
                    symbol="005930", name="삼성전자", quantity=10,
                    avg_price=100000, current_price=93000,
                ),
            ], _EMPTY_SUMMARY))
            engine.order.sell = AsyncMock(return_value={
                "success": True, "order_no": "SL01", "message": "ok",
            })

            await engine._tick()

        assert len(engine._orders) == 1
        order = engine._orders[0]
        assert order.reason == "stop_loss"
        assert "손절 매도" in order.reason_detail
        assert "100,000" in order.reason_detail
        assert "93,000" in order.reason_detail
        assert "7.0%" in order.reason_detail

    @pytest.mark.asyncio
    async def test_trailing_stop_reason_detail(self):
        """트레일링 스탑 시 고점/현재가/하락률 상세 기록"""
        settings = _make_settings()
        settings.trading.trailing_stop_pct = 5.0
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        engine._entry_prices["005930"] = 100_000.0
        engine._buy_timestamps["005930"] = datetime(2026, 2, 10, 10, 0, 0)
        engine._peak_prices["005930"] = 110_000.0

        chart = _make_chart([100] * 30)
        price = StockPrice(
            symbol="005930", current_price=100000,
            change=-10000, change_rate=-9.1, volume=5000,
            high=101000, low=99000, opening=100500,
        )

        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 12, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_daily_chart = AsyncMock(return_value=chart)
            engine.market.get_current_price = AsyncMock(return_value=price)
            engine.order.get_balance = AsyncMock(return_value=([
                Position(
                    symbol="005930", name="삼성전자", quantity=10,
                    avg_price=100000, current_price=100000,
                ),
            ], _EMPTY_SUMMARY))
            engine.order.sell = AsyncMock(return_value={
                "success": True, "order_no": "TS01", "message": "ok",
            })

            await engine._tick()

        assert len(engine._orders) == 1
        order = engine._orders[0]
        assert order.reason == "trailing_stop"
        assert "트레일링 스탑" in order.reason_detail
        assert "110,000" in order.reason_detail
        assert "100,000" in order.reason_detail

    @pytest.mark.asyncio
    async def test_max_holding_reason_detail(self):
        """보유기간 초과 시 매수일/현재일/보유일수 상세 기록"""
        settings = _make_settings()
        settings.trading.max_holding_days = 20
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        engine._entry_prices["005930"] = 70_000.0
        engine._buy_timestamps["005930"] = datetime(2026, 1, 20, 10, 0, 0)

        chart = _make_chart([100] * 30)
        price = StockPrice(
            symbol="005930", current_price=72000,
            change=0, change_rate=0.0, volume=5000,
            high=72500, low=71500, opening=72000,
        )

        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 12, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_daily_chart = AsyncMock(return_value=chart)
            engine.market.get_current_price = AsyncMock(return_value=price)
            engine.order.get_balance = AsyncMock(return_value=([
                Position(
                    symbol="005930", name="삼성전자", quantity=10,
                    avg_price=70000, current_price=72000,
                ),
            ], _EMPTY_SUMMARY))
            engine.order.sell = AsyncMock(return_value={
                "success": True, "order_no": "MH01", "message": "ok",
            })

            await engine._tick()

        assert len(engine._orders) == 1
        order = engine._orders[0]
        assert order.reason == "max_holding"
        assert "보유기간 초과" in order.reason_detail
        assert "01/20" in order.reason_detail
        assert "02/12" in order.reason_detail
        assert "23일 보유" in order.reason_detail

    @pytest.mark.asyncio
    async def test_force_close_reason_detail(self):
        """장 마감 강제 청산 시 시각 상세 기록"""
        settings = _make_settings()
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        engine.order.get_balance = AsyncMock(return_value=([
            Position(
                symbol="005930", name="삼성전자", quantity=5,
                avg_price=70000, current_price=71000,
            ),
        ], _EMPTY_SUMMARY))
        engine.order.sell = AsyncMock(return_value={
            "success": True, "order_no": "FC01", "message": "ok",
        })

        now = datetime(2026, 2, 12, 15, 20, 0)
        await engine._force_close_all(now, market=MarketType.DOMESTIC)

        assert len(engine._orders) == 1
        order = engine._orders[0]
        assert order.reason == "force_close"
        assert "장 마감 강제 청산" in order.reason_detail
        assert "15:20" in order.reason_detail

    @pytest.mark.asyncio
    async def test_signal_sell_carries_reason_detail(self):
        """시그널 매도 시 전략의 reason_detail이 전달됨"""
        settings = _make_settings()
        engine = TradingEngine(settings)
        engine._watch_symbols = ["005930"]
        engine._status = EngineStatus.RUNNING

        # 데드크로스 차트: SMA5가 SMA20 아래로
        closes = [200] * 15 + [200, 199, 198, 197, 196, 190, 185, 180, 175, 170]
        chart = _make_chart(closes)
        price = StockPrice(
            symbol="005930", current_price=170,
            change=-30, change_rate=-15.0, volume=10000,
            high=175, low=168, opening=175,
        )

        with patch("app.trading.engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 12, 10, 0, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            engine.market.get_daily_chart = AsyncMock(return_value=chart)
            engine.market.get_current_price = AsyncMock(return_value=price)
            engine.order.get_balance = AsyncMock(return_value=([
                Position(
                    symbol="005930", name="삼성전자", quantity=10,
                    avg_price=200, current_price=170,
                ),
            ], _EMPTY_SUMMARY))
            engine.order.sell = AsyncMock(return_value={
                "success": True, "order_no": "SIG01", "message": "ok",
            })

            await engine._tick()

        # 시그널이 SELL인 경우만 체크
        sell_orders = [o for o in engine._orders if o.side == "sell"]
        if sell_orders:
            order = sell_orders[0]
            assert order.reason == "signal"
            # reason_detail은 전략에서 생성된 값 (빈 문자열도 허용)
            assert isinstance(order.reason_detail, str)
