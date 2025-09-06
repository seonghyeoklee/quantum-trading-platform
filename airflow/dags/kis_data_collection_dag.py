#!/usr/bin/env python3
"""
KIS API 데이터 수집 DAG
종목 코드를 파라미터로 받아서 KIS API 데이터를 수집하고 PostgreSQL에 저장

Author: Quantum Trading Platform
Created: 2025-09-06
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
import pendulum

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
    'start_date': pendulum.datetime(2025, 9, 6, tz="Asia/Seoul"),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=3),
}

# DAG 정의
dag = DAG(
    'kis_data_collection',
    default_args=default_args,
    description='KIS API 데이터 수집 및 저장 - 종목 코드 파라미터 지원',
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    max_active_runs=1,
    tags=['kis-api', 'data-collection', 'market-data'],
    params={
        "symbols": "005930,000660,035720",  # 기본값: 삼성전자, SK하이닉스, 카카오
        "data_types": "price,chart",        # 수집할 데이터 타입
        "chart_period": "D",                # 차트 기간 (D: 일봉)
        "chart_count": 100                  # 차트 데이터 개수
    }
)

def collect_kis_data(**context):
    """KIS API 데이터 수집 메인 함수"""
    
    # 모듈 가용성 체크
    if not KIS_MODULES_AVAILABLE:
        logger.error("❌ KIS 모듈을 사용할 수 없습니다. 컨테이너 설정을 확인하세요.")
        raise ImportError("KIS modules not available")
    
    # DAG 파라미터 가져오기
    dag_run = context.get('dag_run')
    if dag_run and dag_run.conf:
        symbols = dag_run.conf.get('symbols', context['params']['symbols'])
        data_types = dag_run.conf.get('data_types', context['params']['data_types'])
        chart_period = dag_run.conf.get('chart_period', context['params']['chart_period'])
        chart_count = dag_run.conf.get('chart_count', context['params']['chart_count'])
    else:
        symbols = context['params']['symbols']
        data_types = context['params']['data_types']
        chart_period = context['params']['chart_period']
        chart_count = context['params']['chart_count']
    
    # 파라미터 파싱
    symbol_list = [s.strip() for s in symbols.split(',')]
    data_type_list = [d.strip() for d in data_types.split(',')]
    
    logger.info(f"🎯 KIS 데이터 수집 시작")
    logger.info(f"📈 종목: {symbol_list}")
    logger.info(f"📊 데이터 타입: {data_type_list}")
    
    # KIS 데이터 제공자 및 DB 매니저 초기화
    try:
        kis_provider = KISDataProvider(base_url="http://host.docker.internal:8000")
        db_manager = DatabaseManager()
        
        total_success = 0
        total_requests = 0
        
        for symbol in symbol_list:
            logger.info(f"🔄 {symbol} 데이터 수집 중...")
            
            for data_type in data_type_list:
                total_requests += 1
                
                try:
                    if data_type == 'price':
                        # 현재가 데이터 수집
                        success = collect_price_data(kis_provider, db_manager, symbol)
                    elif data_type == 'chart':
                        # 차트 데이터 수집
                        success = collect_chart_data(
                            kis_provider, db_manager, symbol, 
                            chart_period, int(chart_count)
                        )
                    else:
                        logger.warning(f"⚠️ 지원하지 않는 데이터 타입: {data_type}")
                        continue
                    
                    if success:
                        total_success += 1
                        logger.info(f"✅ {symbol} {data_type} 수집 완료")
                    else:
                        logger.error(f"❌ {symbol} {data_type} 수집 실패")
                        
                except Exception as e:
                    logger.error(f"❌ {symbol} {data_type} 수집 중 오류: {e}")
        
        # 결과 요약
        success_rate = (total_success / total_requests * 100) if total_requests > 0 else 0
        logger.info(f"📊 수집 완료: {total_success}/{total_requests} ({success_rate:.1f}%)")
        
        # XCom으로 결과 반환
        return {
            'total_requests': total_requests,
            'total_success': total_success,
            'success_rate': success_rate,
            'symbols': symbol_list,
            'data_types': data_type_list
        }
        
    except Exception as e:
        logger.error(f"❌ KIS 데이터 수집 중 치명적 오류: {e}")
        raise
    finally:
        if 'db_manager' in locals():
            db_manager.disconnect()

def collect_price_data(kis_provider: KISDataProvider, db_manager: DatabaseManager, 
                      symbol: str) -> bool:
    """현재가 데이터 수집"""
    try:
        # KIS API 호출
        price_data = kis_provider.get_current_price(symbol)
        
        if not price_data or price_data.get('rt_cd') != '0':
            logger.warning(f"⚠️ {symbol} 현재가 데이터 없음 또는 오류")
            return False
        
        # DB 저장
        success = db_manager.save_kis_raw_data(
            symbol=symbol,
            api_endpoint=f"/domestic/price/{symbol}",
            data_type="price",
            market_type="domestic",
            request_params={},
            raw_response=price_data
        )
        
        return success
        
    except Exception as e:
        logger.error(f"❌ {symbol} 현재가 수집 실패: {e}")
        return False

def collect_chart_data(kis_provider: KISDataProvider, db_manager: DatabaseManager, 
                      symbol: str, period: str, count: int) -> bool:
    """차트 데이터 수집"""
    try:
        # KIS API 호출
        chart_df = kis_provider.get_chart_data(symbol, period, count)
        
        if chart_df.empty:
            logger.warning(f"⚠️ {symbol} 차트 데이터 없음")
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
        
        # DB 저장
        success = db_manager.save_kis_raw_data(
            symbol=symbol,
            api_endpoint=f"/domestic/chart/{symbol}",
            data_type="chart",
            market_type="domestic",
            request_params={"period": period, "count": count},
            raw_response=raw_response
        )
        
        if success:
            logger.info(f"📊 {symbol} 차트 데이터 {len(chart_records)}건 저장")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ {symbol} 차트 데이터 수집 실패: {e}")
        return False

def validate_collection_result(**context):
    """데이터 수집 결과 검증"""
    
    # 이전 태스크 결과 가져오기
    result = context['task_instance'].xcom_pull(task_ids='collect_kis_data_task')
    
    if not result:
        logger.error("❌ 수집 결과 데이터 없음")
        raise ValueError("수집 결과 데이터 없음")
    
    success_rate = result.get('success_rate', 0)
    total_requests = result.get('total_requests', 0)
    
    logger.info(f"📊 수집 결과 검증:")
    logger.info(f"   - 전체 요청: {total_requests}")
    logger.info(f"   - 성공률: {success_rate:.1f}%")
    logger.info(f"   - 종목: {result.get('symbols', [])}")
    
    # 성공률이 50% 미만이면 경고
    if success_rate < 50:
        logger.warning(f"⚠️ 데이터 수집 성공률이 낮습니다: {success_rate:.1f}%")
    
    # DB에서 실제 저장된 데이터 확인
    try:
        db_manager = DatabaseManager()
        summary = db_manager.get_market_data_summary(days=1)
        logger.info(f"📈 DB 저장 현황: {summary}")
        db_manager.disconnect()
    except Exception as e:
        logger.error(f"❌ DB 검증 실패: {e}")
    
    return result

# DAG 태스크 정의
collect_data_task = PythonOperator(
    task_id='collect_kis_data_task',
    python_callable=collect_kis_data,
    provide_context=True,
    dag=dag,
)

validate_result_task = PythonOperator(
    task_id='validate_collection_result',
    python_callable=validate_collection_result,
    provide_context=True,
    dag=dag,
)

# 태스크 의존성 설정
collect_data_task >> validate_result_task