"""
실시간 WebSocket 해외주식 데이터 제공자
KIS WebSocket API를 통한 실시간 해외주식 데이터 수집
환율 정보, 거래시간 관리 포함
"""

import asyncio
import logging
import sys
import os
import json
import time
import websockets
import traceback
import requests
from datetime import datetime, timezone
from typing import Optional, Dict, List, Callable
from queue import Queue
from threading import Lock

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from overseas_trading_system.core.overseas_data_types import (
    OverseasMarketData, ExchangeRate, ExchangeType, TradingSession,
    TradingHours, DEFAULT_EXCHANGES, TRADING_HOURS_MAP
)


class RealtimeWebSocketProvider:
    """WebSocket 기반 실시간 해외주식 데이터 제공자"""

    def __init__(self, kis_appkey: str, kis_appsecret: str, environment: str = "prod"):
        self.logger = logging.getLogger("realtime_websocket_provider")

        # KIS API 설정
        self.kis_appkey = kis_appkey
        self.kis_appsecret = kis_appsecret
        self.environment = environment  # "prod" 실전투자만 지원

        # WebSocket 설정
        if environment == "prod":
            self.ws_url = 'ws://ops.koreainvestment.com:21000'  # 실전투자
        else:
            raise ValueError("Only 'prod' environment is supported for real trading")

        # 연결 상태
        self.websocket = None
        self.is_connected = False
        self.approval_key = None

        # 실시간 데이터 관리
        self.market_data_callbacks = {}  # symbol -> callback function
        self.latest_market_data = {}  # symbol -> OverseasMarketData
        self.data_lock = Lock()

        # 환율 관리
        self.exchange_rate_cache: Optional[ExchangeRate] = None
        self.rate_update_interval = 60  # 1분마다 환율 업데이트

        # 거래소 및 시간 설정
        self.exchange_map = DEFAULT_EXCHANGES
        self.trading_hours = TRADING_HOURS_MAP

    async def initialize(self):
        """WebSocket 연결 초기화"""
        try:
            # KIS 승인키 발급
            self.approval_key = self._get_approval_key(self.kis_appkey, self.kis_appsecret)
            self.logger.info(f"KIS 승인키 발급 완료: {self.approval_key[:20]}...")

            # WebSocket 연결
            await self.connect()

            self.logger.info("실시간 WebSocket 연결 초기화 완료")
            return True

        except Exception as e:
            self.logger.error(f"WebSocket 초기화 실패: {e}")
            return False

    def _get_approval_key(self, appkey: str, appsecret: str) -> str:
        """WebSocket 접속키 발급"""
        try:
            url = 'https://openapi.koreainvestment.com:9443'  # 실전투자계좌
            headers = {"content-type": "application/json"}
            body = {
                "grant_type": "client_credentials",
                "appkey": appkey,
                "secretkey": appsecret
            }
            path = "oauth2/Approval"
            api_url = f"{url}/{path}"

            time.sleep(0.05)
            response = requests.post(api_url, headers=headers, data=json.dumps(body))

            if response.status_code == 200:
                approval_key = response.json()["approval_key"]
                return approval_key
            else:
                raise Exception(f"승인키 발급 실패: {response.status_code} {response.text}")

        except Exception as e:
            self.logger.error(f"승인키 발급 오류: {e}")
            raise

    async def connect(self):
        """WebSocket 서버에 연결"""
        try:
            self.websocket = await websockets.connect(self.ws_url, ping_interval=None)
            self.is_connected = True
            self.logger.info(f"WebSocket 연결 성공: {self.ws_url}")

            # 메시지 수신 태스크 시작
            asyncio.create_task(self._message_handler())

        except Exception as e:
            self.logger.error(f"WebSocket 연결 실패: {e}")
            self.is_connected = False
            raise

    async def disconnect(self):
        """WebSocket 연결 해제"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            self.logger.info("WebSocket 연결 해제")

    async def subscribe_stock(self, symbol: str, callback: Callable = None):
        """종목 실시간 구독"""
        try:
            if not self.is_connected:
                await self.connect()

            exchange = self.exchange_map.get(symbol, ExchangeType.NAS)

            # 미국 주식 실시간 체결가 구독 (HDFSCNT0)
            subscribe_message = {
                "header": {
                    "approval_key": self.approval_key,
                    "custtype": "P",
                    "tr_type": "1",
                    "content-type": "utf-8"
                },
                "body": {
                    "input": {
                        "tr_id": "HDFSCNT0",  # 해외주식 체결가 TR
                        "tr_key": f"DNAS{symbol}"  # 미국 종목 (D=실시간, NAS=나스닥, AAPL=종목코드)
                    }
                }
            }

            # 콜백 등록
            if callback:
                self.market_data_callbacks[symbol] = callback

            # 구독 메시지 전송
            await self.websocket.send(json.dumps(subscribe_message))
            await asyncio.sleep(0.5)

            self.logger.info(f"종목 구독 완료: {symbol}")

        except Exception as e:
            self.logger.error(f"종목 구독 실패 [{symbol}]: {e}")

    async def unsubscribe_stock(self, symbol: str):
        """종목 구독 해제"""
        try:
            # 구독 해제 메시지 (tr_type = "2")
            unsubscribe_message = {
                "header": {
                    "approval_key": self.approval_key,
                    "custtype": "P",
                    "tr_type": "2",
                    "content-type": "utf-8"
                },
                "body": {
                    "input": {
                        "tr_id": "HDFSCNT0",
                        "tr_key": f"DNAS{symbol}"
                    }
                }
            }

            await self.websocket.send(json.dumps(unsubscribe_message))

            # 콜백 제거
            if symbol in self.market_data_callbacks:
                del self.market_data_callbacks[symbol]

            # 캐시된 데이터 제거
            with self.data_lock:
                if symbol in self.latest_market_data:
                    del self.latest_market_data[symbol]

            self.logger.info(f"종목 구독 해제: {symbol}")

        except Exception as e:
            self.logger.error(f"종목 구독 해제 실패 [{symbol}]: {e}")

    async def _message_handler(self):
        """WebSocket 메시지 처리기"""
        try:
            while self.is_connected:
                data = await self.websocket.recv()

                # 실시간 데이터 처리
                if data[0] == '0':  # 실시간 데이터
                    await self._process_realtime_data(data)

                elif data[0] == '1':  # 체결통보 (현재는 사용 안함)
                    pass

                else:  # JSON 응답 (구독 확인, 에러 등)
                    await self._process_json_response(data)

        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("WebSocket 연결이 종료됨")
            self.is_connected = False
        except Exception as e:
            self.logger.error(f"메시지 처리 오류: {e}")
            self.logger.error(traceback.format_exc())

    async def _process_realtime_data(self, data: str):
        """실시간 데이터 처리"""
        try:
            recv_data = data.split('|')
            tr_id = recv_data[1]

            if tr_id == "HDFSCNT0":  # 해외주식 체결가
                data_cnt = int(recv_data[2])
                raw_data = recv_data[3]

                # 체결 데이터 파싱
                await self._parse_overseas_stock_data(data_cnt, raw_data)

        except Exception as e:
            self.logger.error(f"실시간 데이터 처리 오류: {e}")

    async def _parse_overseas_stock_data(self, data_cnt: int, raw_data: str):
        """해외주식 체결 데이터 파싱"""
        try:
            # 데이터 필드 정의
            fields = [
                "실시간종목코드", "종목코드", "수수점자리수", "현지영업일자", "현지일자", "현지시간",
                "한국일자", "한국시간", "시가", "고가", "저가", "현재가", "대비구분", "전일대비",
                "등락율", "매수호가", "매도호가", "매수잔량", "매도잔량", "체결량", "거래량",
                "거래대금", "매도체결량", "매수체결량", "체결강도", "시장구분"
            ]

            values = raw_data.split('^')

            # 필드별 데이터 매핑
            data_dict = {}
            for i, field in enumerate(fields):
                if i < len(values):
                    data_dict[field] = values[i]

            # 종목코드 추출
            symbol = data_dict.get("종목코드", "").strip()
            if not symbol:
                return

            # 환율 정보 가져오기
            exchange_rate = await self.get_exchange_rate()

            # OverseasMarketData 생성
            market_data = OverseasMarketData(
                symbol=symbol,
                exchange=self.exchange_map.get(symbol, ExchangeType.NAS),
                timestamp=datetime.now(),
                current_price=float(data_dict.get("현재가", 0)),
                open_price=float(data_dict.get("시가", 0)),
                high_price=float(data_dict.get("고가", 0)),
                low_price=float(data_dict.get("저가", 0)),
                previous_close=float(data_dict.get("현재가", 0)) - float(data_dict.get("전일대비", 0)),
                volume=int(data_dict.get("거래량", 0)),
                change=float(data_dict.get("전일대비", 0)),
                change_percent=float(data_dict.get("등락율", 0)),
                trading_session=self.get_trading_session(self.exchange_map.get(symbol, ExchangeType.NAS)),
                exchange_rate=exchange_rate
            )

            # 데이터 캐시 업데이트
            with self.data_lock:
                self.latest_market_data[symbol] = market_data

            # 콜백 호출
            if symbol in self.market_data_callbacks:
                callback = self.market_data_callbacks[symbol]
                if callback:
                    await callback(market_data)

            self.logger.debug(f"실시간 데이터 업데이트: {symbol} ${market_data.current_price:.2f}")

        except Exception as e:
            self.logger.error(f"데이터 파싱 오류: {e}")

    async def _process_json_response(self, data: str):
        """JSON 응답 처리 (구독 확인, 에러 등)"""
        try:
            json_obj = json.loads(data)
            tr_id = json_obj.get("header", {}).get("tr_id", "")

            if tr_id != "PINGPONG":
                rt_cd = json_obj.get("body", {}).get("rt_cd", "")
                msg = json_obj.get("body", {}).get("msg1", "")

                if rt_cd == '1':  # 에러
                    if msg != 'ALREADY IN SUBSCRIBE':
                        self.logger.error(f"API 에러 [{tr_id}]: {msg}")
                elif rt_cd == '0':  # 정상
                    self.logger.info(f"구독 성공 [{tr_id}]: {msg}")

            elif tr_id == "PINGPONG":
                # PING/PONG 응답
                await self.websocket.pong(data)
                self.logger.debug("PINGPONG 응답 전송")

        except json.JSONDecodeError:
            self.logger.error(f"JSON 파싱 실패: {data}")
        except Exception as e:
            self.logger.error(f"JSON 응답 처리 오류: {e}")

    async def get_realtime_price(self, symbol: str) -> Optional[OverseasMarketData]:
        """실시간 주식 가격 조회 (캐시된 데이터)"""
        with self.data_lock:
            return self.latest_market_data.get(symbol)

    async def get_exchange_rate(self, force_update: bool = False) -> Optional[ExchangeRate]:
        """USD/KRW 환율 조회 (캐시 지원)"""
        try:
            # 캐시된 환율이 있고 강제 업데이트가 아닌 경우
            if not force_update and self.exchange_rate_cache:
                cache_age = (datetime.now() - self.exchange_rate_cache.timestamp).seconds
                if cache_age < self.rate_update_interval:
                    return self.exchange_rate_cache

            # 실제 환율 API 호출 (임시로 고정 환율 사용)
            # TODO: KIS API 환율 조회 엔드포인트 연동
            current_rate = 1310.0  # USD/KRW 임시 환율

            exchange_rate = ExchangeRate(
                base_currency="USD",
                quote_currency="KRW",
                rate=current_rate,
                timestamp=datetime.now()
            )

            self.exchange_rate_cache = exchange_rate
            self.logger.debug(f"환율 업데이트: 1 USD = {current_rate} KRW")

            return exchange_rate

        except Exception as e:
            self.logger.error(f"환율 조회 오류: {e}")
            # 기본 환율 반환
            return ExchangeRate(rate=1300.0, timestamp=datetime.now())

    def get_trading_session(self, exchange: ExchangeType) -> TradingSession:
        """현재 거래 세션 확인"""
        trading_hours = self.trading_hours.get(exchange, TradingHours(exchange))
        return trading_hours.get_current_session()

    def is_market_open(self, exchange: ExchangeType) -> bool:
        """시장 개장 여부"""
        session = self.get_trading_session(exchange)
        return session in [TradingSession.PRE_MARKET, TradingSession.REGULAR, TradingSession.AFTER_HOURS]

    async def health_check(self) -> bool:
        """WebSocket 연결 상태 확인"""
        return self.is_connected and self.websocket is not None

    def get_subscribed_symbols(self) -> List[str]:
        """구독 중인 종목 리스트"""
        return list(self.market_data_callbacks.keys())

    async def get_all_latest_data(self) -> Dict[str, OverseasMarketData]:
        """모든 구독 종목의 최신 데이터"""
        with self.data_lock:
            return self.latest_market_data.copy()


# 테스트 함수
async def test_realtime_websocket():
    """실시간 WebSocket 데이터 제공자 테스트"""
    print("=== 실시간 WebSocket 해외주식 데이터 테스트 ===")

    # 설정 파일에서 API 키 로드
    import yaml
    try:
        with open('/Users/admin/KIS/config/kis_devlp.yaml', 'r') as f:
            config = yaml.safe_load(f)
            appkey = config['my_app']
            appsecret = config['my_sec']
    except Exception as e:
        print(f"설정 파일 로드 실패: {e}")
        return

    # WebSocket 데이터 제공자 초기화
    provider = RealtimeWebSocketProvider(appkey, appsecret, "prod")

    # Tesla 실시간 데이터 콜백
    async def tesla_callback(market_data: OverseasMarketData):
        print(f"🚗 TESLA 실시간: ${market_data.current_price:.2f} "
              f"({market_data.change_percent:+.2f}%) "
              f"₩{market_data.get_price_krw():,.0f}")

    try:
        # 초기화
        await provider.initialize()

        # Tesla 구독
        await provider.subscribe_stock("TSLA", tesla_callback)

        print("✅ Tesla 실시간 데이터 구독 시작")
        print("Ctrl+C로 종료...")

        # 30초간 실시간 데이터 수신
        await asyncio.sleep(30)

    except KeyboardInterrupt:
        print("\n⏹️  테스트 중단")
    finally:
        await provider.disconnect()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(test_realtime_websocket())