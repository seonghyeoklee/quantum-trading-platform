"""
Quantum Trading Platform - 실시간 모니터링 DAG
장중 실시간 주요 종목 모니터링 파이프라인

Author: Quantum Trading Platform
Created: 2025-09-04
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
# from airflow.operators.http import SimpleHttpOperator  # HTTP operators 미사용
from airflow.operators.dummy import DummyOperator
import logging

# DAG 기본 설정
default_args = {
    'owner': 'quantum-trading',
    'depends_on_past': False,
    'start_date': datetime(2025, 9, 4),
    'email_on_failure': False,  # 실시간은 알림 끄기
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
    'execution_timeout': timedelta(minutes=10),
}

# DAG 정의  
dag = DAG(
    'quantum_realtime_monitoring',
    default_args=default_args,
    description='실시간 주요 종목 모니터링',
    schedule_interval='*/30 9-15 * * 1-5',  # 평일 9시-15시 30분마다
    catchup=False,
    tags=['quantum', 'stock', 'realtime', 'monitoring'],
    max_active_runs=1,
)

# ================================================================
# Task Functions
# ================================================================

def check_trading_hours(**context):
    """거래시간 확인"""
    from datetime import datetime
    import holidays
    
    execution_date = context['execution_date']
    current_hour = execution_date.hour
    
    # 한국 공휴일 확인
    kr_holidays = holidays.SouthKorea()
    is_holiday = execution_date.date() in kr_holidays
    is_weekend = execution_date.weekday() >= 5
    
    # 거래시간 확인 (9:00-15:30)
    is_trading_hours = 9 <= current_hour <= 15
    
    if is_weekend or is_holiday or not is_trading_hours:
        raise Exception("거래시간 외 모니터링 스킵")
    
    logging.info(f"✅ 거래시간 확인: {execution_date}")
    return True

def monitor_key_stocks(**context):
    """주요 종목 실시간 모니터링"""
    import sys
    sys.path.append('/opt/airflow/quantum_analysis')
    
    try:
        # 주요 종목 리스트 (TOP 20)
        key_symbols = [
            "005930", "000660", "035420", "035720", "207940",  # 대형주
            "005380", "012330", "000270", "068270", "326030",  # 자동차/바이오
            "AAPL", "MSFT", "GOOGL", "TSLA", "AMZN",           # 미국 주요주
            "NVDA", "META", "JPM", "JNJ", "V"                 # 미국 추가
        ]
        
        from core.multi_data_provider import MultiDataProvider
        from datetime import datetime, timedelta
        
        provider = MultiDataProvider(enable_kis=True)
        
        snapshots = []
        for symbol in key_symbols:
            try:
                # 최근 5일 데이터로 빠른 체크
                end_date = datetime.now()
                start_date = end_date - timedelta(days=5)
                
                market_data = provider.get_stock_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if market_data and not market_data.data.empty:
                    latest = market_data.data.iloc[-1]
                    prev = market_data.data.iloc[-2] if len(market_data.data) > 1 else latest
                    
                    snapshot = {
                        'symbol': symbol,
                        'timestamp': datetime.now().isoformat(),
                        'current_price': float(latest['close']),
                        'price_change': float(latest['close'] - prev['close']),
                        'price_change_rate': float((latest['close'] / prev['close'] - 1) * 100),
                        'volume': int(latest['volume']),
                        'data_source': market_data.source.value
                    }
                    snapshots.append(snapshot)
                    
            except Exception as e:
                logging.warning(f"⚠️  종목 모니터링 실패 {symbol}: {e}")
                continue
        
        logging.info(f"✅ 실시간 모니터링 완료: {len(snapshots)}개 종목")
        
        # Spring Boot API로 실시간 데이터 전송
        return {
            'monitored_stocks': len(snapshots),
            'snapshots': snapshots[:10],  # 상위 10개만 로그에
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.error(f"❌ 실시간 모니터링 오류: {e}")
        raise

def update_realtime_data(**context):
    """실시간 데이터 업데이트"""
    task_instance = context['task_instance']
    monitoring_data = task_instance.xcom_pull(task_ids='monitor_key_stocks')
    
    logging.info(f"📊 실시간 데이터 업데이트: {monitoring_data['monitored_stocks']}개 종목")
    
    # TODO: PostgreSQL realtime_snapshots 테이블에 저장
    # TODO: WebSocket으로 프론트엔드에 실시간 전송
    
    return {"realtime_update": True, "count": monitoring_data['monitored_stocks']}

# ================================================================
# Task Definitions
# ================================================================

# 거래시간 확인
check_hours = PythonOperator(
    task_id='check_trading_hours',
    python_callable=check_trading_hours,
    dag=dag
)

# 주요 종목 모니터링
monitor_stocks = PythonOperator(
    task_id='monitor_key_stocks',
    python_callable=monitor_key_stocks,
    dag=dag
)

# 실시간 데이터 업데이트
update_data = PythonOperator(
    task_id='update_realtime_data',
    python_callable=update_realtime_data,
    dag=dag
)

# Spring Boot WebSocket 알림 (나중에 구현)
notify_websocket = DummyOperator(
    task_id='notify_websocket',
    dag=dag
)

# ================================================================
# Task Dependencies  
# ================================================================

check_hours >> monitor_stocks >> update_data >> notify_websocket