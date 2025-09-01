"""
Java 백엔드 연동 브리지

Python 전략 엔진에서 생성된 매매신호를 Java 백엔드로 전송하는 브리지 모듈
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import httpx
from dataclasses import dataclass

# Handle both relative and absolute imports for different execution contexts
try:
    from ..config.settings import settings
    from ..strategy.models.trading_signal import TradingSignal
    from ..utils.rate_limiter import get_rate_limiter
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from kiwoom_api.config.settings import settings
    from kiwoom_api.strategy.models.trading_signal import TradingSignal
    from kiwoom_api.utils.rate_limiter import get_rate_limiter


@dataclass
class SignalTransmissionResult:
    """신호 전송 결과"""
    success: bool
    message: str
    response_data: Optional[Dict] = None
    transmission_time_ms: Optional[int] = None
    retry_count: int = 0


class JavaBackendBridge:
    """
    Java 백엔드 연동 브리지
    
    Python 전략 엔진에서 생성된 TradingSignal을 Java 백엔드의 
    /api/v1/trading/signals/receive 엔드포인트로 전송합니다.
    """
    
    def __init__(self, java_backend_url: str = None):
        """
        Java 브리지 초기화
        
        Args:
            java_backend_url: Java 백엔드 URL (기본값: 환경변수에서 가져옴)
        """
        self.java_backend_url = java_backend_url or settings.JAVA_BACKEND_URL
        self.signal_endpoint = f"{self.java_backend_url}/api/v1/trading/signals/receive"
        self.health_endpoint = f"{self.java_backend_url}/actuator/health"
        
        # HTTP 클라이언트 설정
        self.timeout = httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=10.0)
        
        # 재시도 설정
        self.max_retries = 3
        self.retry_delays = [1, 2, 4]  # exponential backoff
        
        # 전송 통계
        self.transmission_stats = {
            "total_sent": 0,
            "successful_sent": 0,
            "failed_sent": 0,
            "last_transmission": None
        }
        
        print(f"🔗 Java Backend Bridge initialized - Target: {self.java_backend_url}")
    
    async def check_java_backend_health(self) -> bool:
        """
        Java 백엔드 헬스체크
        
        Returns:
            Java 백엔드가 정상이면 True, 아니면 False
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.health_endpoint)
                
                if response.status_code == 200:
                    health_data = response.json()
                    status = health_data.get("status", "DOWN")
                    print(f"✅ Java Backend Health: {status}")
                    return status == "UP"
                else:
                    print(f"⚠️ Java Backend Health Check Failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ Java Backend Health Check Error: {e}")
            return False
    
    async def send_trading_signal(self, signal: TradingSignal) -> SignalTransmissionResult:
        """
        매매신호를 Java 백엔드로 전송
        
        Args:
            signal: 전송할 매매신호
            
        Returns:
            SignalTransmissionResult 객체
        """
        start_time = datetime.now()
        
        try:
            # 신호 데이터를 JSON으로 변환
            signal_data = self._convert_signal_to_dict(signal)
            
            # Rate limiting 적용
            rate_limiter = await get_rate_limiter()
            
            async def _send_request():
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.signal_endpoint,
                        json=signal_data,
                        headers={
                            "Content-Type": "application/json",
                            "X-Source": "PythonStrategyEngine",
                            "X-Timestamp": datetime.now().isoformat()
                        }
                    )
                    return response
            
            # Rate limiting과 재시도 로직이 적용된 요청 실행
            response = await rate_limiter.execute_with_retry(
                f"java_signal_{signal.symbol}_{signal.strategy_name}",
                _send_request
            )
            
            # 전송 시간 계산
            transmission_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # 응답 처리
            if response.status_code == 200:
                response_data = response.json()
                result = SignalTransmissionResult(
                    success=True,
                    message="Signal transmitted successfully",
                    response_data=response_data,
                    transmission_time_ms=int(transmission_time)
                )
                
                # 성공 통계 업데이트
                self._update_stats(success=True, signal=signal)
                
                print(f"📤 Signal transmitted to Java: {signal.symbol} {signal.signal_type.value} "
                      f"(Confidence: {signal.confidence:.3f}, Time: {transmission_time:.0f}ms)")
                
                return result
                
            else:
                error_message = f"HTTP {response.status_code}: {response.text}"
                result = SignalTransmissionResult(
                    success=False,
                    message=error_message,
                    transmission_time_ms=int(transmission_time)
                )
                
                # 실패 통계 업데이트
                self._update_stats(success=False, signal=signal)
                
                print(f"❌ Signal transmission failed: {error_message}")
                return result
                
        except Exception as e:
            transmission_time = (datetime.now() - start_time).total_seconds() * 1000
            error_message = f"Signal transmission error: {str(e)}"
            
            result = SignalTransmissionResult(
                success=False,
                message=error_message,
                transmission_time_ms=int(transmission_time)
            )
            
            # 실패 통계 업데이트
            self._update_stats(success=False, signal=signal)
            
            print(f"❌ {error_message}")
            return result
    
    async def send_multiple_signals(self, signals: List[TradingSignal]) -> List[SignalTransmissionResult]:
        """
        여러 매매신호를 병렬로 전송
        
        Args:
            signals: 전송할 매매신호 리스트
            
        Returns:
            전송 결과 리스트
        """
        if not signals:
            return []
        
        print(f"📤 Sending {len(signals)} signals to Java backend...")
        
        # 병렬 전송 실행
        tasks = [self.send_trading_signal(signal) for signal in signals]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 예외 처리된 결과들을 변환
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(SignalTransmissionResult(
                    success=False,
                    message=f"Signal transmission exception: {str(result)}"
                ))
            else:
                processed_results.append(result)
        
        # 전송 요약 로그
        successful = sum(1 for r in processed_results if r.success)
        failed = len(processed_results) - successful
        
        print(f"📊 Signal transmission summary: {successful} successful, {failed} failed")
        
        return processed_results
    
    def _convert_signal_to_dict(self, signal: TradingSignal) -> Dict[str, Any]:
        """
        TradingSignal을 Java 백엔드가 이해할 수 있는 딕셔너리로 변환
        
        Args:
            signal: 변환할 매매신호
            
        Returns:
            Java 호환 딕셔너리
        """
        return {
            "strategyName": signal.strategy_name,
            "symbol": signal.symbol,
            "signalType": signal.signal_type.value,  # BUY, SELL, HOLD, CLOSE
            "strength": signal.strength.value,       # WEAK, MODERATE, STRONG
            "currentPrice": float(signal.current_price),
            "targetPrice": float(signal.target_price) if signal.target_price else None,
            "stopLoss": float(signal.stop_loss) if signal.stop_loss else None,
            "confidence": signal.confidence,
            "reason": signal.reason,
            "timestamp": signal.timestamp.isoformat(),
            "validUntil": signal.valid_until.isoformat() if signal.valid_until else None,
            "dryRun": getattr(signal, 'dry_run', True),  # 기본값은 모의투자
            "metadata": {
                "source": "PythonStrategyEngine",
                "generatedAt": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
    
    def _update_stats(self, success: bool, signal: TradingSignal) -> None:
        """전송 통계 업데이트"""
        self.transmission_stats["total_sent"] += 1
        
        if success:
            self.transmission_stats["successful_sent"] += 1
        else:
            self.transmission_stats["failed_sent"] += 1
        
        self.transmission_stats["last_transmission"] = {
            "timestamp": datetime.now().isoformat(),
            "symbol": signal.symbol,
            "strategy": signal.strategy_name,
            "success": success
        }
    
    def get_transmission_stats(self) -> Dict[str, Any]:
        """
        전송 통계 반환
        
        Returns:
            전송 통계 딕셔너리
        """
        stats = self.transmission_stats.copy()
        
        # 성공률 계산
        total = stats["total_sent"]
        if total > 0:
            stats["success_rate"] = stats["successful_sent"] / total
        else:
            stats["success_rate"] = 0.0
        
        return stats
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Java 백엔드 연결 테스트
        
        Returns:
            테스트 결과 딕셔너리
        """
        print("🔍 Testing Java backend connection...")
        
        # 1. 헬스체크
        health_ok = await self.check_java_backend_health()
        
        # 2. 테스트 신호 생성
        from ..strategy.models.trading_signal import SignalType, SignalStrength
        from decimal import Decimal
        
        test_signal = TradingSignal(
            strategy_name="ConnectionTest",
            symbol="000000",  # 테스트용 심볼
            signal_type=SignalType.HOLD,
            strength=SignalStrength.WEAK,
            current_price=Decimal("1000"),
            confidence=0.5,
            reason="Connection test signal",
            timestamp=datetime.now(),
            dry_run=True
        )
        
        # 3. 테스트 신호 전송
        transmission_result = await self.send_trading_signal(test_signal)
        
        return {
            "health_check": health_ok,
            "signal_transmission": transmission_result.success,
            "transmission_time_ms": transmission_result.transmission_time_ms,
            "java_backend_url": self.java_backend_url,
            "test_timestamp": datetime.now().isoformat()
        }


# 전역 브리지 인스턴스
_global_bridge = None

async def get_java_bridge() -> JavaBackendBridge:
    """
    전역 Java 브리지 인스턴스 반환
    
    Returns:
        JavaBackendBridge 인스턴스
    """
    global _global_bridge
    
    if _global_bridge is None:
        _global_bridge = JavaBackendBridge()
        # 초기 헬스체크
        await _global_bridge.check_java_backend_health()
    
    return _global_bridge


# 편의 함수들

async def send_signal_to_java(signal: TradingSignal) -> SignalTransmissionResult:
    """
    단일 신호를 Java 백엔드로 전송하는 편의 함수
    
    Args:
        signal: 전송할 매매신호
        
    Returns:
        SignalTransmissionResult 객체
    """
    bridge = await get_java_bridge()
    return await bridge.send_trading_signal(signal)


async def send_signals_to_java(signals: List[TradingSignal]) -> List[SignalTransmissionResult]:
    """
    여러 신호를 Java 백엔드로 전송하는 편의 함수
    
    Args:
        signals: 전송할 매매신호 리스트
        
    Returns:
        전송 결과 리스트
    """
    bridge = await get_java_bridge()
    return await bridge.send_multiple_signals(signals)


# 테스트 함수
async def test_java_bridge():
    """Java 브리지 테스트 함수"""
    bridge = await get_java_bridge()
    test_result = await bridge.test_connection()
    
    print(f"🧪 Java Bridge Test Result:")
    print(f"   Health Check: {'✅' if test_result['health_check'] else '❌'}")
    print(f"   Signal Transmission: {'✅' if test_result['signal_transmission'] else '❌'}")
    print(f"   Transmission Time: {test_result.get('transmission_time_ms', 0)}ms")
    print(f"   Java Backend URL: {test_result['java_backend_url']}")
    
    return test_result


if __name__ == "__main__":
    # 스크립트 직접 실행 시 테스트 수행
    import asyncio
    asyncio.run(test_java_bridge())