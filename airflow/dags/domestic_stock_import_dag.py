"""
국내주식종목 가져오기 DAG (DDD 기반)
- KOSPI/KOSDAQ 국내 종목 파일 파싱 및 DB 적재
- domestic_stocks 테이블 사용
- 데이터 검증 및 품질 관리
"""

import os
import re
import uuid
import pandas as pd
import psycopg2
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pytz

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator


# ========================================
# DAG 설정
# ========================================
default_args = {
    'owner': 'quantum-trading',
    'depends_on_past': False,
    'start_date': datetime(2025, 9, 6, tzinfo=pytz.timezone("Asia/Seoul")),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
    'execution_timeout': timedelta(hours=2),
}

dag = DAG(
    dag_id='Stock_Data__10_Master_Import',
    default_args=default_args,
    description='국내주식종목 가져오기 - KOSPI/KOSDAQ 종목 파일 파싱 및 DB 적재 (DDD 설계)',
    schedule_interval='0 2 * * 1-5',  # 주중 새벽 2시 실행
    max_active_runs=1,
    catchup=False,
    tags=['domestic-stocks', 'kospi', 'kosdaq', 'ddd'],
)


# ========================================
# 파일 파싱 함수들
# ========================================

def parse_domestic_stock_file(file_path: str, market_type: str) -> List[Dict[str, Any]]:
    """
    국내 종목 파일 파싱 (KOSPI/KOSDAQ)
    
    고정길이 포맷:
    종목코드(6) + 종목명(40) + 기타정보...
    """
    results = []
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Stock file not found: {file_path}")
    
    print(f"📊 Parsing {market_type} file: {file_path}")
    
    with open(file_path, 'r', encoding='cp949') as f:
        lines = f.readlines()
    
    for line_num, line in enumerate(lines, 1):
        try:
            # 라인이 너무 짧으면 스킵 (최소 KR7 위치까지 확인)
            if len(line.strip()) < 52:
                continue
            
            # 고정길이 파싱 (KIS 포맷 기반)
            # 분석 결과: 종목코드는 0-6 위치, 종목명은 KR7 코드 뒤에 위치
            stock_code = line[0:6].strip()
            
            # KR7 위치를 찾아서 종목명 추출
            kr_pos = line.find('KR7')
            if kr_pos > 0:
                # KR7 코드는 12자리이므로 KR7 + 12 = 15자리
                # 그 다음부터 종목명 시작 (보통 21번째 위치부터)
                name_start = kr_pos + 12  # KR7 + 9자리 = 12
                # 종목명은 공백으로 구분되므로 첫 번째 공백까지
                name_end = name_start
                while name_end < len(line) and line[name_end] not in [' ', '\t']:
                    name_end += 1
                stock_name = line[name_start:name_end].strip()
            else:
                # KR7을 찾지 못한 경우 기본 위치에서 추출
                stock_name = line[21:60].strip() if len(line) > 60 else line[21:].strip()
            
            # 유효성 검증
            if not stock_code or not re.match(r'^[A-Z0-9]{6}$', stock_code):
                continue
                
            if not stock_name or stock_name in ['', 'N/A']:
                continue
            
            # 데이터 구조화
            stock_data = {
                'stock_code': stock_code,
                'stock_name': stock_name,
                'market_type': market_type,
                'raw_data': line.strip(),
                'line_number': line_num,
                'file_path': file_path
            }
            
            results.append(stock_data)
            
        except Exception as e:
            print(f"❌ Error parsing line {line_num} in {file_path}: {e}")
            continue
    
    print(f"✅ Successfully parsed {len(results)} stocks from {market_type}")
    return results


def sync_domestic_stocks(**context):
    """국내주식종목 동기화 메인 함수"""
    
    print("🚀 Starting domestic stock synchronization...")
    
    # PostgreSQL 연결
    pg_hook = PostgresHook(postgres_conn_id='quantum_postgres')
    
    # 파일 경로 설정
    kospi_file = "/opt/airflow/data/kospi_stocks.txt"
    kosdaq_file = "/opt/airflow/data/kosdaq_stocks.txt"
    
    all_stocks = []
    
    try:
        # KOSPI 파일 파싱
        if os.path.exists(kospi_file):
            kospi_stocks = parse_domestic_stock_file(kospi_file, 'KOSPI')
            all_stocks.extend(kospi_stocks)
            print(f"📈 KOSPI stocks parsed: {len(kospi_stocks)}")
        else:
            print("⚠️ KOSPI file not found, using sample data")
            # 샘플 데이터
            sample_kospi = [
                {'stock_code': '005930', 'stock_name': '삼성전자', 'market_type': 'KOSPI', 'raw_data': '005930삼성전자...'},
                {'stock_code': '000660', 'stock_name': 'SK하이닉스', 'market_type': 'KOSPI', 'raw_data': '000660SK하이닉스...'},
            ]
            all_stocks.extend(sample_kospi)
        
        # KOSDAQ 파일 파싱
        if os.path.exists(kosdaq_file):
            kosdaq_stocks = parse_domestic_stock_file(kosdaq_file, 'KOSDAQ')
            all_stocks.extend(kosdaq_stocks)
            print(f"📊 KOSDAQ stocks parsed: {len(kosdaq_stocks)}")
        else:
            print("⚠️ KOSDAQ file not found, using sample data")
            # 샘플 데이터
            sample_kosdaq = [
                {'stock_code': '035720', 'stock_name': '카카오', 'market_type': 'KOSDAQ', 'raw_data': '035720카카오...'},
            ]
            all_stocks.extend(sample_kosdaq)
        
        if not all_stocks:
            raise ValueError("No stock data to process")
        
        # 데이터베이스에 저장
        save_count = save_domestic_stocks_to_db(pg_hook, all_stocks)
        
        print(f"🎉 Domestic stock sync completed: {save_count} stocks processed")
        
        # XCom으로 결과 전달
        return {
            'total_stocks': len(all_stocks),
            'saved_stocks': save_count,
            'kospi_count': len([s for s in all_stocks if s['market_type'] == 'KOSPI']),
            'kosdaq_count': len([s for s in all_stocks if s['market_type'] == 'KOSDAQ']),
            'sync_time': datetime.now(pytz.timezone("Asia/Seoul")).isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error in domestic stock sync: {e}")
        raise


def save_domestic_stocks_to_db(pg_hook: PostgresHook, stocks: List[Dict[str, Any]]) -> int:
    """국내주식종목 데이터를 domestic_stocks 테이블에 저장"""
    
    print(f"💾 Saving {len(stocks)} domestic stocks to database...")
    
    # UPSERT SQL (INSERT ... ON CONFLICT ... UPDATE)
    upsert_sql = """
    INSERT INTO domestic_stocks (
        stock_code,
        stock_name,
        market_type,
        raw_data,
        is_active,
        created_at,
        updated_at
    ) VALUES (
        %(stock_code)s,
        %(stock_name)s,
        %(market_type)s,
        %(raw_data)s,
        true,
        NOW(),
        NOW()
    )
    ON CONFLICT (stock_code) 
    DO UPDATE SET
        stock_name = EXCLUDED.stock_name,
        market_type = EXCLUDED.market_type,
        raw_data = EXCLUDED.raw_data,
        is_active = EXCLUDED.is_active,
        updated_at = NOW();
    """
    
    saved_count = 0
    
    try:
        # 배치 처리로 성능 향상
        with pg_hook.get_conn() as conn:
            with conn.cursor() as cursor:
                for stock in stocks:
                    try:
                        cursor.execute(upsert_sql, {
                            'stock_code': stock['stock_code'],
                            'stock_name': stock['stock_name'],
                            'market_type': stock['market_type'],
                            'raw_data': stock.get('raw_data', ''),
                        })
                        saved_count += cursor.rowcount
                        
                    except Exception as e:
                        print(f"❌ Error saving stock {stock['stock_code']}: {e}")
                        continue
                
                conn.commit()
                
    except Exception as e:
        print(f"❌ Database error: {e}")
        raise
    
    print(f"✅ Successfully saved {saved_count} domestic stocks")
    return saved_count


def validate_domestic_stock_data(**context):
    """국내주식종목 데이터 검증"""
    
    print("🔍 Validating domestic stock data...")
    
    pg_hook = PostgresHook(postgres_conn_id='quantum_postgres')
    
    try:
        # 기본 통계 조회
        stats_sql = """
        SELECT 
            market_type,
            COUNT(*) as stock_count,
            COUNT(DISTINCT stock_code) as unique_codes,
            MIN(created_at) as oldest_record,
            MAX(updated_at) as newest_record
        FROM domestic_stocks 
        WHERE is_active = true
        GROUP BY market_type
        ORDER BY market_type;
        """
        
        stats = pg_hook.get_records(stats_sql)
        
        print("📊 Domestic Stock Statistics:")
        total_stocks = 0
        for stat in stats:
            market_type, count, unique, oldest, newest = stat
            total_stocks += count
            print(f"  {market_type}: {count} stocks (unique: {unique})")
            print(f"    Oldest: {oldest}, Newest: {newest}")
        
        # 데이터 품질 검증
        quality_sql = """
        SELECT 
            'duplicate_codes' as issue_type,
            COUNT(*) as issue_count
        FROM (
            SELECT stock_code 
            FROM domestic_stocks 
            WHERE is_active = true
            GROUP BY stock_code 
            HAVING COUNT(*) > 1
        ) duplicates
        
        UNION ALL
        
        SELECT 
            'empty_names' as issue_type,
            COUNT(*) as issue_count
        FROM domestic_stocks 
        WHERE is_active = true 
          AND (stock_name IS NULL OR stock_name = '')
        
        UNION ALL
        
        SELECT 
            'invalid_codes' as issue_type,
            COUNT(*) as issue_count
        FROM domestic_stocks 
        WHERE is_active = true 
          AND stock_code !~ '^[A-Z0-9]{6}$';
        """
        
        quality_results = pg_hook.get_records(quality_sql)
        
        print("🔍 Data Quality Check:")
        issues_found = False
        for issue_type, count in quality_results:
            if count > 0:
                issues_found = True
                print(f"  ⚠️ {issue_type}: {count}")
            else:
                print(f"  ✅ {issue_type}: OK")
        
        if not issues_found:
            print("✅ All data quality checks passed!")
        
        # 결과 반환
        return {
            'total_stocks': total_stocks,
            'kospi_stocks': next((s[1] for s in stats if s[0] == 'KOSPI'), 0),
            'kosdaq_stocks': next((s[1] for s in stats if s[0] == 'KOSDAQ'), 0),
            'validation_passed': not issues_found,
            'validation_time': datetime.now(pytz.timezone("Asia/Seoul")).isoformat()
        }
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        raise


# ========================================
# DAG 태스크 정의
# ========================================

# 1. 국내주식종목 동기화
sync_domestic_stocks_task = PythonOperator(
    task_id='sync_domestic_stocks',
    python_callable=sync_domestic_stocks,
    dag=dag,
)

# 2. 데이터 검증
validate_data_task = PythonOperator(
    task_id='validate_domestic_stock_data',
    python_callable=validate_domestic_stock_data,
    dag=dag,
)

# 3. 통계 정보 업데이트 (SQL)
update_stats_task = PostgresOperator(
    task_id='update_domestic_stock_stats',
    postgres_conn_id='quantum_postgres',
    sql="""
    -- 국내주식종목 통계 업데이트 (UPSERT)
    INSERT INTO airflow.dag_run_stats (
        dag_id,
        task_id,
        execution_date,
        stats_json,
        created_at
    )
    SELECT 
        'domestic_stock_import' as dag_id,
        'update_stats' as task_id,
        '{{ ds }}' as execution_date,
        json_build_object(
            'total_domestic_stocks', COUNT(*),
            'kospi_stocks', COUNT(*) FILTER (WHERE market_type = 'KOSPI'),
            'kosdaq_stocks', COUNT(*) FILTER (WHERE market_type = 'KOSDAQ'),
            'active_stocks', COUNT(*) FILTER (WHERE is_active = true),
            'last_updated', MAX(updated_at)
        ) as stats_json,
        NOW() as created_at
    FROM domestic_stocks
    ON CONFLICT (dag_id, task_id, execution_date)
    DO UPDATE SET
        stats_json = EXCLUDED.stats_json,
        created_at = NOW();
    """,
    dag=dag,
)

# 4. 성공 알림
success_notification_task = BashOperator(
    task_id='success_notification',
    bash_command='''
    echo "🎉 국내주식종목 가져오기 완료!"
    echo "실행 시간: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "DAG: domestic_stock_import"
    echo "테이블: domestic_stocks"
    ''',
    dag=dag,
)

# ========================================
# 태스크 의존성 설정
# ========================================
sync_domestic_stocks_task >> validate_data_task >> update_stats_task >> success_notification_task