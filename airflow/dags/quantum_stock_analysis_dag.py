"""
Quantum Trading Platform - 주식 분석 DAG
일간 주식 분석 파이프라인

Author: Quantum Trading Platform
Created: 2025-09-04
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
# from airflow.operators.http import SimpleHttpOperator  # HTTP operators 미사용
from airflow.operators.dummy import DummyOperator
from airflow.sensors.filesystem import FileSensor
import logging

# DAG 기본 설정
default_args = {
    'owner': 'quantum-trading',
    'depends_on_past': False,
    'start_date': datetime(2025, 9, 4),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=1),
}

# DAG 정의
dag = DAG(
    'quantum_daily_stock_analysis',
    default_args=default_args,
    description='일간 종합 주식 분석 파이프라인',
    schedule_interval='30 6 * * 1-5',  # 평일 오전 6시 30분 (시장 마감 후)
    catchup=False,
    tags=['quantum', 'stock', 'analysis', 'daily'],
    max_active_runs=1,  # 동시 실행 방지
)

# ================================================================
# Task Functions
# ================================================================

def check_market_status(**context):
    """시장 상태 확인"""
    from datetime import datetime
    import holidays
    
    execution_date = context['execution_date']
    
    # 한국 공휴일 확인
    kr_holidays = holidays.SouthKorea()
    us_holidays = holidays.UnitedStates()
    
    is_kr_holiday = execution_date.date() in kr_holidays
    is_us_holiday = execution_date.date() in us_holidays
    is_weekend = execution_date.weekday() >= 5
    
    logging.info(f"Market Status Check:")
    logging.info(f"  Date: {execution_date.date()}")
    logging.info(f"  Weekend: {is_weekend}")
    logging.info(f"  KR Holiday: {is_kr_holiday}")
    logging.info(f"  US Holiday: {is_us_holiday}")
    
    # 테스트를 위해 주말만 스킵하도록 수정
    if is_weekend:
        logging.warning("주말이므로 분석 스킵")
        raise Exception("주말로 인한 분석 스킵")
    
    # 평일에는 항상 실행 (테스트용)
    logging.info("✅ 분석 진행 (테스트 모드)")
    
    return {
        'kr_market_open': not is_kr_holiday,
        'us_market_open': not is_us_holiday,
        'analysis_date': execution_date.strftime('%Y-%m-%d')
    }

def run_comprehensive_analysis(**context):
    """종합 주식 분석 실행"""
    import sys
    import os
    
    # Python path 추가
    sys.path.append('/opt/airflow/quantum_analysis')
    
    try:
        from comprehensive_batch_analyzer import ComprehensiveBatchAnalyzer
        from db_manager import DatabaseManager
        
        logging.info("🚀 종합 주식 분석 시작...")
        
        # 분석기 초기화
        analyzer = ComprehensiveBatchAnalyzer()
        
        # 분석 실행 (동기 버전)
        results = analyzer.run_comprehensive_analysis_sync()
        
        if not results:
            raise Exception("분석 결과가 없습니다")
        
        # 데이터베이스 저장
        db = DatabaseManager()
        success = db.save_analysis_result(results)
        
        if not success:
            raise Exception("데이터베이스 저장 실패")
        
        logging.info(f"✅ 분석 완료: {len(results.get('analysis_results', []))}개 종목")
        
        return {
            'total_stocks': len(results.get('analysis_results', [])),
            'analysis_completed': True,
            'db_saved': success
        }
        
    except Exception as e:
        logging.error(f"❌ 분석 실행 오류: {e}")
        raise

def generate_analysis_summary(**context):
    """분석 요약 생성"""
    import sys
    sys.path.append('/opt/airflow/quantum_analysis')
    
    try:
        from db_manager import DatabaseManager
        
        db = DatabaseManager()
        summary = db.get_analysis_summary()
        
        if not summary:
            raise Exception("분석 요약 데이터 없음")
        
        logging.info("📊 분석 요약:")
        logging.info(f"  총 종목: {summary.get('total_stocks', 0)}개")
        logging.info(f"  평균 점수: {summary.get('total_avg_score', 0):.1f}점")
        logging.info(f"  매수 추천: {summary.get('buy_recommend_count', 0)}개")
        
        return summary
        
    except Exception as e:
        logging.error(f"❌ 요약 생성 오류: {e}")
        raise

def send_analysis_notification(**context):
    """분석 완료 알림"""
    task_instance = context['task_instance']
    summary_data = task_instance.xcom_pull(task_ids='generate_summary')
    
    logging.info("📨 분석 완료 알림 발송")
    logging.info(f"분석 결과: {summary_data}")
    
    # TODO: 실제 알림 시스템 연동 (이메일, 슬랙 등)
    return {"notification_sent": True}

# ================================================================
# Task Definitions
# ================================================================

# 시작 더미 태스크
start_task = DummyOperator(
    task_id='start_analysis_pipeline',
    dag=dag
)

# 시장 상태 확인
market_check = PythonOperator(
    task_id='check_market_status',
    python_callable=check_market_status,
    dag=dag
)

# 종합 분석 실행
run_analysis = PythonOperator(
    task_id='run_comprehensive_analysis',
    python_callable=run_comprehensive_analysis,
    dag=dag
)

# 분석 요약 생성
generate_summary = PythonOperator(
    task_id='generate_summary',
    python_callable=generate_analysis_summary,
    dag=dag
)

# 분석 완료 로그 (Spring API는 나중에 추가)
log_completion = DummyOperator(
    task_id='log_analysis_completion',
    dag=dag
)

# 분석 완료 알림
send_notification = PythonOperator(
    task_id='send_notification',
    python_callable=send_analysis_notification,
    dag=dag
)

# 종료 더미 태스크
end_task = DummyOperator(
    task_id='analysis_pipeline_complete',
    dag=dag
)

# ================================================================
# Task Dependencies
# ================================================================

start_task >> market_check >> run_analysis >> generate_summary >> log_completion >> send_notification >> end_task