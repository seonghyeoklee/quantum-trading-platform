"""일일 매매 저널 리포트 생성 스크립트

Usage:
    uv run python scripts/generate_daily_report.py              # 오늘
    uv run python scripts/generate_daily_report.py 2026-02-14   # 특정 날짜
"""

import sys
from datetime import date

from app.trading.journal import TradingJournal


def main() -> None:
    if len(sys.argv) > 1:
        try:
            d = date.fromisoformat(sys.argv[1])
        except ValueError:
            print(f"잘못된 날짜 형식: {sys.argv[1]} (YYYY-MM-DD)")
            sys.exit(1)
    else:
        d = date.today()

    journal = TradingJournal()
    events = journal.read_events(d)

    if not events:
        print(f"{d.isoformat()}: 기록된 이벤트 없음")
        # 빈 리포트라도 생성
        path = journal.generate_daily_report(d)
        print(f"빈 리포트 생성: {path}")
        return

    print(f"{d.isoformat()}: {len(events)}건 이벤트")

    signals = [e for e in events if e.event_type == "signal"]
    orders = [e for e in events if e.event_type in ("order", "force_close")]
    buys = [o for o in orders if o.side == "buy"]
    sells = [o for o in orders if o.side == "sell"]

    print(f"  시그널: {len(signals)}건")
    print(f"  매수: {len(buys)}건")
    print(f"  매도: {len(sells)}건")

    path = journal.generate_daily_report(d)
    print(f"리포트 생성: {path}")


if __name__ == "__main__":
    main()
