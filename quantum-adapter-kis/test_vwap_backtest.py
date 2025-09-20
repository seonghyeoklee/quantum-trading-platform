#!/usr/bin/env python3
"""
VWAP 전략 백테스트 - 기존 로그 데이터 사용
수정된 파라미터 효과 검증
"""

import pandas as pd
import sys
import os
from pathlib import Path

# 프로젝트 경로 추가
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from overseas_trading_system.strategies.vwap_strategy import VWAPStrategy
from overseas_trading_system.core.overseas_data_types import OverseasMarketData, ExchangeType, TradingSession
from datetime import datetime

def load_historical_data(csv_path: str) -> pd.DataFrame:
    """기존 CSV 로그에서 데이터 로드"""
    try:
        df = pd.read_csv(csv_path)
        print(f"✅ 데이터 로드 완료: {len(df)} rows")
        return df
    except Exception as e:
        print(f"❌ 데이터 로드 실패: {e}")
        return None

def convert_to_market_data(row) -> OverseasMarketData:
    """CSV 행을 OverseasMarketData 객체로 변환"""
    return OverseasMarketData(
        symbol=row['symbol'],
        exchange=ExchangeType.NAS,
        timestamp=datetime.now(),
        current_price=float(row['price']),
        volume=int(row['volume']),
        change=0.0,  # CSV에 없으므로 기본값
        change_percent=float(row['change_percent']),
        high_price=float(row['price']) * 1.005,  # 추정값
        low_price=float(row['price']) * 0.995,   # 추정값
        open_price=float(row['price']),    # 추정값
        previous_close=float(row['price']) * (1 - row['change_percent']/100)
    )

def run_vwap_backtest(csv_path: str):
    """VWAP 전략 백테스트 실행"""
    print("🚀 VWAP 전략 백테스트 시작")
    print("=" * 50)

    # 데이터 로드
    df = load_historical_data(csv_path)
    if df is None:
        return

    # 기존 파라미터로 전략 초기화
    old_config = {
        'std_multiplier': 2.0,
        'volume_threshold': 1.5,
        'min_confidence': 0.7,
        'min_data_points': 20
    }
    old_strategy = VWAPStrategy(old_config)

    # 새 파라미터로 전략 초기화 (수정된 기본값 사용)
    new_strategy = VWAPStrategy()

    # 결과 저장
    old_signals = []
    new_signals = []

    print("📊 백테스트 진행 중...")

    # 데이터 순회하며 신호 생성 (14000라인부터 시작 - 신호 발생 구간)
    start_idx = 14000
    test_data = df.iloc[start_idx:start_idx+5000]  # 5000개만 테스트

    for idx, row in test_data.iterrows():
        if (idx - start_idx) % 1000 == 0:
            print(f"진행률: {(idx-start_idx)/len(test_data)*100:.1f}%")

        market_data = convert_to_market_data(row)

        # 기존 전략 신호
        old_signal = old_strategy.analyze_signal(market_data)
        if old_signal:
            old_signals.append({
                'timestamp': row['timestamp'],
                'price': row['price'],
                'signal_type': old_signal.signal_type.value,
                'confidence': old_signal.confidence,
                'reason': old_signal.reason
            })

        # 새 전략 신호
        new_signal = new_strategy.analyze_signal(market_data)
        if new_signal:
            new_signals.append({
                'timestamp': row['timestamp'],
                'price': row['price'],
                'signal_type': new_signal.signal_type.value,
                'confidence': new_signal.confidence,
                'reason': new_signal.reason
            })

    # 결과 분석
    print("\n" + "=" * 50)
    print("📈 백테스트 결과 비교")
    print("=" * 50)

    print(f"📊 전체 데이터 포인트: {len(df):,}")
    print(f"📊 테스트 데이터 포인트: {len(test_data):,}")
    print(f"⏱️  테스트 기간: {test_data['timestamp'].iloc[0]} ~ {test_data['timestamp'].iloc[-1]}")

    print(f"\n🔴 기존 파라미터 (min_confidence=0.7, std_multiplier=2.0):")
    print(f"   총 신호 수: {len(old_signals):,}")
    print(f"   신호 밀도: {len(old_signals)/len(test_data)*100:.2f}%")

    print(f"\n🔵 새 파라미터 (min_confidence=0.8, std_multiplier=2.5):")
    print(f"   총 신호 수: {len(new_signals):,}")
    print(f"   신호 밀도: {len(new_signals)/len(test_data)*100:.2f}%")

    if len(old_signals) > 0:
        reduction_rate = (1 - len(new_signals)/len(old_signals)) * 100
        print(f"\n📉 신호 감소율: {reduction_rate:.1f}%")

    # 신호 타입별 분석
    if new_signals:
        new_df = pd.DataFrame(new_signals)
        buy_signals = len(new_df[new_df['signal_type'] == 'BUY'])
        sell_signals = len(new_df[new_df['signal_type'] == 'SELL'])
        avg_confidence = new_df['confidence'].mean()

        print(f"\n🔵 새 전략 상세 분석:")
        print(f"   매수 신호: {buy_signals}")
        print(f"   매도 신호: {sell_signals}")
        print(f"   평균 신뢰도: {avg_confidence:.3f}")

        # 신뢰도 분포
        high_conf = len(new_df[new_df['confidence'] >= 0.9])
        med_conf = len(new_df[(new_df['confidence'] >= 0.8) & (new_df['confidence'] < 0.9)])

        print(f"   고신뢰도 (≥0.9): {high_conf}")
        print(f"   중신뢰도 (0.8-0.9): {med_conf}")

    # 최근 신호 몇 개 출력
    if new_signals:
        print(f"\n🔍 최근 신호 샘플 (최대 5개):")
        for signal in new_signals[-5:]:
            print(f"   {signal['timestamp']} | {signal['signal_type']} | "
                  f"신뢰도: {signal['confidence']:.3f} | {signal['reason'][:50]}...")

if __name__ == "__main__":
    # 기존 TSLA 로그 파일 사용
    csv_path = "logs/trading/data/TSLA_vwap_data_20250919_223603.csv"

    if os.path.exists(csv_path):
        run_vwap_backtest(csv_path)
    else:
        print(f"❌ 로그 파일을 찾을 수 없습니다: {csv_path}")
        print("다른 경로를 확인해주세요.")