#!/usr/bin/env python3
"""
KIS Holiday DAG 직접 테스트
"""

import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime
import sys

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_kis_api():
    """KIS API 테스트"""
    logger.info("KIS API 테스트 시작")
    
    try:
        current_date = datetime.now()
        response = requests.get(
            "http://localhost:8000/domestic/holiday",
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
        logger.info(f"✅ KIS API 테스트 성공: {len(holiday_data)}건 조회")
        
        return {
            "status": "success",
            "data": holiday_data,
            "count": len(holiday_data)
        }
        
    except Exception as e:
        logger.error(f"❌ KIS API 테스트 실패: {str(e)}")
        return {"status": "failed", "error": str(e)}

def test_database_connection():
    """데이터베이스 연결 테스트"""
    logger.info("데이터베이스 연결 테스트 시작")
    
    conn_params = {
        'host': 'localhost',
        'port': 5432,
        'database': 'quantum_trading',
        'user': 'quantum',
        'password': 'quantum123'
    }
    
    try:
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT COUNT(*) as count FROM kis_domestic_holidays;")
                result = cursor.fetchone()
                logger.info(f"✅ 데이터베이스 연결 성공: 현재 {result['count']}건 저장됨")
                return {"status": "success", "current_count": result['count']}
                
    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 실패: {str(e)}")
        return {"status": "failed", "error": str(e)}

def test_data_insert(holiday_data):
    """데이터 삽입 테스트"""
    logger.info("데이터 삽입 테스트 시작")
    
    conn_params = {
        'host': 'localhost',
        'port': 5432,
        'database': 'quantum_trading',
        'user': 'quantum',
        'password': 'quantum123'
    }
    
    try:
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                
                inserted_count = 0
                
                # 처음 5건만 테스트
                for holiday_item in holiday_data[:5]:
                    holiday_date = datetime.strptime(holiday_item["bass_dt"], "%Y%m%d").date()
                    business_day_yn = holiday_item.get("bzdy_yn", "")
                    trade_day_yn = holiday_item.get("tr_day_yn", "")
                    opening_day_yn = holiday_item.get("opnd_yn", "")
                    settlement_day_yn = holiday_item.get("sttl_day_yn", "")
                    holiday_name = holiday_item.get("holi_nm", "")
                    
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
                    
                    if cursor.rowcount > 0:
                        inserted_count += 1
                
                conn.commit()
                
                # 삽입 후 검증
                cursor.execute("SELECT COUNT(*) as count FROM kis_domestic_holidays;")
                result = cursor.fetchone()
                
                logger.info(f"✅ 데이터 삽입 테스트 성공: {inserted_count}건 처리, 총 {result['count']}건")
                return {"status": "success", "inserted": inserted_count, "total": result['count']}
                
    except Exception as e:
        logger.error(f"❌ 데이터 삽입 테스트 실패: {str(e)}")
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    print("🚀 KIS Holiday DAG 테스트 시작\n")
    
    # 1. KIS API 테스트
    api_result = test_kis_api()
    if api_result["status"] != "success":
        print("❌ API 테스트 실패로 중단")
        sys.exit(1)
    
    # 2. 데이터베이스 연결 테스트
    db_result = test_database_connection()
    if db_result["status"] != "success":
        print("❌ DB 연결 테스트 실패로 중단")
        sys.exit(1)
    
    # 3. 데이터 삽입 테스트
    insert_result = test_data_insert(api_result["data"])
    if insert_result["status"] != "success":
        print("❌ 데이터 삽입 테스트 실패")
        sys.exit(1)
    
    print(f"""
✅ 모든 테스트 성공!

📊 결과 요약:
- KIS API: {api_result["count"]}건 조회
- 데이터베이스: {insert_result["inserted"]}건 삽입
- 총 저장된 데이터: {insert_result["total"]}건
    """)