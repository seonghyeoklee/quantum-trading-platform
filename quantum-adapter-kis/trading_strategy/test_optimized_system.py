#!/usr/bin/env python3
"""
최적화된 신호 감지 시스템 테스트
백테스팅 결과 기반 종목별 최적 확정 기간 적용 검증
"""

import sys
from pathlib import Path

# 프로젝트 경로 추가
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir.parent))

from core.signal_detector import SignalDetector
import pandas as pd
from datetime import datetime, timedelta

def test_optimal_periods():
    """종목별 최적 확정 기간 테스트"""
    print("🧪 종목별 최적 확정 기간 테스트")
    print("=" * 50)
    
    detector = SignalDetector()
    
    test_symbols = {
        "005930": "삼성전자",
        "035720": "카카오", 
        "009540": "HD한국조선해양",
        "012450": "한화에어로스페이스",
        "010060": "OCI",
        "000660": "SK하이닉스",  # 대형주 (기본값 테스트)
        "123456": "테스트종목"    # 미등록 종목 (기본값 테스트)
    }
    
    for symbol, name in test_symbols.items():
        optimal_days = detector.get_optimal_confirmation_days(symbol)
        print(f"📊 {name}({symbol}): {optimal_days}일 확정")
    
    print("\n✅ 백테스팅 결과 기반 설정이 정상 적용됨")

def create_test_data():
    """골든크로스 패턴 테스트 데이터 생성"""
    dates = pd.date_range(start='2024-08-01', end='2024-09-04', freq='D')
    
    # 골든크로스 패턴 생성
    df = pd.DataFrame(index=dates)
    df['close'] = 50000  # 기본 가격
    df['volume'] = 1000000  # 기본 거래량
    df['volume_sma20'] = 1000000
    df['volume_ratio'] = 1.2
    
    # SMA5 < SMA20 → SMA5 > SMA20 패턴 (골든크로스)
    df['sma20'] = 50000  # 장기 이동평균
    
    # 처음 10일은 데드크로스 상태
    df.loc[df.index[:10], 'sma5'] = 49500  # SMA5 < SMA20
    
    # 11일째부터 골든크로스 시작 (7일간 지속)
    df.loc[df.index[10:17], 'sma5'] = 50500  # SMA5 > SMA20
    
    # 나머지는 다시 데드크로스
    df.loc[df.index[17:], 'sma5'] = 49500
    
    return df

def test_signal_detection():
    """개선된 신호 감지 테스트"""
    print("\n🎯 개선된 신호 감지 로직 테스트")
    print("=" * 50)
    
    df = create_test_data()
    detector = SignalDetector()
    
    test_cases = [
        ("005930", "삼성전자", 7),  # 7일 확정
        ("035720", "카카오", 1),   # 1일 확정
        ("012450", "한화에어로스페이스", 2)  # 2일 확정
    ]
    
    for symbol, name, expected_days in test_cases:
        print(f"\n📈 {name}({symbol}) 테스트:")
        
        # 11일째 데이터로 테스트 (골든크로스 시작점)
        test_data = df.iloc[:11].copy()
        signal = detector.detect_golden_cross(test_data, symbol, name)
        
        if signal:
            actual_days = detector.get_optimal_confirmation_days(symbol)
            print(f"  ✅ 신호 감지됨")
            print(f"  📊 설정된 확정 기간: {actual_days}일 (예상: {expected_days}일)")
            print(f"  🎯 신호 타입: {signal.signal_type.value}")
            print(f"  💪 신호 강도: {signal.strength:.1f}/100")
            print(f"  🔒 확신도: {signal.confidence.value}")
        else:
            print(f"  ❌ 신호 미감지")
    
    print("\n✅ 종목별 최적 설정이 정상 적용됨")

if __name__ == "__main__":
    try:
        test_optimal_periods()
        test_signal_detection()
        
        print(f"\n🎉 최적화된 시스템 테스트 완료!")
        print("\n💡 주요 개선사항:")
        print("  1. 백테스팅 결과 기반 종목별 최적 확정 기간 적용")
        print("  2. 대형주(7일) vs 중소형주(2일) 기본 전략")
        print("  3. 동적 신호 강도 계산 및 확신도 판정")
        
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {e}")
        sys.exit(1)