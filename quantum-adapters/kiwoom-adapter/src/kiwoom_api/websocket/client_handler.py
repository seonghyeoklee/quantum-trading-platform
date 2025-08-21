"""WebSocket 클라이언트 연결 관리자

웹 클라이언트와 키움 WebSocket 서버 간의 브릿지 역할
실시간 데이터 브로드캐스팅 및 구독 관리
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Set, List, Any, Optional
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect

# Handle both relative and absolute imports for different execution contexts
try:
    from .realtime import get_websocket_client, ensure_websocket_connected
    from ..models.websocket import (
        WebSocketRegisterRequest, 
        WebSocketRemoveRequest,
        REALTIME_TYPE_CODES
    )
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from kiwoom_api.websocket.realtime import get_websocket_client, ensure_websocket_connected
    from kiwoom_api.models.websocket import (
        WebSocketRegisterRequest,
        WebSocketRemoveRequest, 
        REALTIME_TYPE_CODES
    )

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """웹 클라이언트 WebSocket 연결 관리자
    
    여러 웹 클라이언트의 WebSocket 연결을 관리하고
    키움 WebSocket에서 수신한 실시간 데이터를 브로드캐스팅
    """

    def __init__(self):
        # 활성 연결 관리
        self.active_connections: Dict[str, WebSocket] = {}
        
        # 구독 관리 (connection_id -> {symbol, types})
        self.subscriptions: Dict[str, Dict[str, Any]] = {}
        
        # 키움 WebSocket 클라이언트 연결 상태
        self.kiwoom_connected = False
        
        # 등록된 실시간 항목 추적 (중복 등록 방지)
        self.registered_items: Set[str] = set()

    async def connect(self, websocket: WebSocket, connection_id: str) -> None:
        """웹 클라이언트 연결"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        logger.info(f"🔗 웹 클라이언트 연결: {connection_id}")
        
        # 첫 번째 연결일 경우 키움 WebSocket 연결 확인
        if len(self.active_connections) == 1:
            await self._ensure_kiwoom_connection()

    async def disconnect(self, connection_id: str) -> None:
        """웹 클라이언트 연결 해제"""
        try:
            # 연결 제거
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
                
            # 구독 정보 처리
            if connection_id in self.subscriptions:
                try:
                    # 해당 연결의 구독 항목 해지
                    await self._unsubscribe_items(connection_id)
                except Exception as e:
                    logger.warning(f"⚠️ 구독 해지 중 오류 ({connection_id}): {str(e)}")
                finally:
                    # 구독 정보는 항상 제거
                    del self.subscriptions[connection_id]
                
            logger.info(f"🔌 웹 클라이언트 연결 해제 완료: {connection_id}")
            
            # 모든 연결이 해제된 경우 키움 WebSocket 정리
            if not self.active_connections:
                await self._cleanup_kiwoom_connection()
                
        except Exception as e:
            logger.error(f"❌ 연결 해제 중 오류 ({connection_id}): {str(e)}")
            # 오류가 발생해도 연결 정보는 제거
            self.active_connections.pop(connection_id, None)
            self.subscriptions.pop(connection_id, None)

    async def _ensure_kiwoom_connection(self) -> None:
        """키움 WebSocket 연결 확인 및 실시간 데이터 핸들러 등록"""
        try:
            kiwoom_client = await ensure_websocket_connected()
            
            # 실시간 데이터 핸들러 등록
            kiwoom_client.add_message_handler('REAL', self._handle_realtime_data)
            
            self.kiwoom_connected = True
            logger.info("✅ 키움 WebSocket 연결 및 핸들러 등록 완료")
            
        except Exception as e:
            logger.error(f"❌ 키움 WebSocket 연결 실패: {str(e)}")
            self.kiwoom_connected = False

    async def _cleanup_kiwoom_connection(self) -> None:
        """키움 WebSocket 연결 정리"""
        try:
            # 모든 등록된 실시간 항목 해지
            if self.registered_items:
                kiwoom_client = await get_websocket_client()
                await kiwoom_client.remove_realtime(
                    items=list(self.registered_items),
                    types=["00"]  # 기본 타입으로 일괄 해지
                )
                self.registered_items.clear()
                
            self.kiwoom_connected = False
            logger.info("🧹 키움 WebSocket 연결 정리 완료")
            
        except Exception as e:
            logger.error(f"❌ 키움 WebSocket 정리 실패: {str(e)}")

    async def subscribe_realtime(self, connection_id: str, symbols: List[str], 
                               types: List[str] = None) -> bool:
        """실시간 데이터 구독
        
        Args:
            connection_id: 웹 클라이언트 연결 ID
            symbols: 구독할 종목코드 리스트
            types: 실시간 데이터 타입 리스트 (기본값: ["00"])
            
        Returns:
            bool: 구독 성공 여부
        """
        if not self.kiwoom_connected:
            logger.error("❌ 키움 WebSocket 연결이 필요합니다")
            return False
            
        if types is None:
            types = ["00"]  # 기본값: 주식호가잔량
            
        try:
            # 구독 정보 저장
            self.subscriptions[connection_id] = {
                'symbols': symbols,
                'types': types,
                'subscribed_at': datetime.now()
            }
            
            # 새로운 항목만 키움에 등록
            new_items = [symbol for symbol in symbols if symbol not in self.registered_items]
            
            if new_items:
                kiwoom_client = await get_websocket_client()
                success = await kiwoom_client.register_realtime(
                    items=new_items,
                    types=types
                )
                
                if success:
                    self.registered_items.update(new_items)
                    logger.info(f"📝 실시간 구독 등록: {connection_id} -> {symbols}")
                    return True
                else:
                    logger.error(f"❌ 키움 WebSocket 등록 실패: {new_items}")
                    return False
            else:
                # 이미 등록된 항목들만 있는 경우
                logger.info(f"📝 기존 실시간 데이터 구독: {connection_id} -> {symbols}")
                return True
                
        except Exception as e:
            logger.error(f"❌ 실시간 구독 실패: {str(e)}")
            return False

    async def _unsubscribe_items(self, connection_id: str) -> None:
        """특정 연결의 구독 항목 해지"""
        if connection_id not in self.subscriptions:
            return
            
        try:
            subscription = self.subscriptions[connection_id]
            symbols = subscription.get('symbols', [])
            
            # 다른 연결에서 사용 중이지 않은 항목만 해지
            items_to_remove = []
            for symbol in symbols:
                if symbol in self.registered_items:
                    # 다른 연결에서 이 심볼을 사용하는지 확인
                    used_by_others = any(
                        symbol in sub.get('symbols', [])
                        for conn_id, sub in self.subscriptions.items()
                        if conn_id != connection_id
                    )
                    
                    if not used_by_others:
                        items_to_remove.append(symbol)
            
            # 해지 요청
            if items_to_remove:
                kiwoom_client = await get_websocket_client()
                await kiwoom_client.remove_realtime(
                    items=items_to_remove,
                    types=subscription.get('types', ["00"])
                )
                
                # 등록된 항목에서 제거
                self.registered_items -= set(items_to_remove)
                
                logger.info(f"🗑️ 실시간 구독 해지: {connection_id} -> {items_to_remove}")
                
        except Exception as e:
            logger.error(f"❌ 실시간 구독 해지 실패: {str(e)}")

    async def _handle_realtime_data(self, response: Dict[str, Any]) -> None:
        """키움에서 수신한 실시간 데이터를 웹 클라이언트들에게 브로드캐스팅"""
        try:
            # 실시간 데이터 파싱
            data_list = response.get('data', [])
            
            for data_item in data_list:
                symbol = data_item.get('item', '')
                data_type = data_item.get('type', '')
                values = data_item.get('values', {})
                
                # 구독 중인 클라이언트들에게 데이터 전송
                message = {
                    'type': 'realtime_data',
                    'symbol': symbol,
                    'data_type': data_type,
                    'data_type_name': REALTIME_TYPE_CODES.get(data_type, data_type),
                    'values': values,
                    'timestamp': datetime.now().isoformat()
                }
                
                await self._broadcast_to_subscribers(symbol, message)
                
        except Exception as e:
            logger.error(f"❌ 실시간 데이터 처리 실패: {str(e)}")

    async def _broadcast_to_subscribers(self, symbol: str, message: Dict[str, Any]) -> None:
        """특정 종목을 구독하는 클라이언트들에게 메시지 브로드캐스팅"""
        disconnected_connections = []
        
        for connection_id, websocket in self.active_connections.items():
            # 이 연결이 해당 심볼을 구독하는지 확인
            if (connection_id in self.subscriptions and 
                symbol in self.subscriptions[connection_id].get('symbols', [])):
                
                try:
                    # WebSocket 연결 상태 확인
                    if websocket.client_state.name != "CONNECTED":
                        logger.warning(f"⚠️ 브로드캐스트 시 WebSocket 연결 비활성 ({connection_id})")
                        disconnected_connections.append(connection_id)
                        continue
                        
                    await websocket.send_text(json.dumps(message, ensure_ascii=False))
                    
                except WebSocketDisconnect:
                    logger.info(f"🔌 브로드캐스트 시 WebSocket 연결 해제 감지 ({connection_id})")
                    disconnected_connections.append(connection_id)
                except RuntimeError as e:
                    if "WebSocket" in str(e) and "close" in str(e):
                        logger.info(f"🔌 브로드캐스트 시 WebSocket 이미 종료됨 ({connection_id})")
                        disconnected_connections.append(connection_id)
                    else:
                        logger.error(f"❌ 브로드캐스트 런타임 오류 ({connection_id}): {str(e)}")
                        disconnected_connections.append(connection_id)
                except Exception as e:
                    logger.error(f"❌ 브로드캐스트 실패 ({connection_id}): {str(e)}")
                    disconnected_connections.append(connection_id)
        
        # 연결이 끊어진 클라이언트들 정리
        for connection_id in disconnected_connections:
            await self.disconnect(connection_id)

    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """특정 연결에 메시지 전송"""
        if connection_id not in self.active_connections:
            return False
            
        try:
            websocket = self.active_connections[connection_id]
            
            # WebSocket 연결 상태 확인
            if websocket.client_state.name != "CONNECTED":
                logger.warning(f"⚠️ WebSocket 연결이 활성화되지 않음 ({connection_id}): {websocket.client_state.name}")
                await self.disconnect(connection_id)
                return False
                
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
            return True
            
        except WebSocketDisconnect:
            logger.info(f"🔌 WebSocket 연결 해제 감지 ({connection_id})")
            await self.disconnect(connection_id)
            return False
        except RuntimeError as e:
            if "WebSocket" in str(e) and "close" in str(e):
                logger.info(f"🔌 WebSocket 이미 종료됨 ({connection_id})")
                await self.disconnect(connection_id)
                return False
            else:
                logger.error(f"❌ 런타임 오류 ({connection_id}): {str(e)}")
                return False
        except Exception as e:
            logger.error(f"❌ 메시지 전송 실패 ({connection_id}): {str(e)}")
            await self.disconnect(connection_id)
            return False

    def get_connection_info(self) -> Dict[str, Any]:
        """연결 상태 정보 반환"""
        return {
            'active_connections': len(self.active_connections),
            'kiwoom_connected': self.kiwoom_connected,
            'registered_items': list(self.registered_items),
            'subscriptions': {
                conn_id: {
                    'symbols': sub.get('symbols', []),
                    'types': sub.get('types', []),
                    'subscribed_at': sub.get('subscribed_at').isoformat() if sub.get('subscribed_at') else None
                }
                for conn_id, sub in self.subscriptions.items()
            }
        }


# 전역 연결 관리자 인스턴스 (싱글톤 패턴)
connection_manager = WebSocketConnectionManager()