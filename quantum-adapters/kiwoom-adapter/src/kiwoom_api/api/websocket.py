"""실시간 WebSocket API

웹 클라이언트를 위한 실시간 시세 WebSocket 엔드포인트
키움 실시간 데이터를 웹 클라이언트로 브로드캐스트
"""

import json
import logging
import asyncio
from typing import Dict, List, Set
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse

# Handle both relative and absolute imports for different execution contexts
try:
    from ..realtime.client import RealtimeClient
    from ..config.settings import settings
except ImportError:
    import sys
    from pathlib import Path
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    from kiwoom_api.realtime.client import RealtimeClient
    from kiwoom_api.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.client_subscriptions: Dict[WebSocket, Set[str]] = {}
        self.realtime_client: RealtimeClient = None
        self.is_realtime_running = False
        
    async def connect(self, websocket: WebSocket):
        """클라이언트 연결"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.client_subscriptions[websocket] = set()
        logger.info(f"🔗 웹 클라이언트 연결: {len(self.active_connections)}개 연결됨")
        
        # 환영 메시지 전송
        await self.send_to_client(websocket, {
            "event": "connected",
            "message": "키움 실시간 시세 연결 성공",
            "timestamp": datetime.now().isoformat(),
            "info": {
                "mode": settings.kiwoom_mode_description,
                "available_stocks": ["005930", "000660"],
                "data_types": ["stock_trade", "stock_orderbook"]
            }
        })
        
        # 키움 실시간 클라이언트 시작 (첫 번째 연결 시에만)
        if not self.is_realtime_running:
            try:
                await self.start_realtime_client()
            except Exception as e:
                logger.warning(f"키움 실시간 클라이언트 시작 실패: {e}")
                await self.send_to_client(websocket, {
                    "event": "warning", 
                    "message": f"키움 서버 연결 실패: {str(e)}, 데모 모드로 전환합니다"
                })
                # 키움 연결 실패시에만 데모 모드 시작
                await self.start_demo_mode()
    
    def disconnect(self, websocket: WebSocket):
        """클라이언트 연결 해제"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.client_subscriptions:
            del self.client_subscriptions[websocket]
        logger.info(f"🔌 웹 클라이언트 연결 해제: {len(self.active_connections)}개 연결됨")
        
        # 모든 연결이 끊어지면 키움 클라이언트 중지
        if not self.active_connections and self.is_realtime_running:
            asyncio.create_task(self.stop_realtime_client())
    
    async def start_realtime_client(self):
        """키움 실시간 클라이언트 시작"""
        if self.is_realtime_running:
            return
            
        try:
            logger.info("🚀 키움 실시간 클라이언트 시작")
            
            # 키움 WebSocket URL
            kiwoom_ws_url = settings.kiwoom_websocket_url
            
            # RealtimeClient 초기화
            self.realtime_client = RealtimeClient(kiwoom_ws_url, skip_login=False)
            
            # 실시간 데이터 콜백 등록
            self.realtime_client.add_message_callback(self._handle_realtime_data)
            
            # 키움 서버 연결
            if await self.realtime_client.connect():
                self.is_realtime_running = True
                logger.info("✅ 키움 실시간 클라이언트 연결 성공")
                
                # 백그라운드에서 메시지 수신
                asyncio.create_task(self._receive_realtime_messages())
                
                # 웹 클라이언트에서 동적으로 구독할 때까지 대기
                logger.info("📊 웹 클라이언트에서 종목 선택을 대기 중...")
            else:
                logger.error("❌ 키움 실시간 클라이언트 연결 실패")
                
        except Exception as e:
            logger.error(f"❌ 키움 실시간 클라이언트 시작 실패: {e}")
    
    async def start_demo_mode(self):
        """데모 모드 시작 - 테스트 데이터 전송"""
        logger.info("🎮 데모 모드 시작 - 테스트 데이터 전송")
        
        # 백그라운드에서 데모 데이터 전송
        asyncio.create_task(self._send_demo_data())
    
    async def _send_demo_data(self):
        """데모 실시간 데이터 전송"""
        import random
        
        while self.active_connections:
            # 삼성전자 데모 데이터
            demo_price = 75000 + random.randint(-1000, 1000)
            demo_change = random.randint(-500, 500)
            demo_volume = random.randint(1000, 10000)
            
            demo_message = {
                "type": "realtime_data",
                "data": {
                    "stock_code": "005930",
                    "stock_name": "삼성전자",
                    "current_price": f"{demo_price:,}원",
                    "price_change": f"{demo_change:+,}원",
                    "change_rate": f"{demo_change/demo_price*100:+.2f}%",
                    "volume": f"{demo_volume:,}주",
                    "timestamp": datetime.now().isoformat(),
                    "trend": "up" if demo_change > 0 else "down" if demo_change < 0 else "flat"
                }
            }
            
            await self.broadcast(demo_message)
            await asyncio.sleep(3)  # 3초마다 데이터 전송
    
    async def stop_realtime_client(self):
        """키움 실시간 클라이언트 중지"""
        if not self.is_realtime_running:
            return
            
        try:
            logger.info("🛑 키움 실시간 클라이언트 중지")
            if self.realtime_client:
                await self.realtime_client.disconnect()
            self.is_realtime_running = False
            logger.info("✅ 키움 실시간 클라이언트 중지 완료")
        except Exception as e:
            logger.error(f"❌ 키움 실시간 클라이언트 중지 실패: {e}")
    
    async def _receive_realtime_messages(self):
        """키움 실시간 메시지 수신 (백그라운드)"""
        try:
            await self.realtime_client.receive_messages()
        except Exception as e:
            logger.error(f"❌ 실시간 메시지 수신 오류: {e}")
            self.is_realtime_running = False
    
    def _handle_realtime_data(self, data: Dict):
        """키움 실시간 데이터 처리 및 웹 클라이언트 전송 (원본 형태)"""
        try:
            # 업종 지수 데이터 상세 로깅
            trnm = data.get('trnm', 'UNKNOWN')
            
            if trnm == 'REAL':
                data_list = data.get('data', [])
                for item in data_list:
                    item_code = item.get('item', 'N/A')
                    data_type = item.get('type', 'N/A')
                    data_name = item.get('name', 'Unknown')
                    values = item.get('values', {})
                    
                    # 업종 지수 패턴 확인 (실제 키움 형식: 숫자 3자리 + 0J 타입)
                    is_sector = (len(item_code) == 3 and item_code.isdigit()) or item_code.startswith('KRX:')
                    is_sector_type = data_type in ['0J', '0B', '0D', '0E']
                    
                    if is_sector and data_type == '0J':
                        logger.info(f"📊 업종 지수 데이터 수신:")
                        logger.info(f"   🏢 업종: {data_name} ({item_code})")
                        logger.info(f"   📈 데이터 타입: {data_type} (업종지수)")
                        
                        # 0J 업종지수 데이터 구조
                        current_value = values.get('10', 'N/A')    # 현재 지수값
                        change_value = values.get('11', 'N/A')     # 전일대비
                        change_rate = values.get('12', 'N/A')      # 등락율
                        volume = values.get('15', 'N/A')           # 거래량
                        total_volume = values.get('13', 'N/A')     # 누적거래량
                        total_amount = values.get('14', 'N/A')     # 누적거래대금
                        open_price = values.get('16', 'N/A')       # 시가
                        high_price = values.get('17', 'N/A')       # 고가  
                        low_price = values.get('18', 'N/A')        # 저가
                        time = values.get('20', 'N/A')             # 체결시간
                        
                        logger.info(f"   💰 지수: {current_value}, 대비: {change_value} ({change_rate}%)")
                        logger.info(f"   📊 거래량: {volume}, 누적거래량: {total_volume}")
                        logger.info(f"   💸 누적거래대금: {total_amount}")
                        logger.info(f"   📈 시/고/저: {open_price}/{high_price}/{low_price}")
                        logger.info(f"   ⏰ 체결시간: {time}")
                        
                        # 모든 values 키-값 로깅 (디버깅용)
                        logger.debug(f"   🔍 전체 데이터: {values}")
                        
                    elif is_sector and is_sector_type:
                        logger.info(f"📊 업종 관련 데이터:")
                        logger.info(f"   🏢 업종: {data_name} ({item_code})")
                        logger.info(f"   📈 데이터 타입: {data_type}")
                        
                        if data_type == '0B':  # 체결 데이터
                            current_price = values.get('10', 'N/A')
                            price_change = values.get('11', 'N/A') 
                            change_rate = values.get('12', 'N/A')
                            volume = values.get('15', 'N/A')
                            logger.info(f"   💰 현재가: {current_price}, 대비: {price_change} ({change_rate}%), 거래량: {volume}")
                            
                        elif data_type == '0D':  # 지수 데이터
                            index_value = values.get('10', 'N/A')
                            index_change = values.get('11', 'N/A')
                            change_rate = values.get('12', 'N/A')
                            trading_value = values.get('14', 'N/A')
                            logger.info(f"   📈 지수: {index_value}, 대비: {index_change} ({change_rate}%), 거래대금: {trading_value}")
                            
                        elif data_type == '0E':  # 예상체결
                            expected_price = values.get('10', 'N/A')
                            expected_change = values.get('11', 'N/A')
                            logger.info(f"   🔮 예상가: {expected_price}, 예상대비: {expected_change}")
                    
                    else:
                        # 일반 종목 데이터는 기본 로깅
                        logger.debug(f"📈 종목 데이터: {data_name} ({item_code}) - {data_type}")
            
            # 원본 키움 데이터에 타임스탬프 추가
            original_message = {
                "type": "kiwoom_realtime",
                "timestamp": datetime.now().isoformat(),
                "original_data": data  # 키움 원본 데이터 그대로 전달
            }
            
            # 모든 연결된 웹 클라이언트에게 원본 데이터 브로드캐스트
            asyncio.create_task(self.broadcast(original_message))
            logger.debug(f"📡 키움 실시간 원본 데이터 브로드캐스트: {trnm}")
                
        except Exception as e:
            logger.error(f"❌ 실시간 데이터 처리 오류: {e}")
    
    def _convert_to_web_format(self, kiwoom_data: Dict) -> Dict:
        """키움 데이터를 웹 클라이언트 친화적 포맷으로 변환"""
        try:
            trnm = kiwoom_data.get('trnm', 'UNKNOWN')
            
            if trnm == 'REAL':
                # REAL 메시지 처리
                data_list = kiwoom_data.get('data', [])
                converted_items = []
                
                for item in data_list:
                    stock_code = item.get('item', 'N/A')
                    data_type = item.get('type', 'N/A')
                    data_name = item.get('name', 'Unknown')
                    values = item.get('values', {})
                    
                    if data_type == '0B':  # 주식체결
                        current_price = values.get('10', 'N/A')      # 현재가
                        price_change = values.get('11', 'N/A')      # 전일대비
                        change_rate = values.get('12', 'N/A')       # 등락율
                        volume = values.get('15', 'N/A')            # 거래량
                        trading_volume = values.get('13', 'N/A')    # 누적거래량
                        
                        # 종목명 매핑
                        stock_name = {
                            '005930': '삼성전자',
                            '000660': 'SK하이닉스'
                        }.get(stock_code, stock_code)
                        
                        # 상승/하락 트렌드
                        trend = 'up' if current_price.startswith('+') else 'down' if current_price.startswith('-') else 'flat'
                        
                        # + 또는 - 기호 제거
                        clean_price = current_price.replace('+', '').replace('-', '') if current_price not in ['N/A'] else current_price
                        
                        converted_items.append({
                            'type': 'stock_trade',
                            'stock_code': stock_code,
                            'stock_name': stock_name,
                            'current_price': clean_price,
                            'price_change': price_change,
                            'change_rate': change_rate,
                            'volume': volume,
                            'trading_volume': trading_volume,
                            'trend': trend,
                            'timestamp': datetime.now().isoformat()
                        })
                    
                    elif data_type == '0A':  # 주식호가
                        ask_price_1 = values.get('41', 'N/A')  # 매도1호가
                        bid_price_1 = values.get('51', 'N/A')  # 매수1호가
                        ask_vol_1 = values.get('61', 'N/A')    # 매도1수량
                        bid_vol_1 = values.get('71', 'N/A')    # 매수1수량
                        
                        # 종목명 매핑
                        stock_name = {
                            '005930': '삼성전자',
                            '000660': 'SK하이닉스'
                        }.get(stock_code, stock_code)
                        
                        converted_items.append({
                            'type': 'stock_orderbook',
                            'stock_code': stock_code,
                            'stock_name': stock_name,
                            'ask_price': ask_price_1,
                            'bid_price': bid_price_1,
                            'ask_volume': ask_vol_1,
                            'bid_volume': bid_vol_1,
                            'timestamp': datetime.now().isoformat()
                        })
                
                if converted_items:
                    return {
                        'event': 'realtime_data',
                        'data': converted_items
                    }
            
            elif trnm in ['0A', '0B']:
                # 레거시 형식 처리
                return {
                    'event': 'realtime_data_legacy',
                    'type': trnm,
                    'data': kiwoom_data
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 웹 포맷 변환 오류: {e}")
            return None
    
    async def broadcast(self, message: Dict):
        """모든 연결된 클라이언트에게 메시지 브로드캐스트"""
        if not self.active_connections:
            return
            
        message_json = json.dumps(message, ensure_ascii=False)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(f"⚠️ 클라이언트 전송 실패: {e}")
                disconnected.append(connection)
        
        # 연결 끊어진 클라이언트 정리
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_to_client(self, websocket: WebSocket, message: Dict):
        """특정 클라이언트에게 메시지 전송"""
        try:
            message_json = json.dumps(message, ensure_ascii=False)
            await websocket.send_text(message_json)
        except Exception as e:
            logger.error(f"메시지 전송 실패: {e}")
            # 연결이 끊어진 경우 정리
            if websocket in self.active_connections:
                self.disconnect(websocket)
    
    async def send_personal_message(self, message: Dict, websocket: WebSocket):
        """특정 클라이언트에게 메시지 전송 (별칭)"""
        await self.send_to_client(websocket, message)
    
    async def handle_registration(self, websocket: WebSocket, message: Dict):
        """종목 등록 요청 처리"""
        try:
            # 키움 REG 메시지 형태로 변환
            grp_no = message.get('grp_no', '1')
            refresh = message.get('refresh', '0')  # 기본값: 기존 구독 해지하고 새로 구독 ('0')
            data_list = message.get('data', [])
            
            if not data_list:
                await self.send_to_client(websocket, {
                    'trnm': 'REG',
                    'return_code': 1,
                    'return_msg': '등록할 데이터가 없습니다',
                    'timestamp': datetime.now().isoformat()
                })
                return
                
            # 키움 클라이언트가 연결되어 있는지 확인
            if not self.realtime_client or not self.is_realtime_running:
                await self.send_to_client(websocket, {
                    'trnm': 'REG',
                    'return_code': 1, 
                    'return_msg': '키움 실시간 클라이언트가 연결되지 않았습니다',
                    'timestamp': datetime.now().isoformat()
                })
                return
                
            # 각 데이터 항목 처리
            for data_item in data_list:
                items = data_item.get('item', [])
                types = data_item.get('type', [])
                
                if not items or not types:
                    continue
                    
                # 문자열로 온 경우 리스트로 변환
                if isinstance(items, str):
                    items = [items]
                if isinstance(types, str):
                    types = [types]
                
                # 업종 지수 등록 요청 로깅 (실제 키움 형식: 숫자 3자리 + 0J 타입)
                sector_items = [item for item in items if (len(item) == 3 and item.isdigit()) or item.startswith('KRX:')]
                sector_types = [t for t in types if t == '0J']  # 업종지수 타입
                
                if sector_items and sector_types:
                    logger.info(f"📊 업종 지수 등록 요청:")
                    logger.info(f"   🏢 업종 코드: {sector_items}")
                    logger.info(f"   📈 데이터 타입: {types} (업종지수: {sector_types})")
                    logger.info(f"   🔄 새로고침 모드: {'기존 유지' if refresh == '1' else '기존 해지'}")
                elif sector_items:
                    logger.info(f"📊 업종 관련 등록 요청:")
                    logger.info(f"   🏢 코드: {sector_items}")  
                    logger.info(f"   📈 데이터 타입: {types}")
                
                regular_items = [item for item in items if not ((len(item) == 3 and item.isdigit()) or item.startswith('KRX:'))]
                if regular_items:
                    logger.debug(f"📈 일반 종목 등록: {regular_items} -> {types}")
                
                try:
                    # 키움 실시간 클라이언트에 구독 요청 (refresh 파라미터 전달)
                    success = await self.realtime_client.subscribe(items, types, refresh)
                    
                    if success:
                        # 클라이언트별 구독 정보 업데이트
                        if websocket not in self.client_subscriptions:
                            self.client_subscriptions[websocket] = set()
                        
                        for item in items:
                            for data_type in types:
                                self.client_subscriptions[websocket].add(f"{item}:{data_type}")
                        
                        logger.info(f"📊 종목 구독 완료: {items} -> {types}")
                        
                    else:
                        await self.send_to_client(websocket, {
                            'trnm': 'REG',
                            'return_code': 1,
                            'return_msg': f'종목 구독 실패: {items}',
                            'timestamp': datetime.now().isoformat()
                        })
                        return
                        
                except Exception as e:
                    logger.error(f"❌ 종목 구독 오류: {e}")
                    await self.send_to_client(websocket, {
                        'trnm': 'REG',
                        'return_code': 1,
                        'return_msg': f'종목 구독 오류: {str(e)}',
                        'timestamp': datetime.now().isoformat()
                    })
                    return
            
            # 성공 응답
            await self.send_to_client(websocket, {
                'trnm': 'REG',
                'return_code': 0,
                'return_msg': '종목 등록 성공',
                'grp_no': grp_no,
                'data': data_list,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ 종목 등록 처리 오류: {e}")
            await self.send_to_client(websocket, {
                'trnm': 'REG',
                'return_code': 1,
                'return_msg': f'등록 처리 오류: {str(e)}',
                'timestamp': datetime.now().isoformat()
            })
    
    async def handle_removal(self, websocket: WebSocket, message: Dict):
        """종목 해지 요청 처리"""
        try:
            grp_no = message.get('grp_no', '1')
            data_list = message.get('data', [])
            
            if not data_list:
                # 전체 해지
                if websocket in self.client_subscriptions:
                    self.client_subscriptions[websocket].clear()
                    
                await self.send_to_client(websocket, {
                    'trnm': 'REMOVE',
                    'return_code': 0,
                    'return_msg': '전체 구독 해지 완료',
                    'grp_no': grp_no,
                    'timestamp': datetime.now().isoformat()
                })
                return
            
            # 특정 종목 해지
            removed_items = []
            for data_item in data_list:
                items = data_item.get('item', [])
                types = data_item.get('type', [])
                
                if isinstance(items, str):
                    items = [items]
                if isinstance(types, str):
                    types = [types]
                
                if websocket in self.client_subscriptions:
                    for item in items:
                        for data_type in types:
                            subscription_key = f"{item}:{data_type}"
                            if subscription_key in self.client_subscriptions[websocket]:
                                self.client_subscriptions[websocket].remove(subscription_key)
                                removed_items.append(subscription_key)
            
            # 성공 응답
            await self.send_to_client(websocket, {
                'trnm': 'REMOVE',
                'return_code': 0,
                'return_msg': f'구독 해지 완료: {len(removed_items)}개 항목',
                'grp_no': grp_no,
                'removed_items': removed_items,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"📊 종목 구독 해지 완료: {removed_items}")
            
        except Exception as e:
            logger.error(f"❌ 종목 해지 처리 오류: {e}")
            await self.send_to_client(websocket, {
                'trnm': 'REMOVE',
                'return_code': 1,
                'return_msg': f'해지 처리 오류: {str(e)}',
                'timestamp': datetime.now().isoformat()
            })

# 전역 연결 관리자
manager = ConnectionManager()

@router.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """실시간 시세 WebSocket 엔드포인트"""
    await manager.connect(websocket)
    
    try:
        while True:
            # 연결 유지를 위한 간단한 대기 루프
            try:
                # 1초 타임아웃으로 메시지 대기
                data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                
                # 메시지 처리 (ping/pong 등)
                try:
                    message = json.loads(data)
                    command = message.get('command', '')
                    
                    if command == 'ping':
                        await manager.send_to_client(websocket, {
                            'event': 'pong',
                            'timestamp': datetime.now().isoformat()
                        })
                        
                    elif command == 'REG':
                        # 종목 등록 요청
                        await manager.handle_registration(websocket, message)
                        
                    elif command == 'REMOVE':
                        # 종목 해지 요청  
                        await manager.handle_removal(websocket, message)
                        
                    elif command == 'subscribe':
                        # 구독 요청 처리 (레거시)
                        await manager.send_to_client(websocket, {
                            'event': 'subscribe_ok',
                            'message': '구독 요청을 받았습니다 (REG 명령어 사용 권장)',
                            'timestamp': datetime.now().isoformat()
                        })
                        
                except json.JSONDecodeError:
                    await manager.send_to_client(websocket, {
                        'event': 'error',
                        'message': 'JSON 파싱 오류'
                    })
                    
            except asyncio.TimeoutError:
                # 타임아웃은 정상 - 연결 유지를 위해 계속 루프
                continue
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)

@router.get("/ws/test")
async def websocket_test_page():
    """WebSocket 테스트 페이지"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>키움 실시간 시세 WebSocket 테스트</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 800px; }
            .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
            .connected { background-color: #d4edda; border: 1px solid #c3e6cb; }
            .disconnected { background-color: #f8d7da; border: 1px solid #f5c6cb; }
            .message-box { border: 1px solid #ccc; height: 400px; overflow-y: auto; padding: 10px; background: #f8f9fa; }
            .stock-item { margin: 5px 0; padding: 5px; border: 1px solid #ddd; border-radius: 3px; }
            .stock-up { background-color: #ffe6e6; }
            .stock-down { background-color: #e6f3ff; }
            button { padding: 8px 16px; margin: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 키움 실시간 시세 WebSocket 테스트</h1>
            
            <div id="status" class="status disconnected">
                연결 안됨
            </div>
            
            <button onclick="connect()">연결</button>
            <button onclick="disconnect()">연결 해제</button>
            <button onclick="subscribe()">종목 구독</button>
            <button onclick="ping()">Ping 테스트</button>
            <button onclick="clearMessages()">메시지 지우기</button>
            
            <h3>📊 실시간 데이터</h3>
            <div id="messages" class="message-box">
                연결을 시작하면 실시간 데이터가 표시됩니다...
            </div>
        </div>

        <script>
            let socket = null;
            let messageCount = 0;
            
            function updateStatus(connected, message) {
                const status = document.getElementById('status');
                if (connected) {
                    status.className = 'status connected';
                    status.textContent = '✅ ' + message;
                } else {
                    status.className = 'status disconnected';
                    status.textContent = '❌ ' + message;
                }
            }
            
            function addMessage(content) {
                const messages = document.getElementById('messages');
                const time = new Date().toLocaleTimeString();
                messages.innerHTML += '<div class="message">[' + time + '] ' + content + '</div>';
                messages.scrollTop = messages.scrollHeight;
                messageCount++;
                
                // 메시지가 너무 많으면 일부 삭제
                if (messageCount > 100) {
                    const messageElements = messages.getElementsByClassName('message');
                    for (let i = 0; i < 20; i++) {
                        if (messageElements[0]) {
                            messageElements[0].remove();
                        }
                    }
                    messageCount = 80;
                }
            }
            
            function connect() {
                if (socket) {
                    socket.close();
                }
                
                socket = new WebSocket('ws://localhost:10201/ws/realtime');
                
                socket.onopen = function(event) {
                    updateStatus(true, '웹소켓 연결됨');
                    addMessage('🔗 WebSocket 연결 성공');
                };
                
                socket.onmessage = function(event) {
                    try {
                        const data = JSON.parse(event.data);
                        
                        if (data.event === 'connected') {
                            addMessage('🎉 키움 실시간 서비스 연결: ' + data.message);
                            addMessage('📊 모드: ' + data.info.mode + ', 지원 종목: ' + data.info.available_stocks.join(', '));
                        }
                        else if (data.event === 'realtime_data') {
                            // 실시간 데이터 표시
                            data.data.forEach(item => {
                                if (item.type === 'stock_trade') {
                                    const trend = item.trend === 'up' ? '📈' : item.trend === 'down' ? '📉' : '➡️';
                                    const color = item.trend === 'up' ? 'stock-up' : 'stock-down';
                                    addMessage(
                                        '<div class="stock-item ' + color + '">' +
                                        trend + ' [' + item.stock_name + '] ' +
                                        '현재가: ' + item.current_price + '원 (' +
                                        item.price_change + ', ' + item.change_rate + '%) ' +
                                        '거래량: ' + item.volume + '주' +
                                        '</div>'
                                    );
                                }
                                else if (item.type === 'stock_orderbook') {
                                    addMessage(
                                        '<div class="stock-item">' +
                                        '📊 [' + item.stock_name + '] 호가 - ' +
                                        '매도: ' + item.ask_price + '(' + item.ask_volume + ') / ' +
                                        '매수: ' + item.bid_price + '(' + item.bid_volume + ')' +
                                        '</div>'
                                    );
                                }
                            });
                        }
                        else if (data.event === 'subscribe_response') {
                            addMessage('📝 구독 응답: ' + data.message + ' (성공: ' + data.success + ')');
                        }
                        else if (data.event === 'pong') {
                            addMessage('🏓 Pong 수신');
                        }
                        else {
                            addMessage('📨 메시지: ' + JSON.stringify(data));
                        }
                    } catch (e) {
                        addMessage('❌ JSON 파싱 오류: ' + event.data);
                    }
                };
                
                socket.onclose = function(event) {
                    updateStatus(false, '연결 끊어짐 (코드: ' + event.code + ')');
                    addMessage('🔌 WebSocket 연결 종료');
                };
                
                socket.onerror = function(error) {
                    updateStatus(false, '연결 오류');
                    addMessage('❌ WebSocket 오류: ' + error);
                };
            }
            
            function disconnect() {
                if (socket) {
                    socket.close();
                }
            }
            
            function subscribe() {
                if (socket && socket.readyState === WebSocket.OPEN) {
                    // REG 명령어로 업종지수 + 종목정보 구독
                    const message = {
                        command: 'REG',
                        grp_no: '1',
                        refresh: '0',
                        data: [{
                            item: [
                                '001',    // KOSPI 지수
                                '028',    // 코스피200
                                '005930', // 삼성전자
                                '000660', // SK하이닉스
                                '373220'  // LG에너지솔루션
                            ],
                            type: [
                                '0J',  // 업종지수
                                '0U',  // 업종등락
                                '0B',  // 주식체결
                                '0g'   // 주식종목정보
                            ]
                        }]
                    };
                    socket.send(JSON.stringify(message));
                    addMessage('📤 REG 구독 요청 전송: 업종지수 + 종목정보');
                    addMessage('🏢 업종: KOSPI(001), 코스피200(028)');
                    addMessage('📈 종목: 삼성전자, SK하이닉스, LG에너지솔루션');
                } else {
                    addMessage('❌ WebSocket이 연결되지 않았습니다');
                }
            }
            
            function ping() {
                if (socket && socket.readyState === WebSocket.OPEN) {
                    socket.send(JSON.stringify({command: 'ping'}));
                    addMessage('📤 Ping 전송');
                } else {
                    addMessage('❌ WebSocket이 연결되지 않았습니다');
                }
            }
            
            function clearMessages() {
                document.getElementById('messages').innerHTML = '';
                messageCount = 0;
            }
            
            // 페이지 로드 시 자동 연결
            window.onload = function() {
                addMessage('🌟 페이지 로드됨. "연결" 버튼을 눌러 시작하세요.');
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)