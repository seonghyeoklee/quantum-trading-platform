"""키움 WebSocket 실시간 클라이언트

키움증권 실시간 시세 서버와의 WebSocket 연결을 관리하는 클라이언트
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Callable

import websockets
from websockets.exceptions import ConnectionClosed

# Handle both relative and absolute imports for different execution contexts
try:
    from ..config.settings import settings
    from ..auth.token_cache import token_cache
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from kiwoom_api.config.settings import settings
    from kiwoom_api.auth.token_cache import token_cache

logger = logging.getLogger(__name__)


class KiwoomWebSocketClient:
    """키움증권 실시간 WebSocket 클라이언트
    
    키움 WebSocket 프로토콜을 구현하여 실시간 시세 데이터를 수신
    LOGIN, REG, REMOVE, PING 메시지 처리
    """

    def __init__(self, uri: Optional[str] = None, access_token: Optional[str] = None):
        """WebSocket 클라이언트 초기화
        
        Args:
            uri: WebSocket 서버 URI (기본값: 설정에서 자동 선택)
            access_token: 인증 토큰 (기본값: 캐시에서 자동 로드)
        """
        self.uri = uri or self._get_websocket_url()
        self.access_token = access_token
        self.websocket = None
        self.connected = False
        self.keep_running = True
        self.message_handlers = {}
        
    def _get_websocket_url(self) -> str:
        """설정에 따른 WebSocket URL 반환"""
        return settings.kiwoom_websocket_url
        
    async def _get_access_token(self) -> str:
        """캐시된 토큰 또는 새 토큰 획득"""
        if self.access_token:
            return self.access_token
            
        # 캐시에서 토큰 조회
        cached_token = await token_cache.get_cached_token(settings.KIWOOM_APP_KEY)
        if cached_token and not cached_token.is_expired():
            return cached_token.token
            
        # 토큰이 없거나 만료된 경우 새로 발급 필요
        logger.error("유효한 액세스 토큰이 없습니다. 먼저 /api/fn_au10001을 호출하여 토큰을 발급받으세요.")
        raise ValueError("유효한 액세스 토큰이 필요합니다")

    async def connect(self) -> bool:
        """WebSocket 서버에 연결
        
        Returns:
            bool: 연결 성공 여부
        """
        try:
            logger.info(f"🔌 키움 WebSocket 서버에 연결 시도: {self.uri}")
            self.websocket = await websockets.connect(self.uri)
            self.connected = True
            
            # 토큰 획득
            access_token = await self._get_access_token()
            
            # 로그인 패킷 전송
            login_packet = {
                'trnm': 'LOGIN',
                'token': access_token
            }
            
            logger.info("🔑 실시간 시세 서버로 로그인 패킷 전송")
            await self.send_message(login_packet)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ WebSocket 연결 실패: {str(e)}")
            self.connected = False
            return False

    async def send_message(self, message: Dict[str, Any]) -> bool:
        """서버에 메시지 전송
        
        Args:
            message: 전송할 메시지 (딕셔너리)
            
        Returns:
            bool: 전송 성공 여부
        """
        if not self.connected:
            logger.warning("🔄 연결이 끊어져 재연결 시도")
            if not await self.connect():
                return False
                
        if self.connected and self.websocket:
            try:
                # JSON 직렬화
                message_str = json.dumps(message, ensure_ascii=False)
                await self.websocket.send(message_str)
                
                # PING이 아닌 경우만 로깅
                if message.get('trnm') != 'PING':
                    logger.info(f"📤 메시지 전송: {message_str}")
                    
                return True
                
            except Exception as e:
                logger.error(f"❌ 메시지 전송 실패: {str(e)}")
                return False
                
        return False

    async def receive_messages(self) -> None:
        """서버에서 메시지 수신 및 처리"""
        while self.keep_running and self.connected:
            try:
                # 서버로부터 메시지 수신
                message_str = await self.websocket.recv()
                response = json.loads(message_str)
                
                # 메시지 타입별 처리
                trnm = response.get('trnm')
                
                if trnm == 'LOGIN':
                    await self._handle_login_response(response)
                elif trnm == 'PING':
                    await self._handle_ping(response)
                elif trnm == 'REAL':
                    await self._handle_real_data(response)
                elif trnm in ['REG', 'REMOVE']:
                    await self._handle_registration_response(response)
                else:
                    logger.info(f"📥 알 수 없는 메시지 타입: {response}")
                    
                # 커스텀 핸들러 호출
                await self._call_message_handlers(trnm, response)
                    
            except ConnectionClosed:
                logger.warning("📡 서버에서 연결이 종료됨")
                self.connected = False
                break
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON 파싱 오류: {str(e)}")
            except Exception as e:
                logger.error(f"❌ 메시지 수신 오류: {str(e)}")

    async def _handle_login_response(self, response: Dict[str, Any]) -> None:
        """로그인 응답 처리"""
        return_code = response.get('return_code', -1)
        return_msg = response.get('return_msg', '')
        
        if return_code != 0:
            logger.error(f"❌ 로그인 실패: {return_msg}")
            await self.disconnect()
        else:
            logger.info("✅ 로그인 성공")

    async def _handle_ping(self, response: Dict[str, Any]) -> None:
        """PING 메시지 처리 (응답 필요)"""
        await self.send_message(response)

    async def _handle_real_data(self, response: Dict[str, Any]) -> None:
        """실시간 데이터 수신 처리"""
        logger.info(f"📊 실시간 데이터 수신: {json.dumps(response, ensure_ascii=False)}")

    async def _handle_registration_response(self, response: Dict[str, Any]) -> None:
        """등록/해지 응답 처리"""
        return_code = response.get('return_code', -1)
        return_msg = response.get('return_msg', '')
        trnm = response.get('trnm')
        
        if return_code == 0:
            logger.info(f"✅ {trnm} 성공: {return_msg}")
        else:
            logger.error(f"❌ {trnm} 실패: {return_msg}")

    async def _call_message_handlers(self, trnm: str, response: Dict[str, Any]) -> None:
        """등록된 메시지 핸들러 호출"""
        if trnm in self.message_handlers:
            try:
                await self.message_handlers[trnm](response)
            except Exception as e:
                logger.error(f"❌ 메시지 핸들러 오류 ({trnm}): {str(e)}")

    def add_message_handler(self, trnm: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """메시지 핸들러 등록
        
        Args:
            trnm: 메시지 타입 (LOGIN, REAL, REG, REMOVE, PING)
            handler: 핸들러 함수 (async)
        """
        self.message_handlers[trnm] = handler
        logger.info(f"📋 메시지 핸들러 등록: {trnm}")

    async def register_realtime(self, grp_no: str = "1", refresh: str = "1", 
                              items: list = None, types: list = None) -> bool:
        """실시간 데이터 등록
        
        Args:
            grp_no: 그룹번호 (기본값: "1")
            refresh: 기존등록유지여부 (기본값: "1")
            items: 실시간 등록 요소 리스트 (종목코드 등)
            types: 실시간 항목 리스트 (TR명)
            
        Returns:
            bool: 등록 요청 성공 여부
        """
        if items is None:
            items = [""]
        if types is None:
            types = ["00"]
            
        reg_message = {
            'trnm': 'REG',
            'grp_no': grp_no,
            'refresh': refresh,
            'data': [{
                'item': items,
                'type': types
            }]
        }
        
        logger.info(f"📝 실시간 데이터 등록: items={items}, types={types}")
        return await self.send_message(reg_message)

    async def remove_realtime(self, grp_no: str = "1", 
                            items: list = None, types: list = None) -> bool:
        """실시간 데이터 해지
        
        Args:
            grp_no: 그룹번호 (기본값: "1")
            items: 해지할 등록 요소 리스트
            types: 해지할 항목 리스트
            
        Returns:
            bool: 해지 요청 성공 여부
        """
        if items is None:
            items = [""]
        if types is None:
            types = ["00"]
            
        remove_message = {
            'trnm': 'REMOVE',
            'grp_no': grp_no,
            'data': [{
                'item': items,
                'type': types
            }]
        }
        
        logger.info(f"🗑️ 실시간 데이터 해지: items={items}, types={types}")
        return await self.send_message(remove_message)

    async def run(self) -> None:
        """WebSocket 클라이언트 실행 (연결 + 메시지 수신)"""
        if await self.connect():
            await self.receive_messages()

    async def disconnect(self) -> None:
        """WebSocket 연결 종료"""
        self.keep_running = False
        if self.connected and self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info("🔌 WebSocket 연결 종료")


# 전역 WebSocket 클라이언트 인스턴스 (싱글톤 패턴)
_websocket_client: Optional[KiwoomWebSocketClient] = None


async def get_websocket_client() -> KiwoomWebSocketClient:
    """전역 WebSocket 클라이언트 인스턴스 반환"""
    global _websocket_client
    if _websocket_client is None:
        _websocket_client = KiwoomWebSocketClient()
    return _websocket_client


async def ensure_websocket_connected() -> KiwoomWebSocketClient:
    """WebSocket 연결 확인 및 연결되지 않은 경우 연결"""
    client = await get_websocket_client()
    if not client.connected:
        await client.connect()
    return client