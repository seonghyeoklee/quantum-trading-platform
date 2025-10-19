"""
데이터 관리 서비스

실시간 데이터 수집, 기술적 지표 계산, 시장 미시구조 분석을 담당합니다.
"""

import asyncio
import websockets
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from ..models import CandleData, OrderBookData, TechnicalIndicators
from ..config import settings
# from ..utils.kis_client import KISClient
# from ..utils.database import DatabaseManager

@dataclass
class MarketDataPoint:
    """시장 데이터 포인트"""
    symbol: str
    timestamp: datetime
    price: float
    volume: int
    bid_price: float
    ask_price: float
    bid_volume: int
    ask_volume: int

class DataManager:
    """데이터 관리 메인 클래스"""
    
    def __init__(self):
        self.is_collecting = False
        self.websocket_connections = {}
        self.candle_buffers = {}  # 5분봉 집계용 버퍼
        self.orderbook_cache = {}  # 호가창 캐시
        
        # TODO: 외부 서비스 초기화
        # self.kis_client = KISClient()
        # self.db_manager = DatabaseManager()
        
        # 기술적 지표 계산용 데이터 저장소
        self.price_history = {}  # 종목별 가격 히스토리
        self.volume_history = {}  # 종목별 거래량 히스토리
        
    async def start_realtime_collection(self):
        """실시간 데이터 수집 시작"""
        
        if self.is_collecting:
            return
            
        print("🚀 실시간 데이터 수집 시작...")
        self.is_collecting = True
        
        try:
            # TODO: KIS WebSocket 연결
            # await self._connect_kis_websocket()
            
            # TODO: 관심종목 구독
            for symbol in settings.watchlist:
                await self._subscribe_symbol(symbol)
                
            # TODO: 데이터 처리 태스크 시작
            asyncio.create_task(self._process_realtime_data())
            asyncio.create_task(self._aggregate_candles())
            
            print("✅ 실시간 데이터 수집 시작 완료")
            
        except Exception as e:
            print(f"❌ 실시간 데이터 수집 시작 실패: {e}")
            self.is_collecting = False
            raise
    
    async def stop_realtime_collection(self):
        """실시간 데이터 수집 중지"""
        
        print("🛑 실시간 데이터 수집 중지...")
        self.is_collecting = False
        
        # TODO: WebSocket 연결 해제
        # for connection in self.websocket_connections.values():
        #     await connection.close()
        
        self.websocket_connections.clear()
        print("✅ 실시간 데이터 수집 중지 완료")
    
    async def _connect_kis_websocket(self):
        """KIS WebSocket 연결"""
        
        try:
            # TODO: KIS WebSocket 인증 및 연결
            # websocket_url = settings.kis_websocket_url
            # auth_token = await self.kis_client.get_websocket_token()
            
            # connection = await websockets.connect(
            #     websocket_url,
            #     extra_headers={"Authorization": f"Bearer {auth_token}"}
            # )
            
            # self.websocket_connections['main'] = connection
            print("✅ KIS WebSocket 연결 완료")
            
        except Exception as e:
            print(f"❌ KIS WebSocket 연결 실패: {e}")
            raise
    
    async def _subscribe_symbol(self, symbol: str):
        """종목 구독"""
        
        try:
            # TODO: 실시간 시세 구독 메시지 전송
            subscribe_message = {
                "header": {
                    "approval_key": "approval_key_here",  # TODO: 실제 승인키
                    "custtype": "P",
                    "tr_type": "1",  # 등록
                    "content-type": "utf-8"
                },
                "body": {
                    "input": {
                        "tr_id": "H0STCNT0",  # 실시간 체결가
                        "tr_key": symbol
                    }
                }
            }
            
            # TODO: WebSocket으로 구독 메시지 전송
            # connection = self.websocket_connections.get('main')
            # if connection:
            #     await connection.send(json.dumps(subscribe_message))
            
            print(f"📡 종목 구독 완료: {symbol}")
            
            # 호가창 구독도 추가
            await self._subscribe_orderbook(symbol)
            
        except Exception as e:
            print(f"❌ 종목 구독 실패 {symbol}: {e}")
    
    async def _subscribe_orderbook(self, symbol: str):
        """호가창 구독"""
        
        try:
            # TODO: 실시간 호가 구독 메시지 전송
            orderbook_message = {
                "header": {
                    "approval_key": "approval_key_here",
                    "custtype": "P", 
                    "tr_type": "1",
                    "content-type": "utf-8"
                },
                "body": {
                    "input": {
                        "tr_id": "H0STASP0",  # 실시간 호가
                        "tr_key": symbol
                    }
                }
            }
            
            # TODO: WebSocket으로 호가 구독 메시지 전송
            # connection = self.websocket_connections.get('main')
            # if connection:
            #     await connection.send(json.dumps(orderbook_message))
            
            print(f"📊 호가창 구독 완료: {symbol}")
            
        except Exception as e:
            print(f"❌ 호가창 구독 실패 {symbol}: {e}")
    
    async def _process_realtime_data(self):
        """실시간 데이터 처리 루프"""
        
        while self.is_collecting:
            try:
                # TODO: WebSocket에서 데이터 수신
                # connection = self.websocket_connections.get('main')
                # if not connection:
                #     await asyncio.sleep(1)
                #     continue
                
                # message = await connection.recv()
                # data = json.loads(message)
                
                # 임시 데이터 시뮬레이션
                await self._simulate_market_data()
                
                await asyncio.sleep(0.1)  # 100ms마다 체크
                
            except Exception as e:
                print(f"❌ 실시간 데이터 처리 오류: {e}")
                await asyncio.sleep(1)
    
    async def _simulate_market_data(self):
        """시장 데이터 시뮬레이션 (개발용)"""
        
        # 임시로 가상의 시장 데이터 생성
        for symbol in settings.watchlist:
            # 가격 데이터 시뮬레이션
            base_price = 75000 if symbol == "005930" else 50000
            price_change = np.random.normal(0, base_price * 0.001)  # 0.1% 표준편차
            current_price = base_price + price_change
            
            # 거래량 시뮬레이션
            volume = np.random.randint(1000, 10000)
            
            # 호가 데이터 시뮬레이션
            spread = current_price * 0.001  # 0.1% 스프레드
            bid_price = current_price - spread/2
            ask_price = current_price + spread/2
            
            # 데이터 포인트 생성
            data_point = MarketDataPoint(
                symbol=symbol,
                timestamp=datetime.now(),
                price=current_price,
                volume=volume,
                bid_price=bid_price,
                ask_price=ask_price,
                bid_volume=np.random.randint(100, 1000),
                ask_volume=np.random.randint(100, 1000)
            )
            
            # 데이터 처리
            await self._process_market_data_point(data_point)
    
    async def _process_market_data_point(self, data_point: MarketDataPoint):
        """개별 시장 데이터 포인트 처리"""
        
        symbol = data_point.symbol
        
        # 가격 히스토리 업데이트
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append({
            'timestamp': data_point.timestamp,
            'price': data_point.price,
            'volume': data_point.volume
        })
        
        # 최근 1000개 데이터만 유지
        if len(self.price_history[symbol]) > 1000:
            self.price_history[symbol] = self.price_history[symbol][-1000:]
        
        # 5분봉 버퍼에 추가
        await self._add_to_candle_buffer(data_point)
        
        # 호가창 캐시 업데이트
        self.orderbook_cache[symbol] = {
            'timestamp': data_point.timestamp,
            'bid_price': data_point.bid_price,
            'ask_price': data_point.ask_price,
            'bid_volume': data_point.bid_volume,
            'ask_volume': data_point.ask_volume
        }
    
    async def _add_to_candle_buffer(self, data_point: MarketDataPoint):
        """5분봉 버퍼에 데이터 추가"""
        
        symbol = data_point.symbol
        current_time = data_point.timestamp
        
        # 5분 단위로 시간 정규화 (예: 09:32:45 -> 09:30:00)
        candle_time = current_time.replace(
            minute=(current_time.minute // 5) * 5,
            second=0,
            microsecond=0
        )
        
        if symbol not in self.candle_buffers:
            self.candle_buffers[symbol] = {}
        
        if candle_time not in self.candle_buffers[symbol]:
            # 새로운 5분봉 시작
            self.candle_buffers[symbol][candle_time] = {
                'open': data_point.price,
                'high': data_point.price,
                'low': data_point.price,
                'close': data_point.price,
                'volume': data_point.volume,
                'count': 1
            }
        else:
            # 기존 5분봉 업데이트
            candle = self.candle_buffers[symbol][candle_time]
            candle['high'] = max(candle['high'], data_point.price)
            candle['low'] = min(candle['low'], data_point.price)
            candle['close'] = data_point.price
            candle['volume'] += data_point.volume
            candle['count'] += 1
    
    async def _aggregate_candles(self):
        """5분봉 집계 및 저장"""
        
        while self.is_collecting:
            try:
                current_time = datetime.now()
                
                for symbol in self.candle_buffers:
                    # 완성된 5분봉 찾기 (현재 시간보다 5분 이전)
                    completed_candles = []
                    
                    for candle_time, candle_data in list(self.candle_buffers[symbol].items()):
                        if current_time - candle_time >= timedelta(minutes=5):
                            completed_candles.append((candle_time, candle_data))
                    
                    # 완성된 캔들 처리
                    for candle_time, candle_data in completed_candles:
                        await self._save_completed_candle(symbol, candle_time, candle_data)
                        
                        # 버퍼에서 제거
                        del self.candle_buffers[symbol][candle_time]
                
                await asyncio.sleep(60)  # 1분마다 체크
                
            except Exception as e:
                print(f"❌ 5분봉 집계 오류: {e}")
                await asyncio.sleep(60)
    
    async def _save_completed_candle(self, symbol: str, candle_time: datetime, candle_data: dict):
        """완성된 5분봉 저장"""
        
        try:
            # CandleData 객체 생성
            candle = CandleData(
                symbol=symbol,
                timestamp=candle_time,
                open_price=candle_data['open'],
                high_price=candle_data['high'],
                low_price=candle_data['low'],
                close_price=candle_data['close'],
                volume=candle_data['volume'],
                amount=candle_data['close'] * candle_data['volume']  # 근사치
            )
            
            # TODO: 데이터베이스에 저장
            # await self.db_manager.save_candle(candle)
            
            print(f"💾 5분봉 저장 완료: {symbol} {candle_time} OHLCV({candle_data['open']:.0f}, {candle_data['high']:.0f}, {candle_data['low']:.0f}, {candle_data['close']:.0f}, {candle_data['volume']})")
            
            # 기술적 지표 계산 트리거
            await self._calculate_indicators_for_symbol(symbol)
            
        except Exception as e:
            print(f"❌ 5분봉 저장 실패 {symbol}: {e}")
    
    async def calculate_indicators(self, symbol: str) -> Optional[TechnicalIndicators]:
        """기술적 지표 계산"""
        
        try:
            return await self._calculate_indicators_for_symbol(symbol)
            
        except Exception as e:
            print(f"❌ 기술적 지표 계산 실패 {symbol}: {e}")
            return None
    
    async def _calculate_indicators_for_symbol(self, symbol: str) -> Optional[TechnicalIndicators]:
        """특정 종목의 기술적 지표 계산"""
        
        try:
            # 가격 히스토리에서 데이터 가져오기
            if symbol not in self.price_history or len(self.price_history[symbol]) < 50:
                return None
            
            # pandas DataFrame으로 변환
            df = pd.DataFrame(self.price_history[symbol])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # 기술적 지표 계산
            indicators = TechnicalIndicators(
                symbol=symbol,
                timestamp=datetime.now()
            )
            
            # 이동평균 계산
            if len(df) >= settings.ema_short_period:
                indicators.ema_5 = df['price'].ewm(span=settings.ema_short_period).mean().iloc[-1]
            
            if len(df) >= settings.ema_long_period:
                indicators.ema_20 = df['price'].ewm(span=settings.ema_long_period).mean().iloc[-1]
            
            # RSI 계산
            if len(df) >= settings.rsi_period + 1:
                indicators.rsi = self._calculate_rsi(df['price'], settings.rsi_period)
            
            # MACD 계산
            if len(df) >= settings.macd_slow:
                macd_line, macd_signal, macd_histogram = self._calculate_macd(
                    df['price'], 
                    settings.macd_fast, 
                    settings.macd_slow, 
                    settings.macd_signal
                )
                indicators.macd = macd_line
                indicators.macd_signal = macd_signal
                indicators.macd_histogram = macd_histogram
            
            # 볼린저 밴드 계산
            if len(df) >= settings.bb_period:
                bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(
                    df['price'], 
                    settings.bb_period, 
                    settings.bb_std_dev
                )
                indicators.bb_upper = bb_upper
                indicators.bb_middle = bb_middle
                indicators.bb_lower = bb_lower
            
            # VWAP 계산
            if len(df) >= 20:
                indicators.vwap = self._calculate_vwap(df['price'], df['volume'])
            
            # 거래량 이동평균
            if len(df) >= 20:
                indicators.volume_sma = df['volume'].rolling(window=20).mean().iloc[-1]
            
            return indicators
            
        except Exception as e:
            print(f"❌ 기술적 지표 계산 오류 {symbol}: {e}")
            return None
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> float:
        """RSI 계산"""
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1]
    
    def _calculate_macd(self, prices: pd.Series, fast: int, slow: int, signal: int) -> tuple:
        """MACD 계산"""
        
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        
        macd_line = ema_fast - ema_slow
        macd_signal = macd_line.ewm(span=signal).mean()
        macd_histogram = macd_line - macd_signal
        
        return (
            macd_line.iloc[-1],
            macd_signal.iloc[-1], 
            macd_histogram.iloc[-1]
        )
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int, std_dev: float) -> tuple:
        """볼린저 밴드 계산"""
        
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return (
            upper_band.iloc[-1],
            sma.iloc[-1],
            lower_band.iloc[-1]
        )
    
    def _calculate_vwap(self, prices: pd.Series, volumes: pd.Series) -> float:
        """VWAP 계산"""
        
        # 최근 20개 데이터로 VWAP 계산
        recent_prices = prices.tail(20)
        recent_volumes = volumes.tail(20)
        
        vwap = (recent_prices * recent_volumes).sum() / recent_volumes.sum()
        return vwap
    
    async def get_current_orderbook(self, symbol: str) -> Optional[OrderBookData]:
        """현재 호가창 데이터 조회"""
        
        try:
            if symbol not in self.orderbook_cache:
                return None
            
            cache_data = self.orderbook_cache[symbol]
            
            # TODO: 실제 호가창 데이터 구성 (임시로 단순화)
            orderbook = OrderBookData(
                symbol=symbol,
                timestamp=cache_data['timestamp'],
                ask_prices=[cache_data['ask_price']],
                ask_volumes=[cache_data['ask_volume']],
                bid_prices=[cache_data['bid_price']],
                bid_volumes=[cache_data['bid_volume']],
                total_ask_volume=cache_data['ask_volume'],
                total_bid_volume=cache_data['bid_volume']
            )
            
            return orderbook
            
        except Exception as e:
            print(f"❌ 호가창 데이터 조회 실패 {symbol}: {e}")
            return None
    
    async def health_check(self) -> bool:
        """데이터 관리자 상태 확인"""
        
        try:
            # 수집 상태 확인
            if not self.is_collecting:
                return False
            
            # WebSocket 연결 상태 확인
            # TODO: 실제 연결 상태 확인
            # if not self.websocket_connections:
            #     return False
            
            # 최근 데이터 수신 확인
            recent_data_count = 0
            for symbol_history in self.price_history.values():
                if symbol_history and (datetime.now() - symbol_history[-1]['timestamp']).seconds < 300:
                    recent_data_count += 1
            
            # 최소 1개 종목에서 최근 5분 내 데이터 수신되었는지 확인
            return recent_data_count > 0
            
        except Exception as e:
            print(f"❌ 데이터 관리자 헬스체크 실패: {e}")
            return False
