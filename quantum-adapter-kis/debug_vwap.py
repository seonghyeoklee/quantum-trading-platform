#!/usr/bin/env python3
"""
VWAP 전략 디버깅 - 왜 신호가 생성되지 않는지 확인
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

def convert_to_market_data(row) -> OverseasMarketData:
    """CSV 행을 OverseasMarketData 객체로 변환"""
    return OverseasMarketData(
        symbol=row['symbol'],
        exchange=ExchangeType.NAS,
        timestamp=datetime.now(),
        current_price=float(row['price']),
        volume=int(row['volume']),
        change=0.0,
        change_percent=float(row['change_percent']),
        high_price=float(row['price']) * 1.005,
        low_price=float(row['price']) * 0.995,
        open_price=float(row['price']),
        previous_close=float(row['price']) * (1 - row['change_percent']/100)
    )

def debug_vwap_strategy():
    """VWAP 전략 디버깅"""
    print("🔍 VWAP 전략 디버깅 시작")

    # 데이터 로드
    csv_path = "logs/trading/data/TSLA_vwap_data_20250919_223603.csv"
    if not os.path.exists(csv_path):
        print(f"❌ 파일 없음: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    print(f"✅ 데이터 로드: {len(df)} rows")

    # 전략 초기화
    strategy = VWAPStrategy()
    print(f"📋 전략 설정: {strategy.config}")

    # 처음 1000개 데이터로 테스트 (50개 이후부터 신호 가능)
    for idx, row in df.head(1000).iterrows():
        market_data = convert_to_market_data(row)

        # analyze_signal 전에 상태 확인
        signal = strategy.analyze_signal(market_data)

        if idx < 10 or idx == 50 or idx == 100:  # 처음 10개 + 50, 100번째 상세 출력
            print(f"\n[{idx}] 가격: ${row['price']:.3f}")
            print(f"    VWAP: {strategy.current_vwap:.3f}")
            print(f"    Upper/Lower: {strategy.upper_band:.3f} / {strategy.lower_band:.3f}")
            print(f"    데이터 포인트: {len(strategy.vwap_data_points)}")
            print(f"    최소 필요: {strategy.config['min_data_points']}")
            print(f"    신호: {signal}")

        if signal:
            print(f"🎯 신호 발견! [{idx}] {signal.signal_type.value} | 신뢰도: {signal.confidence:.3f}")
            break

    # 분석 정보 출력
    analysis = strategy.get_current_analysis()
    print(f"\n📊 최종 분석 상태:")
    for key, value in analysis.items():
        print(f"    {key}: {value}")

if __name__ == "__main__":
    debug_vwap_strategy()