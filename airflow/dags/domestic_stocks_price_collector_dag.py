"""
국내주식 실시간 가격 수집 DAG (KIS API 연동)
- 주요 종목들의 실시간 가격 정보 수집
- domestic_stocks_detail 테이블에 저장
- 매일 장 시간 중 또는 장마감 후 실행
"""

import os
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pytz
import time

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

# ========================================
# DAG 설정
# ========================================
default_args = {
    'owner': 'quantum-trading',
    'depends_on_past': False,
    'start_date': datetime(2025, 9, 7, tzinfo=pytz.timezone("Asia/Seoul")),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=1),
}

dag = DAG(
    dag_id='Stock_Data__14_Price_Collector',
    default_args=default_args,
    description='국내주식 실시간 가격 수집 - KIS API 연동으로 주요 종목 가격 정보 수집',
    schedule_interval='0 16 * * 1-5',  # 주중 오후 4시 (장마감 후)
    max_active_runs=1,
    catchup=False,
    tags=['domestic-stocks', 'kis-api', 'realtime-price', 'collector'],
)

# ========================================
# 주요 종목 리스트 정의
# ========================================
MAJOR_STOCKS = [
    # 대형주 (시가총액 상위)
    {'stock_code': '005930', 'stock_name': '삼성전자', 'priority': 1},
    {'stock_code': '000660', 'stock_name': 'SK하이닉스', 'priority': 1},
    {'stock_code': '035420', 'stock_name': 'NAVER', 'priority': 1},
    {'stock_code': '035720', 'stock_name': '카카오', 'priority': 1},
    {'stock_code': '051910', 'stock_name': 'LG화학', 'priority': 1},
    
    # 바이오/제약
    {'stock_code': '207940', 'stock_name': '삼성바이오로직스', 'priority': 2},
    {'stock_code': '068270', 'stock_name': '셀트리온', 'priority': 2},
    {'stock_code': '196170', 'stock_name': '알테오젠', 'priority': 2},
    
    # 금융
    {'stock_code': '086790', 'stock_name': '하나금융지주', 'priority': 2},
    {'stock_code': '316140', 'stock_name': '우리금융지주', 'priority': 2},
    
    # 에너지/화학
    {'stock_code': '009150', 'stock_name': '삼성전기', 'priority': 2},
    {'stock_code': '010950', 'stock_name': 'S-Oil', 'priority': 3},
    
    # 자동차/조선
    {'stock_code': '005380', 'stock_name': '현대차', 'priority': 2},
    {'stock_code': '012330', 'stock_name': '현대모비스', 'priority': 3},
    {'stock_code': '009540', 'stock_name': 'HD한국조선해양', 'priority': 2},
    
    # AI/게임
    {'stock_code': '036570', 'stock_name': '엔씨소프트', 'priority': 3},
    {'stock_code': '251270', 'stock_name': '넷마블', 'priority': 3},
]

# ========================================
# KIS API 연동 함수들
# ========================================

class KISAPIClient:
    """KIS Open API 클라이언트 - KIS Adapter 연동"""
    
    def __init__(self):
        # KIS Adapter URL (Docker 내부에서는 host.docker.internal 사용)
        # Airflow가 Docker에서 실행중이므로 host.docker.internal 사용
        self.adapter_url = "http://host.docker.internal:8000"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
    def check_adapter_health(self):
        """KIS Adapter 헬스체크"""
        try:
            response = self.session.get(f"{self.adapter_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ KIS Adapter 연결 성공")
                return True
            else:
                print(f"⚠️ KIS Adapter 응답 이상: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ KIS Adapter 연결 실패: {e}")
            return False
        
    def get_auth_token(self, environment='prod'):
        """KIS API 인증 토큰 획득 (KIS Adapter 경유)"""
        
        print(f"🔑 KIS API 인증 토큰 획득 중... (환경: {environment})")
        
        try:
            # KIS Adapter의 토큰 갱신 엔드포인트 호출
            response = self.session.post(
                f"{self.adapter_url}/auth/refresh-token",
                params={"environment": environment},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ KIS API 인증 성공: {result.get('message', 'Token refreshed')}")
                return True
            else:
                print(f"⚠️ KIS API 인증 실패: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ KIS API 인증 오류: {e}")
            return False
    
    def get_current_price(self, stock_code: str) -> Dict[str, Any]:
        """종목 현재가 조회 (실제 KIS API 호출)"""
        
        print(f"📊 {stock_code} 현재가 조회 중...")
        
        try:
            # KIS Adapter를 통해 실제 가격 조회
            response = self.session.get(
                f"{self.adapter_url}/domestic/price/{stock_code}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # API 응답 성공 여부 확인
                if data.get('rt_cd') == '0':
                    output = data.get('output', {})
                    current_price = int(output.get('stck_prpr', 0))
                    volume = int(output.get('acml_vol', 0))
                    
                    print(f"✅ {stock_code} 현재가: {current_price:,}원 (거래량: {volume:,})")
                    
                    # DAG에서 사용하는 형식으로 변환
                    return {
                        'output': {
                            'stck_prpr': output.get('stck_prpr', '0'),  # 현재가
                            'acml_vol': output.get('acml_vol', '0'),    # 누적거래량
                            'prdy_vrss': output.get('prdy_vrss', '0'),  # 전일대비
                            'prdy_vrss_sign': output.get('prdy_vrss_sign', '3'),  # 등락구분
                            'prdy_ctrt': output.get('prdy_ctrt', '0.00'),  # 전일대비율
                            'hgpr': output.get('stck_hgpr', '0'),  # 고가 (필드명 수정)
                            'lwpr': output.get('stck_lwpr', '0'),  # 저가 (필드명 수정)
                        },
                        'rt_cd': '0',  # 성공코드
                        'msg_cd': data.get('msg1', '정상처리'),
                        'raw_response': data  # 원본 응답 저장
                    }
                else:
                    print(f"⚠️ {stock_code} API 오류: {data.get('msg1', 'Unknown error')}")
                    return {
                        'rt_cd': data.get('rt_cd', '1'),
                        'msg_cd': data.get('msg1', 'API Error'),
                        'output': {}
                    }
            else:
                print(f"❌ {stock_code} HTTP 오류: {response.status_code}")
                return {
                    'rt_cd': '1',
                    'msg_cd': f'HTTP Error: {response.status_code}',
                    'output': {}
                }
                
        except requests.exceptions.Timeout:
            print(f"⏱️ {stock_code} 요청 타임아웃")
            return {
                'rt_cd': '1',
                'msg_cd': 'Request Timeout',
                'output': {}
            }
        except Exception as e:
            print(f"❌ {stock_code} 처리 오류: {e}")
            return {
                'rt_cd': '1',
                'msg_cd': str(e),
                'output': {}
            }


def collect_major_stocks_price(**context):
    """주요 종목들의 현재가 수집"""
    
    print("🚀 주요 종목 가격 수집 시작...")
    
    # KIS API 클라이언트 초기화
    kis_client = KISAPIClient()
    
    # Adapter 연결 확인
    if not kis_client.check_adapter_health():
        print("❌ KIS Adapter 연결 실패. 수집을 중단합니다.")
        raise Exception("KIS Adapter is not available")
    
    # 토큰 갱신 (선택적 - Adapter가 자동으로 관리함)
    kis_client.get_auth_token(environment='prod')
    
    # PostgreSQL 연결
    pg_hook = PostgresHook(postgres_conn_id='quantum_postgres')
    
    collected_data = []
    success_count = 0
    error_count = 0
    
    # Priority 1 종목들부터 수집 (우선순위 높은 종목)
    priority_1_stocks = [stock for stock in MAJOR_STOCKS if stock['priority'] == 1]
    
    print(f"📋 Priority 1 종목 {len(priority_1_stocks)}개 수집 중...")
    
    for stock_info in priority_1_stocks:
        stock_code = stock_info['stock_code']
        stock_name = stock_info['stock_name']
        
        try:
            # KIS API로 현재가 조회
            price_data = kis_client.get_current_price(stock_code)
            
            if price_data['rt_cd'] == '0':  # 성공
                output = price_data['output']
                
                # 수집된 데이터 정리
                collected_info = {
                    'stock_code': stock_code,
                    'stock_name': stock_name,
                    'current_price': int(output['stck_prpr']),
                    'volume': int(output['acml_vol']),
                    'change_price': int(output['prdy_vrss']),
                    'change_rate': float(output['prdy_ctrt']),
                    'high_price': int(output['hgpr']),
                    'low_price': int(output['lwpr']),
                    'raw_response': price_data.get('raw_response', price_data),  # 원본 응답 저장
                    'api_endpoint': '/uapi/domestic-stock/v1/quotations/inquire-price',
                    'data_type': 'PRICE',
                }
                
                collected_data.append(collected_info)
                success_count += 1
                
                print(f"✅ {stock_name}({stock_code}): {collected_info['current_price']:,}원")
                
                # Rate Limit 대응 - API 호출 간 0.1초 대기
                time.sleep(0.1)
                
            else:
                print(f"❌ {stock_name}({stock_code}) 조회 실패: {price_data.get('msg_cd', 'Unknown error')}")
                error_count += 1
                
        except Exception as e:
            print(f"❌ {stock_name}({stock_code}) 처리 중 오류: {e}")
            error_count += 1
            continue
    
    # 데이터베이스에 저장
    if collected_data:
        saved_count = save_price_data_to_db(pg_hook, collected_data)
        print(f"💾 데이터베이스 저장 완료: {saved_count}개")
    else:
        print("⚠️ 수집된 데이터가 없습니다.")
        saved_count = 0
    
    # 결과 반환
    result = {
        'total_stocks': len(priority_1_stocks),
        'success_count': success_count,
        'error_count': error_count,
        'saved_count': saved_count,
        'collection_time': datetime.now(pytz.timezone("Asia/Seoul")).isoformat(),
    }
    
    print(f"🎉 가격 수집 완료: {success_count}개 성공, {error_count}개 실패")
    return result


def save_price_data_to_db(pg_hook: PostgresHook, price_data: List[Dict[str, Any]]) -> int:
    """가격 데이터를 domestic_stocks_detail 테이블에 저장"""
    
    print(f"💾 {len(price_data)}개 종목 가격 데이터 저장 중...")
    
    # UPSERT SQL (같은 날짜의 같은 종목은 업데이트)
    upsert_sql = """
    INSERT INTO domestic_stocks_detail (
        stock_code,
        current_price,
        volume,
        trade_date,
        data_type,
        api_endpoint,
        raw_response,
        request_params,
        request_timestamp,
        created_at,
        updated_at
    ) VALUES (
        %(stock_code)s,
        %(current_price)s,
        %(volume)s,
        CURRENT_DATE,
        %(data_type)s,
        %(api_endpoint)s,
        %(raw_response)s,
        %(request_params)s,
        NOW(),
        NOW(),
        NOW()
    )
    ON CONFLICT (stock_code, trade_date, data_type)
    DO UPDATE SET
        current_price = EXCLUDED.current_price,
        volume = EXCLUDED.volume,
        api_endpoint = EXCLUDED.api_endpoint,
        raw_response = EXCLUDED.raw_response,
        request_timestamp = EXCLUDED.request_timestamp,
        updated_at = NOW();
    """
    
    saved_count = 0
    
    try:
        with pg_hook.get_conn() as conn:
            with conn.cursor() as cursor:
                for data in price_data:
                    try:
                        cursor.execute(upsert_sql, {
                            'stock_code': data['stock_code'],
                            'current_price': data['current_price'],
                            'volume': data['volume'],
                            'data_type': data['data_type'],
                            'api_endpoint': data['api_endpoint'],
                            'raw_response': json.dumps(data['raw_response']),
                            'request_params': json.dumps({'stock_code': data['stock_code']}),
                        })
                        saved_count += cursor.rowcount
                        
                    except Exception as e:
                        print(f"❌ {data['stock_code']} 저장 오류: {e}")
                        continue
                
                conn.commit()
                
    except Exception as e:
        print(f"❌ 데이터베이스 저장 오류: {e}")
        raise
    
    print(f"✅ {saved_count}개 가격 데이터 저장 완료")
    return saved_count


def validate_collected_data(**context):
    """수집된 데이터 검증"""
    
    print("🔍 수집된 가격 데이터 검증 중...")
    
    pg_hook = PostgresHook(postgres_conn_id='quantum_postgres')
    
    try:
        # 오늘 수집된 데이터 통계
        today_stats = pg_hook.get_records("""
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT stock_code) as unique_stocks,
            AVG(current_price) as avg_price,
            MAX(volume) as max_volume,
            MIN(request_timestamp) as first_collection,
            MAX(request_timestamp) as last_collection
        FROM domestic_stocks_detail 
        WHERE trade_date = CURRENT_DATE 
        AND data_type = 'PRICE';
        """)
        
        if today_stats and today_stats[0][0] > 0:
            total, unique, avg_price, max_vol, first_time, last_time = today_stats[0]
            
            print(f"📊 오늘 수집 데이터 통계:")
            print(f"  총 레코드: {total}개")
            print(f"  유니크 종목: {unique}개")
            print(f"  평균 주가: {avg_price:,.0f}원")
            print(f"  최대 거래량: {max_vol:,}주")
            print(f"  수집 시작: {first_time}")
            print(f"  수집 완료: {last_time}")
            
            # 주요 종목별 데이터 확인
            major_stock_data = pg_hook.get_records("""
            SELECT 
                ds.stock_code,
                ds.stock_name,
                dsd.current_price,
                dsd.volume,
                dsd.request_timestamp
            FROM domestic_stocks ds
            JOIN domestic_stocks_detail dsd ON ds.stock_code = dsd.stock_code
            WHERE dsd.trade_date = CURRENT_DATE 
            AND dsd.data_type = 'PRICE'
            ORDER BY dsd.current_price DESC
            LIMIT 5;
            """)
            
            print(f"\n🏆 주요 종목 현재가 (상위 5개):")
            for code, name, price, volume, timestamp in major_stock_data:
                print(f"  {name}({code}): {price:,}원, 거래량: {volume:,}주")
            
            validation_result = {
                'validation_passed': True,
                'total_records': total,
                'unique_stocks': unique,
                'validation_time': datetime.now(pytz.timezone("Asia/Seoul")).isoformat(),
            }
            
        else:
            print("⚠️ 오늘 수집된 데이터가 없습니다.")
            validation_result = {
                'validation_passed': False,
                'total_records': 0,
                'unique_stocks': 0,
                'validation_time': datetime.now(pytz.timezone("Asia/Seoul")).isoformat(),
            }
        
        return validation_result
        
    except Exception as e:
        print(f"❌ 데이터 검증 오류: {e}")
        raise


# ========================================
# DAG 태스크 정의
# ========================================

# 1. 주요 종목 가격 수집
collect_price_task = PythonOperator(
    task_id='collect_major_stocks_price',
    python_callable=collect_major_stocks_price,
    dag=dag,
)

# 2. 수집 데이터 검증
validate_data_task = PythonOperator(
    task_id='validate_collected_data',
    python_callable=validate_collected_data,
    dag=dag,
)

# 3. 성공 알림
from airflow.operators.bash import BashOperator

success_notification_task = BashOperator(
    task_id='price_collection_success',
    bash_command='''
    echo "🎉 국내주식 가격 수집 완료!"
    echo "실행 시간: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "DAG: domestic_stocks_price_collector"
    echo "테이블: domestic_stocks_detail"
    ''',
    dag=dag,
)

# ========================================
# 태스크 의존성 설정
# ========================================
collect_price_task >> validate_data_task >> success_notification_task