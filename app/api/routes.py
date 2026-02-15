"""API 엔드포인트"""

import asyncio
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.config import StrategyConfig, load_settings
from app.dashboard import build_dashboard_html
from app.models import BacktestRequest, MarketType, detect_market_type
from typing import Literal
from app.trading.backtest import (
    fetch_chart_from_yfinance,
    run_backtest,
    run_bollinger_backtest,
    to_yfinance_ticker,
)
from app.trading.engine import TradingEngine

router = APIRouter()


def get_engine(request: Request) -> TradingEngine:
    """FastAPI 의존성 주입으로 엔진 인스턴스 획득"""
    engine: TradingEngine | None = getattr(request.app.state, "engine", None)
    if engine is None:
        raise HTTPException(status_code=503, detail="엔진이 초기화되지 않았습니다.")
    return engine


# --- 요청/응답 모델 ---


class StartRequest(BaseModel):
    symbols: list[str] | None = None
    market: Literal["domestic", "us"] | None = None  # None이면 symbols 기반 자동 판단


# --- 엔드포인트 ---


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """실시간 트레이딩 대시보드"""
    return build_dashboard_html()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/market/price/{symbol}")
async def get_price(symbol: str, engine: TradingEngine = Depends(get_engine)):
    try:
        if detect_market_type(symbol) == MarketType.US:
            exchange = engine.settings.trading.us_symbol_exchanges.get(symbol, "NAS")
            price = await engine.us_market.get_current_price(symbol, exchange)
        else:
            price = await engine.market.get_current_price(symbol)
        return price.model_dump()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/trading/start")
async def start_trading(req: StartRequest, engine: TradingEngine = Depends(get_engine)):
    status = engine.get_status()
    if status.status.value == "RUNNING":
        raise HTTPException(status_code=409, detail="이미 실행 중입니다.")
    market = MarketType(req.market) if req.market else None
    try:
        await engine.start(req.symbols, market=market)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    status = engine.get_status()
    return {
        "message": "자동매매 시작",
        "market": req.market or "all",
        "symbols": status.watch_symbols,
    }


@router.post("/trading/stop")
async def stop_trading(engine: TradingEngine = Depends(get_engine)):
    await engine.stop()
    return {"message": "자동매매 중지"}


@router.get("/trading/status")
async def trading_status(engine: TradingEngine = Depends(get_engine)):
    status = engine.get_status()
    return status.model_dump(mode="json")


@router.get("/trading/positions")
async def get_positions(engine: TradingEngine = Depends(get_engine)):
    try:
        positions, summary = await engine.order.get_balance()
        result = {
            "domestic": {
                "positions": [p.model_dump() for p in positions],
                "summary": summary.model_dump(),
            },
        }
        # 해외 잔고도 조회 시도
        try:
            us_positions, us_summary = await engine.us_order.get_balance()
            result["us"] = {
                "positions": [p.model_dump() for p in us_positions],
                "summary": us_summary.model_dump(),
            }
        except Exception:
            result["us"] = {"positions": [], "summary": {}}
        return result
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/trading/strategy")
async def get_strategy(engine: TradingEngine = Depends(get_engine)):
    """현재 전략 설정 조회"""
    return engine.get_strategy_config().model_dump()


@router.post("/trading/strategy")
async def update_strategy(
    config: StrategyConfig, engine: TradingEngine = Depends(get_engine)
):
    """전략 + 파라미터 변경 (재시작 불필요)"""
    engine.update_strategy(config)
    return {
        "message": "전략 설정 변경 완료",
        "strategy": engine.get_strategy_config().model_dump(),
    }


@router.post("/backtest")
async def run_backtest_api(req: BacktestRequest):
    """과거 데이터 기반 전략 백테스트"""
    settings = load_settings()

    end_date = req.end_date or datetime.now().strftime("%Y%m%d")
    ticker = to_yfinance_ticker(req.symbol)

    try:
        chart = await asyncio.to_thread(
            fetch_chart_from_yfinance, ticker, req.start_date, end_date
        )
    except ImportError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"yfinance 데이터 조회 실패: {e}")

    if not chart:
        raise HTTPException(status_code=404, detail="조회된 데이터가 없습니다.")

    if req.strategy_type == "bollinger":
        result = run_bollinger_backtest(
            chart=chart,
            initial_capital=req.initial_capital,
            order_amount=req.order_amount,
            period=req.bollinger_period,
            num_std=req.bollinger_num_std,
            max_holding_days=req.bollinger_max_holding_days,
            max_daily_trades=req.bollinger_max_daily_trades,
        )
    else:
        result = run_backtest(
            chart=chart,
            initial_capital=req.initial_capital,
            order_amount=req.order_amount,
            short_period=settings.trading.short_ma_period,
            long_period=settings.trading.long_ma_period,
            use_advanced=req.use_advanced_strategy,
            rsi_period=settings.trading.rsi_period,
            rsi_overbought=settings.trading.rsi_overbought,
            rsi_oversold=settings.trading.rsi_oversold,
            volume_ma_period=settings.trading.volume_ma_period,
            stop_loss_pct=req.stop_loss_pct,
            max_holding_days=req.max_holding_days,
        )

    return {
        "symbol": req.symbol,
        "period": f"{req.start_date} ~ {end_date}",
        "data_points": len(chart),
        "total_return_pct": result.total_return_pct,
        "buy_and_hold_pct": result.buy_and_hold_pct,
        "trade_count": result.trade_count,
        "win_rate": result.win_rate,
        "max_drawdown_pct": result.max_drawdown_pct,
        "sharpe_ratio": result.sharpe_ratio,
        "trades": [
            {"date": t.date, "side": t.side, "price": t.price, "quantity": t.quantity, "reason": t.reason}
            for t in result.trades
        ],
    }


# --- 저널 엔드포인트 ---


@router.get("/trading/journal")
async def list_journal_dates(engine: TradingEngine = Depends(get_engine)):
    """저널 날짜 목록 (내림차순)"""
    return {"dates": engine.journal.list_dates()}


@router.get("/trading/journal/{date_str}")
async def get_journal_events(
    date_str: str, engine: TradingEngine = Depends(get_engine)
):
    """특정 날짜 이벤트 조회"""
    try:
        d = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="날짜 형식: YYYY-MM-DD")
    events = engine.journal.read_events(d)
    return {"date": date_str, "count": len(events), "events": [e.model_dump(mode="json") for e in events]}


@router.get("/trading/journal/{date_str}/report")
async def get_journal_report(
    date_str: str, engine: TradingEngine = Depends(get_engine)
):
    """일일 리포트 HTML 반환"""
    try:
        d = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="날짜 형식: YYYY-MM-DD")
    path = engine.journal.generate_daily_report(d)
    with open(path, encoding="utf-8") as f:
        html = f.read()
    return HTMLResponse(content=html)
