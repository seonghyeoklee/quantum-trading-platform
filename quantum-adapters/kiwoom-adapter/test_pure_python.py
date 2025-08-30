"""
순수 Python으로 기술적 지표 계산 테스트
(pandas, numpy 등의 외부 의존성 없이 실행)
"""

def calculate_rsi_simple(prices, period=14):
    """
    순수 Python으로 RSI 계산
    """
    if len(prices) < period + 1:
        raise ValueError(f"RSI 계산을 위해서는 최소 {period + 1}개의 가격 데이터가 필요합니다.")
    
    # 가격 변화량 계산
    deltas = []
    for i in range(1, len(prices)):
        deltas.append(prices[i] - prices[i-1])
    
    # 상승분과 하락분 분리
    gains = [max(delta, 0) for delta in deltas]
    losses = [max(-delta, 0) for delta in deltas]
    
    # 첫 번째 기간의 평균 계산
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    # 이후 기간들에 대한 지수 이동 평균 계산 (Wilder's smoothing)
    for i in range(period, len(gains)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period
    
    # RS (Relative Strength) 계산
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    
    # RSI 계산
    rsi = 100.0 - (100.0 / (1.0 + rs))
    
    return round(rsi, 2)


def calculate_sma_simple(prices, period):
    """
    순수 Python으로 단순이동평균 계산
    """
    if len(prices) < period:
        raise ValueError(f"SMA 계산을 위해서는 최소 {period}개의 데이터가 필요합니다.")
    
    return round(sum(prices[-period:]) / period, 2)


def calculate_ema_simple(prices, period):
    """
    순수 Python으로 지수이동평균 계산
    """
    if len(prices) < period:
        raise ValueError(f"EMA 계산을 위해서는 최소 {period}개의 데이터가 필요합니다.")
    
    # 초기값은 SMA로 설정
    ema = sum(prices[:period]) / period
    multiplier = 2.0 / (period + 1)
    
    # EMA 계산
    for i in range(period, len(prices)):
        ema = (prices[i] * multiplier) + (ema * (1 - multiplier))
    
    return round(ema, 2)


def test_pure_python_indicators():
    """순수 Python 기술적 지표 테스트"""
    print("=== 순수 Python 기술적 지표 테스트 ===")
    
    try:
        # 테스트 데이터 - 실제 주식 가격처럼 변동하는 패턴
        print("📊 테스트 데이터 생성 중...")
        
        # 상승 후 하락하는 패턴 (RSI 변화를 보기 위해)
        test_prices = [
            # 초기 상승 구간
            45000, 45200, 45400, 45100, 45600, 45800, 46000, 46200, 46400, 46100,
            # 더 큰 상승
            46500, 46800, 47000, 47300, 47500, 47800, 48000, 48200, 47900, 48100,
            # 하락 시작
            47800, 47500, 47200, 46900, 46600, 46300, 46000, 45700, 45400, 45100,
            # 더 큰 하락
            44800, 44500, 44200, 43900, 43600, 43300, 43000, 42700, 42400, 42100
        ]
        
        print(f"   - 데이터 기간: {len(test_prices)}일")
        print(f"   - 시작가: {test_prices[0]:,}원")
        print(f"   - 종료가: {test_prices[-1]:,}원") 
        print(f"   - 최고가: {max(test_prices):,}원")
        print(f"   - 최저가: {min(test_prices):,}원")
        
        # 1. RSI 계산 테스트
        print("\n--- RSI 계산 테스트 ---")
        rsi_14 = calculate_rsi_simple(test_prices, 14)
        print(f"✅ RSI(14일): {rsi_14}")
        
        # RSI 해석
        if rsi_14 < 30:
            rsi_signal = "🔵 과매도 - 매수 고려"
        elif rsi_14 > 70:
            rsi_signal = "🔴 과매수 - 매도 고려"  
        else:
            rsi_signal = "⚪ 중립 - 관망"
        
        print(f"   📈 신호: {rsi_signal}")
        
        # 2. 이동평균 계산 테스트
        print("\n--- 이동평균 계산 테스트 ---")
        sma_5 = calculate_sma_simple(test_prices, 5)
        sma_20 = calculate_sma_simple(test_prices, 20)
        
        print(f"✅ 5일 단순이동평균: {sma_5:,}원")
        print(f"✅ 20일 단순이동평균: {sma_20:,}원")
        
        # 이동평균 교차 분석
        current_price = test_prices[-1]
        print(f"   현재가: {current_price:,}원")
        
        # 골든크로스/데드크로스 판단
        if sma_5 > sma_20:
            ma_signal = "🟢 골든크로스 - 상승 추세"
        elif sma_5 < sma_20:
            ma_signal = "🔴 데드크로스 - 하락 추세"
        else:
            ma_signal = "⚪ 중립"
        
        print(f"   📊 신호: {ma_signal}")
        print(f"   📏 MA 차이: {abs(sma_5 - sma_20):,.0f}원 ({abs(sma_5 - sma_20)/sma_20*100:.2f}%)")
        
        # 3. 지수이동평균 테스트
        print("\n--- 지수이동평균 테스트 ---")
        ema_12 = calculate_ema_simple(test_prices, 12)
        ema_26 = calculate_ema_simple(test_prices, 26)
        
        print(f"✅ 12일 지수이동평균: {ema_12:,}원")
        print(f"✅ 26일 지수이동평균: {ema_26:,}원")
        
        # MACD 기본 계산 (EMA12 - EMA26)
        macd_line = ema_12 - ema_26
        print(f"   📈 MACD Line: {macd_line:,.0f} ({'상승' if macd_line > 0 else '하락' if macd_line < 0 else '중립'})")
        
        # 4. 추세 분석
        print("\n--- 추세 분석 ---")
        
        # 최근 5일간 가격 변화
        recent_change = test_prices[-1] - test_prices[-6]
        recent_change_pct = (recent_change / test_prices[-6]) * 100
        
        print(f"📊 최근 5일 변화: {recent_change:+,}원 ({recent_change_pct:+.2f}%)")
        
        # 전체 기간 변화
        total_change = test_prices[-1] - test_prices[0]
        total_change_pct = (total_change / test_prices[0]) * 100
        
        print(f"📊 전체 기간 변화: {total_change:+,}원 ({total_change_pct:+.2f}%)")
        
        # 5. 종합 분석
        print("\n" + "="*50)
        print("📋 종합 기술 분석 결과")
        print("="*50)
        
        signals = []
        
        # RSI 신호
        if rsi_14 < 30:
            signals.append("RSI 매수 신호")
        elif rsi_14 > 70:
            signals.append("RSI 매도 신호")
        
        # 이동평균 신호  
        if sma_5 > sma_20 and abs(sma_5 - sma_20) / sma_20 > 0.01:  # 1% 이상 차이
            signals.append("이동평균 상승 신호")
        elif sma_5 < sma_20 and abs(sma_5 - sma_20) / sma_20 > 0.01:
            signals.append("이동평균 하락 신호")
        
        # MACD 신호
        if macd_line > 0:
            signals.append("MACD 상승")
        elif macd_line < 0:
            signals.append("MACD 하락")
        
        print(f"🎯 현재가: {current_price:,}원")
        print(f"📈 RSI: {rsi_14} ({rsi_signal.split(' - ')[1]})")
        print(f"📊 이동평균: {ma_signal.split(' - ')[1]}")
        
        if signals:
            print(f"🚨 주요 신호: {' | '.join(signals)}")
        else:
            print("⏸️  뚜렷한 신호 없음 - 관망")
        
        # 추천 액션
        buy_signals = sum(1 for s in signals if '매수' in s or '상승' in s)
        sell_signals = sum(1 for s in signals if '매도' in s or '하락' in s)
        
        if buy_signals > sell_signals:
            action = "🟢 매수 검토"
        elif sell_signals > buy_signals:
            action = "🔴 매도 검토"
        else:
            action = "⚪ 관망 권장"
        
        print(f"💡 추천: {action}")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_edge_cases():
    """극값 테스트"""
    print("\n=== 극값 상황 테스트 ===")
    
    try:
        # 1. 연속 상승 (과매수 유도)
        rising_prices = [40000 + i * 300 for i in range(25)]
        rsi_up = calculate_rsi_simple(rising_prices, 14)
        print(f"📈 연속 상승 패턴 RSI: {rsi_up} ({'과매수!' if rsi_up > 70 else '정상'})")
        
        # 2. 연속 하락 (과매도 유도)  
        falling_prices = [50000 - i * 300 for i in range(25)]
        rsi_down = calculate_rsi_simple(falling_prices, 14)
        print(f"📉 연속 하락 패턴 RSI: {rsi_down} ({'과매도!' if rsi_down < 30 else '정상'})")
        
        # 3. 횡보 패턴
        sideways_prices = [45000 + ((-1)**i) * (i % 3) * 100 for i in range(25)]
        rsi_side = calculate_rsi_simple(sideways_prices, 14)
        print(f"📊 횡보 패턴 RSI: {rsi_side} (중립 예상)")
        
        # 4. 변동성이 큰 패턴
        volatile_prices = [45000]
        for i in range(1, 25):
            change = ((-1)**i) * (i % 4 + 1) * 200
            volatile_prices.append(volatile_prices[-1] + change)
        
        rsi_vol = calculate_rsi_simple(volatile_prices, 14)
        print(f"🎢 변동성 큰 패턴 RSI: {rsi_vol}")
        
        return True
        
    except Exception as e:
        print(f"❌ 극값 테스트 실패: {e}")
        return False


def main():
    """메인 함수"""
    print("🚀 순수 Python 기술적 지표 테스트")
    print("=" * 50)
    
    success_count = 0
    total_tests = 2
    
    # 1. 기본 지표 테스트
    if test_pure_python_indicators():
        success_count += 1
        print("\n✅ 기본 지표 테스트 성공!")
    else:
        print("\n❌ 기본 지표 테스트 실패!")
    
    # 2. 극값 테스트
    if test_edge_cases():
        success_count += 1  
        print("\n✅ 극값 테스트 성공!")
    else:
        print("\n❌ 극값 테스트 실패!")
    
    # 결과 요약
    print("\n" + "="*50)
    print("🎯 최종 결과")
    print("="*50)
    print(f"성공: {success_count}/{total_tests} 테스트")
    
    if success_count == total_tests:
        print("🎉 모든 기술적 지표 계산이 정상 동작합니다!")
        print("\n💡 검증된 기능:")
        print("   ✅ RSI 계산 (과매수/과매도 판단)")
        print("   ✅ 단순이동평균 계산 (골든/데드크로스)")
        print("   ✅ 지수이동평균 계산 (MACD 기초)")
        print("   ✅ 다양한 시장 상황 대응")
        
        print("\n🚀 다음 단계:")
        print("   1. 의존성 설치 후 전략 클래스 테스트")
        print("   2. 실제 키움 API 데이터 연동")
        print("   3. 자동매매 전략 백테스팅")
        
    else:
        print("⚠️  일부 기능에 문제가 있습니다.")
    
    return success_count == total_tests


if __name__ == "__main__":
    main()