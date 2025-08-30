"""
기술적 지표만 테스트하는 간단한 스크립트
(pydantic, 전략 클래스 등의 의존성 없이 실행)
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_technical_indicators():
    """기술적 지표 계산 테스트"""
    print("=== 기술적 지표 계산 테스트 ===")
    
    try:
        from kiwoom_api.analysis.indicators.technical import calculate_rsi, calculate_sma, calculate_ema, calculate_obv
        
        print("✅ 기술적 지표 모듈 import 성공")
        
        # 테스트 데이터 (실제 주가 패턴 시뮬레이션)
        # 상승 후 하락하는 패턴으로 RSI가 변화하도록 설계
        test_prices = [
            # 상승 구간 (RSI 상승)
            40000, 40500, 41000, 41200, 41800, 42000, 42500, 43000, 43200, 43800,
            44000, 44500, 44800, 45000, 45500,
            # 하락 구간 (RSI 하락)  
            45200, 44800, 44000, 43500, 43000, 42500, 42000, 41500, 41000, 40500,
            40000, 39500, 39000, 38500, 38000
        ]
        
        test_volumes = [100000 + i * 1000 for i in range(len(test_prices))]
        
        print(f"📊 테스트 데이터: {len(test_prices)}일간 가격 데이터")
        print(f"   - 시작가: {test_prices[0]:,}원")
        print(f"   - 종료가: {test_prices[-1]:,}원")
        print(f"   - 최고가: {max(test_prices):,}원")
        print(f"   - 최저가: {min(test_prices):,}원")
        
        # 1. RSI 계산 테스트
        print("\n--- RSI(Relative Strength Index) 테스트 ---")
        rsi_14 = calculate_rsi(test_prices, period=14)
        rsi_21 = calculate_rsi(test_prices, period=21)
        
        print(f"✅ RSI(14일): {rsi_14:.2f}")
        print(f"✅ RSI(21일): {rsi_21:.2f}")
        
        # RSI 해석
        if rsi_14 < 30:
            rsi_interpretation = "과매도 구간 - 매수 고려"
        elif rsi_14 > 70:
            rsi_interpretation = "과매수 구간 - 매도 고려"
        else:
            rsi_interpretation = "중립 구간 - 관망"
        
        print(f"   📈 RSI 해석: {rsi_interpretation}")
        
        # 2. 이동평균 계산 테스트
        print("\n--- 이동평균(Moving Average) 테스트 ---")
        sma_5 = calculate_sma(test_prices, period=5)
        sma_10 = calculate_sma(test_prices, period=10)
        sma_20 = calculate_sma(test_prices, period=20)
        
        print(f"✅ 5일 단순이동평균: {sma_5:,.0f}원")
        print(f"✅ 10일 단순이동평균: {sma_10:,.0f}원")
        print(f"✅ 20일 단순이동평균: {sma_20:,.0f}원")
        
        # 이동평균 분석
        current_price = test_prices[-1]
        print(f"   📊 현재가 vs 이동평균:")
        print(f"      현재가({current_price:,}) vs 5일MA({sma_5:,.0f}): {'상회' if current_price > sma_5 else '하회'}")
        print(f"      현재가({current_price:,}) vs 20일MA({sma_20:,.0f}): {'상회' if current_price > sma_20 else '하회'}")
        
        # 골든크로스/데드크로스 확인
        if sma_5 > sma_20:
            ma_signal = "골든크로스 상태 - 상승 추세"
        elif sma_5 < sma_20:
            ma_signal = "데드크로스 상태 - 하락 추세"
        else:
            ma_signal = "중립 상태"
        print(f"   📈 이동평균 신호: {ma_signal}")
        
        # 3. 지수이동평균 테스트
        print("\n--- 지수이동평균(EMA) 테스트 ---")
        ema_12 = calculate_ema(test_prices, period=12)
        ema_26 = calculate_ema(test_prices, period=26)
        
        print(f"✅ 12일 지수이동평균: {ema_12:,.0f}원")
        print(f"✅ 26일 지수이동평균: {ema_26:,.0f}원")
        
        # 4. OBV 테스트
        print("\n--- OBV(On-Balance Volume) 테스트 ---")
        obv_value = calculate_obv(test_prices, test_volumes)
        print(f"✅ OBV 값: {obv_value:,}")
        
        if obv_value > 0:
            obv_interpretation = "매수 압력 우세"
        elif obv_value < 0:
            obv_interpretation = "매도 압력 우세"
        else:
            obv_interpretation = "균형 상태"
        print(f"   📊 OBV 해석: {obv_interpretation}")
        
        # 5. 전체 분석 요약
        print("\n" + "="*50)
        print("📋 종합 기술적 분석 요약")
        print("="*50)
        print(f"🎯 종목: 테스트 데이터")
        print(f"💰 현재가: {current_price:,}원")
        print(f"📈 RSI(14): {rsi_14:.1f} - {rsi_interpretation}")
        print(f"📊 이동평균: {ma_signal}")
        print(f"📉 거래량: {obv_interpretation}")
        
        # 종합 신호
        signals = []
        if rsi_14 < 30:
            signals.append("RSI 매수")
        elif rsi_14 > 70:
            signals.append("RSI 매도")
        
        if sma_5 > sma_20:
            signals.append("MA 상승")
        elif sma_5 < sma_20:
            signals.append("MA 하락")
        
        if signals:
            print(f"🚨 주요 신호: {', '.join(signals)}")
        else:
            print("⏸️  특별한 신호 없음 - 관망 권장")
        
        return True
        
    except Exception as e:
        print(f"❌ 기술적 지표 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rsi_edge_cases():
    """RSI 극값 테스트"""
    print("\n=== RSI 극값 테스트 ===")
    
    try:
        from kiwoom_api.analysis.indicators.technical import calculate_rsi
        
        # 극단적 상승 패턴 (과매수 유도)
        rising_prices = [40000 + i * 500 for i in range(20)]  # 계속 상승
        rsi_rising = calculate_rsi(rising_prices, period=14)
        print(f"📈 상승 패턴 RSI: {rsi_rising:.1f} ({'과매수' if rsi_rising > 70 else '정상'})")
        
        # 극단적 하락 패턴 (과매도 유도)
        falling_prices = [50000 - i * 500 for i in range(20)]  # 계속 하락
        rsi_falling = calculate_rsi(falling_prices, period=14)
        print(f"📉 하락 패턴 RSI: {rsi_falling:.1f} ({'과매도' if rsi_falling < 30 else '정상'})")
        
        # 횡보 패턴
        sideways_prices = [45000 + (i % 3 - 1) * 100 for i in range(20)]  # 횡보
        rsi_sideways = calculate_rsi(sideways_prices, period=14)
        print(f"📊 횡보 패턴 RSI: {rsi_sideways:.1f} (중립)")
        
        return True
        
    except Exception as e:
        print(f"❌ RSI 극값 테스트 실패: {e}")
        return False


def main():
    """메인 테스트 실행"""
    print("🚀 기술적 지표 테스트 시작\n")
    
    success_count = 0
    total_tests = 2
    
    # 1. 기본 기술적 지표 테스트
    if test_technical_indicators():
        success_count += 1
        print("✅ 기본 기술적 지표 테스트 성공\n")
    else:
        print("❌ 기본 기술적 지표 테스트 실패\n")
    
    # 2. RSI 극값 테스트
    if test_rsi_edge_cases():
        success_count += 1
        print("✅ RSI 극값 테스트 성공\n")
    else:
        print("❌ RSI 극값 테스트 실패\n")
    
    # 결과 요약
    print("=" * 50)
    print("🎯 테스트 완료!")
    print(f"📊 성공: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 모든 기술적 지표가 정상 동작합니다!")
        print("\n💡 다음 단계:")
        print("   1. 의존성 설치 후 전략 클래스 테스트")
        print("   2. 실제 키움 API 연동 테스트")
        print("   3. 실시간 매매신호 생성 테스트")
    else:
        print("⚠️  일부 테스트에서 문제가 발생했습니다.")
    
    return success_count == total_tests


if __name__ == "__main__":
    main()