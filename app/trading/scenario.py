"""시나리오 기반 자동 백테스트 프레임워크.

실제 과거 일봉 데이터(yfinance) + 합성 분봉 데이터로 시나리오를 정의하고,
run_bollinger_backtest()로 실행, 선언적 기대치와 비교하여 PASS/FAIL 판정.

- 8개 시나리오: tests/fixtures/scenario_charts/*.json (실제 일봉 데이터)
- 2개 시나리오: 합성 분봉 데이터 (trailing_stop_grace_minutes 테스트용)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from app.models import ChartData
from app.trading.backtest import BacktestResult, Trade, run_bollinger_backtest


# ---------------------------------------------------------------------------
# 데이터 구조
# ---------------------------------------------------------------------------

@dataclass
class TradeExpectation:
    """특정 거래에 대한 기대치."""
    index: int  # 거래 인덱스 (0=첫번째, -1=마지막)
    side: str | None = None  # "buy" / "sell"
    reason: str | None = None  # "signal" / "stop_loss" / "trailing_stop" / "max_holding"


@dataclass
class ScenarioExpectation:
    """시나리오 검증 기대치."""
    min_trades: int | None = None
    max_trades: int | None = None
    must_have_reasons: list[str] = field(default_factory=list)
    must_not_have_reasons: list[str] = field(default_factory=list)
    trade_expectations: list[TradeExpectation] = field(default_factory=list)
    custom_check: Callable[[BacktestResult, list[ChartData]], list[tuple[str, bool, str]]] | None = None


@dataclass
class Scenario:
    """시나리오 정의."""
    name: str
    description: str
    category: str  # "risk_management" | "signal_quality"
    chart_generator: Callable[[], list[ChartData]]
    backtest_params: dict
    expectation: ScenarioExpectation
    # 리포트용 상세 설명
    market_context: str = ""      # 시장 상황 설명
    test_point: str = ""          # 테스트 핵심 포인트
    expected_behavior: str = ""   # 기대 동작 설명
    key_params: dict | None = None  # 핵심 파라미터 (표시용)
    data_source: str = ""         # "real" 또는 "synthetic"


@dataclass
class ScenarioResult:
    """시나리오 실행 결과."""
    scenario: Scenario
    backtest_result: BacktestResult
    checks: list[tuple[str, bool, str]]  # (check_name, passed, detail)
    passed: bool
    chart: list[ChartData]


# ---------------------------------------------------------------------------
# Fixture 로더
# ---------------------------------------------------------------------------

_FIXTURE_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "scenario_charts"


def _load_fixture(name: str) -> list[ChartData]:
    """JSON fixture 파일 → list[ChartData] 변환."""
    fp = _FIXTURE_DIR / f"{name}.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    return [ChartData(**c) for c in data["chart"]]


def get_fixture_meta(name: str) -> dict:
    """fixture 메타정보(ticker, start, end) 반환. 리포트용."""
    fp = _FIXTURE_DIR / f"{name}.json"
    if not fp.exists():
        return {}
    data = json.loads(fp.read_text(encoding="utf-8"))
    return {"ticker": data.get("ticker", ""), "start": data.get("start", ""), "end": data.get("end", "")}


# ---------------------------------------------------------------------------
# 합성 데이터 헬퍼 (grace_minutes 시나리오 전용)
# ---------------------------------------------------------------------------

def _make_scenario_chart(
    prices: list[float],
    volumes: list[int] | None = None,
    base_date: str = "2026-01-05",
    base_hour: int = 9,
    base_minute: int = 0,
) -> list[ChartData]:
    """분봉 ChartData 리스트 생성.

    날짜: "YYYY-MM-DD HH:MM" 형식 (run_bollinger_backtest의 _parse_hhmm 호환).
    1분 간격으로 시간 증가. 장 시간(09:00~15:30) 내에서만 생성.
    """
    if volumes is None:
        volumes = [100_000] * len(prices)

    chart: list[ChartData] = []
    hour, minute = base_hour, base_minute

    for i, price in enumerate(prices):
        vol = volumes[i] if i < len(volumes) else 100_000
        date_str = f"{base_date} {hour:02d}:{minute:02d}"
        chart.append(ChartData(
            date=date_str,
            open=price,
            high=price + price * 0.002,
            low=price - price * 0.002,
            close=price,
            volume=vol,
        ))
        minute += 1
        if minute >= 60:
            minute = 0
            hour += 1

    return chart


def _gen_crash_in_grace() -> list[ChartData]:
    """시나리오 2: 매수 직후 급락 (유예 기간 내).

    밴드 하단 반등→매수, 이후 10분 이내에 고점 대비 5% 이상 급락.
    grace=30분이므로 트레일링 스탑 미발동.
    """
    prices: list[float] = []
    base = 10000.0
    for i in range(20):
        prices.append(base - i * 30)
    prices.append(9200.0)
    prices.append(9500.0)
    for _ in range(5):
        prices.append(9600.0)
    for _ in range(5):
        prices.append(9050.0)
    for _ in range(10):
        prices.append(9200.0)
    return _make_scenario_chart(prices)


def _gen_crash_after_grace() -> list[ChartData]:
    """시나리오 3: 유예 후 급락 — 트레일링 스탑 발동.

    grace=15분, 매수 후 20분 경과 뒤 급락.
    """
    prices: list[float] = []
    base = 10000.0
    for i in range(20):
        prices.append(base - i * 30)
    prices.append(9200.0)
    prices.append(9500.0)
    for i in range(20):
        prices.append(9600.0 + i * 5)
    for _ in range(10):
        prices.append(9150.0)
    for _ in range(10):
        prices.append(9200.0)
    return _make_scenario_chart(prices)


# ---------------------------------------------------------------------------
# 검증 엔진
# ---------------------------------------------------------------------------

def check_scenario(
    result: BacktestResult,
    chart: list[ChartData],
    expectation: ScenarioExpectation,
) -> list[tuple[str, bool, str]]:
    """선언적 기대치와 실제 결과 비교. (check_name, passed, detail) 리스트 반환."""
    checks: list[tuple[str, bool, str]] = []

    sell_reasons = [t.reason for t in result.trades if t.side == "sell"]

    # min_trades
    if expectation.min_trades is not None:
        ok = result.trade_count >= expectation.min_trades
        checks.append((
            "min_trades",
            ok,
            f"거래 {result.trade_count}건 >= {expectation.min_trades} 기대",
        ))

    # max_trades
    if expectation.max_trades is not None:
        ok = result.trade_count <= expectation.max_trades
        checks.append((
            "max_trades",
            ok,
            f"거래 {result.trade_count}건 <= {expectation.max_trades} 기대",
        ))

    # must_have_reasons
    for reason in expectation.must_have_reasons:
        ok = reason in sell_reasons
        checks.append((
            f"must_have_{reason}",
            ok,
            f"매도 사유 '{reason}' {'포함' if ok else '미포함'} (전체: {sell_reasons})",
        ))

    # must_not_have_reasons
    for reason in expectation.must_not_have_reasons:
        ok = reason not in sell_reasons
        checks.append((
            f"must_not_have_{reason}",
            ok,
            f"매도 사유 '{reason}' {'미포함' if ok else '포함됨'} (전체: {sell_reasons})",
        ))

    # trade_expectations (특정 거래 검증)
    for te in expectation.trade_expectations:
        if not result.trades:
            checks.append((
                f"trade[{te.index}]",
                False,
                "거래 없음",
            ))
            continue
        try:
            trade = result.trades[te.index]
        except IndexError:
            checks.append((
                f"trade[{te.index}]",
                False,
                f"거래 인덱스 {te.index} 범위 초과 (총 {len(result.trades)}건)",
            ))
            continue

        if te.side is not None:
            ok = trade.side == te.side
            checks.append((
                f"trade[{te.index}].side",
                ok,
                f"거래 side='{trade.side}' {'==' if ok else '!='} '{te.side}'",
            ))
        if te.reason is not None:
            ok = trade.reason == te.reason
            checks.append((
                f"trade[{te.index}].reason",
                ok,
                f"거래 reason='{trade.reason}' {'==' if ok else '!='} '{te.reason}'",
            ))

    # custom_check
    if expectation.custom_check is not None:
        custom_results = expectation.custom_check(result, chart)
        checks.extend(custom_results)

    return checks


def _check_min_profit_improvement(
    result: BacktestResult, chart: list[ChartData],
) -> list[tuple[str, bool, str]]:
    """min_profit_pct 적용 시 수익률이 미적용 대비 개선되는지 검증."""
    baseline = run_bollinger_backtest(
        chart,
        **{**_BASE_PARAMS, "min_profit_pct": 0.0},
    )
    ok = result.total_return_pct >= baseline.total_return_pct
    return [(
        "min_profit_improvement",
        ok,
        f"min_profit 적용 {result.total_return_pct:+.2f}% >= "
        f"미적용 {baseline.total_return_pct:+.2f}%",
    )]


def run_scenario(scenario: Scenario) -> ScenarioResult:
    """시나리오 1개 실행."""
    chart = scenario.chart_generator()
    result = run_bollinger_backtest(chart, **scenario.backtest_params)
    checks = check_scenario(result, chart, scenario.expectation)
    passed = all(c[1] for c in checks)
    return ScenarioResult(
        scenario=scenario,
        backtest_result=result,
        checks=checks,
        passed=passed,
        chart=chart,
    )


def run_all_scenarios() -> list[ScenarioResult]:
    """전체 시나리오 실행."""
    return [run_scenario(s) for s in SCENARIOS]


# ---------------------------------------------------------------------------
# 시나리오 정의 (10개)
# ---------------------------------------------------------------------------

# 공통 백테스트 파라미터 (일봉 20일 볼린저)
_BASE_PARAMS = dict(
    initial_capital=10_000_000,
    order_amount=1_000_000,
    period=20,
    num_std=2.0,
    max_holding_days=50,
    max_daily_trades=5,
)


SCENARIOS: list[Scenario] = [
    # 1. 초저변동 ETF — 밴드 좁아서 매수 차단
    Scenario(
        name="largecap_low_vol",
        description="초저변동 ETF — 밴드 좁아서 매수 차단",
        category="signal_quality",
        chart_generator=lambda: _load_fixture("largecap_low_vol"),
        backtest_params={**_BASE_PARAMS, "min_bandwidth": 3.0},
        expectation=ScenarioExpectation(max_trades=0),
        market_context="T-Bill ETF(BIL)의 실제 일봉 데이터. "
            "초단기 국채 ETF는 가격 변동이 극히 미미하여 볼린저 밴드가 극도로 수축 (밴드폭 < 1%).",
        test_point="min_bandwidth 필터가 좁은 밴드에서 의미 없는 매수 시그널을 정확히 차단하는지 확인.",
        expected_behavior="밴드 폭이 3% 미만이므로 하단 반등 시그널이 발생해도 매수가 차단되어 거래 0건.",
        key_params={"min_bandwidth": "3.0%"},
        data_source="real",
    ),
    # 2. 매수 직후 급락 (유예 기간 내) → 트레일링 미발동
    Scenario(
        name="crash_in_grace",
        description="매수 직후 급락 (유예 기간 내) — 트레일링 미발동",
        category="risk_management",
        chart_generator=_gen_crash_in_grace,
        backtest_params={
            **_BASE_PARAMS,
            "trailing_stop_pct": 3.0,
            "trailing_stop_grace_minutes": 30,
        },
        expectation=ScenarioExpectation(
            must_not_have_reasons=["trailing_stop"],
        ),
        market_context="볼린저 하단 반등으로 매수 진입한 직후(10분 이내), "
            "일시적 매물 출회로 고점 대비 5% 이상 급락하는 상황. "
            "이후 가격이 어느 정도 회복됨.",
        test_point="trailing_stop_grace_minutes(유예 기간) 동안은 트레일링 스탑이 발동하지 않는지 확인. "
            "매수 직후 변동성이 클 때 조기 손절을 방지하는 안전장치.",
        expected_behavior="매수 후 10분밖에 안 지났으므로(유예 30분 미만) 트레일링 스탑이 작동하지 않음. "
            "'trailing_stop' 사유 매도가 없어야 함.",
        key_params={"trailing_stop_pct": "3.0%", "grace_minutes": "30분"},
        data_source="synthetic",
    ),
    # 3. 유예 후 급락 → 트레일링 발동
    Scenario(
        name="crash_after_grace",
        description="유예 후 급락 — 트레일링 스탑 발동",
        category="risk_management",
        chart_generator=_gen_crash_after_grace,
        backtest_params={
            **_BASE_PARAMS,
            "trailing_stop_pct": 3.0,
            "trailing_stop_grace_minutes": 15,
        },
        expectation=ScenarioExpectation(
            must_have_reasons=["trailing_stop"],
        ),
        market_context="볼린저 하단 반등으로 매수 진입 후, 20분간 소폭 상승하며 고점을 형성. "
            "이후 갑자기 매도세가 몰리며 고점 대비 5% 이상 급락.",
        test_point="유예 기간(15분)이 지난 뒤에는 트레일링 스탑이 정상 발동하는지 확인. "
            "시나리오 2(crash_in_grace)와 짝으로 유예 기간 경계값을 검증.",
        expected_behavior="매수 후 20분 경과(유예 15분 초과) + 고점 대비 5% 하락이므로 "
            "트레일링 스탑 발동. 'trailing_stop' 사유 매도가 반드시 존재.",
        key_params={"trailing_stop_pct": "3.0%", "grace_minutes": "15분"},
        data_source="synthetic",
    ),
    # 4. 초저변동 ETF (2) — 매수 차단
    Scenario(
        name="narrow_oscillation",
        description="초저변동 ETF — 매수 차단",
        category="signal_quality",
        chart_generator=lambda: _load_fixture("narrow_oscillation"),
        backtest_params={**_BASE_PARAMS, "min_bandwidth": 3.0},
        expectation=ScenarioExpectation(max_trades=0),
        market_context="단기 국채 ETF(SHV)의 실제 일봉 데이터. "
            "거의 무위험 자산으로 가격 변동이 극미하여 볼린저 밴드가 극도로 수축.",
        test_point="시나리오 1(largecap_low_vol)과 유사하지만 다른 초저변동 상품으로 검증. "
            "min_bandwidth가 전 구간에서 일관되게 매수를 차단하는지 확인.",
        expected_behavior="전체 기간 밴드 폭이 3% 미만 유지. 거래 0건.",
        key_params={"min_bandwidth": "3.0%"},
        data_source="real",
    ),
    # 5. 상단 도달 매도 (시그널)
    Scenario(
        name="upper_touch_sell",
        description="하단 반등 매수 → 상단 도달 시그널 매도",
        category="risk_management",
        chart_generator=lambda: _load_fixture("upper_touch_sell"),
        backtest_params={
            **_BASE_PARAMS,
            "stop_loss_pct": 5.0,
        },
        expectation=ScenarioExpectation(
            min_trades=2,  # 매수 + 매도
            must_have_reasons=["signal"],
        ),
        market_context="Amazon(AMZN) 실제 일봉 데이터. "
            "조정 구간에서 볼린저 하단 반등 매수 후, 실적 호조로 상단밴드 돌파 시 매도.",
        test_point="볼린저 전략의 핵심인 '상단 도달 → 익절 매도'가 손절보다 먼저 작동하는지 확인. "
            "리스크 관리(stop_loss)가 설정되어 있어도 시그널 매도가 우선하는 시나리오.",
        expected_behavior="매수 + 매도 최소 2건 발생. 마지막 매도의 사유는 'signal'(상단 도달).",
        key_params={"stop_loss_pct": "5.0%"},
        data_source="real",
    ),
    # 6. 하단 반등 → 손절선 미도달 → 시그널 매도
    Scenario(
        name="v_recovery",
        description="하단 반등 매수 → 손절선 미도달 → 시그널 매도",
        category="risk_management",
        chart_generator=lambda: _load_fixture("v_recovery"),
        backtest_params={
            **_BASE_PARAMS,
            "stop_loss_pct": 5.0,
        },
        expectation=ScenarioExpectation(
            must_not_have_reasons=["stop_loss"],
        ),
        market_context="Coca-Cola(KO) 실제 일봉 데이터. "
            "안정적인 소비재 대형주로 하단 반등 매수 후 손절선(5%)에 도달하지 않고 "
            "상단밴드까지 회복하여 시그널 매도 성공.",
        test_point="손절선에 근접하지만 도달하지 않는 경우, 불필요한 손절이 발생하지 않고 "
            "정상적인 시그널 매도로 이익 실현이 가능한지 확인.",
        expected_behavior="안정적 상승으로 손절선(5%) 미도달. 'stop_loss' 매도 없음.",
        key_params={"stop_loss_pct": "5.0%"},
        data_source="real",
    ),
    # 7. 하락 → 손절 발동
    Scenario(
        name="gradual_decline",
        description="하락 추세 — 손절 발동",
        category="risk_management",
        chart_generator=lambda: _load_fixture("gradual_decline"),
        backtest_params={
            **_BASE_PARAMS,
            "stop_loss_pct": 5.0,
        },
        expectation=ScenarioExpectation(
            must_have_reasons=["stop_loss"],
        ),
        market_context="Intel(INTC) 2024년 Q3 실제 일봉 데이터. "
            "반도체 업황 둔화로 주가가 $31→$23 하락(-25.8%). "
            "하단 반등 매수 후 다음 날 5% 이상 급락하여 손절 발동.",
        test_point="시나리오 6(v_recovery)과 짝으로 손절선을 넘었을 때 정확히 발동하는지 확인. "
            "전략의 방어 효과: B&H -25.8% vs 전략 -0.5%.",
        expected_behavior="매수가 대비 5% 이상 하락하여 'stop_loss' 매도가 반드시 발동.",
        key_params={"stop_loss_pct": "5.0%"},
        data_source="real",
    ),
    # 8. 보유기간 초과
    Scenario(
        name="long_holding",
        description="보유기간 초과 — max_holding 매도",
        category="risk_management",
        chart_generator=lambda: _load_fixture("long_holding"),
        backtest_params={
            **_BASE_PARAMS,
            "max_holding_days": 10,
        },
        expectation=ScenarioExpectation(
            must_have_reasons=["max_holding"],
        ),
        market_context="Disney(DIS) 실제 일봉 데이터. "
            "하단 반등 매수 후 밴드 중앙부에서 횡보하여 상단/하단 모두 닿지 않는 교착 상태.",
        test_point="볼린저 전략 특성상 밴드 중앙 횡보 시 매매 시그널이 없어 포지션이 고착될 수 있음. "
            "max_holding_days가 이 교착 상태를 해소하는지 확인.",
        expected_behavior="10일 보유 후 상단/하단 터치 없이 시간이 초과하여 "
            "'max_holding' 사유로 강제 매도.",
        key_params={"max_holding_days": "10일"},
        data_source="real",
    ),
    # 9. 소폭 수익 매도 보류 → 더 높은 가격에 매도 성공
    Scenario(
        name="small_profit_block",
        description="소폭 수익 매도 보류 → 수익률 개선",
        category="signal_quality",
        chart_generator=lambda: _load_fixture("small_profit_block"),
        backtest_params={
            **_BASE_PARAMS,
            "min_profit_pct": 4.0,
        },
        expectation=ScenarioExpectation(
            must_have_reasons=["signal"],
            custom_check=_check_min_profit_improvement,
        ),
        market_context="AMD 실제 일봉 데이터. "
            "하단 반등 매수($110) 후 첫 상단밴드 도달 시 수익률 +3.6%로 "
            "min_profit_pct(4%) 미만이어서 매도 보류. "
            "다음 날 $115(+4.5%)에 기준 초과하여 매도 성공.",
        test_point="min_profit_pct 게이트가 조기 매도를 방지하여 수익률을 개선하는지 확인. "
            "기준 미만 수익에서 매도를 보류하고, 기준 초과 시 매도 실행.",
        expected_behavior="첫 상단 도달(+3.6%)은 4% 미만이므로 보류. "
            "다음 상단 도달(+4.5%)에서 기준 초과하여 'signal' 매도. "
            "min_profit 미적용 대비 수익률 개선.",
        key_params={"min_profit_pct": "4.0%"},
        data_source="real",
    ),
    # 10. 손실 상태 매도 허용
    Scenario(
        name="loss_sell_allowed",
        description="손실 상태 매도 허용 — 수익률 게이트 미적용",
        category="signal_quality",
        chart_generator=lambda: _load_fixture("loss_sell_allowed"),
        backtest_params={
            **_BASE_PARAMS,
            "min_profit_pct": 4.0,
        },
        expectation=ScenarioExpectation(
            must_have_reasons=["signal"],
        ),
        market_context="Meta(META) 실제 일봉 데이터. "
            "하단 반등 매수 후 실적 쇼크로 하락하여 손실 상태(-11%)에서 밴드가 수축. "
            "상단밴드가 매수가 아래로 내려와 현재가가 상단밴드를 돌파하는 역전 상황.",
        test_point="min_profit_pct 게이트는 '소액 이익에서의 조기 매도'만 방지하는 것이 목적. "
            "손실 상태(수익률 < 0%)에서는 게이트가 적용되지 않아야 함 — 탈출 기회를 놓치면 안 됨.",
        expected_behavior="수익률이 마이너스이므로 min_profit_pct 조건(0 <= profit < 4%)에 해당하지 않음. "
            "상단 도달 시 정상적으로 'signal' 매도 실행.",
        key_params={"min_profit_pct": "4.0%", "실제 수익률": "~-11%"},
        data_source="real",
    ),
]
