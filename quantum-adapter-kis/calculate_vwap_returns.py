#!/usr/bin/env python3
"""
VWAP 전략 수익률 계산
고신뢰도 신호(≥0.8)의 실제 수익률 분석
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def calculate_vwap_returns():
    """VWAP 전략 수익률 계산"""
    print("💰 VWAP 전략 수익률 계산")
    print("=" * 60)

    # 원본 로그 로드
    csv_path = "logs/trading/data/TSLA_vwap_data_20250919_223603.csv"
    if not os.path.exists(csv_path):
        print(f"❌ 파일 없음: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    print(f"✅ 데이터 로드: {len(df):,} rows")

    # 신호 데이터 필터링
    signal_data = df[df['signal_type'].notna() & (df['signal_type'] != '')].copy()
    high_conf_signals = signal_data[signal_data['confidence'] >= 0.8].copy()

    print(f"📊 전체 신호: {len(signal_data):,}")
    print(f"📊 고신뢰도 신호 (≥0.8): {len(high_conf_signals):,}")

    if len(high_conf_signals) == 0:
        print("❌ 고신뢰도 신호가 없습니다.")
        return

    # 타임스탬프를 datetime으로 변환
    high_conf_signals['timestamp'] = pd.to_datetime(high_conf_signals['timestamp'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # 수익률 계산을 위한 리스트
    trades = []
    current_position = None
    entry_price = 0
    entry_time = None

    print(f"\n🔄 거래 시뮬레이션 시작...")

    for idx, signal in high_conf_signals.iterrows():
        signal_type = signal['signal_type']
        price = signal['price']
        timestamp = signal['timestamp']
        confidence = signal['confidence']

        if signal_type == '매수' and current_position != 'LONG':
            # 매수 진입
            if current_position == 'SHORT':
                # 공매도 포지션 청산
                profit = entry_price - price
                profit_pct = (profit / entry_price) * 100
                trades.append({
                    'type': 'SHORT',
                    'entry_price': entry_price,
                    'exit_price': price,
                    'entry_time': entry_time,
                    'exit_time': timestamp,
                    'profit': profit,
                    'profit_pct': profit_pct,
                    'confidence': confidence
                })

            # 새로운 매수 포지션
            current_position = 'LONG'
            entry_price = price
            entry_time = timestamp

        elif signal_type == '매도' and current_position != 'SHORT':
            # 매도 진입
            if current_position == 'LONG':
                # 매수 포지션 청산
                profit = price - entry_price
                profit_pct = (profit / entry_price) * 100
                trades.append({
                    'type': 'LONG',
                    'entry_price': entry_price,
                    'exit_price': price,
                    'entry_time': entry_time,
                    'exit_time': timestamp,
                    'profit': profit,
                    'profit_pct': profit_pct,
                    'confidence': confidence
                })

            # 새로운 공매도 포지션
            current_position = 'SHORT'
            entry_price = price
            entry_time = timestamp

    # 마지막 포지션 정리 (데이터 끝 가격으로)
    if current_position and len(df) > 0:
        final_price = df['price'].iloc[-1]
        final_time = df['timestamp'].iloc[-1]

        if current_position == 'LONG':
            profit = final_price - entry_price
            profit_pct = (profit / entry_price) * 100
        else:  # SHORT
            profit = entry_price - final_price
            profit_pct = (profit / entry_price) * 100

        trades.append({
            'type': current_position,
            'entry_price': entry_price,
            'exit_price': final_price,
            'entry_time': entry_time,
            'exit_time': final_time,
            'profit': profit,
            'profit_pct': profit_pct,
            'confidence': 0.8  # 기본값
        })

    if not trades:
        print("❌ 완료된 거래가 없습니다.")
        return

    # 거래 결과 분석
    trades_df = pd.DataFrame(trades)

    print(f"\n📈 거래 결과 분석")
    print(f"=" * 40)
    print(f"총 거래 수: {len(trades_df)}")

    # 수익 거래 vs 손실 거래
    profitable_trades = trades_df[trades_df['profit_pct'] > 0]
    losing_trades = trades_df[trades_df['profit_pct'] <= 0]

    print(f"수익 거래: {len(profitable_trades)} ({len(profitable_trades)/len(trades_df)*100:.1f}%)")
    print(f"손실 거래: {len(losing_trades)} ({len(losing_trades)/len(trades_df)*100:.1f}%)")

    # 수익률 통계
    total_return_pct = trades_df['profit_pct'].sum()
    avg_return_pct = trades_df['profit_pct'].mean()
    median_return_pct = trades_df['profit_pct'].median()
    max_return_pct = trades_df['profit_pct'].max()
    min_return_pct = trades_df['profit_pct'].min()

    print(f"\n💰 수익률 분석")
    print(f"=" * 40)
    print(f"총 수익률: {total_return_pct:+.2f}%")
    print(f"평균 수익률: {avg_return_pct:+.3f}%")
    print(f"중간 수익률: {median_return_pct:+.3f}%")
    print(f"최대 수익률: {max_return_pct:+.2f}%")
    print(f"최대 손실률: {min_return_pct:+.2f}%")

    # 거래 타입별 분석
    if len(trades_df[trades_df['type'] == 'LONG']) > 0:
        long_trades = trades_df[trades_df['type'] == 'LONG']
        long_return = long_trades['profit_pct'].sum()
        print(f"\n📈 매수 거래 분석")
        print(f"   거래 수: {len(long_trades)}")
        print(f"   총 수익률: {long_return:+.2f}%")
        print(f"   평균 수익률: {long_trades['profit_pct'].mean():+.3f}%")
        print(f"   승률: {len(long_trades[long_trades['profit_pct'] > 0])/len(long_trades)*100:.1f}%")

    if len(trades_df[trades_df['type'] == 'SHORT']) > 0:
        short_trades = trades_df[trades_df['type'] == 'SHORT']
        short_return = short_trades['profit_pct'].sum()
        print(f"\n📉 공매도 거래 분석")
        print(f"   거래 수: {len(short_trades)}")
        print(f"   총 수익률: {short_return:+.2f}%")
        print(f"   평균 수익률: {short_trades['profit_pct'].mean():+.3f}%")
        print(f"   승률: {len(short_trades[short_trades['profit_pct'] > 0])/len(short_trades)*100:.1f}%")

    # 거래 비용 고려 (수수료 + 슬리피지)
    commission_rate = 0.001  # 0.1%
    slippage_rate = 0.0005   # 0.05%
    total_cost_per_trade = (commission_rate + slippage_rate) * 2  # 매수/매도 양방향

    total_cost_pct = len(trades_df) * total_cost_per_trade * 100
    net_return_pct = total_return_pct - total_cost_pct

    print(f"\n💸 거래 비용 분석")
    print(f"=" * 40)
    print(f"총 거래 횟수: {len(trades_df)}")
    print(f"거래당 비용: {total_cost_per_trade*100:.2f}% (수수료 + 슬리피지)")
    print(f"총 거래 비용: -{total_cost_pct:.2f}%")
    print(f"순 수익률: {net_return_pct:+.2f}%")

    # 투자 시뮬레이션 (50만원 기준)
    initial_capital = 500_000  # 50만원
    final_capital = initial_capital * (1 + net_return_pct / 100)
    profit_krw = final_capital - initial_capital

    print(f"\n🏦 투자 시뮬레이션 (50만원 기준)")
    print(f"=" * 40)
    print(f"초기 자본: {initial_capital:,}원")
    print(f"최종 자본: {final_capital:,.0f}원")
    print(f"손익: {profit_krw:+,.0f}원")

    # 기존 전략 대비 비교 (6,290개 신호)
    old_strategy_trades = len(signal_data)  # 모든 신호를 거래로 가정
    old_strategy_cost = old_strategy_trades * total_cost_per_trade * 100

    print(f"\n⚖️  기존 전략 대비 비교")
    print(f"=" * 40)
    print(f"기존 전략 거래 비용: -{old_strategy_cost:.1f}% ({old_strategy_trades}회 거래)")
    print(f"새 전략 거래 비용: -{total_cost_pct:.1f}% ({len(trades_df)}회 거래)")
    print(f"비용 절약: {old_strategy_cost - total_cost_pct:.1f}%p")

    # 상위 수익 거래 표시
    print(f"\n🏆 상위 수익 거래 (Top 5)")
    print(f"=" * 60)
    top_trades = trades_df.nlargest(5, 'profit_pct')
    for idx, trade in top_trades.iterrows():
        duration = trade['exit_time'] - trade['entry_time']
        print(f"   {trade['type']} | {trade['profit_pct']:+.2f}% | "
              f"진입: ${trade['entry_price']:.2f} → 청산: ${trade['exit_price']:.2f} | "
              f"기간: {duration}")

    # 최악 손실 거래 표시
    print(f"\n💥 최대 손실 거래 (Bottom 3)")
    print(f"=" * 60)
    worst_trades = trades_df.nsmallest(3, 'profit_pct')
    for idx, trade in worst_trades.iterrows():
        duration = trade['exit_time'] - trade['entry_time']
        print(f"   {trade['type']} | {trade['profit_pct']:+.2f}% | "
              f"진입: ${trade['entry_price']:.2f} → 청산: ${trade['exit_price']:.2f} | "
              f"기간: {duration}")

    return {
        'total_return': net_return_pct,
        'trades_count': len(trades_df),
        'win_rate': len(profitable_trades)/len(trades_df)*100,
        'avg_return': avg_return_pct,
        'total_cost': total_cost_pct
    }

if __name__ == "__main__":
    calculate_vwap_returns()