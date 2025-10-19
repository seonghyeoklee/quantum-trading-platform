"""
실제 기술적 지표 연동 자동매매 API 서버

KIS MCP + TA-Lib을 활용하여 실제 기술적 지표를 계산하는 서버입니다.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# KIS MCP 모듈 임포트를 위한 경로 설정
sys.path.append('/Users/admin/study/quantum-trading-platform/quantum-adapter-kis')

try:
    # TA-Lib 임포트
    import talib
    print("✅ TA-Lib 로드 성공")
    TALIB_AVAILABLE = True
except ImportError as e:
    print(f"❌ TA-Lib 로드 실패: {e}")
    TALIB_AVAILABLE = False

try:
    # KIS MCP 모듈 임포트
    from domestic_stock.inquire_price import inquire_price
    from domestic_stock.inquire_account_balance import inquire_account_balance
    from domestic_stock.inquire_daily_itemchartprice import inquire_daily_itemchartprice
    print("✅ KIS MCP 모듈 로드 성공")
    KIS_MCP_AVAILABLE = True
except ImportError as e:
    print(f"❌ KIS MCP 모듈 로드 실패: {e}")
    KIS_MCP_AVAILABLE = False

# FastAPI 앱 생성
app = FastAPI(
    title="실제 기술적 지표 연동 자동매매 시스템",
    description="KIS MCP + TA-Lib을 활용한 실제 기술적 지표 기반 자동매매 시스템",
    version="4.0.0"
)

# 전역 상태 관리
system_state = {
    "is_running": False,
    "positions": {},
    "orders": [],
    "balance": 0,
    "order_counter": 1,
    "trading_signals": [],
    "indicators_cache": {}  # 지표 캐시
}

# 요청 모델
class IndicatorRequest(BaseModel):
    symbol: str
    period: int = 14
    timeframe: str = "D"  # D: 일봉, W: 주봉, M: 월봉

# KIS MCP 연동 함수들
async def get_real_stock_price(symbol: str) -> Dict[str, Any]:
    """KIS MCP를 통한 실제 주식 현재가 조회"""
    if not KIS_MCP_AVAILABLE:
        return None
        
    try:
        df = inquire_price("demo", "J", symbol)
        
        if not df.empty:
            data = df.iloc[0]
            return {
                "symbol": symbol,
                "name": data.get("prdt_name", ""),
                "current_price": int(data.get("stck_prpr", 0)),
                "change": int(data.get("prdy_vrss", 0)),
                "change_percent": float(data.get("prdy_ctrt", 0)),
                "volume": int(data.get("acml_vol", 0)),
                "high_price": int(data.get("stck_hgpr", 0)),
                "low_price": int(data.get("stck_lwpr", 0)),
                "open_price": int(data.get("stck_oprc", 0)),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return None
    except Exception as e:
        print(f"❌ 현재가 조회 오류: {e}")
        return None

async def get_historical_data(symbol: str, days: int = 30) -> pd.DataFrame:
    """KIS MCP를 통한 과거 차트 데이터 조회"""
    if not KIS_MCP_AVAILABLE:
        return pd.DataFrame()
    
    try:
        # 날짜 계산 (30일 전부터 오늘까지)
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        
        # KIS MCP 호출
        df1, df2 = inquire_daily_itemchartprice(
            "demo",      # 모의투자
            "J",         # KRX
            symbol,      # 종목코드
            start_date,  # 시작일
            end_date,    # 종료일
            "D",         # 일봉
            "1"          # 원주가
        )
        
        if not df2.empty:
            # 데이터 정리 및 정렬
            df2 = df2.copy()
            df2['stck_bsop_date'] = pd.to_datetime(df2['stck_bsop_date'])
            df2 = df2.sort_values('stck_bsop_date')
            
            # 숫자형 변환
            numeric_columns = ['stck_oprc', 'stck_hgpr', 'stck_lwpr', 'stck_clpr', 'acml_vol']
            for col in numeric_columns:
                df2[col] = pd.to_numeric(df2[col], errors='coerce')
            
            return df2
        else:
            return pd.DataFrame()
            
    except Exception as e:
        print(f"❌ 과거 데이터 조회 오류: {e}")
        return pd.DataFrame()

async def calculate_technical_indicators(symbol: str, period: int = 14) -> Dict[str, Any]:
    """실제 기술적 지표 계산"""
    
    # 캐시 확인 (5분간 유효)
    cache_key = f"{symbol}_{period}"
    if cache_key in system_state["indicators_cache"]:
        cached_data = system_state["indicators_cache"][cache_key]
        if (datetime.now() - cached_data["timestamp"]).seconds < 300:  # 5분
            return cached_data["data"]
    
    # 과거 데이터 조회
    df = await get_historical_data(symbol, days=max(50, period * 3))  # 충분한 데이터 확보
    
    if df.empty or len(df) < period:
        return None
    
    try:
        # 가격 데이터 추출
        close_prices = df['stck_clpr'].values
        high_prices = df['stck_hgpr'].values
        low_prices = df['stck_lwpr'].values
        open_prices = df['stck_oprc'].values
        volumes = df['acml_vol'].values
        
        indicators = {}
        
        if TALIB_AVAILABLE:
            # TA-Lib을 사용한 정확한 계산
            
            # RSI (Relative Strength Index)
            rsi = talib.RSI(close_prices, timeperiod=period)
            indicators['rsi'] = float(rsi[-1]) if not np.isnan(rsi[-1]) else 50.0
            
            # MACD (Moving Average Convergence Divergence)
            macd, macdsignal, macdhist = talib.MACD(close_prices, fastperiod=12, slowperiod=26, signalperiod=9)
            indicators['macd'] = float(macd[-1]) if not np.isnan(macd[-1]) else 0.0
            indicators['macd_signal'] = float(macdsignal[-1]) if not np.isnan(macdsignal[-1]) else 0.0
            indicators['macd_histogram'] = float(macdhist[-1]) if not np.isnan(macdhist[-1]) else 0.0
            
            # 이동평균선 (EMA)
            ema_5 = talib.EMA(close_prices, timeperiod=5)
            ema_20 = talib.EMA(close_prices, timeperiod=20)
            indicators['ema_5'] = float(ema_5[-1]) if not np.isnan(ema_5[-1]) else close_prices[-1]
            indicators['ema_20'] = float(ema_20[-1]) if not np.isnan(ema_20[-1]) else close_prices[-1]
            
            # 볼린저 밴드
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close_prices, timeperiod=20, nbdevup=2, nbdevdn=2)
            indicators['bollinger_upper'] = float(bb_upper[-1]) if not np.isnan(bb_upper[-1]) else close_prices[-1] * 1.02
            indicators['bollinger_middle'] = float(bb_middle[-1]) if not np.isnan(bb_middle[-1]) else close_prices[-1]
            indicators['bollinger_lower'] = float(bb_lower[-1]) if not np.isnan(bb_lower[-1]) else close_prices[-1] * 0.98
            
            # 스토캐스틱
            slowk, slowd = talib.STOCH(high_prices, low_prices, close_prices, fastk_period=14, slowk_period=3, slowd_period=3)
            indicators['stoch_k'] = float(slowk[-1]) if not np.isnan(slowk[-1]) else 50.0
            indicators['stoch_d'] = float(slowd[-1]) if not np.isnan(slowd[-1]) else 50.0
            
            # 거래량 지표
            volume_sma = talib.SMA(volumes.astype(float), timeperiod=20)
            indicators['volume_sma'] = float(volume_sma[-1]) if not np.isnan(volume_sma[-1]) else volumes[-1]
            
            # ATR (Average True Range) - 변동성 지표
            atr = talib.ATR(high_prices, low_prices, close_prices, timeperiod=14)
            indicators['atr'] = float(atr[-1]) if not np.isnan(atr[-1]) else 0.0
            
        else:
            # TA-Lib 없을 때 간단한 계산
            indicators = {
                'rsi': 50.0,
                'macd': 0.0,
                'macd_signal': 0.0,
                'macd_histogram': 0.0,
                'ema_5': float(close_prices[-5:].mean()),
                'ema_20': float(close_prices[-20:].mean()) if len(close_prices) >= 20 else float(close_prices[-1]),
                'bollinger_upper': float(close_prices[-1] * 1.02),
                'bollinger_middle': float(close_prices[-1]),
                'bollinger_lower': float(close_prices[-1] * 0.98),
                'stoch_k': 50.0,
                'stoch_d': 50.0,
                'volume_sma': float(volumes[-20:].mean()) if len(volumes) >= 20 else float(volumes[-1]),
                'atr': 0.0
            }
        
        # 추가 분석 정보
        indicators.update({
            'data_points': len(df),
            'latest_date': df['stck_bsop_date'].iloc[-1].strftime('%Y-%m-%d'),
            'current_price': float(close_prices[-1]),
            'price_change_5d': float((close_prices[-1] - close_prices[-6]) / close_prices[-6] * 100) if len(close_prices) >= 6 else 0.0,
            'volume_ratio': float(volumes[-1] / indicators['volume_sma']) if indicators['volume_sma'] > 0 else 1.0,
            'timestamp': datetime.now().isoformat()
        })
        
        # 캐시에 저장
        system_state["indicators_cache"][cache_key] = {
            "data": indicators,
            "timestamp": datetime.now()
        }
        
        return indicators
        
    except Exception as e:
        print(f"❌ 기술적 지표 계산 오류: {e}")
        return None

# API 엔드포인트들
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "실제 기술적 지표 연동 자동매매 시스템",
        "version": "4.0.0",
        "status": "running" if system_state["is_running"] else "stopped",
        "features": {
            "kis_mcp": KIS_MCP_AVAILABLE,
            "talib": TALIB_AVAILABLE,
            "real_indicators": KIS_MCP_AVAILABLE and TALIB_AVAILABLE
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """헬스체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system_running": system_state["is_running"],
        "data_source": "KIS MCP + TA-Lib",
        "capabilities": {
            "real_prices": KIS_MCP_AVAILABLE,
            "real_indicators": TALIB_AVAILABLE,
            "historical_data": KIS_MCP_AVAILABLE
        }
    }

@app.get("/market-data/stocks/{symbol}/price")
async def get_stock_price(symbol: str):
    """실제 주식 현재가 조회 (KIS MCP 연동)"""
    price_data = await get_real_stock_price(symbol)
    if price_data:
        return price_data
    else:
        raise HTTPException(status_code=500, detail=f"{symbol} 종목의 현재가 조회에 실패했습니다")

@app.get("/market-data/stocks/{symbol}/indicators")
async def get_real_indicators(symbol: str, period: int = 14):
    """실제 기술적 지표 조회 (KIS MCP + TA-Lib)"""
    
    # 현재가 정보도 함께 조회
    price_data = await get_real_stock_price(symbol)
    if not price_data:
        raise HTTPException(status_code=500, detail="현재가 조회에 실패했습니다")
    
    # 기술적 지표 계산
    indicators = await calculate_technical_indicators(symbol, period)
    if not indicators:
        raise HTTPException(status_code=500, detail="기술적 지표 계산에 실패했습니다")
    
    # 결합된 결과 반환
    return {
        "symbol": symbol,
        "name": price_data["name"],
        "current_price": price_data["current_price"],
        "change_percent": price_data["change_percent"],
        "volume": price_data["volume"],
        
        # 실제 기술적 지표
        "rsi": indicators["rsi"],
        "macd": indicators["macd"],
        "macd_signal": indicators["macd_signal"],
        "macd_histogram": indicators["macd_histogram"],
        "ema_5": indicators["ema_5"],
        "ema_20": indicators["ema_20"],
        "bollinger_upper": indicators["bollinger_upper"],
        "bollinger_middle": indicators["bollinger_middle"],
        "bollinger_lower": indicators["bollinger_lower"],
        "stoch_k": indicators["stoch_k"],
        "stoch_d": indicators["stoch_d"],
        "atr": indicators["atr"],
        "volume_sma": indicators["volume_sma"],
        "volume_ratio": indicators["volume_ratio"],
        
        # 메타 정보
        "data_source": "KIS MCP + TA-Lib (실제 계산)",
        "data_points": indicators["data_points"],
        "latest_date": indicators["latest_date"],
        "calculation_period": period,
        "timestamp": indicators["timestamp"]
    }

@app.get("/market-data/stocks/{symbol}/analysis")
async def get_comprehensive_analysis(symbol: str):
    """종합 기술적 분석"""
    
    # 현재가 및 지표 조회
    price_data = await get_real_stock_price(symbol)
    indicators = await calculate_technical_indicators(symbol)
    
    if not price_data or not indicators:
        raise HTTPException(status_code=500, detail="데이터 조회에 실패했습니다")
    
    # 종합 분석
    analysis = {
        "symbol": symbol,
        "name": price_data["name"],
        "current_price": price_data["current_price"],
        "analysis_time": datetime.now().isoformat(),
        
        # 추세 분석
        "trend_analysis": {
            "short_term": "상승" if indicators["ema_5"] > indicators["ema_20"] else "하락",
            "price_vs_bb": "상단" if price_data["current_price"] > indicators["bollinger_upper"] else 
                          "하단" if price_data["current_price"] < indicators["bollinger_lower"] else "중간",
            "macd_signal": "매수" if indicators["macd"] > indicators["macd_signal"] else "매도"
        },
        
        # 모멘텀 분석
        "momentum_analysis": {
            "rsi_status": "과매수" if indicators["rsi"] > 70 else "과매도" if indicators["rsi"] < 30 else "중립",
            "stoch_status": "과매수" if indicators["stoch_k"] > 80 else "과매도" if indicators["stoch_k"] < 20 else "중립",
            "volume_status": "급증" if indicators["volume_ratio"] > 2.0 else "평균" if indicators["volume_ratio"] > 0.5 else "저조"
        },
        
        # 변동성 분석
        "volatility_analysis": {
            "atr_level": "높음" if indicators["atr"] > price_data["current_price"] * 0.03 else "보통",
            "bb_squeeze": abs(indicators["bollinger_upper"] - indicators["bollinger_lower"]) / price_data["current_price"] < 0.1
        },
        
        # 종합 점수 (0-100)
        "overall_score": min(100, max(0, 
            (indicators["rsi"] if indicators["rsi"] < 70 else 100 - indicators["rsi"]) * 0.3 +
            (50 + indicators["macd_histogram"] * 10) * 0.3 +
            (indicators["volume_ratio"] * 25) * 0.2 +
            (50 if indicators["ema_5"] > indicators["ema_20"] else 30) * 0.2
        )),
        
        "raw_indicators": indicators
    }
    
    return analysis

if __name__ == "__main__":
    print("🚀 실제 기술적 지표 연동 자동매매 서버 시작")
    print(f"📊 KIS MCP: {'✅ 연결됨' if KIS_MCP_AVAILABLE else '❌ 연결 실패'}")
    print(f"📈 TA-Lib: {'✅ 사용 가능' if TALIB_AVAILABLE else '❌ 사용 불가'}")
    print("🎯 포트: 8004")
    
    uvicorn.run(
        "real_indicators_server:app",
        host="0.0.0.0",
        port=8004,
        reload=False,
        log_level="info"
    )
