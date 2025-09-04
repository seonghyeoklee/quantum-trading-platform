"""
스마트 주문 관리자
기술적 분석 결과를 바탕으로 최적의 매매가를 자동 결정
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class OrderRecommendation:
    """주문 추천 정보"""
    order_type: str          # MARKET, LIMIT, STOP_LIMIT
    price: int               # 주문가격
    confidence: float        # 가격 전략 확신도
    strategy: str            # AGGRESSIVE, BALANCED, PATIENT
    reasoning: str           # 가격 결정 근거
    validity_minutes: int    # 주문 유효시간(분)

class SmartOrderManager:
    """스마트 주문 관리자"""
    
    def __init__(self):
        """초기화"""
        self.logger = logging.getLogger(__name__)
        
        # 가격 전략 설정
        self.price_strategies = {
            'AGGRESSIVE': {
                'buy_discount': 0.002,   # 0.2% 할인
                'sell_premium': 0.002,   # 0.2% 프리미엄  
                'order_type': 'MARKET',
                'validity_minutes': 5
            },
            'BALANCED': {
                'buy_discount': 0.005,   # 0.5% 할인
                'sell_premium': 0.005,   # 0.5% 프리미엄
                'order_type': 'LIMIT',
                'validity_minutes': 30
            },
            'PATIENT': {
                'buy_discount': 0.01,    # 1.0% 할인
                'sell_premium': 0.01,    # 1.0% 프리미엄
                'order_type': 'LIMIT', 
                'validity_minutes': 120
            }
        }
        
        self.logger.info("Smart Order Manager 초기화 완료")
    
    def get_optimal_order(self, symbol: str, action: str, 
                         technical_indicators: dict, 
                         current_price: float,
                         market_conditions: dict = None) -> OrderRecommendation:
        """최적 주문 정보 생성"""
        
        # 1. 시장 상황 분석
        strategy = self._analyze_market_strategy(technical_indicators, market_conditions)
        
        # 2. 가격 계산
        optimal_price, order_type = self._calculate_price(
            current_price, action, strategy, technical_indicators
        )
        
        # 3. 확신도 계산
        confidence = self._calculate_price_confidence(
            technical_indicators, strategy, market_conditions
        )
        
        # 4. 근거 생성
        reasoning = self._generate_price_reasoning(
            strategy, technical_indicators, action, current_price, optimal_price
        )
        
        return OrderRecommendation(
            order_type=order_type,
            price=int(optimal_price),
            confidence=confidence,
            strategy=strategy,
            reasoning=reasoning,
            validity_minutes=self.price_strategies[strategy]['validity_minutes']
        )
    
    def _analyze_market_strategy(self, indicators: dict, market_conditions: dict = None) -> str:
        """시장 상황 분석하여 전략 결정"""
        
        # 기본값
        strategy_scores = {'AGGRESSIVE': 0, 'BALANCED': 0, 'PATIENT': 0}
        
        # 1. RSI 기반 분석
        rsi = indicators.get('rsi')
        if rsi:
            if rsi < 30:  # 과매도
                strategy_scores['AGGRESSIVE'] += 2  # 빠른 매수 기회
                strategy_scores['PATIENT'] += 1
            elif rsi > 70:  # 과매수
                strategy_scores['PATIENT'] += 2   # 신중한 매도
                strategy_scores['BALANCED'] += 1
            else:  # 중립
                strategy_scores['BALANCED'] += 2
        
        # 2. 거래량 분석
        volume_ratio = indicators.get('volume_ratio', 1.0)
        if volume_ratio > 1.5:  # 거래량 급증
            strategy_scores['AGGRESSIVE'] += 2
        elif volume_ratio < 0.8:  # 거래량 부족
            strategy_scores['PATIENT'] += 2
        else:
            strategy_scores['BALANCED'] += 1
        
        # 3. 가격 변동성 분석
        change_rate = indicators.get('change_rate', 0)
        if abs(change_rate) > 3:  # 3% 이상 변동
            strategy_scores['PATIENT'] += 2  # 변동성 클 때는 신중
        elif abs(change_rate) < 1:  # 1% 미만 변동
            strategy_scores['AGGRESSIVE'] += 1  # 안정적일 때 적극적
        
        # 4. 이동평균선 분석
        sma5 = indicators.get('sma5')
        sma20 = indicators.get('sma20')
        current_price = indicators.get('close')
        
        if all([sma5, sma20, current_price]):
            if current_price > sma5 > sma20:  # 상승 추세
                strategy_scores['BALANCED'] += 1
            elif current_price < sma5 < sma20:  # 하락 추세
                strategy_scores['PATIENT'] += 1
        
        # 최고 점수 전략 선택
        best_strategy = max(strategy_scores.items(), key=lambda x: x[1])[0]
        
        self.logger.info(f"전략 점수: {strategy_scores}, 선택: {best_strategy}")
        return best_strategy
    
    def _calculate_price(self, current_price: float, action: str, 
                        strategy: str, indicators: dict) -> Tuple[float, str]:
        """최적 가격 계산"""
        
        strategy_config = self.price_strategies[strategy]
        
        if action.upper() == "BUY":
            # 매수: 현재가보다 할인된 가격
            discount_rate = strategy_config['buy_discount']
            optimal_price = current_price * (1 - discount_rate)
            
        elif action.upper() == "SELL":
            # 매도: 현재가보다 프리미엄 가격
            premium_rate = strategy_config['sell_premium']
            optimal_price = current_price * (1 + premium_rate)
            
        else:
            # 기본값: 현재가
            optimal_price = current_price
        
        # 주문 타입 결정
        order_type = strategy_config['order_type']
        
        # 시장가인 경우 현재가 사용
        if order_type == 'MARKET':
            optimal_price = current_price
        
        return optimal_price, order_type
    
    def _calculate_price_confidence(self, indicators: dict, strategy: str, 
                                   market_conditions: dict = None) -> float:
        """가격 전략 확신도 계산"""
        
        base_confidence = 0.7  # 기본 확신도
        
        # RSI 확신도 조정
        rsi = indicators.get('rsi')
        if rsi:
            if 30 <= rsi <= 70:  # 안정 구간
                base_confidence += 0.1
            elif rsi < 20 or rsi > 80:  # 극단 구간
                base_confidence += 0.2  # 반전 확률 높음
        
        # 거래량 확신도 조정
        volume_ratio = indicators.get('volume_ratio', 1.0)
        if 1.2 <= volume_ratio <= 2.0:  # 적당한 거래량 증가
            base_confidence += 0.1
        elif volume_ratio > 3.0:  # 과도한 거래량
            base_confidence -= 0.1
        
        # 전략별 확신도 조정
        if strategy == 'BALANCED':
            base_confidence += 0.05  # 중도 전략이 안전
        
        return min(base_confidence, 1.0)
    
    def _generate_price_reasoning(self, strategy: str, indicators: dict, 
                                 action: str, current_price: float, 
                                 optimal_price: float) -> str:
        """가격 결정 근거 생성"""
        
        reasoning_parts = []
        
        # 전략 설명
        strategy_desc = {
            'AGGRESSIVE': '거래량 급증 및 명확한 신호로 신속 체결 우선',
            'BALANCED': '안정적인 시장 상황으로 합리적 가격 추구',
            'PATIENT': '변동성 높음 또는 극단적 상황으로 신중한 접근'
        }
        reasoning_parts.append(strategy_desc[strategy])
        
        # 가격 차이 설명
        price_diff = (optimal_price - current_price) / current_price * 100
        if action.upper() == "BUY":
            if price_diff < 0:
                reasoning_parts.append(f"현재가 대비 {abs(price_diff):.1f}% 할인가로 매수")
            else:
                reasoning_parts.append(f"시장가 매수 (즉시 체결)")
        else:
            if price_diff > 0:
                reasoning_parts.append(f"현재가 대비 {price_diff:.1f}% 프리미엄으로 매도")
            else:
                reasoning_parts.append(f"시장가 매도 (즉시 체결)")
        
        # 기술적 지표 근거
        rsi = indicators.get('rsi')
        if rsi:
            if rsi < 30:
                reasoning_parts.append(f"RSI {rsi:.1f} 과매도 구간")
            elif rsi > 70:
                reasoning_parts.append(f"RSI {rsi:.1f} 과매수 구간")
        
        volume_ratio = indicators.get('volume_ratio')
        if volume_ratio and volume_ratio > 1.3:
            reasoning_parts.append(f"거래량 {volume_ratio:.1f}배 증가")
        
        return " | ".join(reasoning_parts)
    
    def should_retry_order(self, order_result: dict, recommendation: OrderRecommendation, 
                          elapsed_minutes: int) -> bool:
        """주문 재시도 여부 판단"""
        
        # 주문 실패 시
        if order_result.get('status') == 'FAILED':
            return True
        
        # 지정가 주문이 유효시간 내 미체결인 경우
        if (order_result.get('status') == 'PENDING' and 
            recommendation.order_type == 'LIMIT' and
            elapsed_minutes >= recommendation.validity_minutes):
            return True
        
        return False
    
    def get_retry_recommendation(self, original_recommendation: OrderRecommendation,
                               current_indicators: dict, 
                               current_price: float) -> OrderRecommendation:
        """재시도 주문 추천"""
        
        # 더 적극적인 전략으로 변경
        new_strategy = 'AGGRESSIVE' if original_recommendation.strategy != 'AGGRESSIVE' else 'BALANCED'
        
        # 새로운 추천 생성
        return self.get_optimal_order(
            symbol="",  # 실제 구현에서는 symbol 전달
            action="",  # 실제 구현에서는 action 전달
            technical_indicators=current_indicators,
            current_price=current_price
        )


# 테스트 및 사용 예시
if __name__ == "__main__":
    # 예시 기술적 지표
    test_indicators = {
        'close': 50000,
        'rsi': 25,  # 과매도
        'volume_ratio': 1.8,  # 거래량 증가
        'change_rate': -2.5,  # 2.5% 하락
        'sma5': 51000,
        'sma20': 52000
    }
    
    # Smart Order Manager 테스트
    manager = SmartOrderManager()
    
    # 매수 추천
    buy_recommendation = manager.get_optimal_order(
        symbol="005930",
        action="BUY", 
        technical_indicators=test_indicators,
        current_price=50000
    )
    
    print("=== 매수 주문 추천 ===")
    print(f"주문 타입: {buy_recommendation.order_type}")
    print(f"추천 가격: {buy_recommendation.price:,}원")
    print(f"전략: {buy_recommendation.strategy}")
    print(f"확신도: {buy_recommendation.confidence:.2f}")
    print(f"근거: {buy_recommendation.reasoning}")
    print(f"유효시간: {buy_recommendation.validity_minutes}분")