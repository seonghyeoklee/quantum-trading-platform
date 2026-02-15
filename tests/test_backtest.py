"""백테스트 엔진 단위 테스트 — yfinance 호출 없이 합성 데이터로 검증"""

from app.models import ChartData
from app.trading.backtest import (
    BacktestResult,
    RegimeBacktestResult,
    run_backtest,
    run_bollinger_backtest,
    run_regime_segmented_backtest,
    to_yfinance_ticker,
    _calc_max_drawdown,
    _calc_sharpe_ratio,
)


def _make_chart(prices: list[int], base_date: int = 20240101) -> list[ChartData]:
    """테스트용 합성 차트 데이터 생성. volume은 기본 100_000."""
    chart = []
    for i, price in enumerate(prices):
        chart.append(
            ChartData(
                date=str(base_date + i),
                open=price,
                high=price + 10,
                low=price - 10,
                close=price,
                volume=100_000,
            )
        )
    return chart


def _make_chart_with_volume(
    prices: list[int], volumes: list[int], base_date: int = 20240101
) -> list[ChartData]:
    """가격 + 거래량을 직접 지정하는 합성 차트 생성."""
    chart = []
    for i, (price, vol) in enumerate(zip(prices, volumes)):
        chart.append(
            ChartData(
                date=str(base_date + i),
                open=price,
                high=price + 10,
                low=price - 10,
                close=price,
                volume=vol,
            )
        )
    return chart


class TestBuyAndHold:
    """시그널 없는 횡보장 → 거래 0회"""

    def test_flat_prices_no_trades(self):
        """일정한 가격 → SMA 크로스 없음 → 거래 0회, 수익률 0%"""
        prices = [10000] * 30
        chart = _make_chart(prices)

        result = run_backtest(chart, initial_capital=10_000_000, order_amount=500_000)

        assert result.trade_count == 0
        assert result.total_return_pct == 0.0
        assert result.buy_and_hold_pct == 0.0


class TestSingleBuySellCycle:
    """매수→매도 1사이클 수익 계산 정확성"""

    def test_golden_cross_then_dead_cross(self):
        """SMA5 > SMA20 골든크로스 → 매수 → 데드크로스 → 매도"""
        prices = (
            [1000] * 15
            + [950, 900, 850, 800, 750]  # 15-19: 하락 (SMA5 << SMA20)
            + [850, 950, 1050, 1150, 1250]  # 20-24: 급등 (골든크로스)
            + [1300, 1350, 1400, 1400, 1400]  # 25-29: 상승 유지
            + [1350, 1300, 1250, 1200, 1150]  # 30-34: 하락
            + [1100, 1050, 1000, 950, 900]  # 35-39: 급락 (데드크로스)
            + [850, 800, 750, 700, 650]  # 40-44: 추가 하락
        )
        chart = _make_chart(prices)

        result = run_backtest(
            chart,
            initial_capital=10_000_000,
            order_amount=500_000,
            short_period=5,
            long_period=20,
        )

        # 매수/매도 쌍이 있어야 함
        buy_trades = [t for t in result.trades if t.side == "buy"]
        sell_trades = [t for t in result.trades if t.side == "sell"]
        assert len(buy_trades) >= 1
        assert len(sell_trades) >= 1

        # 첫 매수가와 첫 매도가 확인
        buy_price = buy_trades[0].price
        sell_price = sell_trades[0].price
        qty = buy_trades[0].quantity
        expected_pnl = qty * (sell_price - buy_price)
        actual_pnl = result.equity_curve[-1] - 10_000_000
        assert abs(actual_pnl - expected_pnl) < 1


class TestMaxDrawdown:
    """알려진 자산 곡선으로 MDD 검증"""

    def test_known_drawdown(self):
        """100 → 120 → 90 → 110: MDD = (120-90)/120 = 25%"""
        equity = [100.0, 110.0, 120.0, 100.0, 90.0, 95.0, 110.0]
        mdd = _calc_max_drawdown(equity)
        assert abs(mdd - 25.0) < 0.01

    def test_no_drawdown(self):
        """순수 상승 → MDD = 0%"""
        equity = [100.0, 110.0, 120.0, 130.0]
        mdd = _calc_max_drawdown(equity)
        assert mdd == 0.0

    def test_monotone_decrease(self):
        """순수 하락 → MDD = 전체 하락폭"""
        equity = [100.0, 80.0, 60.0, 40.0]
        mdd = _calc_max_drawdown(equity)
        assert abs(mdd - 60.0) < 0.01


class TestWinRate:
    """승률 검증 — trades 목록과 일관성 확인"""

    def test_win_rate_matches_trades(self):
        """win_rate는 trades 목록의 매수→매도 페어 기준으로 정확히 계산"""
        prices = (
            [1000] * 15
            + [950, 900, 850, 800, 750]
            + [850, 950, 1050, 1150, 1250]
            + [1300, 1350, 1400, 1400, 1400]
            + [1350, 1300, 1250, 1200, 1150]
            + [1100, 1050, 1000, 950, 900]
            + [850, 800, 850, 900, 950]
            + [1000, 1050, 1100, 1150, 1200]
            + [1150, 1100, 1050, 1000, 950]
        )
        chart = _make_chart(prices)

        result = run_backtest(
            chart,
            initial_capital=10_000_000,
            order_amount=500_000,
            short_period=5,
            long_period=20,
        )

        # trades 목록에서 직접 승률 재계산
        buy_price = None
        wins = 0
        total_pairs = 0
        for t in result.trades:
            if t.side == "buy":
                buy_price = t.price
            elif t.side == "sell" and buy_price is not None:
                total_pairs += 1
                if t.price > buy_price:
                    wins += 1
                buy_price = None

        expected_win_rate = (wins / total_pairs * 100) if total_pairs > 0 else 0.0
        assert result.win_rate == round(expected_win_rate, 2)

    def test_no_completed_trades_zero_win_rate(self):
        """매도 없이 매수만 → 완결 거래 0 → 승률 0%"""
        # 골든크로스 후 매도 없이 끝나는 데이터
        prices = (
            [1000] * 15
            + [950, 900, 850, 800, 750]
            + [850, 950, 1050, 1150, 1250]  # 골든크로스 → 매수
        )
        chart = _make_chart(prices)
        result = run_backtest(chart)

        sell_trades = [t for t in result.trades if t.side == "sell"]
        assert len(sell_trades) == 0
        assert result.win_rate == 0.0


class TestSharpeRatio:
    """Sharpe ratio 계산 검증"""

    def test_constant_equity_returns_none(self):
        """일정 자산 → std=0 → Sharpe=None"""
        equity = [100.0, 100.0, 100.0, 100.0]
        sharpe = _calc_sharpe_ratio(equity)
        assert sharpe is None

    def test_positive_returns_positive_sharpe(self):
        """꾸준한 상승 → 양의 Sharpe"""
        equity = [100.0 + i * 0.5 for i in range(100)]
        sharpe = _calc_sharpe_ratio(equity)
        assert sharpe is not None
        assert sharpe > 0

    def test_insufficient_data_returns_none(self):
        """데이터 부족 → None"""
        equity = [100.0, 101.0]
        sharpe = _calc_sharpe_ratio(equity)
        assert sharpe is None


class TestAdvancedVsBasicStrategy:
    """동일 데이터에서 basic vs advanced 전략 비교"""

    def test_both_strategies_run(self):
        """두 전략 모두 에러 없이 실행되고 BacktestResult 반환"""
        prices = (
            [1000] * 15
            + [980, 960, 940, 920, 900]
            + [920, 940, 960, 980, 1000, 1020, 1040, 1060, 1080, 1100]
            + [1080, 1060, 1040, 1020, 1000]
        )
        chart = _make_chart(prices)

        basic = run_backtest(chart, use_advanced=False)
        advanced = run_backtest(chart, use_advanced=True)

        assert isinstance(basic, BacktestResult)
        assert isinstance(advanced, BacktestResult)

    def test_advanced_may_filter_trades(self):
        """advanced 전략은 RSI/거래량 필터로 거래가 같거나 적을 수 있음"""
        prices = (
            [1000] * 15
            + [980, 960, 940, 920, 900]
            + [950, 1000, 1050, 1100, 1150]
            + [1100, 1050, 1000, 950, 900]
        )
        chart = _make_chart(prices)

        basic = run_backtest(chart, use_advanced=False)
        advanced = run_backtest(chart, use_advanced=True)

        assert advanced.trade_count <= basic.trade_count


class TestEdgeCases:
    """엣지 케이스"""

    def test_insufficient_data(self):
        """데이터 부족 시 빈 결과 반환"""
        chart = _make_chart([1000] * 10)
        result = run_backtest(chart, long_period=20)

        assert result.trade_count == 0
        assert result.total_return_pct == 0.0
        assert result.sharpe_ratio is None

    def test_equity_curve_length(self):
        """equity_curve 길이 = 차트 길이"""
        chart = _make_chart([1000] * 30)
        result = run_backtest(chart)
        assert len(result.equity_curve) == len(chart)

    def test_initial_capital_preserved_no_trades(self):
        """거래 없으면 초기 자본 유지"""
        chart = _make_chart([1000] * 30)
        result = run_backtest(chart, initial_capital=5_000_000)
        assert result.equity_curve[-1] == 5_000_000


class TestStopLossAndMaxHolding:
    """SMA 크로스오버 백테스트: 손절 + 최대 보유기간 테스트"""

    def test_stop_loss_triggers_sell(self):
        """매수 후 5% 하락 → stop_loss 매도"""
        # SMA5/SMA20 골든크로스 → 매수 → 5% 이상 하락
        prices = (
            [1000] * 15
            + [950, 900, 850, 800, 750]  # 하락 (SMA5 << SMA20)
            + [850, 950, 1050, 1150, 1250]  # 골든크로스 → 매수 @ ~1250
            + [1200, 1150, 1100]  # 하락 (~12% drop from 1250)
        )
        chart = _make_chart(prices)
        result = run_backtest(
            chart, short_period=5, long_period=20,
            stop_loss_pct=5.0,
        )
        stop_loss_sells = [t for t in result.trades if t.reason == "stop_loss"]
        assert len(stop_loss_sells) >= 1, f"stop_loss 매도 없음. trades={result.trades}"

    def test_stop_loss_disabled_by_default(self):
        """stop_loss_pct=0.0 → stop-loss 미발동"""
        prices = (
            [1000] * 15
            + [950, 900, 850, 800, 750]
            + [850, 950, 1050, 1150, 1250]
            + [1200, 1150, 1100]
        )
        chart = _make_chart(prices)
        result = run_backtest(
            chart, short_period=5, long_period=20,
            stop_loss_pct=0.0,
        )
        stop_loss_sells = [t for t in result.trades if t.reason == "stop_loss"]
        assert len(stop_loss_sells) == 0

    def test_stop_loss_with_advanced_filters(self):
        """Advanced 전략 + stop-loss 조합 동작"""
        prices = (
            [1000] * 15
            + [950, 900, 850, 800, 750]
            + [850, 950, 1050, 1150, 1250]
            + [1200, 1150, 1100, 1050, 1000]
        )
        volumes = [200_000] * len(prices)  # 높은 거래량으로 필터 통과
        chart = _make_chart_with_volume(prices, volumes)
        result = run_backtest(
            chart, short_period=5, long_period=20,
            use_advanced=True, stop_loss_pct=5.0,
        )
        # 에러 없이 실행되면 성공 (advanced 필터가 매수를 차단할 수도 있음)
        assert isinstance(result, BacktestResult)

    def test_max_holding_days_forces_sell(self):
        """보유기간 초과 → max_holding 매도"""
        # 골든크로스 → 매수 → 횡보(데드크로스 없이 보유기간 초과)
        prices = (
            [1000] * 15
            + [950, 900, 850, 800, 750]  # 하락
            + [850, 950, 1050, 1150, 1250]  # 골든크로스 → 매수
            + [1260, 1270, 1265, 1260, 1255]  # 소폭 횡보 (데드크로스 안 남)
        )
        chart = _make_chart(prices)
        result = run_backtest(
            chart, short_period=5, long_period=20,
            max_holding_days=3,
        )
        max_holding_sells = [t for t in result.trades if t.reason == "max_holding"]
        assert len(max_holding_sells) >= 1, f"max_holding 매도 없음. trades={result.trades}"

    def test_max_holding_days_disabled_by_default(self):
        """max_holding_days=0 → 비활성"""
        prices = (
            [1000] * 15
            + [950, 900, 850, 800, 750]
            + [850, 950, 1050, 1150, 1250]
            + [1260, 1270, 1265, 1260, 1255]
        )
        chart = _make_chart(prices)
        result = run_backtest(
            chart, short_period=5, long_period=20,
            max_holding_days=0,
        )
        max_holding_sells = [t for t in result.trades if t.reason == "max_holding"]
        assert len(max_holding_sells) == 0


class TestVolumeFilterBasic:
    """기본 SMA 모드 거래량 필터 테스트"""

    def test_volume_filter_basic_blocks_low_volume(self):
        """volume_filter_basic=True → 거래량 부족 시 매수 차단"""
        # 골든크로스가 발생하는 데이터 + 낮은 거래량
        prices = (
            [1000] * 15
            + [950, 900, 850, 800, 750]  # 하락
            + [850, 950, 1050, 1150, 1250]  # 골든크로스
        )
        # 높은 거래량 SMA, 마지막(매수 시점) 거래량 매우 낮음
        volumes = [200_000] * 24 + [100]
        chart = _make_chart_with_volume(prices, volumes)

        result_no_filter = run_backtest(
            chart, short_period=5, long_period=20,
            volume_filter_basic=False,
        )
        result_with_filter = run_backtest(
            chart, short_period=5, long_period=20,
            volume_filter_basic=True, volume_ma_period=20,
        )

        buys_no = len([t for t in result_no_filter.trades if t.side == "buy"])
        buys_with = len([t for t in result_with_filter.trades if t.side == "buy"])
        assert buys_with <= buys_no


class TestBollingerBacktest:
    """볼린저밴드 반전 전략 백테스트 테스트"""

    def _make_bollinger_chart(
        self, prices: list[int], volumes: list[int] | None = None
    ) -> list[ChartData]:
        """볼린저밴드 테스트용 차트 생성."""
        chart = []
        for i, price in enumerate(prices):
            vol = volumes[i] if volumes else 100_000
            chart.append(
                ChartData(
                    date=str(20240101 + i),
                    open=price,
                    high=price + 10,
                    low=price - 10,
                    close=price,
                    volume=vol,
                )
            )
        return chart

    def test_insufficient_data(self):
        """데이터 부족 시 빈 결과 반환"""
        chart = self._make_bollinger_chart([1000] * 15)
        result = run_bollinger_backtest(chart, period=20)

        assert result.trade_count == 0
        assert result.total_return_pct == 0.0
        assert result.sharpe_ratio is None

    def test_flat_prices_no_trades(self):
        """일정 가격 → 밴드 폭 0 → 거래 없음"""
        chart = self._make_bollinger_chart([1000] * 30)
        result = run_bollinger_backtest(chart, period=20)

        assert result.trade_count == 0
        assert result.total_return_pct == 0.0

    def test_buy_sell_cycle(self):
        """하단 반등 매수 → 상단 도달 매도 사이클"""
        # period=5 로 작은 윈도우 사용하여 빠른 시그널 생성
        # 안정 구간 → 급락(하단 돌파) → 반등(매수) → 급등(상단 도달, 매도)
        prices = (
            [1000] * 10  # 안정 구간 (밴드 형성)
            + [950, 900, 850, 800, 750]  # 급락 → 하단밴드 아래로
            + [850]  # 반등 → 매수 시그널 (prev ≤ lower, curr > lower)
            + [900, 950, 1000, 1050, 1100, 1150, 1200, 1250]  # 상승 → 상단 도달 → 매도
        )
        chart = self._make_bollinger_chart(prices)
        result = run_bollinger_backtest(chart, period=5, num_std=1.5)

        buy_trades = [t for t in result.trades if t.side == "buy"]
        sell_trades = [t for t in result.trades if t.side == "sell"]

        assert len(buy_trades) >= 1, f"매수 없음. trades={result.trades}"
        assert len(sell_trades) >= 1, f"매도 없음. trades={result.trades}"

    def test_forced_liquidation(self):
        """max_holding_days 이후 강제 청산"""
        # 하단 반등 매수 후 밴드 내에서 횡보 → 강제 청산
        prices = (
            [1000] * 10
            + [950, 900, 850, 800, 750]  # 급락
            + [850]  # 반등 → 매수
            + [860, 870, 865, 860, 855, 850]  # 횡보 (상단 미도달)
        )
        chart = self._make_bollinger_chart(prices)
        result = run_bollinger_backtest(
            chart, period=5, num_std=1.5, max_holding_days=3
        )

        sell_trades = [t for t in result.trades if t.side == "sell"]
        buy_trades = [t for t in result.trades if t.side == "buy"]

        # 매수가 발생했으면 강제 청산에 의해 매도도 발생해야 함
        if len(buy_trades) >= 1:
            assert len(sell_trades) >= 1, "강제 청산이 발생하지 않음"

    def test_max_daily_trades_limit(self):
        """당일 매수 횟수 제한"""
        # 같은 날짜에 여러 번 매수 시그널이 발생하도록 구성
        # (실제로는 일봉이므로 같은 날짜 반복은 어렵지만, 제한 로직 검증)
        prices = [1000] * 10 + [950, 900, 850, 800, 750, 850, 900, 950, 1000, 1050]
        chart = self._make_bollinger_chart(prices)
        result = run_bollinger_backtest(
            chart, period=5, num_std=1.5, max_daily_trades=1
        )

        # 각 날짜별 매수가 최대 1회인지 확인
        from collections import Counter
        buy_dates = [t.date for t in result.trades if t.side == "buy"]
        date_counts = Counter(buy_dates)
        for date, count in date_counts.items():
            assert count <= 1, f"{date} 날짜에 {count}회 매수 (최대 1회)"

    def test_equity_curve_length(self):
        """equity_curve 길이 = 차트 길이"""
        chart = self._make_bollinger_chart([1000] * 30)
        result = run_bollinger_backtest(chart, period=20)
        assert len(result.equity_curve) == len(chart)

    def test_initial_capital_preserved_no_trades(self):
        """거래 없으면 초기 자본 유지"""
        chart = self._make_bollinger_chart([1000] * 30)
        result = run_bollinger_backtest(chart, initial_capital=5_000_000, period=20)
        assert result.equity_curve[-1] == 5_000_000

    def test_buy_and_hold_calculation(self):
        """buy_and_hold 수익률은 첫날/마지막날 종가 기준"""
        prices = list(range(1000, 1031))  # 1000 → 1030
        chart = self._make_bollinger_chart(prices)
        result = run_bollinger_backtest(chart, period=20)
        expected_bnh = (1030 - 1000) / 1000 * 100
        assert abs(result.buy_and_hold_pct - expected_bnh) < 0.01

    def test_win_rate_accuracy(self):
        """승률이 trades 기반으로 정확히 계산되는지 검증"""
        prices = (
            [1000] * 10
            + [950, 900, 850, 800, 750]
            + [850, 950, 1050, 1150, 1250]
            + [1200, 1150, 1100, 1050, 1000]
            + [900, 800, 850, 900, 950]
        )
        chart = self._make_bollinger_chart(prices)
        result = run_bollinger_backtest(chart, period=5, num_std=1.5)

        # trades 목록에서 직접 승률 재계산
        buy_price = None
        wins = 0
        total_pairs = 0
        for t in result.trades:
            if t.side == "buy":
                buy_price = t.price
            elif t.side == "sell" and buy_price is not None:
                total_pairs += 1
                if t.price > buy_price:
                    wins += 1
                buy_price = None

        expected = (wins / total_pairs * 100) if total_pairs > 0 else 0.0
        assert result.win_rate == round(expected, 2)


def _make_minute_chart(
    prices: list[int],
    volumes: list[int] | None = None,
    base_hour: int = 9,
    base_minute: int = 0,
) -> list[ChartData]:
    """분봉 형식(YYYY-MM-DD HH:MM) 차트 데이터 생성."""
    chart = []
    for i, price in enumerate(prices):
        h = base_hour + (base_minute + i) // 60
        m = (base_minute + i) % 60
        vol = volumes[i] if volumes else 100_000
        chart.append(
            ChartData(
                date=f"2026-02-10 {h:02d}:{m:02d}",
                open=price,
                high=price + 10,
                low=price - 10,
                close=price,
                volume=vol,
            )
        )
    return chart


class TestBollingerIntradayConstraints:
    """볼린저 백테스트 장중 제약 테스트"""

    def test_force_close_at_cutoff(self):
        """15:10 이후 보유 포지션 강제 매도"""
        # period=5, 14:30 시작 → 충분히 15:10 이후까지 데이터 확보
        # 안정 → 급락 → 반등(매수) → 횡보(상단 미도달, 보유 유지) → 15:10에 강제 청산
        prices = (
            [1000] * 10
            + [950, 900, 850, 800, 750]  # 급락
            + [850]  # 반등 → 매수
            + [855, 860, 855, 860, 855, 860, 855, 860,  # 횡보 (상단 미도달)
               855, 860, 855, 860, 855, 860, 855, 860,
               855, 860, 855, 860, 855, 860, 855, 860,
               855]  # 15:11 시점 (index 41)
        )
        chart = _make_minute_chart(prices, base_hour=14, base_minute=30)
        result = run_bollinger_backtest(
            chart, period=5, num_std=1.5,
            force_close_minute=1510,
            max_holding_days=999,  # 보유기간 제한 비활성화
        )
        buy_trades = [t for t in result.trades if t.side == "buy"]
        sell_trades = [t for t in result.trades if t.side == "sell"]
        if len(buy_trades) >= 1:
            assert len(sell_trades) >= 1, "강제 청산이 발생하지 않음"
            # 강제 청산에 의한 매도가 포함되어야 함
            force_close_sells = [
                t for t in sell_trades
                if int(t.date[11:13]) * 100 + int(t.date[14:16]) >= 1510
            ]
            assert len(force_close_sells) >= 1, (
                f"15:10 이후 강제 청산 없음. 매도 시각: "
                f"{[t.date for t in sell_trades]}"
            )

    def test_no_buy_after_cutoff(self):
        """매수금지 시간(14:50) 이후 매수 차단"""
        # 14:45~15:10 분봉, 하단 반등 시그널이 14:50 이후에 발생
        prices = (
            [1000] * 10
            + [950, 900, 850, 800, 750]  # 급락
            + [850, 900, 950, 1000, 1050]  # 반등
        )
        chart = _make_minute_chart(prices, base_hour=14, base_minute=45)
        # no_new_buy_minute=1450 → 14:50 이후 매수 금지
        result = run_bollinger_backtest(
            chart, period=5, num_std=1.5,
            no_new_buy_minute=1450,
        )
        # 모든 매수가 14:50 전에만 발생해야 함
        for t in result.trades:
            if t.side == "buy":
                buy_hhmm = int(t.date[11:13]) * 100 + int(t.date[14:16])
                assert buy_hhmm < 1450, f"매수금지 시간 이후 매수 발생: {t.date}"

    def test_active_window_filter(self):
        """비활성 시간대(11:00~14:00)에는 매수 차단"""
        # 11:50~12:20 분봉, 하단 반등 시그널 발생
        prices = (
            [1000] * 10
            + [950, 900, 850, 800, 750]  # 급락
            + [850, 900, 950, 1000, 1050]  # 반등
        )
        chart = _make_minute_chart(prices, base_hour=11, base_minute=50)
        # 활성 시간대: 09:30~11:00, 14:00~14:50 → 11:50~12:20은 비활성
        result = run_bollinger_backtest(
            chart, period=5, num_std=1.5,
            active_windows=[(930, 1100), (1400, 1450)],
        )
        # 비활성 시간대에는 매수가 없어야 함
        for t in result.trades:
            if t.side == "buy":
                buy_hhmm = int(t.date[11:13]) * 100 + int(t.date[14:16])
                in_window = any(s <= buy_hhmm < e for s, e in [(930, 1100), (1400, 1450)])
                assert in_window, f"비활성 시간대 매수 발생: {t.date} ({buy_hhmm})"

    def test_volume_filter_blocks_low_volume(self):
        """거래량 부족 시 매수 차단"""
        # 하단 반등 조건 충족 + 낮은 거래량
        prices = (
            [1000] * 10
            + [950, 900, 850, 800, 750]  # 급락
            + [850]  # 반등
            + [900, 950, 1000, 1050, 1100, 1150, 1200, 1250]  # 상승
        )
        # 과거 거래량 높고 반등 시점 거래량 매우 낮음
        volumes = (
            [100_000] * 15
            + [500]  # 반등 시점: 거래량 매우 낮음
            + [100_000] * 8
        )
        chart_no_filter = []
        chart_with_filter = []
        for i, price in enumerate(prices):
            vol = volumes[i]
            chart_no_filter.append(
                ChartData(
                    date=str(20240101 + i), open=price, high=price + 10,
                    low=price - 10, close=price, volume=vol,
                )
            )
            chart_with_filter.append(
                ChartData(
                    date=str(20240101 + i), open=price, high=price + 10,
                    low=price - 10, close=price, volume=vol,
                )
            )

        result_no_filter = run_bollinger_backtest(
            chart_no_filter, period=5, num_std=1.5,
        )
        result_with_filter = run_bollinger_backtest(
            chart_with_filter, period=5, num_std=1.5, volume_ma_period=10,
        )
        # 거래량 필터 적용 시 매수 횟수가 같거나 적어야 함
        buys_no = len([t for t in result_no_filter.trades if t.side == "buy"])
        buys_with = len([t for t in result_with_filter.trades if t.side == "buy"])
        assert buys_with <= buys_no, (
            f"거래량 필터 매수 {buys_with} > 필터 없음 {buys_no}"
        )


class TestRegimeSegmentedBacktest:
    """국면별 백테스트 검증"""

    def test_regime_results_produced(self):
        """상승→하락 데이터 → 국면별 결과 분리"""
        # 150일 상승 + 150일 하락 = 국면 전환
        prices_up = [int(500 + i) for i in range(150)]
        prices_down = [int(650 - i) for i in range(150)]
        chart = _make_chart(prices_up + prices_down)
        results = run_regime_segmented_backtest(
            chart, short_period=5, long_period=20,
        )
        assert len(results) >= 2
        for r in results:
            assert isinstance(r, RegimeBacktestResult)
            assert r.days > 0
            assert len(r.strategy_results) == 4
            for label, br in r.strategy_results.items():
                assert isinstance(br, BacktestResult)

    def test_warmup_enables_sma(self):
        """warm-up 패딩으로 SMA 계산 가능한지 확인"""
        # 200일 데이터로 국면 분할 후 각 구간에 SMA 계산 가능
        prices = [int(500 + i) for i in range(200)]
        chart = _make_chart(prices)
        results = run_regime_segmented_backtest(
            chart, short_period=5, long_period=20,
        )
        # 에러 없이 결과가 나오면 warm-up 패딩이 정상 동작
        assert len(results) >= 1

    def test_independent_capital_per_regime(self):
        """각 국면은 동일 초기자본으로 독립 시뮬레이션"""
        prices = [int(500 + i) for i in range(150)] + [int(650 - i) for i in range(150)]
        chart = _make_chart(prices)
        results = run_regime_segmented_backtest(
            chart, initial_capital=10_000_000,
            short_period=5, long_period=20,
        )
        for r in results:
            for label, br in r.strategy_results.items():
                if br.equity_curve:
                    # 첫 번째 equity는 초기자본과 동일 (보유 없이 시작)
                    assert br.equity_curve[0] == 10_000_000

    def test_insufficient_data_returns_empty(self):
        """120개 미만 데이터 → 빈 리스트"""
        chart = _make_chart([1000] * 100)
        results = run_regime_segmented_backtest(chart)
        assert results == []


class TestTrailingStop:
    """트레일링 스탑 기능 테스트"""

    def test_trailing_stop_triggers_sell(self):
        """매수→상승(고점)→하락 시 trailing stop 매도 확인"""
        prices = (
            [1000] * 15
            + [950, 900, 850, 800, 750]  # 하락 → SMA5 << SMA20
            + [850, 950, 1050, 1150, 1250]  # 급등 → 골든크로스 → 매수
            + [1350, 1450, 1500, 1500, 1500]  # 상승 (고점 1500)
            + [1450, 1400, 1350, 1300, 1250]  # 하락 → 1250/1500 = 16.7% 하락
        )
        chart = _make_chart(prices)

        result = run_backtest(
            chart,
            initial_capital=10_000_000,
            order_amount=500_000,
            short_period=5,
            long_period=20,
            trailing_stop_pct=10.0,  # 고점 대비 10% 하락 시 매도
        )

        # 매수 + 매도 발생 확인
        sell_trades = [t for t in result.trades if t.side == "sell"]
        assert len(sell_trades) >= 1
        assert sell_trades[0].reason == "trailing_stop"

    def test_trailing_stop_disabled_when_zero(self):
        """trailing_stop_pct=0이면 trailing stop 미작동"""
        prices = (
            [1000] * 15
            + [950, 900, 850, 800, 750]
            + [850, 950, 1050, 1150, 1250]
            + [1350, 1450, 1500, 1500, 1500]
            + [1450, 1400, 1350, 1300, 1250]
        )
        chart = _make_chart(prices)

        result = run_backtest(
            chart,
            initial_capital=10_000_000,
            order_amount=500_000,
            short_period=5,
            long_period=20,
            trailing_stop_pct=0.0,
        )

        trailing_sells = [t for t in result.trades if t.reason == "trailing_stop"]
        assert len(trailing_sells) == 0


class TestCapitalRatio:
    """자본 활용 비율 기능 테스트"""

    def test_capital_ratio_increases_quantity(self):
        """capital_ratio=0.5일 때 초기자본 50% 사용 → 더 큰 수량 매수"""
        prices = (
            [1000] * 15
            + [950, 900, 850, 800, 750]
            + [850, 950, 1050, 1150, 1250]  # 골든크로스
            + [1300] * 10
        )
        chart = _make_chart(prices)

        # capital_ratio=0.5 → 10M * 0.5 = 5M / 1250 = 4000주
        result_ratio = run_backtest(
            chart,
            initial_capital=10_000_000,
            order_amount=500_000,
            short_period=5,
            long_period=20,
            capital_ratio=0.5,
        )

        # capital_ratio=0 → order_amount 500K / 1250 = 400주
        result_fixed = run_backtest(
            chart,
            initial_capital=10_000_000,
            order_amount=500_000,
            short_period=5,
            long_period=20,
            capital_ratio=0.0,
        )

        buy_ratio = [t for t in result_ratio.trades if t.side == "buy"]
        buy_fixed = [t for t in result_fixed.trades if t.side == "buy"]

        assert len(buy_ratio) >= 1
        assert len(buy_fixed) >= 1
        assert buy_ratio[0].quantity > buy_fixed[0].quantity

    def test_capital_ratio_zero_uses_order_amount(self):
        """capital_ratio=0이면 기존 order_amount 동작 유지"""
        prices = (
            [1000] * 15
            + [950, 900, 850, 800, 750]
            + [850, 950, 1050, 1150, 1250]
            + [1300] * 10
        )
        chart = _make_chart(prices)

        result = run_backtest(
            chart,
            initial_capital=10_000_000,
            order_amount=500_000,
            short_period=5,
            long_period=20,
            capital_ratio=0.0,
        )

        buy_trades = [t for t in result.trades if t.side == "buy"]
        if buy_trades:
            # 500_000 // close = expected qty
            expected_qty = 500_000 // buy_trades[0].price
            assert buy_trades[0].quantity == expected_qty


class TestYfinanceTicker:
    """to_yfinance_ticker 변환 테스트"""

    def test_domestic_symbol(self):
        assert to_yfinance_ticker("005930") == "005930.KS"

    def test_us_symbol_aapl(self):
        assert to_yfinance_ticker("AAPL") == "AAPL"

    def test_us_symbol_tsla(self):
        assert to_yfinance_ticker("TSLA") == "TSLA"

    def test_us_symbol_single_char(self):
        assert to_yfinance_ticker("F") == "F"

    def test_five_digit_number(self):
        """5자리 숫자는 국내가 아님"""
        assert to_yfinance_ticker("12345") == "12345"
