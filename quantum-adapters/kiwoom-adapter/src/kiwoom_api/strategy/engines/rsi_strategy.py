"""
RSI 기반 자동매매 전략

RSI(Relative Strength Index) 지표를 활용한 과매수/과매도 전략
- RSI > 70: 과매수 (매도 신호)
- RSI < 30: 과매도 (매수 신호)
- RSI 30-70: 중립 (신호 없음)
"""

import sys
from pathlib import Path
from typing import Dict, Optional
from decimal import Decimal

# Handle both relative and absolute imports for different execution contexts
try:
    from .base_strategy import BaseStrategy
    from ..models.trading_signal import TradingSignal, SignalType, SignalStrength
    from ..models.strategy_config import StrategyConfig
    from ...analysis.indicators.technical import calculate_rsi
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from kiwoom_api.strategy.engines.base_strategy import BaseStrategy
    from kiwoom_api.strategy.models.trading_signal import TradingSignal, SignalType, SignalStrength
    from kiwoom_api.strategy.models.strategy_config import StrategyConfig
    from kiwoom_api.analysis.indicators.technical import calculate_rsi


class RSIStrategy(BaseStrategy):
    """
    RSI 기반 자동매매 전략
    
    RSI 지표를 사용하여 과매수/과매도 구간에서 매매신호를 생성합니다.
    """
    
    def __init__(self, config: StrategyConfig):
        """
        RSI 전략 초기화
        
        Args:
            config: 전략 설정 객체
        """
        super().__init__(config)
        
        # RSI 전략별 파라미터 설정
        self.rsi_period = config.get_strategy_param("rsi_period", 14)
        self.oversold_threshold = config.get_strategy_param("oversold_threshold", 30.0)
        self.overbought_threshold = config.get_strategy_param("overbought_threshold", 70.0)
        self.rsi_extreme_threshold = config.get_strategy_param("rsi_extreme_threshold", 80.0)  # 극단값 임계치
        
        # 파라미터 검증
        self._validate_rsi_params()
    
    def _validate_rsi_params(self) -> None:
        """RSI 전략 파라미터 검증"""
        if self.rsi_period < 5 or self.rsi_period > 50:
            raise ValueError("RSI 기간은 5~50 사이여야 합니다.")
        
        if self.oversold_threshold >= self.overbought_threshold:
            raise ValueError("과매도 임계치가 과매수 임계치보다 작아야 합니다.")
        
        if not (0 < self.oversold_threshold < 50):
            raise ValueError("과매도 임계치는 0과 50 사이여야 합니다.")
        
        if not (50 < self.overbought_threshold < 100):
            raise ValueError("과매수 임계치는 50과 100 사이여야 합니다.")
    
    async def analyze(self, symbol: str) -> Optional[TradingSignal]:
        """
        종목 분석 및 RSI 기반 매매신호 생성
        
        Args:
            symbol: 종목코드 (6자리)
            
        Returns:
            TradingSignal 객체 또는 None (신호 없음)
        """
        try:
            # 차트 데이터 조회
            chart_data = await self.get_chart_data(symbol, days=max(30, self.rsi_period + 10))
            if not chart_data:
                return None
            
            prices = chart_data["prices"]
            if len(prices) < self.rsi_period + 1:
                print(f"RSI 계산을 위한 충분한 데이터가 없습니다. (필요: {self.rsi_period + 1}, 현재: {len(prices)})")
                return None
            
            # RSI 계산
            current_rsi = calculate_rsi(prices, self.rsi_period)
            current_price = Decimal(str(prices[-1]))
            
            # 분석 데이터 준비
            analysis_data = {
                "rsi": current_rsi,
                "prices": prices,
                "current_price": float(current_price)
            }
            
            # 매수/매도 조건 확인
            if await self.should_buy(symbol, analysis_data):
                return self._create_buy_signal(symbol, current_price, current_rsi)
            elif await self.should_sell(symbol, analysis_data):
                return self._create_sell_signal(symbol, current_price, current_rsi)
            
            return None  # 신호 없음
            
        except Exception as e:
            print(f"RSI 전략 분석 실패 - 종목: {symbol}, 오류: {e}")
            return None
    
    async def should_buy(self, symbol: str, data: Dict) -> bool:
        """
        RSI 기반 매수 조건 확인
        
        Args:
            symbol: 종목코드
            data: 분석 데이터 딕셔너리 (rsi, prices, current_price 포함)
            
        Returns:
            매수해야 하면 True, 아니면 False
        """
        rsi = data.get("rsi", 50.0)
        
        # 과매도 구간에서 매수 신호
        if rsi <= self.oversold_threshold:
            return True
        
        return False
    
    async def should_sell(self, symbol: str, data: Dict) -> bool:
        """
        RSI 기반 매도 조건 확인
        
        Args:
            symbol: 종목코드
            data: 분석 데이터 딕셔너리 (rsi, prices, current_price 포함)
            
        Returns:
            매도해야 하면 True, 아니면 False
        """
        rsi = data.get("rsi", 50.0)
        
        # 과매수 구간에서 매도 신호
        if rsi >= self.overbought_threshold:
            return True
        
        return False
    
    def _create_buy_signal(self, symbol: str, current_price: Decimal, rsi: float) -> TradingSignal:
        """
        RSI 기반 매수 신호 생성
        
        Args:
            symbol: 종목코드
            current_price: 현재가
            rsi: 현재 RSI 값
            
        Returns:
            매수 TradingSignal 객체
        """
        # RSI가 낮을수록 높은 신뢰도 (과매도가 심할수록)
        signal_strength = max(0.0, (self.oversold_threshold - rsi) / self.oversold_threshold)
        confidence = self.calculate_confidence(signal_strength)
        
        # 신호 강도 결정
        if rsi <= 20:
            strength = SignalStrength.STRONG
        elif rsi <= 25:
            strength = SignalStrength.MODERATE
        else:
            strength = SignalStrength.WEAK
        
        reason = f"RSI 과매도 매수신호 (RSI: {rsi:.2f} <= {self.oversold_threshold})"
        
        return self.create_signal(
            symbol=symbol,
            signal_type=SignalType.BUY,
            current_price=current_price,
            confidence=confidence,
            reason=reason,
            strength=strength
        )
    
    def _create_sell_signal(self, symbol: str, current_price: Decimal, rsi: float) -> TradingSignal:
        """
        RSI 기반 매도 신호 생성
        
        Args:
            symbol: 종목코드
            current_price: 현재가
            rsi: 현재 RSI 값
            
        Returns:
            매도 TradingSignal 객체
        """
        # RSI가 높을수록 높은 신뢰도 (과매수가 심할수록)
        signal_strength = min(1.0, (rsi - self.overbought_threshold) / (100 - self.overbought_threshold))
        confidence = self.calculate_confidence(signal_strength)
        
        # 신호 강도 결정
        if rsi >= self.rsi_extreme_threshold:
            strength = SignalStrength.STRONG
        elif rsi >= 75:
            strength = SignalStrength.MODERATE
        else:
            strength = SignalStrength.WEAK
        
        reason = f"RSI 과매수 매도신호 (RSI: {rsi:.2f} >= {self.overbought_threshold})"
        
        return self.create_signal(
            symbol=symbol,
            signal_type=SignalType.SELL,
            current_price=current_price,
            confidence=confidence,
            reason=reason,
            strength=strength
        )
    
    def get_current_rsi_status(self, rsi: float) -> str:
        """
        현재 RSI 상태 반환
        
        Args:
            rsi: RSI 값
            
        Returns:
            RSI 상태 문자열
        """
        if rsi <= 20:
            return "극도로 과매도"
        elif rsi <= self.oversold_threshold:
            return "과매도"
        elif rsi >= 80:
            return "극도로 과매수"
        elif rsi >= self.overbought_threshold:
            return "과매수"
        else:
            return "중립"
    
    def get_strategy_info(self) -> Dict:
        """
        RSI 전략 정보 반환
        
        Returns:
            전략 정보 딕셔너리
        """
        info = super().get_strategy_info()
        info.update({
            "strategy_specific": {
                "rsi_period": self.rsi_period,
                "oversold_threshold": self.oversold_threshold,
                "overbought_threshold": self.overbought_threshold,
                "rsi_extreme_threshold": self.rsi_extreme_threshold
            }
        })
        return info


# 간단한 테스트 함수
async def test_rsi_strategy():
    """RSI 전략 테스트"""
    from kiwoom_api.strategy.models.strategy_config import StrategyConfig, StrategyType, RiskLevel
    
    # 테스트 설정
    config = StrategyConfig(
        strategy_name="RSI Test Strategy",
        strategy_type=StrategyType.RSI_MEAN_REVERSION,
        target_symbols=["005930"],  # 삼성전자
        risk_level=RiskLevel.MODERATE,
        max_position_size=Decimal("1000000"),  # 100만원
        execution_interval=60,
        strategy_params={
            "rsi_period": 14,
            "oversold_threshold": 30.0,
            "overbought_threshold": 70.0
        }
    )
    
    # 전략 생성 및 테스트
    strategy = RSIStrategy(config)
    result = await strategy.analyze("005930")
    
    if result:
        print(f"매매신호 생성: {result.signal_type.value} - {result.reason}")
        print(f"신뢰도: {result.confidence:.3f}, 강도: {result.strength.value}")
    else:
        print("매매신호 없음")
    
    return result


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_rsi_strategy())