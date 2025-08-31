"""
이동평균 교차 전략

단기/장기 이동평균선의 교차를 활용한 추세 추종 전략
- 골든크로스(단기 > 장기): 매수 신호
- 데드크로스(단기 < 장기): 매도 신호
- RSI 보조지표로 거짓 신호 필터링
"""

import sys
from pathlib import Path
from typing import Dict, Optional, List
from decimal import Decimal

# Handle both relative and absolute imports for different execution contexts
try:
    from .base_strategy import BaseStrategy
    from ..models.trading_signal import TradingSignal, SignalType, SignalStrength
    from ..models.strategy_config import StrategyConfig
    from ...analysis.indicators.technical import calculate_sma, calculate_rsi
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from kiwoom_api.strategy.engines.base_strategy import BaseStrategy
    from kiwoom_api.strategy.models.trading_signal import TradingSignal, SignalType, SignalStrength
    from kiwoom_api.strategy.models.strategy_config import StrategyConfig
    from kiwoom_api.analysis.indicators.technical import calculate_sma, calculate_rsi


class MovingAverageCrossoverStrategy(BaseStrategy):
    """
    이동평균 교차 자동매매 전략
    
    단기 이동평균선과 장기 이동평균선의 교차를 통해 매매신호를 생성합니다.
    RSI 지표를 보조지표로 사용하여 거짓 신호를 필터링합니다.
    """
    
    def __init__(self, config: StrategyConfig):
        """
        이동평균 교차 전략 초기화
        
        Args:
            config: 전략 설정 객체
        """
        super().__init__(config)
        
        # 이동평균 전략별 파라미터 설정
        self.short_period = config.get_strategy_param("short_period", 5)
        self.long_period = config.get_strategy_param("long_period", 20)
        self.use_rsi_filter = config.get_strategy_param("use_rsi_filter", True)
        self.rsi_oversold = config.get_strategy_param("rsi_oversold", 35)
        self.rsi_overbought = config.get_strategy_param("rsi_overbought", 65)
        self.trend_confirmation = config.get_strategy_param("trend_confirmation", True)
        
        # 파라미터 검증
        self._validate_ma_params()
    
    def _validate_ma_params(self) -> None:
        """이동평균 전략 파라미터 검증"""
        if self.short_period >= self.long_period:
            raise ValueError("단기 이동평균 기간이 장기 이동평균 기간보다 작아야 합니다.")
        
        if self.short_period < 3 or self.short_period > 50:
            raise ValueError("단기 이동평균 기간은 3~50 사이여야 합니다.")
        
        if self.long_period < 10 or self.long_period > 200:
            raise ValueError("장기 이동평균 기간은 10~200 사이여야 합니다.")
        
        if self.use_rsi_filter:
            if not (20 <= self.rsi_oversold <= 40):
                raise ValueError("RSI 과매도 임계치는 20~40 사이여야 합니다.")
            if not (60 <= self.rsi_overbought <= 80):
                raise ValueError("RSI 과매수 임계치는 60~80 사이여야 합니다.")
    
    async def analyze(self, symbol: str) -> Optional[TradingSignal]:
        """
        종목 분석 및 이동평균 교차 매매신호 생성
        
        Args:
            symbol: 종목코드 (6자리)
            
        Returns:
            TradingSignal 객체 또는 None (신호 없음)
        """
        try:
            # 충분한 데이터 조회 (장기 이동평균 + 여유분)
            required_days = self.long_period + 20
            chart_data = await self.get_chart_data(symbol, days=required_days)
            if not chart_data:
                return None
            
            prices = chart_data["prices"]
            if len(prices) < required_days:
                print(f"이동평균 계산을 위한 충분한 데이터가 없습니다. (필요: {required_days}, 현재: {len(prices)})")
                return None
            
            # 분석 데이터 계산
            analysis_data = await self._calculate_indicators(prices)
            current_price = Decimal(str(prices[-1]))
            
            # 매수/매도 조건 확인
            if await self.should_buy(symbol, analysis_data):
                return self._create_buy_signal(symbol, current_price, analysis_data)
            elif await self.should_sell(symbol, analysis_data):
                return self._create_sell_signal(symbol, current_price, analysis_data)
            
            return None  # 신호 없음
            
        except Exception as e:
            print(f"이동평균 교차 전략 분석 실패 - 종목: {symbol}, 오류: {e}")
            return None
    
    async def _calculate_indicators(self, prices: List[float]) -> Dict:
        """
        기술적 지표 계산
        
        Args:
            prices: 가격 리스트
            
        Returns:
            계산된 지표들이 담긴 딕셔너리
        """
        # 현재와 이전 이동평균 계산
        current_short_ma = calculate_sma(prices, self.short_period)
        current_long_ma = calculate_sma(prices, self.long_period)
        
        # 이전 시점의 이동평균 계산 (교차 확인용)
        prev_prices = prices[:-1]
        if len(prev_prices) >= self.long_period:
            prev_short_ma = calculate_sma(prev_prices, self.short_period)
            prev_long_ma = calculate_sma(prev_prices, self.long_period)
        else:
            prev_short_ma = current_short_ma
            prev_long_ma = current_long_ma
        
        # RSI 계산 (필터링용)
        rsi = None
        if self.use_rsi_filter and len(prices) >= 15:
            try:
                rsi = calculate_rsi(prices, period=14)
            except:
                rsi = 50.0  # RSI 계산 실패시 중립값
        
        return {
            "current_price": prices[-1],
            "current_short_ma": current_short_ma,
            "current_long_ma": current_long_ma,
            "prev_short_ma": prev_short_ma,
            "prev_long_ma": prev_long_ma,
            "rsi": rsi,
            "prices": prices
        }
    
    async def should_buy(self, symbol: str, data: Dict) -> bool:
        """
        이동평균 교차 기반 매수 조건 확인
        
        Args:
            symbol: 종목코드
            data: 분석 데이터 딕셔너리
            
        Returns:
            매수해야 하면 True, 아니면 False
        """
        current_short_ma = data["current_short_ma"]
        current_long_ma = data["current_long_ma"]
        prev_short_ma = data["prev_short_ma"]
        prev_long_ma = data["prev_long_ma"]
        rsi = data.get("rsi")
        
        # 골든크로스 확인: 이전에는 단기 < 장기였는데, 현재는 단기 > 장기
        golden_cross = (prev_short_ma <= prev_long_ma) and (current_short_ma > current_long_ma)
        
        if not golden_cross:
            return False
        
        # RSI 필터링 (설정된 경우)
        if self.use_rsi_filter and rsi is not None:
            # 과매수 구간에서는 매수하지 않음
            if rsi >= self.rsi_overbought:
                return False
        
        # 추세 확인 (설정된 경우)
        if self.trend_confirmation:
            # 현재가가 장기 이동평균보다 위에 있어야 함 (상승 추세 확인)
            current_price = data["current_price"]
            if current_price <= current_long_ma:
                return False
        
        return True
    
    async def should_sell(self, symbol: str, data: Dict) -> bool:
        """
        이동평균 교차 기반 매도 조건 확인
        
        Args:
            symbol: 종목코드
            data: 분석 데이터 딕셔너리
            
        Returns:
            매도해야 하면 True, 아니면 False
        """
        current_short_ma = data["current_short_ma"]
        current_long_ma = data["current_long_ma"]
        prev_short_ma = data["prev_short_ma"]
        prev_long_ma = data["prev_long_ma"]
        rsi = data.get("rsi")
        
        # 데드크로스 확인: 이전에는 단기 > 장기였는데, 현재는 단기 < 장기
        dead_cross = (prev_short_ma >= prev_long_ma) and (current_short_ma < current_long_ma)
        
        if not dead_cross:
            return False
        
        # RSI 필터링 (설정된 경우)
        if self.use_rsi_filter and rsi is not None:
            # 과매도 구간에서는 매도하지 않음
            if rsi <= self.rsi_oversold:
                return False
        
        # 추세 확인 (설정된 경우)
        if self.trend_confirmation:
            # 현재가가 장기 이동평균보다 아래에 있어야 함 (하락 추세 확인)
            current_price = data["current_price"]
            if current_price >= current_long_ma:
                return False
        
        return True
    
    def _create_buy_signal(self, symbol: str, current_price: Decimal, data: Dict) -> TradingSignal:
        """
        이동평균 교차 기반 매수 신호 생성
        
        Args:
            symbol: 종목코드
            current_price: 현재가
            data: 분석 데이터
            
        Returns:
            매수 TradingSignal 객체
        """
        short_ma = data["current_short_ma"]
        long_ma = data["current_long_ma"]
        rsi = data.get("rsi")
        
        # 이동평균 간의 거리로 신호 강도 계산
        ma_distance_ratio = abs(short_ma - long_ma) / long_ma
        signal_strength = min(1.0, ma_distance_ratio * 10)  # 거리에 비례하되 1.0을 넘지 않음
        
        confidence = self.calculate_confidence(signal_strength)
        
        # 신호 강도 결정
        if ma_distance_ratio >= 0.02:  # 2% 이상 차이
            strength = SignalStrength.STRONG
        elif ma_distance_ratio >= 0.01:  # 1% 이상 차이
            strength = SignalStrength.MODERATE
        else:
            strength = SignalStrength.WEAK
        
        # RSI 정보 포함
        rsi_info = f", RSI: {rsi:.1f}" if rsi else ""
        reason = f"골든크로스 매수신호 (단기MA: {short_ma:.0f} > 장기MA: {long_ma:.0f}{rsi_info})"
        
        return self.create_signal(
            symbol=symbol,
            signal_type=SignalType.BUY,
            current_price=current_price,
            confidence=confidence,
            reason=reason,
            strength=strength
        )
    
    def _create_sell_signal(self, symbol: str, current_price: Decimal, data: Dict) -> TradingSignal:
        """
        이동평균 교차 기반 매도 신호 생성
        
        Args:
            symbol: 종목코드
            current_price: 현재가
            data: 분석 데이터
            
        Returns:
            매도 TradingSignal 객체
        """
        short_ma = data["current_short_ma"]
        long_ma = data["current_long_ma"]
        rsi = data.get("rsi")
        
        # 이동평균 간의 거리로 신호 강도 계산
        ma_distance_ratio = abs(long_ma - short_ma) / long_ma
        signal_strength = min(1.0, ma_distance_ratio * 10)
        
        confidence = self.calculate_confidence(signal_strength)
        
        # 신호 강도 결정
        if ma_distance_ratio >= 0.02:  # 2% 이상 차이
            strength = SignalStrength.STRONG
        elif ma_distance_ratio >= 0.01:  # 1% 이상 차이
            strength = SignalStrength.MODERATE
        else:
            strength = SignalStrength.WEAK
        
        # RSI 정보 포함
        rsi_info = f", RSI: {rsi:.1f}" if rsi else ""
        reason = f"데드크로스 매도신호 (단기MA: {short_ma:.0f} < 장기MA: {long_ma:.0f}{rsi_info})"
        
        return self.create_signal(
            symbol=symbol,
            signal_type=SignalType.SELL,
            current_price=current_price,
            confidence=confidence,
            reason=reason,
            strength=strength
        )
    
    def get_current_trend(self, data: Dict) -> str:
        """
        현재 추세 상태 반환
        
        Args:
            data: 분석 데이터
            
        Returns:
            추세 상태 문자열
        """
        short_ma = data["current_short_ma"]
        long_ma = data["current_long_ma"]
        current_price = data["current_price"]
        
        if short_ma > long_ma and current_price > short_ma:
            return "강한 상승세"
        elif short_ma > long_ma:
            return "약한 상승세"
        elif short_ma < long_ma and current_price < short_ma:
            return "강한 하락세"
        elif short_ma < long_ma:
            return "약한 하락세"
        else:
            return "횡보"
    
    def get_strategy_info(self) -> Dict:
        """
        이동평균 교차 전략 정보 반환
        
        Returns:
            전략 정보 딕셔너리
        """
        info = super().get_strategy_info()
        info.update({
            "strategy_specific": {
                "short_period": self.short_period,
                "long_period": self.long_period,
                "use_rsi_filter": self.use_rsi_filter,
                "rsi_oversold": self.rsi_oversold,
                "rsi_overbought": self.rsi_overbought,
                "trend_confirmation": self.trend_confirmation
            }
        })
        return info


# 간단한 테스트 함수
async def test_ma_crossover_strategy():
    """이동평균 교차 전략 테스트"""
    from kiwoom_api.strategy.models.strategy_config import StrategyConfig, StrategyType, RiskLevel
    
    # 테스트 설정
    config = StrategyConfig(
        strategy_name="MA Crossover Test Strategy",
        strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
        target_symbols=["{종목코드}"],  # 예시 종목
        risk_level=RiskLevel.MODERATE,
        max_position_size=Decimal("2000000"),  # 200만원
        execution_interval=300,  # 5분
        strategy_params={
            "short_period": 5,
            "long_period": 20,
            "use_rsi_filter": True,
            "rsi_oversold": 35,
            "rsi_overbought": 65,
            "trend_confirmation": True
        }
    )
    
    # 전략 생성 및 테스트
    strategy = MovingAverageCrossoverStrategy(config)
    result = await strategy.analyze("{종목코드}")
    
    if result:
        print(f"매매신호 생성: {result.signal_type.value} - {result.reason}")
        print(f"신뢰도: {result.confidence:.3f}, 강도: {result.strength.value}")
        print(f"현재가: {result.current_price}, 목표가: {result.target_price}, 손절가: {result.stop_loss}")
    else:
        print("매매신호 없음")
    
    return result


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_ma_crossover_strategy())