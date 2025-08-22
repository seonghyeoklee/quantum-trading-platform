#!/usr/bin/env python3
"""
키움증권 공식 가이드 기반 WebSocket 실시간 시세 클라이언트

공식 문서 기준으로 구현:
- 서버: wss://api.kiwoom.com:10000/api/dostk/websocket
- 프로토콜: LOGIN → REG → REAL 데이터 수신
- PING/PONG 자동 처리
"""

import asyncio
import websockets
import json
import sys
import os
from pathlib import Path

# 환경 설정 로드 (상대 경로 import)
try:
    from .config.settings import settings
    from .functions.auth import get_access_token
except ImportError:
    # 직접 실행 시 절대 경로 import
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from kiwoom_api.config.settings import settings
    from kiwoom_api.functions.auth import get_access_token

# 키움 공식 WebSocket 서버 URL
SOCKET_URL = 'wss://api.kiwoom.com:10000/api/dostk/websocket'

class KiwoomWebSocketClient:
    """키움증권 공식 가이드 기반 WebSocket 클라이언트"""
    
    def __init__(self, uri):
        self.uri = uri
        self.websocket = None
        self.connected = False
        self.keep_running = True
        self.access_token = None
        
    async def get_access_token(self):
        """액세스 토큰 획득"""
        try:
            print("🔑 액세스 토큰 획득 중...")
            token_response = await get_access_token()
            self.access_token = token_response.get('token')
            if self.access_token:
                print(f"✅ 토큰 획득 성공: {self.access_token[:20]}...")
            return self.access_token
        except Exception as e:
            print(f"❌ 토큰 획득 실패: {e}")
            return None
    
    async def connect(self):
        """웹소켓 서버에 연결"""
        try:
            print("🔌 서버와 연결을 시도 중입니다.")
            self.websocket = await websockets.connect(self.uri)
            self.connected = True
            print("✅ WebSocket 연결 성공!")
            
            # 액세스 토큰 획득
            if not self.access_token:
                await self.get_access_token()
            
            if not self.access_token:
                raise Exception("액세스 토큰이 필요합니다")
            
            # 로그인 패킷 전송 (공식 가이드 방식)
            login_packet = {
                'trnm': 'LOGIN',
                'token': self.access_token
            }
            
            print('🔑 실시간 시세 서버로 로그인 패킷을 전송합니다.')
            await self.send_message(message=login_packet)
            
        except Exception as e:
            print(f'❌ Connection error: {e}')
            self.connected = False
    
    async def send_message(self, message):
        """서버에 메시지 전송"""
        if not self.connected:
            await self.connect()  # 연결이 끊어졌다면 재연결
            
        if self.connected and self.websocket:
            try:
                # message가 문자열이 아니면 JSON으로 직렬화
                if not isinstance(message, str):
                    message = json.dumps(message, ensure_ascii=False)
                
                await self.websocket.send(message)
                
                # PING 메시지가 아닌 경우만 출력
                if not (isinstance(message, str) and 'PING' in message):
                    print(f'📤 Message sent: {message}')
                    
            except Exception as e:
                print(f'❌ Send error: {e}')
                self.connected = False
    
    async def receive_messages(self):
        """서버에서 메시지 수신 및 처리"""
        while self.keep_running and self.connected:
            try:
                # 서버로부터 수신한 메시지를 JSON 형식으로 파싱
                message_str = await self.websocket.recv()
                response = json.loads(message_str)
                
                # 메시지 유형별 처리
                trnm = response.get('trnm')
                
                if trnm == 'LOGIN':
                    await self.handle_login_response(response)
                elif trnm == 'PING':
                    await self.handle_ping(response)
                elif trnm == 'REAL':
                    await self.handle_real_data(response)
                elif trnm in ['REG', 'REMOVE']:
                    await self.handle_registration_response(response)
                else:
                    print(f'📥 Unknown message type: {response}')
                    
            except websockets.ConnectionClosed:
                print('📡 Connection closed by the server')
                self.connected = False
                break
            except json.JSONDecodeError as e:
                print(f'❌ JSON parse error: {e}')
            except Exception as e:
                print(f'❌ Receive error: {e}')
    
    async def handle_login_response(self, response):
        """로그인 응답 처리 (공식 가이드 방식)"""
        return_code = response.get('return_code')
        return_msg = response.get('return_msg', '')
        
        if return_code != 0:
            print(f'❌ 로그인 실패하였습니다: {return_msg}')
            await self.disconnect()
        else:
            print('✅ 로그인 성공하였습니다.')
    
    async def handle_ping(self, response):
        """PING 메시지 처리 - 수신값 그대로 송신 (공식 가이드 방식)"""
        await self.send_message(response)
    
    async def handle_real_data(self, response):
        """실시간 데이터 처리"""
        print(f'📊 실시간 시세 서버 응답 수신: {json.dumps(response, ensure_ascii=False, indent=2)}')
    
    async def handle_registration_response(self, response):
        """등록/해지 응답 처리"""
        return_code = response.get('return_code')
        return_msg = response.get('return_msg', '')
        trnm = response.get('trnm')
        
        if return_code == 0:
            print(f'✅ {trnm} 성공: {return_msg}')
        else:
            print(f'❌ {trnm} 실패: {return_msg}')
    
    async def register_realtime(self, symbols, types=['0B']):
        """실시간 항목 등록 (공식 가이드 방식)"""
        reg_message = {
            'trnm': 'REG',        # 서비스명
            'grp_no': '1',        # 그룹번호  
            'refresh': '1',       # 기존등록유지여부
            'data': [{            # 실시간 등록 리스트
                'item': symbols,  # 실시간 등록 요소 (종목코드 리스트)
                'type': types,    # 실시간 항목 (데이터 타입 리스트)
            }]
        }
        
        print(f"📝 실시간 시세 등록: {symbols} - {types}")
        await self.send_message(reg_message)
    
    async def run(self):
        """웹소켓 클라이언트 실행"""
        await self.connect()
        if self.connected:
            await self.receive_messages()
    
    async def disconnect(self):
        """웹소켓 연결 종료"""
        self.keep_running = False
        if self.connected and self.websocket:
            await self.websocket.close()
            self.connected = False
            print('🔌 Disconnected from WebSocket server')


async def main():
    """메인 실행 함수 (공식 가이드 방식)"""
    print("🚀 키움증권 공식 WebSocket 클라이언트 시작")
    print("=" * 50)
    
    # WebSocketClient 전역 변수 선언
    websocket_client = KiwoomWebSocketClient(SOCKET_URL)
    
    try:
        # WebSocket 클라이언트를 백그라운드에서 실행
        receive_task = asyncio.create_task(websocket_client.run())
        
        # 로그인 완료까지 대기
        await asyncio.sleep(2)
        
        if websocket_client.connected:
            # 실시간 항목 등록 (공식 가이드 예시)
            print("\n📝 실시간 시세 등록 중...")
            await websocket_client.register_realtime(
                symbols=['005930', '000660', '035420'],  # 삼성전자, SK하이닉스, NAVER
                types=['0B']  # 주식체결
            )
            
            print("\n📊 실시간 데이터 수신 대기 중... (Ctrl+C로 종료)")
            
            # 수신 작업이 종료될 때까지 대기
            await receive_task
        else:
            print("❌ WebSocket 연결 실패")
            
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 중단됨")
        await websocket_client.disconnect()
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        await websocket_client.disconnect()


# asyncio로 프로그램을 실행합니다.
if __name__ == '__main__':
    asyncio.run(main())