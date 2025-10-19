#!/usr/bin/env python3
"""
KIS API MCP 서버

한국투자증권 Open API를 MCP(Model Context Protocol)로 제공하는 서버입니다.
실제 KIS API와 연동하여 주식 데이터 및 매매 기능을 제공합니다.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from datetime import datetime
import aiohttp
import yaml

# MCP 관련 임포트
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kis-mcp-server")

# KIS API 설정 로드
def load_kis_config():
    """KIS 설정 파일 로드"""
    try:
        config_path = "/Users/admin/study/quantum-trading-platform/quantum-adapter-kis/kis_devlp.yaml"
        with open(config_path, encoding="UTF-8") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        return config
    except Exception as e:
        logger.error(f"KIS 설정 파일 로드 실패: {e}")
        return None

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

# 전역 상태
mcp_state = {
    "kis_token": None,
    "token_expires_at": None,
    "last_api_call": 0,
    "session": None
}

class KISMCPClient:
    """KIS API MCP 클라이언트"""
    
    def __init__(self):
        self.session = None
    
    async def initialize(self):
        """클라이언트 초기화"""
        self.session = aiohttp.ClientSession()
        await self.get_access_token()
        logger.info("✅ KIS MCP 클라이언트 초기화 완료")
    
    async def cleanup(self):
        """클라이언트 정리"""
        if self.session:
            await self.session.close()
    
    async def rate_limit(self):
        """API 호출 제한 (1초 간격)"""
        import time
        current_time = time.time()
        if current_time - mcp_state["last_api_call"] < 1.0:
            await asyncio.sleep(1.0 - (current_time - mcp_state["last_api_call"]))
        mcp_state["last_api_call"] = time.time()
    
    async def get_access_token(self):
        """KIS API 접근 토큰 발급"""
        
        # 기존 토큰이 유효한지 확인
        if (mcp_state["kis_token"] and mcp_state["token_expires_at"] and 
            datetime.now().timestamp() < mcp_state["token_expires_at"] - 300):
            return mcp_state["kis_token"]
        
        url = f"{KIS_CONFIG['base_url']}/oauth2/tokenP"
        
        headers = {"Content-Type": "application/json"}
        data = {
            "grant_type": "client_credentials",
            "appkey": KIS_CONFIG['app_key'],
            "appsecret": KIS_CONFIG['app_secret']
        }
        
        try:
            await self.rate_limit()
            async with self.session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    token = result.get("access_token")
                    expires_in = result.get("expires_in", 3600)
                    
                    if token:
                        mcp_state["kis_token"] = token
                        mcp_state["token_expires_at"] = datetime.now().timestamp() + expires_in
                        logger.info(f"✅ KIS 토큰 발급 성공: {token[:20]}...")
                        return token
                    else:
                        logger.error("❌ 토큰이 응답에 없습니다")
                        return None
                else:
                    error_text = await response.text()
                    logger.error(f"❌ 토큰 발급 실패: {response.status} - {error_text}")
                    return None
        except Exception as e:
            logger.error(f"❌ 토큰 발급 오류: {e}")
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
            await self.rate_limit()
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get("rt_cd") == "0":
                        output = result.get("output", {})
                        return {
                            "symbol": symbol,
                            "name": output.get("prdt_name", ""),
                            "current_price": int(output.get("stck_prpr", 0)),
                            "change": int(output.get("stck_prdy_vrss", 0)),
                            "change_percent": float(output.get("prdy_ctrt", 0)),
                            "volume": int(output.get("acml_vol", 0)),
                            "high_price": int(output.get("stck_hgpr", 0)),
                            "low_price": int(output.get("stck_lwpr", 0)),
                            "open_price": int(output.get("stck_oprc", 0)),
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        logger.error(f"❌ API 오류: {result.get('msg1', 'Unknown error')}")
                        return None
                else:
                    error_text = await response.text()
                    logger.error(f"❌ 현재가 조회 실패: {response.status} - {error_text}")
                    return None
        except Exception as e:
            logger.error(f"❌ 현재가 조회 오류: {e}")
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
            await self.rate_limit()
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get("rt_cd") == "0":
                        output1 = result.get("output1", [])
                        output2 = result.get("output2", [{}])[0] if result.get("output2") else {}
                        
                        # 보유 종목 정보
                        positions = []
                        for item in output1:
                            if int(item.get("hldg_qty", 0)) > 0:
                                positions.append({
                                    "symbol": item.get("pdno", ""),
                                    "name": item.get("prdt_name", ""),
                                    "quantity": int(item.get("hldg_qty", 0)),
                                    "avg_price": float(item.get("pchs_avg_pric", 0)),
                                    "current_price": float(item.get("prpr", 0)),
                                    "eval_amount": int(item.get("evlu_amt", 0)),
                                    "profit_loss": int(item.get("evlu_pfls_amt", 0)),
                                    "profit_loss_rate": float(item.get("evlu_pfls_rt", 0))
                                })
                        
                        # 계좌 요약 정보
                        total_balance = int(output2.get("tot_evlu_amt", 0))
                        cash_balance = int(output2.get("dnca_tot_amt", 0))
                        stock_balance = int(output2.get("scts_evlu_amt", 0))
                        
                        return {
                            "account_summary": {
                                "total_balance": total_balance,
                                "available_balance": cash_balance,
                                "stock_balance": stock_balance,
                                "profit_loss": int(output2.get("evlu_pfls_smtl_amt", 0)),
                                "profit_loss_rate": float(output2.get("tot_evlu_pfls_rt", 0))
                            },
                            "positions": positions,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        logger.error(f"❌ API 오류: {result.get('msg1', 'Unknown error')}")
                        return None
                else:
                    error_text = await response.text()
                    logger.error(f"❌ 잔고 조회 실패: {response.status} - {error_text}")
                    return None
        except Exception as e:
            logger.error(f"❌ 잔고 조회 오류: {e}")
            return None

# KIS 클라이언트 인스턴스
kis_client = KISMCPClient()

# MCP 서버 생성
server = Server("kis-api-server")

@server.list_resources()
async def handle_list_resources() -> List[Resource]:
    """사용 가능한 리소스 목록 반환"""
    return [
        Resource(
            uri="kis://account/balance",
            name="계좌 잔고 및 보유 종목",
            description="KIS API를 통한 실제 계좌 잔고 및 보유 종목 정보",
            mimeType="application/json"
        ),
        Resource(
            uri="kis://market/kospi",
            name="KOSPI 주요 종목",
            description="KOSPI 시장의 주요 종목 정보",
            mimeType="application/json"
        ),
        Resource(
            uri="kis://market/kosdaq",
            name="KOSDAQ 주요 종목",
            description="KOSDAQ 시장의 주요 종목 정보",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """리소스 내용 반환"""
    
    if uri == "kis://account/balance":
        balance_data = await kis_client.get_account_balance()
        if balance_data:
            return json.dumps(balance_data, ensure_ascii=False, indent=2)
        else:
            return json.dumps({"error": "계좌 정보를 가져올 수 없습니다"}, ensure_ascii=False)
    
    elif uri == "kis://market/kospi":
        # KOSPI 주요 종목 정보
        kospi_symbols = ["005930", "000660", "035420", "051910", "006400", "035720", "005380", "012330", "028260", "066570"]
        market_data = []
        
        for symbol in kospi_symbols:
            price_data = await kis_client.get_current_price(symbol)
            if price_data:
                market_data.append(price_data)
        
        return json.dumps({
            "market": "KOSPI",
            "timestamp": datetime.now().isoformat(),
            "stocks": market_data
        }, ensure_ascii=False, indent=2)
    
    elif uri == "kis://market/kosdaq":
        # KOSDAQ 주요 종목 정보
        kosdaq_symbols = ["247540", "091990", "263750", "086900", "196170", "357780", "039030", "145020", "112040", "041510"]
        market_data = []
        
        for symbol in kosdaq_symbols:
            price_data = await kis_client.get_current_price(symbol)
            if price_data:
                market_data.append(price_data)
        
        return json.dumps({
            "market": "KOSDAQ",
            "timestamp": datetime.now().isoformat(),
            "stocks": market_data
        }, ensure_ascii=False, indent=2)
    
    else:
        raise ValueError(f"알 수 없는 리소스: {uri}")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """사용 가능한 도구 목록 반환"""
    return [
        Tool(
            name="get_stock_price",
            description="특정 종목의 실시간 현재가 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "종목 코드 (예: 005930)"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_account_info",
            description="계좌 잔고 및 보유 종목 조회",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="analyze_market_trend",
            description="시장 동향 분석 (KOSPI/KOSDAQ 주요 종목)",
            inputSchema={
                "type": "object",
                "properties": {
                    "market": {
                        "type": "string",
                        "enum": ["KOSPI", "KOSDAQ", "ALL"],
                        "description": "분석할 시장 (KOSPI, KOSDAQ, ALL)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "분석할 종목 수 (기본값: 10)",
                        "default": 10
                    }
                },
                "required": ["market"]
            }
        ),
        Tool(
            name="get_trading_signals",
            description="매매 신호 분석 (기술적 분석 기반)",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "분석할 종목 코드 리스트"
                    },
                    "signal_type": {
                        "type": "string",
                        "enum": ["buy", "sell", "all"],
                        "description": "신호 타입 (buy, sell, all)",
                        "default": "all"
                    }
                },
                "required": ["symbols"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """도구 실행"""
    
    if name == "get_stock_price":
        symbol = arguments.get("symbol")
        if not symbol:
            return [TextContent(type="text", text="종목 코드가 필요합니다.")]
        
        price_data = await kis_client.get_current_price(symbol)
        if price_data:
            result = f"""📊 **{price_data['name']} ({symbol})** 실시간 시세

💹 **현재가**: {price_data['current_price']:,}원
📈 **등락**: {price_data['change']:+,}원 ({price_data['change_percent']:+.2f}%)
📊 **거래량**: {price_data['volume']:,}주
🔺 **고가**: {price_data['high_price']:,}원
🔻 **저가**: {price_data['low_price']:,}원
🏁 **시가**: {price_data['open_price']:,}원

⏰ 조회시간: {price_data['timestamp']}"""
            return [TextContent(type="text", text=result)]
        else:
            return [TextContent(type="text", text=f"❌ {symbol} 종목의 현재가를 조회할 수 없습니다.")]
    
    elif name == "get_account_info":
        balance_data = await kis_client.get_account_balance()
        if balance_data:
            account = balance_data['account_summary']
            positions = balance_data['positions']
            
            result = f"""💰 **계좌 현황**

📊 **계좌 요약**:
- 총 평가금액: {account['total_balance']:,}원
- 예수금: {account['available_balance']:,}원
- 주식 평가금액: {account['stock_balance']:,}원
- 평가손익: {account['profit_loss']:+,}원 ({account['profit_loss_rate']:+.2f}%)

📈 **보유 종목** ({len(positions)}개):"""
            
            for pos in positions:
                result += f"""
• **{pos['name']} ({pos['symbol']})**
  - 보유수량: {pos['quantity']:,}주
  - 평균단가: {pos['avg_price']:,.0f}원
  - 현재가: {pos['current_price']:,.0f}원
  - 평가금액: {pos['eval_amount']:,}원
  - 손익: {pos['profit_loss']:+,}원 ({pos['profit_loss_rate']:+.2f}%)"""
            
            if not positions:
                result += "\n  보유 종목이 없습니다."
            
            result += f"\n\n⏰ 조회시간: {balance_data['timestamp']}"
            return [TextContent(type="text", text=result)]
        else:
            return [TextContent(type="text", text="❌ 계좌 정보를 조회할 수 없습니다.")]
    
    elif name == "analyze_market_trend":
        market = arguments.get("market", "ALL")
        limit = arguments.get("limit", 10)
        
        if market in ["KOSPI", "ALL"]:
            kospi_symbols = ["005930", "000660", "035420", "051910", "006400"][:limit]
            kospi_data = []
            for symbol in kospi_symbols:
                price_data = await kis_client.get_current_price(symbol)
                if price_data:
                    kospi_data.append(price_data)
        
        if market in ["KOSDAQ", "ALL"]:
            kosdaq_symbols = ["247540", "091990", "263750", "086900", "196170"][:limit]
            kosdaq_data = []
            for symbol in kosdaq_symbols:
                price_data = await kis_client.get_current_price(symbol)
                if price_data:
                    kosdaq_data.append(price_data)
        
        result = f"📊 **시장 동향 분석** ({market})\n\n"
        
        if market in ["KOSPI", "ALL"] and 'kospi_data' in locals():
            result += "🏛️ **KOSPI 주요 종목**:\n"
            for stock in kospi_data:
                trend = "📈" if stock['change_percent'] > 0 else "📉" if stock['change_percent'] < 0 else "➡️"
                result += f"{trend} {stock['name']}: {stock['current_price']:,}원 ({stock['change_percent']:+.2f}%)\n"
            result += "\n"
        
        if market in ["KOSDAQ", "ALL"] and 'kosdaq_data' in locals():
            result += "🏢 **KOSDAQ 주요 종목**:\n"
            for stock in kosdaq_data:
                trend = "📈" if stock['change_percent'] > 0 else "📉" if stock['change_percent'] < 0 else "➡️"
                result += f"{trend} {stock['name']}: {stock['current_price']:,}원 ({stock['change_percent']:+.2f}%)\n"
        
        result += f"\n⏰ 분석시간: {datetime.now().isoformat()}"
        return [TextContent(type="text", text=result)]
    
    elif name == "get_trading_signals":
        symbols = arguments.get("symbols", [])
        signal_type = arguments.get("signal_type", "all")
        
        if not symbols:
            return [TextContent(type="text", text="분석할 종목 코드를 입력해주세요.")]
        
        result = f"🎯 **매매 신호 분석**\n\n"
        
        for symbol in symbols:
            price_data = await kis_client.get_current_price(symbol)
            if price_data:
                # 간단한 기술적 분석 신호 생성
                change_pct = price_data['change_percent']
                
                if change_pct <= -2.0:
                    signal = "🟢 강한 매수"
                    reason = "급락 후 반등 기대"
                elif change_pct <= -1.0:
                    signal = "🟡 매수 관심"
                    reason = "하락 후 매수 타이밍"
                elif change_pct >= 2.0:
                    signal = "🔴 매도 고려"
                    reason = "급등 후 차익실현"
                elif change_pct >= 1.0:
                    signal = "🟠 매도 관심"
                    reason = "상승 후 관망"
                else:
                    signal = "⚪ 관망"
                    reason = "횡보 구간"
                
                # 신호 타입 필터링
                if signal_type == "buy" and "매수" not in signal:
                    continue
                elif signal_type == "sell" and "매도" not in signal:
                    continue
                
                result += f"""📊 **{price_data['name']} ({symbol})**
💹 현재가: {price_data['current_price']:,}원 ({change_pct:+.2f}%)
🎯 신호: {signal}
💡 근거: {reason}

"""
        
        result += f"⏰ 분석시간: {datetime.now().isoformat()}"
        return [TextContent(type="text", text=result)]
    
    else:
        return [TextContent(type="text", text=f"알 수 없는 도구: {name}")]

async def main():
    """메인 함수"""
    # KIS 클라이언트 초기화
    await kis_client.initialize()
    
    # MCP 서버 실행
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="kis-api-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("MCP 서버가 중단되었습니다.")
    finally:
        # 정리 작업
        asyncio.run(kis_client.cleanup())
