"""
자동매매 전략 API 엔드포인트

Python 전략 엔진을 FastAPI로 노출하여 Java 백엔드와 연동
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from decimal import Decimal

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

# Handle both relative and absolute imports for different execution contexts
try:
    from ..strategy.engines.rsi_strategy import RSIStrategy
    from ..strategy.engines.moving_average_crossover import MovingAverageCrossoverStrategy
    from ..strategy.models.strategy_config import StrategyConfig, StrategyType, RiskLevel
    from ..strategy.models.trading_signal import TradingSignal, SignalType, SignalStrength
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from kiwoom_api.strategy.engines.rsi_strategy import RSIStrategy
    from kiwoom_api.strategy.engines.moving_average_crossover import MovingAverageCrossoverStrategy
    from kiwoom_api.strategy.models.strategy_config import StrategyConfig, StrategyType, RiskLevel
    from kiwoom_api.strategy.models.trading_signal import TradingSignal, SignalType, SignalStrength

router = APIRouter(prefix="/api/v1/strategy", tags=["Strategy"])

# 전역 전략 실행 상태 관리
active_strategies: Dict[str, Dict] = {}
strategy_results: List[Dict] = []


# === Pydantic 모델들 ===

class StrategyStartRequest(BaseModel):
    """전략 시작 요청"""
    strategy_name: str
    strategy_type: str  # "rsi" or "ma_crossover"
    symbols: List[str]  # ["005930", "000660"]
    risk_level: str = "moderate"  # "conservative", "moderate", "aggressive"
    max_position_size: int = 1000000  # 최대 포지션 크기 (원)
    min_confidence: float = 0.7
    dry_run: bool = True  # 모의투자 여부
    
    # 전략별 파라미터 (선택적)
    rsi_period: Optional[int] = 14
    rsi_oversold: Optional[float] = 30.0
    rsi_overbought: Optional[float] = 70.0
    
    ma_short_period: Optional[int] = 5
    ma_long_period: Optional[int] = 20
    ma_use_rsi_filter: Optional[bool] = True


class StrategyStopRequest(BaseModel):
    """전략 중지 요청"""
    strategy_name: str


class AnalysisRequest(BaseModel):
    """단발성 분석 요청"""
    strategy_type: str  # "rsi" or "ma_crossover"
    symbol: str  # "005930"
    
    # RSI 파라미터
    rsi_period: Optional[int] = 14
    rsi_oversold: Optional[float] = 30.0
    rsi_overbought: Optional[float] = 70.0
    
    # MA 파라미터
    ma_short_period: Optional[int] = 5
    ma_long_period: Optional[int] = 20
    ma_use_rsi_filter: Optional[bool] = True


class TradingSignalResponse(BaseModel):
    """매매신호 응답"""
    strategy_name: str
    symbol: str
    signal_type: str  # "BUY", "SELL", "HOLD", "CLOSE"
    strength: str  # "WEAK", "MODERATE", "STRONG"
    current_price: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    confidence: float
    reason: str
    timestamp: datetime
    valid_until: Optional[datetime] = None


class StrategyStatusResponse(BaseModel):
    """전략 상태 응답"""
    strategy_name: str
    status: str  # "ACTIVE", "STOPPED", "ERROR"
    symbols: List[str]
    last_analysis: Optional[datetime] = None
    signals_generated: int
    errors: List[str] = []


# === 유틸리티 함수들 ===

def create_strategy_config(request: StrategyStartRequest) -> StrategyConfig:
    """요청으로부터 전략 설정 생성"""
    strategy_type_map = {
        "rsi": StrategyType.RSI_MEAN_REVERSION,
        "ma_crossover": StrategyType.MOVING_AVERAGE_CROSSOVER
    }
    
    risk_level_map = {
        "conservative": RiskLevel.CONSERVATIVE,
        "moderate": RiskLevel.MODERATE,
        "aggressive": RiskLevel.AGGRESSIVE
    }
    
    # 전략별 파라미터 구성
    strategy_params = {}
    if request.strategy_type == "rsi":
        strategy_params.update({
            "rsi_period": request.rsi_period,
            "oversold_threshold": request.rsi_oversold,
            "overbought_threshold": request.rsi_overbought
        })
    elif request.strategy_type == "ma_crossover":
        strategy_params.update({
            "short_period": request.ma_short_period,
            "long_period": request.ma_long_period,
            "use_rsi_filter": request.ma_use_rsi_filter
        })
    
    return StrategyConfig(
        strategy_name=request.strategy_name,
        strategy_type=strategy_type_map[request.strategy_type],
        target_symbols=request.symbols,
        risk_level=risk_level_map[request.risk_level],
        max_position_size=Decimal(str(request.max_position_size)),
        execution_interval=60,
        min_confidence=request.min_confidence,
        dry_run=request.dry_run,
        strategy_params=strategy_params
    )


def create_strategy_instance(config: StrategyConfig):
    """설정에 따른 전략 인스턴스 생성"""
    if config.strategy_type == StrategyType.RSI_MEAN_REVERSION:
        return RSIStrategy(config)
    elif config.strategy_type == StrategyType.MOVING_AVERAGE_CROSSOVER:
        return MovingAverageCrossoverStrategy(config)
    else:
        raise ValueError(f"지원하지 않는 전략 타입: {config.strategy_type}")


def trading_signal_to_response(signal: TradingSignal) -> TradingSignalResponse:
    """TradingSignal을 응답 모델로 변환"""
    return TradingSignalResponse(
        strategy_name=signal.strategy_name,
        symbol=signal.symbol,
        signal_type=signal.signal_type.value,
        strength=signal.strength.value,
        current_price=float(signal.current_price),
        target_price=float(signal.target_price) if signal.target_price else None,
        stop_loss=float(signal.stop_loss) if signal.stop_loss else None,
        confidence=signal.confidence,
        reason=signal.reason,
        timestamp=signal.timestamp,
        valid_until=signal.valid_until
    )


# === API 엔드포인트들 ===

@router.post("/analyze", response_model=Optional[TradingSignalResponse])
async def analyze_symbol(request: AnalysisRequest):
    """
    단일 종목 즉시 분석
    
    지정된 전략으로 특정 종목을 즉시 분석하여 매매신호 반환
    """
    try:
        # 임시 전략 설정 생성
        temp_config = StrategyConfig(
            strategy_name=f"temp_{request.strategy_type}_{request.symbol}",
            strategy_type=StrategyType.RSI_MEAN_REVERSION if request.strategy_type == "rsi" else StrategyType.MOVING_AVERAGE_CROSSOVER,
            target_symbols=[request.symbol],
            risk_level=RiskLevel.MODERATE,
            max_position_size=Decimal("1000000"),
            execution_interval=60,
            strategy_params={
                "rsi_period": request.rsi_period,
                "oversold_threshold": request.rsi_oversold,
                "overbought_threshold": request.rsi_overbought,
                "short_period": request.ma_short_period,
                "long_period": request.ma_long_period,
                "use_rsi_filter": request.ma_use_rsi_filter
            } if request.strategy_type == "rsi" else {
                "short_period": request.ma_short_period,
                "long_period": request.ma_long_period,
                "use_rsi_filter": request.ma_use_rsi_filter
            }
        )
        
        # 전략 인스턴스 생성 및 분석 실행
        strategy = create_strategy_instance(temp_config)
        signal = await strategy.analyze(request.symbol)
        
        if signal:
            # 결과 저장 (최근 100개만 유지)
            result = {
                "timestamp": datetime.now(),
                "type": "single_analysis",
                "signal": trading_signal_to_response(signal).dict()
            }
            strategy_results.append(result)
            if len(strategy_results) > 100:
                strategy_results.pop(0)
            
            return trading_signal_to_response(signal)
        else:
            return None
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)}")


@router.post("/start")
async def start_strategy(request: StrategyStartRequest, background_tasks: BackgroundTasks):
    """
    전략 시작
    
    지정된 전략을 백그라운드에서 지속적으로 실행
    """
    try:
        if request.strategy_name in active_strategies:
            raise HTTPException(status_code=400, detail=f"전략 '{request.strategy_name}'이 이미 실행 중입니다.")
        
        # 전략 설정 및 인스턴스 생성
        config = create_strategy_config(request)
        strategy = create_strategy_instance(config)
        
        # 전략 상태 초기화
        active_strategies[request.strategy_name] = {
            "config": config,
            "strategy": strategy,
            "status": "ACTIVE",
            "start_time": datetime.now(),
            "last_analysis": None,
            "signals_generated": 0,
            "errors": []
        }
        
        # 백그라운드 실행 시작
        background_tasks.add_task(run_strategy_background, request.strategy_name)
        
        return {"message": f"전략 '{request.strategy_name}' 시작됨", "symbols": request.symbols}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"전략 시작 실패: {str(e)}")


@router.post("/stop")
async def stop_strategy(request: StrategyStopRequest):
    """전략 중지"""
    try:
        if request.strategy_name not in active_strategies:
            raise HTTPException(status_code=404, detail=f"전략 '{request.strategy_name}'을 찾을 수 없습니다.")
        
        active_strategies[request.strategy_name]["status"] = "STOPPED"
        
        return {"message": f"전략 '{request.strategy_name}' 중지됨"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"전략 중지 실패: {str(e)}")


@router.get("/status/{strategy_name}", response_model=StrategyStatusResponse)
async def get_strategy_status(strategy_name: str):
    """전략 상태 조회"""
    if strategy_name not in active_strategies:
        raise HTTPException(status_code=404, detail=f"전략 '{strategy_name}'을 찾을 수 없습니다.")
    
    strategy_info = active_strategies[strategy_name]
    
    return StrategyStatusResponse(
        strategy_name=strategy_name,
        status=strategy_info["status"],
        symbols=strategy_info["config"].target_symbols,
        last_analysis=strategy_info["last_analysis"],
        signals_generated=strategy_info["signals_generated"],
        errors=strategy_info["errors"]
    )


@router.get("/list")
async def list_strategies():
    """실행 중인 전략 목록 조회"""
    return {
        "active_strategies": list(active_strategies.keys()),
        "total_count": len(active_strategies)
    }


@router.get("/signals/recent")
async def get_recent_signals(limit: int = 20):
    """최근 매매신호 조회"""
    recent_signals = [
        result for result in strategy_results 
        if result["type"] in ["single_analysis", "continuous_analysis"]
    ][-limit:]
    
    return {"signals": recent_signals, "count": len(recent_signals)}


@router.delete("/clear")
async def clear_all_strategies():
    """모든 전략 중지 및 결과 초기화"""
    for strategy_name in active_strategies:
        active_strategies[strategy_name]["status"] = "STOPPED"
    
    active_strategies.clear()
    strategy_results.clear()
    
    return {"message": "모든 전략이 중지되고 결과가 초기화되었습니다."}


# === 백그라운드 실행 함수 ===

async def run_strategy_background(strategy_name: str):
    """백그라운드에서 전략 지속 실행"""
    if strategy_name not in active_strategies:
        return
    
    strategy_info = active_strategies[strategy_name]
    config = strategy_info["config"]
    strategy = strategy_info["strategy"]
    
    print(f"🚀 전략 '{strategy_name}' 백그라운드 실행 시작")
    
    while strategy_info["status"] == "ACTIVE":
        try:
            for symbol in config.target_symbols:
                # 전략이 중지되었으면 즉시 종료
                if strategy_info["status"] != "ACTIVE":
                    break
                
                # 분석 실행
                signal = await strategy.analyze(symbol)
                strategy_info["last_analysis"] = datetime.now()
                
                if signal:
                    # 신호 생성 시 결과 저장
                    result = {
                        "timestamp": datetime.now(),
                        "type": "continuous_analysis",
                        "strategy_name": strategy_name,
                        "signal": trading_signal_to_response(signal).dict()
                    }
                    strategy_results.append(result)
                    if len(strategy_results) > 1000:  # 최대 1000개 유지
                        strategy_results.pop(0)
                    
                    strategy_info["signals_generated"] += 1
                    
                    print(f"📊 [{strategy_name}] {symbol} 신호: {signal.signal_type.value} (신뢰도: {signal.confidence:.3f})")
                    
                    # 여기서 Java 백엔드로 신호 전송 가능
                    # await send_signal_to_java_backend(signal)
            
            # 실행 간격 대기
            await asyncio.sleep(config.execution_interval)
            
        except Exception as e:
            error_msg = f"전략 실행 오류: {str(e)}"
            strategy_info["errors"].append(error_msg)
            print(f"❌ [{strategy_name}] {error_msg}")
            
            # 오류가 너무 많이 발생하면 전략 중지
            if len(strategy_info["errors"]) > 10:
                strategy_info["status"] = "ERROR"
                break
            
            await asyncio.sleep(10)  # 오류 발생 시 10초 대기
    
    print(f"🛑 전략 '{strategy_name}' 백그라운드 실행 종료")


# === Java 백엔드 연동 함수 (추후 구현) ===

async def send_signal_to_java_backend(signal: TradingSignal):
    """Java 백엔드로 매매신호 전송"""
    # TODO: 구현 예정
    # HTTP POST to quantum-web-api/api/v1/trading/signals/receive
    pass