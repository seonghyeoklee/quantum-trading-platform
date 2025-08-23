"""
키움증권 실시간 WebSocket 모듈

실시간 데이터 수신과 TR 명령어 처리를 통합 지원
"""

from .client import RealtimeClient

__all__ = ["RealtimeClient"]