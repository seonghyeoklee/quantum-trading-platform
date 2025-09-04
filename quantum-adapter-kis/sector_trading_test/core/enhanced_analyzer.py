"""
섹터 트레이딩을 위한 향상된 분석기
trading_strategy 폴더의 기술적 분석 및 신호 감지 모듈 통합
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging

# trading_strategy 모듈 경로 추가
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir.parent / 'trading_strategy'))

try:
    from trading_strategy.core.technical_analysis import TechnicalAnalyzer
    from trading_strategy.core.signal_detector import SignalDetector, TradingSignal, SignalType, ConfidenceLevel
    from trading_strategy.core.multi_data_provider import MultiDataProvider, DataSource
except ImportError as e:
    print(f"trading_strategy 모듈 import 실패: {e}")
    # Fallback classes 정의
    class TechnicalAnalyzer:
        def calculate_all_indicators(self, df):
            return df
        def get_latest_indicators(self, df):
            return {}
    
    class SignalDetector:
        def __init__(self, confirmation_days=1):
            pass
        def detect_golden_cross(self, df, symbol, name):
            return None
    
    class MultiDataProvider:
        def __init__(self, enable_kis=False, cache_enabled=True):
            pass
        def get_stock_data(self, symbol, start_date, end_date, source):
            return None
    
    # Mock classes for compatibility
    class TradingSignal:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def to_dict(self):
            return self.__dict__
    
    class SignalType:
        GOLDEN_CROSS = "GOLDEN_CROSS"
        DEAD_CROSS = "DEAD_CROSS"
    
    class ConfidenceLevel:
        CONFIRMED = "CONFIRMED"
        TENTATIVE = "TENTATIVE" 
        WEAK = "WEAK"
    
    class DataSource:
        AUTO = "AUTO"

# 기존 KIS 모듈들
sys.path.append(str(current_dir.parent / 'examples_llm'))
try:
    import kis_auth as ka
except ImportError:
    print("KIS 모듈 import 실패")

logger = logging.getLogger(__name__)

class SectorAnalysisResult:
    """섹터 분석 결과"""
    def __init__(self, symbol: str, name: str, sector: str):
        self.symbol = symbol
        self.name = name
        self.sector = sector
        self.current_price = None
        self.technical_indicators = {}
        self.trading_signals = []
        self.data_quality = "UNKNOWN"
        self.analysis_timestamp = datetime.now()
        self.recommendation = "HOLD"
        self.confidence_score = 0.0
        self.risk_score = 0.0
        
    def to_dict(self) -> dict:
        return {
            'symbol': self.symbol,
            'name': self.name,
            'sector': self.sector,
            'current_price': self.current_price,
            'technical_indicators': self.technical_indicators,
            'trading_signals': [s.to_dict() if hasattr(s, 'to_dict') else str(s) for s in self.trading_signals],
            'data_quality': self.data_quality,
            'recommendation': self.recommendation,
            'confidence_score': self.confidence_score,
            'risk_score': self.risk_score,
            'analysis_timestamp': self.analysis_timestamp.isoformat()
        }

class EnhancedSectorAnalyzer:
    """향상된 섹터 분석기 - trading_strategy 모듈 통합"""
    
    def __init__(self, use_kis_api: bool = False):
        """
        초기화
        
        Args:
            use_kis_api: KIS API 사용 여부 (기본값 False로 rate limiting 회피)
        """
        self.use_kis_api = use_kis_api
        self.logger = logging.getLogger(__name__)
        
        # trading_strategy 모듈들 초기화
        try:
            self.technical_analyzer = TechnicalAnalyzer()
            self.signal_detector = SignalDetector(confirmation_days=1)
            self.multi_data_provider = MultiDataProvider(
                enable_kis=use_kis_api, 
                cache_enabled=True
            )
        except Exception as e:
            self.logger.error(f"trading_strategy 모듈 초기화 실패: {e}")
            self.technical_analyzer = None
            self.signal_detector = None
            self.multi_data_provider = None
        
        # Simple Data Provider 초기화 (fallback)
        from .simple_data_provider import SimpleDataProvider
        self.simple_data_provider = SimpleDataProvider()
        
        # 데이터 캐시 (API 호출 최소화)
        self.price_cache = {}
        self.chart_data_cache = {}
        self.cache_timestamp = {}
        
        self.logger.info(f"Enhanced Sector Analyzer 초기화 완료 (KIS API: {use_kis_api})")
    
    def analyze_sector_portfolio(self, sectors_config: dict) -> Dict[str, List[SectorAnalysisResult]]:
        """
        전체 섹터 포트폴리오 분석
        
        Args:
            sectors_config: 섹터 설정 딕셔너리
            
        Returns:
            섹터별 분석 결과
        """
        portfolio_analysis = {}
        
        for sector_name, sector_data in sectors_config['sectors'].items():
            self.logger.info(f"\n=== {sector_name} 섹터 분석 시작 ===")
            
            sector_results = []
            
            # 주요 종목 분석
            for stock_type, stock_info in sector_data['stocks'].items():
                symbol = stock_info['symbol']
                name = stock_info['name']
                
                try:
                    result = self.analyze_single_stock(
                        symbol=symbol,
                        name=name,
                        sector=sector_name
                    )
                    sector_results.append(result)
                    
                    self.logger.info(
                        f"{stock_type}: {name}({symbol}) - "
                        f"추천: {result.recommendation}, "
                        f"신뢰도: {result.confidence_score:.2f}"
                    )
                    
                except Exception as e:
                    self.logger.error(f"{name}({symbol}) 분석 실패: {e}")
                    # 빈 결과 객체라도 생성
                    error_result = SectorAnalysisResult(symbol, name, sector_name)
                    error_result.recommendation = "ERROR"
                    sector_results.append(error_result)
            
            portfolio_analysis[sector_name] = sector_results
            self.logger.info(f"{sector_name} 섹터 분석 완료: {len(sector_results)}개 종목")
        
        return portfolio_analysis
    
    def analyze_single_stock(self, symbol: str, name: str, sector: str) -> SectorAnalysisResult:
        """
        개별 종목 분석
        
        Args:
            symbol: 종목 코드
            name: 종목명
            sector: 섹터명
            
        Returns:
            분석 결과
        """
        result = SectorAnalysisResult(symbol, name, sector)
        
        try:
            # 1. 현재가 조회 (캐시 활용)
            current_price = self._get_current_price_cached(symbol)
            if current_price:
                result.current_price = current_price
            
            # 2. 차트 데이터 조회 (다중 데이터 소스 활용)
            chart_data = self._get_chart_data_multi_source(symbol)
            
            if chart_data is not None and not chart_data.empty:
                # 3. 기술적 분석
                technical_indicators = self._calculate_technical_indicators(chart_data)
                result.technical_indicators = technical_indicators
                
                # 4. 매매 신호 감지
                trading_signals = self._detect_trading_signals(
                    chart_data, symbol, name
                )
                result.trading_signals = trading_signals
                
                # 5. 종합 추천 및 신뢰도 계산
                recommendation, confidence = self._generate_recommendation(
                    technical_indicators, trading_signals
                )
                result.recommendation = recommendation
                result.confidence_score = confidence
                
                # 6. 위험도 계산
                risk_score = self._calculate_risk_score(technical_indicators)
                result.risk_score = risk_score
                
                result.data_quality = "GOOD"
                
            else:
                self.logger.warning(f"{symbol} 차트 데이터 없음")
                result.data_quality = "POOR"
                result.recommendation = "HOLD"
                
        except Exception as e:
            self.logger.error(f"{symbol} 분석 중 오류: {e}")
            result.recommendation = "ERROR"
            result.data_quality = "POOR"
        
        return result
    
    def _get_current_price_cached(self, symbol: str) -> Optional[float]:
        """캐시된 현재가 조회 (5분 캐시)"""
        cache_key = f"price_{symbol}"
        now = datetime.now()
        
        # 캐시 확인
        if (cache_key in self.price_cache and 
            cache_key in self.cache_timestamp and
            now - self.cache_timestamp[cache_key] < timedelta(minutes=5)):
            return self.price_cache[cache_key]
        
        # 실제 데이터 조회
        current_price = None
        
        # KIS API 사용하는 경우에만 호출
        if self.use_kis_api:
            try:
                from examples_llm.kis_auth import get_inquire_price
                result = get_inquire_price("demo", symbol)
                
                if isinstance(result, dict) and 'output' in result:
                    current_price = float(result['output']['stck_prpr'])
                elif hasattr(result, 'empty') and not result.empty:
                    if 'stck_prpr' in result.columns:
                        current_price = float(result.iloc[0]['stck_prpr'])
                        
            except Exception as e:
                self.logger.warning(f"KIS API 현재가 조회 실패 {symbol}: {e}")
        
        # Simple Data Provider 활용 (KIS API 실패 시 또는 analysis_only 모드)
        if current_price is None:
            try:
                current_price = self.simple_data_provider.get_current_price(symbol)
            except Exception as e:
                self.logger.warning(f"Simple data provider 현재가 조회 실패 {symbol}: {e}")
        
        # 다중 데이터 소스 활용 (최후 수단)
        if current_price is None and self.multi_data_provider:
            try:
                # 최근 1일 데이터로 현재가 추정
                end_date = datetime.now()
                start_date = end_date - timedelta(days=5)  # 5일 여유
                
                market_data = self.multi_data_provider.get_stock_data(
                    symbol, start_date, end_date, DataSource.AUTO
                )
                
                if market_data and not market_data.data.empty:
                    current_price = float(market_data.data['close'].iloc[-1])
                    
            except Exception as e:
                self.logger.warning(f"Multi data source 현재가 조회 실패 {symbol}: {e}")
        
        # 캐시 저장
        if current_price:
            self.price_cache[cache_key] = current_price
            self.cache_timestamp[cache_key] = now
        
        return current_price
    
    def _get_chart_data_multi_source(self, symbol: str, days: int = 60) -> Optional[pd.DataFrame]:
        """다중 데이터 소스를 활용한 차트 데이터 조회"""
        cache_key = f"chart_{symbol}_{days}"
        now = datetime.now()
        
        # 캐시 확인 (30분 캐시)
        if (cache_key in self.chart_data_cache and 
            cache_key in self.cache_timestamp and
            now - self.cache_timestamp[cache_key] < timedelta(minutes=30)):
            return self.chart_data_cache[cache_key]
        
        chart_data = None
        
        # Simple Data Provider 우선 사용
        try:
            chart_data = self.simple_data_provider.get_chart_data(symbol, days)
        except Exception as e:
            self.logger.warning(f"Simple data provider 차트 조회 실패 {symbol}: {e}")
        
        # 다중 데이터 소스 fallback
        if chart_data is None and self.multi_data_provider:
            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                market_data = self.multi_data_provider.get_stock_data(
                    symbol, start_date, end_date, DataSource.AUTO
                )
                
                if market_data and not market_data.data.empty:
                    chart_data = market_data.data
                    
            except Exception as e:
                self.logger.warning(f"Multi data source 차트 조회 실패 {symbol}: {e}")
        
        # KIS API 사용 (fallback)
        if chart_data is None and self.use_kis_api:
            try:
                # KIS API를 통한 차트 데이터 조회 (기존 코드 활용)
                pass  # 필요시 구현
            except Exception as e:
                self.logger.warning(f"KIS API 차트 조회 실패 {symbol}: {e}")
        
        # 캐시 저장
        if chart_data is not None:
            self.chart_data_cache[cache_key] = chart_data
            self.cache_timestamp[cache_key] = now
        
        return chart_data
    
    def _calculate_technical_indicators(self, df: pd.DataFrame) -> dict:
        """기술적 지표 계산"""
        if df is None or df.empty:
            return {}
        
        try:
            # trading_strategy 모듈이 있는 경우
            if self.technical_analyzer is not None:
                # 모든 기술적 지표 계산
                df_with_indicators = self.technical_analyzer.calculate_all_indicators(df.copy())
                
                # 최신 지표 값 추출
                latest_indicators = self.technical_analyzer.get_latest_indicators(df_with_indicators)
                
                return latest_indicators
            else:
                # Simple Data Provider 사용
                return self.simple_data_provider.get_technical_indicators(df)
            
        except Exception as e:
            self.logger.error(f"기술적 지표 계산 실패: {e}")
            # fallback to simple provider
            try:
                return self.simple_data_provider.get_technical_indicators(df)
            except:
                return {}
    
    def _detect_trading_signals(self, df: pd.DataFrame, symbol: str, name: str) -> List[TradingSignal]:
        """매매 신호 감지"""
        if self.signal_detector is None or df.empty:
            return []
        
        signals = []
        
        try:
            # 기술적 지표 추가
            df_with_indicators = self.technical_analyzer.calculate_all_indicators(df.copy())
            
            # 골든크로스/데드크로스 신호 감지
            signal = self.signal_detector.detect_golden_cross(
                df_with_indicators, symbol, name
            )
            
            if signal:
                signals.append(signal)
            
        except Exception as e:
            self.logger.error(f"매매 신호 감지 실패 {symbol}: {e}")
        
        return signals
    
    def _generate_recommendation(self, technical_indicators: dict, trading_signals: List[TradingSignal]) -> Tuple[str, float]:
        """종합 추천 및 신뢰도 생성"""
        recommendation = "HOLD"
        confidence = 0.5
        
        try:
            # SimpleDataProvider의 신호 생성 활용
            if technical_indicators:
                signal_data = self.simple_data_provider.generate_simple_signal(technical_indicators)
                recommendation = signal_data.get('recommendation', 'HOLD')
                confidence = signal_data.get('confidence_score', 0.5)
            
            # trading_strategy 신호가 있다면 우선순위 부여
            if trading_signals:
                latest_signal = trading_signals[-1]  # 가장 최근 신호
                
                if hasattr(latest_signal, 'signal_type'):
                    if latest_signal.signal_type == SignalType.GOLDEN_CROSS:
                        recommendation = "BUY"
                        confidence = latest_signal.strength / 100 if hasattr(latest_signal, 'strength') else 0.7
                    elif latest_signal.signal_type == SignalType.DEAD_CROSS:
                        recommendation = "SELL"
                        confidence = latest_signal.strength / 100 if hasattr(latest_signal, 'strength') else 0.7
            
            # 기술적 지표로 추가 보정
            if technical_indicators:
                rsi = technical_indicators.get('rsi')
                if rsi:
                    if rsi < 30 and recommendation != "SELL":
                        recommendation = "BUY"
                        confidence = min(confidence + 0.2, 1.0)
                    elif rsi > 70 and recommendation != "BUY":
                        recommendation = "SELL"  
                        confidence = min(confidence + 0.2, 1.0)
                
                # 이동평균선 배열로 추가 확인
                sma5 = technical_indicators.get('sma5')
                sma20 = technical_indicators.get('sma20')
                current_price = technical_indicators.get('close')
                
                if all([sma5, sma20, current_price]):
                    if current_price > sma5 > sma20:  # 상승 배열
                        if recommendation == "BUY":
                            confidence = min(confidence + 0.1, 1.0)
                    elif current_price < sma5 < sma20:  # 하락 배열
                        if recommendation == "SELL":
                            confidence = min(confidence + 0.1, 1.0)
            
        except Exception as e:
            self.logger.error(f"추천 생성 실패: {e}")
        
        return recommendation, confidence
    
    def _calculate_risk_score(self, technical_indicators: dict) -> float:
        """위험도 계산 (0-1, 높을수록 위험)"""
        risk_score = 0.5  # 기본값
        
        try:
            if technical_indicators:
                rsi = technical_indicators.get('rsi')
                if rsi:
                    # RSI 극단값 체크
                    if rsi < 20 or rsi > 80:
                        risk_score += 0.3
                
                # 볼린저 밴드 위치
                bb_position = technical_indicators.get('bb_position')
                if bb_position:
                    if bb_position < 0.1 or bb_position > 0.9:
                        risk_score += 0.2
                
                # 변동성 (최근 변화율)
                change_rate = technical_indicators.get('change_rate')
                if change_rate and abs(change_rate) > 5:  # 5% 이상 변동
                    risk_score += 0.2
        
        except Exception as e:
            self.logger.error(f"위험도 계산 실패: {e}")
        
        return min(risk_score, 1.0)
    
    def get_portfolio_summary(self, portfolio_analysis: Dict[str, List[SectorAnalysisResult]]) -> dict:
        """포트폴리오 전체 요약"""
        summary = {
            'total_stocks': 0,
            'buy_signals': 0,
            'sell_signals': 0,
            'hold_signals': 0,
            'error_count': 0,
            'avg_confidence': 0.0,
            'high_risk_stocks': 0,
            'sector_summary': {}
        }
        
        all_confidences = []
        
        for sector_name, results in portfolio_analysis.items():
            sector_summary = {
                'stock_count': len(results),
                'buy_count': 0,
                'sell_count': 0,
                'hold_count': 0,
                'avg_confidence': 0.0,
                'recommendations': []
            }
            
            sector_confidences = []
            
            for result in results:
                summary['total_stocks'] += 1
                
                if result.recommendation == "BUY":
                    summary['buy_signals'] += 1
                    sector_summary['buy_count'] += 1
                elif result.recommendation == "SELL":
                    summary['sell_signals'] += 1
                    sector_summary['sell_count'] += 1
                elif result.recommendation == "HOLD":
                    summary['hold_signals'] += 1
                    sector_summary['hold_count'] += 1
                else:  # ERROR
                    summary['error_count'] += 1
                
                if result.confidence_score > 0:
                    all_confidences.append(result.confidence_score)
                    sector_confidences.append(result.confidence_score)
                
                if result.risk_score > 0.7:
                    summary['high_risk_stocks'] += 1
                
                sector_summary['recommendations'].append({
                    'symbol': result.symbol,
                    'name': result.name,
                    'recommendation': result.recommendation,
                    'confidence': result.confidence_score,
                    'risk': result.risk_score
                })
            
            if sector_confidences:
                sector_summary['avg_confidence'] = sum(sector_confidences) / len(sector_confidences)
            
            summary['sector_summary'][sector_name] = sector_summary
        
        if all_confidences:
            summary['avg_confidence'] = sum(all_confidences) / len(all_confidences)
        
        return summary