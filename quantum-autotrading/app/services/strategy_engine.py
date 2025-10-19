"""
매매 전략 엔진

기술적 분석, 시장 미시구조 분석을 통한 매매 신호 생성 및 리스크 관리를 담당합니다.
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..models import TradingSignal, SignalType, TechnicalIndicators, OrderBookData
from ..config import settings, trading_config
# from .data_manager import DataManager

class SignalStrength(Enum):
    """신호 강도"""
    WEAK = 0.3
    MODERATE = 0.6
    STRONG = 0.8
    VERY_STRONG = 1.0

@dataclass
class TechnicalAnalysis:
    """기술적 분석 결과"""
    symbol: str
    timestamp: datetime
    
    # 추세 분석
    trend_direction: str  # "up", "down", "sideways"
    trend_strength: float  # 0.0 ~ 1.0
    
    # 모멘텀 분석
    momentum_score: float  # -1.0 ~ 1.0
    rsi_signal: str  # "oversold", "overbought", "neutral"
    macd_signal: str  # "bullish", "bearish", "neutral"
    
    # 지지/저항 분석
    support_level: float
    resistance_level: float
    price_position: str  # "above_support", "below_resistance", "between"
    
    # 종합 점수
    technical_score: float  # 0.0 ~ 1.0

@dataclass
class MicrostructureAnalysis:
    """시장 미시구조 분석 결과"""
    symbol: str
    timestamp: datetime
    
    # 호가창 분석
    order_imbalance: float  # -1.0 ~ 1.0 (매도우세 ~ 매수우세)
    spread_analysis: str  # "tight", "normal", "wide"
    depth_ratio: float  # 매수/매도 잔량 비율
    
    # 체결 분석
    execution_strength: float  # 체결강도
    volume_profile: str  # "accumulation", "distribution", "neutral"
    large_order_flow: str  # "buy", "sell", "neutral"
    
    # 변동성 분석
    short_term_volatility: float
    volatility_regime: str  # "low", "normal", "high"
    
    # 종합 점수
    microstructure_score: float  # 0.0 ~ 1.0

class StrategyEngine:
    """매매 전략 엔진 메인 클래스"""
    
    def __init__(self):
        self.is_active = False
        self.signal_history = {}  # 종목별 신호 히스토리
        self.analysis_cache = {}  # 분석 결과 캐시
        
        # TODO: 외부 서비스 연결
        # self.data_manager = data_manager
        
        # 리스크 관리 상태
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.active_positions = {}
        
    async def start_signal_monitoring(self):
        """매매 신호 모니터링 시작"""
        
        if self.is_active:
            return
            
        print("🎯 매매 신호 모니터링 시작...")
        self.is_active = True
        
        try:
            # 신호 생성 태스크 시작
            asyncio.create_task(self._signal_generation_loop())
            asyncio.create_task(self._risk_monitoring_loop())
            
            print("✅ 매매 신호 모니터링 시작 완료")
            
        except Exception as e:
            print(f"❌ 매매 신호 모니터링 시작 실패: {e}")
            self.is_active = False
            raise
    
    async def stop_signal_monitoring(self):
        """매매 신호 모니터링 중지"""
        
        print("🛑 매매 신호 모니터링 중지...")
        self.is_active = False
        print("✅ 매매 신호 모니터링 중지 완료")
    
    async def _signal_generation_loop(self):
        """신호 생성 루프"""
        
        while self.is_active:
            try:
                # 관심종목별 신호 생성
                for symbol in settings.watchlist:
                    signal = await self.generate_signal(symbol)
                    if signal and signal.signal_type != SignalType.HOLD:
                        await self._process_generated_signal(signal)
                
                await asyncio.sleep(30)  # 30초마다 신호 생성
                
            except Exception as e:
                print(f"❌ 신호 생성 루프 오류: {e}")
                await asyncio.sleep(60)
    
    async def generate_signal(self, symbol: str) -> Optional[TradingSignal]:
        """매매 신호 생성"""
        
        try:
            # 1. 기술적 분석 수행
            technical_analysis = await self._perform_technical_analysis(symbol)
            if not technical_analysis:
                return None
            
            # 2. 시장 미시구조 분석 수행
            microstructure_analysis = await self._perform_microstructure_analysis(symbol)
            if not microstructure_analysis:
                return None
            
            # 3. 센티먼트 분석 (간단한 버전)
            sentiment_score = await self._analyze_sentiment(symbol)
            
            # 4. 종합 신호 생성
            signal = await self._generate_composite_signal(
                symbol, 
                technical_analysis, 
                microstructure_analysis, 
                sentiment_score
            )
            
            return signal
            
        except Exception as e:
            print(f"❌ 매매 신호 생성 실패 {symbol}: {e}")
            return None
    
    async def _perform_technical_analysis(self, symbol: str) -> Optional[TechnicalAnalysis]:
        """기술적 분석 수행"""
        
        try:
            # TODO: 데이터 매니저에서 기술적 지표 가져오기
            # indicators = await self.data_manager.calculate_indicators(symbol)
            # if not indicators:
            #     return None
            
            # 임시 지표 데이터 (실제로는 data_manager에서 가져옴)
            indicators = TechnicalIndicators(
                symbol=symbol,
                timestamp=datetime.now(),
                ema_5=74800,
                ema_20=74200,
                rsi=65.5,
                macd=150.2,
                macd_signal=120.8,
                macd_histogram=29.4,
                bb_upper=76500,
                bb_middle=75000,
                bb_lower=73500,
                vwap=74950
            )
            
            # 추세 분석
            trend_direction = "up" if indicators.ema_5 > indicators.ema_20 else "down"
            trend_strength = abs(indicators.ema_5 - indicators.ema_20) / indicators.ema_20
            
            # 모멘텀 분석
            momentum_score = 0.0
            
            # RSI 분석
            rsi_signal = "neutral"
            if indicators.rsi < settings.rsi_oversold:
                rsi_signal = "oversold"
                momentum_score += 0.3
            elif indicators.rsi > settings.rsi_overbought:
                rsi_signal = "overbought"
                momentum_score -= 0.3
            
            # MACD 분석
            macd_signal = "neutral"
            if indicators.macd > indicators.macd_signal and indicators.macd_histogram > 0:
                macd_signal = "bullish"
                momentum_score += 0.4
            elif indicators.macd < indicators.macd_signal and indicators.macd_histogram < 0:
                macd_signal = "bearish"
                momentum_score -= 0.4
            
            # 지지/저항 레벨 (볼린저 밴드 기준)
            support_level = indicators.bb_lower
            resistance_level = indicators.bb_upper
            current_price = indicators.vwap  # 현재가 근사치
            
            price_position = "between"
            if current_price <= support_level * 1.02:  # 2% 마진
                price_position = "above_support"
            elif current_price >= resistance_level * 0.98:
                price_position = "below_resistance"
            
            # 기술적 분석 종합 점수 계산
            technical_score = self._calculate_technical_score(
                trend_direction, trend_strength, momentum_score, 
                rsi_signal, macd_signal, price_position
            )
            
            return TechnicalAnalysis(
                symbol=symbol,
                timestamp=datetime.now(),
                trend_direction=trend_direction,
                trend_strength=min(trend_strength, 1.0),
                momentum_score=max(-1.0, min(1.0, momentum_score)),
                rsi_signal=rsi_signal,
                macd_signal=macd_signal,
                support_level=support_level,
                resistance_level=resistance_level,
                price_position=price_position,
                technical_score=technical_score
            )
            
        except Exception as e:
            print(f"❌ 기술적 분석 실패 {symbol}: {e}")
            return None
    
    def _calculate_technical_score(self, trend_direction: str, trend_strength: float, 
                                 momentum_score: float, rsi_signal: str, 
                                 macd_signal: str, price_position: str) -> float:
        """기술적 분석 종합 점수 계산"""
        
        score = 0.5  # 기본 점수
        
        # 추세 점수
        if trend_direction == "up":
            score += trend_strength * 0.2
        else:
            score -= trend_strength * 0.2
        
        # 모멘텀 점수
        score += momentum_score * 0.3
        
        # RSI 점수
        if rsi_signal == "oversold":
            score += 0.1  # 매수 신호
        elif rsi_signal == "overbought":
            score -= 0.1  # 매도 신호
        
        # MACD 점수
        if macd_signal == "bullish":
            score += 0.15
        elif macd_signal == "bearish":
            score -= 0.15
        
        # 지지/저항 점수
        if price_position == "above_support":
            score += 0.1  # 지지선 근처에서 반등 기대
        elif price_position == "below_resistance":
            score -= 0.1  # 저항선 근처에서 하락 기대
        
        return max(0.0, min(1.0, score))
    
    async def _perform_microstructure_analysis(self, symbol: str) -> Optional[MicrostructureAnalysis]:
        """시장 미시구조 분석 수행"""
        
        try:
            # TODO: 데이터 매니저에서 호가창 데이터 가져오기
            # orderbook = await self.data_manager.get_current_orderbook(symbol)
            # if not orderbook:
            #     return None
            
            # 임시 호가창 데이터
            orderbook = OrderBookData(
                symbol=symbol,
                timestamp=datetime.now(),
                ask_prices=[75100, 75200, 75300],
                ask_volumes=[1000, 1500, 2000],
                bid_prices=[75000, 74900, 74800],
                bid_volumes=[2000, 1800, 1000],
                total_ask_volume=4500,
                total_bid_volume=4800
            )
            
            # 호가창 불균형 계산
            total_bid = orderbook.total_bid_volume
            total_ask = orderbook.total_ask_volume
            order_imbalance = (total_bid - total_ask) / (total_bid + total_ask)
            
            # 스프레드 분석
            best_bid = orderbook.bid_prices[0] if orderbook.bid_prices else 0
            best_ask = orderbook.ask_prices[0] if orderbook.ask_prices else 0
            spread = (best_ask - best_bid) / best_bid if best_bid > 0 else 0
            
            spread_analysis = "normal"
            if spread < 0.001:  # 0.1% 미만
                spread_analysis = "tight"
            elif spread > 0.005:  # 0.5% 초과
                spread_analysis = "wide"
            
            # 호가 깊이 비율
            depth_ratio = total_bid / total_ask if total_ask > 0 else 1.0
            
            # 체결강도 시뮬레이션 (실제로는 실시간 체결 데이터 필요)
            execution_strength = np.random.uniform(80, 120)  # 임시값
            
            # 거래량 프로파일 분석 (간단한 버전)
            volume_profile = "neutral"
            if order_imbalance > 0.2:
                volume_profile = "accumulation"
            elif order_imbalance < -0.2:
                volume_profile = "distribution"
            
            # 대량 주문 흐름 (임시)
            large_order_flow = "neutral"
            if order_imbalance > 0.3:
                large_order_flow = "buy"
            elif order_imbalance < -0.3:
                large_order_flow = "sell"
            
            # 단기 변동성 (임시)
            short_term_volatility = np.random.uniform(0.01, 0.03)
            
            volatility_regime = "normal"
            if short_term_volatility < 0.015:
                volatility_regime = "low"
            elif short_term_volatility > 0.025:
                volatility_regime = "high"
            
            # 미시구조 종합 점수 계산
            microstructure_score = self._calculate_microstructure_score(
                order_imbalance, spread_analysis, execution_strength,
                volume_profile, large_order_flow, volatility_regime
            )
            
            return MicrostructureAnalysis(
                symbol=symbol,
                timestamp=datetime.now(),
                order_imbalance=order_imbalance,
                spread_analysis=spread_analysis,
                depth_ratio=depth_ratio,
                execution_strength=execution_strength,
                volume_profile=volume_profile,
                large_order_flow=large_order_flow,
                short_term_volatility=short_term_volatility,
                volatility_regime=volatility_regime,
                microstructure_score=microstructure_score
            )
            
        except Exception as e:
            print(f"❌ 시장 미시구조 분석 실패 {symbol}: {e}")
            return None
    
    def _calculate_microstructure_score(self, order_imbalance: float, spread_analysis: str,
                                      execution_strength: float, volume_profile: str,
                                      large_order_flow: str, volatility_regime: str) -> float:
        """미시구조 분석 종합 점수 계산"""
        
        score = 0.5  # 기본 점수
        
        # 호가창 불균형 점수
        score += order_imbalance * 0.3  # -0.3 ~ +0.3
        
        # 스프레드 점수 (타이트한 스프레드가 좋음)
        if spread_analysis == "tight":
            score += 0.1
        elif spread_analysis == "wide":
            score -= 0.1
        
        # 체결강도 점수
        if execution_strength > 110:
            score += 0.15
        elif execution_strength < 90:
            score -= 0.15
        
        # 거래량 프로파일 점수
        if volume_profile == "accumulation":
            score += 0.1
        elif volume_profile == "distribution":
            score -= 0.1
        
        # 대량 주문 흐름 점수
        if large_order_flow == "buy":
            score += 0.1
        elif large_order_flow == "sell":
            score -= 0.1
        
        # 변동성 점수 (적당한 변동성이 좋음)
        if volatility_regime == "normal":
            score += 0.05
        elif volatility_regime == "high":
            score -= 0.05
        
        return max(0.0, min(1.0, score))
    
    async def _analyze_sentiment(self, symbol: str) -> float:
        """센티먼트 분석 (간단한 버전)"""
        
        try:
            # TODO: 뉴스 분석, 소셜미디어 분석 등
            # 현재는 시장 전반적인 센티먼트만 고려 (임시)
            
            # 시장 지수 기반 센티먼트 (임시)
            market_sentiment = 0.6  # 0.0 ~ 1.0
            
            # 외국인/기관 매매 동향 (임시)
            foreign_flow = 0.3  # -1.0 ~ 1.0
            
            # 종합 센티먼트 점수
            sentiment_score = (market_sentiment + foreign_flow * 0.5) / 1.5
            
            return max(0.0, min(1.0, sentiment_score))
            
        except Exception as e:
            print(f"❌ 센티먼트 분석 실패 {symbol}: {e}")
            return 0.5  # 중립
    
    async def _generate_composite_signal(self, symbol: str, technical: TechnicalAnalysis,
                                       microstructure: MicrostructureAnalysis,
                                       sentiment: float) -> TradingSignal:
        """종합 매매 신호 생성"""
        
        try:
            # 가중치 적용하여 종합 점수 계산
            weights = trading_config.SIGNAL_WEIGHTS
            
            composite_score = (
                technical.technical_score * weights["technical_indicators"] +
                microstructure.microstructure_score * weights["market_microstructure"] +
                sentiment * weights["sentiment"]
            )
            
            # 신호 유형 결정
            signal_type = SignalType.HOLD
            if composite_score > 0.7:
                signal_type = SignalType.BUY
            elif composite_score < 0.3:
                signal_type = SignalType.SELL
            
            # 신호 강도 계산
            if signal_type == SignalType.BUY:
                strength = (composite_score - 0.7) / 0.3  # 0.7~1.0 -> 0~1
            elif signal_type == SignalType.SELL:
                strength = (0.3 - composite_score) / 0.3  # 0~0.3 -> 1~0
            else:
                strength = 0.0
            
            # 신뢰도 계산 (각 분석의 일치도 기반)
            confidence = self._calculate_signal_confidence(technical, microstructure, sentiment)
            
            # 현재가 추정 (실제로는 실시간 데이터에서 가져옴)
            current_price = 75000.0  # 임시값
            
            # 목표가 및 손절가 계산
            target_price = None
            stop_loss_price = None
            
            if signal_type == SignalType.BUY:
                target_price = current_price * (1 + settings.take_profit_percent / 100)
                stop_loss_price = current_price * (1 - settings.stop_loss_percent / 100)
            elif signal_type == SignalType.SELL:
                target_price = current_price * (1 - settings.take_profit_percent / 100)
                stop_loss_price = current_price * (1 + settings.stop_loss_percent / 100)
            
            # 신호 발생 이유 생성
            reasoning = self._generate_signal_reasoning(technical, microstructure, sentiment, signal_type)
            
            signal = TradingSignal(
                symbol=symbol,
                signal_type=signal_type,
                timestamp=datetime.now(),
                strength=strength,
                confidence=confidence,
                technical_score=technical.technical_score,
                microstructure_score=microstructure.microstructure_score,
                sentiment_score=sentiment,
                current_price=current_price,
                target_price=target_price,
                stop_loss_price=stop_loss_price,
                reasoning=reasoning,
                metadata={
                    "trend_direction": technical.trend_direction,
                    "rsi_signal": technical.rsi_signal,
                    "macd_signal": technical.macd_signal,
                    "order_imbalance": microstructure.order_imbalance,
                    "execution_strength": microstructure.execution_strength,
                    "composite_score": composite_score
                }
            )
            
            return signal
            
        except Exception as e:
            print(f"❌ 종합 신호 생성 실패 {symbol}: {e}")
            return None
    
    def _calculate_signal_confidence(self, technical: TechnicalAnalysis,
                                   microstructure: MicrostructureAnalysis,
                                   sentiment: float) -> float:
        """신호 신뢰도 계산"""
        
        # 각 분석 결과의 일치도 확인
        scores = [technical.technical_score, microstructure.microstructure_score, sentiment]
        
        # 점수들의 표준편차가 낮을수록 신뢰도 높음
        std_dev = np.std(scores)
        confidence = 1.0 - (std_dev * 2)  # 표준편차를 신뢰도로 변환
        
        return max(0.0, min(1.0, confidence))
    
    def _generate_signal_reasoning(self, technical: TechnicalAnalysis,
                                 microstructure: MicrostructureAnalysis,
                                 sentiment: float, signal_type: SignalType) -> str:
        """신호 발생 이유 생성"""
        
        reasons = []
        
        # 기술적 분석 이유
        if technical.trend_direction == "up" and signal_type == SignalType.BUY:
            reasons.append("상승 추세 지속")
        elif technical.trend_direction == "down" and signal_type == SignalType.SELL:
            reasons.append("하락 추세 지속")
        
        if technical.rsi_signal == "oversold" and signal_type == SignalType.BUY:
            reasons.append("RSI 과매도 반등")
        elif technical.rsi_signal == "overbought" and signal_type == SignalType.SELL:
            reasons.append("RSI 과매수 조정")
        
        if technical.macd_signal == "bullish" and signal_type == SignalType.BUY:
            reasons.append("MACD 상승 신호")
        elif technical.macd_signal == "bearish" and signal_type == SignalType.SELL:
            reasons.append("MACD 하락 신호")
        
        # 미시구조 분석 이유
        if microstructure.order_imbalance > 0.2 and signal_type == SignalType.BUY:
            reasons.append("호가창 매수 우세")
        elif microstructure.order_imbalance < -0.2 and signal_type == SignalType.SELL:
            reasons.append("호가창 매도 우세")
        
        if microstructure.execution_strength > 110 and signal_type == SignalType.BUY:
            reasons.append("체결강도 강함")
        elif microstructure.execution_strength < 90 and signal_type == SignalType.SELL:
            reasons.append("체결강도 약함")
        
        # 센티먼트 이유
        if sentiment > 0.6 and signal_type == SignalType.BUY:
            reasons.append("시장 센티먼트 긍정적")
        elif sentiment < 0.4 and signal_type == SignalType.SELL:
            reasons.append("시장 센티먼트 부정적")
        
        return " + ".join(reasons) if reasons else "종합 분석 결과"
    
    async def _process_generated_signal(self, signal: TradingSignal):
        """생성된 신호 처리"""
        
        try:
            # 신호 히스토리에 저장
            if signal.symbol not in self.signal_history:
                self.signal_history[signal.symbol] = []
            
            self.signal_history[signal.symbol].append(signal)
            
            # 최근 100개 신호만 유지
            if len(self.signal_history[signal.symbol]) > 100:
                self.signal_history[signal.symbol] = self.signal_history[signal.symbol][-100:]
            
            # 리스크 관리 체크
            risk_approved = await self.check_risk_management(signal)
            if not risk_approved:
                print(f"⚠️ 리스크 관리로 인한 신호 거부: {signal.symbol} {signal.signal_type}")
                return
            
            # 신호 출력
            print(f"📊 매매 신호 생성: {signal.symbol} {signal.signal_type.value.upper()} "
                  f"(강도: {signal.strength:.2f}, 신뢰도: {signal.confidence:.2f}) - {signal.reasoning}")
            
            # TODO: 주문 실행기로 신호 전달
            # await self.order_executor.process_signal(signal)
            
        except Exception as e:
            print(f"❌ 신호 처리 실패: {e}")
    
    async def check_risk_management(self, signal: TradingSignal) -> bool:
        """리스크 관리 체크"""
        
        try:
            # 1. 일일 손실 한도 체크
            daily_loss_limit = settings.max_position_size_percent * trading_config.RISK_RULES["daily_loss_limit"]
            if self.daily_pnl < -daily_loss_limit:
                return False
            
            # 2. 연속 손실 체크
            if self.consecutive_losses >= trading_config.RISK_RULES["max_consecutive_losses"]:
                return False
            
            # 3. 최대 포지션 수 체크
            if len(self.active_positions) >= settings.max_positions:
                return False
            
            # 4. 동일 종목 중복 신호 체크
            if signal.symbol in self.active_positions:
                return False
            
            # 5. 신호 강도 및 신뢰도 체크
            if signal.strength < 0.5 or signal.confidence < 0.6:
                return False
            
            # 6. 거래 시간 체크
            # TODO: 실제 거래 시간 확인
            # if not is_trading_time():
            #     return False
            
            return True
            
        except Exception as e:
            print(f"❌ 리스크 관리 체크 실패: {e}")
            return False
    
    async def calculate_position_size(self, signal: TradingSignal) -> int:
        """포지션 사이징 계산"""
        
        try:
            # TODO: 계좌 잔고 조회
            # account_balance = await self.get_account_balance()
            account_balance = 10000000  # 임시값 (1천만원)
            
            # 기본 포지션 크기 (계좌 대비 %)
            base_position_percent = settings.max_position_size_percent / 100
            
            # 신호 강도에 따른 조정
            strength_multiplier = 0.5 + (signal.strength * 0.5)  # 0.5 ~ 1.0
            
            # 신뢰도에 따른 조정
            confidence_multiplier = 0.7 + (signal.confidence * 0.3)  # 0.7 ~ 1.0
            
            # 최종 포지션 크기 계산
            position_amount = account_balance * base_position_percent * strength_multiplier * confidence_multiplier
            
            # 주식 수량 계산
            quantity = int(position_amount / signal.current_price)
            
            # 최소 1주, 최대 제한 적용
            quantity = max(1, min(quantity, 1000))  # 최대 1000주
            
            return quantity
            
        except Exception as e:
            print(f"❌ 포지션 사이징 계산 실패: {e}")
            return 1  # 기본 1주
    
    async def _risk_monitoring_loop(self):
        """리스크 모니터링 루프"""
        
        while self.is_active:
            try:
                # 포지션별 리스크 체크
                await self._check_position_risks()
                
                # 일일 손익 업데이트
                await self._update_daily_pnl()
                
                # 시장 상황 모니터링
                await self._monitor_market_conditions()
                
                await asyncio.sleep(60)  # 1분마다 체크
                
            except Exception as e:
                print(f"❌ 리스크 모니터링 오류: {e}")
                await asyncio.sleep(60)
    
    async def _check_position_risks(self):
        """포지션별 리스크 체크"""
        
        # TODO: 실제 포지션 데이터로 손절/익절 체크
        pass
    
    async def _update_daily_pnl(self):
        """일일 손익 업데이트"""
        
        # TODO: 실제 계좌 데이터에서 일일 손익 계산
        pass
    
    async def _monitor_market_conditions(self):
        """시장 상황 모니터링"""
        
        # TODO: 시장 급변 상황 감지 및 대응
        pass
    
    async def health_check(self) -> bool:
        """전략 엔진 상태 확인"""
        
        try:
            # 활성 상태 확인
            if not self.is_active:
                return False
            
            # 최근 신호 생성 확인
            recent_signals = 0
            cutoff_time = datetime.now() - timedelta(minutes=10)
            
            for symbol_signals in self.signal_history.values():
                for signal in symbol_signals:
                    if signal.timestamp > cutoff_time:
                        recent_signals += 1
            
            # 최근 10분 내 신호가 있으면 정상
            return recent_signals > 0
            
        except Exception as e:
            print(f"❌ 전략 엔진 헬스체크 실패: {e}")
            return False
