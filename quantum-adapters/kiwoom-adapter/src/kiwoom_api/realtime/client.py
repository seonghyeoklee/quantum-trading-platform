"""
키움증권 실시간 WebSocket 클라이언트
18개 실시간 시세 타입을 지원하는 확장 가능한 구조
"""

import asyncio
import websockets
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

# 상대 import 처리
try:
    from ..config.settings import settings
    from ..functions.auth import get_access_token
except ImportError:
    # 직접 실행 시 절대 경로 import
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root / 'src'))
    os.chdir(project_root)
    
    from kiwoom_api.config.settings import settings
    from kiwoom_api.functions.auth import get_access_token

from .subscription_manager import SubscriptionManager
from .handlers.type_handlers import TypeHandlerRegistry
from .models.realtime_data import RealtimeResponse, RealtimeData
from .types.realtime_types import is_supported_type, get_supported_types


# 키움 공식 WebSocket 서버 URL
KIWOOM_OFFICIAL_URL = 'wss://api.kiwoom.com:10000/api/dostk/websocket'


class RealtimeClient:
    """키움증권 18개 실시간 시세 지원 WebSocket 클라이언트"""
    
    def __init__(self, uri: str = KIWOOM_OFFICIAL_URL):
        self.uri = uri
        self.websocket = None
        self.connected = False
        self.keep_running = True
        self.access_token = None
        
        # 구독 및 핸들러 관리
        self.subscription_manager = SubscriptionManager()
        self.handler_registry = TypeHandlerRegistry()
        
        # 글로벌 콜백들
        self.connection_callbacks: List[Callable[[bool], None]] = []
        self.error_callbacks: List[Callable[[Exception], None]] = []
        self.message_callbacks: List[Callable[[RealtimeResponse], None]] = []
        
    async def get_access_token(self) -> Optional[str]:
        """액세스 토큰 획득"""
        try:
            print("🔑 키움 액세스 토큰 획득 중...")
            token_response = await get_access_token()
            self.access_token = token_response.get('token')
            if self.access_token:
                print(f"✅ 토큰 획득 성공: {self.access_token[:20]}...")
            return self.access_token
        except Exception as e:
            print(f"❌ 토큰 획득 실패: {e}")
            await self._execute_error_callbacks(e)
            return None
    
    async def connect(self) -> bool:
        """키움 공식 서버에 연결"""
        try:
            print("🔌 키움 공식 WebSocket 서버 연결 시도...")
            self.websocket = await websockets.connect(
                self.uri,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            )
            self.connected = True
            print("✅ WebSocket 연결 성공!")
            
            # 액세스 토큰 획득
            if not self.access_token:
                await self.get_access_token()
            
            if not self.access_token:
                raise Exception("키움 액세스 토큰이 필요합니다")
            
            # 로그인 패킷 전송 (공식 가이드 방식)
            login_packet = {
                'trnm': 'LOGIN',
                'token': self.access_token
            }
            
            print('🔑 키움 서버로 로그인 패킷 전송')
            await self.send_message(login_packet)
            
            # 연결 콜백 실행
            await self._execute_connection_callbacks(True)
            
            return True
            
        except Exception as e:
            print(f'❌ 키움 WebSocket 연결 실패: {e}')
            self.connected = False
            await self._execute_error_callbacks(e)
            await self._execute_connection_callbacks(False)
            return False
    
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """키움 서버에 메시지 전송"""
        if not self.connected:
            print("🔄 연결이 끊어져 재연결 시도")
            if not await self.connect():
                return False
                
        if self.connected and self.websocket:
            try:
                message_str = json.dumps(message, ensure_ascii=False)
                await self.websocket.send(message_str)
                
                # PING이 아닌 경우만 로깅
                if message.get('trnm') != 'PING':
                    print(f"📤 키움 메시지 전송: {message.get('trnm')}")
                    
                return True
                
            except Exception as e:
                print(f"❌ 키움 메시지 전송 실패: {e}")
                self.connected = False
                await self._execute_error_callbacks(e)
                return False
                
        return False
    
    async def receive_messages(self) -> None:
        """키움 서버에서 메시지 수신 및 처리"""
        while self.keep_running and self.connected:
            try:
                message_str = await self.websocket.recv()
                response_dict = json.loads(message_str)
                
                # Pydantic 모델로 파싱
                response = RealtimeResponse.model_validate(response_dict)
                
                # 메시지 유형별 처리
                await self._handle_response(response)
                
                # 글로벌 메시지 콜백 실행
                await self._execute_message_callbacks(response)
                    
            except websockets.ConnectionClosed:
                print("📡 키움 서버에서 연결이 종료됨")
                self.connected = False
                await self._execute_connection_callbacks(False)
                break
            except json.JSONDecodeError as e:
                print(f"❌ 키움 JSON 파싱 오류: {e}")
            except Exception as e:
                print(f"❌ 키움 메시지 수신 오류: {e}")
                await self._execute_error_callbacks(e)
    
    async def _handle_response(self, response: RealtimeResponse) -> None:
        """응답 타입별 처리"""
        if response.is_ping:
            # PING 응답 - 수신값 그대로 송신
            await self.send_message(response.model_dump(exclude_none=True))
            
        elif response.is_login_response:
            # 로그인 응답 처리
            if not response.is_success:
                print(f"❌ 키움 로그인 실패: {response.return_msg}")
                await self.disconnect()
            else:
                print("✅ 키움 로그인 성공")
                
        elif response.is_registration_response:
            # 등록/해지 응답 처리
            if response.is_success:
                print(f"✅ 키움 {response.trnm} 성공: {response.return_msg}")
            else:
                print(f"❌ 키움 {response.trnm} 실패: {response.return_msg}")
                
        elif response.is_realtime_data:
            # 실시간 데이터 처리
            await self._handle_realtime_data(response)
    
    async def _handle_realtime_data(self, response: RealtimeResponse) -> None:
        """실시간 데이터 처리"""
        if not response.data:
            return
            
        for data_item in response.data:
            try:
                # 타입별 핸들러로 라우팅
                processed_data = await self.handler_registry.handle_data(data_item)
                
                if processed_data:
                    print(f"📊 실시간 데이터 처리 완료: {data_item.type} - {data_item.item}")
                    
            except Exception as e:
                print(f"❌ 실시간 데이터 처리 실패: {e}")
    
    # 구독 관리 메서드들
    async def subscribe(self, symbols: List[str], types: List[str] = None, 
                       group_no: Optional[str] = None) -> bool:
        """실시간 시세 구독"""
        if types is None:
            types = ['0B']  # 기본값: 주식체결
            
        # 지원하지 않는 타입 체크
        unsupported_types = [t for t in types if not is_supported_type(t)]
        if unsupported_types:
            print(f"⚠️ 지원하지 않는 타입: {unsupported_types}")
            print(f"📋 지원하는 타입: {list(get_supported_types().keys())}")
            
        # 구독 관리자에 추가
        actual_group_no = self.subscription_manager.add_subscription(symbols, types, group_no)
        
        # REG 요청 생성 및 전송
        reg_message = self.subscription_manager.get_subscription_request(
            symbols, types, actual_group_no
        )
        
        print(f"📝 키움 실시간 시세 등록: {symbols} - {types} (그룹: {actual_group_no})")
        success = await self.send_message(reg_message)
        
        return success
    
    async def unsubscribe(self, symbols: List[str], types: List[str] = None,
                         group_no: Optional[str] = None) -> bool:
        """실시간 시세 구독 해지"""
        if types is None:
            types = ['0B']
            
        # REMOVE 요청 생성 및 전송
        remove_message = self.subscription_manager.get_removal_request(
            symbols, types, group_no
        )
        
        print(f"🗑️ 키움 실시간 시세 해지: {symbols} - {types}")
        success = await self.send_message(remove_message)
        
        if success:
            # 구독 관리자에서 제거
            self.subscription_manager.remove_subscription(symbols, types, group_no)
            
        return success
    
    async def subscribe_multiple(self, subscriptions: Dict[str, List[str]]) -> bool:
        """여러 종목/타입 일괄 구독"""
        success_count = 0
        total_count = len(subscriptions)
        
        for symbol, types in subscriptions.items():
            if await self.subscribe([symbol], types):
                success_count += 1
                
        print(f"📊 일괄 구독 결과: {success_count}/{total_count} 성공")
        return success_count == total_count
    
    # 콜백 관리 메서드들
    def add_connection_callback(self, callback: Callable[[bool], None]) -> None:
        """연결 상태 변경 콜백 추가"""
        self.connection_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[Exception], None]) -> None:
        """에러 콜백 추가"""
        self.error_callbacks.append(callback)
        
    def add_message_callback(self, callback: Callable[[RealtimeResponse], None]) -> None:
        """메시지 수신 콜백 추가"""
        self.message_callbacks.append(callback)
    
    def add_type_handler_callback(self, type_code: str, callback: Callable[[RealtimeData], None]) -> None:
        """특정 타입 핸들러에 콜백 추가"""
        handler = self.handler_registry.get_handler(type_code)
        handler.add_callback(callback)
    
    # 내부 콜백 실행 메서드들
    async def _execute_connection_callbacks(self, connected: bool) -> None:
        """연결 콜백들 실행"""
        for callback in self.connection_callbacks:
            try:
                callback(connected)
            except Exception as e:
                print(f"❌ 연결 콜백 실행 오류: {e}")
    
    async def _execute_error_callbacks(self, error: Exception) -> None:
        """에러 콜백들 실행"""
        for callback in self.error_callbacks:
            try:
                callback(error)
            except Exception as e:
                print(f"❌ 에러 콜백 실행 오류: {e}")
                
    async def _execute_message_callbacks(self, response: RealtimeResponse) -> None:
        """메시지 콜백들 실행"""
        for callback in self.message_callbacks:
            try:
                callback(response)
            except Exception as e:
                print(f"❌ 메시지 콜백 실행 오류: {e}")
    
    # 유틸리티 메서드들
    def get_connection_info(self) -> Dict[str, Any]:
        """연결 상태 정보 반환"""
        return {
            'connected': self.connected,
            'server': 'kiwoom_official',
            'url': self.uri,
            'subscriptions': self.subscription_manager.get_statistics(),
            'supported_types': get_supported_types()
        }
    
    def get_subscription_statistics(self) -> Dict[str, Any]:
        """구독 통계 정보 반환"""
        return self.subscription_manager.get_statistics()
    
    async def run(self) -> None:
        """WebSocket 클라이언트 실행"""
        if await self.connect():
            await self.receive_messages()
    
    async def disconnect(self) -> None:
        """WebSocket 연결 종료"""
        self.keep_running = False
        if self.connected and self.websocket:
            await self.websocket.close()
            self.connected = False
            print("🔌 키움 WebSocket 연결 종료")
            await self._execute_connection_callbacks(False)


# 간단한 사용 예시 (직접 실행 시)
async def main():
    """테스트용 메인 함수"""
    client = RealtimeClient()
    
    # 연결 및 기본 구독
    if await client.connect():
        # 여러 타입 구독 테스트
        await client.subscribe(['005930'], ['0B', '00'])  # 삼성전자 체결+호가
        await client.subscribe(['000660'], ['0B'])        # SK하이닉스 체결
        
        # 실시간 데이터 수신
        await client.receive_messages()
    
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())