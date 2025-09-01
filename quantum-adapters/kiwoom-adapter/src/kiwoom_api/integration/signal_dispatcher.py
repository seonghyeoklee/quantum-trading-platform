"""
신호 디스패처

매매신호를 여러 대상(Java 백엔드, WebSocket 클라이언트, 로깅 시스템 등)으로 배포하는 디스패처
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json

# Handle both relative and absolute imports for different execution contexts
try:
    from ..strategy.models.trading_signal import TradingSignal
    from .java_bridge import get_java_bridge, SignalTransmissionResult
    from ..config.settings import settings
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from kiwoom_api.strategy.models.trading_signal import TradingSignal
    from kiwoom_api.integration.java_bridge import get_java_bridge, SignalTransmissionResult
    from kiwoom_api.config.settings import settings


class DispatchTarget(Enum):
    """디스패치 대상"""
    JAVA_BACKEND = "java_backend"
    WEBSOCKET = "websocket"
    FILE_LOGGER = "file_logger"
    CONSOLE = "console"
    CUSTOM = "custom"


class DispatchResult(Enum):
    """디스패치 결과"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    PARTIAL = "partial"


@dataclass
class DispatcherResult:
    """디스패처 결과"""
    target: DispatchTarget
    result: DispatchResult
    message: str
    data: Optional[Any] = None
    processing_time_ms: Optional[int] = None


@dataclass
class DispatchConfig:
    """디스패치 설정"""
    # 활성화된 디스패치 대상들
    enabled_targets: List[DispatchTarget] = field(default_factory=lambda: [
        DispatchTarget.JAVA_BACKEND,
        DispatchTarget.CONSOLE
    ])
    
    # 병렬 처리 설정
    parallel_dispatch: bool = True
    max_concurrent_dispatches: int = 5
    dispatch_timeout: int = 10  # 초
    
    # 재시도 설정
    enable_retry: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # 필터링 설정
    min_confidence_threshold: float = 0.0  # 최소 신뢰도
    allowed_signal_types: Optional[List[str]] = None  # 허용된 신호 타입
    blocked_symbols: List[str] = field(default_factory=list)  # 차단된 심볼
    
    # 로깅 설정
    enable_logging: bool = True
    log_file_path: Optional[str] = None
    
    # WebSocket 설정
    websocket_broadcast: bool = True
    websocket_channels: List[str] = field(default_factory=lambda: ["trading_signals"])
    
    # 커스텀 핸들러 설정
    custom_handlers: Dict[str, Callable] = field(default_factory=dict)


class SignalDispatcher:
    """
    신호 디스패처
    
    매매신호를 설정된 여러 대상으로 배포하고 결과를 관리합니다.
    """
    
    def __init__(self, config: DispatchConfig = None):
        """
        신호 디스패처 초기화
        
        Args:
            config: 디스패치 설정
        """
        self.config = config or DispatchConfig()
        
        # 디스패치 통계
        self.dispatch_stats = {
            "total_signals": 0,
            "successful_dispatches": 0,
            "failed_dispatches": 0,
            "filtered_signals": 0,
            "target_stats": {},
            "last_dispatch": None,
            "start_time": datetime.now()
        }
        
        # 각 타겟별 통계 초기화
        for target in DispatchTarget:
            self.dispatch_stats["target_stats"][target.value] = {
                "total": 0,
                "success": 0,
                "failed": 0,
                "average_time_ms": 0.0
            }
        
        print(f"📡 Signal Dispatcher initialized with targets: {[t.value for t in self.config.enabled_targets]}")
    
    async def dispatch_signal(self, signal: TradingSignal) -> List[DispatcherResult]:
        """
        단일 신호 디스패치
        
        Args:
            signal: 디스패치할 매매신호
            
        Returns:
            디스패치 결과 리스트
        """
        self.dispatch_stats["total_signals"] += 1
        
        # 신호 필터링 확인
        if not self._should_dispatch_signal(signal):
            self.dispatch_stats["filtered_signals"] += 1
            return [DispatcherResult(
                target=DispatchTarget.CUSTOM,
                result=DispatchResult.SKIPPED,
                message="Signal filtered out"
            )]
        
        # 디스패치 실행
        if self.config.parallel_dispatch:
            results = await self._dispatch_parallel(signal)
        else:
            results = await self._dispatch_sequential(signal)
        
        # 통계 업데이트
        self._update_dispatch_stats(results)
        
        # 마지막 디스패치 기록
        self.dispatch_stats["last_dispatch"] = {
            "timestamp": datetime.now().isoformat(),
            "signal": {
                "symbol": signal.symbol,
                "strategy": signal.strategy_name,
                "type": signal.signal_type.value
            },
            "results": len(results),
            "success_count": sum(1 for r in results if r.result == DispatchResult.SUCCESS)
        }
        
        return results
    
    async def dispatch_multiple_signals(self, signals: List[TradingSignal]) -> Dict[str, List[DispatcherResult]]:
        """
        여러 신호 일괄 디스패치
        
        Args:
            signals: 디스패치할 매매신호 리스트
            
        Returns:
            신호별 디스패치 결과 딕셔너리
        """
        if not signals:
            return {}
        
        print(f"📡 Dispatching {len(signals)} signals...")
        
        # 병렬 디스패치 실행
        dispatch_tasks = []
        for signal in signals:
            task = asyncio.create_task(self.dispatch_signal(signal))
            dispatch_tasks.append((signal, task))
        
        # 결과 수집
        results = {}
        for signal, task in dispatch_tasks:
            try:
                signal_key = f"{signal.symbol}_{signal.strategy_name}_{signal.timestamp.isoformat()}"
                results[signal_key] = await task
            except Exception as e:
                signal_key = f"{signal.symbol}_{signal.strategy_name}_{signal.timestamp.isoformat()}"
                results[signal_key] = [DispatcherResult(
                    target=DispatchTarget.CUSTOM,
                    result=DispatchResult.FAILED,
                    message=f"Dispatch task failed: {str(e)}"
                )]
        
        return results
    
    async def _dispatch_parallel(self, signal: TradingSignal) -> List[DispatcherResult]:
        """병렬 디스패치 실행"""
        tasks = []
        
        for target in self.config.enabled_targets:
            task = asyncio.create_task(self._dispatch_to_target(target, signal))
            tasks.append(task)
        
        # 타임아웃과 함께 실행
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.config.dispatch_timeout
            )
            
            # 예외 처리된 결과 변환
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    target = self.config.enabled_targets[i]
                    processed_results.append(DispatcherResult(
                        target=target,
                        result=DispatchResult.FAILED,
                        message=f"Dispatch exception: {str(result)}"
                    ))
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except asyncio.TimeoutError:
            print(f"⚠️ Dispatch timeout for signal: {signal.symbol}")
            return [DispatcherResult(
                target=DispatchTarget.CUSTOM,
                result=DispatchResult.FAILED,
                message="Dispatch timeout"
            )]
    
    async def _dispatch_sequential(self, signal: TradingSignal) -> List[DispatcherResult]:
        """순차 디스패치 실행"""
        results = []
        
        for target in self.config.enabled_targets:
            try:
                result = await self._dispatch_to_target(target, signal)
                results.append(result)
            except Exception as e:
                results.append(DispatcherResult(
                    target=target,
                    result=DispatchResult.FAILED,
                    message=f"Sequential dispatch error: {str(e)}"
                ))
        
        return results
    
    async def _dispatch_to_target(self, target: DispatchTarget, signal: TradingSignal) -> DispatcherResult:
        """특정 대상으로 디스패치"""
        start_time = datetime.now()
        
        try:
            if target == DispatchTarget.JAVA_BACKEND:
                return await self._dispatch_to_java(signal, start_time)
            
            elif target == DispatchTarget.WEBSOCKET:
                return await self._dispatch_to_websocket(signal, start_time)
            
            elif target == DispatchTarget.FILE_LOGGER:
                return await self._dispatch_to_file(signal, start_time)
            
            elif target == DispatchTarget.CONSOLE:
                return await self._dispatch_to_console(signal, start_time)
            
            elif target == DispatchTarget.CUSTOM:
                return await self._dispatch_to_custom(signal, start_time)
            
            else:
                return DispatcherResult(
                    target=target,
                    result=DispatchResult.FAILED,
                    message=f"Unknown dispatch target: {target.value}",
                    processing_time_ms=0
                )
                
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            return DispatcherResult(
                target=target,
                result=DispatchResult.FAILED,
                message=f"Dispatch error: {str(e)}",
                processing_time_ms=int(processing_time)
            )
    
    async def _dispatch_to_java(self, signal: TradingSignal, start_time: datetime) -> DispatcherResult:
        """Java 백엔드로 디스패치"""
        try:
            java_bridge = await get_java_bridge()
            transmission_result = await java_bridge.send_trading_signal(signal)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if transmission_result.success:
                return DispatcherResult(
                    target=DispatchTarget.JAVA_BACKEND,
                    result=DispatchResult.SUCCESS,
                    message="Successfully sent to Java backend",
                    data=transmission_result.response_data,
                    processing_time_ms=int(processing_time)
                )
            else:
                return DispatcherResult(
                    target=DispatchTarget.JAVA_BACKEND,
                    result=DispatchResult.FAILED,
                    message=transmission_result.message,
                    processing_time_ms=int(processing_time)
                )
                
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            return DispatcherResult(
                target=DispatchTarget.JAVA_BACKEND,
                result=DispatchResult.FAILED,
                message=f"Java dispatch error: {str(e)}",
                processing_time_ms=int(processing_time)
            )
    
    async def _dispatch_to_websocket(self, signal: TradingSignal, start_time: datetime) -> DispatcherResult:
        """WebSocket으로 디스패치"""
        try:
            # WebSocket 브로드캐스트 (구현 예정)
            # 현재는 플레이스홀더
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if self.config.websocket_broadcast:
                # TODO: WebSocket manager와 연동
                signal_data = {
                    "type": "trading_signal",
                    "data": {
                        "symbol": signal.symbol,
                        "strategy": signal.strategy_name,
                        "signal_type": signal.signal_type.value,
                        "confidence": signal.confidence,
                        "timestamp": signal.timestamp.isoformat()
                    }
                }
                
                # WebSocket 채널별 브로드캐스트 시뮬레이션
                for channel in self.config.websocket_channels:
                    print(f"📡 [WebSocket:{channel}] {signal.symbol} {signal.signal_type.value}")
            
            return DispatcherResult(
                target=DispatchTarget.WEBSOCKET,
                result=DispatchResult.SUCCESS,
                message="WebSocket broadcast completed",
                processing_time_ms=int(processing_time)
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            return DispatcherResult(
                target=DispatchTarget.WEBSOCKET,
                result=DispatchResult.FAILED,
                message=f"WebSocket dispatch error: {str(e)}",
                processing_time_ms=int(processing_time)
            )
    
    async def _dispatch_to_file(self, signal: TradingSignal, start_time: datetime) -> DispatcherResult:
        """파일로 디스패치"""
        try:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # 로그 데이터 준비
            log_entry = {
                "timestamp": signal.timestamp.isoformat(),
                "strategy": signal.strategy_name,
                "symbol": signal.symbol,
                "signal_type": signal.signal_type.value,
                "strength": signal.strength.value,
                "current_price": float(signal.current_price),
                "confidence": signal.confidence,
                "reason": signal.reason
            }
            
            # 파일 경로 결정
            log_file = self.config.log_file_path or f"trading_signals_{datetime.now().strftime('%Y%m%d')}.jsonl"
            
            # 파일에 기록
            import os
            os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else ".", exist_ok=True)
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
            return DispatcherResult(
                target=DispatchTarget.FILE_LOGGER,
                result=DispatchResult.SUCCESS,
                message=f"Logged to file: {log_file}",
                processing_time_ms=int(processing_time)
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            return DispatcherResult(
                target=DispatchTarget.FILE_LOGGER,
                result=DispatchResult.FAILED,
                message=f"File logging error: {str(e)}",
                processing_time_ms=int(processing_time)
            )
    
    async def _dispatch_to_console(self, signal: TradingSignal, start_time: datetime) -> DispatcherResult:
        """콘솔로 디스패치"""
        try:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # 콘솔 출력
            timestamp_str = signal.timestamp.strftime("%H:%M:%S")
            confidence_str = f"{signal.confidence:.3f}"
            
            print(f"🎯 [{timestamp_str}] {signal.strategy_name}: {signal.symbol} "
                  f"{signal.signal_type.value} (신뢰도: {confidence_str}) - {signal.reason}")
            
            return DispatcherResult(
                target=DispatchTarget.CONSOLE,
                result=DispatchResult.SUCCESS,
                message="Console output completed",
                processing_time_ms=int(processing_time)
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            return DispatcherResult(
                target=DispatchTarget.CONSOLE,
                result=DispatchResult.FAILED,
                message=f"Console output error: {str(e)}",
                processing_time_ms=int(processing_time)
            )
    
    async def _dispatch_to_custom(self, signal: TradingSignal, start_time: datetime) -> DispatcherResult:
        """커스텀 핸들러로 디스패치"""
        try:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # 커스텀 핸들러 실행
            results = []
            for handler_name, handler_func in self.config.custom_handlers.items():
                try:
                    if asyncio.iscoroutinefunction(handler_func):
                        await handler_func(signal)
                    else:
                        handler_func(signal)
                    results.append(f"{handler_name}: success")
                except Exception as e:
                    results.append(f"{handler_name}: failed - {str(e)}")
            
            return DispatcherResult(
                target=DispatchTarget.CUSTOM,
                result=DispatchResult.SUCCESS if results else DispatchResult.SKIPPED,
                message=f"Custom handlers: {', '.join(results)}" if results else "No custom handlers",
                processing_time_ms=int(processing_time)
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            return DispatcherResult(
                target=DispatchTarget.CUSTOM,
                result=DispatchResult.FAILED,
                message=f"Custom dispatch error: {str(e)}",
                processing_time_ms=int(processing_time)
            )
    
    def _should_dispatch_signal(self, signal: TradingSignal) -> bool:
        """신호 디스패치 여부 결정"""
        # 신뢰도 필터
        if signal.confidence < self.config.min_confidence_threshold:
            return False
        
        # 신호 타입 필터
        if self.config.allowed_signal_types:
            if signal.signal_type.value not in self.config.allowed_signal_types:
                return False
        
        # 차단된 심볼 필터
        if signal.symbol in self.config.blocked_symbols:
            return False
        
        return True
    
    def _update_dispatch_stats(self, results: List[DispatcherResult]) -> None:
        """디스패치 통계 업데이트"""
        success_count = sum(1 for r in results if r.result == DispatchResult.SUCCESS)
        
        if success_count > 0:
            self.dispatch_stats["successful_dispatches"] += 1
        
        if success_count < len(results):
            self.dispatch_stats["failed_dispatches"] += 1
        
        # 타겟별 통계 업데이트
        for result in results:
            target_stats = self.dispatch_stats["target_stats"][result.target.value]
            target_stats["total"] += 1
            
            if result.result == DispatchResult.SUCCESS:
                target_stats["success"] += 1
            else:
                target_stats["failed"] += 1
            
            # 평균 처리 시간 업데이트
            if result.processing_time_ms:
                current_avg = target_stats["average_time_ms"]
                total = target_stats["total"]
                target_stats["average_time_ms"] = (current_avg * (total - 1) + result.processing_time_ms) / total
    
    def get_dispatch_stats(self) -> Dict[str, Any]:
        """
        디스패치 통계 조회
        
        Returns:
            디스패치 통계 딕셔너리
        """
        stats = self.dispatch_stats.copy()
        
        # 성공률 계산
        total = stats["successful_dispatches"] + stats["failed_dispatches"]
        if total > 0:
            stats["success_rate"] = stats["successful_dispatches"] / total
        else:
            stats["success_rate"] = 0.0
        
        # 실행 시간 계산
        stats["runtime_seconds"] = (datetime.now() - stats["start_time"]).total_seconds()
        stats["start_time"] = stats["start_time"].isoformat()
        
        return stats
    
    def add_custom_handler(self, name: str, handler: Callable) -> None:
        """
        커스텀 핸들러 추가
        
        Args:
            name: 핸들러 이름
            handler: 핸들러 함수 (동기 또는 비동기)
        """
        self.config.custom_handlers[name] = handler
        print(f"📋 Custom handler added: {name}")
    
    def remove_custom_handler(self, name: str) -> bool:
        """
        커스텀 핸들러 제거
        
        Args:
            name: 제거할 핸들러 이름
            
        Returns:
            제거 성공 시 True
        """
        if name in self.config.custom_handlers:
            del self.config.custom_handlers[name]
            print(f"🗑️ Custom handler removed: {name}")
            return True
        return False


# 전역 디스패처 인스턴스
_global_dispatcher = None

async def get_signal_dispatcher(config: DispatchConfig = None) -> SignalDispatcher:
    """
    전역 신호 디스패처 인스턴스 반환
    
    Args:
        config: 디스패치 설정 (선택적)
        
    Returns:
        SignalDispatcher 인스턴스
    """
    global _global_dispatcher
    
    if _global_dispatcher is None:
        _global_dispatcher = SignalDispatcher(config)
    
    return _global_dispatcher


# 편의 함수들

async def dispatch_signal(signal: TradingSignal, config: DispatchConfig = None) -> List[DispatcherResult]:
    """
    단일 신호 디스패치 편의 함수
    
    Args:
        signal: 디스패치할 신호
        config: 디스패치 설정 (선택적)
        
    Returns:
        디스패치 결과 리스트
    """
    dispatcher = await get_signal_dispatcher(config)
    return await dispatcher.dispatch_signal(signal)


async def dispatch_multiple_signals(signals: List[TradingSignal], config: DispatchConfig = None) -> Dict[str, List[DispatcherResult]]:
    """
    여러 신호 디스패치 편의 함수
    
    Args:
        signals: 디스패치할 신호 리스트
        config: 디스패치 설정 (선택적)
        
    Returns:
        신호별 디스패치 결과 딕셔너리
    """
    dispatcher = await get_signal_dispatcher(config)
    return await dispatcher.dispatch_multiple_signals(signals)


# 테스트 함수
async def test_signal_dispatcher():
    """신호 디스패처 테스트"""
    from ..strategy.models.trading_signal import TradingSignal, SignalType, SignalStrength
    from decimal import Decimal
    
    # 테스트 설정
    config = DispatchConfig(
        enabled_targets=[DispatchTarget.CONSOLE, DispatchTarget.FILE_LOGGER],
        parallel_dispatch=True,
        enable_logging=True
    )
    
    dispatcher = SignalDispatcher(config)
    
    # 테스트 신호 생성
    test_signal = TradingSignal(
        strategy_name="Test Dispatcher Strategy",
        symbol="005930",
        signal_type=SignalType.BUY,
        strength=SignalStrength.MODERATE,
        current_price=Decimal("75000"),
        confidence=0.85,
        reason="테스트 신호 - 디스패처 동작 확인",
        timestamp=datetime.now()
    )
    
    # 신호 디스패치
    results = await dispatcher.dispatch_signal(test_signal)
    
    print(f"📊 Dispatch Results:")
    for result in results:
        print(f"   {result.target.value}: {result.result.value} - {result.message} ({result.processing_time_ms}ms)")
    
    # 통계 출력
    stats = dispatcher.get_dispatch_stats()
    print(f"📈 Dispatch Stats: {json.dumps(stats, indent=2, default=str)}")
    
    return results


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_signal_dispatcher())