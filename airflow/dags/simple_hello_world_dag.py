#!/usr/bin/env python3
"""
Simple Hello World DAG for Airflow Learning
가장 간단한 Airflow DAG 예시 - 학습용

Author: Quantum Trading Platform
Created: 2025-09-05
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# DAG 기본 설정
default_args = {
    'owner': 'quantum-trading',
    'depends_on_past': False,
    'start_date': datetime(2025, 9, 5),
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

# DAG 정의
dag = DAG(
    'simple_hello_world',
    default_args=default_args,
    description='가장 간단한 Hello World DAG - 학습용',
    schedule_interval=None,  # 수동 실행만
    catchup=False,
    tags=['tutorial', 'hello-world', 'learning'],
)

# ================================================================
# Task Functions
# ================================================================

def print_hello():
    """Hello 메시지 출력"""
    print("🎉 Hello World from Airflow!")
    print("안녕하세요! Airflow에서 인사드립니다!")
    return "hello_completed"

def print_current_time():
    """현재 시간 출력"""
    from datetime import datetime
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"⏰ 현재 시간: {current_time}")
    print(f"🕒 Current time: {current_time}")
    return f"time_logged_{current_time}"

def print_goodbye():
    """Goodbye 메시지 출력"""
    print("👋 Goodbye from Airflow!")
    print("안녕히 가세요! Airflow 작업이 완료되었습니다!")
    return "goodbye_completed"

# ================================================================
# Task Definitions
# ================================================================

# Task 1: Hello 출력
task_hello = PythonOperator(
    task_id='print_hello',
    python_callable=print_hello,
    dag=dag
)

# Task 2: 현재 시간 출력
task_datetime = PythonOperator(
    task_id='print_datetime',
    python_callable=print_current_time,
    dag=dag
)

# Task 3: Goodbye 출력
task_goodbye = PythonOperator(
    task_id='print_goodbye',
    python_callable=print_goodbye,
    dag=dag
)

# ================================================================
# Task Dependencies (순차 실행)
# ================================================================

# hello → datetime → goodbye 순서로 실행
task_hello >> task_datetime >> task_goodbye