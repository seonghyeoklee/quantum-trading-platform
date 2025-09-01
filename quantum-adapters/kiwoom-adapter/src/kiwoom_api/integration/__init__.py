"""
Integration module for external system connectivity

Java 백엔드, 외부 시스템과의 연동을 위한 통합 모듈
"""

# Handle both relative and absolute imports for different execution contexts
try:
    from .java_bridge import (
        JavaBackendBridge,
        SignalTransmissionResult,
        get_java_bridge,
        send_signal_to_java,
        send_signals_to_java,
        test_java_bridge
    )
    from .strategy_executor import StrategyExecutor, ExecutionConfig
    from .signal_dispatcher import SignalDispatcher, DispatchConfig
except ImportError:
    # Graceful handling for import errors during development
    pass

__all__ = [
    'JavaBackendBridge',
    'SignalTransmissionResult', 
    'StrategyExecutor',
    'ExecutionConfig',
    'SignalDispatcher',
    'DispatchConfig',
    'get_java_bridge',
    'send_signal_to_java',
    'send_signals_to_java',
    'test_java_bridge'
]