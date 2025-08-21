"""
키움 실시간 WebSocket 클라이언트
"""
import asyncio
import json
import logging
import websockets
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from enum import Enum

try:
    from ..models.websocket import (
        WebSocketLoginRequest,
        WebSocketRegisterRequest,
        WebSocketRemoveRequest,
        WebSocketResponse,
        WebSocketRealtimeDataItem,
        REALTIME_TYPE_CODES
    )
    from ..config.settings import settings
except ImportError:
    from kiwoom_api.models.websocket import (
        WebSocketLoginRequest,
        WebSocketRegisterRequest,
        WebSocketRemoveRequest,
        WebSocketResponse,
        WebSocketRealtimeDataItem,
        REALTIME_TYPE_CODES
    )
    from kiwoom_api.config.settings import settings


logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """WebSocket 연결 상태"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    ERROR = "error"


class KiwoomWebSocketClient:
    """키움증권 WebSocket 실시간 데이터 클라이언트"""
    
    def __init__(self, access_token: str):
        """
        WebSocket 클라이언트 초기화
        
        Args:
            access_token: 키움증권 OAuth access token
        """
        self.access_token = access_token
        self.websocket = None
        self.status = ConnectionStatus.DISCONNECTED
        self.keep_running = True
        self.registered_items: Dict[str, List[str]] = {}  # {grp_no: [items]}
        
        # 콜백 함수들
        self.on_connected: Optional[Callable] = None
        self.on_login_success: Optional[Callable] = None
        self.on_login_failed: Optional[Callable[[str], None]] = None
        self.on_realtime_data: Optional[Callable[[WebSocketRealtimeDataItem], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_disconnected: Optional[Callable] = None
        
        # WebSocket URL 설정 (샌드박스 모드에 따라)
        if settings.kiwoom_sandbox_mode:
            self.ws_url = 'wss://mockapi.kiwoom.com:10000/api/dostk/websocket'
        else:
            self.ws_url = 'wss://api.kiwoom.com:10000/api/dostk/websocket'
            
        logger.info(f"WebSocket 클라이언트 초기화 완료 - URL: {self.ws_url}")

    async def connect(self) -> bool:
        """
        WebSocket 서버에 연결
        
        Returns:
            bool: 연결 성공 여부
        """
        try:
            self.status = ConnectionStatus.CONNECTING
            logger.info("WebSocket 서버 연결 시도 중...")
            
            self.websocket = await websockets.connect(
                self.ws_url,
                ping_interval=30,  # 30초마다 ping
                ping_timeout=10,   # ping timeout 10초
                close_timeout=10   # close timeout 10초
            )
            
            self.status = ConnectionStatus.CONNECTED
            logger.info("WebSocket 서버 연결 성공")
            
            if self.on_connected:
                await self.on_connected()
            
            # 자동 로그인
            await self._login()
            
            return True
            
        except Exception as e:
            self.status = ConnectionStatus.ERROR
            error_msg = f"WebSocket 연결 실패: {str(e)}"
            logger.error(error_msg)
            
            if self.on_error:
                await self.on_error(error_msg)
            
            return False

    async def _login(self) -> None:
        """로그인 패킷 전송"""
        login_request = WebSocketLoginRequest(token=self.access_token)
        await self._send_message(login_request.dict())
        logger.info("로그인 패킷 전송 완료")

    async def _send_message(self, message: Dict[str, Any]) -> None:
        """
        WebSocket 메시지 전송
        
        Args:
            message: 전송할 메시지 (딕셔너리)
        """
        if not self.websocket or self.websocket.closed:
            raise ConnectionError("WebSocket 연결이 끊어졌습니다")
            
        message_json = json.dumps(message, ensure_ascii=False)
        await self.websocket.send(message_json)
        
        # PING 메시지가 아닌 경우에만 로그
        if message.get('trnm') != 'PING':
            logger.debug(f"메시지 전송: {message}")

    async def register_realtime(
        self, 
        items: List[str], 
        types: List[str], 
        group_no: str = "1",
        refresh: str = "1"
    ) -> bool:
        """
        실시간 데이터 등록
        
        Args:
            items: 종목코드 리스트
            types: 실시간 타입 리스트 (예: ['0B'])
            group_no: 그룹 번호
            refresh: 기존 등록 유지 여부 (0: 기존유지안함, 1: 기존유지)
            
        Returns:
            bool: 등록 성공 여부
        """
        try:
            if self.status != ConnectionStatus.LOGIN_SUCCESS:
                raise ConnectionError("로그인이 필요합니다")
            
            register_request = WebSocketRegisterRequest(
                grp_no=group_no,
                refresh=refresh,
                data=[{
                    "item": items,
                    "type": types
                }]
            )
            
            await self._send_message(register_request.dict())
            
            # 등록된 아이템 저장
            if group_no not in self.registered_items:
                self.registered_items[group_no] = []
            self.registered_items[group_no].extend(items)
            
            logger.info(f"실시간 데이터 등록: 그룹={group_no}, 종목={items}, 타입={types}")
            return True
            
        except Exception as e:
            error_msg = f"실시간 데이터 등록 실패: {str(e)}"
            logger.error(error_msg)
            if self.on_error:
                await self.on_error(error_msg)
            return False

    async def unregister_realtime(
        self, 
        items: List[str], 
        types: List[str], 
        group_no: str = "1"
    ) -> bool:
        """
        실시간 데이터 해지
        
        Args:
            items: 해지할 종목코드 리스트
            types: 실시간 타입 리스트
            group_no: 그룹 번호
            
        Returns:
            bool: 해지 성공 여부
        """
        try:
            if self.status != ConnectionStatus.LOGIN_SUCCESS:
                raise ConnectionError("로그인이 필요합니다")
            
            remove_request = WebSocketRemoveRequest(
                grp_no=group_no,
                data=[{
                    "item": items,
                    "type": types
                }]
            )
            
            await self._send_message(remove_request.dict())
            
            # 등록된 아이템에서 제거
            if group_no in self.registered_items:
                for item in items:
                    if item in self.registered_items[group_no]:
                        self.registered_items[group_no].remove(item)
            
            logger.info(f"실시간 데이터 해지: 그룹={group_no}, 종목={items}, 타입={types}")
            return True
            
        except Exception as e:
            error_msg = f"실시간 데이터 해지 실패: {str(e)}"
            logger.error(error_msg)
            if self.on_error:
                await self.on_error(error_msg)
            return False

    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """
        수신된 메시지 처리
        
        Args:
            message: 수신된 메시지
        """
        trnm = message.get('trnm')
        
        if trnm == 'LOGIN':
            await self._handle_login_response(message)
        elif trnm == 'PING':
            await self._handle_ping(message)
        elif trnm == 'REAL':
            await self._handle_realtime_data(message)
        elif trnm in ['REG', 'REMOVE']:
            await self._handle_registration_response(message)
        else:
            logger.debug(f"알 수 없는 메시지 타입: {trnm}")

    async def _handle_login_response(self, message: Dict[str, Any]) -> None:
        """로그인 응답 처리"""
        return_code = message.get('return_code', 1)
        return_msg = message.get('return_msg', '')
        
        if return_code == 0:
            self.status = ConnectionStatus.LOGIN_SUCCESS
            logger.info("WebSocket 로그인 성공")
            if self.on_login_success:
                await self.on_login_success()
        else:
            self.status = ConnectionStatus.LOGIN_FAILED
            error_msg = f"WebSocket 로그인 실패: {return_msg}"
            logger.error(error_msg)
            if self.on_login_failed:
                await self.on_login_failed(return_msg)

    async def _handle_ping(self, message: Dict[str, Any]) -> None:
        """PING 메시지 처리 (수신한 PING을 그대로 반환)"""
        await self._send_message(message)
        logger.debug("PING 응답 전송")

    async def _handle_realtime_data(self, message: Dict[str, Any]) -> None:
        """실시간 데이터 처리"""
        data_list = message.get('data', [])
        
        for data_item in data_list:
            try:
                realtime_item = WebSocketRealtimeDataItem(**data_item)
                
                # 실시간 타입명 추가
                if realtime_item.type and realtime_item.type in REALTIME_TYPE_CODES:
                    realtime_item.name = REALTIME_TYPE_CODES[realtime_item.type]
                
                logger.debug(f"실시간 데이터 수신: {realtime_item.item} - {realtime_item.type}")
                
                if self.on_realtime_data:
                    await self.on_realtime_data(realtime_item)
                    
            except Exception as e:
                logger.error(f"실시간 데이터 파싱 오류: {str(e)}")

    async def _handle_registration_response(self, message: Dict[str, Any]) -> None:
        """등록/해지 응답 처리"""
        return_code = message.get('return_code', 1)
        return_msg = message.get('return_msg', '')
        trnm = message.get('trnm')
        
        if return_code == 0:
            logger.info(f"{trnm} 요청 성공: {return_msg}")
        else:
            logger.error(f"{trnm} 요청 실패: {return_msg}")

    async def listen(self) -> None:
        """메시지 수신 루프"""
        while self.keep_running and self.websocket:
            try:
                raw_message = await self.websocket.recv()
                message = json.loads(raw_message)
                
                # PING 메시지가 아닌 경우에만 로그
                if message.get('trnm') != 'PING':
                    logger.debug(f"메시지 수신: {message}")
                
                await self._handle_message(message)
                
            except websockets.ConnectionClosed:
                logger.info("WebSocket 연결이 서버에 의해 종료됨")
                break
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 오류: {str(e)}")
            except Exception as e:
                error_msg = f"메시지 처리 오류: {str(e)}"
                logger.error(error_msg)
                if self.on_error:
                    await self.on_error(error_msg)

    async def run(self) -> None:
        """WebSocket 클라이언트 실행"""
        if await self.connect():
            await self.listen()
        await self.disconnect()

    async def disconnect(self) -> None:
        """WebSocket 연결 종료"""
        self.keep_running = False
        
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
            
        self.status = ConnectionStatus.DISCONNECTED
        self.registered_items.clear()
        
        logger.info("WebSocket 연결 종료")
        
        if self.on_disconnected:
            await self.on_disconnected()

    def get_status(self) -> Dict[str, Any]:
        """현재 상태 정보 반환"""
        return {
            "status": self.status.value,
            "connected": self.websocket is not None and not self.websocket.closed,
            "registered_groups": list(self.registered_items.keys()),
            "registered_items_count": sum(len(items) for items in self.registered_items.values()),
            "ws_url": self.ws_url
        }

    # 콜백 함수 설정 메서드들
    def set_on_connected(self, callback: Callable):
        """연결 성공 콜백 설정"""
        self.on_connected = callback

    def set_on_login_success(self, callback: Callable):
        """로그인 성공 콜백 설정"""
        self.on_login_success = callback

    def set_on_login_failed(self, callback: Callable[[str], None]):
        """로그인 실패 콜백 설정"""
        self.on_login_failed = callback

    def set_on_realtime_data(self, callback: Callable[[WebSocketRealtimeDataItem], None]):
        """실시간 데이터 수신 콜백 설정"""
        self.on_realtime_data = callback

    def set_on_error(self, callback: Callable[[str], None]):
        """에러 발생 콜백 설정"""
        self.on_error = callback

    def set_on_disconnected(self, callback: Callable):
        """연결 종료 콜백 설정"""
        self.on_disconnected = callback


# 싱글톤 WebSocket 클라이언트 매니저
class WebSocketManager:
    """WebSocket 클라이언트 매니저 (싱글톤)"""
    
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_client(self, access_token: str = None) -> Optional[KiwoomWebSocketClient]:
        """WebSocket 클라이언트 인스턴스 반환"""
        if self._client is None and access_token:
            self._client = KiwoomWebSocketClient(access_token)
        return self._client
    
    def clear_client(self):
        """클라이언트 인스턴스 제거"""
        if self._client:
            asyncio.create_task(self._client.disconnect())
        self._client = None


# 전역 매니저 인스턴스
websocket_manager = WebSocketManager()