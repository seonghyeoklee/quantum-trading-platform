from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime, date
from contextlib import asynccontextmanager

from app.services.database import DatabaseService
from app.services.technical_analysis import TechnicalAnalysisService
from app.models.candle import StockCandle

# 전역 데이터베이스 서비스 인스턴스
db_service = DatabaseService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작시 데이터베이스 초기화
    await db_service.initialize()
    yield
    # 종료시 연결 해제
    await db_service.close()

app = FastAPI(
    title="Quantum Trading Analysis API", 
    version="1.0.0",
    description="주식 차트 분석 및 기술적 지표 API",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PriceData(BaseModel):
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

class TechnicalIndicators(BaseModel):
    symbol: str
    timeframe: str
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    stoch_k: Optional[float] = None
    stoch_d: Optional[float] = None

class TradingSignal(BaseModel):
    symbol: str
    timeframe: str
    timestamp: datetime
    overall_signal: str  # strong_buy, buy, hold, sell, strong_sell
    signals: Dict[str, str]  # 개별 지표별 신호
    confidence: float
    analysis: Dict[str, Any]
    reason: str

@app.get("/")
def read_root():
    return {"message": "Quantum Trading Analysis Service"}

# 차트 데이터 조회 API
@app.get("/api/v1/stocks/{symbol}/candles", response_model=List[StockCandle])
async def get_stock_candles(
    symbol: str,
    timeframe: str = Query("1d", description="시간 단위 (1m, 5m, 15m, 30m, 1h, 1d)"),
    start_date: Optional[datetime] = Query(None, description="시작일시"),
    end_date: Optional[datetime] = Query(None, description="종료일시"),
    limit: int = Query(1000, ge=1, le=5000, description="최대 개수")
):
    """주식 캔들 데이터 조회"""
    try:
        candles = await db_service.get_stock_candles(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        return candles
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 조회 실패: {str(e)}")

@app.get("/api/v1/stocks/{symbol}/technical-analysis", response_model=Dict[str, Any])
async def get_technical_analysis(
    symbol: str,
    timeframe: str = Query("1d", description="시간 단위"),
    period_days: int = Query(100, ge=50, le=1000, description="분석 기간 (일)")
):
    """종합 기술적 분석"""
    try:
        # 데이터 조회
        df = await db_service.get_candles_as_dataframe(
            symbol=symbol,
            timeframe=timeframe,
            limit=period_days
        )
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"데이터를 찾을 수 없습니다: {symbol}")
        
        if len(df) < 50:
            raise HTTPException(status_code=400, detail="분석을 위한 데이터가 부족합니다 (최소 50개 필요)")
        
        # 종합 기술적 분석 실행
        analysis = TechnicalAnalysisService.comprehensive_analysis(df)
        analysis['symbol'] = symbol
        analysis['timeframe'] = timeframe
        analysis['data_points'] = len(df)
        analysis['last_updated'] = df.index[-1].isoformat()
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)}")

@app.get("/api/v1/stocks/{symbol}/signals", response_model=TradingSignal)
async def get_trading_signals(
    symbol: str,
    timeframe: str = Query("1d", description="시간 단위"),
    period_days: int = Query(100, ge=50, le=1000, description="분석 기간")
):
    """매매 신호 생성"""
    try:
        # 기술적 분석 실행
        analysis_result = await get_technical_analysis(symbol, timeframe, period_days)
        
        # 신호 추출
        signals = analysis_result.get('signals', {})
        overall_signal = signals.get('overall', 'hold')
        
        # TechnicalIndicators 객체 생성
        indicators = TechnicalIndicators(
            symbol=symbol,
            timeframe=timeframe,
            sma_20=analysis_result.get('sma_20'),
            sma_50=analysis_result.get('sma_50'),
            ema_12=analysis_result.get('ema_12'),
            ema_26=analysis_result.get('ema_26'),
            rsi=analysis_result.get('rsi'),
            macd=analysis_result.get('macd'),
            macd_signal=analysis_result.get('macd_signal'),
            macd_histogram=analysis_result.get('macd_histogram'),
            bb_upper=analysis_result.get('bb_upper'),
            bb_middle=analysis_result.get('bb_middle'),
            bb_lower=analysis_result.get('bb_lower'),
            stoch_k=analysis_result.get('stoch_k'),
            stoch_d=analysis_result.get('stoch_d')
        )
        
        # 신뢰도 계산
        bullish_count = sum(1 for sig in signals.values() if 'bullish' in sig or 'oversold' in sig)
        bearish_count = sum(1 for sig in signals.values() if 'bearish' in sig or 'overbought' in sig)
        total_signals = len(signals) - 1  # overall 제외
        
        if bullish_count > bearish_count:
            confidence = bullish_count / total_signals if total_signals > 0 else 0.5
        elif bearish_count > bullish_count:
            confidence = bearish_count / total_signals if total_signals > 0 else 0.5
        else:
            confidence = 0.5
        
        # 신호 설명 생성
        reason_parts = []
        for indicator, signal in signals.items():
            if indicator != 'overall' and signal != 'neutral':
                reason_parts.append(f"{indicator}: {signal}")
        
        reason = "; ".join(reason_parts) if reason_parts else "No clear signals"
        
        return TradingSignal(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=datetime.now(),
            overall_signal=overall_signal,
            signals=signals,
            confidence=round(confidence, 3),
            analysis=analysis_result,
            reason=reason
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"신호 생성 실패: {str(e)}")

@app.get("/api/v1/market/overview")
async def get_market_overview(
    timeframe: str = Query("1d", description="시간 단위"),
    top_n: int = Query(20, ge=5, le=100, description="상위 N개 종목")
):
    """시장 개요 (거래량 상위 종목)"""
    try:
        overview_df = await db_service.get_market_overview(timeframe=timeframe, top_n=top_n)
        return overview_df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시장 개요 조회 실패: {str(e)}")

@app.get("/api/v1/stocks/symbols")
async def get_available_symbols(timeframe: str = Query("1d", description="시간 단위")):
    """사용 가능한 종목 코드 목록"""
    try:
        symbols = await db_service.get_available_symbols(timeframe=timeframe)
        return {"symbols": symbols, "count": len(symbols)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"종목 목록 조회 실패: {str(e)}")

# 레거시 API (하위 호환성)
@app.post("/analyze/technical", response_model=TechnicalIndicators)
async def analyze_technical_legacy(price_data: List[PriceData]):
    """기술적 지표 분석 (레거시)"""
    if len(price_data) < 50:
        raise HTTPException(status_code=400, detail="Need at least 50 data points for analysis")
    
    # DataFrame 변환
    df = TechnicalAnalysisService.candles_to_dataframe([
        StockCandle(
            symbol=p.symbol,
            timeframe="1d",  # 기본값
            timestamp=p.timestamp,
            open_price=p.open,
            high_price=p.high,
            low_price=p.low,
            close_price=p.close,
            volume=p.volume
        ) for p in price_data
    ])
    
    # 종합 분석
    analysis = TechnicalAnalysisService.comprehensive_analysis(df)
    
    return TechnicalIndicators(
        symbol=price_data[0].symbol,
        timeframe="1d",
        sma_20=analysis.get('sma_20'),
        sma_50=analysis.get('sma_50'),
        ema_12=analysis.get('ema_12'),
        ema_26=analysis.get('ema_26'),
        rsi=analysis.get('rsi'),
        macd=analysis.get('macd'),
        macd_signal=analysis.get('macd_signal'),
        macd_histogram=analysis.get('macd_histogram'),
        bb_upper=analysis.get('bb_upper'),
        bb_middle=analysis.get('bb_middle'),
        bb_lower=analysis.get('bb_lower'),
        stoch_k=analysis.get('stoch_k'),
        stoch_d=analysis.get('stoch_d')
    )

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}