#!/usr/bin/env python3
"""
KIS Holiday 데이터 직접 삽입
"""

import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("KIS Holiday 데이터 전체 삽입 시작")
    
    # 1. KIS API 데이터 조회
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
            raise Exception(f"KIS API 호출 실패: {response.status_code}")
        
        data = response.json()
        
        if data.get("rt_cd") != "0":
            raise Exception(f"KIS API 에러: {data.get('msg1')}")
        
        holiday_data = data.get("output", [])
        logger.info(f"KIS API에서 {len(holiday_data)}건 조회 완료")
        
    except Exception as e:
        logger.error(f"KIS API 조회 실패: {str(e)}")
        return
    
    # 2. 데이터베이스 삽입
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
                updated_count = 0
                
                logger.info("데이터베이스에 삽입 시작...")
                
                for i, holiday_item in enumerate(holiday_data):
                    if i % 50 == 0:
                        logger.info(f"진행 상황: {i}/{len(holiday_data)}건 처리 중...")
                    
                    try:
                        # 데이터 파싱
                        holiday_date = datetime.strptime(holiday_item["bass_dt"], "%Y%m%d").date()
                        business_day_yn = holiday_item.get("bzdy_yn", "")
                        trade_day_yn = holiday_item.get("tr_day_yn", "")
                        opening_day_yn = holiday_item.get("opnd_yn", "")
                        settlement_day_yn = holiday_item.get("sttl_day_yn", "")
                        holiday_name = holiday_item.get("holi_nm", "")
                        
                        # 기존 데이터 확인
                        cursor.execute("SELECT id FROM kis_domestic_holidays WHERE holiday_date = %s", (holiday_date,))
                        existing = cursor.fetchone()
                        
                        if existing:
                            # 업데이트
                            update_query = """
                            UPDATE kis_domestic_holidays SET
                                business_day_yn = %s,
                                trade_day_yn = %s,
                                opening_day_yn = %s,
                                settlement_day_yn = %s,
                                holiday_name = %s,
                                updated_at = NOW()
                            WHERE holiday_date = %s
                            """
                            cursor.execute(update_query, (
                                business_day_yn, trade_day_yn, opening_day_yn, settlement_day_yn, holiday_name, holiday_date
                            ))
                            updated_count += 1
                        else:
                            # 삽입
                            insert_query = """
                            INSERT INTO kis_domestic_holidays 
                            (holiday_date, business_day_yn, trade_day_yn, opening_day_yn, settlement_day_yn, holiday_name, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                            """
                            cursor.execute(insert_query, (
                                holiday_date, business_day_yn, trade_day_yn, opening_day_yn, settlement_day_yn, holiday_name
                            ))
                            inserted_count += 1
                            
                    except Exception as e:
                        logger.warning(f"데이터 처리 실패 ({holiday_item['bass_dt']}): {e}")
                        continue
                
                # 커밋
                conn.commit()
                
                # 결과 확인
                cursor.execute("SELECT COUNT(*) as total FROM kis_domestic_holidays;")
                result = cursor.fetchone()
                
                logger.info(f"""
✅ 데이터 삽입 완료!
- 신규 삽입: {inserted_count}건
- 업데이트: {updated_count}건  
- 총 저장된 데이터: {result['total']}건
                """)
                
                # 샘플 데이터 확인
                cursor.execute("SELECT holiday_date, opening_day_yn FROM kis_domestic_holidays ORDER BY holiday_date LIMIT 10;")
                samples = cursor.fetchall()
                
                print("\n📋 저장된 데이터 샘플:")
                for sample in samples:
                    status = "거래일" if sample['opening_day_yn'] == 'Y' else "휴장일"
                    print(f"- {sample['holiday_date']}: {status}")
                    
    except Exception as e:
        logger.error(f"데이터베이스 삽입 실패: {str(e)}")

if __name__ == "__main__":
    main()