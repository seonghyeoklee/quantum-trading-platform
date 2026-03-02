"""시나리오 기반 자동 백테스트 — pytest 파라미터화 테스트"""

import pytest

from app.trading.scenario import SCENARIOS, run_scenario


@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s.name for s in SCENARIOS])
def test_scenario(scenario):
    result = run_scenario(scenario)
    failures = [c for c in result.checks if not c[1]]
    if failures:
        details = "\n".join(
            f"  FAIL: {name} — {detail}" for name, _, detail in failures
        )
        trades_summary = "\n".join(
            f"    [{i}] {t.side} @ {t.price} reason={t.reason} date={t.date}"
            for i, t in enumerate(result.backtest_result.trades)
        )
        pytest.fail(
            f"Scenario '{scenario.name}' ({scenario.description}):\n"
            f"{details}\n"
            f"  Trades ({result.backtest_result.trade_count}):\n{trades_summary}"
        )
