"""
기술적 분석 모듈
이동평균, RSI, MACD 등 기술적 지표 계산
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class TechnicalAnalyzer:
    """기술적 분석 엔진"""
    
    @staticmethod
    def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
        """
        단순이동평균(SMA) 계산
        
        Args:
            prices: 가격 시리즈
            period: 기간
        
        Returns:
            SMA 시리즈
        """
        return prices.rolling(window=period, min_periods=period).mean()
    
    @staticmethod
    def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
        """
        지수이동평균(EMA) 계산
        
        Args:
            prices: 가격 시리즈
            period: 기간
        
        Returns:
            EMA 시리즈
        """
        return prices.ewm(span=period, adjust=False, min_periods=period).mean()
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        RSI (Relative Strength Index) 계산
        
        Args:
            prices: 가격 시리즈
            period: RSI 기간 (기본 14)
        
        Returns:
            RSI 시리즈
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_macd(prices: pd.Series, 
                      fast_period: int = 12, 
                      slow_period: int = 26, 
                      signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        MACD (Moving Average Convergence Divergence) 계산
        
        Args:
            prices: 가격 시리즈
            fast_period: 빠른 EMA 기간
            slow_period: 느린 EMA 기간
            signal_period: 시그널 라인 EMA 기간
        
        Returns:
            (MACD, Signal Line, Histogram) 튜플
        """
        ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
        ema_slow = prices.ewm(span=slow_period, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal_period, adjust=False).mean()
        histogram = macd - signal_line
        
        return macd, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, 
                                 period: int = 20, 
                                 std_dev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        볼린저 밴드 계산
        
        Args:
            prices: 가격 시리즈
            period: 이동평균 기간
            std_dev: 표준편차 배수
        
        Returns:
            (Upper Band, Middle Band, Lower Band) 튜플
        """
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return upper, middle, lower
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        모든 기술적 지표 계산
        
        Args:
            df: OHLCV 데이터프레임
        
        Returns:
            지표가 추가된 데이터프레임
        """
        # 컬럼명을 소문자로 표준화
        df.columns = df.columns.str.lower()
        
        # 기본 컬럼 확인
        required_columns = ['close', 'volume']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"필수 컬럼이 없습니다: {required_columns}")
        
        df = df.copy()
        
        # 이동평균선 계산
        df['sma5'] = self.calculate_sma(df['close'], 5)
        df['sma20'] = self.calculate_sma(df['close'], 20)
        df['sma60'] = self.calculate_sma(df['close'], 60)
        df['sma120'] = self.calculate_sma(df['close'], 120)
        
        df['ema5'] = self.calculate_ema(df['close'], 5)
        df['ema20'] = self.calculate_ema(df['close'], 20)
        
        # 거래량 이동평균
        df['volume_sma20'] = self.calculate_sma(df['volume'], 20)
        df['volume_ratio'] = df['volume'] / df['volume_sma20']
        
        # RSI 계산
        df['rsi'] = self.calculate_rsi(df['close'])
        df['rsi_signal'] = 'neutral'
        df.loc[df['rsi'] < 30, 'rsi_signal'] = 'oversold'
        df.loc[df['rsi'] > 70, 'rsi_signal'] = 'overbought'
        
        # MACD 계산
        df['macd'], df['signal_line'], df['histogram'] = self.calculate_macd(df['close'])
        
        # 볼린저 밴드
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = self.calculate_bollinger_bands(df['close'])
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # 가격 변화율
        df['change_rate'] = df['close'].pct_change() * 100
        df['change_rate_5d'] = (df['close'] / df['close'].shift(5) - 1) * 100
        df['change_rate_20d'] = (df['close'] / df['close'].shift(20) - 1) * 100
        
        logger.info(f"기술적 지표 계산 완료: {len(df)}개 데이터")
        
        return df
    
    def get_latest_indicators(self, df: pd.DataFrame) -> dict:
        """
        최신 지표 값 반환
        
        Args:
            df: 지표가 계산된 데이터프레임
        
        Returns:
            최신 지표 딕셔너리
        """
        if df.empty:
            return {}
        
        latest = df.iloc[-1]
        
        return {
            'date': str(latest.name) if hasattr(latest, 'name') else None,
            'close': float(latest['close']) if 'close' in latest else None,
            'sma5': float(latest['sma5']) if pd.notna(latest.get('sma5')) else None,
            'sma20': float(latest['sma20']) if pd.notna(latest.get('sma20')) else None,
            'sma60': float(latest['sma60']) if pd.notna(latest.get('sma60')) else None,
            'rsi': float(latest['rsi']) if pd.notna(latest.get('rsi')) else None,
            'rsi_signal': latest.get('rsi_signal', 'neutral'),
            'macd': float(latest['macd']) if pd.notna(latest.get('macd')) else None,
            'volume': int(latest['volume']) if 'volume' in latest else None,
            'volume_ratio': float(latest['volume_ratio']) if pd.notna(latest.get('volume_ratio')) else None,
            'change_rate': float(latest['change_rate']) if pd.notna(latest.get('change_rate')) else None
        }