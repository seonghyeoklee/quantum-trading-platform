#!/usr/bin/env python3
"""
키움증권 공식 가이드 기반 WebSocket 실시간 시세 클라이언트 (Legacy)

⚠️ 이 파일은 하위 호환성을 위해 유지되며, 새로운 구조의 래퍼입니다.
새로운 개발은 realtime.client.RealtimeClient를 사용하세요.

공식 문서 기준으로 구현:
- 서버: wss://api.kiwoom.com:10000/api/dostk/websocket
- 프로토콜: LOGIN → REG → REAL 데이터 수신
- PING/PONG 자동 처리
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Any, List

# Handle both relative and absolute imports for different execution contexts
try:
    from .realtime.client import RealtimeClient
    from .realtime.models.realtime_data import RealtimeResponse
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from kiwoom_api.realtime.client import RealtimeClient
    from kiwoom_api.realtime.models.realtime_data import RealtimeResponse

# 키움 공식 WebSocket 서버 URL
SOCKET_URL = 'wss://api.kiwoom.com:10000/api/dostk/websocket'


class KiwoomWebSocketClient:
    """키움증권 공식 가이드 기반 WebSocket 클라이언트 (Legacy Wrapper)
    
    ⚠️ 하위 호환성을 위한 래퍼 클래스입니다.
    새로운 기능 개발은 RealtimeClient를 직접 사용하세요.
    """
    
    def __init__(self, uri):
        self.uri = uri
        self._client = RealtimeClient(uri)
        
        # Legacy 호환성을 위한 속성들
        self.websocket = None
        self.connected = False
        self.keep_running = True
        self.access_token = None
        
        # 새로운 클라이언트의 상태를 동기화하는 콜백 설정
        self._client.add_connection_callback(self._sync_connection_state)
        
    def _sync_connection_state(self, connected: bool):
        """연결 상태 동기화"""
        self.connected = connected
        self.websocket = self._client.websocket if connected else None
        self.access_token = self._client.access_token
        
    async def get_access_token(self):
        """액세스 토큰 획득 (Legacy 메서드)"""
        print("⚠️ 이 메서드는 deprecated입니다. RealtimeClient를 사용하세요.")
        token = await self._client.get_access_token()
        self.access_token = token
        return token
    
    async def connect(self):
        """웹소켓 서버에 연결 (Legacy 메서드)"""
        print("⚠️ 이 메서드는 deprecated입니다. RealtimeClient를 사용하세요.")
        success = await self._client.connect()
        return success
    
    async def send_message(self, message):
        """서버에 메시지 전송 (Legacy 메서드)"""
        print("⚠️ 이 메서드는 deprecated입니다. RealtimeClient를 사용하세요.")
        
        # 딕셔너리가 아니면 변환
        if isinstance(message, str):
            import json
            try:
                message = json.loads(message)
            except json.JSONDecodeError:
                print("❌ 잘못된 JSON 형식")
                return False
                
        return await self._client.send_message(message)
    
    async def receive_messages(self):
        """서버에서 오는 메시지를 수신하여 출력 (Legacy 메서드)"""
        print("⚠️ 이 메서드는 deprecated입니다. RealtimeClient를 사용하세요.")
        await self._client.receive_messages()
    
    async def run(self):
        """WebSocket 실행 (Legacy 메서드)"""
        print("⚠️ 이 메서드는 deprecated입니다. RealtimeClient를 사용하세요.")
        await self._client.run()
    
    async def disconnect(self):
        """WebSocket 연결 종료 (Legacy 메서드)"""
        print("⚠️ 이 메서드는 deprecated입니다. RealtimeClient를 사용하세요.")
        self.keep_running = False
        await self._client.disconnect()
        
    # 새로운 기능에 대한 편의 메서드들
    async def subscribe(self, symbols: List[str], types: List[str] = None):
        """실시간 시세 구독 (새로운 기능)"""
        return await self._client.subscribe(symbols, types)
        
    async def unsubscribe(self, symbols: List[str], types: List[str] = None):
        """실시간 시세 구독 해지 (새로운 기능)"""
        return await self._client.unsubscribe(symbols, types)
        
    def get_realtime_client(self) -> RealtimeClient:
        """새로운 RealtimeClient 인스턴스 반환"""
        return self._client


async def main():
    """향상된 테스트용 메인 함수 - 실시간 데이터 + TR 명령어 통합 테스트"""
    print("🚀 키움증권 WebSocket 클라이언트 시작 (실시간 + TR 통합)")
    print("=" * 60)
    
    # 새로운 구조 사용 권장
    print("✨ 통합 구조로 실행 중...")
    client = RealtimeClient(SOCKET_URL)
    
    # TR 콜백 등록
    def tr_callback(tr_name: str, result: Dict[str, Any]):
        if tr_name == "CNSRLST":
            print(f"\n📋 조건검색 목록: {result.get('total_count', 0)}개 조건식")
            for condition in result.get('conditions', []):
                print(f"   - {condition['seq']}: {condition['name']}")
        elif tr_name == "CNSRREQ":
            print(f"\n🔍 조건검색 결과: {result.get('total_results', 0)}개 종목 발견")
            if result.get('realtime_enabled'):
                print(f"   ⚡ 실시간 감시 모드 활성화됨")
        elif tr_name == "SCREENER_REALTIME":
            print(f"\n🚨 조건검색 알림: {result['stock_code']} - {result['action_description']}")
        elif tr_name == "CNSRCLR":
            print(f"\n⏹️ 실시간 감시 중단: 조건식 {result.get('seq')}")
    
    client.add_tr_callback(tr_callback)
    
    try:
        # 연결
        if await client.connect():
            print("✅ 연결 성공!")
            
            # 로그인 완료 후 3초 대기 (안정적인 구독을 위해)
            print("⏳ 로그인 완료 대기 중... (3초)")
            await asyncio.sleep(3)
            
            print(f"\n📊 지원 기능:")
            stats = client.get_subscription_statistics()
            tr_stats = client.get_tr_statistics()
            print(f"   - 실시간 데이터: 18종 지원")
            print(f"   - TR 명령어: {len(tr_stats['supported_trs'])}개 지원")
            print(f"     * {', '.join(tr_stats['supported_trs'])}")
            
            # 실시간 시세 구독 테스트 (기존 기능)
            print("\n📝 실시간 시세 구독 테스트...")
            await client.subscribe(['005930'], ['0A', '0B'])
            await asyncio.sleep(0.5)
            
            # TR 명령어 테스트 (신규 기능)  
            print("\n🔧 TR 명령어 테스트...")
            
            # 1. 조건검색 목록조회
            print("1️⃣ 조건검색 목록조회 요청...")
            await client.get_screener_list()
            await asyncio.sleep(1)
            
            # 2. 조건검색 실행 (일반 모드)
            print("2️⃣ 조건검색 실행 (일반 모드)...")
            await client.execute_screener_search("0", "0")  # 첫 번째 조건식, 일반 모드
            await asyncio.sleep(1)
            
            # 3. 조건검색 실행 (실시간 모드)
            print("3️⃣ 조건검색 실행 (실시간 모드)...")
            await client.execute_screener_search("0", "1")  # 첫 번째 조건식, 실시간 모드
            await asyncio.sleep(2)
            
            print(f"\n📊 현재 구독 상태:")
            stats = client.get_subscription_statistics()
            print(f"   - 실시간 종목: {stats['total_symbols']}개")
            print(f"   - 실시간 타입: {stats['total_types']}개")
            print(f"   - 연결 상태: {'✅ 연결됨' if stats['connected'] else '❌ 연결 끊김'}")
            
            print("\n📊 데이터 수신 중... (실시간 시세 + 조건검색 알림)")
            print("   * Ctrl+C로 종료")
            await client.receive_messages()
            
    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 중단됨")
        
        # 종료 전 정리 작업
        print("🧹 실시간 감시 정리 중...")
        try:
            await client.clear_screener_realtime("0")  # 활성화된 조건검색 정리
            await asyncio.sleep(0.5)
        except:
            pass
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
    finally:
        await client.disconnect()
        print("🏁 클라이언트 종료")


if __name__ == "__main__":
    asyncio.run(main())