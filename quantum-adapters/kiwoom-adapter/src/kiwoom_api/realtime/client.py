#!/usr/bin/env python3
"""
키움증권 실시간 WebSocket 클라이언트

18가지 실시간 데이터 타입 지원 + TR 명령어 처리
- 기존: REAL 메시지로 실시간 시세 데이터 수신
- 신규: TR 메시지로 조건검색 명령어 처리 (CNSRLST, CNSRREQ, CNSRCLR)
"""

import asyncio
import json
import logging
import websockets
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import traceback

# Handle both relative and absolute imports
try:
    from ..auth.oauth_client import KiwoomOAuthClient
    from ..config.settings import settings
    from .models.realtime_data import RealtimeData, RealtimeResponse
    from .models.tr_data import TRRequest, TRResponse
    from .handlers.tr_handlers import TRHandlerRegistry
    from ..events.kafka_publisher import get_kafka_publisher
    from ..events.realtime_transformer import RealtimeEventTransformer
except ImportError:
    from kiwoom_api.auth.oauth_client import KiwoomOAuthClient
    from kiwoom_api.config.settings import settings
    from kiwoom_api.realtime.models.realtime_data import RealtimeData, RealtimeResponse
    from kiwoom_api.realtime.models.tr_data import TRRequest, TRResponse
    from kiwoom_api.realtime.handlers.tr_handlers import TRHandlerRegistry
    from kiwoom_api.events.kafka_publisher import get_kafka_publisher
    from kiwoom_api.events.realtime_transformer import RealtimeEventTransformer

logger = logging.getLogger(__name__)


class RealtimeClient:
    """키움증권 실시간 WebSocket 클라이언트

    기능:
    1. 18가지 실시간 시세 데이터 수신 (기존 기능)
    2. 조건검색 TR 명령어 처리 (신규 기능)
        - CNSRLST: 조건검색 목록조회
        - CNSRREQ: 조건검색 실행 (일반/실시간)
        - CNSRCLR: 조건검색 실시간 해제
    """

    def __init__(self, uri: str, enable_kafka: bool = None, skip_login: bool = False):
        self.uri = uri
        self.websocket = None
        self.access_token = None
        self.connected = False
        # enable_kafka가 None이면 설정 파일의 값 사용
        self.enable_kafka = enable_kafka if enable_kafka is not None else settings.ENABLE_KAFKA
        self.skip_login = skip_login  # 로그인 스킵 옵션 (개발/테스트용)

        # OAuth 클라이언트 초기화
        self.oauth_client = KiwoomOAuthClient(
            app_key=settings.get_app_key(),
            app_secret=settings.get_app_secret(),
            sandbox_mode=settings.KIWOOM_SANDBOX_MODE
        )

        # 실시간 데이터 구독 관리
        self.subscriptions = {}  # {symbol: [types]}
        self.subscription_groups = {}  # 구독 그룹 관리

        # TR 핸들러 시스템 초기화
        self.tr_handlers = TRHandlerRegistry()

        # 콜백 시스템
        self.connection_callbacks = []
        self.message_callbacks = []
        self.tr_callbacks = []

        # Kafka 이벤트 시스템 초기화
        self.kafka_publisher = None
        self.event_transformer = RealtimeEventTransformer()

        logger.info(f"RealtimeClient 초기화 완료 - 실시간 데이터 + TR 명령어 지원 (Kafka: {enable_kafka})")

    def add_connection_callback(self, callback: Callable[[bool], None]):
        """연결 상태 변경 콜백 등록"""
        self.connection_callbacks.append(callback)

    def add_message_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """실시간 메시지 콜백 등록"""
        self.message_callbacks.append(callback)

    def add_tr_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """TR 응답 콜백 등록"""
        self.tr_callbacks.append(callback)

    async def get_access_token(self) -> Optional[str]:
        """액세스 토큰 획득"""
        try:
            logger.info("액세스 토큰 요청 중...")
            token_response = await self.oauth_client.request_token()
            
            # TokenResponse에서 실제 토큰 추출
            if token_response.return_code == 0:  # 정수 0으로 비교
                self.access_token = token_response.token
                logger.info("액세스 토큰 획득 성공")
                return token_response.token
            else:
                logger.error(f"토큰 발급 실패: {token_response.return_msg}")
                return None
                
        except Exception as e:
            logger.error(f"액세스 토큰 획득 실패: {e}")
            return None

    async def connect(self) -> bool:
        """WebSocket 서버에 연결"""
        try:
            # 로그인 스킵 모드가 아닌 경우에만 토큰 획득
            if not self.skip_login:
                # 액세스 토큰 획득
                if not self.access_token:
                    token = await self.get_access_token()
                    if not token:
                        logger.error("액세스 토큰이 없어 연결 불가")
                        return False

            # Kafka Publisher 초기화 (WebSocket 연결 전)
            if self.enable_kafka:
                try:
                    self.kafka_publisher = await get_kafka_publisher()
                    logger.info("✅ Kafka Publisher 초기화 완료")
                except Exception as e:
                    logger.warning(f"⚠️ Kafka Publisher 초기화 실패: {e}")
                    # Kafka 실패해도 WebSocket은 계속 진행
                    self.enable_kafka = False

            logger.info(f"WebSocket 서버 연결 중: {self.uri}")

            # WebSocket 연결
            self.websocket = await websockets.connect(self.uri)

            # 로그인 스킵 모드인 경우 로그인 과정 생략
            if self.skip_login:
                logger.info("🔧 로그인 스킵 모드 - 개발/테스트용")
                self.connected = True
                logger.info("✅ WebSocket 연결 성공! (로그인 스킵)")
                return True

            # 로그인 메시지 전송
            login_message = {
                "trnm": "LOGIN",
                "token": self.access_token
            }

            await self.websocket.send(json.dumps(login_message))
            logger.info("로그인 메시지 전송 완료")

            # 로그인 응답 대기
            response = await self.websocket.recv()
            login_response = json.loads(response)

            if login_response.get("return_code") == 0:
                self.connected = True
                logger.info("WebSocket 로그인 성공")

                # 연결 콜백 호출
                for callback in self.connection_callbacks:
                    try:
                        callback(True)
                    except Exception as e:
                        logger.error(f"연결 콜백 실행 실패: {e}")

                return True
            else:
                logger.error(f"WebSocket 로그인 실패: {login_response}")
                return False

        except Exception as e:
            logger.error(f"WebSocket 연결 실패: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """WebSocket 연결 종료"""
        try:
            if self.websocket:
                await self.websocket.close()
                self.connected = False
                logger.info("WebSocket 연결 종료")

                # 연결 콜백 호출
                for callback in self.connection_callbacks:
                    try:
                        callback(False)
                    except Exception as e:
                        logger.error(f"연결 해제 콜백 실행 실패: {e}")

        except Exception as e:
            logger.error(f"연결 종료 중 오류: {e}")

    async def send_message(self, message: Dict[str, Any]) -> bool:
        """서버에 메시지 전송"""
        try:
            if not self.connected or not self.websocket:
                logger.error("연결되지 않은 상태에서 메시지 전송 시도")
                return False

            message_json = json.dumps(message, ensure_ascii=False)
            await self.websocket.send(message_json)
            logger.debug(f"메시지 전송: {message.get('trnm', 'UNKNOWN')}")
            return True

        except Exception as e:
            logger.error(f"메시지 전송 실패: {e}")
            return False

    # ============== 실시간 데이터 구독 관리 (기존 기능) ==============

    async def subscribe(self, symbols: List[str], types: List[str] = None, refresh: str = "0") -> bool:
        """실시간 시세 구독 (키움 공식 REG 메시지 형식)

        Args:
            symbols: 종목 코드 리스트
            types: 실시간 타입 리스트 (기본값: ['0B'])
            refresh: 기존등록유지여부 ("0": 기존해지, "1": 기존유지)
        """
        if not types:
            types = ['0B']  # 기본: 주식체결

        try:
            # 키움 공식 REG 메시지 형식
            message = {
                "trnm": "REG",          # 서비스명
                "grp_no": "1",          # 그룹번호
                "refresh": refresh,     # 기존등록유지여부
                "data": [{
                    "item": symbols,    # 실시간 등록 종목 리스트
                    "type": types,      # 실시간 항목 리스트
                }]
            }
            
            success = await self.send_message(message)
            if success:
                # 구독 정보 저장 (전체 종목에 대해)
                for symbol in symbols:
                    if symbol not in self.subscriptions:
                        self.subscriptions[symbol] = []
                    for rt_type in types:
                        if rt_type not in self.subscriptions[symbol]:
                            self.subscriptions[symbol].append(rt_type)

                logger.info(f"✅ 실시간 구독 성공: {symbols} - {types}")
                return True
            else:
                logger.error(f"❌ 실시간 구독 실패: 메시지 전송 오류")
                return False

        except Exception as e:
            logger.error(f"실시간 구독 실패: {e}")
            return False

    async def unsubscribe(self, symbols: List[str], types: List[str] = None) -> bool:
        """실시간 시세 구독 해지"""
        if not types:
            types = self.subscriptions.get(symbols[0], []) if symbols else []

        try:
            for symbol in symbols:
                for rt_type in types:
                    message = {
                        "trnm": "UNREG",
                        "data": [{"symbol": symbol, "type": rt_type}]
                    }

                    success = await self.send_message(message)
                    if success and symbol in self.subscriptions:
                        if rt_type in self.subscriptions[symbol]:
                            self.subscriptions[symbol].remove(rt_type)
                        if not self.subscriptions[symbol]:
                            del self.subscriptions[symbol]

                        logger.info(f"실시간 구독 해지: {symbol} - {rt_type}")
                        await asyncio.sleep(0.1)

            return True

        except Exception as e:
            logger.error(f"실시간 구독 해지 실패: {e}")
            return False

    # ============== TR 명령어 처리 (신규 기능) ==============

    async def send_tr_request(self, tr_name: str, data: Dict[str, Any]) -> bool:
        """TR 요청 전송

        Args:
            tr_name: TR 명 (CNSRLST, CNSRREQ, CNSRCLR)
            data: TR 요청 데이터
        """
        try:
            # 로그인 상태 확인
            if not self.is_authenticated():
                logger.error(f"TR 요청 실패 ({tr_name}): 로그인 상태가 아닙니다")
                return False

            tr_message = {
                "trnm": tr_name,
                **data
            }

            logger.info(f"TR 요청 전송: {tr_name} (인증 상태: 정상)")
            success = await self.send_message(tr_message)

            if success:
                logger.debug(f"TR 요청 성공: {tr_name}")
            else:
                logger.warning(f"TR 요청 전송 실패: {tr_name}")

            return success

        except Exception as e:
            logger.error(f"TR 요청 실패 ({tr_name}): {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """로그인 및 인증 상태 확인"""
        if self.skip_login:
            # 스킵 로그인 모드에서는 연결만 확인
            return self.connected
        else:
            # 일반 모드에서는 연결 + 토큰 모두 확인
            return self.connected and bool(self.access_token)

    async def get_screener_list(self) -> Dict[str, Any]:
        """조건검색 목록조회 (CNSRLST)"""
        success = await self.send_tr_request("CNSRLST", {})
        if success:
            logger.info("조건검색 목록조회 요청 전송")
        return {"success": success, "tr_name": "CNSRLST"}

    async def execute_screener_search(self, seq: str, search_type: str = "0",
                                    stex_tp: str = "K") -> Dict[str, Any]:
        """조건검색 실행 (CNSRREQ)

        Args:
            seq: 조건식 일련번호
            search_type: 조회타입 (0:일반, 1:실시간포함)
            stex_tp: 거래소구분 (K:KRX)
        """
        data = {
            "seq": seq,
            "search_type": search_type,
            "stex_tp": stex_tp,
            "cont_yn": "N",
            "next_key": ""
        }

        success = await self.send_tr_request("CNSRREQ", data)
        if success:
            mode = "실시간포함" if search_type == "1" else "일반"
            logger.info(f"조건검색 실행 요청 전송: seq={seq}, 모드={mode}")

        return {"success": success, "tr_name": "CNSRREQ", "seq": seq, "search_type": search_type}

    async def clear_screener_realtime(self, seq: str) -> Dict[str, Any]:
        """조건검색 실시간 해제 (CNSRCLR)

        Args:
            seq: 조건식 일련번호
        """
        data = {"seq": seq}

        success = await self.send_tr_request("CNSRCLR", data)
        if success:
            logger.info(f"조건검색 실시간 해제 요청 전송: seq={seq}")

        return {"success": success, "tr_name": "CNSRCLR", "seq": seq}

    # ============== 메시지 수신 및 처리 ==============

    async def receive_messages(self):
        """서버에서 오는 메시지 수신 및 처리"""
        try:
            logger.info("메시지 수신 시작")

            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._process_message(data)

                except json.JSONDecodeError:
                    logger.warning(f"잘못된 JSON 메시지: {message[:100]}...")
                except Exception as e:
                    logger.error(f"메시지 처리 중 오류: {e}")
                    logger.error(traceback.format_exc())

        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket 연결이 종료됨")
            self.connected = False
        except Exception as e:
            logger.error(f"메시지 수신 중 오류: {e}")
            self.connected = False

    async def _process_message(self, data: Dict[str, Any]):
        """수신된 메시지 처리"""
        try:
            trnm = data.get('trnm', '')

            # Kafka 이벤트 발행 (모든 메시지 대상)
            if self.enable_kafka and self.kafka_publisher:
                await self._publish_websocket_events(data)

            # TR 응답 처리
            if trnm in ['CNSRLST', 'CNSRREQ', 'CNSRCLR']:
                await self._process_tr_response(data)

            # 실시간 데이터 처리
            elif trnm == 'REAL':
                await self._process_realtime_data(data)

            # PING/PONG 처리 (키움 서버는 PONG을 지원하지 않음)
            elif trnm == 'PING':
                # 키움 서버는 PONG 응답을 지원하지 않으므로 응답하지 않음
                logger.debug("PING 수신 - PONG 응답 비활성화 (키움 서버 미지원)")

            # 기타 메시지
            else:
                logger.debug(f"기타 메시지 수신: {trnm}")
                # 메시지 콜백 호출
                for callback in self.message_callbacks:
                    try:
                        callback(data)
                    except Exception as e:
                        logger.error(f"메시지 콜백 실행 실패: {e}")

        except Exception as e:
            logger.error(f"메시지 처리 실패: {e}")

    async def _process_tr_response(self, data: Dict[str, Any]):
        """TR 응답 처리"""
        try:
            tr_name = data.get('trnm')

            # TR 핸들러를 통한 처리
            if self.tr_handlers.has_tr_handler(tr_name):
                # 요청 데이터는 임시로 빈 딕셔너리 사용 (실제로는 요청 추적 시스템 필요)
                request_data = {}
                result = await self.tr_handlers.handle_tr_response(tr_name, request_data, data)

                if result:
                    logger.info(f"TR 응답 처리 완료: {tr_name}")

                    # TR 콜백 호출
                    for callback in self.tr_callbacks:
                        try:
                            callback(tr_name, result)
                        except Exception as e:
                            logger.error(f"TR 콜백 실행 실패: {e}")
                else:
                    logger.warning(f"TR 응답 처리 결과 없음: {tr_name}")
            else:
                logger.warning(f"지원하지 않는 TR: {tr_name}")

        except Exception as e:
            logger.error(f"TR 응답 처리 실패: {e}")

    async def _process_realtime_data(self, data: Dict[str, Any]):
        """실시간 데이터 처리"""
        try:
            # 조건검색 실시간 알림 확인
            realtime_data = RealtimeData(
                symbol="",  # 실제 데이터에서 추출 필요
                type="",    # 실제 데이터에서 추출 필요
                values=data.get('data', [{}])[0].get('values', {}) if data.get('data') else {}
            )

            # 조건검색 실시간 알림 처리
            screener_result = await self.tr_handlers.handle_screener_realtime(realtime_data)
            if screener_result:
                logger.info(f"조건검색 실시간 알림: {screener_result['condition_seq']} - {screener_result['stock_code']} ({screener_result['action_description']})")

                # TR 콜백으로 전달
                for callback in self.tr_callbacks:
                    try:
                        callback("SCREENER_REALTIME", screener_result)
                    except Exception as e:
                        logger.error(f"조건검색 실시간 콜백 실행 실패: {e}")
            else:
                # 일반 실시간 데이터 처리
                logger.debug(f"일반 실시간 데이터 수신")

                # 메시지 콜백 호출
                for callback in self.message_callbacks:
                    try:
                        callback(data)
                    except Exception as e:
                        logger.error(f"실시간 메시지 콜백 실행 실패: {e}")

        except Exception as e:
            logger.error(f"실시간 데이터 처리 실패: {e}")

    # ============== 상태 관리 및 통계 ==============

    def get_subscription_statistics(self) -> Dict[str, int]:
        """구독 통계 반환"""
        total_symbols = len(self.subscriptions)
        total_types = sum(len(types) for types in self.subscriptions.values())
        total_groups = len(self.subscription_groups)

        return {
            "total_symbols": total_symbols,
            "total_types": total_types,
            "total_groups": total_groups,
            "connected": self.connected
        }

    def get_tr_statistics(self) -> Dict[str, Any]:
        """TR 처리 통계 반환"""
        return {
            "supported_trs": self.tr_handlers.get_supported_trs(),
            "tr_handler_count": len(self.tr_handlers.tr_handlers),
            "realtime_handler_count": len(self.tr_handlers.realtime_handlers)
        }

    async def run(self):
        """WebSocket 실행 (연결 + 메시지 수신)"""
        try:
            # 연결
            if await self.connect():
                logger.info("✅ WebSocket 연결 성공")
                logger.info(f"📊 지원 기능: 실시간 데이터 18종 + TR 명령어 {len(self.tr_handlers.get_supported_trs())}개")

                # 메시지 수신 시작
                await self.receive_messages()
            else:
                logger.error("❌ WebSocket 연결 실패")

        except KeyboardInterrupt:
            logger.info("사용자에 의해 중단됨")
        except Exception as e:
            logger.error(f"실행 중 오류: {e}")
        finally:
            await self.disconnect()

    # ============== Kafka 이벤트 발행 기능 ==============
    
    async def _publish_websocket_events(self, ws_data: Dict[str, Any]):
        """WebSocket 메시지를 Kafka 이벤트로 발행"""
        try:
            if not self.kafka_publisher:
                return
                
            # WebSocket 메시지를 이벤트로 변환
            events = await self.event_transformer.transform_websocket_message(ws_data)
            
            if not events:
                return
                
            # 배치로 이벤트 발행
            success_count = 0
            for event_data in events:
                try:
                    success = await self.kafka_publisher.publish_event(event_data)
                    if success:
                        success_count += 1
                except Exception as e:
                    logger.error(f"개별 이벤트 발행 실패: {e}")
                    
            if success_count > 0:
                logger.debug(f"📤 Kafka 이벤트 발행 성공: {success_count}개")
                
        except Exception as e:
            logger.error(f"Kafka 이벤트 발행 중 오류: {e}")
            
    async def get_kafka_status(self) -> Dict[str, Any]:
        """Kafka 연동 상태 정보 반환"""
        status = {
            'kafka_enabled': self.enable_kafka,
            'kafka_connected': False,
            'kafka_publisher': None
        }
        
        if self.kafka_publisher:
            try:
                kafka_info = await self.kafka_publisher.get_connection_info()
                status.update({
                    'kafka_connected': kafka_info.get('is_connected', False),
                    'kafka_publisher': kafka_info
                })
            except Exception as e:
                logger.error(f"Kafka 상태 조회 실패: {e}")
                
        return status
