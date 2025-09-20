#!/usr/bin/env python3
"""
VWAP 전략 비교 분석
기존 vs 최적화된 전략의 상세 비교
"""

import pandas as pd
import numpy as np
import os

def compare_vwap_strategies():
    """VWAP 전략 비교 분석"""
    print("⚖️  VWAP 전략 비교 분석")
    print("=" * 70)

    # 데이터 로드
    csv_path = "logs/trading/data/TSLA_vwap_data_20250919_223603.csv"
    df = pd.read_csv(csv_path)
    signal_data = df[df['signal_type'].notna() & (df['signal_type'] != '')].copy()

    # 기존 전략 (모든 신호)
    all_signals = signal_data.copy()

    # 최적화 전략 (고신뢰도만)
    high_conf_signals = signal_data[signal_data['confidence'] >= 0.8].copy()

    print(f"📊 데이터 개요")
    print(f"   전체 데이터: {len(df):,} 포인트")
    print(f"   기존 전략 신호: {len(all_signals):,}개")
    print(f"   최적화 전략 신호: {len(high_conf_signals):,}개")
    print(f"   신호 감소율: {(1-len(high_conf_signals)/len(all_signals))*100:.1f}%")

    def simulate_trading(signals, strategy_name):
        """거래 시뮬레이션"""
        if len(signals) == 0:
            return None

        signals = signals.copy()
        signals['timestamp'] = pd.to_datetime(signals['timestamp'])

        # 간단한 시뮬레이션: 매수/매도 신호를 번갈아가며 실행
        buy_signals = signals[signals['signal_type'] == '매수'].sort_values('timestamp')
        sell_signals = signals[signals['signal_type'] == '매도'].sort_values('timestamp')

        trades = []
        position = None
        entry_price = 0

        # 시간순으로 정렬
        all_signals_sorted = signals.sort_values('timestamp')

        for idx, signal in all_signals_sorted.iterrows():
            if signal['signal_type'] == '매수' and position != 'LONG':
                if position == 'SHORT':
                    # 공매도 청산
                    profit = (entry_price - signal['price']) / entry_price
                    trades.append(profit)

                # 매수 진입
                position = 'LONG'
                entry_price = signal['price']

            elif signal['signal_type'] == '매도' and position != 'SHORT':
                if position == 'LONG':
                    # 매수 청산
                    profit = (signal['price'] - entry_price) / entry_price
                    trades.append(profit)

                # 공매도 진입
                position = 'SHORT'
                entry_price = signal['price']

        return trades

    # 거래 비용 설정 (해외주식 기준)
    commission_rate = 0.0025  # 0.25% (해외주식 수수료)
    slippage_rate = 0.0005    # 0.05% (슬리피지)
    cost_per_trade = commission_rate + slippage_rate  # 0.3% per trade

    # 기존 전략 시뮬레이션
    old_trades = simulate_trading(all_signals, "기존")
    if old_trades:
        old_gross_return = sum(old_trades) * 100
        old_trade_count = len(old_trades)
        old_cost = old_trade_count * cost_per_trade * 100
        old_net_return = old_gross_return - old_cost
    else:
        old_gross_return = old_net_return = old_cost = old_trade_count = 0

    # 최적화 전략 시뮬레이션
    new_trades = simulate_trading(high_conf_signals, "최적화")
    if new_trades:
        new_gross_return = sum(new_trades) * 100
        new_trade_count = len(new_trades)
        new_cost = new_trade_count * cost_per_trade * 100
        new_net_return = new_gross_return - new_cost
    else:
        new_gross_return = new_net_return = new_cost = new_trade_count = 0

    # 결과 출력
    print(f"\n📈 기존 전략 (min_confidence=0.7)")
    print(f"=" * 50)
    print(f"   신호 수: {len(all_signals):,}개")
    print(f"   거래 수: {old_trade_count}회")
    print(f"   총 수익률: {old_gross_return:+.2f}%")
    print(f"   거래 비용: -{old_cost:.2f}%")
    print(f"   순 수익률: {old_net_return:+.2f}%")
    if old_trade_count > 0:
        print(f"   거래당 평균: {old_gross_return/old_trade_count:+.3f}%")

    print(f"\n🔵 최적화 전략 (min_confidence=0.8)")
    print(f"=" * 50)
    print(f"   신호 수: {len(high_conf_signals):,}개")
    print(f"   거래 수: {new_trade_count}회")
    print(f"   총 수익률: {new_gross_return:+.2f}%")
    print(f"   거래 비용: -{new_cost:.2f}%")
    print(f"   순 수익률: {new_net_return:+.2f}%")
    if new_trade_count > 0:
        print(f"   거래당 평균: {new_gross_return/new_trade_count:+.3f}%")

    # 비교 분석
    print(f"\n⚖️  성과 비교")
    print(f"=" * 50)

    if old_trade_count > 0 and new_trade_count > 0:
        cost_reduction = old_cost - new_cost
        performance_diff = new_net_return - old_net_return

        print(f"   거래 비용 절약: {cost_reduction:.2f}%p")
        print(f"   순 수익률 차이: {performance_diff:+.2f}%p")
        print(f"   거래 효율성: {new_gross_return/new_trade_count - old_gross_return/old_trade_count:+.3f}%p")

    # 투자 시뮬레이션 (다양한 금액)
    investment_amounts = [500_000, 1_000_000, 5_000_000, 10_000_000]

    print(f"\n💰 투자 시뮬레이션")
    print(f"=" * 70)
    print(f"{'투자금액':>10} | {'기존전략':>12} | {'최적화전략':>12} | {'차이':>12}")
    print(f"{'-'*10}|{'-'*13}|{'-'*13}|{'-'*12}")

    for amount in investment_amounts:
        old_final = amount * (1 + old_net_return/100)
        new_final = amount * (1 + new_net_return/100)
        difference = new_final - old_final

        print(f"{amount//10000:>8}만원 | {old_final//10000:>10.0f}만원 | {new_final//10000:>10.0f}만원 | {difference//10000:>+8.0f}만원")

    # 실행 가능성 분석
    print(f"\n🚀 실행 가능성 분석")
    print(f"=" * 50)

    # 분당 거래 빈도
    total_time_hours = 10.5  # 대략 10.5시간 데이터
    old_freq = len(all_signals) / (total_time_hours * 60)
    new_freq = len(high_conf_signals) / (total_time_hours * 60)

    print(f"   기존 전략 신호 빈도: {old_freq:.1f}개/분")
    print(f"   최적화 전략 신호 빈도: {new_freq:.2f}개/분")
    print(f"   실행 가능성: {'❌ 불가능' if old_freq > 1 else '✅ 가능'} → {'✅ 가능' if new_freq < 1 else '❌ 여전히 높음'}")

    # 리스크 분석
    if old_trades and new_trades:
        old_volatility = np.std(old_trades) * 100
        new_volatility = np.std(new_trades) * 100

        print(f"\n📊 리스크 분석")
        print(f"=" * 50)
        print(f"   기존 전략 변동성: {old_volatility:.2f}%")
        print(f"   최적화 전략 변동성: {new_volatility:.2f}%")
        print(f"   리스크 변화: {new_volatility - old_volatility:+.2f}%p")

    # 최종 권장사항
    print(f"\n💡 최종 권장사항")
    print(f"=" * 50)

    if new_net_return > old_net_return:
        print(f"   ✅ 최적화 전략 권장")
        print(f"   📈 순 수익률 {new_net_return - old_net_return:+.2f}%p 개선")
        print(f"   💸 거래 비용 {old_cost - new_cost:.1f}%p 절약")
        print(f"   🎯 실행 가능한 신호 빈도")
    else:
        print(f"   ⚠️  추가 최적화 필요")
        print(f"   📉 순 수익률 {new_net_return - old_net_return:+.2f}%p")

    return {
        'old_strategy': {
            'signals': len(all_signals),
            'trades': old_trade_count,
            'gross_return': old_gross_return,
            'net_return': old_net_return,
            'cost': old_cost
        },
        'new_strategy': {
            'signals': len(high_conf_signals),
            'trades': new_trade_count,
            'gross_return': new_gross_return,
            'net_return': new_net_return,
            'cost': new_cost
        }
    }

if __name__ == "__main__":
    compare_vwap_strategies()