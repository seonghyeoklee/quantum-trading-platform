#!/usr/bin/env python3
"""
국내주식정보 수집 DAG (DDD 기반)
domestic_stocks 테이블에서 종목을 자동으로 가져와서 KIS API 데이터를 수집하고 domestic_stock_data에 저장

Author: Quantum Trading Platform  
Created: 2025-09-07
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pytz

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.models import Variable

# 로깅 설정 (먼저 설정)
logger = logging.getLogger(__name__)

# 프로젝트 경로 추가 - 더 구체적인 경로 설정
import os
project_root = '/opt/airflow/quantum-adapter-kis'
if os.path.exists(project_root):
    sys.path.insert(0, project_root)
    sys.path.insert(0, os.path.join(project_root, 'trading_strategy'))

# KIS 데이터 관련 모듈 임포트 (모듈이 없어도 DAG 파싱은 가능하도록)
try:
    from trading_strategy.core.kis_data_provider import KISDataProvider
    from trading_strategy.db_manager import DatabaseManager
    KIS_MODULES_AVAILABLE = True
    logger.info("KIS modules loaded successfully")
except ImportError as e:
    logger.warning(f"KIS modules not available: {e}")
    KISDataProvider = None
    DatabaseManager = None
    KIS_MODULES_AVAILABLE = False

# DAG 기본 설정
default_args = {
    'owner': 'quantum-trading',
    'depends_on_past': False,
    'start_date': datetime(2025, 9, 6, tzinfo=pytz.timezone("Asia/Seoul")),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=3),
}

# DAG 정의
dag = DAG(
    'domestic_stock_data_collection',
    default_args=default_args,
    description='국내주식정보 수집 - domestic_stocks에서 종목 자동 조회하여 KIS API 데이터 수집 (DDD 설계)',
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    max_active_runs=1,
    tags=['domestic-stock-data', 'kis-api', 'data-collection', 'ddd'],
    params={
        "data_types": "price,chart",        # 수집할 데이터 타입
        "chart_period": "D",                # 차트 기간 (D: 일봉)
        "chart_count": 100,                 # 차트 데이터 개수
        "limit_stocks": 50,                 # 처리할 종목 수 제한 (성능 고려)
        "market_filter": "ALL"              # KOSPI, KOSDAQ, ALL
    }
)


def get_domestic_stocks_from_db(**context):
    """domestic_stocks 테이블에서 활성 종목 목록 조회"""
    
    # DAG 파라미터 가져오기
    dag_run = context.get('dag_run')
    if dag_run and dag_run.conf:
        limit_stocks = dag_run.conf.get('limit_stocks', context['params']['limit_stocks'])
        market_filter = dag_run.conf.get('market_filter', context['params']['market_filter'])
    else:
        limit_stocks = context['params']['limit_stocks']
        market_filter = context['params']['market_filter']
    
    logger.info(f"🔍 Querying domestic stocks from database...")
    logger.info(f"📊 Parameters: limit={limit_stocks}, market_filter={market_filter}")
    
    # PostgreSQL 연결
    pg_hook = PostgresHook(postgres_conn_id='quantum_postgres')
    
    try:
        # SQL 쿼리 작성
        base_sql = """
        SELECT 
            stock_code,
            stock_name,
            market_type,
            updated_at
        FROM domestic_stocks 
        WHERE is_active = true
        """
        
        # 시장 필터 적용
        if market_filter != 'ALL':
            base_sql += f" AND market_type = '{market_filter}'"
        
        # 최신 업데이트 순으로 정렬 및 제한
        base_sql += " ORDER BY updated_at DESC"
        
        if limit_stocks and limit_stocks > 0:
            base_sql += f" LIMIT {limit_stocks}"
        
        # 쿼리 실행
        stocks = pg_hook.get_records(base_sql)
        
        if not stocks:
            logger.error("❌ No active domestic stocks found in database")
            raise ValueError("No active domestic stocks found")
        
        # 결과 변환
        stock_list = []
        for stock in stocks:
            stock_code, stock_name, market_type, updated_at = stock
            stock_list.append({
                'stock_code': stock_code,
                'stock_name': stock_name, 
                'market_type': market_type,
                'updated_at': updated_at.isoformat() if updated_at else None
            })
        
        logger.info(f"✅ Found {len(stock_list)} domestic stocks")
        logger.info(f"📈 Market distribution: {market_filter} filter applied")
        
        # 샘플 출력
        for i, stock in enumerate(stock_list[:5]):
            logger.info(f"  {i+1}. {stock['stock_code']} - {stock['stock_name']} ({stock['market_type']})")
        
        if len(stock_list) > 5:
            logger.info(f"  ... and {len(stock_list) - 5} more stocks")
        
        return {
            'stocks': stock_list,
            'total_count': len(stock_list),
            'market_filter': market_filter,
            'query_time': datetime.now(pytz.timezone("Asia/Seoul")).isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error querying domestic stocks: {e}")
        raise


def collect_domestic_stock_data(**context):
    """국내주식정보 수집 메인 함수"""
    
    # 모듈 가용성 체크
    if not KIS_MODULES_AVAILABLE:
        logger.error("❌ KIS 모듈을 사용할 수 없습니다. 컨테이너 설정을 확인하세요.")
        raise ImportError("KIS modules not available")
    
    # 이전 태스크에서 종목 목록 가져오기
    stock_data = context['task_instance'].xcom_pull(task_ids='get_domestic_stocks')
    if not stock_data or not stock_data.get('stocks'):
        logger.error("❌ No stock data received from previous task")
        raise ValueError("No stock data available")
    
    stocks = stock_data['stocks']
    
    # DAG 파라미터 가져오기
    dag_run = context.get('dag_run')
    if dag_run and dag_run.conf:
        data_types = dag_run.conf.get('data_types', context['params']['data_types'])
        chart_period = dag_run.conf.get('chart_period', context['params']['chart_period'])
        chart_count = dag_run.conf.get('chart_count', context['params']['chart_count'])
    else:
        data_types = context['params']['data_types']
        chart_period = context['params']['chart_period']
        chart_count = context['params']['chart_count']
    
    # 파라미터 파싱
    data_type_list = [d.strip() for d in data_types.split(',')]
    
    logger.info(f"🎯 국내주식정보 수집 시작")
    logger.info(f"📈 종목 수: {len(stocks)}")
    logger.info(f"📊 데이터 타입: {data_type_list}")
    
    # KIS 데이터 제공자 및 DB 매니저 초기화
    try:
        kis_provider = KISDataProvider(base_url="http://host.docker.internal:8000")
        db_manager = DatabaseManager()
        
        total_success = 0
        total_requests = 0
        
        for stock in stocks:
            stock_code = stock['stock_code']
            stock_name = stock['stock_name']
            
            logger.info(f"🔄 {stock_code}({stock_name}) 데이터 수집 중...")
            
            for data_type in data_type_list:
                total_requests += 1
                
                try:
                    if data_type == 'price':
                        # 현재가 데이터 수집
                        success = collect_price_data(kis_provider, db_manager, stock_code)
                    elif data_type == 'chart':
                        # 차트 데이터 수집
                        success = collect_chart_data(
                            kis_provider, db_manager, stock_code, 
                            chart_period, int(chart_count)
                        )
                    else:
                        logger.warning(f"⚠️ 지원하지 않는 데이터 타입: {data_type}")
                        continue
                    
                    if success:
                        total_success += 1
                        logger.info(f"✅ {stock_code} {data_type} 수집 완료")
                    else:
                        logger.error(f"❌ {stock_code} {data_type} 수집 실패")
                        
                except Exception as e:
                    logger.error(f"❌ {stock_code} {data_type} 수집 중 오류: {e}")
        
        # 결과 요약
        success_rate = (total_success / total_requests * 100) if total_requests > 0 else 0
        logger.info(f"📊 수집 완료: {total_success}/{total_requests} ({success_rate:.1f}%)")
        
        # XCom으로 결과 반환
        return {
            'total_requests': total_requests,
            'total_success': total_success,
            'success_rate': success_rate,
            'processed_stocks': len(stocks),
            'data_types': data_type_list,
            'collection_time': datetime.now(pytz.timezone("Asia/Seoul")).isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 국내주식정보 수집 중 치명적 오류: {e}")
        raise
    finally:
        if 'db_manager' in locals():
            db_manager.disconnect()


def collect_price_data(kis_provider: KISDataProvider, db_manager: DatabaseManager, 
                      stock_code: str) -> bool:
    """현재가 데이터 수집"""
    try:
        # KIS API 호출
        price_data = kis_provider.get_current_price(stock_code)
        
        if not price_data or price_data.get('rt_cd') != '0':
            logger.warning(f"⚠️ {stock_code} 현재가 데이터 없음 또는 오류")
            return False
        
        # DB 저장 (새로운 테이블 구조 사용)
        success = save_domestic_stock_data(
            db_manager=db_manager,
            stock_code=stock_code,
            api_endpoint=f"/domestic/price/{stock_code}",
            data_type="price",
            request_params={},
            raw_response=price_data
        )
        
        return success
        
    except Exception as e:
        logger.error(f"❌ {stock_code} 현재가 수집 실패: {e}")
        return False


def collect_chart_data(kis_provider: KISDataProvider, db_manager: DatabaseManager, 
                      stock_code: str, period: str, count: int) -> bool:
    """차트 데이터 수집"""
    try:
        # KIS API 호출
        chart_df = kis_provider.get_chart_data(stock_code, period, count)
        
        if chart_df.empty:
            logger.warning(f"⚠️ {stock_code} 차트 데이터 없음")
            return False
        
        # DataFrame을 원시 응답 형태로 변환
        chart_records = chart_df.reset_index().to_dict(orient='records')
        raw_response = {
            'rt_cd': '0',
            'msg_cd': 'SUCCESS',
            'msg1': '정상처리',
            'output1': {},
            'output2': chart_records
        }
        
        # DB 저장 (새로운 테이블 구조 사용)
        success = save_domestic_stock_data(
            db_manager=db_manager,
            stock_code=stock_code,
            api_endpoint=f"/domestic/chart/{stock_code}",
            data_type="chart",
            request_params={"period": period, "count": count},
            raw_response=raw_response
        )
        
        if success:
            logger.info(f"📊 {stock_code} 차트 데이터 {len(chart_records)}건 저장")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ {stock_code} 차트 데이터 수집 실패: {e}")
        return False


def save_domestic_stock_data(db_manager: DatabaseManager, stock_code: str, 
                           api_endpoint: str, data_type: str, 
                           request_params: dict, raw_response: dict) -> bool:
    """국내주식정보를 domestic_stock_detail 테이블에 저장"""
    
    try:
        # PostgreSQL 연결 (db_manager 대신 직접 연결)
        pg_hook = PostgresHook(postgres_conn_id='quantum_postgres')
        
        # INSERT SQL
        insert_sql = """
        INSERT INTO domestic_stock_detail (
            stock_code,
            api_endpoint,
            data_type,
            request_params,
            request_timestamp,
            raw_response,
            response_code,
            current_price,
            trade_date,
            volume,
            created_at,
            data_quality
        ) VALUES (
            %(stock_code)s,
            %(api_endpoint)s,
            %(data_type)s,
            %(request_params)s,
            %(request_timestamp)s,
            %(raw_response)s,
            %(response_code)s,
            %(current_price)s,
            %(trade_date)s,
            %(volume)s,
            NOW(),
            'GOOD'
        );
        """
        
        # 데이터 추출
        response_code = raw_response.get('rt_cd', '0')
        current_price = None
        trade_date = None
        volume = None
        
        if data_type == 'price' and 'output' in raw_response:
            output = raw_response['output']
            current_price = output.get('stck_prpr', 0)  # 현재가
            volume = output.get('acml_vol', 0)  # 누적 거래량
            trade_date = datetime.now().date()  # 오늘 날짜
        elif data_type == 'chart' and 'output2' in raw_response:
            # 차트 데이터는 여러 건이므로 첫 번째 레코드 사용
            if raw_response['output2']:
                first_record = raw_response['output2'][0]
                current_price = first_record.get('stck_clpr', 0)  # 종가
                volume = first_record.get('acml_vol', 0)  # 거래량
                trade_date_str = first_record.get('stck_bsop_date')
                if trade_date_str:
                    trade_date = datetime.strptime(trade_date_str, '%Y%m%d').date()
        
        # DB에 저장
        pg_hook.run(insert_sql, parameters={
            'stock_code': stock_code,
            'api_endpoint': api_endpoint,
            'data_type': data_type,
            'request_params': request_params,
            'request_timestamp': datetime.now(pytz.timezone("Asia/Seoul")),
            'raw_response': raw_response,
            'response_code': response_code,
            'current_price': int(current_price) if current_price else None,
            'trade_date': trade_date,
            'volume': int(volume) if volume else None,
        })
        
        return True
        
    except Exception as e:
        logger.error(f"❌ DB 저장 실패 - {stock_code}: {e}")
        return False


def validate_collection_result(**context):
    """데이터 수집 결과 검증"""
    
    # 이전 태스크 결과 가져오기
    result = context['task_instance'].xcom_pull(task_ids='collect_domestic_stock_data')
    
    if not result:
        logger.error("❌ 수집 결과 데이터 없음")
        raise ValueError("수집 결과 데이터 없음")
    
    success_rate = result.get('success_rate', 0)
    total_requests = result.get('total_requests', 0)
    processed_stocks = result.get('processed_stocks', 0)
    
    logger.info(f"📊 국내주식정보 수집 결과 검증:")
    logger.info(f"   - 처리 종목: {processed_stocks}개")
    logger.info(f"   - 전체 요청: {total_requests}건")
    logger.info(f"   - 성공률: {success_rate:.1f}%")
    
    # 성공률이 50% 미만이면 경고
    if success_rate < 50:
        logger.warning(f"⚠️ 데이터 수집 성공률이 낮습니다: {success_rate:.1f}%")
    
    # DB에서 실제 저장된 데이터 확인
    try:
        pg_hook = PostgresHook(postgres_conn_id='quantum_postgres')
        
        # 오늘 저장된 데이터 개수 확인
        count_sql = """
        SELECT 
            data_type,
            COUNT(*) as record_count,
            COUNT(DISTINCT stock_code) as unique_stocks
        FROM domestic_stock_detail 
        WHERE DATE(created_at) = CURRENT_DATE
        GROUP BY data_type
        ORDER BY data_type;
        """
        
        counts = pg_hook.get_records(count_sql)
        
        logger.info(f"📈 DB 저장 현황 (오늘):")
        for data_type, record_count, unique_stocks in counts:
            logger.info(f"   - {data_type}: {record_count}건 ({unique_stocks}개 종목)")
            
    except Exception as e:
        logger.error(f"❌ DB 검증 실패: {e}")
    
    return result


# ========================================
# DAG 태스크 정의
# ========================================

# 1. domestic_stocks에서 종목 목록 조회
get_stocks_task = PythonOperator(
    task_id='get_domestic_stocks',
    python_callable=get_domestic_stocks_from_db,
    provide_context=True,
    dag=dag,
)

# 2. 국내주식정보 수집
collect_data_task = PythonOperator(
    task_id='collect_domestic_stock_data',
    python_callable=collect_domestic_stock_data,
    provide_context=True,
    dag=dag,
)

# 3. 수집 결과 검증
validate_result_task = PythonOperator(
    task_id='validate_collection_result',
    python_callable=validate_collection_result,
    provide_context=True,
    dag=dag,
)

# ========================================
# 태스크 의존성 설정
# ========================================
get_stocks_task >> collect_data_task >> validate_result_task