"""
특정 종목 2년치 데이터 수집 DAG (Stock_Data__17_Custom_Backfill)
- 사용자가 지정한 특정 종목들의 2년치 히스토리 데이터 수집
- 수동 실행으로 필요할 때만 작동
- UPSERT 방식으로 중복 데이터 자동 관리
- 실제 KIS API 연동
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pytz

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.models import DagRun


# ========================================
# DAG 설정
# ========================================
default_args = {
    'owner': 'quantum-trading',
    'depends_on_past': False,
    'start_date': datetime(2025, 9, 9, tzinfo=pytz.timezone("Asia/Seoul")),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=15),
    'execution_timeout': timedelta(hours=6),
}

dag = DAG(
    dag_id='Stock_Data__17_Custom_Backfill',
    default_args=default_args,
    description='특정 종목 2년치 데이터 수집 - 사용자 지정 종목들의 히스토리 데이터 백필 (수동 실행)',
    schedule_interval=None,  # 수동 실행만
    max_active_runs=1,
    catchup=False,
    tags=['custom-backfill', 'manual', 'historical-data', 'kis-api', 'user-specified'],
    params={
        "stock_codes": ["005930", "000660", "035720"],  # 기본값: 삼성전자, SK하이닉스, 카카오
        "period_days": 730,  # 기본값: 2년
        "batch_size": 20,    # 배치 크기
    }
)

# ========================================
# 상수 정의
# ========================================

# 배치 처리 설정
DEFAULT_BATCH_SIZE = 20
DEFAULT_PERIOD_DAYS = 730  # 2년
REQUEST_DELAY = 0.05  # 50ms API 호출 간격
BATCH_DELAY = 15  # 배치 간 15초 대기

# ========================================
# KIS API 클라이언트 (커스텀 백필용)
# ========================================

class KISCustomBackfillClient:
    """커스텀 백필용 KIS API 클라이언트"""
    
    def __init__(self):
        self.adapter_base_url = "http://host.docker.internal:8000"
        self.request_delay = REQUEST_DELAY
        self.success_count = 0
        self.error_count = 0
    
    def get_historical_data(self, stock_code: str, retries: int = 3) -> Optional[Dict]:
        """2년치 히스토리 데이터 조회 (재시도 포함)"""
        for attempt in range(retries):
            try:
                print(f"🔍 [{attempt+1}/{retries}] {stock_code} 2년치 데이터 조회...")
                
                url = f"{self.adapter_base_url}/domestic/chart/{stock_code}"
                params = {
                    'period': 'D',  # 일봉
                    'adj_price': 1  # 수정주가
                }
                
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                kis_data = response.json()
                
                # KIS API 응답 검증
                if kis_data.get('rt_cd') != '0':
                    if attempt == 0:  # 첫 번째 시도에서만 로그
                        print(f"❌ {stock_code}: KIS API 오류 - {kis_data.get('msg1', 'Unknown')}")
                    return None
                
                if not kis_data.get('output2'):
                    if attempt == 0:
                        print(f"❌ {stock_code}: output2 데이터 없음")
                    return None
                
                chart_data = kis_data['output2']
                print(f"✅ {stock_code}: KIS API에서 {len(chart_data)}일 데이터 조회 성공")
                
                self.success_count += 1
                time.sleep(self.request_delay)
                return kis_data
                
            except Exception as e:
                if attempt == retries - 1:  # 마지막 시도에서만 에러 카운트
                    self.error_count += 1
                    print(f"❌ {stock_code} 최종 실패: {e}")
                else:
                    wait_time = (attempt + 1) * 2  # 2초, 4초, 6초 대기
                    print(f"🔄 {stock_code} 재시도 전 {wait_time}초 대기...")
                    time.sleep(wait_time)
        
        return None

# ========================================
# 핵심 함수들
# ========================================

def validate_custom_stocks(**context):
    """사용자가 지정한 종목들의 유효성 검증"""
    
    print("🔍 사용자 지정 종목 유효성 검증 시작...")
    
    # DAG 실행 시 전달된 파라미터 가져오기
    dag_run: DagRun = context['dag_run']
    conf = dag_run.conf or {}
    
    stock_codes = conf.get('stock_codes', dag.params['stock_codes'])
    period_days = conf.get('period_days', dag.params['period_days'])
    batch_size = conf.get('batch_size', dag.params['batch_size'])
    
    print(f"📊 요청된 설정:")
    print(f"  - 종목 코드: {stock_codes}")
    print(f"  - 수집 기간: {period_days}일")
    print(f"  - 배치 크기: {batch_size}")
    
    if not stock_codes or len(stock_codes) == 0:
        raise ValueError("종목 코드가 지정되지 않았습니다.")
    
    # PostgreSQL 연결
    pg_hook = PostgresHook(postgres_conn_id='quantum_postgres')
    
    # domestic_stocks에서 종목 유효성 검증
    placeholders = ','.join(['%s'] * len(stock_codes))
    validation_sql = f"""
    SELECT stock_code, stock_name, market_type, is_active
    FROM domestic_stocks 
    WHERE stock_code IN ({placeholders})
    ORDER BY market_type, stock_code;
    """
    
    valid_stocks = pg_hook.get_records(validation_sql, parameters=stock_codes)
    
    valid_stock_codes = [row[0] for row in valid_stocks]
    invalid_codes = [code for code in stock_codes if code not in valid_stock_codes]
    inactive_stocks = [row for row in valid_stocks if not row[3]]  # is_active가 False인 것들
    
    print(f"📈 종목 검증 결과:")
    print(f"  - 유효한 종목: {len(valid_stock_codes)}개")
    print(f"  - 무효한 종목: {len(invalid_codes)}개")
    print(f"  - 비활성 종목: {len(inactive_stocks)}개")
    
    if invalid_codes:
        print(f"⚠️ 무효한 종목 코드: {invalid_codes}")
    
    if inactive_stocks:
        inactive_codes = [row[0] for row in inactive_stocks]
        print(f"⚠️ 비활성 종목: {inactive_codes}")
    
    if not valid_stock_codes:
        raise ValueError("유효한 종목이 하나도 없습니다.")
    
    # 유효한 종목 정보를 구조화
    validated_stocks = []
    for row in valid_stocks:
        if row[3]:  # 활성 종목만
            validated_stocks.append({
                'stock_code': row[0],
                'stock_name': row[1],
                'market_type': row[2],
                'is_active': row[3]
            })
    
    # XCom으로 검증된 정보 전달
    context['task_instance'].xcom_push(key='validated_stocks', value=validated_stocks)
    context['task_instance'].xcom_push(key='period_days', value=period_days)
    context['task_instance'].xcom_push(key='batch_size', value=batch_size)
    
    return {
        'total_requested': len(stock_codes),
        'valid_stocks_count': len(validated_stocks),
        'invalid_codes': invalid_codes,
        'inactive_codes': [row[0] for row in inactive_stocks],
        'validated_stocks': validated_stocks[:5],  # 상위 5개만 반환
        'validation_time': datetime.now(pytz.timezone("Asia/Seoul")).isoformat()
    }


def fetch_custom_stock_data(**context):
    """사용자 지정 종목들의 2년치 데이터 수집"""
    
    print("🚀 커스텀 종목 데이터 수집 시작...")
    
    # XCom에서 검증된 종목 정보 가져오기
    validated_stocks = context['task_instance'].xcom_pull(key='validated_stocks', task_ids='validate_custom_stocks')
    batch_size = context['task_instance'].xcom_pull(key='batch_size', task_ids='validate_custom_stocks')
    
    if not validated_stocks:
        print("✅ 수집할 종목이 없습니다.")
        return {'collected_count': 0, 'total_records': 0}
    
    print(f"📦 {len(validated_stocks)}개 종목을 {batch_size}개씩 배치 처리...")
    
    # KIS API 클라이언트 초기화
    kis_client = KISCustomBackfillClient()
    pg_hook = PostgresHook(postgres_conn_id='quantum_postgres')
    
    total_collected = 0
    total_records = 0
    total_errors = 0
    
    # 배치별 처리
    for i in range(0, len(validated_stocks), batch_size):
        batch = validated_stocks[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(validated_stocks) - 1) // batch_size + 1
        
        print(f"📦 배치 {batch_num}/{total_batches}: {len(batch)}개 종목 처리 중...")
        
        batch_collected = 0
        batch_records = 0
        
        for stock in batch:
            stock_code = stock['stock_code']
            stock_name = stock['stock_name']
            
            try:
                print(f"🔄 {stock_code} ({stock_name}) 데이터 수집 시작...")
                
                # 2년치 차트 데이터 조회
                chart_response = kis_client.get_historical_data(stock_code)
                
                if chart_response and chart_response.get('rt_cd') == '0':
                    chart_data = chart_response['output2']
                    
                    # 데이터베이스에 저장
                    saved_count = save_custom_backfill_to_db(pg_hook, stock_code, chart_data, chart_response)
                    total_records += saved_count
                    batch_collected += 1
                    batch_records += saved_count
                    
                    print(f"✅ {stock_code}: {saved_count}일 데이터 저장 완료")
                    
                else:
                    print(f"❌ {stock_code}: 데이터 수집 실패")
                    total_errors += 1
                    
            except Exception as e:
                print(f"❌ {stock_code} 처리 중 오류: {e}")
                total_errors += 1
                continue
        
        total_collected += batch_collected
        
        print(f"  배치 {batch_num} 완료: {batch_collected}/{len(batch)}개 수집, {batch_records:,}건 저장")
        
        # 배치 간 휴식 (마지막 배치 제외)
        if i + batch_size < len(validated_stocks):
            print(f"⏸️ {BATCH_DELAY}초 휴식...")
            time.sleep(BATCH_DELAY)
    
    result = {
        'collected_count': total_collected,
        'total_records': total_records,
        'error_count': total_errors,
        'api_success_count': kis_client.success_count,
        'api_error_count': kis_client.error_count,
        'collection_time': datetime.now(pytz.timezone("Asia/Seoul")).isoformat()
    }
    
    print(f"🎉 커스텀 데이터 수집 완료: {total_collected}개 종목, {total_records:,}건 저장")
    print(f"📊 API 호출 결과: {kis_client.success_count}개 성공, {kis_client.error_count}개 실패")
    
    return result


def save_custom_backfill_to_db(pg_hook: PostgresHook, stock_code: str, chart_data: List[Dict], full_response: Dict) -> int:
    """커스텀 백필 데이터를 domestic_stocks_detail에 UPSERT로 저장"""
    
    if not chart_data:
        return 0
    
    # UPSERT SQL (기존 데이터가 있으면 업데이트, 없으면 생성)
    upsert_sql = """
    INSERT INTO domestic_stocks_detail (
        stock_code,
        trade_date,
        current_price,
        volume,
        data_type,
        api_endpoint,
        raw_response,
        request_params,
        request_timestamp,
        created_at,
        updated_at,
        response_code,
        data_quality
    ) VALUES (
        %(stock_code)s,
        TO_DATE(%(trade_date)s, 'YYYYMMDD'),
        %(close_price)s,
        %(volume)s,
        'CHART',
        '/uapi/domestic-stock/v1/quotations/inquire-daily-price',
        %(raw_response)s,
        %(request_params)s,
        NOW(),
        NOW(),
        NOW(),
        '0',
        'EXCELLENT'
    )
    ON CONFLICT (stock_code, trade_date, data_type)
    DO UPDATE SET
        current_price = EXCLUDED.current_price,
        volume = EXCLUDED.volume,
        raw_response = EXCLUDED.raw_response,
        request_params = EXCLUDED.request_params,
        request_timestamp = EXCLUDED.request_timestamp,
        updated_at = NOW(),
        data_quality = 'EXCELLENT',
        response_code = '0';
    """
    
    saved_count = 0
    
    try:
        with pg_hook.get_conn() as conn:
            with conn.cursor() as cursor:
                for daily_data in chart_data:
                    try:
                        # OHLCV 데이터 추출
                        ohlcv_data = {
                            'open': int(daily_data['stck_oprc']),
                            'high': int(daily_data['stck_hgpr']),
                            'low': int(daily_data['stck_lwpr']),
                            'close': int(daily_data['stck_clpr']),
                            'volume': int(daily_data['acml_vol']),
                        }
                        
                        cursor.execute(upsert_sql, {
                            'stock_code': stock_code,
                            'trade_date': daily_data['stck_bsop_date'],
                            'close_price': ohlcv_data['close'],
                            'volume': ohlcv_data['volume'],
                            'raw_response': json.dumps({
                                **daily_data,
                                'ohlcv': ohlcv_data,
                                'custom_backfill_source': 'custom_stock_backfill_dag',
                                'backfill_timestamp': datetime.now(pytz.timezone("Asia/Seoul")).isoformat()
                            }),
                            'request_params': json.dumps({
                                'stock_code': stock_code,
                                'period': '2years_custom',
                                'data_type': 'custom_backfill',
                                'source': 'user_specified_backfill'
                            }),
                        })
                        saved_count += 1
                        
                    except Exception as e:
                        print(f"❌ {stock_code} {daily_data.get('stck_bsop_date', 'unknown')} 저장 오류: {e}")
                        continue
                
                conn.commit()
                
    except Exception as e:
        print(f"❌ {stock_code} 데이터베이스 커넥션 오류: {e}")
        raise
    
    return saved_count


def validate_custom_results(**context):
    """커스텀 백필 결과 검증"""
    
    print("🔍 커스텀 백필 결과 검증 시작...")
    
    pg_hook = PostgresHook(postgres_conn_id='quantum_postgres')
    
    # 수집 결과 가져오기
    collection_result = context['task_instance'].xcom_pull(task_ids='fetch_custom_stock_data') or {}
    validated_stocks = context['task_instance'].xcom_pull(key='validated_stocks', task_ids='validate_custom_stocks')
    
    collected_count = collection_result.get('collected_count', 0)
    total_records = collection_result.get('total_records', 0)
    
    # 오늘 저장된 커스텀 백필 데이터 확인
    today_sql = """
    SELECT 
        COUNT(DISTINCT stock_code) as updated_stocks,
        COUNT(*) as updated_records,
        MIN(trade_date) as earliest_date,
        MAX(trade_date) as latest_date
    FROM domestic_stocks_detail 
    WHERE DATE(created_at) = CURRENT_DATE
    AND data_type = 'CHART'
    AND raw_response::text LIKE '%custom_backfill_source%';
    """
    
    today_stats = pg_hook.get_first(today_sql)
    today_updated_stocks, today_updated_records, earliest_date, latest_date = today_stats
    
    # 개별 종목 데이터 확인
    if validated_stocks:
        stock_codes = [stock['stock_code'] for stock in validated_stocks]
        placeholders = ','.join(['%s'] * len(stock_codes))
        
        individual_sql = f"""
        SELECT 
            stock_code,
            COUNT(*) as record_count,
            MIN(trade_date) as earliest_date,
            MAX(trade_date) as latest_date
        FROM domestic_stocks_detail 
        WHERE stock_code IN ({placeholders})
        AND data_type = 'CHART'
        GROUP BY stock_code
        ORDER BY record_count DESC;
        """
        
        individual_stats = pg_hook.get_records(individual_sql, parameters=stock_codes)
        
        print(f"📈 개별 종목 데이터 현황:")
        for stock_code, record_count, earliest, latest in individual_stats[:5]:  # 상위 5개만 출력
            stock_name = next((s['stock_name'] for s in validated_stocks if s['stock_code'] == stock_code), 'Unknown')
            print(f"  - {stock_code} ({stock_name}): {record_count:,}건 ({earliest} ~ {latest})")
        
        if len(individual_stats) > 5:
            print(f"  ... 및 {len(individual_stats)-5}개 더")
    
    validation_result = {
        'requested_stocks': len(validated_stocks) if validated_stocks else 0,
        'collected_stocks': collected_count,
        'total_records_saved': total_records,
        'today_updated_stocks': today_updated_stocks or 0,
        'today_updated_records': today_updated_records or 0,
        'data_date_range': {
            'earliest': str(earliest_date) if earliest_date else None,
            'latest': str(latest_date) if latest_date else None
        },
        'success_rate': round(collected_count / len(validated_stocks) * 100, 1) if validated_stocks else 0,
        'validation_time': datetime.now(pytz.timezone("Asia/Seoul")).isoformat()
    }
    
    print(f"🎯 커스텀 백필 검증 결과:")
    print(f"  - 요청 종목: {validation_result['requested_stocks']}개")
    print(f"  - 수집 완료: {validation_result['collected_stocks']}개")
    print(f"  - 성공률: {validation_result['success_rate']}%")
    print(f"  - 저장된 레코드: {validation_result['total_records_saved']:,}건")
    print(f"  - 데이터 범위: {validation_result['data_date_range']['earliest']} ~ {validation_result['data_date_range']['latest']}")
    
    return validation_result


# ========================================
# DAG 태스크 정의
# ========================================

# 1. 사용자 지정 종목 유효성 검증
validate_stocks_task = PythonOperator(
    task_id='validate_custom_stocks',
    python_callable=validate_custom_stocks,
    dag=dag,
)

# 2. 커스텀 종목 데이터 수집
fetch_data_task = PythonOperator(
    task_id='fetch_custom_stock_data',
    python_callable=fetch_custom_stock_data,
    dag=dag,
)

# 3. 수집 결과 검증
validate_results_task = PythonOperator(
    task_id='validate_custom_results',
    python_callable=validate_custom_results,
    dag=dag,
)

# 4. 완료 알림
completion_notification_task = BashOperator(
    task_id='completion_notification',
    bash_command='''
    echo "🎉 특정 종목 2년치 데이터 수집 완료!"
    echo "실행 시간: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "DAG: Stock_Data__17_Custom_Backfill"
    echo "실행 방식: 수동 실행 (사용자 지정 종목)"
    echo "데이터 처리: UPSERT 방식으로 중복 자동 관리"
    ''',
    dag=dag,
)

# ========================================
# 태스크 의존성 설정
# ========================================
validate_stocks_task >> fetch_data_task >> validate_results_task >> completion_notification_task