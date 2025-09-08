"""
KIS 국내휴장일 수집 DAG

KIS API의 국내휴장일조회(TCA0903R) 서비스를 1일 1회 호출하여 
kis_domestic_holidays 테이블에 저장하는 배치 작업

스케줄: 매일 오전 6시 (장 시작 전)
재시도: 3회, 30분 간격
"""

from datetime import datetime, timedelta
from airflow.decorators import dag, task
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from typing import Dict, List, Any
import json
import os

# 기본 인수
default_args = {
    'owner': 'quantum-trading',
    'depends_on_past': False,
    'start_date': datetime(2025, 9, 6),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=30),
}

@dag(
    dag_id='System_Auth__01_Holiday_Sync',
    default_args=default_args,
    description='KIS 국내휴장일 데이터 수집 및 DB 저장',
    schedule_interval='0 6 * * *',  # 매일 오전 6시
    max_active_runs=1,
    catchup=False,
    tags=['kis', 'holiday', 'batch', 'daily']
)
def kis_holiday_sync_dag():
    
    @task(retries=3, retry_delay=timedelta(minutes=30))
    def fetch_holiday_data() -> Dict[str, Any]:
        """
        KIS API에서 휴장일 데이터 조회
        1일 1회 제한 준수
        """
        logging.info("KIS 휴장일 데이터 조회 시작")
        
        # KIS Adapter URL (FastAPI 서버) - Docker 컨테이너에서 호스트 접근
        kis_adapter_url = "http://host.docker.internal:8000"
        
        try:
            # 현재 날짜부터 1년 후까지 조회
            current_date = datetime.now()
            end_date = current_date + timedelta(days=365)
            
            # KIS Adapter의 휴장일 API 호출
            response = requests.get(
                f"{kis_adapter_url}/domestic/holiday",
                params={
                    "bass_dt": current_date.strftime("%Y%m%d"),
                    "ctx_area_nk": "",
                    "ctx_area_fk": ""
                },
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"KIS API 호출 실패: {response.status_code} - {response.text}")
            
            data = response.json()
            
            if data.get("rt_cd") != "0":
                raise Exception(f"KIS API 에러: {data.get('msg1', 'Unknown error')}")
            
            holiday_data = data.get("output", [])
            logging.info(f"휴장일 데이터 {len(holiday_data)}건 조회 완료")
            
            return {
                "status": "success",
                "data": holiday_data,
                "fetched_at": current_date.isoformat(),
                "count": len(holiday_data)
            }
            
        except Exception as e:
            logging.error(f"휴장일 데이터 조회 실패: {str(e)}")
            raise
    
    @task
    def save_to_database(holiday_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        조회된 휴장일 데이터를 kis_domestic_holidays 테이블에 저장
        """
        logging.info("휴장일 데이터 DB 저장 시작")
        
        if holiday_result["status"] != "success":
            raise Exception("휴장일 데이터 조회가 실패했으므로 저장을 건너뜀")
        
        # PostgreSQL 연결 설정 - 같은 네트워크의 quantum-postgres 사용
        conn_params = {
            'host': 'quantum-postgres',
            'port': 5432,
            'database': 'quantum_trading',
            'user': 'quantum',
            'password': 'quantum123'
        }
        
        try:
            with psycopg2.connect(**conn_params) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    
                    inserted_count = 0
                    updated_count = 0
                    
                    for holiday_item in holiday_result["data"]:
                        # 데이터 파싱
                        holiday_date = datetime.strptime(holiday_item["bass_dt"], "%Y%m%d").date()
                        business_day_yn = holiday_item.get("bzdy_yn", "")
                        trade_day_yn = holiday_item.get("tr_day_yn", "")
                        opening_day_yn = holiday_item.get("opnd_yn", "")
                        settlement_day_yn = holiday_item.get("sttl_day_yn", "")
                        
                        # 휴일명 추출 (API 응답에 있다면)
                        holiday_name = holiday_item.get("holi_nm", "")
                        
                        # UPSERT 쿼리 (중복 방지)
                        upsert_query = """
                        INSERT INTO kis_domestic_holidays 
                        (holiday_date, business_day_yn, trade_day_yn, opening_day_yn, settlement_day_yn, holiday_name, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                        ON CONFLICT (holiday_date) 
                        DO UPDATE SET
                            business_day_yn = EXCLUDED.business_day_yn,
                            trade_day_yn = EXCLUDED.trade_day_yn,
                            opening_day_yn = EXCLUDED.opening_day_yn,
                            settlement_day_yn = EXCLUDED.settlement_day_yn,
                            holiday_name = EXCLUDED.holiday_name,
                            updated_at = NOW()
                        """
                        
                        cursor.execute(upsert_query, (
                            holiday_date,
                            business_day_yn,
                            trade_day_yn,
                            opening_day_yn,
                            settlement_day_yn,
                            holiday_name
                        ))
                        
                        # 삽입/업데이트 구분
                        if cursor.rowcount > 0:
                            # 실제로는 구분하기 어려우므로 전체를 처리된 것으로 카운트
                            inserted_count += 1
                    
                    conn.commit()
                    
                    logging.info(f"휴장일 데이터 저장 완료: {inserted_count}건 처리")
                    
                    return {
                        "status": "success",
                        "processed_count": inserted_count,
                        "saved_at": datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logging.error(f"휴장일 데이터 저장 실패: {str(e)}")
            raise
    
    @task
    def validate_data(save_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        저장된 데이터 검증
        """
        logging.info("휴장일 데이터 검증 시작")
        
        if save_result["status"] != "success":
            raise Exception("데이터 저장이 실패했으므로 검증을 건너뜀")
        
        conn_params = {
            'host': 'quantum-postgres',
            'port': 5432,
            'database': 'quantum_trading',
            'user': 'quantum',
            'password': 'quantum123'
        }
        
        try:
            with psycopg2.connect(**conn_params) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    
                    # 오늘 이후 데이터 개수 확인
                    cursor.execute("""
                        SELECT COUNT(*) as total_count,
                               COUNT(CASE WHEN opening_day_yn = 'Y' THEN 1 END) as trading_days,
                               COUNT(CASE WHEN opening_day_yn = 'N' THEN 1 END) as holidays
                        FROM kis_domestic_holidays 
                        WHERE holiday_date >= CURRENT_DATE
                    """)
                    
                    stats = cursor.fetchone()
                    
                    logging.info(f"데이터 검증 완료 - 전체: {stats['total_count']}, 거래일: {stats['trading_days']}, 휴장일: {stats['holidays']}")
                    
                    return {
                        "status": "success",
                        "validation_stats": dict(stats),
                        "validated_at": datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logging.error(f"데이터 검증 실패: {str(e)}")
            raise
    
    @task
    def send_notification(validation_result: Dict[str, Any]) -> None:
        """
        완료 알림 (로그)
        """
        if validation_result["status"] == "success":
            stats = validation_result["validation_stats"]
            logging.info(f"""
            ✅ KIS 휴장일 동기화 완료
            - 처리 시간: {validation_result['validated_at']}
            - 전체 데이터: {stats['total_count']}건
            - 거래일: {stats['trading_days']}건  
            - 휴장일: {stats['holidays']}건
            """)
        else:
            logging.error("❌ KIS 휴장일 동기화 실패")
    
    # Task 의존성 정의
    holiday_data = fetch_holiday_data()
    save_result = save_to_database(holiday_data)
    validation_result = validate_data(save_result)
    send_notification(validation_result)

# DAG 인스턴스 생성
kis_holiday_dag = kis_holiday_sync_dag()