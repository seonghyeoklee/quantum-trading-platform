"""
KIS API 기반 간단한 데이터 공급자
섹터 트레이딩을 위한 단순화된 데이터 제공자
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging
import requests

# trading_strategy 모듈 경로 추가
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir.parent / 'trading_strategy'))

# KIS 데이터 제공자 import
try:
    from trading_strategy.core.kis_data_provider import KISDataProvider
    logger = logging.getLogger(__name__)
    logger.info("KISDataProvider import 성공")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"KISDataProvider import 실패: {e}")

class KISSimpleDataProvider:
    """KIS API 기반 섹터 트레이딩용 데이터 공급자"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Args:
            base_url: KIS Adapter FastAPI 서버 주소
        """
        self.kis_provider = KISDataProvider(base_url)
        logger.info("KIS 기반 SimpleDataProvider 초기화 완료")
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """현재가 조회"""
        try:
            price_info = self.kis_provider.get_current_price(symbol)
            
            # KIS API 응답에서 현재가 추출 (응답 구조에 따라 조정 필요)
            if price_info and 'data' in price_info:
                return float(price_info['data'].get('current_price', 0))
            elif price_info and 'current_price' in price_info:
                return float(price_info['current_price'])
            else:
                logger.warning(f"현재가 정보 구조 확인 필요: {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"현재가 조회 실패 ({symbol}): {e}")
            return None
    
    def get_historical_data(self, symbol: str, days: int = 100) -> pd.DataFrame:
        """과거 데이터 조회"""
        try:
            chart_data = self.kis_provider.get_chart_data(symbol, period="D", count=days)
            
            if chart_data is not None and not chart_data.empty:
                logger.debug(f"과거 데이터 조회 성공: {symbol} ({len(chart_data)}일)")
                return chart_data
            else:
                logger.warning(f"과거 데이터 없음: {symbol}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"과거 데이터 조회 실패 ({symbol}): {e}")
            return pd.DataFrame()
    
    def get_comprehensive_data(self, symbol: str) -> Dict[str, Any]:
        """종목 종합 데이터 조회"""
        try:
            return self.kis_provider.get_comprehensive_data(symbol)
        except Exception as e:
            logger.error(f"종합 데이터 조회 실패 ({symbol}): {e}")
            return {"symbol": symbol, "error": str(e)}
    
    def get_moving_averages(self, symbol: str, periods: List[int] = [5, 20, 60]) -> Dict[int, float]:
        """이동평균선 조회"""
        try:
            comprehensive_data = self.get_comprehensive_data(symbol)
            
            moving_averages = {}
            for period in periods:
                key = f'sma_{period}'
                if key in comprehensive_data and comprehensive_data[key] is not None:
                    moving_averages[period] = comprehensive_data[key]
                else:
                    # 차트 데이터에서 직접 계산
                    chart_data = comprehensive_data.get('chart_data')
                    if chart_data is not None and not chart_data.empty and 'close' in chart_data.columns:
                        if len(chart_data) >= period:
                            moving_averages[period] = chart_data['close'].rolling(period).mean().iloc[-1]
                        else:
                            logger.warning(f"이동평균 계산 불가: {symbol} (데이터 {len(chart_data)}일 < {period}일)")
            
            return moving_averages
            
        except Exception as e:
            logger.error(f"이동평균 조회 실패 ({symbol}): {e}")
            return {}
    
    def get_rsi(self, symbol: str, period: int = 14) -> Optional[float]:
        """RSI 조회"""
        try:
            comprehensive_data = self.get_comprehensive_data(symbol)
            
            # KISDataProvider에서 이미 계산된 RSI 사용
            if 'rsi_14' in comprehensive_data and comprehensive_data['rsi_14'] is not None:
                return comprehensive_data['rsi_14']
            
            # 차트 데이터에서 직접 계산
            chart_data = comprehensive_data.get('chart_data')
            if chart_data is not None and not chart_data.empty and 'close' in chart_data.columns:
                return self._calculate_rsi(chart_data['close'], period)
            
            return None
            
        except Exception as e:
            logger.error(f"RSI 조회 실패 ({symbol}): {e}")
            return None
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> Optional[float]:
        """RSI 계산"""
        try:
            if len(prices) < period + 1:
                return None
                
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.iloc[-1] if not rsi.empty else None
            
        except Exception:
            return None
    
    def get_volume_analysis(self, symbol: str) -> Dict[str, Any]:
        """거래량 분석"""
        try:
            comprehensive_data = self.get_comprehensive_data(symbol)
            
            analysis = {}
            
            # 현재 거래량 (현재가 정보에서)
            current_price_data = comprehensive_data.get('current_price', {})
            if current_price_data and 'volume' in current_price_data:
                analysis['current_volume'] = current_price_data['volume']
            
            # 평균 거래량
            if 'volume_avg_20' in comprehensive_data:
                analysis['avg_volume_20'] = comprehensive_data['volume_avg_20']
                
                if analysis.get('current_volume') and analysis['avg_volume_20']:
                    analysis['volume_ratio'] = analysis['current_volume'] / analysis['avg_volume_20']
            
            # 차트 데이터에서 거래량 분석
            chart_data = comprehensive_data.get('chart_data')
            if chart_data is not None and not chart_data.empty and 'volume' in chart_data.columns:
                recent_volume = chart_data['volume'].iloc[-1] if len(chart_data) > 0 else 0
                avg_volume = chart_data['volume'].rolling(20).mean().iloc[-1] if len(chart_data) >= 20 else None
                
                analysis.update({
                    'recent_volume': recent_volume,
                    'volume_trend': 'increasing' if len(chart_data) > 1 and recent_volume > chart_data['volume'].iloc[-2] else 'decreasing'
                })
                
                if avg_volume:
                    analysis['volume_surge'] = recent_volume / avg_volume > 2.0  # 2배 이상 급증
            
            return analysis
            
        except Exception as e:
            logger.error(f"거래량 분석 실패 ({symbol}): {e}")
            return {}
    
    def get_price_momentum(self, symbol: str, days: int = 5) -> Dict[str, Any]:
        """가격 모멘텀 분석"""
        try:
            chart_data = self.get_historical_data(symbol, days * 2)  # 여유분 확보
            
            if chart_data.empty or 'close' in chart_data.columns:
                return {}
            
            if len(chart_data) < days:
                return {}
            
            recent_prices = chart_data['close'].tail(days)
            momentum = {}
            
            # 가격 변화율
            momentum['price_change'] = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0] * 100
            
            # 연속 상승/하락 일수
            price_diff = recent_prices.diff()
            consecutive_up = 0
            consecutive_down = 0
            
            for diff in price_diff.tail(days-1):
                if diff > 0:
                    consecutive_up += 1
                    consecutive_down = 0
                elif diff < 0:
                    consecutive_down += 1
                    consecutive_up = 0
                else:
                    break
            
            momentum['consecutive_up_days'] = consecutive_up
            momentum['consecutive_down_days'] = consecutive_down
            
            # 변동성 (표준편차)
            momentum['volatility'] = recent_prices.pct_change().std() * 100
            
            return momentum
            
        except Exception as e:
            logger.error(f"가격 모멘텀 분석 실패 ({symbol}): {e}")
            return {}
    
    def is_golden_cross(self, symbol: str) -> bool:
        """골든크로스 확인"""
        try:
            ma_data = self.get_moving_averages(symbol, [5, 20])
            
            if 5 in ma_data and 20 in ma_data:
                return ma_data[5] > ma_data[20]
            
            return False
            
        except Exception as e:
            logger.error(f"골든크로스 확인 실패 ({symbol}): {e}")
            return False
    
    def is_dead_cross(self, symbol: str) -> bool:
        """데드크로스 확인"""
        try:
            ma_data = self.get_moving_averages(symbol, [5, 20])
            
            if 5 in ma_data and 20 in ma_data:
                return ma_data[5] < ma_data[20]
            
            return False
            
        except Exception as e:
            logger.error(f"데드크로스 확인 실패 ({symbol}): {e}")
            return False
    
    def get_sector_strength(self, symbols: List[str]) -> Dict[str, float]:
        """섹터 강도 분석"""
        try:
            strength_scores = {}
            
            for symbol in symbols:
                try:
                    # 가격 모멘텀
                    momentum = self.get_price_momentum(symbol)
                    momentum_score = momentum.get('price_change', 0)
                    
                    # 거래량 분석
                    volume_analysis = self.get_volume_analysis(symbol)
                    volume_score = 10 if volume_analysis.get('volume_surge', False) else 0
                    
                    # RSI (과매수/과매도 반영)
                    rsi = self.get_rsi(symbol)
                    rsi_score = 0
                    if rsi:
                        if 30 <= rsi <= 70:  # 정상 범위
                            rsi_score = 5
                        elif rsi < 30:  # 과매도
                            rsi_score = 8
                        else:  # 과매수
                            rsi_score = -5
                    
                    # 종합 점수
                    total_score = momentum_score + volume_score + rsi_score
                    strength_scores[symbol] = total_score
                    
                except Exception as e:
                    logger.warning(f"종목 {symbol} 강도 분석 실패: {e}")
                    strength_scores[symbol] = 0
            
            return strength_scores
            
        except Exception as e:
            logger.error(f"섹터 강도 분석 실패: {e}")
            return {}

# 하위 호환성을 위한 별칭
SimpleDataProvider = KISSimpleDataProvider