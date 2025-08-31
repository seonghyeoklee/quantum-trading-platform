"""
자동매매 전략 테스트 모듈

RSI 전략, 이동평균 교차 전략의 정확성을 검증하는 테스트
"""

import pytest
import sys
from pathlib import Path
from decimal import Decimal
from unittest.mock import AsyncMock, patch

# Handle import path for both development and test environments
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from kiwoom_api.strategy.engines.base_strategy import BaseStrategy
from kiwoom_api.strategy.engines.rsi_strategy import RSIStrategy
from kiwoom_api.strategy.engines.moving_average_crossover import MovingAverageCrossoverStrategy
from kiwoom_api.strategy.models.strategy_config import StrategyConfig, StrategyType, RiskLevel
from kiwoom_api.strategy.models.trading_signal import TradingSignal, SignalType, SignalStrength


class TestBaseStrategy:
    """BaseStrategy 추상 클래스 테스트"""
    
    @pytest.fixture
    def base_config(self):
        """기본 전략 설정"""
        return StrategyConfig(
            strategy_name="Test Strategy",
            strategy_type=StrategyType.RSI_MEAN_REVERSION,
            target_symbols=["005930", "000660"],
            risk_level=RiskLevel.MODERATE,
            max_position_size=Decimal("1000000"),
            execution_interval=60,
            min_confidence=0.7
        )
    
    def test_config_validation(self, base_config):
        """전략 설정 검증 테스트"""
        # 올바른 설정은 통과해야 함
        class TestStrategy(BaseStrategy):
            async def analyze(self, symbol): return None
            async def should_buy(self, symbol, data): return False
            async def should_sell(self, symbol, data): return False
        
        strategy = TestStrategy(base_config)
        assert strategy.name == "Test Strategy"
        assert strategy.enabled is True
    
    def test_invalid_config_validation(self):
        """잘못된 설정 검증 테스트"""
        class TestStrategy(BaseStrategy):
            async def analyze(self, symbol): return None
            async def should_buy(self, symbol, data): return False
            async def should_sell(self, symbol, data): return False
        
        # 대상 종목이 없는 경우
        with pytest.raises(ValueError, match="대상 종목이 설정되지 않았습니다"):
            config = StrategyConfig(
                strategy_name="Invalid Strategy",
                strategy_type=StrategyType.RSI_MEAN_REVERSION,
                target_symbols=[],
                risk_level=RiskLevel.MODERATE,
                max_position_size=Decimal("1000000")
            )
            TestStrategy(config)
        
        # 잘못된 신뢰도
        with pytest.raises(ValueError, match="최소 신뢰도는 0.0과 1.0 사이여야 합니다"):
            config = StrategyConfig(
                strategy_name="Invalid Strategy",
                strategy_type=StrategyType.RSI_MEAN_REVERSION,
                target_symbols=["005930"],
                risk_level=RiskLevel.MODERATE,
                max_position_size=Decimal("1000000"),
                min_confidence=1.5
            )
            TestStrategy(config)
    
    def test_confidence_calculation(self, base_config):
        """신뢰도 계산 테스트"""
        class TestStrategy(BaseStrategy):
            async def analyze(self, symbol): return None
            async def should_buy(self, symbol, data): return False
            async def should_sell(self, symbol, data): return False
        
        strategy = TestStrategy(base_config)
        
        # 기본 신뢰도 계산
        assert strategy.calculate_confidence(0.8) == 0.8
        assert strategy.calculate_confidence(0.5, "bull") == 0.55
        assert strategy.calculate_confidence(0.9, "bear") == 0.81
        
        # 1.0을 넘지 않아야 함
        assert strategy.calculate_confidence(0.95, "bull") == 1.0
    
    def test_market_hours_check(self, base_config):
        """장중 시간 확인 테스트"""
        class TestStrategy(BaseStrategy):
            async def analyze(self, symbol): return None
            async def should_buy(self, symbol, data): return False
            async def should_sell(self, symbol, data): return False
        
        strategy = TestStrategy(base_config)
        
        # 실제 시장 시간은 환경에 따라 다르므로 메서드 존재 여부만 확인
        result = strategy.is_market_hours()
        assert isinstance(result, bool)
    
    def test_create_signal(self, base_config):
        """매매신호 생성 테스트"""
        class TestStrategy(BaseStrategy):
            async def analyze(self, symbol): return None
            async def should_buy(self, symbol, data): return False
            async def should_sell(self, symbol, data): return False
        
        strategy = TestStrategy(base_config)
        current_price = Decimal("50000")
        
        signal = strategy.create_signal(
            symbol="005930",
            signal_type=SignalType.BUY,
            current_price=current_price,
            confidence=0.85,
            reason="테스트 매수신호"
        )
        
        assert signal.strategy_name == "Test Strategy"
        assert signal.symbol == "005930"
        assert signal.signal_type == SignalType.BUY
        assert signal.current_price == current_price
        assert signal.confidence == 0.85
        assert signal.stop_loss == current_price * 0.95  # 5% 손절
        assert signal.target_price == current_price * 1.1  # 10% 익절


class TestRSIStrategy:
    """RSI 전략 테스트"""
    
    @pytest.fixture
    def rsi_config(self):
        """RSI 전략 설정"""
        return StrategyConfig(
            strategy_name="RSI Test Strategy",
            strategy_type=StrategyType.RSI_MEAN_REVERSION,
            target_symbols=["005930"],
            risk_level=RiskLevel.MODERATE,
            max_position_size=Decimal("1000000"),
            execution_interval=60,
            strategy_params={
                "rsi_period": 14,
                "oversold_threshold": 30.0,
                "overbought_threshold": 70.0
            }
        )
    
    def test_rsi_strategy_init(self, rsi_config):
        """RSI 전략 초기화 테스트"""
        strategy = RSIStrategy(rsi_config)
        assert strategy.rsi_period == 14
        assert strategy.oversold_threshold == 30.0
        assert strategy.overbought_threshold == 70.0
    
    def test_invalid_rsi_params(self):
        """잘못된 RSI 파라미터 테스트"""
        # 잘못된 RSI 기간
        with pytest.raises(ValueError, match="RSI 기간은 5~50 사이여야 합니다"):
            config = StrategyConfig(
                strategy_name="Invalid RSI",
                strategy_type=StrategyType.RSI_MEAN_REVERSION,
                target_symbols=["005930"],
                risk_level=RiskLevel.MODERATE,
                max_position_size=Decimal("1000000"),
                strategy_params={"rsi_period": 100}
            )
            RSIStrategy(config)
    
    @pytest.mark.asyncio
    async def test_rsi_buy_condition(self, rsi_config):
        """RSI 매수 조건 테스트"""
        strategy = RSIStrategy(rsi_config)
        
        # 과매도 상황 (RSI < 30)
        data = {"rsi": 25.0, "prices": [100] * 20, "current_price": 100}
        assert await strategy.should_buy("005930", data) is True
        
        # 중립 상황 (RSI = 50)
        data = {"rsi": 50.0, "prices": [100] * 20, "current_price": 100}
        assert await strategy.should_buy("005930", data) is False
        
        # 과매수 상황 (RSI > 70)
        data = {"rsi": 80.0, "prices": [100] * 20, "current_price": 100}
        assert await strategy.should_buy("005930", data) is False
    
    @pytest.mark.asyncio
    async def test_rsi_sell_condition(self, rsi_config):
        """RSI 매도 조건 테스트"""
        strategy = RSIStrategy(rsi_config)
        
        # 과매수 상황 (RSI > 70)
        data = {"rsi": 75.0, "prices": [100] * 20, "current_price": 100}
        assert await strategy.should_sell("005930", data) is True
        
        # 중립 상황 (RSI = 50)
        data = {"rsi": 50.0, "prices": [100] * 20, "current_price": 100}
        assert await strategy.should_sell("005930", data) is False
        
        # 과매도 상황 (RSI < 30)
        data = {"rsi": 25.0, "prices": [100] * 20, "current_price": 100}
        assert await strategy.should_sell("005930", data) is False


class TestMovingAverageCrossoverStrategy:
    """이동평균 교차 전략 테스트"""
    
    @pytest.fixture
    def ma_config(self):
        """이동평균 교차 전략 설정"""
        return StrategyConfig(
            strategy_name="MA Crossover Test Strategy",
            strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
            target_symbols=["005930"],
            risk_level=RiskLevel.MODERATE,
            max_position_size=Decimal("2000000"),
            execution_interval=300,
            strategy_params={
                "short_period": 5,
                "long_period": 20,
                "use_rsi_filter": False,  # 테스트 단순화를 위해 비활성화
                "trend_confirmation": False
            }
        )
    
    def test_ma_strategy_init(self, ma_config):
        """이동평균 교차 전략 초기화 테스트"""
        strategy = MovingAverageCrossoverStrategy(ma_config)
        assert strategy.short_period == 5
        assert strategy.long_period == 20
        assert strategy.use_rsi_filter is False
    
    def test_invalid_ma_params(self):
        """잘못된 이동평균 파라미터 테스트"""
        # 단기가 장기보다 큰 경우
        with pytest.raises(ValueError, match="단기 이동평균 기간이 장기 이동평균 기간보다 작아야 합니다"):
            config = StrategyConfig(
                strategy_name="Invalid MA",
                strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
                target_symbols=["005930"],
                risk_level=RiskLevel.MODERATE,
                max_position_size=Decimal("1000000"),
                strategy_params={
                    "short_period": 20,
                    "long_period": 10
                }
            )
            MovingAverageCrossoverStrategy(config)
    
    @pytest.mark.asyncio
    async def test_golden_cross_buy_condition(self, ma_config):
        """골든크로스 매수 조건 테스트"""
        strategy = MovingAverageCrossoverStrategy(ma_config)
        
        # 골든크로스 상황: 이전에는 단기 < 장기, 현재는 단기 > 장기
        data = {
            "current_price": 110,
            "current_short_ma": 105,  # 단기 > 장기
            "current_long_ma": 100,
            "prev_short_ma": 98,      # 이전에는 단기 < 장기
            "prev_long_ma": 100,
            "rsi": None,
            "prices": [100] * 30
        }
        
        assert await strategy.should_buy("005930", data) is True
    
    @pytest.mark.asyncio
    async def test_dead_cross_sell_condition(self, ma_config):
        """데드크로스 매도 조건 테스트"""
        strategy = MovingAverageCrossoverStrategy(ma_config)
        
        # 데드크로스 상황: 이전에는 단기 > 장기, 현재는 단기 < 장기
        data = {
            "current_price": 90,
            "current_short_ma": 98,   # 단기 < 장기
            "current_long_ma": 100,
            "prev_short_ma": 102,     # 이전에는 단기 > 장기
            "prev_long_ma": 100,
            "rsi": None,
            "prices": [100] * 30
        }
        
        assert await strategy.should_sell("005930", data) is True
    
    @pytest.mark.asyncio
    async def test_no_crossover_condition(self, ma_config):
        """교차 없는 상황 테스트"""
        strategy = MovingAverageCrossoverStrategy(ma_config)
        
        # 교차 없음: 계속 단기 > 장기 상태 유지
        data = {
            "current_price": 110,
            "current_short_ma": 105,  # 단기 > 장기
            "current_long_ma": 100,
            "prev_short_ma": 103,     # 이전에도 단기 > 장기
            "prev_long_ma": 100,
            "rsi": None,
            "prices": [100] * 30
        }
        
        assert await strategy.should_buy("005930", data) is False
        assert await strategy.should_sell("005930", data) is False


class TestIntegrationTests:
    """통합 테스트"""
    
    @pytest.mark.skip(reason="Mock 데이터 테스트 비활성화 - 실제 데이터만 사용")
    async def test_strategy_with_mock_data(self):
        """Mock 데이터를 사용한 전체 전략 테스트 - 비활성화됨"""
        pass
    
    def test_strategy_info(self):
        """전략 정보 반환 테스트"""
        config = StrategyConfig(
            strategy_name="Info Test Strategy",
            strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
            target_symbols=["005930", "000660"],
            risk_level=RiskLevel.AGGRESSIVE,
            max_position_size=Decimal("5000000"),
            execution_interval=120
        )
        
        strategy = MovingAverageCrossoverStrategy(config)
        info = strategy.get_strategy_info()
        
        assert info["name"] == "Info Test Strategy"
        assert info["type"] == "moving_average_crossover"
        assert info["enabled"] is True
        assert info["target_symbols"] == ["005930", "000660"]
        assert info["risk_level"] == "aggressive"
        assert info["execution_interval"] == 120
        assert "strategy_specific" in info


# pytest 실행을 위한 메인 함수
if __name__ == "__main__":
    import asyncio
    
    # 간단한 실행 테스트
    async def run_simple_test():
        print("=== 자동매매 전략 테스트 ===")
        
        # RSI 전략 테스트
        rsi_config = StrategyConfig(
            strategy_name="Simple RSI Test",
            strategy_type=StrategyType.RSI_MEAN_REVERSION,
            target_symbols=["005930"],
            risk_level=RiskLevel.MODERATE,
            max_position_size=Decimal("1000000"),
            strategy_params={"rsi_period": 14}
        )
        
        rsi_strategy = RSIStrategy(rsi_config)
        print(f"RSI 전략 정보: {rsi_strategy.get_strategy_info()}")
        
        # 이동평균 교차 전략 테스트
        ma_config = StrategyConfig(
            strategy_name="Simple MA Test",
            strategy_type=StrategyType.MOVING_AVERAGE_CROSSOVER,
            target_symbols=["005930"],
            risk_level=RiskLevel.MODERATE,
            max_position_size=Decimal("2000000"),
            strategy_params={"short_period": 5, "long_period": 20}
        )
        
        ma_strategy = MovingAverageCrossoverStrategy(ma_config)
        print(f"MA 전략 정보: {ma_strategy.get_strategy_info()}")
        
        print("테스트 완료!")
    
    asyncio.run(run_simple_test())