#!/usr/bin/env python3
"""
단일 종목 상세 분석 과정 데모
MultiDataProvider → SignalDetector → Backtrader 전 과정 로그
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import time
import logging

# 프로젝트 경로 추가
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir.parent))

from core.multi_data_provider import MultiDataProvider, DataSource, MarketData
from core.backtester import GoldenCrossBacktester
from core.signal_detector import SignalDetector
from core.technical_analysis import TechnicalAnalyzer

# 상세 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def detailed_single_stock_analysis(symbol="005930", name="삼성전자"):
    """단일 종목 상세 분석 과정"""
    
    print("=" * 80)
    print(f"🔍 단일 종목 상세 분석: {name}({symbol})")
    print("=" * 80)
    
    # =========================================================================
    # 📊 1단계: 데이터 수집 과정 (다중 소스 시도)
    # =========================================================================
    print(f"\n📊 1단계: {name}({symbol}) 데이터 수집 과정")
    print("-" * 60)
    
    # 데이터 공급자 초기화
    print("🔧 MultiDataProvider 초기화...")
    provider = MultiDataProvider(enable_kis=False, cache_enabled=True)
    
    # 사용 가능한 소스 표시
    print(f"✅ 사용 가능한 데이터 소스: {[s.value for s in provider.available_sources]}")
    
    # 데이터 수집 요청 (최근 2년 - 백테스팅 신뢰성 확보)
    start_date = datetime.now() - timedelta(days=730)  # 2년 데이터
    end_date = datetime.now()
    
    print(f"\n📅 요청 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')} (730일)")
    print(f"🎯 요청 모드: AUTO (자동 소스 선택)")
    print(f"🔄 폴백 모드: 활성화")
    
    # 성능 통계 확인
    print(f"\n📈 현재 소스별 성능 통계:")
    current_stats = provider.performance_stats
    for source, stats in current_stats.items():
        if stats['calls'] > 0:
            success_rate = stats['success'] / stats['calls'] * 100
            print(f"   {source.value}: 성공률 {success_rate:.1f}%, 평균응답 {stats['avg_time']:.3f}초")
        else:
            print(f"   {source.value}: 사용 기록 없음")
    
    print(f"\n🚀 데이터 수집 시작...")
    collection_start = time.time()
    
    result = provider.get_stock_data(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        source=DataSource.AUTO,
        fallback=True
    )
    
    collection_time = time.time() - collection_start
    
    if not result:
        print("❌ 데이터 수집 실패 - 분석 종료")
        return None
    
    # 수집 결과 상세 표시
    print(f"\n✅ 데이터 수집 성공!")
    print(f"   📡 선택된 소스: {result.source.value}")
    print(f"   📊 데이터 품질: {result.quality.value}")
    print(f"   📅 실제 데이터: {len(result.data)}일")
    print(f"   ⚡ 수집 시간: {collection_time:.3f}초")
    print(f"   💾 메타데이터: {result.metadata}")
    
    # 데이터 샘플 표시
    print(f"\n📋 데이터 샘플 (최근 3일):")
    sample_data = result.data.tail(3)
    for idx, row in sample_data.iterrows():
        print(f"   {idx.strftime('%Y-%m-%d')}: "
              f"시가 {row['open']:,.0f}, 고가 {row['high']:,.0f}, "
              f"저가 {row['low']:,.0f}, 종가 {row['close']:,.0f}, "
              f"거래량 {row['volume']:,.0f}")
    
    # 기본 통계
    df = result.data
    print(f"\n📊 기본 통계:")
    print(f"   💰 가격 범위: {df['low'].min():,.0f}원 ~ {df['high'].max():,.0f}원")
    print(f"   📈 기간 수익률: {((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100):+.2f}%")
    print(f"   📊 평균 거래량: {df['volume'].mean():,.0f}")
    print(f"   📉 변동성 (표준편차): {df['close'].pct_change().std() * 100:.2f}%")
    
    # =========================================================================
    # 🔧 2단계: 기술적 분석 및 지표 계산
    # =========================================================================
    print(f"\n🔧 2단계: 기술적 분석 및 지표 계산")
    print("-" * 60)
    
    print("📈 기술적 지표 계산 중...")
    
    # SMA 계산
    sma5 = TechnicalAnalyzer.calculate_sma(df['close'], 5)
    sma20 = TechnicalAnalyzer.calculate_sma(df['close'], 20)
    sma60 = TechnicalAnalyzer.calculate_sma(df['close'], 60)
    
    # RSI 계산
    rsi = TechnicalAnalyzer.calculate_rsi(df['close'])
    
    # MACD 계산
    try:
        macd_line, signal_line, histogram = TechnicalAnalyzer.calculate_macd(df['close'])
        macd_available = True
    except:
        macd_available = False
    
    # 볼린저 밴드 계산
    try:
        bb_upper, bb_middle, bb_lower = TechnicalAnalyzer.calculate_bollinger_bands(df['close'])
        bb_available = True
    except:
        bb_available = False
    
    # 최신 지표 값들
    latest_close = df['close'].iloc[-1]
    latest_sma5 = sma5.iloc[-1] if pd.notna(sma5.iloc[-1]) else None
    latest_sma20 = sma20.iloc[-1] if pd.notna(sma20.iloc[-1]) else None
    latest_sma60 = sma60.iloc[-1] if pd.notna(sma60.iloc[-1]) else None
    latest_rsi = rsi.iloc[-1] if pd.notna(rsi.iloc[-1]) else None
    
    print(f"\n📊 최신 기술적 지표 ({df.index[-1].strftime('%Y-%m-%d')}):")
    print(f"   💰 현재가: {latest_close:,.0f}원")
    print(f"   📈 SMA5: {latest_sma5:,.0f}원" if latest_sma5 else "   📈 SMA5: 계산 중...")
    print(f"   📈 SMA20: {latest_sma20:,.0f}원" if latest_sma20 else "   📈 SMA20: 계산 중...")
    print(f"   📈 SMA60: {latest_sma60:,.0f}원" if latest_sma60 else "   📈 SMA60: 계산 중...")
    print(f"   📊 RSI: {latest_rsi:.1f}" if latest_rsi else "   📊 RSI: 계산 중...")
    
    if latest_rsi:
        if latest_rsi < 30:
            print("      ⬆️ 과매도 구간 (매수 신호)")
        elif latest_rsi > 70:
            print("      ⬇️ 과매수 구간 (매도 신호)")
        else:
            print("      ➡️ 중립 구간")
    
    if macd_available:
        latest_macd = macd_line.iloc[-1] if pd.notna(macd_line.iloc[-1]) else None
        latest_signal = signal_line.iloc[-1] if pd.notna(signal_line.iloc[-1]) else None
        if latest_macd and latest_signal:
            print(f"   📈 MACD: {latest_macd:.2f}, Signal: {latest_signal:.2f}")
            if latest_macd > latest_signal:
                print("      ⬆️ MACD 상승 추세")
            else:
                print("      ⬇️ MACD 하락 추세")
    
    # 이동평균선 배열 분석
    if latest_close and latest_sma5 and latest_sma20 and latest_sma60:
        print(f"\n📊 이동평균선 배열 분석:")
        if latest_close > latest_sma5 > latest_sma20 > latest_sma60:
            print("   🟢 정배열 (강력한 상승 추세)")
        elif latest_close < latest_sma5 < latest_sma20 < latest_sma60:
            print("   🔴 역배열 (강력한 하락 추세)")
        else:
            print("   🟡 혼재 (박스권 또는 추세 전환)")
    
    # =========================================================================
    # 🎯 3단계: 골든크로스 신호 감지
    # =========================================================================
    print(f"\n🎯 3단계: 골든크로스 신호 감지")
    print("-" * 60)
    
    # 신호 감지기 초기화
    print("🎯 SignalDetector 초기화...")
    detector = SignalDetector()
    
    # 종목별 최적 확정기간 확인
    optimal_days = detector.get_optimal_confirmation_days(symbol)
    print(f"📅 {name}({symbol}) 최적 확정기간: {optimal_days}일 (백테스팅 검증 결과)")
    
    # 골든크로스 신호 감지
    print(f"\n🔍 골든크로스 신호 분석 중...")
    signal_start = time.time()
    
    signal = detector.detect_golden_cross(df, symbol, name)
    
    signal_time = time.time() - signal_start
    print(f"⚡ 신호 분석 시간: {signal_time:.3f}초")
    
    if signal:
        print(f"\n🚨 골든크로스 신호 발생!")
        print(f"   🎯 신호 타입: {signal.signal_type.value}")
        print(f"   📊 확신도: {signal.confidence.value}")
        print(f"   💪 신호 강도: {signal.strength:.1f}/100")
        print(f"   💰 현재가: {signal.price:,.0f}원")
        print(f"   📈 SMA5: {signal.sma5:,.0f}원")
        print(f"   📈 SMA20: {signal.sma20:,.0f}원")
        print(f"   📅 감지 시점: {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   📊 확정 일수: {signal.confirmation_days}일")
        print(f"   📈 스프레드: {signal.spread_percent:.2f}%")
        print(f"   📊 거래량 비율: {signal.volume_ratio:.2f}x")
        
        # 신호 강도에 따른 추천
        if signal.confidence.value == 'CONFIRMED' and signal.strength >= 80:
            print(f"   ✅ 매수 추천 - 고확신 강력 신호")
        elif signal.confidence.value == 'TENTATIVE' and signal.strength >= 60:
            print(f"   🟡 매수 고려 - 중간 확신 신호")
        else:
            print(f"   ⚠️ 신호 약함 - 추가 관찰 필요")
    else:
        print(f"\n⭕ 현재 골든크로스 신호 없음")
        
        # 현재 상태 분석
        if latest_sma5 and latest_sma20:
            gap = (latest_sma5 - latest_sma20) / latest_sma20 * 100
            print(f"   📊 SMA5-SMA20 갭: {gap:+.2f}%")
            
            if gap > -1 and gap < 1:
                print(f"   👀 주목: 이동평균선이 근접 (골든크로스 임박 가능성)")
            elif gap > 0:
                print(f"   📈 SMA5가 SMA20 위에 위치 (상승 추세)")
            else:
                print(f"   📉 SMA5가 SMA20 아래 위치 (하락 추세)")
    
    # =========================================================================
    # ⚡ 4단계: Backtrader 백테스팅 검증
    # =========================================================================
    print(f"\n⚡ 4단계: Backtrader 백테스팅 검증")
    print("-" * 60)
    
    print("⚡ GoldenCrossBacktester 초기화...")
    backtester = GoldenCrossBacktester()
    
    print(f"📊 백테스팅 설정:")
    print(f"   🎯 확정기간: {optimal_days}일")
    print(f"   💰 초기자금: 1,000만원")
    print(f"   📅 분석기간: {len(df)}일")
    print(f"   🔧 수수료: 0.015%")
    
    # 데이터 변환 및 백테스팅
    try:
        print(f"\n🔄 백테스팅 실행 중...")
        backtest_start = time.time()
        
        # Backtrader 형식으로 데이터 변환
        df_bt = df.copy()
        df_bt.columns = [col.lower() for col in df_bt.columns]
        bt_data = backtester.prepare_data(df_bt, symbol)
        
        # 백테스팅 실행
        backtest_result = backtester.run_single_test(
            data=bt_data,
            symbol=symbol,
            symbol_name=name,
            confirmation_days=optimal_days
        )
        
        backtest_time = time.time() - backtest_start
        print(f"⚡ 백테스팅 완료 시간: {backtest_time:.3f}초")
        
        if backtest_result:
            print(f"\n📊 백테스팅 결과:")
            total_return = backtest_result.get('total_return', 'N/A')
            start_cash = backtest_result.get('initial_value', 'N/A')
            final_cash = backtest_result.get('final_value', 'N/A')
            
            print(f"   💰 총 수익률: {total_return:+.2f}%" if total_return != 'N/A' else f"   💰 총 수익률: {total_return}")
            print(f"   💵 시작 자금: {start_cash:,.0f}원" if start_cash != 'N/A' else f"   💵 시작 자금: {start_cash}")
            print(f"   💵 최종 자금: {final_cash:,.0f}원" if final_cash != 'N/A' else f"   💵 최종 자금: {final_cash}")
            print(f"   📅 확정 기간: {optimal_days}일")
            
            # 수익률 평가
            if total_return != 'N/A':
                try:
                    total_return_pct = float(total_return) if isinstance(total_return, (int, float)) else float(str(total_return).rstrip('%'))
                except (ValueError, AttributeError):
                    total_return_pct = 0
                if total_return_pct > 5:
                    print(f"   🎉 우수한 성과 - 연간 환산 시 높은 수익 기대")
                elif total_return_pct > 0:
                    print(f"   ✅ 양호한 성과 - 시장 수익률 상회")
                elif total_return_pct > -5:
                    print(f"   🟡 보통 성과 - 시장과 유사한 수준")
                else:
                    print(f"   ⚠️ 저조한 성과 - 전략 개선 필요")
            else:
                total_return_pct = 0
        else:
            print(f"❌ 백테스팅 결과 없음")
    
    except Exception as e:
        print(f"❌ 백테스팅 오류: {e}")
        backtest_result = None
    
    # =========================================================================
    # 📊 5단계: 최종 투자 결정 및 리스크 분석
    # =========================================================================
    print(f"\n📊 5단계: 최종 투자 결정 및 리스크 분석")
    print("-" * 60)
    
    # 종합 점수 계산
    total_score = 0
    max_score = 100
    
    print(f"🎯 투자 적합성 종합 평가:")
    
    # 1. 신호 점수 (40점)
    if signal:
        signal_score = min(signal.confidence * 40, 40)
        print(f"   📊 신호 점수: {signal_score:.1f}/40 (확신도: {signal.confidence:.3f})")
    else:
        signal_score = 0
        print(f"   📊 신호 점수: 0/40 (신호 없음)")
    total_score += signal_score
    
    # 2. 백테스팅 점수 (30점)
    if backtest_result and '총수익률' in backtest_result and backtest_result['총수익률'] != 'N/A':
        try:
            return_pct = float(backtest_result['총수익률'].rstrip('%'))
            backtest_score = min(max(return_pct * 3, 0), 30)  # 10% 수익률 = 30점
            print(f"   ⚡ 백테스팅 점수: {backtest_score:.1f}/30 (수익률: {return_pct:+.2f}%)")
        except (ValueError, AttributeError):
            backtest_score = 15  # 중간 점수
            print(f"   ⚡ 백테스팅 점수: 15/30 (결과 파싱 오류 - 중간 점수)")
    else:
        backtest_score = 15  # 중간 점수
        print(f"   ⚡ 백테스팅 점수: 15/30 (결과 없음 - 중간 점수)")
    total_score += backtest_score
    
    # 3. 기술적 지표 점수 (30점)
    tech_score = 0
    
    # RSI 점수 (10점)
    if latest_rsi:
        if 40 <= latest_rsi <= 60:
            rsi_score = 10  # 중립권 최고
        elif 30 <= latest_rsi <= 70:
            rsi_score = 8   # 적정권
        else:
            rsi_score = 5   # 과매수/과매도
    else:
        rsi_score = 5
    tech_score += rsi_score
    rsi_display = f"{latest_rsi:.1f}" if latest_rsi else "N/A"
    print(f"   📈 RSI 점수: {rsi_score}/10 (RSI: {rsi_display})")
    
    # 이동평균 점수 (10점)
    if latest_close and latest_sma20:
        ma_ratio = (latest_close - latest_sma20) / latest_sma20
        if 0 <= ma_ratio <= 0.05:  # 0~5% 위
            ma_score = 10
        elif -0.02 <= ma_ratio < 0:  # 2% 아래까지
            ma_score = 8
        elif ma_ratio > 0.05:  # 5% 이상 위
            ma_score = 6
        else:  # 2% 이상 아래
            ma_score = 4
    else:
        ma_score = 5
    tech_score += ma_score
    print(f"   📈 이동평균 점수: {ma_score}/10")
    
    # 변동성 점수 (10점)
    volatility = df['close'].pct_change().std() * 100
    if volatility < 2:
        vol_score = 10  # 안정적
    elif volatility < 3:
        vol_score = 8   # 적당
    elif volatility < 4:
        vol_score = 6   # 다소 높음
    else:
        vol_score = 4   # 매우 높음
    tech_score += vol_score
    print(f"   📊 변동성 점수: {vol_score}/10 (변동성: {volatility:.2f}%)")
    
    total_score += tech_score
    print(f"   📈 기술적 지표 총점: {tech_score}/30")
    
    # 최종 점수 및 추천
    print(f"\n🎯 최종 투자 적합성 점수: {total_score:.1f}/100")
    
    if total_score >= 80:
        recommendation = "🟢 강력 매수 추천"
        risk_level = "낮음"
    elif total_score >= 65:
        recommendation = "🟡 매수 고려"
        risk_level = "보통"
    elif total_score >= 50:
        recommendation = "🔶 신중한 관찰"
        risk_level = "보통"
    else:
        recommendation = "🔴 매수 비추천"
        risk_level = "높음"
    
    print(f"   📊 투자 추천: {recommendation}")
    print(f"   ⚠️ 리스크 수준: {risk_level}")
    
    # 리스크 요인 분석
    print(f"\n⚠️ 주요 리스크 요인:")
    risk_factors = []
    
    if latest_rsi and (latest_rsi > 70 or latest_rsi < 30):
        risk_factors.append(f"과매수/과매도 상태 (RSI: {latest_rsi:.1f})")
    
    if volatility > 3:
        risk_factors.append(f"높은 변동성 ({volatility:.2f}%)")
    
    if not signal:
        risk_factors.append("명확한 매수 신호 부재")
    
    if backtest_result and '총수익률' in backtest_result and backtest_result['총수익률'] != 'N/A':
        try:
            return_pct = float(backtest_result['총수익률'].rstrip('%'))
            if return_pct < 0:
                risk_factors.append(f"백테스팅 손실 ({return_pct:+.2f}%)")
        except (ValueError, AttributeError):
            pass
    
    if risk_factors:
        for factor in risk_factors:
            print(f"   ⚠️ {factor}")
    else:
        print(f"   ✅ 주요 리스크 요인 없음")
    
    # =========================================================================
    # 🎉 분석 완료 요약
    # =========================================================================
    print(f"\n" + "=" * 80)
    print(f"🎉 {name}({symbol}) 상세 분석 완료!")
    print("=" * 80)
    
    print(f"📊 분석 결과 요약:")
    print(f"   📡 데이터 소스: {result.source.value}")
    print(f"   📅 분석 기간: {len(df)}일")
    print(f"   💰 현재가: {latest_close:,.0f}원")
    print(f"   📈 기간 수익률: {((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100):+.2f}%")
    print(f"   🎯 신호 상태: {'발생' if signal else '없음'}")
    print(f"   ⚡ 백테스팅: {backtest_result.get('총수익률', 'N/A') if backtest_result else 'N/A'}")
    print(f"   📊 투자 점수: {total_score:.1f}/100")
    print(f"   💡 추천: {recommendation}")
    
    return {
        'symbol': symbol,
        'name': name,
        'market_data': result,
        'signal': signal,
        'backtest_result': backtest_result,
        'technical_indicators': {
            'rsi': latest_rsi,
            'sma5': latest_sma5,
            'sma20': latest_sma20,
            'sma60': latest_sma60,
            'volatility': volatility
        },
        'investment_score': total_score,
        'recommendation': recommendation,
        'risk_level': risk_level,
        'risk_factors': risk_factors
    }

if __name__ == "__main__":
    print("🎬 단일 종목 상세 분석 과정 데모 시작")
    
    # 사용자 입력 또는 기본값
    test_symbols = [
        ("005930", "삼성전자"),
        ("035720", "카카오"),
        ("000660", "SK하이닉스")
    ]
    
    print(f"\n분석 가능한 종목:")
    for i, (symbol, name) in enumerate(test_symbols, 1):
        print(f"   {i}. {name}({symbol})")
    
    # 기본적으로 삼성전자 분석
    symbol, name = test_symbols[0]
    
    print(f"\n🎯 선택된 종목: {name}({symbol})")
    print("분석을 시작합니다...\n")
    
    # 상세 분석 실행
    result = detailed_single_stock_analysis(symbol, name)
    
    if result:
        print(f"\n✅ 분석 완료! 투자 결정에 활용하세요.")
    else:
        print(f"\n❌ 분석 실패. 네트워크 연결이나 데이터 소스를 확인해주세요.")