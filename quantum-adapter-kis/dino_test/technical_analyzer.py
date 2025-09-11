"""
디노테스트 기술 영역 분석기

기술 영역 4개 지표를 평가하여 0~4점 범위에서 점수를 산출합니다:
1. OBV (±1점)
2. RSI (±1점) 
3. 투자심리 (±1점)
4. 기타지표 (±1점)
"""

import logging
import pandas as pd
import pandas_ta as ta
from typing import Optional, Dict, Any
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class TechnicalData:
    """기술분석 데이터 구조"""
    # 차트 데이터
    chart_data: Optional[pd.DataFrame] = None  # OHLCV 데이터
    
    # 계산된 지표들
    obv_current: Optional[float] = None        # 현재 OBV
    obv_2years_ago: Optional[float] = None     # 2년전 OBV
    rsi_current: Optional[float] = None        # 현재 RSI
    stochastic_current: Optional[float] = None # 현재 Stochastic %K
    macd_current: Optional[float] = None       # 현재 MACD
    macd_signal: Optional[float] = None        # MACD Signal
    
    # 가격 데이터
    price_current: Optional[float] = None      # 현재 주가
    price_2years_ago: Optional[float] = None   # 2년전 주가

@dataclass
class TechnicalScoreDetail:
    """기술분석 점수 상세 내역"""
    obv_score: int = 0                         # OBV 점수
    rsi_score: int = 0                         # RSI 점수  
    sentiment_score: int = 0                   # 투자심리 점수
    other_indicator_score: int = 0             # 기타지표 점수
    
    total_score: int = 0                       # 최종 점수 (0~5점)
    
    # 상세 계산 결과
    obv_change_rate: Optional[float] = None    # OBV 2년 변화율 (%)
    price_change_rate: Optional[float] = None  # 주가 2년 변화율 (%)
    rsi_value: Optional[float] = None          # RSI 값
    stochastic_value: Optional[float] = None   # Stochastic 값
    macd_value: Optional[float] = None         # MACD 값
    obv_status: Optional[str] = None           # OBV 상태 설명

class DinoTestTechnicalAnalyzer:
    """디노테스트 기술 영역 분석기"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_obv_score(self, technical_data: TechnicalData) -> tuple[int, Optional[float], Optional[str]]:
        """
        OBV 점수 계산 (±1점)
        
        판단 기준:
        - OBV 2년 변화율 > 0%이고 주가도 상승: +1점 (OBV 만족)
        - OBV 2년 변화율 < 0%이고 주가도 하락: +1점 (OBV 만족)
        - OBV와 주가 변화율이 반대 방향: -1점 (OBV 불만족)
        - 나머지 경우: 0점
        """
        if (technical_data.obv_current is None or 
            technical_data.obv_2years_ago is None or
            technical_data.price_current is None or
            technical_data.price_2years_ago is None):
            self.logger.warning("OBV 계산을 위한 데이터 부족")
            return 0, None, "데이터 부족"
        
        # OBV 변화율 계산
        if technical_data.obv_2years_ago == 0:
            obv_change_rate = 0
        else:
            obv_change_rate = (technical_data.obv_current - technical_data.obv_2years_ago) / abs(technical_data.obv_2years_ago) * 100
        
        # 주가 변화율 계산  
        price_change_rate = (technical_data.price_current - technical_data.price_2years_ago) / technical_data.price_2years_ago * 100
        
        # 판단 로직
        obv_direction = 1 if obv_change_rate > 0 else -1 if obv_change_rate < 0 else 0
        price_direction = 1 if price_change_rate > 0 else -1 if price_change_rate < 0 else 0
        
        if obv_direction == price_direction and obv_direction != 0:
            # OBV와 주가 같은 방향 → 만족
            score = 1
            status = "OBV 만족 (추세 일치)"
        elif obv_direction != price_direction and obv_direction != 0 and price_direction != 0:
            # OBV와 주가 반대 방향 → 불만족
            score = -1
            status = "OBV 불만족 (추세 불일치)"
        else:
            # 중립
            score = 0
            status = "OBV 중립"
        
        self.logger.info(f"OBV: {status}, 변화율: {obv_change_rate:.2f}%, 점수: {score}")
        return score, obv_change_rate, status
    
    def calculate_rsi_score(self, technical_data: TechnicalData) -> tuple[int, Optional[float]]:
        """
        RSI 점수 계산 (±1점)
        
        일반적인 RSI 기준:
        - RSI 30 이하: 과매도 구간 → 매수 시점 (+1점)
        - RSI 70 이상: 과매수 구간 → 매도 시점 (-1점)  
        - RSI 30~70: 중립 구간 (0점)
        """
        if technical_data.rsi_current is None:
            self.logger.warning("RSI 계산을 위한 데이터 부족")
            return 0, None
        
        rsi = technical_data.rsi_current
        
        if rsi <= 30:
            score = 1  # 과매도 → 매수 기회
        elif rsi >= 70:
            score = -1  # 과매수 → 위험 신호
        else:
            score = 0  # 중립
        
        self.logger.info(f"RSI: {rsi:.2f}, 점수: {score}")
        return score, rsi
    
    def calculate_sentiment_score(self, technical_data: TechnicalData) -> tuple[int, Optional[float]]:
        """
        투자심리 점수 계산 (±1점)
        
        Stochastic Oscillator 기준:
        - 투자심리도 25 이하: 침체 → 매수 시점 (+1점)
        - 투자심리도 75 이상: 과열 → 매도 시점 (-1점)  
        - 투자심리도 25~75: 중립 구간 (0점)
        """
        if hasattr(technical_data, 'stochastic_current') and technical_data.stochastic_current is not None:
            stochastic = technical_data.stochastic_current
        else:
            self.logger.warning("투자심리(Stochastic) 계산을 위한 데이터 부족")
            return 0, None
        
        if stochastic <= 25:
            score = 1  # 침체 → 매수 기회
        elif stochastic >= 75:
            score = -1  # 과열 → 위험 신호
        else:
            score = 0  # 중립
        
        self.logger.info(f"투자심리(Stochastic): {stochastic:.2f}%, 점수: {score}")
        return score, stochastic
    
    def calculate_other_indicator_score(self, technical_data: TechnicalData) -> tuple[int, Optional[float]]:
        """
        기타지표 점수 계산 (±1점)
        
        MACD 기준:
        - MACD > Signal: 상승 추세 → (+1점)
        - MACD < Signal: 하락 추세 → (-1점)  
        - MACD ≈ Signal: 중립 (0점)
        """
        if (hasattr(technical_data, 'macd_current') and technical_data.macd_current is not None and
            hasattr(technical_data, 'macd_signal') and technical_data.macd_signal is not None):
            macd = technical_data.macd_current
            signal = technical_data.macd_signal
        else:
            self.logger.warning("MACD 계산을 위한 데이터 부족")
            return 0, None
        
        # MACD와 Signal 차이 계산
        macd_diff = macd - signal
        
        if macd_diff > 0.01:  # 작은 임계값 설정
            score = 1  # 상승 추세
            status = "상승 추세"
        elif macd_diff < -0.01:
            score = -1  # 하락 추세
            status = "하락 추세"
        else:
            score = 0  # 중립
            status = "중립"
        
        self.logger.info(f"MACD: {macd:.4f}, Signal: {signal:.4f}, {status}, 점수: {score}")
        return score, macd
    
    def calculate_chart_data_with_indicators(self, chart_data: pd.DataFrame) -> TechnicalData:
        """
        차트 데이터로부터 기술지표 계산
        
        Args:
            chart_data: OHLCV 데이터 (pandas DataFrame)
                       컬럼: date, open, high, low, close, volume
        
        Returns:
            TechnicalData: 계산된 기술지표 데이터
        """
        if chart_data is None or chart_data.empty:
            return TechnicalData()
        
        # 데이터 정렬 (오래된 순)
        chart_data = chart_data.sort_values('date')
        
        try:
            # OBV 계산
            obv = ta.obv(chart_data['close'], chart_data['volume'])
            
            # RSI 계산 (기본 14일)
            rsi = ta.rsi(chart_data['close'], length=14)
            
            # Stochastic 계산 (기본 14, 3, 3)
            stoch = ta.stoch(chart_data['high'], chart_data['low'], chart_data['close'])
            stoch_k = stoch['STOCHk_14_3_3'] if stoch is not None and 'STOCHk_14_3_3' in stoch.columns else None
            
            # MACD 계산 (기본 12, 26, 9)
            macd_data = ta.macd(chart_data['close'])
            macd = macd_data['MACD_12_26_9'] if macd_data is not None and 'MACD_12_26_9' in macd_data.columns else None
            macd_signal = macd_data['MACDs_12_26_9'] if macd_data is not None and 'MACDs_12_26_9' in macd_data.columns else None
            
            # 현재 값들
            obv_current = obv.iloc[-1] if not obv.empty else None
            rsi_current = rsi.iloc[-1] if not rsi.empty else None
            stoch_current = stoch_k.iloc[-1] if stoch_k is not None and not stoch_k.empty else None
            macd_current = macd.iloc[-1] if macd is not None and not macd.empty else None
            macd_signal_current = macd_signal.iloc[-1] if macd_signal is not None and not macd_signal.empty else None
            price_current = chart_data['close'].iloc[-1]
            
            # 비교 기준점 설정 (실제 데이터 길이에 따라 조정)
            if len(chart_data) >= 500:
                # 500일 이상 데이터가 있으면 500일 전 데이터 사용 (2년)
                obv_2years_ago = obv.iloc[-501] if len(obv) > 500 else None
                price_2years_ago = chart_data['close'].iloc[-501] if len(chart_data) > 500 else None
            elif len(chart_data) >= 252:  # 1년 이상
                # 1년 데이터만 있으면 첫 번째 데이터와 비교 (1년 변화율)
                obv_2years_ago = obv.iloc[0] if len(obv) > 0 else None
                price_2years_ago = chart_data['close'].iloc[0] if len(chart_data) > 0 else None
            elif len(chart_data) >= 30:  # 최소 30일 이상
                # 짧은 데이터라도 첫 번째 데이터와 비교 (단기 추세)
                obv_2years_ago = obv.iloc[0] if len(obv) > 0 else None
                price_2years_ago = chart_data['close'].iloc[0] if len(chart_data) > 0 else None
            else:
                # 데이터가 너무 부족하면 None
                obv_2years_ago = None
                price_2years_ago = None
            
            return TechnicalData(
                chart_data=chart_data,
                obv_current=obv_current,
                obv_2years_ago=obv_2years_ago,
                rsi_current=rsi_current,
                stochastic_current=stoch_current,
                macd_current=macd_current,
                macd_signal=macd_signal_current,
                price_current=price_current,
                price_2years_ago=price_2years_ago
            )
            
        except Exception as e:
            self.logger.error(f"기술지표 계산 실패: {e}")
            return TechnicalData(chart_data=chart_data)
    
    def calculate_total_technical_score(self, technical_data: TechnicalData) -> TechnicalScoreDetail:
        """
        디노테스트 기술 영역 최종 점수 계산
        
        기술 영역 4개 지표:
        1. OBV (±1점)
        2. RSI (±1점)  
        3. 투자심리 (±1점) - 향후 구현
        4. 기타지표 (±1점) - 향후 구현
        """
        self.logger.info("=== 디노테스트 기술 영역 점수 계산 시작 ===")
        
        # OBV 점수 계산
        obv_score, obv_change_rate, obv_status = self.calculate_obv_score(technical_data)
        
        # RSI 점수 계산
        rsi_score, rsi_value = self.calculate_rsi_score(technical_data)
        
        # 투자심리 점수 계산 (Stochastic)
        sentiment_score, stochastic_value = self.calculate_sentiment_score(technical_data)
        
        # 기타지표 점수 계산 (MACD)
        other_score, macd_value = self.calculate_other_indicator_score(technical_data)
        
        # 주가 변화율 계산 (참고용)
        price_change_rate = None
        if technical_data.price_current and technical_data.price_2years_ago:
            price_change_rate = (technical_data.price_current - technical_data.price_2years_ago) / technical_data.price_2years_ago * 100
        
        # 총 점수 계산 (0~5점) - 공식: MAX(0,MIN(5,2+SUM(점수들)))
        individual_sum = obv_score + rsi_score + sentiment_score + other_score
        total_score = max(0, min(5, 2 + individual_sum))
        
        self.logger.info(f"기술 영역 총 점수: {total_score}/5점 (개별 합계: {individual_sum})")
        self.logger.info("=== 디노테스트 기술 영역 점수 계산 완료 ===")
        
        return TechnicalScoreDetail(
            obv_score=obv_score,
            rsi_score=rsi_score,
            sentiment_score=sentiment_score,
            other_indicator_score=other_score,
            total_score=total_score,
            obv_change_rate=obv_change_rate,
            price_change_rate=price_change_rate,
            rsi_value=rsi_value,
            stochastic_value=stochastic_value,
            macd_value=macd_value,
            obv_status=obv_status
        )