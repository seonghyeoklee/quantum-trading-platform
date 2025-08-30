"""
간단한 전략 테스트 스크립트 (pytest 의존성 없음)

RSI 전략과 이동평균 교차 전략을 실제로 테스트해봅니다.
"""

import asyncio
import sys
from pathlib import Path
from decimal import Decimal

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from kiwoom_api.strategy.engines.rsi_strategy import RSIStrategy
from kiwoom_api.strategy.engines.moving_average_crossover import MovingAverageCrossoverStrategy
from kiwoom_api.strategy.models.strategy_config import StrategyConfig, StrategyType, RiskLevel


async def test_rsi_strategy():
    """RSI 전략 테스트"""
    print("=== RSI 전략 테스트 시작 ===")
    
    try:
        # RSI 전략 설정
        config = StrategyConfig(
            strategy_name="RSI 테스트 전략",
            strategy_type=StrategyType.RSI_MEAN_REVERSION,
            target_symbols=["005930"],  # 삼성전자
            risk_level=RiskLevel.MODERATE,
            max_position_size=Decimal("1000000"),  # 100만원
            execution_interval=60,
            strategy_params={
                "rsi_period": 14,
                "oversold_threshold": 30.0,
                "overbought_threshold": 70.0
            }
        )
        
        # 전략 생성
        strategy = RSIStrategy(config)
        print(f"✅ RSI 전략 생성 완료: {strategy.name}")
        print(f"   - RSI 기간: {strategy.rsi_period}일")
        print(f"   - 과매도 임계치: {strategy.oversold_threshold}")
        print(f"   - 과매수 임계치: {strategy.overbought_threshold}")
        
        # 분석 실행
        print("\n📊 삼성전자(005930) RSI 분석 중...")
        result = await strategy.analyze("005930")
        
        if result:
            print(f"🎯 매매신호 생성!")
            print(f"   - 신호 타입: {result.signal_type.value}")
            print(f"   - 신호 강도: {result.strength.value}")
            print(f"   - 신뢰도: {result.confidence:.3f}")
            print(f"   - 현재가: {result.current_price:,}원")
            print(f"   - 목표가: {result.target_price:,}원" if result.target_price else "   - 목표가: 미설정")
            print(f"   - 손절가: {result.stop_loss:,}원" if result.stop_loss else "   - 손절가: 미설정")
            print(f"   - 발생 이유: {result.reason}")
            print(f"   - 생성 시간: {result.timestamp}")
        else:
            print("⏸️  현재 매매신호 없음")
        
        print("✅ RSI 전략 테스트 완료\n")
        return True
        
    except Exception as e:
        print(f"❌ RSI 전략 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_ma_crossover_strategy():
    """이동평균 교차 전략 테스트"""
    print("=== 이동평균 교차 전략 테스트 시작 ===")
    
    try:
        # 이동평균 교차 전략 설정
        config = StrategyConfig(
            strategy_name="이동평균 교차 테스트 전략",
            strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
            target_symbols=["005930"],  # 삼성전자
            risk_level=RiskLevel.MODERATE,
            max_position_size=Decimal("2000000"),  # 200만원
            execution_interval=300,  # 5분
            strategy_params={
                "short_period": 5,
                "long_period": 20,
                "use_rsi_filter": True,
                "rsi_oversold": 35,
                "rsi_overbought": 65,
                "trend_confirmation": True
            }
        )
        
        # 전략 생성
        strategy = MovingAverageCrossoverStrategy(config)
        print(f"✅ 이동평균 교차 전략 생성 완료: {strategy.name}")
        print(f"   - 단기 이동평균: {strategy.short_period}일")
        print(f"   - 장기 이동평균: {strategy.long_period}일")
        print(f"   - RSI 필터 사용: {strategy.use_rsi_filter}")
        print(f"   - 추세 확인: {strategy.trend_confirmation}")
        
        # 분석 실행
        print("\n📊 삼성전자(005930) 이동평균 교차 분석 중...")
        result = await strategy.analyze("005930")
        
        if result:
            print(f"🎯 매매신호 생성!")
            print(f"   - 신호 타입: {result.signal_type.value}")
            print(f"   - 신호 강도: {result.strength.value}")
            print(f"   - 신뢰도: {result.confidence:.3f}")
            print(f"   - 현재가: {result.current_price:,}원")
            print(f"   - 목표가: {result.target_price:,}원" if result.target_price else "   - 목표가: 미설정")
            print(f"   - 손절가: {result.stop_loss:,}원" if result.stop_loss else "   - 손절가: 미설정")
            print(f"   - 발생 이유: {result.reason}")
            print(f"   - 생성 시간: {result.timestamp}")
        else:
            print("⏸️  현재 매매신호 없음")
        
        print("✅ 이동평균 교차 전략 테스트 완료\n")
        return True
        
    except Exception as e:
        print(f"❌ 이동평균 교차 전략 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_strategy_configurations():
    """전략 설정 테스트"""
    print("=== 전략 설정 검증 테스트 ===")
    
    try:
        # 올바른 설정 테스트
        valid_config = StrategyConfig(
            strategy_name="설정 테스트 전략",
            strategy_type=StrategyType.RSI_MEAN_REVERSION,
            target_symbols=["005930", "000660"],
            risk_level=RiskLevel.CONSERVATIVE,
            max_position_size=Decimal("500000"),
            execution_interval=120,
            min_confidence=0.8
        )
        
        strategy = RSIStrategy(valid_config)
        print(f"✅ 올바른 설정으로 전략 생성 성공")
        print(f"   - 전략명: {strategy.name}")
        print(f"   - 대상 종목: {valid_config.target_symbols}")
        print(f"   - 리스크 레벨: {valid_config.risk_level.value}")
        print(f"   - 최대 포지션: {valid_config.max_position_size:,}원")
        print(f"   - 최소 신뢰도: {valid_config.min_confidence}")
        
        # 전략 정보 확인
        info = strategy.get_strategy_info()
        print(f"   - 전략 정보: {info['type']}, 활성화: {info['enabled']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 전략 설정 테스트 실패: {e}")
        return False


async def test_technical_indicators():
    """기술적 지표 계산 테스트"""
    print("=== 기술적 지표 계산 테스트 ===")
    
    try:
        from kiwoom_api.analysis.indicators.technical import calculate_rsi, calculate_sma
        
        # 테스트 데이터 (주가 상승 후 하락 패턴)
        test_prices = [
            45000, 45200, 45100, 44900, 45300, 45500, 45800, 46000, 45700, 45400,
            45100, 44800, 44500, 44200, 43900, 43600, 43400, 43200, 43000, 42800,
            42600, 42400, 42200, 42000, 41800, 41600, 41400, 41200, 41000, 40800
        ]
        
        # RSI 계산
        rsi_value = calculate_rsi(test_prices, period=14)
        print(f"✅ RSI 계산 성공: {rsi_value:.2f}")
        
        if rsi_value < 30:
            print(f"   - 해석: 과매도 구간 (매수 고려)")
        elif rsi_value > 70:
            print(f"   - 해석: 과매수 구간 (매도 고려)")
        else:
            print(f"   - 해석: 중립 구간")
        
        # 이동평균 계산
        sma_5 = calculate_sma(test_prices, period=5)
        sma_20 = calculate_sma(test_prices, period=20)
        print(f"✅ 5일 이동평균: {sma_5:,.0f}원")
        print(f"✅ 20일 이동평균: {sma_20:,.0f}원")
        
        if sma_5 > sma_20:
            print(f"   - 해석: 단기 > 장기 (상승 추세)")
        else:
            print(f"   - 해석: 단기 < 장기 (하락 추세)")
        
        return True
        
    except Exception as e:
        print(f"❌ 기술적 지표 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """메인 테스트 실행"""
    print("🚀 자동매매 전략 시스템 테스트 시작\n")
    
    test_results = []
    
    # 1. 기술적 지표 테스트
    result = await test_technical_indicators()
    test_results.append(("기술적 지표 계산", result))
    print()
    
    # 2. 전략 설정 테스트
    result = await test_strategy_configurations()
    test_results.append(("전략 설정 검증", result))
    print()
    
    # 3. RSI 전략 테스트
    result = await test_rsi_strategy()
    test_results.append(("RSI 전략", result))
    
    # 4. 이동평균 교차 전략 테스트
    result = await test_ma_crossover_strategy()
    test_results.append(("이동평균 교차 전략", result))
    
    # 결과 요약
    print("=" * 50)
    print("📋 테스트 결과 요약")
    print("=" * 50)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 전체 결과: {passed}/{len(test_results)} 테스트 통과")
    
    if passed == len(test_results):
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
    else:
        print("⚠️  일부 테스트에서 문제가 발생했습니다.")
    
    return passed == len(test_results)


if __name__ == "__main__":
    # 이벤트 루프 실행
    success = asyncio.run(main())
    sys.exit(0 if success else 1)