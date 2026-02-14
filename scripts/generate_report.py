#!/usr/bin/env python
"""포트폴리오 최적화 결과 리포트 생성 — JSONL 로그 → Markdown 보고서"""

import json
import sys
from datetime import datetime


def load_log(log_path: str) -> list[dict]:
    entries = []
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def find_best(entries: list[dict]) -> dict | None:
    if not entries:
        return None
    return max(entries, key=lambda e: e["portfolio_summary"]["avg_return_pct"])


def generate_report(log_path: str, config_path: str, output_path: str):
    entries = load_log(log_path)
    if not entries:
        print("로그가 비어있습니다.", file=sys.stderr)
        sys.exit(1)

    with open(config_path) as f:
        final_config = json.load(f)

    best = find_best(entries)
    first = entries[0]

    period = first["period"]
    stock_names = ", ".join(s["name"] for s in first["stocks"])

    lines: list[str] = []
    w = lines.append

    # --- 헤더 ---
    w("# 포트폴리오 백테스트 최적화 보고서")
    w("")
    w(f"- **생성일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    w(f"- **종목**: {stock_names} ({first['stock_count']}종목)")
    w(f"- **기간**: {period}")
    w(f"- **반복 횟수**: {len(entries)}회")
    w(f"- **포트폴리오 평균 B&H**: {first['portfolio_summary']['avg_buy_and_hold_pct']}%")
    w("")

    # --- 요약 ---
    w("## 최적화 요약")
    w("")
    f_s = first["portfolio_summary"]
    b_s = best["portfolio_summary"]

    def delta(a, b):
        d = b - a
        return f"{'+' if d >= 0 else ''}{d:.2f}"

    w("| 지표 | 초기 (1회차) | 최고 기록 | 변화 |")
    w("|------|------------|----------|------|")
    w(f"| 평균 수익률 | {f_s['avg_return_pct']}% | **{b_s['avg_return_pct']}%** | {delta(f_s['avg_return_pct'], b_s['avg_return_pct'])}%p |")
    w(f"| 최악 MDD | {f_s['worst_mdd_pct']}% | {b_s['worst_mdd_pct']}% | {delta(f_s['worst_mdd_pct'], b_s['worst_mdd_pct'])}%p |")

    sf = f_s["avg_sharpe"] if f_s["avg_sharpe"] is not None else 0
    sb = b_s["avg_sharpe"] if b_s["avg_sharpe"] is not None else 0
    w(f"| 평균 Sharpe | {sf} | {sb} | {delta(sf, sb)} |")
    w(f"| 평균 승률 | {f_s['avg_win_rate']}% | {b_s['avg_win_rate']}% | {delta(f_s['avg_win_rate'], b_s['avg_win_rate'])}%p |")
    w(f"| 총 거래 | {f_s['total_trades']} | {b_s['total_trades']} | {delta(f_s['total_trades'], b_s['total_trades'])} |")
    w("")

    # --- 반복별 포트폴리오 결과 ---
    w("## 반복별 포트폴리오 결과")
    w("")
    w("| # | short | long | adv | RSI | vol_ma | 주문금액 | 평균수익률 | 최악MDD | Sharpe | 승률 | 거래 |")
    w("|---|-------|------|-----|-----|--------|---------|----------|--------|--------|------|------|")

    for e in entries:
        p = e["params"]
        s = e["portfolio_summary"]
        it = e.get("iteration", "?")
        adv = "O" if p["use_advanced"] else "X"
        sharpe = s["avg_sharpe"] if s["avg_sharpe"] is not None else "-"
        rsi_info = f"{p['rsi_period']}({p['rsi_oversold']}/{p['rsi_overbought']})"
        amt = f"{p['order_amount']:,}"

        is_best = s["avg_return_pct"] == b_s["avg_return_pct"]
        m = " **" if is_best else ""
        me = "**" if is_best else ""

        w(f"| {it} | {p['short_period']} | {p['long_period']} | {adv} | {rsi_info} | {p['volume_ma_period']} | {amt} | {m}{s['avg_return_pct']}%{me} | {s['worst_mdd_pct']}% | {sharpe} | {s['avg_win_rate']}% | {s['total_trades']} |")

    w("")

    # --- 최적 결과 종목별 상세 ---
    w("## 최적 결과 — 종목별 상세")
    w("")
    w("| 종목 | 섹터 | 수익률 | B&H | 초과수익 | MDD | Sharpe | 승률 | 거래 |")
    w("|------|------|--------|-----|---------|-----|--------|------|------|")

    for st in best["stocks"]:
        excess = round(st["total_return_pct"] - st["buy_and_hold_pct"], 2)
        sharpe = st["sharpe_ratio"] if st["sharpe_ratio"] is not None else "-"
        win = f"{st['win_rate']}%" if st["trade_count"] > 0 else "-"
        w(f"| {st['name']} | {st['sector']} | {st['total_return_pct']}% | {st['buy_and_hold_pct']}% | {excess}%p | {st['max_drawdown_pct']}% | {sharpe} | {win} | {st['trade_count']} |")

    w("")

    # --- 최적 파라미터 ---
    w("## 최적 파라미터")
    w("")
    best_p = best["params"]
    w("```json")
    w(json.dumps({
        "short_period": best_p["short_period"],
        "long_period": best_p["long_period"],
        "use_advanced": best_p["use_advanced"],
        "rsi_period": best_p["rsi_period"],
        "rsi_overbought": best_p["rsi_overbought"],
        "rsi_oversold": best_p["rsi_oversold"],
        "volume_ma_period": best_p["volume_ma_period"],
        "order_amount": best_p["order_amount"],
    }, indent=2))
    w("```")
    w("")

    # --- 종목별 거래 내역 (최적 결과) ---
    w("## 최적 결과 거래 내역")
    w("")
    for st in best["stocks"]:
        if not st["trades"]:
            continue
        w(f"### {st['name']} ({st['code']}) — {st['sector']}")
        w("")
        w("| 날짜 | 방향 | 가격 | 수량 |")
        w("|------|------|------|------|")
        for t in st["trades"]:
            side_kr = "매수" if t["side"] == "buy" else "매도"
            w(f"| {t['date']} | {side_kr} | {t['price']:,}원 | {t['qty']}주 |")
        w("")

    # --- 수익률 추이 ---
    w("## 포트폴리오 평균 수익률 추이")
    w("")
    w("```")
    returns = [e["portfolio_summary"]["avg_return_pct"] for e in entries]
    if returns:
        min_r = min(min(returns), 0)
        max_r = max(max(returns), 1)
        bar_width = 40

        for e in entries:
            it = e.get("iteration", "?")
            r = e["portfolio_summary"]["avg_return_pct"]
            if max_r - min_r > 0:
                normalized = (r - min_r) / (max_r - min_r)
            else:
                normalized = 0.5
            bar_len = int(normalized * bar_width)
            bar = "█" * bar_len + "░" * (bar_width - bar_len)
            w(f"  #{it:>2} |{bar}| {r:>7.2f}%")
    w("```")
    w("")

    # --- 주의사항 ---
    w("## 주의사항")
    w("")
    w("- 과거 데이터 기반 최적화 결과는 미래 수익을 보장하지 않습니다 (과적합 위험)")
    w("- 동일 파라미터를 전 종목에 적용했으므로 개별 종목 최적값과 다를 수 있습니다")
    w("- 실전 적용 전 다른 기간으로 out-of-sample 검증을 권장합니다")
    w("- 거래 수수료(0.015%), 슬리피지는 반영되지 않았습니다")
    w("")
    w("---")
    w("*Generated by quantum-trading-platform backtest optimizer*")

    report = "\n".join(lines)
    with open(output_path, "w") as f:
        f.write(report)

    print(f"리포트 생성: {output_path}")


def main():
    log_path = sys.argv[1] if len(sys.argv) > 1 else "scripts/optimize_log.jsonl"
    config_path = sys.argv[2] if len(sys.argv) > 2 else "scripts/backtest_config.json"
    output_path = sys.argv[3] if len(sys.argv) > 3 else "scripts/optimize_report.md"
    generate_report(log_path, config_path, output_path)


if __name__ == "__main__":
    main()
