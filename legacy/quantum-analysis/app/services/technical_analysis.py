import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from decimal import Decimal
from app.models.candle import StockCandle

class TechnicalAnalysisService:
    """기술적 분석 서비스"""
    
    @staticmethod
    def candles_to_dataframe(candles: List[StockCandle]) -> pd.DataFrame:
        """캔들 데이터를 pandas DataFrame으로 변환"""
        data = []
        for candle in candles:
            data.append({
                'timestamp': candle.timestamp,
                'open': float(candle.open_price),
                'high': float(candle.high_price),
                'low': float(candle.low_price),
                'close': float(candle.close_price),
                'volume': candle.volume,
                'symbol': candle.symbol,
                'timeframe': candle.timeframe
            })
        
        df = pd.DataFrame(data)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)
        
        return df
    
    @staticmethod
    def calculate_sma(df: pd.DataFrame, period: int = 20, price_column: str = 'close') -> pd.Series:
        """단순이동평균 (Simple Moving Average)"""
        return df[price_column].rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int = 20, price_column: str = 'close') -> pd.Series:
        """지수이동평균 (Exponential Moving Average)"""
        return df[price_column].ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14, price_column: str = 'close') -> pd.Series:
        """상대강도지수 (Relative Strength Index)"""
        delta = df[price_column].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0, 
                                price_column: str = 'close') -> Dict[str, pd.Series]:
        """볼린저 밴드 (Bollinger Bands)"""
        sma = df[price_column].rolling(window=period).mean()
        std = df[price_column].rolling(window=period).std()
        
        return {
            'upper_band': sma + (std * std_dev),
            'middle_band': sma,
            'lower_band': sma - (std * std_dev)
        }
    
    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast_period: int = 12, slow_period: int = 26, 
                      signal_period: int = 9, price_column: str = 'close') -> Dict[str, pd.Series]:
        """MACD (Moving Average Convergence Divergence)"""
        ema_fast = df[price_column].ewm(span=fast_period).mean()
        ema_slow = df[price_column].ewm(span=slow_period).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def calculate_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """스토캐스틱 (Stochastic Oscillator)"""
        lowest_low = df['low'].rolling(window=k_period).min()
        highest_high = df['high'].rolling(window=k_period).max()
        
        k_percent = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return {
            'k_percent': k_percent,
            'd_percent': d_percent
        }
    
    @staticmethod
    def calculate_williams_r(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """윌리엄스 %R (Williams %R)"""
        highest_high = df['high'].rolling(window=period).max()
        lowest_low = df['low'].rolling(window=period).min()
        
        williams_r = -100 * ((highest_high - df['close']) / (highest_high - lowest_low))
        return williams_r
    
    @staticmethod
    def calculate_cci(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """상품채널지수 (Commodity Channel Index)"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        sma_tp = typical_price.rolling(window=period).mean()
        mean_deviation = typical_price.rolling(window=period).apply(
            lambda x: np.mean(np.abs(x - x.mean())), raw=True
        )
        cci = (typical_price - sma_tp) / (0.015 * mean_deviation)
        return cci
    
    @staticmethod
    def calculate_adx(df: pd.DataFrame, period: int = 14) -> Dict[str, pd.Series]:
        """평균방향지수 (Average Directional Index)"""
        high_diff = df['high'].diff()
        low_diff = df['low'].diff()
        
        plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
        minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
        
        tr1 = df['high'] - df['low']
        tr2 = (df['high'] - df['close'].shift()).abs()
        tr3 = (df['low'] - df['close'].shift()).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = true_range.rolling(window=period).mean()
        plus_di = 100 * (pd.Series(plus_dm).rolling(window=period).mean() / atr)
        minus_di = 100 * (pd.Series(minus_dm).rolling(window=period).mean() / atr)
        
        dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
        adx = dx.rolling(window=period).mean()
        
        return {
            'adx': adx,
            'plus_di': plus_di,
            'minus_di': minus_di
        }
    
    @staticmethod
    def calculate_support_resistance(df: pd.DataFrame, window: int = 20) -> Dict[str, List[float]]:
        """지지/저항선 계산 (피봇 포인트 기반)"""
        highs = df['high'].rolling(window=window, center=True).max()
        lows = df['low'].rolling(window=window, center=True).min()
        
        # 피봇 고점/저점 찾기
        pivot_highs = []
        pivot_lows = []
        
        for i in range(window, len(df) - window):
            if df['high'].iloc[i] == highs.iloc[i]:
                pivot_highs.append(float(df['high'].iloc[i]))
            if df['low'].iloc[i] == lows.iloc[i]:
                pivot_lows.append(float(df['low'].iloc[i]))
        
        return {
            'resistance_levels': sorted(set(pivot_highs), reverse=True)[:5],  # 상위 5개
            'support_levels': sorted(set(pivot_lows))[:5]  # 하위 5개
        }
    
    @staticmethod
    def analyze_trend(df: pd.DataFrame, short_period: int = 10, long_period: int = 50) -> Dict[str, Any]:
        """추세 분석"""
        if len(df) < long_period:
            return {'trend': 'insufficient_data', 'strength': 0.0}
        
        short_sma = TechnicalAnalysisService.calculate_sma(df, short_period)
        long_sma = TechnicalAnalysisService.calculate_sma(df, long_period)
        
        # 현재 추세 판단
        current_short = short_sma.iloc[-1]
        current_long = long_sma.iloc[-1]
        current_price = df['close'].iloc[-1]
        
        if current_short > current_long and current_price > current_short:
            trend = 'uptrend'
            strength = min((current_short - current_long) / current_long * 100, 100)
        elif current_short < current_long and current_price < current_short:
            trend = 'downtrend'
            strength = min((current_long - current_short) / current_long * 100, 100)
        else:
            trend = 'sideways'
            strength = abs(current_short - current_long) / current_long * 100
        
        return {
            'trend': trend,
            'strength': float(strength),
            'current_price': float(current_price),
            'short_sma': float(current_short),
            'long_sma': float(current_long)
        }
    
    @staticmethod
    def calculate_volatility(df: pd.DataFrame, period: int = 20) -> Dict[str, float]:
        """변동성 계산"""
        returns = df['close'].pct_change().dropna()
        
        # 기본 변동성 (표준편차)
        volatility = returns.rolling(window=period).std() * np.sqrt(252)  # 연환산
        
        # ATR (Average True Range) 기반 변동성
        tr1 = df['high'] - df['low']
        tr2 = (df['high'] - df['close'].shift()).abs()
        tr3 = (df['low'] - df['close'].shift()).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return {
            'price_volatility': float(volatility.iloc[-1]) if not volatility.empty else 0.0,
            'atr': float(atr.iloc[-1]) if not atr.empty else 0.0,
            'atr_percentage': float(atr.iloc[-1] / df['close'].iloc[-1] * 100) if not atr.empty else 0.0
        }
    
    @staticmethod
    def identify_candlestick_patterns(candle: StockCandle, prev_candles: List[StockCandle] = None) -> List[str]:
        """캔들스틱 패턴 인식"""
        patterns = []
        
        body_size = candle.body_size()
        upper_shadow = candle.upper_shadow_length()
        lower_shadow = candle.lower_shadow_length()
        total_range = candle.high_price - candle.low_price
        
        # 도지 패턴
        if body_size / total_range < 0.1:
            patterns.append('doji')
        
        # 해머 패턴
        if (candle.is_bullish() and 
            lower_shadow > body_size * 2 and 
            upper_shadow < body_size * 0.5):
            patterns.append('hammer')
        
        # 행잉맨 패턴
        if (candle.is_bearish() and 
            lower_shadow > body_size * 2 and 
            upper_shadow < body_size * 0.5):
            patterns.append('hanging_man')
        
        # 유성 패턴
        if (upper_shadow > body_size * 2 and 
            lower_shadow < body_size * 0.5):
            patterns.append('shooting_star')
        
        # 장대양봉/음봉
        if body_size / total_range > 0.7:
            if candle.is_bullish():
                patterns.append('long_white_candle')
            else:
                patterns.append('long_black_candle')
        
        return patterns
    
    @staticmethod
    def comprehensive_analysis(df: pd.DataFrame) -> Dict[str, Any]:
        """종합 기술적 분석"""
        if df.empty or len(df) < 50:
            return {'error': 'Insufficient data for analysis'}
        
        analysis = {}
        
        # 이동평균
        analysis['sma_20'] = float(TechnicalAnalysisService.calculate_sma(df, 20).iloc[-1])
        analysis['sma_50'] = float(TechnicalAnalysisService.calculate_sma(df, 50).iloc[-1])
        analysis['ema_12'] = float(TechnicalAnalysisService.calculate_ema(df, 12).iloc[-1])
        analysis['ema_26'] = float(TechnicalAnalysisService.calculate_ema(df, 26).iloc[-1])
        
        # 오실레이터
        analysis['rsi'] = float(TechnicalAnalysisService.calculate_rsi(df).iloc[-1])
        
        macd_data = TechnicalAnalysisService.calculate_macd(df)
        analysis['macd'] = float(macd_data['macd'].iloc[-1])
        analysis['macd_signal'] = float(macd_data['signal'].iloc[-1])
        analysis['macd_histogram'] = float(macd_data['histogram'].iloc[-1])
        
        stoch_data = TechnicalAnalysisService.calculate_stochastic(df)
        analysis['stoch_k'] = float(stoch_data['k_percent'].iloc[-1])
        analysis['stoch_d'] = float(stoch_data['d_percent'].iloc[-1])
        
        # 볼린저 밴드
        bb_data = TechnicalAnalysisService.calculate_bollinger_bands(df)
        analysis['bb_upper'] = float(bb_data['upper_band'].iloc[-1])
        analysis['bb_middle'] = float(bb_data['middle_band'].iloc[-1])
        analysis['bb_lower'] = float(bb_data['lower_band'].iloc[-1])
        
        current_price = df['close'].iloc[-1]
        analysis['bb_position'] = (current_price - analysis['bb_lower']) / (analysis['bb_upper'] - analysis['bb_lower'])
        
        # 추세 분석
        trend_analysis = TechnicalAnalysisService.analyze_trend(df)
        analysis.update(trend_analysis)
        
        # 변동성
        volatility_data = TechnicalAnalysisService.calculate_volatility(df)
        analysis.update(volatility_data)
        
        # 지지/저항선
        support_resistance = TechnicalAnalysisService.calculate_support_resistance(df)
        analysis.update(support_resistance)
        
        # 매매 신호 생성
        analysis['signals'] = TechnicalAnalysisService.generate_trading_signals(analysis)
        
        return analysis
    
    @staticmethod
    def generate_trading_signals(analysis: Dict[str, Any]) -> Dict[str, str]:
        """기술적 분석 기반 매매 신호 생성"""
        signals = {}
        
        # RSI 신호
        rsi = analysis.get('rsi', 50)
        if rsi > 70:
            signals['rsi'] = 'overbought'
        elif rsi < 30:
            signals['rsi'] = 'oversold'
        else:
            signals['rsi'] = 'neutral'
        
        # MACD 신호
        macd = analysis.get('macd', 0)
        signal = analysis.get('macd_signal', 0)
        if macd > signal and analysis.get('macd_histogram', 0) > 0:
            signals['macd'] = 'bullish'
        elif macd < signal and analysis.get('macd_histogram', 0) < 0:
            signals['macd'] = 'bearish'
        else:
            signals['macd'] = 'neutral'
        
        # 볼린저 밴드 신호
        bb_position = analysis.get('bb_position', 0.5)
        if bb_position > 0.8:
            signals['bollinger'] = 'overbought'
        elif bb_position < 0.2:
            signals['bollinger'] = 'oversold'
        else:
            signals['bollinger'] = 'neutral'
        
        # 스토캐스틱 신호
        stoch_k = analysis.get('stoch_k', 50)
        stoch_d = analysis.get('stoch_d', 50)
        if stoch_k > 80 and stoch_d > 80:
            signals['stochastic'] = 'overbought'
        elif stoch_k < 20 and stoch_d < 20:
            signals['stochastic'] = 'oversold'
        else:
            signals['stochastic'] = 'neutral'
        
        # 추세 신호
        trend = analysis.get('trend', 'sideways')
        strength = analysis.get('strength', 0)
        if trend == 'uptrend' and strength > 5:
            signals['trend'] = 'strong_bullish'
        elif trend == 'uptrend':
            signals['trend'] = 'weak_bullish'
        elif trend == 'downtrend' and strength > 5:
            signals['trend'] = 'strong_bearish'
        elif trend == 'downtrend':
            signals['trend'] = 'weak_bearish'
        else:
            signals['trend'] = 'sideways'
        
        # 종합 신호
        bullish_signals = sum(1 for signal in signals.values() 
                            if 'bullish' in signal or 'oversold' in signal)
        bearish_signals = sum(1 for signal in signals.values() 
                            if 'bearish' in signal or 'overbought' in signal)
        
        if bullish_signals >= 3:
            signals['overall'] = 'strong_buy'
        elif bullish_signals >= 2:
            signals['overall'] = 'buy'
        elif bearish_signals >= 3:
            signals['overall'] = 'strong_sell'
        elif bearish_signals >= 2:
            signals['overall'] = 'sell'
        else:
            signals['overall'] = 'hold'
        
        return signals