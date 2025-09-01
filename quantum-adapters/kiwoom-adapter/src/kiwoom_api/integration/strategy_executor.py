"""
전략 실행 오케스트레이터

백그라운드에서 여러 전략을 실행하고 Java 백엔드와 동기화하는 오케스트레이터
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
import json

# Handle both relative and absolute imports for different execution contexts
try:
    from ..strategy.models.strategy_config import StrategyConfig
    from ..strategy.models.trading_signal import TradingSignal
    from ..strategy.engines.rsi_strategy import RSIStrategy
    from ..strategy.engines.moving_average_crossover import MovingAverageCrossoverStrategy
    from .java_bridge import get_java_bridge, SignalTransmissionResult
    from ..config.settings import settings
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from kiwoom_api.strategy.models.strategy_config import StrategyConfig
    from kiwoom_api.strategy.models.trading_signal import TradingSignal
    from kiwoom_api.strategy.engines.rsi_strategy import RSIStrategy
    from kiwoom_api.strategy.engines.moving_average_crossover import MovingAverageCrossoverStrategy
    from kiwoom_api.integration.java_bridge import get_java_bridge, SignalTransmissionResult
    from kiwoom_api.config.settings import settings


class ExecutionMode(Enum):
    """실행 모드"""
    CONTINUOUS = "continuous"  # 지속적 실행
    SINGLE_PASS = "single_pass"  # 한 번만 실행
    SCHEDULED = "scheduled"  # 예약 실행


@dataclass
class ExecutionConfig:
    """실행 설정"""
    mode: ExecutionMode = ExecutionMode.CONTINUOUS
    execution_interval: int = 60  # 실행 간격 (초)
    auto_send_to_java: bool = True  # Java 백엔드 자동 전송 여부
    enable_logging: bool = True  # 로깅 활성화
    max_concurrent_strategies: int = 10  # 최대 동시 실행 전략 수
    error_tolerance: int = 5  # 연속 오류 허용 횟수
    
    # 시간 제한 설정
    market_hours_only: bool = True  # 장중에만 실행
    start_time: str = "09:00"  # 시작 시간 (HH:MM)
    end_time: str = "15:30"  # 종료 시간 (HH:MM)
    
    # 성능 최적화
    batch_signal_transmission: bool = True  # 신호 배치 전송
    max_batch_size: int = 10  # 최대 배치 크기
    batch_timeout: int = 5  # 배치 타임아웃 (초)


class StrategyExecutor:
    """
    전략 실행 오케스트레이터
    
    여러 전략을 백그라운드에서 실행하고 생성된 신호를 Java 백엔드로 전송합니다.
    """
    
    def __init__(self, config: ExecutionConfig = None):
        """
        전략 실행기 초기화
        
        Args:
            config: 실행 설정 (기본값: ExecutionConfig())
        """
        self.config = config or ExecutionConfig()
        
        # 전략 관리
        self.active_strategies: Dict[str, Dict] = {}  # 활성 전략들
        self.strategy_instances: Dict[str, Any] = {}  # 전략 인스턴스들
        
        # 실행 상태
        self.is_running = False
        self.execution_tasks: Set[asyncio.Task] = set()
        
        # 신호 배치 처리
        self.pending_signals: List[TradingSignal] = []
        self.batch_task: Optional[asyncio.Task] = None
        
        # 통계
        self.execution_stats = {
            "start_time": None,
            "total_executions": 0,
            "total_signals_generated": 0,
            "total_signals_sent": 0,
            "successful_transmissions": 0,
            "failed_transmissions": 0,
            "strategies_executed": set(),
            "last_execution": None,
            "errors": []
        }
        
        print(f"🎯 Strategy Executor initialized - Mode: {self.config.mode.value}")
    
    def add_strategy(self, strategy_config: StrategyConfig) -> bool:
        """
        실행할 전략 추가
        
        Args:
            strategy_config: 전략 설정
            
        Returns:
            추가 성공 시 True
        """
        try:
            strategy_name = strategy_config.strategy_name
            
            # 중복 확인
            if strategy_name in self.active_strategies:
                print(f"⚠️ Strategy already exists: {strategy_name}")
                return False
            
            # 전략 인스턴스 생성
            strategy_instance = self._create_strategy_instance(strategy_config)
            if not strategy_instance:
                print(f"❌ Failed to create strategy instance: {strategy_name}")
                return False
            
            # 전략 등록
            self.active_strategies[strategy_name] = {
                "config": strategy_config,
                "status": "ACTIVE",
                "start_time": datetime.now(),
                "last_execution": None,
                "execution_count": 0,
                "signal_count": 0,
                "error_count": 0,
                "last_error": None
            }
            
            self.strategy_instances[strategy_name] = strategy_instance
            
            print(f"✅ Strategy added: {strategy_name} ({strategy_config.strategy_type.value})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to add strategy {strategy_config.strategy_name}: {e}")
            return False
    
    def remove_strategy(self, strategy_name: str) -> bool:
        """
        전략 제거
        
        Args:
            strategy_name: 제거할 전략명
            
        Returns:
            제거 성공 시 True
        """
        try:
            if strategy_name not in self.active_strategies:
                print(f"⚠️ Strategy not found: {strategy_name}")
                return False
            
            # 전략 비활성화
            self.active_strategies[strategy_name]["status"] = "STOPPED"
            
            # 인스턴스 제거
            if strategy_name in self.strategy_instances:
                del self.strategy_instances[strategy_name]
            
            # 활성 전략에서 제거
            del self.active_strategies[strategy_name]
            
            print(f"🗑️ Strategy removed: {strategy_name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to remove strategy {strategy_name}: {e}")
            return False
    
    def _create_strategy_instance(self, config: StrategyConfig):
        """전략 인스턴스 생성"""
        try:
            if config.strategy_type.value == "RSI_MEAN_REVERSION":
                return RSIStrategy(config)
            elif config.strategy_type.value == "MOVING_AVERAGE_CROSSOVER":
                return MovingAverageCrossoverStrategy(config)
            else:
                print(f"❌ Unsupported strategy type: {config.strategy_type}")
                return None
                
        except Exception as e:
            print(f"❌ Strategy instance creation failed: {e}")
            return None
    
    async def start_execution(self) -> bool:
        """
        전략 실행 시작
        
        Returns:
            시작 성공 시 True
        """
        if self.is_running:
            print("⚠️ Strategy executor is already running")
            return False
        
        if not self.active_strategies:
            print("⚠️ No active strategies to execute")
            return False
        
        try:
            self.is_running = True
            self.execution_stats["start_time"] = datetime.now()
            
            print(f"🚀 Starting strategy execution with {len(self.active_strategies)} strategies")
            
            # 배치 신호 처리 태스크 시작
            if self.config.batch_signal_transmission:
                self.batch_task = asyncio.create_task(self._batch_signal_processor())
            
            # 각 전략별 실행 태스크 생성
            for strategy_name in self.active_strategies.keys():
                task = asyncio.create_task(self._execute_strategy_loop(strategy_name))
                self.execution_tasks.add(task)
                task.add_done_callback(self.execution_tasks.discard)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start execution: {e}")
            self.is_running = False
            return False
    
    async def stop_execution(self) -> None:
        """전략 실행 중지"""
        if not self.is_running:
            print("⚠️ Strategy executor is not running")
            return
        
        print("🛑 Stopping strategy execution...")
        
        self.is_running = False
        
        # 모든 실행 태스크 취소
        for task in self.execution_tasks:
            if not task.done():
                task.cancel()
        
        # 배치 처리 태스크 취소
        if self.batch_task and not self.batch_task.done():
            self.batch_task.cancel()
        
        # 대기 중인 신호 전송
        if self.pending_signals:
            await self._flush_pending_signals()
        
        print("✅ Strategy execution stopped")
    
    async def _execute_strategy_loop(self, strategy_name: str) -> None:
        """전략 실행 루프"""
        strategy_info = self.active_strategies[strategy_name]
        strategy_instance = self.strategy_instances[strategy_name]
        config = strategy_info["config"]
        
        print(f"🔄 Starting execution loop for strategy: {strategy_name}")
        
        while self.is_running and strategy_info["status"] == "ACTIVE":
            try:
                # 장중 시간 확인 (설정된 경우)
                if self.config.market_hours_only and not self._is_market_hours():
                    await asyncio.sleep(60)  # 1분 대기 후 다시 확인
                    continue
                
                # 전략별 심볼 처리
                for symbol in config.target_symbols:
                    try:
                        # 신호 생성
                        signal = await strategy_instance.analyze(symbol)
                        
                        if signal:
                            strategy_info["signal_count"] += 1
                            self.execution_stats["total_signals_generated"] += 1
                            
                            print(f"📊 [{strategy_name}] Signal generated: {symbol} {signal.signal_type.value} "
                                  f"(Confidence: {signal.confidence:.3f})")
                            
                            # 신호 처리
                            await self._handle_generated_signal(signal)
                    
                    except Exception as e:
                        strategy_info["error_count"] += 1
                        strategy_info["last_error"] = str(e)
                        self._record_error(strategy_name, f"Symbol analysis error for {symbol}: {e}")
                        
                        # 연속 오류가 너무 많으면 전략 비활성화
                        if strategy_info["error_count"] > self.config.error_tolerance:
                            strategy_info["status"] = "ERROR"
                            print(f"❌ Strategy disabled due to too many errors: {strategy_name}")
                            break
                
                # 실행 통계 업데이트
                strategy_info["execution_count"] += 1
                strategy_info["last_execution"] = datetime.now()
                self.execution_stats["total_executions"] += 1
                self.execution_stats["strategies_executed"].add(strategy_name)
                self.execution_stats["last_execution"] = datetime.now()
                
                # 실행 간격 대기
                await asyncio.sleep(self.config.execution_interval)
                
            except asyncio.CancelledError:
                print(f"🛑 Strategy execution cancelled: {strategy_name}")
                break
                
            except Exception as e:
                strategy_info["error_count"] += 1
                strategy_info["last_error"] = str(e)
                self._record_error(strategy_name, f"Execution loop error: {e}")
                
                # 오류 발생 시 잠시 대기
                await asyncio.sleep(min(10, self.config.execution_interval))
    
    async def _handle_generated_signal(self, signal: TradingSignal) -> None:
        """생성된 신호 처리"""
        try:
            if self.config.auto_send_to_java:
                if self.config.batch_signal_transmission:
                    # 배치 처리를 위해 대기열에 추가
                    self.pending_signals.append(signal)
                else:
                    # 즉시 전송
                    java_bridge = await get_java_bridge()
                    result = await java_bridge.send_trading_signal(signal)
                    self._update_transmission_stats(result)
            
        except Exception as e:
            self._record_error("SignalHandler", f"Signal handling error: {e}")
    
    async def _batch_signal_processor(self) -> None:
        """배치 신호 처리기"""
        while self.is_running:
            try:
                if self.pending_signals:
                    # 배치 크기만큼 또는 모든 신호 처리
                    batch_size = min(len(self.pending_signals), self.config.max_batch_size)
                    signals_to_send = self.pending_signals[:batch_size]
                    self.pending_signals = self.pending_signals[batch_size:]
                    
                    if signals_to_send:
                        # Java 백엔드로 배치 전송
                        java_bridge = await get_java_bridge()
                        results = await java_bridge.send_multiple_signals(signals_to_send)
                        
                        # 전송 결과 통계 업데이트
                        for result in results:
                            self._update_transmission_stats(result)
                        
                        print(f"📤 Batch signals sent: {len(signals_to_send)} signals")
                
                # 배치 타임아웃만큼 대기
                await asyncio.sleep(self.config.batch_timeout)
                
            except asyncio.CancelledError:
                print("🛑 Batch signal processor cancelled")
                break
                
            except Exception as e:
                self._record_error("BatchProcessor", f"Batch processing error: {e}")
                await asyncio.sleep(5)  # 오류 시 5초 대기
    
    async def _flush_pending_signals(self) -> None:
        """대기 중인 모든 신호 전송"""
        if not self.pending_signals:
            return
        
        try:
            print(f"📤 Flushing {len(self.pending_signals)} pending signals...")
            
            java_bridge = await get_java_bridge()
            results = await java_bridge.send_multiple_signals(self.pending_signals)
            
            for result in results:
                self._update_transmission_stats(result)
            
            self.pending_signals.clear()
            print("✅ All pending signals sent")
            
        except Exception as e:
            self._record_error("SignalFlush", f"Failed to flush pending signals: {e}")
    
    def _is_market_hours(self) -> bool:
        """장중 시간 확인"""
        now = datetime.now()
        
        # 주말 확인
        if now.weekday() >= 5:  # 토요일(5), 일요일(6)
            return False
        
        # 시간 확인
        try:
            start_time = datetime.strptime(self.config.start_time, "%H:%M").time()
            end_time = datetime.strptime(self.config.end_time, "%H:%M").time()
            current_time = now.time()
            
            return start_time <= current_time <= end_time
            
        except Exception as e:
            print(f"⚠️ Market hours check error: {e}")
            return True  # 오류 시 항상 허용
    
    def _update_transmission_stats(self, result: SignalTransmissionResult) -> None:
        """전송 통계 업데이트"""
        self.execution_stats["total_signals_sent"] += 1
        
        if result.success:
            self.execution_stats["successful_transmissions"] += 1
        else:
            self.execution_stats["failed_transmissions"] += 1
    
    def _record_error(self, context: str, error_message: str) -> None:
        """오류 기록"""
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "message": error_message
        }
        
        self.execution_stats["errors"].append(error_info)
        
        # 최대 100개 오류만 유지
        if len(self.execution_stats["errors"]) > 100:
            self.execution_stats["errors"].pop(0)
        
        if self.config.enable_logging:
            print(f"❌ [{context}] {error_message}")
    
    def get_execution_status(self) -> Dict[str, Any]:
        """
        실행 상태 조회
        
        Returns:
            실행 상태 딕셔너리
        """
        # 통계 복사 및 추가 정보
        status = self.execution_stats.copy()
        status["strategies_executed"] = list(status["strategies_executed"])  # set을 list로 변환
        
        # 현재 상태 정보 추가
        status.update({
            "is_running": self.is_running,
            "active_strategy_count": len(self.active_strategies),
            "pending_signals": len(self.pending_signals),
            "active_tasks": len(self.execution_tasks),
            "config": {
                "mode": self.config.mode.value,
                "execution_interval": self.config.execution_interval,
                "auto_send_to_java": self.config.auto_send_to_java,
                "batch_transmission": self.config.batch_signal_transmission,
                "market_hours_only": self.config.market_hours_only
            }
        })
        
        # 성공률 계산
        total_sent = status["total_signals_sent"]
        if total_sent > 0:
            status["transmission_success_rate"] = status["successful_transmissions"] / total_sent
        else:
            status["transmission_success_rate"] = 0.0
        
        # 실행 시간 계산
        if status["start_time"]:
            start_time = datetime.fromisoformat(status["start_time"])
            status["runtime_seconds"] = (datetime.now() - start_time).total_seconds()
        else:
            status["runtime_seconds"] = 0
        
        return status
    
    def get_strategy_statuses(self) -> Dict[str, Any]:
        """
        전략별 상태 조회
        
        Returns:
            전략별 상태 딕셔너리
        """
        strategies = {}
        
        for name, info in self.active_strategies.items():
            strategies[name] = {
                "status": info["status"],
                "execution_count": info["execution_count"],
                "signal_count": info["signal_count"],
                "error_count": info["error_count"],
                "last_execution": info["last_execution"].isoformat() if info["last_execution"] else None,
                "last_error": info["last_error"],
                "target_symbols": info["config"].target_symbols,
                "strategy_type": info["config"].strategy_type.value
            }
        
        return strategies


# 전역 실행기 인스턴스
_global_executor = None

async def get_strategy_executor(config: ExecutionConfig = None) -> StrategyExecutor:
    """
    전역 전략 실행기 인스턴스 반환
    
    Args:
        config: 실행 설정 (선택적)
        
    Returns:
        StrategyExecutor 인스턴스
    """
    global _global_executor
    
    if _global_executor is None:
        _global_executor = StrategyExecutor(config)
    
    return _global_executor


# 테스트 함수
async def test_strategy_executor():
    """전략 실행기 테스트"""
    from ..strategy.models.strategy_config import StrategyConfig, StrategyType, RiskLevel
    from decimal import Decimal
    
    # 테스트 설정
    config = ExecutionConfig(
        mode=ExecutionMode.SINGLE_PASS,
        execution_interval=10,
        auto_send_to_java=True,
        batch_signal_transmission=False  # 테스트용으로 즉시 전송
    )
    
    executor = StrategyExecutor(config)
    
    # 테스트 전략 추가
    test_strategy_config = StrategyConfig(
        strategy_name="Test RSI Strategy",
        strategy_type=StrategyType.RSI_MEAN_REVERSION,
        target_symbols=["005930"],  # 삼성전자
        risk_level=RiskLevel.MODERATE,
        max_position_size=Decimal("1000000"),
        execution_interval=10,
        dry_run=True
    )
    
    success = executor.add_strategy(test_strategy_config)
    print(f"Strategy added: {success}")
    
    if success:
        # 실행 시작
        await executor.start_execution()
        
        # 30초 대기
        await asyncio.sleep(30)
        
        # 실행 중지
        await executor.stop_execution()
        
        # 상태 출력
        status = executor.get_execution_status()
        print(f"Execution Status: {json.dumps(status, indent=2, default=str)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_strategy_executor())