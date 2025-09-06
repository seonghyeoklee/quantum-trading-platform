#!/usr/bin/env python3
"""
데이터베이스 연동 매니저 - KIS API 원시 데이터 저장
PostgreSQL kis_market_data 테이블을 사용한 KIS API 데이터 관리

Author: Quantum Trading Platform
Created: 2025-09-04
Updated: 2025-09-06 - KIS API 중심 구조로 변경
"""

import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import traceback

logger = logging.getLogger(__name__)

class DatabaseManager:
    """PostgreSQL KIS Market Data 데이터베이스 연동 매니저"""
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 5433,
                 database: str = "quantum_trading",
                 user: str = "quantum",
                 password: str = "quantum123"):
        """
        데이터베이스 연결 초기화
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        
        self.connect()
    
    def connect(self):
        """데이터베이스 연결"""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            logger.info(f"✅ PostgreSQL 연결 성공: {self.database}")
            return True
        except Exception as e:
            logger.error(f"❌ PostgreSQL 연결 실패: {e}")
            return False
    
    def disconnect(self):
        """데이터베이스 연결 해제"""
        if self.connection:
            self.connection.close()
            logger.info("🔌 PostgreSQL 연결 해제")
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """쿼리 실행"""
        if not self.connection:
            logger.error("❌ 데이터베이스 연결이 없습니다")
            return None
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if fetch:
                    return cursor.fetchall()
                self.connection.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"❌ 쿼리 실행 실패: {e}")
            logger.error(f"Query: {query}")
            logger.error(traceback.format_exc())
            self.connection.rollback()
            return None
    
    def save_kis_raw_data(self, symbol: str, api_endpoint: str, data_type: str, 
                         market_type: str, request_params: Dict, raw_response: Dict) -> bool:
        """KIS API 원시 데이터를 데이터베이스에 저장"""
        try:
            # kis_market_data 테이블에 저장
            query = """
            INSERT INTO kis_market_data (
                symbol, api_endpoint, data_type, market_type,
                request_params, request_timestamp, raw_response,
                response_code, current_price, trade_date, volume
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s
            )
            """
            
            # 응답에서 주요 필드들 추출
            response_code = raw_response.get('rt_cd', 'UNKNOWN')
            current_price = None
            trade_date = None
            volume = None
            
            # 데이터 타입별로 필드 추출
            if data_type == 'price' and 'output' in raw_response:
                output = raw_response['output']
                current_price = self._safe_int(output.get('stck_prpr'))
                volume = self._safe_int(output.get('acml_vol'))
                trade_date = datetime.now().date()  # 현재가는 오늘 날짜
            
            elif data_type == 'chart' and 'output2' in raw_response:
                # 차트 데이터의 경우 첫 번째 레코드에서 추출
                output2 = raw_response['output2']
                if output2 and len(output2) > 0:
                    first_record = output2[0]
                    current_price = self._safe_int(first_record.get('stck_clpr'))  # 종가
                    volume = self._safe_int(first_record.get('acml_vol'))
                    trade_date = self._safe_date(first_record.get('stck_bsop_date'))
            
            params = (
                symbol, api_endpoint, data_type, market_type,
                json.dumps(request_params, ensure_ascii=False), datetime.now(), 
                json.dumps(raw_response, ensure_ascii=False, default=str),
                response_code, current_price, trade_date, volume
            )
            
            result = self.execute_query(query, params)
            if result is not None:
                logger.info(f"✅ KIS 원시 데이터 저장 완료: {symbol} ({data_type})")
                return True
            else:
                logger.error(f"❌ KIS 원시 데이터 저장 실패: {symbol} ({data_type})")
                return False
                
        except Exception as e:
            logger.error(f"❌ KIS 원시 데이터 저장 실패 ({symbol}): {e}")
            logger.error(traceback.format_exc())
            return False
    
    def save_analysis_result(self, analysis_data: Dict[str, Any]) -> bool:
        """분석 결과를 KIS 원시 데이터와 연결하여 저장 (추후 구현)"""
        logger.info("ℹ️  분석 결과 저장은 추후 구현 예정 (현재는 KIS 원시 데이터만 저장)")
        return True
    
    def get_latest_market_data(self, symbol: str, data_type: str = 'price', limit: int = 1) -> List[Dict]:
        """최신 시장 데이터 조회"""
        query = """
        SELECT symbol, data_type, request_timestamp, current_price, volume,
               raw_response, response_code
        FROM kis_market_data 
        WHERE symbol = %s AND data_type = %s
          AND response_code = '0'
        ORDER BY request_timestamp DESC
        LIMIT %s
        """
        
        result = self.execute_query(query, (symbol, data_type, limit), fetch=True)
        return result if result else []
    
    def get_chart_data(self, symbol: str, days: int = 100) -> List[Dict]:
        """차트 데이터 조회"""
        query = """
        SELECT symbol, trade_date, raw_response
        FROM kis_market_data 
        WHERE symbol = %s AND data_type = 'chart'
          AND response_code = '0'
          AND trade_date >= CURRENT_DATE - INTERVAL '%s days'
        ORDER BY trade_date DESC
        LIMIT %s
        """
        
        result = self.execute_query(query, (symbol, days, days), fetch=True)
        return result if result else []
    
    def get_market_data_summary(self, days: int = 7) -> Dict:
        """시장 데이터 요약 조회"""
        query = """
        SELECT 
            COUNT(DISTINCT symbol) as total_symbols,
            COUNT(*) as total_records,
            COUNT(*) FILTER (WHERE market_type = 'domestic') as domestic_count,
            COUNT(*) FILTER (WHERE market_type = 'overseas') as overseas_count,
            COUNT(*) FILTER (WHERE data_type = 'price') as price_records,
            COUNT(*) FILTER (WHERE data_type = 'chart') as chart_records,
            MAX(request_timestamp) as latest_data
        FROM kis_market_data 
        WHERE request_timestamp >= CURRENT_DATE - INTERVAL '%s days'
          AND response_code = '0'
        """
        
        result = self.execute_query(query, (days,), fetch=True)
        return dict(result[0]) if result else {}
    
    def _safe_int(self, value) -> Optional[int]:
        """안전한 정수 변환"""
        if value is None or value == '':
            return None
        try:
            return int(str(value).replace(',', ''))
        except (ValueError, TypeError):
            return None
    
    def _safe_date(self, value) -> Optional[date]:
        """안전한 날짜 변환 (YYYYMMDD 형식)"""
        if value is None or value == '':
            return None
        try:
            date_str = str(value)
            if len(date_str) == 8:
                return datetime.strptime(date_str, '%Y%m%d').date()
            return None
        except (ValueError, TypeError):
            return None