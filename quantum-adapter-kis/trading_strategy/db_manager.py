#!/usr/bin/env python3
"""
데이터베이스 연동 매니저
PostgreSQL에 분석 결과를 저장하고 관리

Author: Quantum Trading Platform
Created: 2025-09-04
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
    """PostgreSQL 데이터베이스 연동 매니저"""
    
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
    
    def save_analysis_result(self, analysis_data: Dict[str, Any]) -> bool:
        """분석 결과를 데이터베이스에 저장"""
        try:
            success_count = 0
            # 각 종목별 분석 결과 저장
            for result in analysis_data.get('analysis_results', []):
                if self.save_single_stock_analysis(result):
                    success_count += 1
                else:
                    logger.warning(f"⚠️  종목 저장 실패: {result.get('symbol', 'Unknown')}")
            
            logger.info(f"✅ 분석 결과 DB 저장 완료: {success_count}/{len(analysis_data.get('analysis_results', []))}개 종목")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ 분석 결과 저장 실패: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def save_single_stock_analysis(self, result: Dict[str, Any]) -> bool:
        """단일 종목 분석 결과 저장"""
        try:
            # stock_analysis 테이블에 저장
            query = """
            INSERT INTO stock_analysis (
                symbol, analyzed_date, symbol_name, market_type, exchange_code, country,
                sector_l1, sector_l2,
                investment_score, recommendation, risk_level, confidence_level,
                signal_type, signal_strength, signal_confidence,
                current_price, price_change, price_change_rate, volume,
                rsi, sma5, sma20, sma60, macd,
                backtest_total_return,
                data_source, data_quality, data_period_days,
                analysis_engine_version, raw_analysis, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s,
                %s, %s, %s,
                %s, %s, %s
            ) ON CONFLICT (symbol, analyzed_date) 
            DO UPDATE SET
                symbol_name = EXCLUDED.symbol_name,
                investment_score = EXCLUDED.investment_score,
                recommendation = EXCLUDED.recommendation,
                current_price = EXCLUDED.current_price,
                price_change = EXCLUDED.price_change,
                price_change_rate = EXCLUDED.price_change_rate,
                rsi = EXCLUDED.rsi,
                backtest_total_return = EXCLUDED.backtest_total_return,
                raw_analysis = EXCLUDED.raw_analysis
            """
            
            # 백테스팅 데이터 처리
            backtest = result.get('backtest', {})
            total_return = backtest.get('total_return', 0.0)
            
            # 시그널 데이터 처리
            signal = result.get('signal', {})
            
            # 지표 데이터 처리
            indicators = result.get('indicators', {})
            
            # 시장 데이터 처리
            market_data = result.get('market_data', {})
            
            # 메타데이터 처리
            meta = result.get('meta', {})
            
            params = (
                result.get('symbol'),
                result.get('analyzed_date'),
                result.get('symbol_name'),
                result.get('market_type'),
                result.get('exchange_code'),
                result.get('country'),
                result.get('sector_l1'),
                result.get('sector_l2'),
                result.get('investment_score'),
                result.get('recommendation'),
                result.get('risk_level'),
                result.get('confidence_level'),
                signal.get('type'),
                signal.get('strength'),
                signal.get('confidence'),
                market_data.get('current_price'),
                market_data.get('price_change'),
                market_data.get('price_change_rate'),
                market_data.get('volume'),
                indicators.get('rsi'),
                indicators.get('sma5'),
                indicators.get('sma20'),
                indicators.get('sma60'),
                indicators.get('macd'),
                total_return,
                meta.get('data_source'),
                meta.get('data_quality'),
                meta.get('data_period_days'),
                meta.get('analysis_engine_version'),
                json.dumps(result, ensure_ascii=False, default=str),
                datetime.now()
            )
            
            return self.execute_query(query, params) is not None
            
        except Exception as e:
            logger.error(f"❌ 종목 분석 결과 저장 실패 ({result.get('symbol')}): {e}")
            return False
    
    def save_analysis_summary(self, analysis_data: Dict[str, Any]) -> bool:
        """분석 요약 정보 저장 (현재 스킵)"""
        logger.info("ℹ️  분석 요약 저장 스킵 (테이블 구조 불일치)")
        return True
    
    def get_latest_analysis(self, limit: int = 10) -> List[Dict]:
        """최근 분석 결과 조회"""
        query = """
        SELECT symbol, analyzed_date, investment_score, recommendation,
               current_price, price_change_rate, rsi
        FROM stock_analysis 
        WHERE analyzed_date = (SELECT MAX(analyzed_date) FROM stock_analysis)
        ORDER BY investment_score DESC
        LIMIT %s
        """
        
        result = self.execute_query(query, (limit,), fetch=True)
        return result if result else []
    
    def get_analysis_summary(self, analysis_date: str = None) -> Dict:
        """분석 요약 조회 (stock_analysis에서 계산)"""
        if not analysis_date:
            # 최근 분석일 조회
            query = "SELECT MAX(analyzed_date) as latest_date FROM stock_analysis"
            result = self.execute_query(query, fetch=True)
            if result and result[0]['latest_date']:
                analysis_date = result[0]['latest_date'].strftime('%Y-%m-%d')
            else:
                return {}
        
        # stock_analysis 테이블에서 요약 정보 계산
        query = """
        SELECT 
            COUNT(*) as total_stocks,
            AVG(investment_score) as total_avg_score,
            COUNT(*) FILTER (WHERE market_type = 'DOMESTIC') as domestic_count,
            AVG(investment_score) FILTER (WHERE market_type = 'DOMESTIC') as domestic_avg_score,
            COUNT(*) FILTER (WHERE market_type = 'OVERSEAS') as overseas_count,
            AVG(investment_score) FILTER (WHERE market_type = 'OVERSEAS') as overseas_avg_score,
            COUNT(*) FILTER (WHERE recommendation = '매수추천') as buy_recommend_count
        FROM stock_analysis 
        WHERE analyzed_date = %s
        """
        
        result = self.execute_query(query, (analysis_date,), fetch=True)
        return dict(result[0]) if result else {}