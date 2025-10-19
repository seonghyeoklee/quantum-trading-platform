#!/usr/bin/env python3
"""
실제 기술적 지표 테스트

TA-Lib + FinanceDataReader를 사용하여 실제 기술적 지표를 계산해보는 테스트입니다.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys

try:
    import talib
    print("✅ TA-Lib 로드 성공")
    TALIB_AVAILABLE = True
except ImportError as e:
    print(f"❌ TA-Lib 로드 실패: {e}")
    TALIB_AVAILABLE = False

try:
    import FinanceDataReader as fdr
    print("✅ FinanceDataReader 로드 성공")
    FDR_AVAILABLE = True
except ImportError as e:
    print(f"❌ FinanceDataReader 로드 실패: {e}")
    FDR_AVAILABLE = False

def get_stock_data(symbol, days=30):
    """한국 주식 데이터 가져오기"""
    try:
        # 날짜 설정
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # FinanceDataReader로 데이터 가져오기
        df = fdr.DataReader(symbol, start_date, end_date)
        
        if not df.empty:
            print(f"✅ {symbol} 데이터 조회 성공: {len(df)}일치")
            return df
        else:
            print(f"❌ {symbol} 데이터가 비어있습니다")
            return None
            
    except Exception as e:
        print(f"❌ {symbol} 데이터 조회 실패: {e}")
        return None

def calculate_indicators(df):
    """실제 기술적 지표 계산"""
    if df is None or df.empty:
        return None
    
    try:
        # 가격 데이터 추출 (TA-Lib은 float64 타입 필요)
        close_prices = df['Close'].astype(np.float64).values
        high_prices = df['High'].astype(np.float64).values
        low_prices = df['Low'].astype(np.float64).values
        open_prices = df['Open'].astype(np.float64).values
        volumes = df['Volume'].astype(np.float64).values
        
        indicators = {}
        
        if TALIB_AVAILABLE:
            print("📊 TA-Lib으로 기술적 지표 계산 중...")
            
            # RSI (Relative Strength Index)
            rsi = talib.RSI(close_prices, timeperiod=14)
            indicators['RSI'] = float(rsi[-1]) if not np.isnan(rsi[-1]) else None
            
            # MACD (Moving Average Convergence Divergence)
            macd, macdsignal, macdhist = talib.MACD(close_prices, fastperiod=12, slowperiod=26, signalperiod=9)
            indicators['MACD'] = float(macd[-1]) if not np.isnan(macd[-1]) else None
            indicators['MACD_Signal'] = float(macdsignal[-1]) if not np.isnan(macdsignal[-1]) else None
            indicators['MACD_Histogram'] = float(macdhist[-1]) if not np.isnan(macdhist[-1]) else None
            
            # 이동평균선 (EMA)
            ema_5 = talib.EMA(close_prices, timeperiod=5)
            ema_20 = talib.EMA(close_prices, timeperiod=20)
            indicators['EMA_5'] = float(ema_5[-1]) if not np.isnan(ema_5[-1]) else None
            indicators['EMA_20'] = float(ema_20[-1]) if not np.isnan(ema_20[-1]) else None
            
            # 볼린저 밴드
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close_prices, timeperiod=20, nbdevup=2, nbdevdn=2)
            indicators['BB_Upper'] = float(bb_upper[-1]) if not np.isnan(bb_upper[-1]) else None
            indicators['BB_Middle'] = float(bb_middle[-1]) if not np.isnan(bb_middle[-1]) else None
            indicators['BB_Lower'] = float(bb_lower[-1]) if not np.isnan(bb_lower[-1]) else None
            
            # 스토캐스틱
            slowk, slowd = talib.STOCH(high_prices, low_prices, close_prices, fastk_period=14, slowk_period=3, slowd_period=3)
            indicators['Stoch_K'] = float(slowk[-1]) if not np.isnan(slowk[-1]) else None
            indicators['Stoch_D'] = float(slowd[-1]) if not np.isnan(slowd[-1]) else None
            
            # ATR (Average True Range)
            atr = talib.ATR(high_prices, low_prices, close_prices, timeperiod=14)
            indicators['ATR'] = float(atr[-1]) if not np.isnan(atr[-1]) else None
            
            # 거래량 지표
            volume_sma = talib.SMA(volumes.astype(float), timeperiod=20)
            indicators['Volume_SMA'] = float(volume_sma[-1]) if not np.isnan(volume_sma[-1]) else None
            
        else:
            print("❌ TA-Lib을 사용할 수 없어 간단한 계산을 사용합니다")
            indicators = {
                'RSI': None,
                'MACD': None,
                'EMA_5': float(close_prices[-5:].mean()),
                'EMA_20': float(close_prices[-20:].mean()) if len(close_prices) >= 20 else None,
                'BB_Upper': None,
                'BB_Middle': None,
                'BB_Lower': None
            }
        
        # 현재 가격 정보 추가
        indicators['Current_Price'] = float(close_prices[-1])
        indicators['Previous_Close'] = float(close_prices[-2]) if len(close_prices) >= 2 else None
        indicators['Price_Change'] = float(close_prices[-1] - close_prices[-2]) if len(close_prices) >= 2 else None
        indicators['Price_Change_Pct'] = float((close_prices[-1] - close_prices[-2]) / close_prices[-2] * 100) if len(close_prices) >= 2 else None
        indicators['Volume'] = int(volumes[-1])
        indicators['Latest_Date'] = df.index[-1].strftime('%Y-%m-%d')
        
        return indicators
        
    except Exception as e:
        print(f"❌ 지표 계산 오류: {e}")
        return None

def analyze_signals(indicators):
    """매매 신호 분석"""
    if not indicators:
        return None
    
    signals = []
    
    # RSI 신호
    if indicators['RSI']:
        if indicators['RSI'] < 30:
            signals.append("🟢 RSI 과매도 (매수 신호)")
        elif indicators['RSI'] > 70:
            signals.append("🔴 RSI 과매수 (매도 신호)")
        else:
            signals.append("⚪ RSI 중립")
    
    # MACD 신호
    if indicators['MACD'] and indicators['MACD_Signal']:
        if indicators['MACD'] > indicators['MACD_Signal']:
            signals.append("🟢 MACD 상승 (매수 신호)")
        else:
            signals.append("🔴 MACD 하락 (매도 신호)")
    
    # 이동평균 신호
    if indicators['EMA_5'] and indicators['EMA_20']:
        if indicators['EMA_5'] > indicators['EMA_20']:
            signals.append("🟢 단기 상승 추세")
        else:
            signals.append("🔴 단기 하락 추세")
    
    # 볼린저 밴드 신호
    if indicators['BB_Upper'] and indicators['BB_Lower'] and indicators['Current_Price']:
        if indicators['Current_Price'] > indicators['BB_Upper']:
            signals.append("🔴 볼린저 밴드 상단 돌파 (과매수)")
        elif indicators['Current_Price'] < indicators['BB_Lower']:
            signals.append("🟢 볼린저 밴드 하단 터치 (과매도)")
        else:
            signals.append("⚪ 볼린저 밴드 중간 구간")
    
    return signals

def main():
    print("🚀 === 실제 기술적 지표 테스트 ===")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 테스트할 종목들
    symbols = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, NAVER
    symbol_names = {"005930": "삼성전자", "000660": "SK하이닉스", "035420": "NAVER"}
    
    for symbol in symbols:
        print(f"📊 === {symbol_names[symbol]}({symbol}) 분석 ===")
        
        # 데이터 가져오기
        df = get_stock_data(symbol, days=50)
        
        if df is not None:
            # 기술적 지표 계산
            indicators = calculate_indicators(df)
            
            if indicators:
                print(f"✅ 기술적 지표 계산 완료")
                print()
                
                # 현재 가격 정보
                print("💹 **현재 가격 정보**:")
                print(f"   현재가: {indicators['Current_Price']:,.0f}원")
                if indicators['Price_Change']:
                    change_sign = "+" if indicators['Price_Change'] > 0 else ""
                    print(f"   등락: {change_sign}{indicators['Price_Change']:,.0f}원 ({indicators['Price_Change_Pct']:+.2f}%)")
                print(f"   거래량: {indicators['Volume']:,}주")
                print(f"   기준일: {indicators['Latest_Date']}")
                print()
                
                # 기술적 지표
                print("📈 **기술적 지표**:")
                if indicators['RSI']:
                    print(f"   RSI(14): {indicators['RSI']:.1f}")
                if indicators['MACD']:
                    print(f"   MACD: {indicators['MACD']:.2f}")
                    print(f"   MACD Signal: {indicators['MACD_Signal']:.2f}")
                    print(f"   MACD Histogram: {indicators['MACD_Histogram']:.2f}")
                if indicators['EMA_5']:
                    print(f"   EMA(5): {indicators['EMA_5']:,.0f}원")
                if indicators['EMA_20']:
                    print(f"   EMA(20): {indicators['EMA_20']:,.0f}원")
                if indicators['BB_Upper']:
                    print(f"   볼린저 상단: {indicators['BB_Upper']:,.0f}원")
                    print(f"   볼린저 중간: {indicators['BB_Middle']:,.0f}원")
                    print(f"   볼린저 하단: {indicators['BB_Lower']:,.0f}원")
                if indicators['Stoch_K']:
                    print(f"   스토캐스틱 K: {indicators['Stoch_K']:.1f}")
                    print(f"   스토캐스틱 D: {indicators['Stoch_D']:.1f}")
                if indicators['ATR']:
                    print(f"   ATR(14): {indicators['ATR']:,.0f}원")
                print()
                
                # 매매 신호 분석
                signals = analyze_signals(indicators)
                if signals:
                    print("🎯 **매매 신호 분석**:")
                    for signal in signals:
                        print(f"   {signal}")
                print()
            else:
                print("❌ 기술적 지표 계산 실패")
                print()
        else:
            print("❌ 데이터 조회 실패")
            print()
    
    print("🏁 테스트 완료")
    print(f"완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
