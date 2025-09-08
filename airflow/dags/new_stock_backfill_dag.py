"""
신규 종목 백필 DAG (Stock_Data__15_New_Stock_Backfill)
- domestic_stocks_detail에 없는 종목들의 장기 히스토리 데이터 수집
- 2년치 OHLCV 데이터 백필
- 주 1회 실행으로 신규 상장 종목 자동 감지
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


# ========================================
# DAG 설정
# ========================================
default_args = {
    'owner': 'quantum-trading',
    'depends_on_past': False,
    'start_date': datetime(2025, 9, 8, tzinfo=pytz.timezone("Asia/Seoul")),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=15),
    'execution_timeout': timedelta(hours=8),
}

dag = DAG(
    dag_id='Stock_Data__15_New_Stock_Backfill',
    default_args=default_args,
    description='신규 종목 백필 - domestic_stocks_detail에 없는 종목들의 2년치 히스토리 데이터 수집',
    schedule_interval='0 1 * * 0',  # 매주 일요일 새벽 1시
    max_active_runs=1,
    catchup=False,
    tags=['backfill', 'new-stocks', 'batch', 'historical-data', 'kis-api'],
)

# ========================================
# KIS API 클라이언트 (백필용)
# ========================================

class KISBackfillClient:
    """신규 종목 백필용 KIS API 클라이언트"""
    
    def __init__(self):
        self.adapter_base_url = "http://host.docker.internal:8000"
        self.request_delay = 0.1  # 100ms 지연 (KIS API 레이트 리미팅)
    
    def get_chart_data_with_retry(self, stock_code: str, retries: int = 3) -> Optional[Dict]:
        """재시도 로직이 포함된 차트 데이터 조회"""
        for attempt in range(retries):
            try:
                print(f"🔍 [{attempt+1}/{retries}] KIS API 호출: {stock_code}")
                
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
                    print(f"❌ {stock_code}: KIS API 오류 - {kis_data.get('msg1', 'Unknown')}")
                    return None
                    
                if not kis_data.get('output2'):
                    print(f"❌ {stock_code}: output2 데이터 없음")
                    return None
                    
                print(f"✅ {stock_code}: KIS API에서 {len(kis_data['output2'])}일 데이터 조회 성공")
                
                # API 레이트 리미팅 준수
                time.sleep(self.request_delay)
                return kis_data
                
            except Exception as e:
                print(f"⚠️ {stock_code} 시도 {attempt+1} 실패: {e}")
                if attempt < retries - 1:
                    wait_time = (attempt + 1) * 2  # 2초, 4초, 6초 대기
                    print(f"🔄 {wait_time}초 후 재시도...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ {stock_code}: 모든 재시도 실패")
                    
        return None

# ========================================
# 핵심 함수들
# ========================================

def find_new_stocks(**context):
    """domestic_stocks_detail에 없는 신규 종목 발견"""
    
    print("🔍 신규 종목 탐지 시작...")
    
    pg_hook = PostgresHook(postgres_conn_id='quantum_postgres')
    
    # domestic_stocks에는 있지만 domestic_stocks_detail에 없는 종목 찾기
    find_new_sql = """
    SELECT ds.stock_code, ds.stock_name, ds.market_type
    FROM domestic_stocks ds
    WHERE ds.is_active = true
    AND ds.stock_code NOT IN (
        SELECT DISTINCT stock_code 
        FROM domestic_stocks_detail
    )
    ORDER BY ds.market_type, ds.stock_code;
    """
    
    new_stocks = pg_hook.get_records(find_new_sql)
    
    if not new_stocks:
        print("✅ 신규 종목이 없습니다. 모든 종목이 이미 수집되었습니다.")
        return {'new_stocks_count': 0, 'new_stocks': []}
    
    new_stocks_list = [
        {'stock_code': row[0], 'stock_name': row[1], 'market_type': row[2]}
        for row in new_stocks
    ]
    
    print(f"📊 발견된 신규 종목: {len(new_stocks_list)}개")
    for stock in new_stocks_list[:5]:  # 처음 5개만 로그
        print(f"  - {stock['stock_code']}: {stock['stock_name']} ({stock['market_type']})")
    
    if len(new_stocks_list) > 5:
        print(f"  ... 및 {len(new_stocks_list)-5}개 더")
    
    # XCom으로 신규 종목 리스트 전달
    context['task_instance'].xcom_push(key='new_stocks', value=new_stocks_list)
    
    return {
        'new_stocks_count': len(new_stocks_list),
        'new_stocks': new_stocks_list[:10],  # 상위 10개만 반환
        'discovery_time': datetime.now(pytz.timezone("Asia/Seoul")).isoformat()
    }


def backfill_new_stocks(**context):
    """신규 종목들의 2년치 히스토리 데이터 백필"""
    
    print("🚀 신규 종목 백필 작업 시작...")
    
    # XCom에서 신규 종목 리스트 가져오기
    new_stocks = context['task_instance'].xcom_pull(key='new_stocks', task_ids='find_new_stocks')
    
    if not new_stocks:
        print("✅ 백필할 신규 종목이 없습니다.")
        return {'backfilled_count': 0, 'total_records': 0}
    
    print(f"📦 {len(new_stocks)}개 신규 종목 백필 시작")
    
    # KIS API 클라이언트 초기화
    kis_client = KISBackfillClient()
    pg_hook = PostgresHook(postgres_conn_id='quantum_postgres')
    
    success_count = 0
    error_count = 0
    total_records = 0
    
    # 배치 처리 (20개씩)
    batch_size = 20
    for i in range(0, len(new_stocks), batch_size):
        batch = new_stocks[i:i+batch_size]
        batch_num = i // batch_size + 1
        
        print(f"📦 배치 {batch_num}/{(len(new_stocks)-1)//batch_size + 1}: {len(batch)}개 종목 처리 중...")
        
        for stock in batch:
            stock_code = stock['stock_code']
            stock_name = stock['stock_name']
            
            try:
                print(f"🔄 {stock_code} ({stock_name}) 백필 시작...")
                
                # 2년치 차트 데이터 조회
                chart_response = kis_client.get_chart_data_with_retry(stock_code)
                
                if chart_response and chart_response.get('rt_cd') == '0':
                    chart_data = chart_response['output2']
                    
                    # 데이터 저장
                    saved_count = save_backfill_data_to_db(pg_hook, stock_code, chart_data, chart_response)
                    total_records += saved_count
                    success_count += 1
                    
                    print(f"✅ {stock_code}: {saved_count}일 백필 데이터 저장 완료")
                    
                else:
                    print(f"❌ {stock_code}: 백필 실패 (KIS API 오류)")
                    error_count += 1
                    
            except Exception as e:
                print(f"❌ {stock_code} 백필 중 오류: {e}")
                error_count += 1
                continue
        
        # 배치 간 휴식 (API 안정성)
        if i + batch_size < len(new_stocks):
            print("⏸️ 배치 간 30초 휴식...")
            time.sleep(30)
    
    result = {
        'backfilled_count': success_count,
        'error_count': error_count,
        'total_records': total_records,
        'backfill_time': datetime.now(pytz.timezone("Asia/Seoul")).isoformat()
    }
    
    print(f"🎉 신규 종목 백필 완료: {success_count}개 성공, {total_records}개 레코드")
    return result


def save_backfill_data_to_db(pg_hook: PostgresHook, stock_code: str, chart_data: List[Dict], full_response: Dict) -> int:
    """백필 데이터를 domestic_stocks_detail에 저장"""
    
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
        request_timestamp = EXCLUDED.request_timestamp,
        updated_at = NOW(),
        data_quality = 'EXCELLENT';
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
                                'backfill_source': 'new_stock_backfill_dag'
                            }),
                            'request_params': json.dumps({
                                'stock_code': stock_code,
                                'period': '2years',
                                'data_type': 'backfill',
                                'source': 'new_stock_detection'
                            }),
                        })
                        saved_count += 1
                        
                    except Exception as e:
                        print(f"❌ {stock_code} {daily_data.get('stck_bsop_date', 'unknown')} 저장 오류: {e}")
                        continue
                
                conn.commit()
                
    except Exception as e:
        print(f"❌ {stock_code} 데이터베이스 오류: {e}")
        raise
    
    return saved_count


def validate_backfill_results(**context):
    """백필 결과 검증"""
    
    print("🔍 백필 결과 검증 시작...")
    
    pg_hook = PostgresHook(postgres_conn_id='quantum_postgres')
    
    # 전체 종목 커버리지 확인
    coverage_sql = """
    SELECT 
        COUNT(*) as total_stocks,
        COUNT(DISTINCT dsd.stock_code) as covered_stocks,
        ROUND(COUNT(DISTINCT dsd.stock_code) * 100.0 / COUNT(*), 2) as coverage_percentage
    FROM domestic_stocks ds
    LEFT JOIN domestic_stocks_detail dsd ON ds.stock_code = dsd.stock_code
    WHERE ds.is_active = true;
    """
    
    coverage = pg_hook.get_first(coverage_sql)
    total_stocks, covered_stocks, coverage_pct = coverage
    
    print(f"📊 전체 종목 커버리지:")
    print(f"  - 전체 활성 종목: {total_stocks:,}개")
    print(f"  - 데이터 보유 종목: {covered_stocks:,}개")
    print(f"  - 커버리지: {coverage_pct}%")
    
    # 백필 품질 확인
    quality_sql = """
    SELECT 
        data_quality,
        COUNT(*) as record_count,
        COUNT(DISTINCT stock_code) as stock_count
    FROM domestic_stocks_detail
    WHERE created_at >= NOW() - INTERVAL '24 hours'
    GROUP BY data_quality
    ORDER BY record_count DESC;
    """
    
    quality_stats = pg_hook.get_records(quality_sql)
    
    print(f"📈 최근 24시간 백필 품질:")
    for quality, record_count, stock_count in quality_stats:
        print(f"  - {quality}: {record_count:,}건 ({stock_count}개 종목)")
    
    return {
        'total_stocks': total_stocks,
        'covered_stocks': covered_stocks,
        'coverage_percentage': float(coverage_pct),
        'validation_time': datetime.now(pytz.timezone("Asia/Seoul")).isoformat()
    }


# ========================================
# DAG 태스크 정의
# ========================================

# 1. 신규 종목 발견
find_new_stocks_task = PythonOperator(
    task_id='find_new_stocks',
    python_callable=find_new_stocks,
    dag=dag,
)

# 2. 신규 종목 백필
backfill_new_stocks_task = PythonOperator(
    task_id='backfill_new_stocks',
    python_callable=backfill_new_stocks,
    dag=dag,
)

# 3. 백필 결과 검증
validate_backfill_task = PythonOperator(
    task_id='validate_backfill_results',
    python_callable=validate_backfill_results,
    dag=dag,
)

# 4. 완료 알림
completion_notification_task = BashOperator(
    task_id='completion_notification',
    bash_command='''
    echo "🎉 신규 종목 백필 완료!"
    echo "실행 시간: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "DAG: Stock_Data__15_New_Stock_Backfill"
    echo "주기: 매주 일요일 새벽 1시"
    echo "목적: 신규 상장 종목 자동 감지 및 2년치 히스토리 백필"
    ''',
    dag=dag,
)

# ========================================
# 태스크 의존성
# ========================================
find_new_stocks_task >> backfill_new_stocks_task >> validate_backfill_task >> completion_notification_task