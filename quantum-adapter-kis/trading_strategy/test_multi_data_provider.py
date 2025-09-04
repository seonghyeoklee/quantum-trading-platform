#!/usr/bin/env python3
"""
통합 데이터 공급자 테스트
MultiDataProvider의 자동 선택 및 폴백 기능 테스트
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import logging
import time

# 프로젝트 경로 추가
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir.parent))

from core.multi_data_provider import MultiDataProvider, DataSource, DataQuality

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)

def test_auto_source_selection():
    """자동 소스 선택 테스트"""
    print("=" * 70)
    print("🤖 자동 소스 선택 테스트")
    print("=" * 70)
    
    provider = MultiDataProvider(enable_kis=False)
    
    # 삼성전자 데이터 요청 (AUTO 모드)
    symbol = "005930"
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    print(f"\n📊 {symbol} 데이터 요청 (최근 30일, AUTO 모드)")
    
    start_time = time.time()
    result = provider.get_stock_data(symbol, start_date, end_date, DataSource.AUTO)
    end_time = time.time()
    
    if result:
        print(f"✅ 성공!")
        print(f"  📈 데이터 소스: {result.source.value}")
        print(f"  📊 데이터 품질: {result.quality.value}")
        print(f"  📅 데이터 기간: {len(result.data)}일")
        print(f"  ⚡ 응답 시간: {end_time - start_time:.3f}초")
        print(f"  💾 메타데이터: {result.metadata}")
        
        # 샘플 데이터 출력
        print(f"\n📈 샘플 데이터:")
        print(result.data.tail(3).to_string())
        
        return True
    else:
        print("❌ 데이터 조회 실패")
        return False

def test_specific_sources():
    """특정 소스 지정 테스트"""
    print("\n" + "=" * 70)
    print("🎯 특정 소스 지정 테스트")
    print("=" * 70)
    
    provider = MultiDataProvider(enable_kis=False)
    symbol = "005930"
    start_date = datetime.now() - timedelta(days=10)
    end_date = datetime.now()
    
    sources_to_test = [
        DataSource.PYKRX,
        DataSource.FINANCE_DATAREADER,
        DataSource.YFINANCE
    ]
    
    results = {}
    
    for source in sources_to_test:
        print(f"\n📡 {source.value} 테스트:")
        
        start_time = time.time()
        result = provider.get_stock_data(symbol, start_date, end_date, source, fallback=False)
        end_time = time.time()
        
        if result:
            print(f"  ✅ 성공 - {len(result.data)}일, {end_time - start_time:.3f}초")
            print(f"  🏆 품질: {result.quality.value}")
            results[source] = {
                'success': True,
                'days': len(result.data),
                'time': end_time - start_time,
                'quality': result.quality
            }
        else:
            print(f"  ❌ 실패")
            results[source] = {'success': False}
    
    # 결과 비교
    print(f"\n📊 소스별 성능 비교:")
    for source, result in results.items():
        if result['success']:
            print(f"  {source.value:20}: {result['days']}일, {result['time']:.3f}초, {result['quality'].value}")
        else:
            print(f"  {source.value:20}: 실패")
    
    return results

def test_fallback_mechanism():
    """폴백 메커니즘 테스트"""
    print("\n" + "=" * 70)
    print("🔄 폴백 메커니즘 테스트")
    print("=" * 70)
    
    provider = MultiDataProvider(enable_kis=False)
    
    # 존재하지 않는 종목으로 테스트 (일부 소스에서 실패할 것)
    symbols_to_test = [
        ("005930", "정상 종목"),
        ("999999", "존재하지 않는 종목"),
        ("AAPL", "해외 종목")
    ]
    
    for symbol, description in symbols_to_test:
        print(f"\n🧪 {description} 테스트: {symbol}")
        
        start_time = time.time()
        result = provider.get_stock_data(
            symbol, 
            datetime.now() - timedelta(days=7), 
            datetime.now(),
            DataSource.AUTO,
            fallback=True
        )
        end_time = time.time()
        
        if result:
            print(f"  ✅ 성공: {result.source.value}")
            print(f"  📊 {len(result.data)}일 데이터, {end_time - start_time:.3f}초")
        else:
            print(f"  ❌ 모든 소스에서 실패")

def test_data_quality():
    """데이터 품질 평가 테스트"""
    print("\n" + "=" * 70)
    print("🏆 데이터 품질 평가 테스트")
    print("=" * 70)
    
    provider = MultiDataProvider(enable_kis=False)
    
    symbols = ["005930", "035720", "000660"]  # 삼성전자, 카카오, SK하이닉스
    
    for symbol in symbols:
        print(f"\n📊 {symbol} 품질 분석:")
        
        result = provider.get_stock_data(
            symbol,
            datetime.now() - timedelta(days=20),
            datetime.now(),
            DataSource.AUTO
        )
        
        if result:
            df = result.data
            print(f"  📈 소스: {result.source.value}")
            print(f"  🏆 품질: {result.quality.value}")
            print(f"  📅 데이터 수: {len(df)}일")
            print(f"  ❌ 결측치: {df.isnull().sum().sum()}개")
            
            # 가격 범위 확인
            if 'Close' in df.columns:
                print(f"  💰 가격 범위: {df['Close'].min():.0f} ~ {df['Close'].max():.0f}")
                print(f"  📊 평균 거래량: {df['Volume'].mean():,.0f}" if 'Volume' in df.columns else "")

def test_performance_stats():
    """성능 통계 테스트"""
    print("\n" + "=" * 70)
    print("📈 성능 통계 테스트")
    print("=" * 70)
    
    provider = MultiDataProvider(enable_kis=False)
    
    # 여러 종목으로 다양한 요청 실행
    symbols = ["005930", "035720", "000660", "012330", "207940"]
    
    print("📊 여러 종목 데이터 요청 중...")
    for symbol in symbols:
        result = provider.get_stock_data(
            symbol,
            datetime.now() - timedelta(days=15),
            datetime.now(),
            DataSource.AUTO
        )
        if result:
            print(f"  ✅ {symbol}: {result.source.value}")
    
    # 성능 리포트 출력
    print(f"\n📈 성능 리포트:")
    report = provider.get_performance_report()
    
    for source, stats in report.items():
        print(f"  {source}:")
        for key, value in stats.items():
            print(f"    {key}: {value}")

def test_caching():
    """캐싱 기능 테스트"""
    print("\n" + "=" * 70)
    print("💾 캐싱 기능 테스트")
    print("=" * 70)
    
    provider = MultiDataProvider(enable_kis=False, cache_enabled=True)
    
    symbol = "005930"
    start_date = datetime.now() - timedelta(days=10)
    end_date = datetime.now()
    
    # 첫 번째 요청 (캐시 없음)
    print("📊 첫 번째 요청 (캐시 없음):")
    start_time = time.time()
    result1 = provider.get_stock_data(symbol, start_date, end_date)
    time1 = time.time() - start_time
    print(f"  ⏰ 시간: {time1:.3f}초")
    
    # 두 번째 요청 (캐시 있음)
    print("\n📊 두 번째 요청 (캐시 사용):")
    start_time = time.time()
    result2 = provider.get_stock_data(symbol, start_date, end_date)
    time2 = time.time() - start_time
    print(f"  ⏰ 시간: {time2:.3f}초")
    
    if time2 < time1:
        print(f"  ✅ 캐싱 효과: {(time1 - time2) / time1 * 100:.1f}% 속도 향상")
    
    # 캐시 정보 출력
    cache_info = provider.get_cache_info()
    print(f"\n💾 캐시 정보: {cache_info}")

if __name__ == "__main__":
    print("🚀 통합 데이터 공급자 테스트 시작")
    
    test_results = []
    
    # 각 테스트 실행
    test_results.append(("자동 소스 선택", test_auto_source_selection()))
    specific_results = test_specific_sources()
    test_fallback_mechanism()
    test_data_quality()
    test_performance_stats()
    test_caching()
    
    # 최종 결과
    print("\n" + "=" * 70)
    print("🎉 테스트 결과 요약")
    print("=" * 70)
    
    for test_name, success in test_results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{test_name:20} : {status}")
    
    print("\n💡 통합 데이터 공급자의 장점:")
    print("  ✅ 자동 소스 선택으로 최적 성능")
    print("  ✅ 폴백 메커니즘으로 높은 안정성")
    print("  ✅ 데이터 품질 평가로 신뢰성 확보")
    print("  ✅ 성능 통계 기반 지능형 최적화")
    print("  ✅ 캐싱으로 빠른 응답 속도")
    
    print("\n✅ 통합 데이터 공급자 테스트 완료!")