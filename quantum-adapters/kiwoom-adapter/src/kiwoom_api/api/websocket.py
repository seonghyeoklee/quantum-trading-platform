"""키움 WebSocket API 엔드포인트

웹 클라이언트용 WebSocket API 엔드포인트
실시간 시세 데이터 스트리밍 및 구독 관리
"""

import json
import logging
import sys
import uuid
from pathlib import Path
from typing import List, Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.responses import HTMLResponse

# Handle both relative and absolute imports for different execution contexts
try:
    from ..websocket.client_handler import connection_manager
    from ..websocket.realtime import get_websocket_client
    from ..models.websocket import (
        WebSocketRegisterRequest,
        WebSocketRemoveRequest,
        REALTIME_TYPE_CODES,
        REALTIME_VALUE_FIELDS
    )
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from kiwoom_api.websocket.client_handler import connection_manager
    from kiwoom_api.websocket.realtime import get_websocket_client
    from kiwoom_api.models.websocket import (
        WebSocketRegisterRequest,
        WebSocketRemoveRequest,
        REALTIME_TYPE_CODES,
        REALTIME_VALUE_FIELDS
    )

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket 실시간 API"])


@router.websocket("/ws/realtime")
async def websocket_realtime_endpoint(websocket: WebSocket):
    """실시간 데이터 WebSocket 엔드포인트
    
    웹 클라이언트가 실시간 시세 데이터를 수신하기 위한 WebSocket 연결
    
    연결 후 JSON 메시지를 통해 실시간 데이터 구독/해지 가능
    
    **메시지 형식:**
    ```json
    {
        "action": "subscribe",
        "symbols": ["005930", "000660"],
        "types": ["00", "0A"]
    }
    ```
    
    **응답 데이터 형식:**
    ```json
    {
        "type": "realtime_data",
        "symbol": "005930",
        "data_type": "00",
        "data_type_name": "주식호가잔량",
        "values": {
            "9001": "005930",
            "302": "삼성전자",
            "10": "75000"
        },
        "timestamp": "2025-01-21T10:30:00"
    }
    ```
    """
    # 고유 연결 ID 생성
    connection_id = str(uuid.uuid4())
    
    try:
        # 웹 클라이언트 연결
        await connection_manager.connect(websocket, connection_id)
        
        # 환영 메시지 전송
        welcome_message = {
            "type": "welcome",
            "connection_id": connection_id,
            "message": "키움 실시간 데이터 서비스에 연결되었습니다",
            "available_types": REALTIME_TYPE_CODES
        }
        await websocket.send_text(json.dumps(welcome_message, ensure_ascii=False))
        
        # 클라이언트 메시지 수신 대기
        while True:
            try:
                # WebSocket 연결 상태 확인
                if websocket.client_state.name != "CONNECTED":
                    logger.info(f"🔌 WebSocket 연결 상태 변경: {websocket.client_state.name}")
                    break
                    
                # 클라이언트로부터 메시지 수신
                data = await websocket.receive_text()
                message = json.loads(data)
                
                await _handle_client_message(connection_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"🔌 WebSocket 정상 해제: {connection_id}")
                break
            except json.JSONDecodeError:
                await _send_error(connection_id, "잘못된 JSON 형식입니다")
            except RuntimeError as e:
                if "disconnect" in str(e).lower() or "close" in str(e).lower():
                    logger.info(f"🔌 WebSocket 연결 종료 감지: {connection_id}")
                    break
                else:
                    logger.error(f"❌ WebSocket 런타임 오류 ({connection_id}): {str(e)}")
                    break
            except Exception as e:
                logger.error(f"❌ 메시지 처리 오류 ({connection_id}): {str(e)}")
                # 연결 관련 오류인 경우 루프 종료
                if "disconnect" in str(e).lower() or "close" in str(e).lower() or "websocket" in str(e).lower():
                    break
                # 그 외의 오류는 에러 메시지 전송 후 계속
                await _send_error(connection_id, f"메시지 처리 오류: {str(e)}")
                
    except WebSocketDisconnect:
        logger.info(f"🔌 클라이언트 연결 해제: {connection_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket 오류: {str(e)}")
    finally:
        await connection_manager.disconnect(connection_id)


async def _handle_client_message(connection_id: str, message: Dict[str, Any]) -> None:
    """클라이언트 메시지 처리"""
    action = message.get("action")
    
    if action == "subscribe":
        await _handle_subscribe(connection_id, message)
    elif action == "unsubscribe":
        await _handle_unsubscribe(connection_id, message)
    elif action == "ping":
        await _handle_ping(connection_id)
    elif action == "get_status":
        await _handle_get_status(connection_id)
    else:
        await _send_error(connection_id, f"알 수 없는 액션: {action}")


async def _handle_subscribe(connection_id: str, message: Dict[str, Any]) -> None:
    """실시간 데이터 구독 처리"""
    try:
        symbols = message.get("symbols", [])
        types = message.get("types", ["00"])
        
        if not symbols:
            await _send_error(connection_id, "구독할 종목코드가 필요합니다")
            return
            
        # 실시간 데이터 구독
        success = await connection_manager.subscribe_realtime(connection_id, symbols, types)
        
        if success:
            response = {
                "type": "subscribe_response",
                "success": True,
                "symbols": symbols,
                "types": types,
                "message": f"{len(symbols)}개 종목 구독이 완료되었습니다"
            }
        else:
            response = {
                "type": "subscribe_response",
                "success": False,
                "message": "구독 실패: 키움 WebSocket 연결을 확인해주세요"
            }
            
        await connection_manager.send_to_connection(connection_id, response)
        
    except Exception as e:
        await _send_error(connection_id, f"구독 처리 오류: {str(e)}")


async def _handle_unsubscribe(connection_id: str, message: Dict[str, Any]) -> None:
    """실시간 데이터 구독 해지 처리"""
    try:
        # 현재는 연결 해제로 구독 해지 처리 (향후 개선 가능)
        await connection_manager.disconnect(connection_id)
        
    except Exception as e:
        await _send_error(connection_id, f"구독 해지 오류: {str(e)}")


async def _handle_ping(connection_id: str) -> None:
    """Ping 요청 처리"""
    pong_message = {
        "type": "pong",
        "timestamp": "now"
    }
    await connection_manager.send_to_connection(connection_id, pong_message)


async def _handle_get_status(connection_id: str) -> None:
    """연결 상태 정보 요청 처리"""
    try:
        status_info = connection_manager.get_connection_info()
        
        response = {
            "type": "status_response",
            **status_info
        }
        
        await connection_manager.send_to_connection(connection_id, response)
        
    except Exception as e:
        await _send_error(connection_id, f"상태 조회 오류: {str(e)}")


async def _send_error(connection_id: str, message: str) -> None:
    """에러 메시지 전송 (안전한 전송)"""
    try:
        error_message = {
            "type": "error",
            "message": message
        }
        await connection_manager.send_to_connection(connection_id, error_message)
    except Exception as e:
        # 에러 메시지 전송 실패는 로그만 기록 (무한 재귀 방지)
        logger.warning(f"⚠️ 에러 메시지 전송 실패 ({connection_id}): {str(e)}")


@router.get("/ws/realtime/info")
async def websocket_info():
    """WebSocket 연결 정보 조회
    
    현재 활성화된 WebSocket 연결 및 구독 정보를 반환합니다.
    
    Returns:
        Dict: 연결 상태 정보
            - active_connections: 활성 연결 수
            - kiwoom_connected: 키움 WebSocket 연결 상태
            - registered_items: 등록된 실시간 항목 리스트
            - subscriptions: 구독 정보
    """
    return connection_manager.get_connection_info()


@router.get("/ws/realtime/types")
async def get_realtime_types():
    """실시간 데이터 타입 코드 조회
    
    키움 WebSocket에서 지원하는 실시간 데이터 타입 코드와 설명을 반환합니다.
    
    Returns:
        Dict: 실시간 데이터 타입 매핑
    """
    return {
        "types": REALTIME_TYPE_CODES,
        "description": "키움 WebSocket 실시간 데이터 타입 코드"
    }


@router.get("/ws/realtime/fields")
async def get_realtime_fields():
    """실시간 데이터 필드 코드 조회
    
    키움 WebSocket 실시간 데이터의 필드 코드와 설명을 반환합니다.
    
    Returns:
        Dict: 실시간 데이터 필드 매핑
    """
    return {
        "fields": REALTIME_VALUE_FIELDS,
        "description": "키움 WebSocket 실시간 데이터 필드 코드"
    }


@router.post("/ws/realtime/test-register")
async def test_register_realtime(request: WebSocketRegisterRequest):
    """실시간 데이터 등록 테스트 (REST API)
    
    WebSocket 연결 없이 키움 WebSocket에 직접 실시간 데이터 등록을 테스트합니다.
    개발 및 디버깅 용도로만 사용하세요.
    
    Args:
        request: 실시간 등록 요청
        
    Returns:
        Dict: 등록 결과
    """
    try:
        kiwoom_client = await get_websocket_client()
        
        if not kiwoom_client.connected:
            if not await kiwoom_client.connect():
                raise HTTPException(status_code=503, detail="키움 WebSocket 연결 실패")
        
        # 첫 번째 데이터 항목으로 등록 (간소화)
        first_data = request.data[0] if request.data else None
        if not first_data:
            raise HTTPException(status_code=400, detail="등록할 데이터가 없습니다")
            
        success = await kiwoom_client.register_realtime(
            grp_no=request.grp_no,
            refresh=request.refresh,
            items=first_data.item,
            types=first_data.type
        )
        
        return {
            "success": success,
            "message": "등록 요청 전송 완료" if success else "등록 요청 실패",
            "grp_no": request.grp_no,
            "items": first_data.item,
            "types": first_data.type
        }
        
    except Exception as e:
        logger.error(f"❌ 실시간 등록 테스트 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"등록 실패: {str(e)}")


@router.get("/ws/test")
async def websocket_test_page():
    """WebSocket 테스트 페이지
    
    WebSocket 연결을 테스트할 수 있는 간단한 HTML 페이지를 제공합니다.
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>키움 WebSocket 테스트</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            .input-group { margin: 10px 0; }
            label { display: inline-block; width: 120px; font-weight: bold; }
            input, textarea { padding: 8px; margin: 5px; }
            button { padding: 10px 20px; margin: 5px; background: #4CAF50; color: white; border: none; cursor: pointer; }
            button:hover { background: #45a049; }
            #messages { border: 1px solid #ccc; height: 400px; overflow-y: auto; padding: 10px; margin: 10px 0; background: #f9f9f9; }
            .message { margin: 5px 0; padding: 5px; background: white; border-radius: 3px; }
            .error { background: #ffebee; color: #c62828; }
            .success { background: #e8f5e8; color: #2e7d2e; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>키움 WebSocket 실시간 데이터 테스트</h1>
            
            <div class="input-group">
                <label>WebSocket URL:</label>
                <input type="text" id="wsUrl" value="ws://localhost:8100/ws/realtime" style="width: 300px;">
            </div>
            
            <div class="input-group">
                <button onclick="connect()">연결</button>
                <button onclick="disconnect()">연결 해제</button>
                <span id="status">연결 안됨</span>
            </div>
            
            <div class="input-group">
                <label>종목코드:</label>
                <input type="text" id="symbols" value="005930,000660" placeholder="005930,000660">
            </div>
            
            <div class="input-group">
                <label>데이터 타입:</label>
                <input type="text" id="types" value="00,0A" placeholder="00,0A">
            </div>
            
            <div class="input-group">
                <button onclick="subscribe()">구독</button>
                <button onclick="unsubscribe()">구독 해지</button>
                <button onclick="getStatus()">상태 조회</button>
                <button onclick="ping()">Ping</button>
            </div>
            
            <div class="input-group">
                <button onclick="clearMessages()">메시지 지우기</button>
            </div>
            
            <div id="messages"></div>
        </div>
        
        <script>
            let ws = null;
            
            function connect() {
                const url = document.getElementById('wsUrl').value;
                ws = new WebSocket(url);
                
                ws.onopen = function(event) {
                    addMessage('WebSocket 연결됨', 'success');
                    document.getElementById('status').textContent = '연결됨';
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    addMessage('수신: ' + JSON.stringify(data, null, 2));
                };
                
                ws.onclose = function(event) {
                    addMessage('WebSocket 연결 해제됨', 'error');
                    document.getElementById('status').textContent = '연결 안됨';
                };
                
                ws.onerror = function(error) {
                    addMessage('WebSocket 오류: ' + error, 'error');
                };
            }
            
            function disconnect() {
                if (ws) {
                    ws.close();
                }
            }
            
            function subscribe() {
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    addMessage('먼저 WebSocket에 연결하세요', 'error');
                    return;
                }
                
                const symbols = document.getElementById('symbols').value.split(',').map(s => s.trim());
                const types = document.getElementById('types').value.split(',').map(s => s.trim());
                
                const message = {
                    action: 'subscribe',
                    symbols: symbols,
                    types: types
                };
                
                ws.send(JSON.stringify(message));
                addMessage('구독 요청 전송: ' + JSON.stringify(message));
            }
            
            function unsubscribe() {
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    addMessage('먼저 WebSocket에 연결하세요', 'error');
                    return;
                }
                
                const message = { action: 'unsubscribe' };
                ws.send(JSON.stringify(message));
                addMessage('구독 해지 요청 전송');
            }
            
            function getStatus() {
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    addMessage('먼저 WebSocket에 연결하세요', 'error');
                    return;
                }
                
                const message = { action: 'get_status' };
                ws.send(JSON.stringify(message));
                addMessage('상태 조회 요청 전송');
            }
            
            function ping() {
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    addMessage('먼저 WebSocket에 연결하세요', 'error');
                    return;
                }
                
                const message = { action: 'ping' };
                ws.send(JSON.stringify(message));
                addMessage('Ping 전송');
            }
            
            function addMessage(message, type = 'normal') {
                const messagesDiv = document.getElementById('messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message ' + type;
                messageDiv.textContent = new Date().toLocaleTimeString() + ' - ' + message;
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
            
            function clearMessages() {
                document.getElementById('messages').innerHTML = '';
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)