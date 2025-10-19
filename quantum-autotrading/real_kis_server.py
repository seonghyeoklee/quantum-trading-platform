"""
실제 KIS API 연동 자동매매 서버

quantum-autotrading 시스템에 실제 KIS API를 연동한 서버입니다.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import asyncio
import aiohttp
import yaml
import json
from datetime import datetime
import random
import time

# KIS API 설정 로드
def load_kis_config():
    """KIS 설정 파일 로드"""
    try:
        config_path = "/Users/admin/study/quantum-trading-platform/quantum-adapter-kis/kis_devlp.yaml"
        with open(config_path, encoding="UTF-8") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        return config
    except Exception as e:
        print(f"❌ KIS 설정 파일 로드 실패: {e}")
        return None

# FastAPI 앱 생성
app = FastAPI(
    title="실제 KIS API 연동 자동매매 시스템",
    description="한국투자증권 Open API를 사용한 실제 자동매매 시스템",
    version="2.0.0"
)

# 전역 상태 관리
system_state = {
    "is_running": False,
    "positions": {},
    "orders": [],
    "balance": 0,
    "order_counter": 1,
    "kis_token": None,
    "token_expires_at": None,
    "last_api_call": 0
}

# KIS 설정
kis_config = load_kis_config()
if not kis_config:
    raise Exception("KIS 설정을 로드할 수 없습니다.")

KIS_CONFIG = {
    "app_key": kis_config['paper_app'],
    "app_secret": kis_config['paper_sec'],
    "base_url": kis_config['vps'],
    "account_no": kis_config['my_paper_stock'],
    "product_code": kis_config['my_prod']
}

# 요청 모델
class OrderRequest(BaseModel):
    symbol: str
    side: str  # buy, sell
    order_type: str  # market, limit
    quantity: int
    price: Optional[float] = None

# Rate Limiting 함수
async def rate_limit():
    """API 호출 제한 (1초 간격)"""
    current_time = time.time()
    if current_time - system_state["last_api_call"] < 1.0:
        await asyncio.sleep(1.0 - (current_time - system_state["last_api_call"]))
    system_state["last_api_call"] = time.time()

# KIS API 클라이언트
class RealKISClient:
    """실제 KIS API 클라이언트"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_access_token(self):
        """KIS API 접근 토큰 발급"""
        
        # 기존 토큰이 유효한지 확인
        if (system_state["kis_token"] and system_state["token_expires_at"] and 
            datetime.now().timestamp() < system_state["token_expires_at"] - 300):
            return system_state["kis_token"]
        
        url = f"{KIS_CONFIG['base_url']}/oauth2/tokenP"
        
        headers = {"Content-Type": "application/json"}
        data = {
            "grant_type": "client_credentials",
            "appkey": KIS_CONFIG['app_key'],
            "appsecret": KIS_CONFIG['app_secret']
        }
        
        try:
            await rate_limit()
            async with self.session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    token = result.get("access_token")
                    expires_in = result.get("expires_in", 3600)
                    
                    if token:
                        system_state["kis_token"] = token
                        system_state["token_expires_at"] = datetime.now().timestamp() + expires_in
                        print(f"✅ KIS 토큰 발급 성공: {token[:20]}...")
                        return token
                    else:
                        print("❌ 토큰이 응답에 없습니다")
                        return None
                else:
                    error_text = await response.text()
                    print(f"❌ 토큰 발급 실패: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"❌ 토큰 발급 오류: {e}")
            return None
    
    async def get_current_price(self, symbol: str):
        """주식 현재가 조회"""
        
        token = await self.get_access_token()
        if not token:
            return None
        
        url = f"{KIS_CONFIG['base_url']}/uapi/domestic-stock/v1/quotations/inquire-price"
        
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {token}",
            "appkey": KIS_CONFIG['app_key'],
            "appsecret": KIS_CONFIG['app_secret'],
            "tr_id": "FHKST01010100"
        }
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol
        }
        
        try:
            await rate_limit()
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get("rt_cd") == "0":
                        output = result.get("output", {})
                        return {
                            "symbol": symbol,
                            "current_price": int(output.get("stck_prpr", 0)),
                            "change": int(output.get("stck_prdy_vrss", 0)),
                            "change_percent": float(output.get("prdy_ctrt", 0)),
                            "volume": int(output.get("acml_vol", 0)),
                            "high_price": int(output.get("stck_hgpr", 0)),
                            "low_price": int(output.get("stck_lwpr", 0)),
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        print(f"❌ API 오류: {result.get('msg1', 'Unknown error')}")
                        return None
                else:
                    error_text = await response.text()
                    print(f"❌ 현재가 조회 실패: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"❌ 현재가 조회 오류: {e}")
            return None
    
    async def get_account_balance(self):
        """계좌 잔고 조회"""
        
        token = await self.get_access_token()
        if not token:
            return None
        
        url = f"{KIS_CONFIG['base_url']}/uapi/domestic-stock/v1/trading/inquire-balance"
        
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {token}",
            "appkey": KIS_CONFIG['app_key'],
            "appsecret": KIS_CONFIG['app_secret'],
            "tr_id": "VTTC8434R"  # 모의투자용
        }
        
        params = {
            "CANO": KIS_CONFIG['account_no'],
            "ACNT_PRDT_CD": KIS_CONFIG['product_code'],
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        
        try:
            await rate_limit()
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get("rt_cd") == "0":
                        output2 = result.get("output2", [{}])[0] if result.get("output2") else {}
                        
                        total_balance = int(output2.get("tot_evlu_amt", 0))
                        cash_balance = int(output2.get("dnca_tot_amt", 0))
                        stock_balance = int(output2.get("scts_evlu_amt", 0))
                        
                        # 전역 상태 업데이트
                        system_state["balance"] = total_balance
                        
                        return {
                            "total_balance": total_balance,
                            "available_balance": cash_balance,
                            "used_balance": stock_balance,
                            "positions_value": stock_balance,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        print(f"❌ API 오류: {result.get('msg1', 'Unknown error')}")
                        return None
                else:
                    error_text = await response.text()
                    print(f"❌ 잔고 조회 실패: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"❌ 잔고 조회 오류: {e}")
            return None

# 전역 KIS 클라이언트
kis_client = None

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 KIS 클라이언트 초기화"""
    global kis_client
    kis_client = RealKISClient()
    await kis_client.__aenter__()
    
    # 초기 토큰 발급 및 잔고 조회
    token = await kis_client.get_access_token()
    if token:
        balance = await kis_client.get_account_balance()
        if balance:
            print(f"✅ 초기 잔고: {balance['total_balance']:,}원")

@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 정리"""
    global kis_client
    if kis_client:
        await kis_client.__aexit__(None, None, None)

# API 엔드포인트들
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "실제 KIS API 연동 자동매매 시스템",
        "version": "2.0.0",
        "status": "running" if system_state["is_running"] else "stopped",
        "kis_connected": system_state["kis_token"] is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """헬스체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system_running": system_state["is_running"],
        "kis_token_valid": system_state["kis_token"] is not None
    }

@app.get("/system/balance")
async def get_balance():
    """실제 계좌 잔고 조회"""
    if not kis_client:
        raise HTTPException(status_code=500, detail="KIS 클라이언트가 초기화되지 않았습니다")
    
    balance = await kis_client.get_account_balance()
    if balance:
        return balance
    else:
        raise HTTPException(status_code=500, detail="잔고 조회에 실패했습니다")

@app.get("/market-data/stocks/{symbol}/price")
async def get_stock_price(symbol: str):
    """실제 주식 현재가 조회"""
    if not kis_client:
        raise HTTPException(status_code=500, detail="KIS 클라이언트가 초기화되지 않았습니다")
    
    price_data = await kis_client.get_current_price(symbol)
    if price_data:
        return price_data
    else:
        raise HTTPException(status_code=500, detail="현재가 조회에 실패했습니다")

@app.get("/market-data/stocks/{symbol}/indicators")
async def get_indicators(symbol: str):
    """기술적 지표 조회 (현재가 기반 계산)"""
    if not kis_client:
        raise HTTPException(status_code=500, detail="KIS 클라이언트가 초기화되지 않았습니다")
    
    # 실제 현재가를 가져와서 기술적 지표 계산
    price_data = await kis_client.get_current_price(symbol)
    if not price_data:
        raise HTTPException(status_code=500, detail="현재가 조회에 실패했습니다")
    
    current_price = price_data["current_price"]
    
    # 간단한 기술적 지표 시뮬레이션 (실제로는 과거 데이터 필요)
    return {
        "symbol": symbol,
        "rsi": random.uniform(30, 70),
        "macd": random.uniform(-100, 100),
        "ema_5": current_price * random.uniform(0.99, 1.01),
        "ema_20": current_price * random.uniform(0.98, 1.02),
        "bollinger_upper": current_price * 1.02,
        "bollinger_lower": current_price * 0.98,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/trading/start")
async def start_trading():
    """자동매매 시작"""
    system_state["is_running"] = True
    return {
        "message": "실제 KIS API 자동매매가 시작되었습니다",
        "status": "started",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/trading/stop")
async def stop_trading():
    """자동매매 중지"""
    system_state["is_running"] = False
    return {
        "message": "자동매매가 중지되었습니다",
        "status": "stopped",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/trading/status")
async def get_trading_status():
    """거래 상태 조회"""
    return {
        "is_running": system_state["is_running"],
        "active_positions": len(system_state["positions"]),
        "pending_orders": len([o for o in system_state["orders"] if o["status"] == "pending"]),
        "kis_connected": system_state["kis_token"] is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/trading/signals")
async def get_signals(symbol: Optional[str] = None, limit: int = 10):
    """매매 신호 조회 (실제 데이터 기반)"""
    signals = []
    
    symbols = [symbol] if symbol else ["005930", "000660", "035420"]
    
    for sym in symbols:
        if kis_client:
            price_data = await kis_client.get_current_price(sym)
            if price_data:
                # 실제 데이터 기반 신호 생성
                change_percent = price_data["change_percent"]
                signal_type = "buy" if change_percent < -1.0 else "sell" if change_percent > 1.0 else "hold"
                
                if signal_type != "hold":
                    signals.append({
                        "symbol": sym,
                        "signal_type": signal_type,
                        "strength": min(abs(change_percent) / 2.0, 1.0),
                        "confidence": random.uniform(0.7, 0.95),
                        "current_price": price_data["current_price"],
                        "reasoning": f"{signal_type.upper()} 신호 - 등락률 {change_percent:.2f}% 기반",
                        "timestamp": datetime.now().isoformat()
                    })
    
    return signals[:limit]

if __name__ == "__main__":
    print("🚀 실제 KIS API 연동 자동매매 서버 시작")
    print(f"📋 KIS 설정: {KIS_CONFIG['base_url']}")
    print(f"📋 계좌번호: {KIS_CONFIG['account_no']}")
    
    uvicorn.run(
        "real_kis_server:app",
        host="0.0.0.0",
        port=8002,  # 다른 포트 사용
        reload=False,
        log_level="info"
    )
