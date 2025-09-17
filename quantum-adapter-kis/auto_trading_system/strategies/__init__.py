# Trading strategies package

from .base_strategy import BaseStrategy, StrategyContext
from .golden_cross_strategy import GoldenCrossStrategy
from .rsi_strategy import RSIStrategy
from .volume_breakout_strategy import VolumeBreakoutStrategy
from .mean_reversion_strategy import MeanReversionStrategy

__all__ = [
    'BaseStrategy',
    'StrategyContext',
    'GoldenCrossStrategy',
    'RSIStrategy',
    'VolumeBreakoutStrategy',
    'MeanReversionStrategy'
]

# 전략 팩토리
STRATEGY_CLASSES = {
    'golden_cross': GoldenCrossStrategy,
    'rsi': RSIStrategy,
    'volume_breakout': VolumeBreakoutStrategy,
    'mean_reversion': MeanReversionStrategy
}

def create_strategy(strategy_name: str, config: dict = None) -> BaseStrategy:
    """
    전략 팩토리 함수

    Args:
        strategy_name: 전략 이름
        config: 전략 설정

    Returns:
        BaseStrategy 인스턴스

    Raises:
        ValueError: 지원하지 않는 전략명
    """
    if strategy_name not in STRATEGY_CLASSES:
        available_strategies = list(STRATEGY_CLASSES.keys())
        raise ValueError(f"지원하지 않는 전략: {strategy_name}. 사용 가능한 전략: {available_strategies}")

    strategy_class = STRATEGY_CLASSES[strategy_name]
    return strategy_class(config)

def get_available_strategies() -> list:
    """사용 가능한 전략 목록 반환"""
    return list(STRATEGY_CLASSES.keys())