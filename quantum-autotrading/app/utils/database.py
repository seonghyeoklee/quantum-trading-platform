"""
데이터베이스 연동 모듈

Supabase를 통한 데이터 저장 및 조회를 담당합니다.
"""

import asyncio
import asyncpg
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from supabase import create_client, Client
import pandas as pd

from ..config import settings
from ..models import CandleData, TradingSignal, Order, Position

class DatabaseManager:
    """데이터베이스 관리 메인 클래스"""
    
    def __init__(self):
        # Supabase 클라이언트
        self.supabase_client = None
        
        # PostgreSQL 연결 풀
        self.pg_pool = None
        
        # 연결 상태
        self.is_connected = False
        
    async def initialize(self):
        """데이터베이스 연결 초기화"""
        
        try:
            # Supabase 클라이언트 초기화
            if settings.supabase_url and settings.supabase_key:
                self.supabase_client = create_client(
                    settings.supabase_url,
                    settings.supabase_key
                )
                print("✅ Supabase 클라이언트 초기화 완료")
            
            # PostgreSQL 연결 풀 생성 (선택적)
            if settings.database_url:
                self.pg_pool = await asyncpg.create_pool(
                    settings.database_url,
                    min_size=5,
                    max_size=20
                )
                print("✅ PostgreSQL 연결 풀 생성 완료")
            
            # 테이블 생성
            await self._create_tables()
            
            self.is_connected = True
            print("✅ 데이터베이스 초기화 완료")
            
        except Exception as e:
            print(f"❌ 데이터베이스 초기화 실패: {e}")
            self.is_connected = False
            raise
    
    async def close(self):
        """데이터베이스 연결 종료"""
        
        try:
            if self.pg_pool:
                await self.pg_pool.close()
                print("✅ PostgreSQL 연결 풀 종료 완료")
            
            self.is_connected = False
            print("✅ 데이터베이스 연결 종료 완료")
            
        except Exception as e:
            print(f"❌ 데이터베이스 연결 종료 실패: {e}")
    
    async def _create_tables(self):
        """필요한 테이블 생성"""
        
        try:
            # TODO: Supabase에서 테이블 생성 (SQL 실행)
            
            # 캔들 데이터 테이블
            candle_table_sql = """
            CREATE TABLE IF NOT EXISTS candle_data (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                timeframe VARCHAR(5) NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                open_price DECIMAL(10,2) NOT NULL,
                high_price DECIMAL(10,2) NOT NULL,
                low_price DECIMAL(10,2) NOT NULL,
                close_price DECIMAL(10,2) NOT NULL,
                volume BIGINT NOT NULL,
                amount DECIMAL(15,2) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                UNIQUE(symbol, timeframe, timestamp)
            );
            
            CREATE INDEX IF NOT EXISTS idx_candle_symbol_timeframe_timestamp 
            ON candle_data(symbol, timeframe, timestamp DESC);
            """
            
            # 매매 신호 테이블
            signal_table_sql = """
            CREATE TABLE IF NOT EXISTS trading_signals (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                signal_type VARCHAR(10) NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                strength DECIMAL(3,2) NOT NULL,
                confidence DECIMAL(3,2) NOT NULL,
                technical_score DECIMAL(3,2) NOT NULL,
                microstructure_score DECIMAL(3,2) NOT NULL,
                sentiment_score DECIMAL(3,2) NOT NULL,
                current_price DECIMAL(10,2) NOT NULL,
                target_price DECIMAL(10,2),
                stop_loss_price DECIMAL(10,2),
                reasoning TEXT NOT NULL,
                metadata JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_signals_symbol_timestamp 
            ON trading_signals(symbol, timestamp DESC);
            """
            
            # 주문 테이블
            order_table_sql = """
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                order_id VARCHAR(50) UNIQUE NOT NULL,
                symbol VARCHAR(10) NOT NULL,
                side VARCHAR(10) NOT NULL,
                order_type VARCHAR(20) NOT NULL,
                quantity INTEGER NOT NULL,
                price DECIMAL(10,2),
                status VARCHAR(20) NOT NULL,
                filled_quantity INTEGER DEFAULT 0,
                remaining_quantity INTEGER NOT NULL,
                avg_fill_price DECIMAL(10,2),
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
                filled_at TIMESTAMP WITH TIME ZONE
            );
            
            CREATE INDEX IF NOT EXISTS idx_orders_symbol_created_at 
            ON orders(symbol, created_at DESC);
            """
            
            # 포지션 테이블
            position_table_sql = """
            CREATE TABLE IF NOT EXISTS positions (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10) UNIQUE NOT NULL,
                quantity INTEGER NOT NULL,
                avg_price DECIMAL(10,2) NOT NULL,
                current_price DECIMAL(10,2) NOT NULL,
                unrealized_pnl DECIMAL(12,2) NOT NULL,
                unrealized_pnl_percent DECIMAL(5,2) NOT NULL,
                stop_loss_price DECIMAL(10,2),
                take_profit_price DECIMAL(10,2),
                opened_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL
            );
            """
            
            # 거래 내역 테이블
            trade_table_sql = """
            CREATE TABLE IF NOT EXISTS trades (
                id SERIAL PRIMARY KEY,
                trade_id VARCHAR(50) UNIQUE NOT NULL,
                symbol VARCHAR(10) NOT NULL,
                side VARCHAR(10) NOT NULL,
                quantity INTEGER NOT NULL,
                entry_price DECIMAL(10,2) NOT NULL,
                exit_price DECIMAL(10,2),
                pnl DECIMAL(12,2),
                pnl_percent DECIMAL(5,2),
                entry_time TIMESTAMP WITH TIME ZONE NOT NULL,
                exit_time TIMESTAMP WITH TIME ZONE,
                holding_time INTERVAL,
                strategy VARCHAR(50),
                signal_strength DECIMAL(3,2),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_trades_symbol_entry_time 
            ON trades(symbol, entry_time DESC);
            """
            
            # 성과 지표 테이블
            performance_table_sql = """
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id SERIAL PRIMARY KEY,
                date DATE UNIQUE NOT NULL,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                win_rate DECIMAL(5,2) DEFAULT 0,
                total_pnl DECIMAL(12,2) DEFAULT 0,
                total_pnl_percent DECIMAL(5,2) DEFAULT 0,
                best_trade DECIMAL(12,2) DEFAULT 0,
                worst_trade DECIMAL(12,2) DEFAULT 0,
                avg_trade_pnl DECIMAL(12,2) DEFAULT 0,
                profit_factor DECIMAL(5,2) DEFAULT 0,
                sharpe_ratio DECIMAL(5,2) DEFAULT 0,
                max_drawdown DECIMAL(5,2) DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
            
            # TODO: 실제로는 Supabase SQL 에디터나 마이그레이션으로 실행
            print("📋 데이터베이스 테이블 스키마 정의 완료")
            
        except Exception as e:
            print(f"❌ 테이블 생성 실패: {e}")
            raise
    
    # === 캔들 데이터 관련 메서드 ===
    
    async def save_candle(self, candle: CandleData) -> bool:
        """캔들 데이터 저장"""
        
        try:
            if not self.supabase_client:
                return False
            
            # TODO: Supabase에 캔들 데이터 저장
            candle_dict = {
                "symbol": candle.symbol,
                "timeframe": "5m",  # 5분봉 고정
                "timestamp": candle.timestamp.isoformat(),
                "open_price": float(candle.open_price),
                "high_price": float(candle.high_price),
                "low_price": float(candle.low_price),
                "close_price": float(candle.close_price),
                "volume": candle.volume,
                "amount": float(candle.amount)
            }
            
            # result = self.supabase_client.table("candle_data").upsert(candle_dict).execute()
            
            print(f"💾 캔들 데이터 저장: {candle.symbol} {candle.timestamp}")
            return True
            
        except Exception as e:
            print(f"❌ 캔들 데이터 저장 실패: {e}")
            return False
    
    async def get_candle_data(self, symbol: str, timeframe: str = "5m", 
                            limit: int = 100, start_date: Optional[datetime] = None) -> List[CandleData]:
        """캔들 데이터 조회"""
        
        try:
            if not self.supabase_client:
                return []
            
            # TODO: Supabase에서 캔들 데이터 조회
            query = self.supabase_client.table("candle_data").select("*").eq("symbol", symbol).eq("timeframe", timeframe)
            
            if start_date:
                query = query.gte("timestamp", start_date.isoformat())
            
            # result = query.order("timestamp", desc=True).limit(limit).execute()
            
            # 임시로 빈 리스트 반환
            return []
            
        except Exception as e:
            print(f"❌ 캔들 데이터 조회 실패: {e}")
            return []
    
    # === 매매 신호 관련 메서드 ===
    
    async def save_signal(self, signal: TradingSignal) -> bool:
        """매매 신호 저장"""
        
        try:
            if not self.supabase_client:
                return False
            
            # TODO: Supabase에 신호 데이터 저장
            signal_dict = {
                "symbol": signal.symbol,
                "signal_type": signal.signal_type.value,
                "timestamp": signal.timestamp.isoformat(),
                "strength": float(signal.strength),
                "confidence": float(signal.confidence),
                "technical_score": float(signal.technical_score),
                "microstructure_score": float(signal.microstructure_score),
                "sentiment_score": float(signal.sentiment_score),
                "current_price": float(signal.current_price),
                "target_price": float(signal.target_price) if signal.target_price else None,
                "stop_loss_price": float(signal.stop_loss_price) if signal.stop_loss_price else None,
                "reasoning": signal.reasoning,
                "metadata": signal.metadata
            }
            
            # result = self.supabase_client.table("trading_signals").insert(signal_dict).execute()
            
            print(f"📊 매매 신호 저장: {signal.symbol} {signal.signal_type.value}")
            return True
            
        except Exception as e:
            print(f"❌ 매매 신호 저장 실패: {e}")
            return False
    
    async def get_signals(self, symbol: Optional[str] = None, 
                         limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """매매 신호 조회"""
        
        try:
            if not self.supabase_client:
                return []
            
            # TODO: Supabase에서 신호 데이터 조회
            query = self.supabase_client.table("trading_signals").select("*")
            
            if symbol:
                query = query.eq("symbol", symbol)
            
            # result = query.order("timestamp", desc=True).range(offset, offset + limit - 1).execute()
            
            # 임시로 빈 리스트 반환
            return []
            
        except Exception as e:
            print(f"❌ 매매 신호 조회 실패: {e}")
            return []
    
    # === 주문 관련 메서드 ===
    
    async def save_order(self, order: Order) -> bool:
        """주문 데이터 저장"""
        
        try:
            if not self.supabase_client:
                return False
            
            # TODO: Supabase에 주문 데이터 저장
            order_dict = {
                "order_id": order.order_id,
                "symbol": order.symbol,
                "side": order.side.value,
                "order_type": order.order_type.value,
                "quantity": order.quantity,
                "price": float(order.price) if order.price else None,
                "status": order.status.value,
                "filled_quantity": order.filled_quantity,
                "remaining_quantity": order.remaining_quantity,
                "avg_fill_price": float(order.avg_fill_price) if order.avg_fill_price else None,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat(),
                "filled_at": order.filled_at.isoformat() if order.filled_at else None
            }
            
            # result = self.supabase_client.table("orders").upsert(order_dict).execute()
            
            print(f"📋 주문 데이터 저장: {order.order_id}")
            return True
            
        except Exception as e:
            print(f"❌ 주문 데이터 저장 실패: {e}")
            return False
    
    async def get_orders(self, symbol: Optional[str] = None, 
                        status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """주문 내역 조회"""
        
        try:
            if not self.supabase_client:
                return []
            
            # TODO: Supabase에서 주문 데이터 조회
            query = self.supabase_client.table("orders").select("*")
            
            if symbol:
                query = query.eq("symbol", symbol)
            if status:
                query = query.eq("status", status)
            
            # result = query.order("created_at", desc=True).limit(limit).execute()
            
            # 임시로 빈 리스트 반환
            return []
            
        except Exception as e:
            print(f"❌ 주문 내역 조회 실패: {e}")
            return []
    
    # === 포지션 관련 메서드 ===
    
    async def save_position(self, position: Position) -> bool:
        """포지션 데이터 저장"""
        
        try:
            if not self.supabase_client:
                return False
            
            # TODO: Supabase에 포지션 데이터 저장
            position_dict = {
                "symbol": position.symbol,
                "quantity": position.quantity,
                "avg_price": float(position.avg_price),
                "current_price": float(position.current_price),
                "unrealized_pnl": float(position.unrealized_pnl),
                "unrealized_pnl_percent": float(position.unrealized_pnl_percent),
                "stop_loss_price": float(position.stop_loss_price) if position.stop_loss_price else None,
                "take_profit_price": float(position.take_profit_price) if position.take_profit_price else None,
                "opened_at": position.opened_at.isoformat(),
                "updated_at": position.updated_at.isoformat()
            }
            
            # result = self.supabase_client.table("positions").upsert(position_dict).execute()
            
            print(f"📈 포지션 데이터 저장: {position.symbol}")
            return True
            
        except Exception as e:
            print(f"❌ 포지션 데이터 저장 실패: {e}")
            return False
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """현재 포지션 조회"""
        
        try:
            if not self.supabase_client:
                return []
            
            # TODO: Supabase에서 포지션 데이터 조회
            # result = self.supabase_client.table("positions").select("*").gt("quantity", 0).execute()
            
            # 임시로 빈 리스트 반환
            return []
            
        except Exception as e:
            print(f"❌ 포지션 조회 실패: {e}")
            return []
    
    async def delete_position(self, symbol: str) -> bool:
        """포지션 삭제 (청산 시)"""
        
        try:
            if not self.supabase_client:
                return False
            
            # TODO: Supabase에서 포지션 삭제
            # result = self.supabase_client.table("positions").delete().eq("symbol", symbol).execute()
            
            print(f"📉 포지션 삭제: {symbol}")
            return True
            
        except Exception as e:
            print(f"❌ 포지션 삭제 실패: {e}")
            return False
    
    # === 성과 분석 관련 메서드 ===
    
    async def save_daily_performance(self, date: datetime, metrics: Dict[str, Any]) -> bool:
        """일일 성과 지표 저장"""
        
        try:
            if not self.supabase_client:
                return False
            
            # TODO: Supabase에 성과 데이터 저장
            performance_dict = {
                "date": date.date().isoformat(),
                **metrics,
                "updated_at": datetime.now().isoformat()
            }
            
            # result = self.supabase_client.table("performance_metrics").upsert(performance_dict).execute()
            
            print(f"📊 일일 성과 저장: {date.date()}")
            return True
            
        except Exception as e:
            print(f"❌ 일일 성과 저장 실패: {e}")
            return False
    
    async def get_performance_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """성과 히스토리 조회"""
        
        try:
            if not self.supabase_client:
                return []
            
            # TODO: Supabase에서 성과 데이터 조회
            start_date = (datetime.now() - timedelta(days=days)).date()
            
            # result = self.supabase_client.table("performance_metrics").select("*").gte("date", start_date.isoformat()).order("date", desc=True).execute()
            
            # 임시로 빈 리스트 반환
            return []
            
        except Exception as e:
            print(f"❌ 성과 히스토리 조회 실패: {e}")
            return []
    
    # === 백테스팅 관련 메서드 ===
    
    async def get_historical_data(self, symbol: str, start_date: datetime, 
                                end_date: datetime) -> pd.DataFrame:
        """백테스팅용 히스토리컬 데이터 조회"""
        
        try:
            if not self.supabase_client:
                return pd.DataFrame()
            
            # TODO: Supabase에서 히스토리컬 데이터 조회
            # result = self.supabase_client.table("candle_data").select("*").eq("symbol", symbol).gte("timestamp", start_date.isoformat()).lte("timestamp", end_date.isoformat()).order("timestamp").execute()
            
            # 임시로 빈 DataFrame 반환
            return pd.DataFrame()
            
        except Exception as e:
            print(f"❌ 히스토리컬 데이터 조회 실패: {e}")
            return pd.DataFrame()
    
    # === 유틸리티 메서드 ===
    
    async def health_check(self) -> bool:
        """데이터베이스 연결 상태 확인"""
        
        try:
            if not self.supabase_client:
                return False
            
            # TODO: 간단한 쿼리로 연결 상태 확인
            # result = self.supabase_client.table("candle_data").select("count", count="exact").limit(1).execute()
            
            return self.is_connected
            
        except Exception as e:
            print(f"❌ 데이터베이스 헬스체크 실패: {e}")
            return False
    
    async def cleanup_old_data(self, days: int = 30):
        """오래된 데이터 정리"""
        
        try:
            if not self.supabase_client:
                return
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # TODO: 오래된 캔들 데이터 삭제
            # self.supabase_client.table("candle_data").delete().lt("timestamp", cutoff_date.isoformat()).execute()
            
            # TODO: 오래된 신호 데이터 삭제
            # self.supabase_client.table("trading_signals").delete().lt("timestamp", cutoff_date.isoformat()).execute()
            
            print(f"🧹 {days}일 이전 데이터 정리 완료")
            
        except Exception as e:
            print(f"❌ 데이터 정리 실패: {e}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """데이터베이스 통계 조회"""
        
        try:
            if not self.supabase_client:
                return {}
            
            # TODO: 각 테이블별 통계 조회
            stats = {
                "candle_data_count": 0,
                "signals_count": 0,
                "orders_count": 0,
                "positions_count": 0,
                "trades_count": 0
            }
            
            return stats
            
        except Exception as e:
            print(f"❌ 데이터베이스 통계 조회 실패: {e}")
            return {}
