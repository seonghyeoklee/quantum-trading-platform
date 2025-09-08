"""
KIS 토큰 자동 갱신 DAG

KIS 토큰을 매 5시간마다 자동 갱신합니다.
기존 kis_auth.py 모듈을 직접 활용하여 안정성을 높입니다.

스케줄: 매 5시간 (0 */5 * * *)
재시도: 3회, 5분 간격
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
import logging
import os
import pytz

# 기본 인수 (한국 시간대 강제 설정)
default_args = {
    'owner': 'quantum-trading',
    'depends_on_past': False,
    'start_date': datetime(2025, 9, 6, tzinfo=pytz.timezone("Asia/Seoul")),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

# DAG 정의
dag = DAG(
    dag_id='System_Auth__00_KIS_Token_Renewal',
    default_args=default_args,
    description='KIS 토큰 자동 갱신',
    schedule_interval='0 */5 * * *',  # 매 5시간마다
    max_active_runs=1,
    catchup=False,
    tags=['kis', 'token', 'auth', 'prod']
)

def check_token_status():
    """현재 토큰 상태 확인"""
    logging.info("🔍 KIS 토큰 상태 확인 시작")
    
    config_root = "/Users/admin/KIS/config"
    # 한국 시간대로 날짜 계산
    kst_now = datetime.now(pytz.timezone("Asia/Seoul"))
    today = kst_now.strftime('%Y%m%d')
    token_file = os.path.join(config_root, f"KIS{today}")
    
    if os.path.exists(token_file):
        mod_time = datetime.fromtimestamp(os.path.getmtime(token_file))
        kst_mod_time = mod_time.replace(tzinfo=pytz.UTC).astimezone(pytz.timezone("Asia/Seoul"))
        logging.info(f"✅ 토큰 파일 존재: {token_file}")
        logging.info(f"   수정시간 (KST): {kst_mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return {"exists": True, "file": token_file, "modified": kst_mod_time.isoformat()}
    else:
        logging.info(f"❌ 토큰 파일 없음: {token_file}")
        return {"exists": False, "file": token_file}

def validate_token_renewal():
    """토큰 갱신 검증"""
    logging.info("🔍 토큰 갱신 검증 시작")
    
    config_root = "/Users/admin/KIS/config"
    # 한국 시간대로 날짜 계산
    kst_now = datetime.now(pytz.timezone("Asia/Seoul"))
    today = kst_now.strftime('%Y%m%d')
    token_file = os.path.join(config_root, f"KIS{today}")
    
    if os.path.exists(token_file):
        mod_time = datetime.fromtimestamp(os.path.getmtime(token_file))
        kst_mod_time = mod_time.replace(tzinfo=pytz.UTC).astimezone(pytz.timezone("Asia/Seoul"))
        
        # 최근 30분 이내에 수정되었다면 갱신 성공
        time_diff = (kst_now - kst_mod_time.replace(tzinfo=None)).total_seconds()
        if time_diff < 1800:  # 30분 = 1800초
            logging.info(f"✅ 토큰 갱신 성공")
            logging.info(f"   수정시간 (KST): {kst_mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logging.info(f"   경과시간: {time_diff/60:.1f}분 전")
            return True
        else:
            logging.warning(f"⚠️  토큰 파일이 오래됨")
            logging.warning(f"   수정시간 (KST): {kst_mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logging.warning(f"   경과시간: {time_diff/60:.1f}분 전")
            return False
    else:
        logging.error(f"❌ 토큰 파일 없음: {token_file}")
        return False

# Task 1: 현재 토큰 상태 확인
check_token_task = PythonOperator(
    task_id='check_token_status',
    python_callable=check_token_status,
    dag=dag
)

# Task 2: KIS 토큰 갱신 (BashOperator 사용)
renew_token_task = BashOperator(
    task_id='renew_kis_token',
    bash_command="""
    echo "🔄 KIS 토큰 갱신 시작..."
    
    # KIS 어댑터 디렉토리로 이동
    cd /Users/admin/study/quantum-trading-platform/quantum-adapter-kis/examples_user
    
    # Python으로 토큰 갱신 실행
    python3 -c "
import sys
sys.path.append('/Users/admin/study/quantum-trading-platform/quantum-adapter-kis/examples_user')
import kis_auth
import logging

logging.basicConfig(level=logging.INFO)

try:
    print('🔄 KIS 실전투자 토큰 갱신 중...')
    
    # 실전투자(prod) 환경으로 토큰 발급
    kis_auth.auth(svr='prod', product='01')
    
    # 토큰 상태 확인
    current_token = kis_auth.read_token()
    if current_token:
        print(f'✅ KIS 토큰 갱신 완료!')
        print(f'   토큰 길이: {len(current_token)} 문자')
        print(f'   토큰 일부: {current_token[:20]}...')
    else:
        print('❌ 토큰 갱신 실패!')
        sys.exit(1)
        
except Exception as e:
    print(f'❌ 토큰 갱신 중 오류 발생: {str(e)}')
    sys.exit(1)
"
    
    echo "✅ KIS 토큰 갱신 완료"
    """,
    retries=3,
    retry_delay=timedelta(minutes=5),
    dag=dag
)

# Task 3: 토큰 갱신 검증
validate_task = PythonOperator(
    task_id='validate_token_renewal',
    python_callable=validate_token_renewal,
    dag=dag
)

# Task 4: 완료 알림 (한국 시간)
notify_task = BashOperator(
    task_id='send_notification',
    bash_command="""
    export TZ=Asia/Seoul
    echo "📢 KIS 토큰 자동 갱신 작업 완료"
    echo "   처리 시간 (KST): $(date '+%Y-%m-%d %H:%M:%S')"
    echo "   다음 실행: 5시간 후"
    echo "   토큰 유효 시간: 6시간 (1시간 여유)"
    echo "   시간대: 한국 표준시 (KST)"
    """,
    dag=dag
)

# Task 의존성 설정
check_token_task >> renew_token_task >> validate_task >> notify_task