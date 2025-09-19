"""
국내주식 실시간 WebSocket 데이터 제공자
KIS WebSocket API를 통한 국내주식 실시간 데이터 수집
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
from datetime import datetime
from typing import Optional, Dict, List, Callable
from queue import Queue
from threading import Lock

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from domestic_trading_system.core.domestic_data_types import (
    DomesticMarketData, MarketType, TradingSession, TradingHours, DEFAULT_MARKETS
)


class DomesticRealtimeWebSocketProvider:
    """WebSocket 기반 실시간 국내주식 데이터 제공자"""

    def __init__(self, kis_appkey: str, kis_appsecret: str, environment: str = "prod"):
        self.logger = logging.getLogger("domestic_realtime_websocket")

        # KIS API 설정
        self.kis_appkey = kis_appkey
        self.kis_appsecret = kis_appsecret
        self.environment = environment

        # WebSocket 설정
        if environment == "prod":
            self.ws_url = 'ws://ops.koreainvestment.com:21000'  # 실전투자
        elif environment == "vps":
            self.ws_url = 'ws://ops.koreainvestment.com:31000'  # 모의투자
        else:
            raise ValueError("Environment must be 'prod' or 'vps'")

        # 연결 상태
        self.websocket = None
        self.is_connected = False
        self.approval_key = None

        # 실시간 데이터 관리
        self.market_data_callbacks = {}  # symbol -> callback function
        self.latest_market_data = {}     # symbol -> DomesticMarketData
        self.data_lock = Lock()

        # 거래시간 관리
        self.trading_hours = TradingHours()
        self.market_map = DEFAULT_MARKETS

    async def initialize(self):
        """WebSocket 연결 초기화"""
        try:
            # KIS 승인키 발급
            self.approval_key = self._get_approval_key(self.kis_appkey, self.kis_appsecret)
            self.logger.info(f"KIS 승인키 발급 완료: {self.approval_key[:20]}...")

            # WebSocket 연결
            await self.connect()

            self.logger.info("국내주식 실시간 WebSocket 연결 초기화 완료")
            return True

        except Exception as e:
            self.logger.error(f"WebSocket 초기화 실패: {e}")
            return False

    def _get_approval_key(self, appkey: str, appsecret: str) -> str:
        """WebSocket 접속키 발급"""
        try:
            if self.environment == "prod":
                url = 'https://openapi.koreainvestment.com:9443'  # 실전투자
            else:
                url = 'https://openapivts.koreainvestment.com:29443'  # 모의투자

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

            market_type = self.market_map.get(symbol, MarketType.KOSPI)

            # 국내주식 실시간 체결가 구독 (H0STCNT0)
            subscribe_message = {
                "header": {
                    "approval_key": self.approval_key,
                    "custtype": "P",
                    "tr_type": "1",
                    "content-type": "utf-8"
                },
                "body": {
                    "input": {
                        "tr_id": "H0STCNT0",     # 국내주식 체결가 TR
                        "tr_key": symbol         # 종목코드 (6자리)
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
                        "tr_id": "H0STCNT0",
                        "tr_key": symbol
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

            if tr_id == "H0STCNT0":  # 국내주식 체결가
                data_cnt = int(recv_data[2])
                raw_data = recv_data[3]

                # 체결 데이터 파싱
                await self._parse_domestic_stock_data(data_cnt, raw_data)

        except Exception as e:
            self.logger.error(f"실시간 데이터 처리 오류: {e}")

    async def _parse_domestic_stock_data(self, data_cnt: int, raw_data: str):
        """국내주식 체결 데이터 파싱"""
        try:
            # 국내주식 실시간 체결가 데이터 필드 정의
            fields = [
                "유가증권단축종목코드", "주식체결시간", "주식현재가", "전일대비부호", "전일대비",
                "전일대비율", "가중평균주식가격", "주식시가", "주식최고가", "주식최저가",
                "매도호가1", "매수호가1", "체결거래량", "누적거래량", "누적거래대금",
                "매도체결건수", "매수체결건수", "순매수체결건수", "체결강도", "총매도수량",
                "총매수수량", "체결구분", "매수비율", "전일거래량대비등락율", "시가시간",
                "시가대비구분", "시가대비", "최고가시간", "고가대비구분", "고가대비",
                "최저가시간", "저가대비구분", "저가대비", "영업일자", "신장개장구분코드",
                "거래정지여부", "매도호가잔량", "매수호가잔량", "총매도호가잔량", "총매수호가잔량",
                "거래량회전율", "전일동시간누적거래량", "전일동시간누적거래량비율", "시간구분코드",
                "임의종료구분코드", "정적VI발동기준가"
            ]

            values = raw_data.split('^')

            # 필드별 데이터 매핑
            data_dict = {}
            for i, field in enumerate(fields):
                if i < len(values):
                    data_dict[field] = values[i]

            # 종목코드 추출
            symbol = data_dict.get("유가증권단축종목코드", "").strip()
            if not symbol:
                return

            # 시장 구분 확인
            market_type = self.market_map.get(symbol, MarketType.KOSPI)

            # 거래 세션 확인
            trading_session = self.trading_hours.get_current_session()

            # DomesticMarketData 생성
            market_data = DomesticMarketData(
                symbol=symbol,
                market_type=market_type,
                timestamp=datetime.now(),
                current_price=float(data_dict.get("주식현재가", 0)),
                open_price=float(data_dict.get("주식시가", 0)),
                high_price=float(data_dict.get("주식최고가", 0)),
                low_price=float(data_dict.get("주식최저가", 0)),
                previous_close=float(data_dict.get("주식현재가", 0)) - float(data_dict.get("전일대비", 0)),
                volume=int(data_dict.get("누적거래량", 0)),
                volume_turnover=float(data_dict.get("누적거래대금", 0)),
                change=float(data_dict.get("전일대비", 0)),
                change_percent=float(data_dict.get("전일대비율", 0)),
                change_sign=data_dict.get("전일대비부호", "2"),
                bid_price=float(data_dict.get("매수호가1", 0)),
                ask_price=float(data_dict.get("매도호가1", 0)),
                bid_volume=int(data_dict.get("매수호가잔량", 0)),
                ask_volume=int(data_dict.get("매도호가잔량", 0)),
                trading_session=trading_session,
                raw_data=data_dict
            )

            # 데이터 캐시 업데이트
            with self.data_lock:
                self.latest_market_data[symbol] = market_data

            # 콜백 호출
            if symbol in self.market_data_callbacks:
                callback = self.market_data_callbacks[symbol]
                if callback:
                    await callback(market_data)

            self.logger.debug(f"실시간 데이터 업데이트: {symbol} {market_data.current_price:,}원")

        except Exception as e:
            self.logger.error(f"데이터 파싱 오류: {e}")
            self.logger.error(f"Raw data: {raw_data}")

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

    async def get_realtime_price(self, symbol: str) -> Optional[DomesticMarketData]:
        """실시간 주식 가격 조회 (캐시된 데이터)"""
        with self.data_lock:
            return self.latest_market_data.get(symbol)

    def get_trading_session(self) -> TradingSession:
        """현재 거래 세션 확인"""
        return self.trading_hours.get_current_session()

    def is_market_open(self) -> bool:
        """시장 개장 여부"""
        return self.trading_hours.is_market_open()

    async def health_check(self) -> bool:
        """WebSocket 연결 상태 확인"""
        return self.is_connected and self.websocket is not None

    def get_subscribed_symbols(self) -> List[str]:
        """구독 중인 종목 리스트"""
        return list(self.market_data_callbacks.keys())

    async def get_all_latest_data(self) -> Dict[str, DomesticMarketData]:
        """모든 구독 종목의 최신 데이터"""
        with self.data_lock:
            return self.latest_market_data.copy()


# 테스트 함수
async def test_domestic_realtime_websocket():
    """국내주식 실시간 WebSocket 데이터 제공자 테스트"""
    print("=== 실시간 국내주식 WebSocket 데이터 테스트 ===")

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
    provider = DomesticRealtimeWebSocketProvider(appkey, appsecret, "prod")

    # 삼성전자 실시간 데이터 콜백
    async def samsung_callback(market_data: DomesticMarketData):
        print(f"📱 삼성전자 실시간: {market_data.current_price:,}원 "
              f"({market_data.change_percent:+.2f}%) "
              f"{market_data.get_change_arrow()}")

    try:
        # 초기화
        await provider.initialize()

        # 삼성전자 구독
        await provider.subscribe_stock("005930", samsung_callback)

        print("✅ 삼성전자 실시간 데이터 구독 시작")
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

    asyncio.run(test_domestic_realtime_websocket())