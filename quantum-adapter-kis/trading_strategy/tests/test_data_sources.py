#!/usr/bin/env python3
"""
다중 데이터 소스 라이브러리 테스트
PyKRX, FinanceDataReader, yfinance 기능 확인
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import logging

# 프로젝트 경로 추가
current_dir = Path(__file__).parent
sys.path.append(str(current_dir.parent))

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)

def test_pykrx():
    """PyKRX 테스트 - KRX 직접 데이터"""
    print("=" * 70)
    print("🔍 PyKRX 테스트 (KRX 직접 스크래핑)")
    print("=" * 70)
    
    try:
        from pykrx import stock
        
        # 1. 종목 리스트 조회
        print("\n📊 1. KRX 종목 리스트 조회")
        today = datetime.now().strftime("%Y%m%d")
        kospi_stocks = stock.get_market_ticker_list(today, market="KOSPI")[:5]
        print(f"✅ KOSPI 종목 (상위 5개): {kospi_stocks}")
        
        # 2. 삼성전자 주가 데이터 (최근 10일)
        print("\n📈 2. 삼성전자(005930) 주가 데이터")
        start_date = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d")
        end_date = datetime.now().strftime("%Y%m%d")
        
        df = stock.get_market_ohlcv_by_date(start_date, end_date, "005930")
        print(f"✅ PyKRX 데이터 ({len(df)}일):")
        print(df.tail(3).to_string())
        
        # 3. 거래량 데이터
        print("\n📊 3. 거래량 및 거래대금")
        volume_data = stock.get_market_trading_volume_by_date(start_date, end_date, "005930")
        print(f"✅ 평균 거래량: {volume_data['거래량'].mean():,.0f}")
        
        return True
        
    except Exception as e:
        print(f"❌ PyKRX 테스트 실패: {e}")
        return False

def test_finance_datareader():
    """FinanceDataReader 테스트 - 다중 소스 데이터"""
    print("\n" + "=" * 70)
    print("🔍 FinanceDataReader 테스트 (다중 소스)")
    print("=" * 70)
    
    try:
        import FinanceDataReader as fdr
        
        # 1. 삼성전자 주가 데이터 (최근 10일)
        print("\n📈 1. 삼성전자(005930) 주가 데이터")
        start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        df = fdr.DataReader("005930", start_date, end_date)
        print(f"✅ FinanceDataReader 데이터 ({len(df)}일):")
        print(df.tail(3).to_string())
        
        # 2. 코스피 지수 데이터
        print("\n📊 2. 코스피 지수(KS11) 데이터")
        kospi_df = fdr.DataReader("KS11", start_date, end_date)
        print(f"✅ 코스피 지수 최근값: {kospi_df['Close'].iloc[-1]:.2f}")
        
        # 3. KRX 종목 리스트
        print("\n📋 3. KRX 종목 리스트")
        krx_stocks = fdr.StockListing("KRX")
        print(f"✅ 전체 종목 수: {len(krx_stocks)}개")
        print(f"✅ 대형주 5개:\n{krx_stocks.head(5)[['Name', 'Market']].to_string()}")
        
        return True
        
    except Exception as e:
        print(f"❌ FinanceDataReader 테스트 실패: {e}")
        return False

def test_yfinance():
    """yfinance 테스트 - Yahoo Finance 데이터"""
    print("\n" + "=" * 70)
    print("🔍 yfinance 테스트 (Yahoo Finance)")
    print("=" * 70)
    
    try:
        import yfinance as yf
        
        # 1. 삼성전자 주가 데이터 (한국 주식은 .KS 접미사)
        print("\n📈 1. 삼성전자(005930.KS) 주가 데이터")
        samsung = yf.Ticker("005930.KS")
        df = samsung.history(period="10d")
        
        if not df.empty:
            print(f"✅ yfinance 데이터 ({len(df)}일):")
            print(df.tail(3)[['Open', 'High', 'Low', 'Close', 'Volume']].to_string())
        else:
            print("⚠️ 데이터 없음 - 다른 종목으로 테스트")
            
        # 2. 코스피 ETF 데이터 (EWY - iShares MSCI South Korea ETF)
        print("\n📊 2. 한국 ETF(EWY) 데이터")
        ewy = yf.Ticker("EWY")
        ewy_df = ewy.history(period="10d")
        print(f"✅ EWY ETF 최근값: ${ewy_df['Close'].iloc[-1]:.2f}")
        
        # 3. 환율 데이터 (USD/KRW)
        print("\n💱 3. 환율(USD/KRW) 데이터")
        usdkrw = yf.Ticker("USDKRW=X")
        krw_df = usdkrw.history(period="5d")
        if not krw_df.empty:
            print(f"✅ USD/KRW 환율: {krw_df['Close'].iloc[-1]:.2f}")
        else:
            print("⚠️ 환율 데이터 없음")
        
        return True
        
    except Exception as e:
        print(f"❌ yfinance 테스트 실패: {e}")
        return False

def test_data_source_comparison():
    """데이터 소스 간 비교 테스트"""
    print("\n" + "=" * 70)
    print("🔍 데이터 소스 비교 분석")
    print("=" * 70)
    
    results = {
        'PyKRX': {'status': False, 'data_points': 0, 'speed': 0},
        'FinanceDataReader': {'status': False, 'data_points': 0, 'speed': 0},
        'yfinance': {'status': False, 'data_points': 0, 'speed': 0}
    }
    
    # 삼성전자 데이터 비교
    symbol = "005930"
    period_days = 30
    
    print(f"\n📊 {period_days}일간 {symbol} 데이터 비교:")
    
    # PyKRX 테스트
    try:
        from pykrx import stock
        import time
        
        start_time = time.time()
        start_date = (datetime.now() - timedelta(days=period_days)).strftime("%Y%m%d")
        end_date = datetime.now().strftime("%Y%m%d")
        
        pykrx_data = stock.get_market_ohlcv_by_date(start_date, end_date, symbol)
        pykrx_time = time.time() - start_time
        
        results['PyKRX']['status'] = True
        results['PyKRX']['data_points'] = len(pykrx_data)
        results['PyKRX']['speed'] = pykrx_time
        
        print(f"✅ PyKRX: {len(pykrx_data)}일, {pykrx_time:.2f}초")
        
    except Exception as e:
        print(f"❌ PyKRX 비교 실패: {e}")
    
    # FinanceDataReader 테스트
    try:
        import FinanceDataReader as fdr
        import time
        
        start_time = time.time()
        start_date = (datetime.now() - timedelta(days=period_days)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        fdr_data = fdr.DataReader(symbol, start_date, end_date)
        fdr_time = time.time() - start_time
        
        results['FinanceDataReader']['status'] = True
        results['FinanceDataReader']['data_points'] = len(fdr_data)
        results['FinanceDataReader']['speed'] = fdr_time
        
        print(f"✅ FinanceDataReader: {len(fdr_data)}일, {fdr_time:.2f}초")
        
    except Exception as e:
        print(f"❌ FinanceDataReader 비교 실패: {e}")
    
    # yfinance 테스트 (한국 주식)
    try:
        import yfinance as yf
        import time
        
        start_time = time.time()
        yf_ticker = yf.Ticker(f"{symbol}.KS")
        yf_data = yf_ticker.history(period="1mo")  # 1개월
        yf_time = time.time() - start_time
        
        results['yfinance']['status'] = True
        results['yfinance']['data_points'] = len(yf_data)
        results['yfinance']['speed'] = yf_time
        
        print(f"✅ yfinance: {len(yf_data)}일, {yf_time:.2f}초")
        
    except Exception as e:
        print(f"❌ yfinance 비교 실패: {e}")
    
    # 결과 요약
    print(f"\n📋 성능 요약:")
    for source, result in results.items():
        if result['status']:
            print(f"  {source}: {result['data_points']}일, {result['speed']:.2f}초")
        else:
            print(f"  {source}: 실패")
    
    return results

if __name__ == "__main__":
    print("🚀 다중 데이터 소스 라이브러리 테스트 시작")
    
    # 개별 테스트
    test_results = []
    test_results.append(("PyKRX", test_pykrx()))
    test_results.append(("FinanceDataReader", test_finance_datareader()))
    test_results.append(("yfinance", test_yfinance()))
    
    # 비교 테스트
    comparison = test_data_source_comparison()
    
    # 최종 결과
    print("\n" + "=" * 70)
    print("🎉 테스트 결과 요약")
    print("=" * 70)
    
    for name, success in test_results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{name:20} : {status}")
    
    print("\n💡 권장 사용법:")
    print("  - PyKRX: 한국 주식 실시간 정확한 데이터")  
    print("  - FinanceDataReader: 다양한 소스, 장기 데이터")
    print("  - yfinance: 글로벌 주식, ETF, 환율 데이터")
    
    print("\n✅ 다중 데이터 소스 테스트 완료!")