#!/bin/bash
# 포트폴리오 백테스트 전략 파라미터 자동 최적화
# 사용법: ./scripts/optimize.sh [최대반복횟수]
# 예시:   ./scripts/optimize.sh 15
set -euo pipefail

cd "$(dirname "$0")/.."

MAX_ITER=${1:-15}
CONFIG="scripts/backtest_config.json"
LOG="scripts/optimize_log.jsonl"
BEST_LOG="scripts/best_result.json"

# 로그 초기화
> "$LOG"
BEST_RETURN="-999999"

STOCK_NAMES=$(python3 -c "
import json
with open('$CONFIG') as f: c = json.load(f)
print(', '.join(s['name'] for s in c['symbols']))
")

echo "============================================"
echo " 포트폴리오 백테스트 파라미터 자동 최적화"
echo " 종목: $STOCK_NAMES"
echo " 최대 반복: ${MAX_ITER}회"
echo "============================================"
echo ""

for i in $(seq 1 $MAX_ITER); do
  echo "--- [$i/$MAX_ITER] 백테스트 실행 ---"

  # 백테스트 실행 (yfinance 경고는 stderr로 버림)
  if ! RESULT=$(uv run python scripts/run_backtest.py 2>/dev/null); then
    echo "백테스트 실행 실패"
    exit 1
  fi

  # 포트폴리오 요약 추출
  SUMMARY=$(echo "$RESULT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
s = d['portfolio_summary']
p = d['params']
print(f\"  파라미터: SMA({p['short_period']},{p['long_period']}) adv={p['use_advanced']} RSI({p['rsi_period']},{p['rsi_overbought']},{p['rsi_oversold']}) vol_ma={p['volume_ma_period']} obv_ma={p.get('obv_ma_period',20)} amt={p['order_amount']:,}\")
print(f\"  포트폴리오 평균수익률: {s['avg_return_pct']}% | B&H평균: {s['avg_buy_and_hold_pct']}%\")
print(f\"  평균Sharpe: {s['avg_sharpe']} | 최악MDD: {s['worst_mdd_pct']}% | 총거래: {s['total_trades']}회 | 평균승률: {s['avg_win_rate']}%\")
print()
# 종목별 한줄 요약
for st in d['stocks']:
    ret = st['total_return_pct']
    bnh = st['buy_and_hold_pct']
    mdd = st['max_drawdown_pct']
    tc = st['trade_count']
    marker = '★' if ret > 0 else '  '
    print(f\"  {marker} {st['name']:8s} 수익:{ret:>7.2f}% | B&H:{bnh:>7.2f}% | MDD:{mdd:>5.2f}% | 거래:{tc}회\")
")

  RETURN=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['portfolio_summary']['avg_return_pct'])")

  echo "$SUMMARY"

  # 로그에 추가
  echo "$RESULT" | python3 -c "
import sys, json
r = json.load(sys.stdin)
r['iteration'] = $i
print(json.dumps(r, ensure_ascii=False))
" >> "$LOG"

  # 최고 기록 갱신
  IS_BETTER=$(python3 -c "print('yes' if $RETURN > $BEST_RETURN else 'no')")
  if [ "$IS_BETTER" = "yes" ]; then
    BEST_RETURN="$RETURN"
    echo "$RESULT" > "$BEST_LOG"
    echo "  >>> 최고 기록 갱신! (평균 수익률 ${RETURN}%) <<<"
  fi
  echo ""

  # 마지막 iteration이면 종료
  if [ "$i" -eq "$MAX_ITER" ]; then
    echo "최대 반복 도달."
    break
  fi

  # Claude에게 최적화 요청
  echo "  Claude에게 파라미터 조정 요청 중..."

  HISTORY=$(cat "$LOG")
  CURRENT_CONFIG=$(cat "$CONFIG")

  env -u CLAUDECODE claude -p "당신은 퀀트 트레이딩 포트폴리오 최적화 전문가입니다.

## 목표
- 포트폴리오 평균 수익률(avg_return_pct) 최대화 (가장 중요)
- 개별 종목 최악 MDD 30% 이하 유지
- 평균 Sharpe ratio 높을수록 좋음
- 종목별 거래 횟수 합계가 너무 적으면(< 20) 과적합 의심
- 특정 종목만 수익이 높고 나머지가 손실이면 안 됨 — 고르게 수익이 나야 좋은 파라미터

## 현재 설정 (scripts/backtest_config.json)
${CURRENT_CONFIG}

## 이번 백테스트 결과 (포트폴리오)
${RESULT}

## 지금까지 시도 이력 (${i}회차)
${HISTORY}

## 조정 가능 파라미터 (전 종목 동일 적용)
- short_period (2~15): 단기 이동평균 기간
- long_period (10~60): 장기 이동평균 기간 (short_period보다 커야 함)
- use_advanced (true/false): RSI+거래량 필터 사용 여부
- rsi_period (5~30): RSI 계산 기간
- rsi_overbought (60~85): RSI 과매수 기준
- rsi_oversold (15~40): RSI 과매도 기준
- volume_ma_period (5~40): 거래량 이동평균 기간
- obv_ma_period (5~40): OBV 이동평균 기간 (OBV > OBV_SMA면 매수 확인, OBV < OBV_SMA면 매도 확인)
- order_amount (100000~2000000): 1회 주문 금액

## 지시사항
1. 종목별 수익률 편차를 분석하세요 — 어떤 종목이 잘 되고 안 되는지
2. 이전 시도에서 수익률이 개선된 방향을 강화하세요
3. 아직 시도하지 않은 파라미터 조합을 시도하세요
4. scripts/backtest_config.json 파일을 수정하세요 (Edit 도구 사용, symbols 배열은 건드리지 마세요)
5. 수정 이유를 한 줄로 설명하세요" \
    --allowedTools "Edit,Read"

  echo ""
done

echo ""
echo "============================================"
echo " 최적화 완료"
echo "============================================"
echo ""
echo "최종 설정:"
python3 -m json.tool "$CONFIG"
echo ""
echo "최고 포트폴리오 평균 수익률:"
if [ -f "$BEST_LOG" ]; then
  python3 -c "
import sys, json
r = json.load(sys.stdin)
s = r['portfolio_summary']
print(f\"  평균 수익률: {s['avg_return_pct']}%\")
print(f\"  평균 B&H:    {s['avg_buy_and_hold_pct']}%\")
print(f\"  평균 Sharpe: {s['avg_sharpe']}\")
print(f\"  최악 MDD:    {s['worst_mdd_pct']}%\")
print(f\"  총 거래:     {s['total_trades']}회\")
print(f\"  평균 승률:   {s['avg_win_rate']}%\")
print()
for st in r['stocks']:
    print(f\"  {st['name']:8s} {st['total_return_pct']:>7.2f}%\")
" < "$BEST_LOG"
fi

# 리포트 생성
REPORT="scripts/optimize_report_$(date +%Y%m%d_%H%M%S).md"
echo ""
uv run python scripts/generate_report.py "$LOG" "$CONFIG" "$REPORT"
echo ""
echo "파일 목록:"
echo "  설정:   $CONFIG"
echo "  로그:   $LOG"
echo "  최고:   $BEST_LOG"
echo "  리포트: $REPORT"
