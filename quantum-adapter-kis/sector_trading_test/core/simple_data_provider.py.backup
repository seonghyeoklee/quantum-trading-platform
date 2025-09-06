"""
간단한 데이터 공급자
PyKRX, yfinance 등을 활용하여 KIS API 없이 주식 데이터 제공
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SimpleDataProvider:
    """간단한 주식 데이터 공급자"""
    
    def __init__(self):
        """초기화"""
        self.available_sources = self._check_available_sources()
        logger.info(f"Available data sources: {self.available_sources}")
    
    def _check_available_sources(self) -> list:
        """사용 가능한 데이터 소스 확인"""
        sources = []
        
        try:
            import pykrx
            sources.append("pykrx")
        except ImportError:
            logger.warning("PyKRX not available")
        
        try:
            import yfinance
            sources.append("yfinance")
        except ImportError:
            logger.warning("yfinance not available")
        
        try:
            import FinanceDataReader as fdr
            sources.append("finance_datareader")
        except ImportError:
            logger.warning("FinanceDataReader not available")
        
        return sources
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """현재가 조회"""
        try:
            # PyKRX로 현재가 조회
            if "pykrx" in self.available_sources:
                from pykrx import stock
                
                # 오늘 날짜
                today = datetime.now().strftime("%Y%m%d")
                
                # 최근 가격 조회
                df = stock.get_market_ohlcv_by_date(
                    fromdate=(datetime.now() - timedelta(days=5)).strftime("%Y%m%d"),
                    todate=today,
                    ticker=symbol
                )
                
                if not df.empty:
                    current_price = df['종가'].iloc[-1]
                    return float(current_price)
            
            # yfinance fallback (한국 주식은 .KS 추가)
            if "yfinance" in self.available_sources:
                import yfinance as yf
                
                ticker = yf.Ticker(f"{symbol}.KS")
                hist = ticker.history(period="1d")
                
                if not hist.empty:
                    return float(hist['Close'].iloc[-1])
            
        except Exception as e:
            logger.error(f"현재가 조회 실패 {symbol}: {e}")
        
        return None
    
    def get_chart_data(self, symbol: str, days: int = 60) -> Optional[pd.DataFrame]:
        """차트 데이터 조회"""
        try:
            if "pykrx" in self.available_sources:
                from pykrx import stock
                
                # 날짜 계산
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                # OHLCV 데이터 조회
                df = stock.get_market_ohlcv_by_date(
                    fromdate=start_date.strftime("%Y%m%d"),
                    todate=end_date.strftime("%Y%m%d"),
                    ticker=symbol
                )
                
                if not df.empty:
                    # 컬럼명을 영어로 변경 (technical analyzer와 호환)
                    # PyKRX는 시가,고가,저가,종가,거래량,거래대금 순서
                    if len(df.columns) >= 5:
                        # 거래대금 컬럼이 있으면 제외
                        df = df.iloc[:, :5]  # 처음 5개 컬럼만 사용
                        df.columns = ['open', 'high', 'low', 'close', 'volume']
                    elif len(df.columns) == 5:
                        df.columns = ['open', 'high', 'low', 'close', 'volume']
                    else:
                        logger.warning(f"예상하지 못한 컬럼 수: {len(df.columns)}")
                        return None
                    
                    # 인덱스를 datetime으로 변환
                    df.index = pd.to_datetime(df.index)
                    
                    return df
            
            # yfinance fallback
            if "yfinance" in self.available_sources:
                import yfinance as yf
                
                ticker = yf.Ticker(f"{symbol}.KS")
                hist = ticker.history(period=f"{days}d")
                
                if not hist.empty:
                    # 컬럼명 소문자로 변경
                    hist.columns = hist.columns.str.lower()
                    return hist
            
        except Exception as e:
            logger.error(f"차트 데이터 조회 실패 {symbol}: {e}")
        
        return None
    
    def get_technical_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """기술적 지표 계산 (간단한 버전)"""
        if df is None or df.empty:
            return {}
        
        try:
            indicators = {}
            
            # 현재가
            if 'close' in df.columns:
                indicators['close'] = float(df['close'].iloc[-1])
            
            # 이동평균선
            if len(df) >= 5:
                indicators['sma5'] = float(df['close'].rolling(5).mean().iloc[-1])
            if len(df) >= 20:
                indicators['sma20'] = float(df['close'].rolling(20).mean().iloc[-1])
            
            # RSI 계산 (간단한 버전)
            if len(df) >= 14:
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                indicators['rsi'] = float(rsi.iloc[-1])
                
                # RSI 시그널
                if indicators['rsi'] < 30:
                    indicators['rsi_signal'] = 'oversold'
                elif indicators['rsi'] > 70:
                    indicators['rsi_signal'] = 'overbought'
                else:
                    indicators['rsi_signal'] = 'neutral'
            
            # 거래량 정보
            if 'volume' in df.columns and len(df) >= 20:
                volume_avg = df['volume'].rolling(20).mean()
                indicators['volume'] = int(df['volume'].iloc[-1])
                indicators['volume_sma20'] = float(volume_avg.iloc[-1])
                indicators['volume_ratio'] = float(df['volume'].iloc[-1] / volume_avg.iloc[-1])
            
            # 가격 변화율
            if len(df) >= 2:
                indicators['change_rate'] = float((df['close'].iloc[-1] / df['close'].iloc[-2] - 1) * 100)
            
            return indicators
            
        except Exception as e:
            logger.error(f"기술적 지표 계산 실패: {e}")
            return {}
    
    def generate_simple_signal(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """간단한 매매 신호 생성"""
        signal = {
            'recommendation': 'HOLD',
            'confidence_score': 0.5,
            'risk_score': 0.5
        }
        
        try:
            # RSI 기반 신호 (더 적극적)
            rsi = indicators.get('rsi')
            if rsi:
                if rsi < 35:  # 과매도 (기준 완화)
                    signal['recommendation'] = 'BUY'
                    signal['confidence_score'] = 0.8 if rsi < 25 else 0.7
                elif rsi > 65:  # 과매수 (기준 완화)
                    signal['recommendation'] = 'SELL'
                    signal['confidence_score'] = 0.8 if rsi > 75 else 0.7
            
            # 이동평균선 기반 추가 신호
            sma5 = indicators.get('sma5')
            sma20 = indicators.get('sma20')
            current_price = indicators.get('close')
            
            if all([sma5, sma20, current_price]):
                # 골든크로스/데드크로스 간단 버전
                if sma5 > sma20 and current_price > sma5:
                    if signal['recommendation'] == 'HOLD':
                        signal['recommendation'] = 'BUY'
                        signal['confidence_score'] = 0.6
                elif sma5 < sma20 and current_price < sma5:
                    if signal['recommendation'] == 'HOLD':
                        signal['recommendation'] = 'SELL'
                        signal['confidence_score'] = 0.6
            
            # 볼린저 밴드 계산 및 위험도 평가
            if 'rsi' in indicators:
                if indicators['rsi'] < 20 or indicators['rsi'] > 80:
                    signal['risk_score'] = 0.8
                elif indicators['rsi'] < 40 or indicators['rsi'] > 60:
                    signal['risk_score'] = 0.3
            
        except Exception as e:
            logger.error(f"신호 생성 실패: {e}")
        
        return signal