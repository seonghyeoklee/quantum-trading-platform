import asyncpg
import pandas as pd
from typing import List, Optional
from datetime import datetime, date
from app.models.candle import StockCandle
import os

class DatabaseService:
    """PostgreSQL 데이터베이스 서비스"""
    
    def __init__(self):
        self.connection_pool = None
    
    async def initialize(self):
        """데이터베이스 연결 풀 초기화"""
        database_url = os.getenv('DATABASE_URL', 'postgresql://admin:password@localhost:5432/quantum_trading')
        self.connection_pool = await asyncpg.create_pool(database_url, min_size=2, max_size=10)
    
    async def close(self):
        """연결 풀 종료"""
        if self.connection_pool:
            await self.connection_pool.close()
    
    async def get_stock_candles(self, symbol: str, timeframe: str, 
                              start_date: Optional[datetime] = None, 
                              end_date: Optional[datetime] = None,
                              limit: int = 1000) -> List[StockCandle]:
        """주식 캔들 데이터 조회"""
        
        query = """
            SELECT id, symbol, timeframe, timestamp, 
                   open_price, high_price, low_price, close_price, 
                   volume, created_at
            FROM tb_stock_candle 
            WHERE symbol = $1 AND timeframe = $2
        """
        params = [symbol, timeframe]
        param_count = 2
        
        if start_date:
            param_count += 1
            query += f" AND timestamp >= ${param_count}"
            params.append(start_date)
        
        if end_date:
            param_count += 1
            query += f" AND timestamp <= ${param_count}"
            params.append(end_date)
        
        query += " ORDER BY timestamp DESC"
        
        if limit:
            param_count += 1
            query += f" LIMIT ${param_count}"
            params.append(limit)
        
        async with self.connection_pool.acquire() as connection:
            rows = await connection.fetch(query, *params)
            
            candles = []
            for row in rows:
                candle = StockCandle(
                    id=row['id'],
                    symbol=row['symbol'],
                    timeframe=row['timeframe'],
                    timestamp=row['timestamp'],
                    open_price=row['open_price'],
                    high_price=row['high_price'],
                    low_price=row['low_price'],
                    close_price=row['close_price'],
                    volume=row['volume'],
                    created_at=row['created_at']
                )
                candles.append(candle)
            
            return candles
    
    async def get_candles_as_dataframe(self, symbol: str, timeframe: str,
                                     start_date: Optional[datetime] = None,
                                     end_date: Optional[datetime] = None,
                                     limit: int = 1000) -> pd.DataFrame:
        """캔들 데이터를 DataFrame으로 조회"""
        
        query = """
            SELECT timestamp, open_price as open, high_price as high, 
                   low_price as low, close_price as close, volume
            FROM tb_stock_candle 
            WHERE symbol = $1 AND timeframe = $2
        """
        params = [symbol, timeframe]
        param_count = 2
        
        if start_date:
            param_count += 1
            query += f" AND timestamp >= ${param_count}"
            params.append(start_date)
        
        if end_date:
            param_count += 1
            query += f" AND timestamp <= ${param_count}"
            params.append(end_date)
        
        query += " ORDER BY timestamp ASC"
        
        if limit:
            param_count += 1
            query += f" LIMIT ${param_count}"
            params.append(limit)
        
        async with self.connection_pool.acquire() as connection:
            rows = await connection.fetch(query, *params)
            
            # pandas DataFrame으로 변환
            data = []
            for row in rows:
                data.append({
                    'timestamp': row['timestamp'],
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': row['volume']
                })
            
            df = pd.DataFrame(data)
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
            
            return df
    
    async def get_available_symbols(self, timeframe: str = "1d") -> List[str]:
        """사용 가능한 종목 코드 목록 조회"""
        
        query = """
            SELECT DISTINCT symbol 
            FROM tb_stock_candle 
            WHERE timeframe = $1
            ORDER BY symbol
        """
        
        async with self.connection_pool.acquire() as connection:
            rows = await connection.fetch(query, timeframe)
            return [row['symbol'] for row in rows]
    
    async def get_latest_candle(self, symbol: str, timeframe: str) -> Optional[StockCandle]:
        """최신 캔들 데이터 조회"""
        
        query = """
            SELECT id, symbol, timeframe, timestamp, 
                   open_price, high_price, low_price, close_price, 
                   volume, created_at
            FROM tb_stock_candle 
            WHERE symbol = $1 AND timeframe = $2
            ORDER BY timestamp DESC 
            LIMIT 1
        """
        
        async with self.connection_pool.acquire() as connection:
            row = await connection.fetchrow(query, symbol, timeframe)
            
            if row:
                return StockCandle(
                    id=row['id'],
                    symbol=row['symbol'],
                    timeframe=row['timeframe'],
                    timestamp=row['timestamp'],
                    open_price=row['open_price'],
                    high_price=row['high_price'],
                    low_price=row['low_price'],
                    close_price=row['close_price'],
                    volume=row['volume'],
                    created_at=row['created_at']
                )
            return None
    
    async def get_market_overview(self, timeframe: str = "1d", top_n: int = 20) -> pd.DataFrame:
        """시장 개요 (거래량 상위 종목)"""
        
        query = """
            SELECT symbol, 
                   AVG(close_price) as avg_price,
                   SUM(volume) as total_volume,
                   COUNT(*) as candle_count,
                   MAX(timestamp) as last_update
            FROM tb_stock_candle 
            WHERE timeframe = $1
              AND timestamp >= NOW() - INTERVAL '30 days'
            GROUP BY symbol
            ORDER BY total_volume DESC
            LIMIT $2
        """
        
        async with self.connection_pool.acquire() as connection:
            rows = await connection.fetch(query, timeframe, top_n)
            
            data = []
            for row in rows:
                data.append({
                    'symbol': row['symbol'],
                    'avg_price': float(row['avg_price']),
                    'total_volume': row['total_volume'],
                    'candle_count': row['candle_count'],
                    'last_update': row['last_update']
                })
            
            return pd.DataFrame(data)