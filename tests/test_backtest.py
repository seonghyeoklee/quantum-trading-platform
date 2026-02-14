"""백테스트 엔진 단위 테스트 — yfinance 호출 없이 합성 데이터로 검증"""

from app.models import ChartData
from app.trading.backtest import BacktestResult, run_backtest, _calc_max_drawdown, _calc_sharpe_ratio


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
