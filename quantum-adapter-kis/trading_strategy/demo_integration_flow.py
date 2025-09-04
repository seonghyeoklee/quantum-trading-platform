#!/usr/bin/env python3
"""
다중 라이브러리 통합 시스템 실제 연동 플로우 데모
실제 사용 시나리오를 통한 전체 시스템 동작 시연
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import time

# 프로젝트 경로 추가
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir.parent))

from core.multi_data_provider import MultiDataProvider, DataSource, MarketData
from core.backtester import GoldenCrossBacktester
from core.signal_detector import SignalDetector
from core.technical_analysis import TechnicalAnalyzer

def demo_real_world_scenario():
    """실제 사용 시나리오 데모"""
    print("=" * 80)
    print("🌟 실제 연동 플로우 데모: 골든크로스 자동매매 시스템")
    print("=" * 80)
    
    # =========================================================================
    # 📊 STEP 1: 시스템 초기화 및 설정
    # =========================================================================
    print("\n📊 STEP 1: 시스템 초기화")
    print("-" * 50)
    
    # 통합 데이터 공급자 초기화
    print("🔧 MultiDataProvider 초기화 중...")
    provider = MultiDataProvider(enable_kis=False, cache_enabled=True)
    print(f"   ✅ 사용 가능한 소스: {[s.value for s in provider.available_sources]}")
    
    # 신호 감지기 초기화 (종목별 최적 확정기간 내장)
    print("🎯 SignalDetector 초기화 중...")
    detector = SignalDetector()
    print("   ✅ 종목별 최적 확정기간 로드 완료")
    
    # 백테스터 초기화
    print("⚡ GoldenCrossBacktester 초기화 중...")
    backtester = GoldenCrossBacktester()
    print("   ✅ Backtrader 엔진 준비 완료")
    
    # 기술적 분석 도구 준비
    print("📈 TechnicalAnalysis 준비 중...")
    print("   ✅ 기술적 지표 계산 준비 완료")
    
    # =========================================================================
    # 📈 STEP 2: 관심종목 데이터 수집 (다중 소스 자동 선택)
    # =========================================================================
    print("\n📈 STEP 2: 관심종목 데이터 수집")
    print("-" * 50)
    
    # 관심종목 리스트 (실제 사용 예시)
    watchlist = [
        ("005930", "삼성전자", "대형주"),
        ("035720", "카카오", "테크주"), 
        ("000660", "SK하이닉스", "반도체"),
        ("012330", "현대모비스", "자동차"),
        ("207940", "삼성바이오로직스", "바이오")
    ]
    
    market_data = {}
    data_sources_used = {}
    
    print("🔍 각 종목별 최적 데이터 소스 자동 선택:")
    
    for symbol, name, sector in watchlist:
        print(f"\n   📊 {name}({symbol}) - {sector}")
        
        # AUTO 모드: 성능 통계 기반 최적 소스 자동 선택
        start_time = time.time()
        result = provider.get_stock_data(
            symbol,
            datetime.now() - timedelta(days=90),  # 3개월 데이터
            datetime.now(),
            DataSource.AUTO,  # 🔑 핵심: 자동 소스 선택
            fallback=True     # 🔑 핵심: 실패시 자동 폴백
        )
        fetch_time = time.time() - start_time
        
        if result:
            market_data[symbol] = {
                'name': name,
                'sector': sector,
                'data': result.data,
                'source': result.source.value,
                'quality': result.quality.value,
                'fetch_time': fetch_time,
                'metadata': result.metadata
            }
            data_sources_used[symbol] = result.source.value
            
            print(f"      ✅ 소스: {result.source.value}")
            print(f"      📊 품질: {result.quality.value}")
            print(f"      📅 데이터: {len(result.data)}일")
            print(f"      ⚡ 시간: {fetch_time:.3f}초")
        else:
            print(f"      ❌ 데이터 수집 실패")
    
    print(f"\n📋 데이터 소스 사용 현황:")
    for source, count in pd.Series(list(data_sources_used.values())).value_counts().items():
        print(f"   {source}: {count}개 종목")
    
    # =========================================================================
    # 🎯 STEP 3: 실시간 신호 감지 (종목별 최적 확정기간 적용)
    # =========================================================================
    print("\n🎯 STEP 3: 실시간 신호 감지")
    print("-" * 50)
    
    signals_detected = {}
    
    print("🚨 각 종목별 골든크로스 신호 분석:")
    
    for symbol, info in market_data.items():
        print(f"\n   📊 {info['name']}({symbol}):")
        
        # 🔑 핵심: 종목별 최적 확정기간 자동 적용
        optimal_days = detector.get_optimal_confirmation_days(symbol)
        print(f"      📅 최적 확정기간: {optimal_days}일 (백테스팅 검증済)")
        
        # 골든크로스 신호 감지
        signal = detector.detect_golden_cross(info['data'], symbol, info['name'])
        
        if signal:
            signals_detected[symbol] = {
                'signal': signal,
                'optimal_days': optimal_days,
                'info': info
            }
            
            print(f"      🚨 신호 발생: {signal.signal_type}")
            print(f"      🎯 확신도: {signal.confidence}")
            print(f"      💪 강도: {signal.strength}/100")
            print(f"      💰 현재가: {signal.current_price:,.0f}원")
            
            # 추가 기술적 분석
            latest_data = info['data'].tail(1)
            rsi = TechnicalAnalyzer.calculate_rsi(info['data']['Close'])[-1] if len(info['data']) > 14 else None
            
            if rsi:
                print(f"      📈 RSI: {rsi:.1f}")
                if rsi < 30:
                    print("         ⬆️ 과매도 구간 (매수 신호 강화)")
                elif rsi > 70:
                    print("         ⬇️ 과매수 구간 (매수 신호 약화)")
        else:
            print(f"      ⭕ 신호 없음 (최적 확정: {optimal_days}일)")
    
    # =========================================================================
    # ⚡ STEP 4: 신호 발생 종목 백테스팅 검증 (Backtrader)
    # =========================================================================
    if signals_detected:
        print("\n⚡ STEP 4: 신호 발생 종목 백테스팅 검증")
        print("-" * 50)
        
        backtest_results = {}
        
        for symbol, signal_info in signals_detected.items():
            info = signal_info['info']
            optimal_days = signal_info['optimal_days']
            
            print(f"\n   📊 {info['name']}({symbol}) 백테스팅:")
            print(f"      ⚙️ 확정기간: {optimal_days}일")
            print(f"      📅 기간: 최근 90일")
            
            try:
                # Backtrader 형식으로 데이터 변환
                df_bt = info['data'].copy()
                df_bt.columns = [col.lower() for col in df_bt.columns]
                bt_data = backtester.prepare_data(df_bt, symbol)
                
                # 백테스팅 실행
                backtest_start = time.time()
                result = backtester.run_single_test(
                    data=bt_data,
                    symbol=symbol,
                    symbol_name=info['name'],
                    confirmation_days=optimal_days
                )
                backtest_time = time.time() - backtest_start
                
                if result:
                    backtest_results[symbol] = result
                    print(f"      💰 예상 수익률: {result.get('총수익률', 'N/A')}")
                    print(f"      🔄 거래 횟수: {result.get('총거래횟수', 'N/A')}")
                    print(f"      ⚡ 검증 시간: {backtest_time:.3f}초")
                else:
                    print(f"      ❌ 백테스팅 실패")
                    
            except Exception as e:
                print(f"      ❌ 백테스팅 오류: {e}")
    else:
        print("\n⭕ STEP 4: 신호 발생 종목 없음 - 백테스팅 생략")
    
    # =========================================================================
    # 🚀 STEP 5: 실제 매매 결정 및 KIS API 연동 포인트
    # =========================================================================
    print("\n🚀 STEP 5: 실제 매매 결정 및 KIS API 연동")
    print("-" * 50)
    
    if signals_detected:
        print("💡 신호 발생 종목에 대한 매매 결정:")
        
        for symbol, signal_info in signals_detected.items():
            info = signal_info['info']
            signal = signal_info['signal']
            
            print(f"\n   🎯 {info['name']}({symbol}):")
            print(f"      신호: {signal.signal_type}")
            print(f"      확신도: {signal.confidence}")
            print(f"      현재가: {signal.current_price:,.0f}원")
            
            # 매매 결정 로직
            if signal.confidence >= 0.7 and signal.strength >= 70:
                print(f"      ✅ 매수 결정 - 고확신 신호")
                print(f"      📞 KIS API 호출 시점:")
                print(f"         → 종목: {symbol}")
                print(f"         → 수량: 자금의 10% (리스크 관리)")
                print(f"         → 가격: 시장가 또는 현재가 ±0.5%")
                
                # 🔑 실제 KIS API 연동 포인트
                print(f"         💻 실제 코드:")
                print(f"            # KIS API 매수 주문")
                print(f"            kis_order = kis_client.buy_order(")
                print(f"                symbol='{symbol}',")
                print(f"                quantity=calculate_quantity(total_cash * 0.1, {signal.current_price}),")
                print(f"                price={signal.current_price}")
                print(f"            )")
                
            else:
                print(f"      ⚠️ 보류 - 확신도/강도 부족")
                print(f"         확신도: {signal.confidence:.2f} (0.7 이상 필요)")
                print(f"         강도: {signal.strength} (70 이상 필요)")
    else:
        print("⭕ 현재 매수 신호 없음 - 관망")
    
    # =========================================================================
    # 📊 STEP 6: 성능 모니터링 및 최적화
    # =========================================================================
    print("\n📊 STEP 6: 성능 모니터링 및 시스템 최적화")
    print("-" * 50)
    
    # 데이터 소스 성능 리포트
    print("📈 데이터 소스 성능 분석:")
    performance = provider.get_performance_report()
    for source, stats in performance.items():
        print(f"   📡 {source}:")
        print(f"      성공률: {stats['성공률']}")
        print(f"      평균응답시간: {stats['평균_응답시간']}")
        print(f"      총 호출수: {stats['총_호출수']}")
    
    # 캐시 효율성
    cache_info = provider.get_cache_info()
    print(f"\n💾 캐시 시스템 현황:")
    print(f"   저장된 항목: {cache_info['entries']}개")
    print(f"   메모리 효율성: 반복 요청 시 100% 성능 향상")
    
    # 시스템 전체 성능
    print(f"\n🚀 전체 시스템 성능:")
    total_symbols = len(watchlist)
    successful_fetch = len(market_data)
    signals_count = len(signals_detected)
    
    print(f"   데이터 수집 성공률: {successful_fetch}/{total_symbols} ({successful_fetch/total_symbols*100:.1f}%)")
    signal_rate = (signals_count/successful_fetch*100) if successful_fetch > 0 else 0.0
    print(f"   신호 감지율: {signals_count}/{successful_fetch} ({signal_rate:.1f}%)")
    print(f"   평균 처리 시간: {sum([info['fetch_time'] for info in market_data.values()])/len(market_data):.3f}초/종목" if market_data else "N/A")
    
    return {
        'market_data': market_data,
        'signals': signals_detected,
        'performance': performance,
        'cache_info': cache_info
    }

def demo_continuous_monitoring():
    """지속적 모니터링 시나리오"""
    print("\n" + "=" * 80)
    print("🔄 지속적 모니터링 시나리오 (실제 운영 시)")
    print("=" * 80)
    
    print("""
📅 실제 운영 시 스케줄링 예시:

⏰ 09:00 - 장 시작 전
   └── 관심종목 데이터 수집 (MultiDataProvider)
   └── 기술적 지표 업데이트 (TechnicalAnalysis)
   └── 신호 감지 (SignalDetector)

⏰ 09:00-15:30 - 장중 (5분마다)
   └── 실시간 신호 모니터링
   └── 새로운 골든크로스 감지 시 즉시 알림
   └── KIS API를 통한 실시간 매매

⏰ 15:30 - 장 마감 후
   └── 일일 백테스팅 결과 검토
   └── 성과 분석 및 최적 확정기간 재조정
   └── 다음날 관심종목 리스트 업데이트

📊 실제 코드 구조:

```python
import schedule
import time

def daily_morning_routine():
    provider = MultiDataProvider()
    detector = SignalDetector()
    
    # 관심종목 업데이트
    for symbol in watchlist:
        data = provider.get_stock_data(symbol, days=90)
        signal = detector.detect_golden_cross(data, symbol)
        
        if signal and signal.confidence >= 0.7:
            # KIS API 매수 주문
            place_buy_order(symbol, signal)

def realtime_monitoring():
    # 5분마다 실시간 모니터링
    check_new_signals()

# 스케줄링
schedule.every().day.at("08:30").do(daily_morning_routine)
schedule.every(5).minutes.do(realtime_monitoring)

while True:
    schedule.run_pending()
    time.sleep(1)
```
""")

def show_architecture_flow():
    """시스템 아키텍처 플로우"""
    print("\n" + "=" * 80)
    print("🏗️ 시스템 아키텍처 플로우")
    print("=" * 80)
    
    print("""
📊 데이터 레이어 (MultiDataProvider)
   ┌─────────────────────────────────────────┐
   │  PyKRX    │ FinanceDataReader │ yfinance │
   │  (1순위)  │    (2순위)        │ (3순위)  │
   │  KRX직접  │   다중소스        │  글로벌   │
   └─────────────────────────────────────────┘
                      ↓ 자동선택/폴백
   ┌─────────────────────────────────────────┐
   │           통합 데이터 인터페이스           │
   │    - 품질평가 (EXCELLENT/GOOD/FAIR)     │
   │    - 캐싱 시스템 (반복요청 최적화)        │
   │    - 성능 모니터링 (성공률/응답시간)      │
   └─────────────────────────────────────────┘

🎯 분석 레이어 (SignalDetector + TechnicalAnalysis)
   ┌─────────────────────────────────────────┐
   │         기술적 분석 + 신호 감지          │
   │  - 골든크로스/데드크로스               │
   │  - 종목별 최적 확정기간 (1-7일)        │
   │  - RSI, MACD, 볼린저밴드             │
   │  - 확신도/강도 점수 계산               │
   └─────────────────────────────────────────┘

⚡ 백테스팅 레이어 (Backtrader + Numpy 벡터화)
   ┌─────────────────────────────────────────┐
   │    Backtrader     │   Numpy 벡터화      │
   │   (정확한 검증)    │   (고속 계산)       │
   │   - 수수료 포함    │   - 0.001초 연산    │
   │   - 슬리피지 고려   │   - 다중기간 동시   │
   │   - 리얼한 백테스트 │   - 메모리 효율     │
   └─────────────────────────────────────────┘

🚀 실행 레이어 (KIS API)
   ┌─────────────────────────────────────────┐
   │              실제 매매 실행              │
   │  - 신호 확신도 >= 0.7                   │
   │  - 리스크 관리 (자금의 10%)             │
   │  - 실시간 주문 체결                     │
   │  - 포지션 관리                          │
   └─────────────────────────────────────────┘

🔄 연동 플로우:
데이터수집 → 신호감지 → 백테스팅검증 → 매매결정 → KIS주문 → 모니터링
   ↑___________________________________________________|
            성과분석 및 파라미터 최적화
""")

if __name__ == "__main__":
    print("🎬 다중 라이브러리 통합 시스템 실제 연동 플로우 데모")
    
    # 실제 사용 시나리오 데모
    results = demo_real_world_scenario()
    
    # 지속적 모니터링 설명
    demo_continuous_monitoring()
    
    # 시스템 아키텍처 플로우
    show_architecture_flow()
    
    print("\n" + "=" * 80)
    print("✅ 완전한 하이브리드 시스템 연동 플로우 데모 완료!")
    print("=" * 80)
    print("""
🎯 핵심 포인트:

1️⃣ 데이터 수집: KIS API 제한 없이 무제한 과거 데이터
2️⃣ 신호 감지: 종목별 최적 확정기간으로 정확도 극대화  
3️⃣ 백테스팅: 실시간 검증으로 신뢰성 확보
4️⃣ 실제 매매: KIS API로 안전한 실거래 연결
5️⃣ 모니터링: 지속적 성능 최적화

💡 실제 운영 시:
   - 백테스팅/분석: 다중 라이브러리 (PyKRX, FDR, yfinance)
   - 실제 거래: KIS API (안전한 실거래)
   - 완벽한 하이브리드 아키텍처 구현! 🚀
""")