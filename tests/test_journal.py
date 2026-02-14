"""매매 저널 단위 테스트"""

from datetime import date, datetime

import pytest

from app.models import EventType, TradeEvent
from app.trading.journal import TradingJournal


@pytest.fixture
def journal(tmp_path):
    """tmp_path를 사용하는 임시 저널"""
    log_dir = tmp_path / "logs"
    return TradingJournal(log_dir=str(log_dir))


def _make_event(
    event_type: str = "signal",
    symbol: str = "005930",
    ts: datetime | None = None,
    **kwargs,
) -> TradeEvent:
    return TradeEvent(
        event_type=event_type,
        timestamp=ts or datetime(2026, 2, 14, 10, 0, 0),
        symbol=symbol,
        **kwargs,
    )


class TestJournalReadWrite:
    """JSONL 쓰기/읽기 라운드트립"""

    def test_write_and_read_single_event(self, journal):
        event = _make_event(signal="BUY", current_price=72000)
        journal.log_event(event)

        events = journal.read_events(date(2026, 2, 14))
        assert len(events) == 1
        assert events[0].event_type == "signal"
        assert events[0].symbol == "005930"
        assert events[0].signal == "BUY"
        assert events[0].current_price == 72000

    def test_write_multiple_events(self, journal):
        for i in range(5):
            journal.log_event(_make_event(
                ts=datetime(2026, 2, 14, 10, i, 0),
                signal="BUY" if i % 2 == 0 else "SELL",
            ))

        events = journal.read_events(date(2026, 2, 14))
        assert len(events) == 5

    def test_different_dates_separated(self, journal):
        journal.log_event(_make_event(ts=datetime(2026, 2, 14, 10, 0, 0)))
        journal.log_event(_make_event(ts=datetime(2026, 2, 15, 10, 0, 0)))

        assert len(journal.read_events(date(2026, 2, 14))) == 1
        assert len(journal.read_events(date(2026, 2, 15))) == 1

    def test_empty_date_returns_empty_list(self, journal):
        events = journal.read_events(date(2026, 1, 1))
        assert events == []


class TestJournalDates:
    """날짜 목록 조회"""

    def test_list_dates(self, journal):
        journal.log_event(_make_event(ts=datetime(2026, 2, 14, 10, 0, 0)))
        journal.log_event(_make_event(ts=datetime(2026, 2, 12, 10, 0, 0)))
        journal.log_event(_make_event(ts=datetime(2026, 2, 13, 10, 0, 0)))

        dates = journal.list_dates()
        assert dates == ["2026-02-14", "2026-02-13", "2026-02-12"]

    def test_list_dates_empty(self, journal):
        assert journal.list_dates() == []


class TestJournalReport:
    """리포트 생성"""

    def test_generate_report_creates_html(self, journal):
        journal.log_event(_make_event(event_type="engine_start"))
        journal.log_event(_make_event(
            event_type="order", side="buy", quantity=10,
            current_price=72000, success=True, reason="signal",
        ))
        journal.log_event(_make_event(
            event_type="order", side="sell", quantity=10,
            current_price=73000, success=True, reason="signal",
            entry_price=72000.0,
        ))
        journal.log_event(_make_event(event_type="engine_stop"))

        path = journal.generate_daily_report(date(2026, 2, 14))
        assert path.endswith(".html")
        with open(path, encoding="utf-8") as f:
            html = f.read()
        assert "2026-02-14" in html
        assert "매매 저널" in html

    def test_generate_empty_report(self, journal):
        """이벤트 없는 날짜도 리포트 생성 가능"""
        path = journal.generate_daily_report(date(2026, 1, 1))
        assert path.endswith(".html")
        with open(path, encoding="utf-8") as f:
            html = f.read()
        assert "주문 없음" in html


class TestReasonField:
    """reason 필드 직렬화"""

    @pytest.mark.parametrize("reason", [
        "signal", "stop_loss", "trailing_stop", "max_holding", "force_close",
    ])
    def test_reason_roundtrip(self, journal, reason):
        event = _make_event(
            event_type="order", side="sell", quantity=10,
            reason=reason, current_price=72000,
        )
        journal.log_event(event)

        events = journal.read_events(date(2026, 2, 14))
        assert len(events) == 1
        assert events[0].reason == reason


class TestJournalResilience:
    """JSONL 읽기 내구성 테스트"""

    def test_corrupted_line_skipped(self, journal):
        """손상된 줄 포함 JSONL → 정상 줄만 반환"""
        journal.log_event(_make_event(signal="BUY", current_price=72000))

        # 손상된 줄 직접 추가
        path = journal._log_path(date(2026, 2, 14))
        with open(path, "a", encoding="utf-8") as f:
            f.write("CORRUPTED JSON LINE\n")

        journal.log_event(_make_event(
            signal="SELL", current_price=73000,
            ts=datetime(2026, 2, 14, 10, 1, 0),
        ))

        events = journal.read_events(date(2026, 2, 14))
        assert len(events) == 2  # 3줄 중 손상된 1줄 제외
        assert events[0].signal == "BUY"
        assert events[1].signal == "SELL"

    def test_multiple_corrupted_lines(self, journal):
        """여러 손상된 줄이 있어도 정상 줄 반환"""
        journal.log_event(_make_event(signal="BUY"))

        path = journal._log_path(date(2026, 2, 14))
        with open(path, "a", encoding="utf-8") as f:
            f.write("bad line 1\n")
            f.write("{invalid json}\n")
            f.write("\n")  # 빈 줄

        events = journal.read_events(date(2026, 2, 14))
        assert len(events) == 1


class TestFactoryMethods:
    """TradeEvent 팩토리 메서드 테스트"""

    def test_engine_event(self):
        event = TradeEvent.engine_event(EventType.ENGINE_START, "symbols=['005930']")
        assert event.event_type == EventType.ENGINE_START
        assert event.detail == "symbols=['005930']"
        assert event.symbol == ""

    def test_engine_event_stop(self):
        event = TradeEvent.engine_event(EventType.ENGINE_STOP)
        assert event.event_type == EventType.ENGINE_STOP
        assert event.detail == ""

    def test_from_order(self):
        result = {"order_no": "0001", "success": True, "message": "ok"}
        event = TradeEvent.from_order(
            "005930", "buy", 10, result, "signal", 72000,
        )
        assert event.event_type == EventType.ORDER
        assert event.symbol == "005930"
        assert event.side == "buy"
        assert event.quantity == 10
        assert event.order_no == "0001"
        assert event.success is True
        assert event.reason == "signal"
        assert event.current_price == 72000

    def test_from_order_force_close(self):
        result = {"order_no": "0002", "success": True}
        event = TradeEvent.from_order(
            "005930", "sell", 5, result, "force_close", 73000,
            entry_price=72000.0, event_type=EventType.FORCE_CLOSE,
        )
        assert event.event_type == EventType.FORCE_CLOSE
        assert event.entry_price == 72000.0

    def test_from_signal(self):
        from app.models import SignalType, TradingSignal
        signal = TradingSignal(
            symbol="005930",
            signal=SignalType.BUY,
            current_price=72000,
            timestamp=datetime(2026, 2, 14, 10, 0, 0),
            short_ma=100.0,
            long_ma=95.0,
            rsi=45.0,
            volume_confirmed=True,
        )
        event = TradeEvent.from_signal(signal)
        assert event.event_type == EventType.SIGNAL
        assert event.symbol == "005930"
        assert event.signal == "BUY"
        assert event.current_price == 72000
        assert event.short_ma == 100.0
        assert event.rsi == 45.0
        assert event.volume_confirmed is True

    def test_factory_roundtrip(self, journal):
        """팩토리 메서드로 생성 → JSONL 저장 → 읽기 라운드트립"""
        event = TradeEvent.engine_event(
            EventType.STRATEGY_CHANGE, "sma_crossover -> bollinger",
            timestamp=datetime(2026, 2, 14, 10, 0, 0),
        )
        journal.log_event(event)

        events = journal.read_events(date(2026, 2, 14))
        assert len(events) == 1
        assert events[0].event_type == EventType.STRATEGY_CHANGE
        assert events[0].detail == "sma_crossover -> bollinger"


class TestAllEventTypes:
    """모든 이벤트 타입 라운드트립"""

    @pytest.mark.parametrize("event_type", [
        "signal", "order", "force_close", "engine_start",
        "engine_stop", "regime_change", "strategy_change",
    ])
    def test_event_type_roundtrip(self, journal, event_type):
        event = _make_event(event_type=event_type, detail=f"test {event_type}")
        journal.log_event(event)

        events = journal.read_events(date(2026, 2, 14))
        assert len(events) == 1
        assert events[0].event_type == event_type
        assert events[0].detail == f"test {event_type}"
