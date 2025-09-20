#!/usr/bin/env python3
"""
원본 VWAP 로그의 신호 분석
기존 파라미터로 생성된 신호를 새 파라미터 기준으로 필터링
"""

import pandas as pd
import os

def analyze_original_signals():
    """원본 로그의 신호 분석"""
    print("🔍 원본 VWAP 신호 분석")
    print("=" * 50)

    # 원본 로그 로드
    csv_path = "logs/trading/data/TSLA_vwap_data_20250919_223603.csv"
    if not os.path.exists(csv_path):
        print(f"❌ 파일 없음: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    print(f"✅ 데이터 로드: {len(df):,} rows")

    # 신호가 있는 데이터만 필터링
    signal_data = df[df['signal_type'].notna() & (df['signal_type'] != '')]
    print(f"📊 총 신호 수: {len(signal_data):,}")

    if len(signal_data) == 0:
        print("❌ 신호 데이터가 없습니다.")
        return

    # 신호 타입별 분석
    buy_signals = signal_data[signal_data['signal_type'] == '매수']
    sell_signals = signal_data[signal_data['signal_type'] == '매도']

    print(f"\n📈 신호 타입별 분석:")
    print(f"   매수 신호: {len(buy_signals):,}")
    print(f"   매도 신호: {len(sell_signals):,}")

    # 신뢰도 분포 분석
    confidence_dist = signal_data['confidence'].describe()
    print(f"\n📊 신뢰도 분포:")
    print(f"   평균: {confidence_dist['mean']:.3f}")
    print(f"   최소: {confidence_dist['min']:.3f}")
    print(f"   최대: {confidence_dist['max']:.3f}")
    print(f"   중간값: {confidence_dist['50%']:.3f}")

    # 새 파라미터 기준으로 필터링
    print(f"\n🔧 새 파라미터 기준 필터링:")

    # 1. min_confidence 0.8 이상
    high_conf_signals = signal_data[signal_data['confidence'] >= 0.8]
    print(f"   신뢰도 ≥0.8: {len(high_conf_signals):,} ({len(high_conf_signals)/len(signal_data)*100:.1f}%)")

    # 2. 매우 높은 신뢰도 (0.9 이상)
    very_high_conf = signal_data[signal_data['confidence'] >= 0.9]
    print(f"   신뢰도 ≥0.9: {len(very_high_conf):,} ({len(very_high_conf)/len(signal_data)*100:.1f}%)")

    # 3. 거래량 분석 (원본에는 volume_threshold 적용 안됨)
    if len(high_conf_signals) > 0:
        print(f"\n🔵 고신뢰도 신호 (≥0.8) 분석:")
        hc_buy = high_conf_signals[high_conf_signals['signal_type'] == '매수']
        hc_sell = high_conf_signals[high_conf_signals['signal_type'] == '매도']
        print(f"   매수: {len(hc_buy):,}")
        print(f"   매도: {len(hc_sell):,}")
        print(f"   평균 신뢰도: {high_conf_signals['confidence'].mean():.3f}")

        # 시간대별 분포
        high_conf_signals['hour'] = pd.to_datetime(high_conf_signals['timestamp']).dt.hour
        time_dist = high_conf_signals['hour'].value_counts().sort_index()
        print(f"\n⏰ 시간대별 분포 (고신뢰도):")
        for hour, count in time_dist.items():
            print(f"   {hour:02d}시: {count} 신호")

    # 신호 감소 효과 계산
    reduction_rate = (1 - len(high_conf_signals) / len(signal_data)) * 100
    print(f"\n📉 예상 신호 감소 효과:")
    print(f"   기존 신호: {len(signal_data):,}")
    print(f"   새 기준 신호: {len(high_conf_signals):,}")
    print(f"   감소율: {reduction_rate:.1f}%")

    # 샘플 신호 출력
    print(f"\n🎯 고신뢰도 신호 샘플 (최대 5개):")
    for idx, row in high_conf_signals.head().iterrows():
        print(f"   {row['timestamp']} | {row['signal_type']} | "
              f"${row['price']:.3f} | 신뢰도: {row['confidence']:.3f}")
        print(f"     사유: {row['reason'][:80]}...")

if __name__ == "__main__":
    analyze_original_signals()