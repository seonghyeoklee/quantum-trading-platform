"""
기존 종목 일일 업데이트 DAG (Stock_Data__16_Daily_Update)
- domestic_stocks_detail에 이미 있는 종목들의 최신 1일치 데이터 추가
- 전체 3,902개 종목 대상
- 매일 장 마감 후 실행
- 실제 KIS API 연동
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
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
    'retries': 3,
    'retry_delay': timedelta(minutes=10),
    'execution_timeout': timedelta(hours=4),
}

dag = DAG(
    dag_id='Stock_Data__16_Daily_Update',
    default_args=default_args,
    description='기존 종목 일일 업데이트 - 전체 종목의 최신 1일치 데이터 추가',
    schedule_interval='0 21 * * 1-5',  # 주중 오후 9시 (장 마감 후)
    max_active_runs=1,
    catchup=False,
    tags=['daily-update', 'all-stocks', 'incremental', 'kis-api', 'production'],
)

# ========================================
# 상수 정의
# ========================================

# 배치 처리 설정
BATCH_SIZE = 30  # 30개씩 처리 (안정성 중시)
BATCH_DELAY = 20  # 배치 간 20초 대기
REQUEST_DELAY = 0.05  # 50ms API 호출 간격 (초당 20회)

# 우선순위 종목 (빠른 처리)
PRIORITY_STOCKS = [
    '005930',  # 삼성전자
    '000660',  # SK하이닉스
    '035420',  # NAVER
    '005380',  # 현대차
    '000270',  # 기아
    '068270',  # 셀트리온
    '035720',  # 카카오
    '207940',  # 삼성바이오로직스
    '006400',  # 삼성SDI
    '051910',  # LG화학
]

# ========================================
# KIS API 클라이언트 (일일 업데이트용)
# ========================================

class KISDailyUpdateClient:
    """일일 업데이트용 KIS API 클라이언트"""
    
    def __init__(self):
        self.adapter_base_url = "http://host.docker.internal:8000"
        self.request_delay = REQUEST_DELAY
        self.success_count = 0
        self.error_count = 0
    
    def get_latest_data(self, stock_code: str, retries: int = 2) -> Optional[Dict]:
        """최신 1일치 데이터 조회 (재시도 포함)"""
        for attempt in range(retries):
            try:
                url = f"{self.adapter_base_url}/domestic/chart/{stock_code}"
                params = {
                    'period': 'D',
                    'adj_price': 1
                }
                
                response = requests.get(url, params=params, timeout=20)
                response.raise_for_status()
                
                kis_data = response.json()
                
                if kis_data.get('rt_cd') != '0':
                    if attempt == 0:  # 첫 번째 시도에서만 로그
                        print(f"⚠️ {stock_code}: KIS API 오류 - {kis_data.get('msg1', 'Unknown')}")
                    return None
                
                if not kis_data.get('output2'):
                    return None
                
                # 최신 거래일 1일치만 반환 (output2의 첫 번째 요소)
                latest_data = kis_data['output2'][0] if kis_data['output2'] else None
                if latest_data:
                    self.success_count += 1
                    time.sleep(self.request_delay)
                    return {
                        'rt_cd': kis_data['rt_cd'],
                        'latest_data': latest_data,
                        'full_response': kis_data
                    }
                
                return None
                
            except Exception as e:
                if attempt == retries - 1:  # 마지막 시도에서만 로그
                    self.error_count += 1
                    print(f"❌ {stock_code}: API 호출 실패 - {e}")
                else:
                    time.sleep(1)  # 재시도 전 1초 대기
        
        return None

# ========================================
# 핵심 함수들
# ========================================

def get_existing_stocks_status(**context):
    """기존 종목들의 최신 데이터 상태 확인"""
    
    print("🔍 기존 종목 데이터 상태 분석...")
    
    pg_hook = PostgresHook(postgres_conn_id='quantum_postgres')
    
    # 데이터가 있는 종목들과 최신 거래일 조회
    status_sql = """
    SELECT 
        ds.stock_code,
        ds.stock_name,
        ds.market_type,
        COALESCE(MAX(dsd.trade_date), '1900-01-01'::date) as latest_date,
        COUNT(dsd.stock_code) as data_count
    FROM domestic_stocks ds
    LEFT JOIN domestic_stocks_detail dsd ON ds.stock_code = dsd.stock_code
    WHERE ds.is_active = true
    GROUP BY ds.stock_code, ds.stock_name, ds.market_type
    HAVING COUNT(dsd.stock_code) > 0  -- 데이터가 있는 종목만
    ORDER BY 
        CASE WHEN ds.stock_code = ANY(ARRAY{priority_list}) THEN 1 ELSE 2 END,
        ds.market_type, 
        ds.stock_code;
    """.format(priority_list=str(PRIORITY_STOCKS).replace("'", "''"))
    
    existing_stocks = pg_hook.get_records(status_sql)
    
    if not existing_stocks:
        print("❌ 데이터가 있는 기존 종목이 없습니다.")
        return {'existing_count': 0, 'stocks': []}
    
    # 우선순위별 분류
    priority_stocks = []
    regular_stocks = []
    
    for row in existing_stocks:
        stock_data = {
            'stock_code': row[0],
            'stock_name': row[1],
            'market_type': row[2],
            'latest_date': row[3].strftime('%Y-%m-%d') if row[3] else '1900-01-01',
            'data_count': row[4]
        }
        
        if row[0] in PRIORITY_STOCKS:
            priority_stocks.append(stock_data)
        else:
            regular_stocks.append(stock_data)
    
    all_stocks = priority_stocks + regular_stocks
    
    print(f"📊 업데이트 대상 종목: {len(all_stocks):,}개")
    print(f"  - 우선순위 종목: {len(priority_stocks)}개")
    print(f"  - 일반 종목: {len(regular_stocks):,}개")
    
    # 데이터 분포 확인
    today = datetime.now(pytz.timezone("Asia/Seoul")).date()
    recent_count = sum(1 for stock in all_stocks 
                      if (today - datetime.strptime(stock['latest_date'], '%Y-%m-%d').date()).days <= 3)
    
    print(f"  - 최근 3일 내 데이터: {recent_count:,}개 ({recent_count/len(all_stocks)*100:.1f}%)")
    
    # XCom으로 종목 리스트 전달
    context['task_instance'].xcom_push(key='existing_stocks', value=all_stocks)
    
    return {
        'existing_count': len(all_stocks),
        'priority_count': len(priority_stocks),
        'regular_count': len(regular_stocks),
        'recent_data_count': recent_count,
        'status_time': datetime.now(pytz.timezone("Asia/Seoul")).isoformat()
    }


def update_priority_stocks(**context):
    """우선순위 종목 먼저 업데이트"""
    
    print("🚀 우선순위 종목 일일 업데이트 시작...")
    
    existing_stocks = context['task_instance'].xcom_pull(key='existing_stocks', task_ids='get_existing_stocks_status')
    priority_stocks = [stock for stock in existing_stocks if stock['stock_code'] in PRIORITY_STOCKS]
    
    if not priority_stocks:
        print("✅ 우선순위 종목이 없습니다.")
        return {'updated_count': 0, 'total_records': 0}
    
    return process_stock_batch(priority_stocks, "우선순위")


def update_regular_stocks(**context):
    """일반 종목 배치 업데이트"""
    
    print("📦 일반 종목 배치 업데이트 시작...")
    
    existing_stocks = context['task_instance'].xcom_pull(key='existing_stocks', task_ids='get_existing_stocks_status')
    regular_stocks = [stock for stock in existing_stocks if stock['stock_code'] not in PRIORITY_STOCKS]
    
    if not regular_stocks:
        print("✅ 일반 종목이 없습니다.")
        return {'updated_count': 0, 'total_records': 0}
    
    print(f"📈 {len(regular_stocks):,}개 일반 종목을 {BATCH_SIZE}개씩 배치 처리...")
    
    return process_stock_batch(regular_stocks, "일반")


def process_stock_batch(stocks: List[Dict], batch_type: str) -> Dict:
    """종목 배치 처리 (공통 함수)"""
    
    kis_client = KISDailyUpdateClient()
    pg_hook = PostgresHook(postgres_conn_id='quantum_postgres')
    
    total_updated = 0
    total_records = 0
    total_errors = 0
    
    # 배치별 처리
    for i in range(0, len(stocks), BATCH_SIZE):
        batch = stocks[i:i+BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(stocks) - 1) // BATCH_SIZE + 1
        
        print(f"📦 {batch_type} 배치 {batch_num}/{total_batches}: {len(batch)}개 종목 처리 중...")
        
        batch_updated = 0
        batch_records = 0
        
        for stock in batch:
            stock_code = stock['stock_code']
            
            try:
                # 최신 데이터 조회
                result = kis_client.get_latest_data(stock_code)
                
                if result and result['latest_data']:
                    latest_data = result['latest_data']
                    
                    # 중복 확인 (이미 있는 날짜면 스킵)
                    trade_date = latest_data['stck_bsop_date']
                    if not should_update_data(pg_hook, stock_code, trade_date):
                        continue
                    
                    # 데이터베이스 저장
                    saved = save_daily_update_to_db(pg_hook, stock_code, latest_data, result['full_response'])
                    if saved:
                        batch_updated += 1
                        batch_records += 1
                        
                        if batch_updated <= 3:  # 처음 3개만 상세 로그
                            print(f"✅ {stock_code}: {trade_date} 데이터 업데이트")
                
            except Exception as e:
                total_errors += 1
                print(f"❌ {stock_code} 업데이트 실패: {e}")
                continue
        
        total_updated += batch_updated
        total_records += batch_records
        
        print(f"  배치 {batch_num} 완료: {batch_updated}/{len(batch)}개 업데이트")
        
        # 배치 간 휴식 (마지막 배치 제외)
        if i + BATCH_SIZE < len(stocks):
            print(f"⏸️ {BATCH_DELAY}초 휴식...")
            time.sleep(BATCH_DELAY)
    
    print(f"🎉 {batch_type} 종목 완료: {total_updated:,}개 업데이트, {total_records:,}개 레코드")
    print(f"📊 성공률: {kis_client.success_count:,}개 성공, {kis_client.error_count}개 실패")
    
    return {
        'batch_type': batch_type,
        'updated_count': total_updated,
        'total_records': total_records,
        'error_count': total_errors,
        'api_success_count': kis_client.success_count,
        'api_error_count': kis_client.error_count
    }


def should_update_data(pg_hook: PostgresHook, stock_code: str, trade_date: str) -> bool:
    """해당 날짜 데이터가 이미 있는지 확인"""
    
    check_sql = """
    SELECT COUNT(*) 
    FROM domestic_stocks_detail 
    WHERE stock_code = %s 
    AND trade_date = TO_DATE(%s, 'YYYYMMDD')
    AND data_type = 'CHART';
    """
    
    count = pg_hook.get_first(check_sql, parameters=(stock_code, trade_date))[0]
    return count == 0


def save_daily_update_to_db(pg_hook: PostgresHook, stock_code: str, daily_data: Dict, full_response: Dict) -> bool:
    """일일 업데이트 데이터를 DB에 저장"""
    
    try:
        # OHLCV 데이터 추출
        ohlcv_data = {
            'open': int(daily_data['stck_oprc']),
            'high': int(daily_data['stck_hgpr']),
            'low': int(daily_data['stck_lwpr']),
            'close': int(daily_data['stck_clpr']),
            'volume': int(daily_data['acml_vol']),
        }
        
        insert_sql = """
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
        );
        """
        
        with pg_hook.get_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(insert_sql, {
                    'stock_code': stock_code,
                    'trade_date': daily_data['stck_bsop_date'],
                    'close_price': ohlcv_data['close'],
                    'volume': ohlcv_data['volume'],
                    'raw_response': json.dumps({
                        **daily_data,
                        'ohlcv': ohlcv_data,
                        'update_source': 'daily_stock_update_dag'
                    }),
                    'request_params': json.dumps({
                        'stock_code': stock_code,
                        'period': '1day',
                        'data_type': 'daily_update',
                        'source': 'scheduled_update'
                    }),
                })
                conn.commit()
        
        return True
        
    except Exception as e:
        print(f"❌ {stock_code} DB 저장 실패: {e}")
        return False


def generate_daily_summary(**context):
    """일일 업데이트 결과 요약"""
    
    print("📊 일일 업데이트 결과 요약 생성...")
    
    # 우선순위 결과
    priority_result = context['task_instance'].xcom_pull(task_ids='update_priority_stocks') or {}
    regular_result = context['task_instance'].xcom_pull(task_ids='update_regular_stocks') or {}
    
    total_updated = priority_result.get('updated_count', 0) + regular_result.get('updated_count', 0)
    total_records = priority_result.get('total_records', 0) + regular_result.get('total_records', 0)
    total_errors = priority_result.get('error_count', 0) + regular_result.get('error_count', 0)
    
    pg_hook = PostgresHook(postgres_conn_id='quantum_postgres')
    
    # 오늘 업데이트된 데이터 확인
    today_sql = """
    SELECT 
        COUNT(DISTINCT stock_code) as updated_stocks,
        COUNT(*) as updated_records,
        MIN(trade_date) as earliest_date,
        MAX(trade_date) as latest_date
    FROM domestic_stocks_detail 
    WHERE DATE(created_at) = CURRENT_DATE
    AND data_type = 'CHART';
    """
    
    today_stats = pg_hook.get_first(today_sql)
    updated_stocks, updated_records, earliest_date, latest_date = today_stats
    
    # 전체 커버리지 확인
    coverage_sql = """
    SELECT 
        COUNT(*) as total_stocks,
        COUNT(DISTINCT dsd.stock_code) as covered_stocks
    FROM domestic_stocks ds
    LEFT JOIN domestic_stocks_detail dsd ON ds.stock_code = dsd.stock_code
    WHERE ds.is_active = true;
    """
    
    total_stocks, covered_stocks = pg_hook.get_first(coverage_sql)
    coverage_pct = (covered_stocks / total_stocks * 100) if total_stocks > 0 else 0
    
    summary = {
        'execution_date': datetime.now(pytz.timezone("Asia/Seoul")).strftime('%Y-%m-%d'),
        'total_updated_stocks': total_updated,
        'total_records': total_records,
        'total_errors': total_errors,
        'today_updated_stocks': updated_stocks or 0,
        'today_updated_records': updated_records or 0,
        'earliest_date': str(earliest_date) if earliest_date else None,
        'latest_date': str(latest_date) if latest_date else None,
        'total_coverage': {
            'total_stocks': total_stocks,
            'covered_stocks': covered_stocks,
            'coverage_percentage': round(coverage_pct, 2)
        },
        'priority_result': priority_result,
        'regular_result': regular_result,
        'summary_time': datetime.now(pytz.timezone("Asia/Seoul")).isoformat()
    }
    
    print("📈 일일 업데이트 요약:")
    print(f"  - 업데이트된 종목: {total_updated:,}개")
    print(f"  - 추가된 레코드: {total_records:,}개")
    print(f"  - 전체 커버리지: {covered_stocks:,}/{total_stocks:,}개 ({coverage_pct:.1f}%)")
    print(f"  - 오늘 신규 레코드: {updated_records or 0:,}개")
    
    return summary


# ========================================
# DAG 태스크 정의
# ========================================

# 1. 기존 종목 상태 확인
get_existing_stocks_task = PythonOperator(
    task_id='get_existing_stocks_status',
    python_callable=get_existing_stocks_status,
    dag=dag,
)

# 2. 우선순위 종목 업데이트
update_priority_stocks_task = PythonOperator(
    task_id='update_priority_stocks',
    python_callable=update_priority_stocks,
    dag=dag,
)

# 3. 일반 종목 업데이트
update_regular_stocks_task = PythonOperator(
    task_id='update_regular_stocks',
    python_callable=update_regular_stocks,
    dag=dag,
)

# 4. 결과 요약
generate_summary_task = PythonOperator(
    task_id='generate_daily_summary',
    python_callable=generate_daily_summary,
    dag=dag,
)

# 5. 완료 알림
completion_notification_task = BashOperator(
    task_id='completion_notification',
    bash_command='''
    echo "🎉 일일 종목 데이터 업데이트 완료!"
    echo "실행 시간: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "DAG: Stock_Data__16_Daily_Update" 
    echo "주기: 매일 오후 9시 (주중)"
    echo "대상: 전체 기존 종목 최신 1일치 데이터 추가"
    ''',
    dag=dag,
)

# ========================================
# 태스크 의존성  
# ========================================
get_existing_stocks_task >> [update_priority_stocks_task, update_regular_stocks_task]
[update_priority_stocks_task, update_regular_stocks_task] >> generate_summary_task >> completion_notification_task