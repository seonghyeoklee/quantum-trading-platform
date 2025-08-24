"""
실시간 WebSocket 데이터를 Kafka 이벤트로 변환하는 트랜스포머

키움 WebSocket 메시지를 표준화된 이벤트 스키마로 변환
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

from .event_schemas import (
    StockTradeEvent,
    StockPriceEvent, 
    OrderBookEvent,
    ScreeningSignalEvent,
    EventType
)

logger = logging.getLogger(__name__)


class RealtimeEventTransformer:
    """실시간 데이터 → 이벤트 변환기"""
    
    def __init__(self):
        self.type_mappings = {
            '0B': self._transform_trade_event,      # 주식체결
            '0A': self._transform_price_event,      # 현재가
            '00': self._transform_orderbook_event,  # 호가
            '0D': self._transform_daily_info_event, # 일일정보
            # TODO: 추가 타입들도 구현 가능
        }
        
    async def transform_websocket_message(
        self, 
        ws_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """WebSocket 메시지를 이벤트 리스트로 변환"""
        events = []
        
        try:
            trnm = ws_data.get('trnm', '')
            
            if trnm == 'REAL':
                # 실시간 데이터 처리
                events.extend(await self._process_realtime_data(ws_data))
            elif trnm in ['CNSRLST', 'CNSRREQ', 'CNSRCLR']:
                # TR 명령어 결과 처리
                event = await self._process_tr_response(ws_data)
                if event:
                    events.append(event)
            else:
                logger.debug(f"변환하지 않는 메시지 타입: {trnm}")
                
        except Exception as e:
            logger.error(f"WebSocket 메시지 변환 실패: {e}")
            
        return events
        
    async def _process_realtime_data(self, ws_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """실시간 데이터 처리"""
        events = []
        
        data_list = ws_data.get('data', [])
        if not data_list:
            return events
            
        for data_item in data_list:
            try:
                symbol = data_item.get('symbol', '')
                realtime_type = data_item.get('type', '')
                values = data_item.get('values', {})
                
                if not symbol or not realtime_type:
                    continue
                    
                # 타입별 변환 함수 호출
                transformer = self.type_mappings.get(realtime_type)
                if transformer:
                    event = await transformer(symbol, values)
                    if event:
                        events.append(event.model_dump())
                else:
                    logger.debug(f"지원하지 않는 실시간 타입: {realtime_type}")
                    
            except Exception as e:
                logger.error(f"실시간 데이터 항목 변환 실패: {e}")
                
        return events
        
    async def _transform_trade_event(
        self, 
        symbol: str, 
        values: Dict[str, Any]
    ) -> Optional[StockTradeEvent]:
        """체결 데이터 (0B) → StockTradeEvent"""
        try:
            # 키움 실시간 체결 데이터 필드 매핑
            price = int(values.get('현재가', 0))
            volume = int(values.get('거래량', 0))
            trade_time = values.get('시간', datetime.now().strftime('%H%M%S'))
            change = int(values.get('전일대비', 0))
            change_rate = float(values.get('등락율', 0.0))
            cumulative_volume = int(values.get('누적거래량', 0))
            
            return StockTradeEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                symbol=symbol,
                price=price,
                volume=volume,
                trade_time=trade_time,
                change=change,
                change_rate=change_rate,
                cumulative_volume=cumulative_volume,
                market_status=values.get('장구분'),
                trade_type=values.get('거래구분')
            )
            
        except Exception as e:
            logger.error(f"체결 이벤트 변환 실패 ({symbol}): {e}")
            return None
            
    async def _transform_price_event(
        self, 
        symbol: str, 
        values: Dict[str, Any]
    ) -> Optional[StockPriceEvent]:
        """현재가 데이터 (0A) → StockPriceEvent"""
        try:
            current_price = int(values.get('현재가', 0))
            change = int(values.get('전일대비', 0))
            change_rate = float(values.get('등락율', 0.0))
            open_price = int(values.get('시가', 0))
            high_price = int(values.get('고가', 0))
            low_price = int(values.get('저가', 0))
            prev_close = int(values.get('전일종가', 0))
            volume = int(values.get('거래량', 0))
            amount = int(values.get('거래대금', 0))
            
            return StockPriceEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                symbol=symbol,
                current_price=current_price,
                change=change,
                change_rate=change_rate,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                prev_close=prev_close,
                volume=volume,
                amount=amount,
                market_cap=values.get('시가총액'),
                shares_outstanding=values.get('상장주식수')
            )
            
        except Exception as e:
            logger.error(f"현재가 이벤트 변환 실패 ({symbol}): {e}")
            return None
            
    async def _transform_orderbook_event(
        self, 
        symbol: str, 
        values: Dict[str, Any]
    ) -> Optional[OrderBookEvent]:
        """호가 데이터 (00) → OrderBookEvent"""
        try:
            # 매수/매도 호가 10단계 (1~10)
            bid_prices = []
            bid_volumes = []
            ask_prices = []
            ask_volumes = []
            
            for i in range(1, 11):  # 1호가 ~ 10호가
                # 매수 호가
                bid_price = int(values.get(f'매수호가{i}', 0))
                bid_volume = int(values.get(f'매수호가수량{i}', 0))
                bid_prices.append(bid_price)
                bid_volumes.append(bid_volume)
                
                # 매도 호가  
                ask_price = int(values.get(f'매도호가{i}', 0))
                ask_volume = int(values.get(f'매도호가수량{i}', 0))
                ask_prices.append(ask_price)
                ask_volumes.append(ask_volume)
                
            total_bid_volume = int(values.get('매수호가총수량', sum(bid_volumes)))
            total_ask_volume = int(values.get('매도호가총수량', sum(ask_volumes)))
            
            return OrderBookEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                symbol=symbol,
                bid_prices=bid_prices,
                bid_volumes=bid_volumes,
                ask_prices=ask_prices,
                ask_volumes=ask_volumes,
                total_bid_volume=total_bid_volume,
                total_ask_volume=total_ask_volume
            )
            
        except Exception as e:
            logger.error(f"호가 이벤트 변환 실패 ({symbol}): {e}")
            return None
            
    async def _transform_daily_info_event(
        self, 
        symbol: str, 
        values: Dict[str, Any]
    ) -> Optional[StockPriceEvent]:
        """일일정보 데이터 (0D) → StockPriceEvent (확장)"""
        # 일일정보는 현재가와 유사하므로 StockPriceEvent로 변환
        return await self._transform_price_event(symbol, values)
        
    async def _process_tr_response(self, ws_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """TR 명령어 응답 → ScreeningSignalEvent"""
        try:
            tr_name = ws_data.get('trnm')
            
            if tr_name == 'CNSRREQ':
                # 조건검색 결과
                return await self._transform_screening_result(ws_data)
            elif tr_name == 'SCREENER_REALTIME':
                # 실시간 조건검색 알림
                return await self._transform_screening_signal(ws_data)
            else:
                logger.debug(f"변환하지 않는 TR: {tr_name}")
                return None
                
        except Exception as e:
            logger.error(f"TR 응답 변환 실패: {e}")
            return None
            
    async def _transform_screening_result(self, ws_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """조건검색 결과 변환"""
        try:
            # TR 결과에서 필요한 정보 추출
            data = ws_data.get('data', {})
            
            event = ScreeningSignalEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                condition_seq=data.get('seq', ''),
                condition_name=data.get('condition_name', ''),
                symbol=data.get('stock_code', ''),
                stock_name=data.get('stock_name', ''),
                signal_type='screening_result',
                action_code=data.get('action', ''),
                action_description='조건검색 결과',
                current_price=data.get('current_price'),
                signal_time=data.get('signal_time')
            )
            
            return event.model_dump()
            
        except Exception as e:
            logger.error(f"조건검색 결과 변환 실패: {e}")
            return None
            
    async def _transform_screening_signal(self, ws_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """실시간 조건검색 신호 변환"""
        try:
            data = ws_data.get('data', {})
            
            event = ScreeningSignalEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                condition_seq=data.get('condition_seq', ''),
                condition_name=data.get('condition_name', ''),
                symbol=data.get('stock_code', ''),
                stock_name=data.get('stock_name', ''),
                signal_type='realtime_signal',
                action_code=data.get('action_code', ''),
                action_description=data.get('action_description', ''),
                current_price=data.get('current_price'),
                signal_time=datetime.now().strftime('%H%M%S')
            )
            
            return event.model_dump()
            
        except Exception as e:
            logger.error(f"실시간 신호 변환 실패: {e}")
            return None