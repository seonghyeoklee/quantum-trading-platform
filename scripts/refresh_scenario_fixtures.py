#!/usr/bin/env python3
"""시나리오 fixture 데이터 다운로드 + JSON 저장.

yfinance에서 실제 과거 일봉 데이터를 다운로드하여
tests/fixtures/scenario_charts/{name}.json 파일로 저장한다.

Usage:
    uv run python scripts/refresh_scenario_fixtures.py
"""

import json
import sys
from pathlib import Path

# 프로젝트 루트를 PYTHONPATH에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.trading.backtest import fetch_chart_from_yfinance

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "scenario_charts"

# 시나리오별 종목/기간 정의
# (name, ticker, start_YYYYMMDD, end_YYYYMMDD)
SCENARIO_SOURCES: list[tuple[str, str, str, str]] = [
    # 1. largecap_low_vol — T-Bill ETF 초저변동 (밴드폭 < 3%)
    ("largecap_low_vol", "BIL", "20250601", "20250901"),
    # 4. narrow_oscillation — 단기 국채 ETF 초저변동 (밴드폭 < 3%)
    ("narrow_oscillation", "SHV", "20250601", "20250901"),
    # 5. upper_touch_sell — 하단 반등 매수 → 상단 도달 시그널 매도
    ("upper_touch_sell", "AMZN", "20250701", "20251001"),
    # 6. v_recovery — 하단 반등 매수 → 손절선 미도달 → 상단 시그널 매도
    ("v_recovery", "KO", "20250101", "20250401"),
    # 7. gradual_decline — 하단 반등 매수 → 5% 이상 하락 → 손절
    ("gradual_decline", "INTC", "20240701", "20241001"),
    # 8. long_holding — 하단 반등 매수 → 밴드 중앙 교착 → 보유기간 초과
    ("long_holding", "DIS", "20250101", "20250401"),
    # 9. small_profit_block — 매수 후 소폭 상승 → min_profit 게이트로 매도 보류
    ("small_profit_block", "AMD", "20250101", "20250401"),
    # 10. loss_sell_allowed — 매수 후 하락 → 손실 상태 상단 도달 → 매도 허용
    ("loss_sell_allowed", "META", "20250101", "20250601"),
]


def main() -> None:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

    for name, ticker, start, end in SCENARIO_SOURCES:
        print(f"  Downloading {name}: {ticker} {start}~{end} ...", end=" ")
        chart = fetch_chart_from_yfinance(ticker, start, end)
        if not chart:
            print(f"EMPTY — skipping")
            continue

        data = {
            "ticker": ticker,
            "start": start,
            "end": end,
            "chart": [
                {
                    "date": c.date,
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume,
                }
                for c in chart
            ],
        }

        out_path = FIXTURE_DIR / f"{name}.json"
        out_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        print(f"OK ({len(chart)} bars) → {out_path.name}")

    print("\nDone.")


if __name__ == "__main__":
    main()
