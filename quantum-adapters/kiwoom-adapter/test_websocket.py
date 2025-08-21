#!/usr/bin/env python3
"""키움 WebSocket 기능 테스트 스크립트

WebSocket 연결, 구독, 실시간 데이터 수신을 테스트합니다.
"""

import asyncio
import json
import websockets
from datetime import datetime


async def test_websocket_connection():
    """WebSocket 연결 및 기본 기능 테스트"""
    uri = "ws://localhost:8100/ws/realtime"
    
    try:
        print("🔌 WebSocket 서버에 연결 중...")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket 연결 성공")
            
            # 환영 메시지 수신
            welcome_message = await websocket.recv()
            print(f"📥 환영 메시지: {welcome_message}")
            
            # 구독 요청
            subscribe_message = {
                "action": "subscribe",
                "symbols": ["005930", "000660"],  # 삼성전자, SK하이닉스
                "types": ["00"]  # 주식호가잔량
            }
            
            print(f"📤 구독 요청 전송: {json.dumps(subscribe_message, ensure_ascii=False)}")
            await websocket.send(json.dumps(subscribe_message))
            
            # 구독 응답 대기
            response = await websocket.recv()
            print(f"📥 구독 응답: {response}")
            
            # 상태 조회
            status_message = {"action": "get_status"}
            print(f"📤 상태 조회 요청: {json.dumps(status_message)}")
            await websocket.send(json.dumps(status_message))
            
            status_response = await websocket.recv()
            print(f"📊 상태 응답: {status_response}")
            
            # Ping 테스트
            ping_message = {"action": "ping"}
            print(f"📤 Ping 전송: {json.dumps(ping_message)}")
            await websocket.send(json.dumps(ping_message))
            
            pong_response = await websocket.recv()
            print(f"📥 Pong 수신: {pong_response}")
            
            # 실시간 데이터 대기 (10초간)
            print("⏰ 실시간 데이터 대기 중 (10초)...")
            try:
                # 타임아웃 설정하여 무한 대기 방지
                realtime_data = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                print(f"📊 실시간 데이터 수신: {realtime_data}")
            except asyncio.TimeoutError:
                print("⏰ 실시간 데이터 타임아웃 (키움 서버 연결 필요)")
            
            print("✅ WebSocket 테스트 완료")
            
    except websockets.exceptions.ConnectionRefused:
        print("❌ WebSocket 서버 연결 실패: 서버가 실행 중인지 확인하세요")
        print("   서버 실행: uvicorn src.kiwoom_api.main:app --host 0.0.0.0 --port 8100")
    except Exception as e:
        print(f"❌ WebSocket 테스트 실패: {str(e)}")


async def test_rest_api_endpoints():
    """REST API 엔드포인트 테스트"""
    import httpx
    
    base_url = "http://localhost:8100"
    
    try:
        async with httpx.AsyncClient() as client:
            print("\n🔍 REST API 엔드포인트 테스트")
            
            # 1. WebSocket 연결 정보 조회
            print("1️⃣ WebSocket 연결 정보 조회...")
            response = await client.get(f"{base_url}/ws/realtime/info")
            print(f"   상태: {response.status_code}")
            print(f"   응답: {response.json()}")
            
            # 2. 실시간 데이터 타입 조회
            print("\n2️⃣ 실시간 데이터 타입 조회...")
            response = await client.get(f"{base_url}/ws/realtime/types")
            print(f"   상태: {response.status_code}")
            types_data = response.json()
            print(f"   타입 개수: {len(types_data.get('types', {}))}")
            
            # 3. 실시간 데이터 필드 조회
            print("\n3️⃣ 실시간 데이터 필드 조회...")
            response = await client.get(f"{base_url}/ws/realtime/fields")
            print(f"   상태: {response.status_code}")
            fields_data = response.json()
            print(f"   필드 개수: {len(fields_data.get('fields', {}))}")
            
            # 4. API 문서 확인
            print("\n4️⃣ API 문서 접근...")
            response = await client.get(f"{base_url}/docs")
            print(f"   상태: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type')}")
            
            print("\n✅ REST API 테스트 완료")
            
    except httpx.ConnectError:
        print("❌ REST API 서버 연결 실패: 서버가 실행 중인지 확인하세요")
    except Exception as e:
        print(f"❌ REST API 테스트 실패: {str(e)}")


def print_test_info():
    """테스트 정보 출력"""
    print("🚀 키움 WebSocket API 테스트 시작")
    print("=" * 50)
    print(f"⏰ 테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 WebSocket URL: ws://localhost:8100/ws/realtime")
    print(f"📚 API 문서: http://localhost:8100/docs")
    print(f"🧪 테스트 페이지: http://localhost:8100/ws/test")
    print("=" * 50)
    print()


async def main():
    """메인 테스트 함수"""
    print_test_info()
    
    # 1. REST API 엔드포인트 테스트
    await test_rest_api_endpoints()
    
    # 2. WebSocket 연결 테스트
    await test_websocket_connection()
    
    print("\n" + "=" * 50)
    print("🏁 모든 테스트 완료")
    print()
    print("📝 추가 테스트 방법:")
    print("   1. 브라우저에서 http://localhost:8100/ws/test 접속")
    print("   2. WebSocket 연결 후 종목코드 입력하여 구독 테스트")
    print("   3. 키움 토큰 발급 후 실시간 데이터 수신 확인")


if __name__ == "__main__":
    asyncio.run(main())