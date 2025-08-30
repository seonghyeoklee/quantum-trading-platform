"""
전략 엔진 모듈

매매 전략의 기본 틀과 구체적인 전략 구현체들
"""

from .base_strategy import BaseStrategy
from .moving_average_crossover import MovingAverageCrossoverStrategy

__all__ = ["BaseStrategy", "MovingAverageCrossoverStrategy"]