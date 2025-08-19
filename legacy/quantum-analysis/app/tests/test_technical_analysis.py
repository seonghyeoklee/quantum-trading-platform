import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.services.technical_analysis import TechnicalAnalysisService
from app.models.candle import StockCandle

class TestTechnicalAnalysisService:
    """기술적 분석 서비스 테스트"""
    
    @pytest.fixture
    def sample_candles(self):
        """테스트용 샘플 캔들 데이터"""
        candles = []
        base_price = 75000
        base_time = datetime(2024, 1, 1, 9, 0)
        
        for i in range(100):
            # 간단한 가격 변동 시뮬레이션
            price_change = np.sin(i * 0.1) * 1000 + np.random.normal(0, 500)
            
            open_price = base_price + price_change
            high_price = open_price + abs(np.random.normal(0, 300))
            low_price = open_price - abs(np.random.normal(0, 300))
            close_price = open_price + np.random.normal(0, 200)
            
            # 가격 유효성 보장
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)
            
            candle = StockCandle(
                symbol="005930",
                timeframe="1d",
                timestamp=base_time + timedelta(days=i),
                open_price=round(open_price, 2),
                high_price=round(high_price, 2),
                low_price=round(low_price, 2),
                close_price=round(close_price, 2),
                volume=np.random.randint(500000, 2000000)
            )
            candles.append(candle)
            base_price = close_price  # 다음 날 기준가
        
        return candles
    
    @pytest.fixture
    def sample_dataframe(self, sample_candles):
        """테스트용 DataFrame"""
        return TechnicalAnalysisService.candles_to_dataframe(sample_candles)
    
    def test_candles_to_dataframe_conversion(self, sample_candles):
        """캔들 데이터를 DataFrame으로 변환 테스트"""
        # when
        df = TechnicalAnalysisService.candles_to_dataframe(sample_candles)
        
        # then
        assert not df.empty
        assert len(df) == len(sample_candles)
        assert list(df.columns) == ['open', 'high', 'low', 'close', 'volume', 'symbol', 'timeframe']
        assert df.index.name == 'timestamp'
        assert df['symbol'].iloc[0] == "005930"
    
    def test_sma_calculation(self, sample_dataframe):
        """단순이동평균 계산 테스트"""
        # when
        sma_20 = TechnicalAnalysisService.calculate_sma(sample_dataframe, 20)
        
        # then
        assert not sma_20.empty
        assert len(sma_20) == len(sample_dataframe)
        assert pd.isna(sma_20.iloc[19]) is False  # 20번째부터 값 존재
        assert pd.isna(sma_20.iloc[18]) is True   # 19번째까지는 NaN
    
    def test_ema_calculation(self, sample_dataframe):
        """지수이동평균 계산 테스트"""
        # when
        ema_12 = TechnicalAnalysisService.calculate_ema(sample_dataframe, 12)
        
        # then
        assert not ema_12.empty
        assert len(ema_12) == len(sample_dataframe)
        assert pd.isna(ema_12.iloc[-1]) is False  # 마지막 값 존재
    
    def test_rsi_calculation(self, sample_dataframe):
        """RSI 계산 테스트"""
        # when
        rsi = TechnicalAnalysisService.calculate_rsi(sample_dataframe, 14)
        
        # then
        assert not rsi.empty
        assert 0 <= rsi.iloc[-1] <= 100  # RSI는 0~100 범위
        assert pd.isna(rsi.iloc[13]) is False  # 14번째부터 값 존재
    
    def test_bollinger_bands_calculation(self, sample_dataframe):
        """볼린저 밴드 계산 테스트"""
        # when
        bb_data = TechnicalAnalysisService.calculate_bollinger_bands(sample_dataframe, 20, 2.0)
        
        # then
        assert 'upper_band' in bb_data
        assert 'middle_band' in bb_data
        assert 'lower_band' in bb_data
        
        # 상단 밴드 > 중간선 > 하단 밴드
        upper = bb_data['upper_band'].iloc[-1]
        middle = bb_data['middle_band'].iloc[-1]
        lower = bb_data['lower_band'].iloc[-1]
        
        assert upper > middle > lower
    
    def test_macd_calculation(self, sample_dataframe):
        """MACD 계산 테스트"""
        # when
        macd_data = TechnicalAnalysisService.calculate_macd(sample_dataframe)
        
        # then
        assert 'macd' in macd_data
        assert 'signal' in macd_data
        assert 'histogram' in macd_data
        
        # 히스토그램 = MACD - Signal
        macd_line = macd_data['macd'].iloc[-1]
        signal_line = macd_data['signal'].iloc[-1]
        histogram = macd_data['histogram'].iloc[-1]
        
        assert abs(histogram - (macd_line - signal_line)) < 1e-10
    
    def test_comprehensive_analysis(self, sample_dataframe):
        """종합 기술적 분석 테스트"""
        # when
        analysis = TechnicalAnalysisService.comprehensive_analysis(sample_dataframe)
        
        # then
        expected_keys = [
            'sma_20', 'sma_50', 'ema_12', 'ema_26', 'rsi',
            'macd', 'macd_signal', 'macd_histogram',
            'bb_upper', 'bb_middle', 'bb_lower', 'bb_position',
            'stoch_k', 'stoch_d', 'trend', 'strength',
            'signals', 'resistance_levels', 'support_levels'
        ]
        
        for key in expected_keys:
            assert key in analysis, f"Missing key: {key}"
        
        # 신호 검증
        signals = analysis['signals']
        assert 'overall' in signals
        assert signals['overall'] in ['strong_buy', 'buy', 'hold', 'sell', 'strong_sell']
    
    def test_trading_signals_generation(self, sample_dataframe):
        """매매 신호 생성 테스트"""
        # given
        analysis = TechnicalAnalysisService.comprehensive_analysis(sample_dataframe)
        
        # when
        signals = TechnicalAnalysisService.generate_trading_signals(analysis)
        
        # then
        expected_indicators = ['rsi', 'macd', 'bollinger', 'stochastic', 'trend', 'overall']
        for indicator in expected_indicators:
            assert indicator in signals
        
        # 신호 값 검증
        valid_signals = ['strong_bullish', 'weak_bullish', 'neutral', 'weak_bearish', 'strong_bearish',
                        'bullish', 'bearish', 'overbought', 'oversold', 'sideways',
                        'strong_buy', 'buy', 'hold', 'sell', 'strong_sell']
        
        for indicator, signal in signals.items():
            assert signal in valid_signals, f"Invalid signal for {indicator}: {signal}"
    
    def test_support_resistance_calculation(self, sample_dataframe):
        """지지/저항선 계산 테스트"""
        # when
        levels = TechnicalAnalysisService.calculate_support_resistance(sample_dataframe, 10)
        
        # then
        assert 'resistance_levels' in levels
        assert 'support_levels' in levels
        assert len(levels['resistance_levels']) <= 5
        assert len(levels['support_levels']) <= 5
        
        # 저항선이 지지선보다 높아야 함
        if levels['resistance_levels'] and levels['support_levels']:
            max_support = max(levels['support_levels'])
            min_resistance = min(levels['resistance_levels'])
            assert min_resistance >= max_support
    
    def test_trend_analysis(self, sample_dataframe):
        """추세 분석 테스트"""
        # when
        trend_data = TechnicalAnalysisService.analyze_trend(sample_dataframe, 10, 50)
        
        # then
        assert 'trend' in trend_data
        assert 'strength' in trend_data
        assert trend_data['trend'] in ['uptrend', 'downtrend', 'sideways']
        assert 0 <= trend_data['strength'] <= 100
    
    def test_volatility_calculation(self, sample_dataframe):
        """변동성 계산 테스트"""
        # when
        volatility_data = TechnicalAnalysisService.calculate_volatility(sample_dataframe, 20)
        
        # then
        assert 'price_volatility' in volatility_data
        assert 'atr' in volatility_data
        assert 'atr_percentage' in volatility_data
        
        assert volatility_data['price_volatility'] >= 0
        assert volatility_data['atr'] >= 0
        assert volatility_data['atr_percentage'] >= 0
    
    def test_insufficient_data_handling(self):
        """데이터 부족시 처리 테스트"""
        # given - 데이터가 부족한 경우
        small_candles = []
        for i in range(10):  # 50개 미만
            candle = StockCandle(
                symbol="005930",
                timeframe="1d",
                timestamp=datetime.now() + timedelta(days=i),
                open_price=75000,
                high_price=76000,
                low_price=74000,
                close_price=75500,
                volume=1000000
            )
            small_candles.append(candle)
        
        df = TechnicalAnalysisService.candles_to_dataframe(small_candles)
        
        # when
        analysis = TechnicalAnalysisService.comprehensive_analysis(df)
        
        # then
        assert 'error' in analysis
        assert 'Insufficient data' in analysis['error']