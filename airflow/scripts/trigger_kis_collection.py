#!/usr/bin/env python3
"""
KIS 데이터 수집 DAG 트리거 유틸리티
종목 코드와 데이터 타입을 파라미터로 전달하여 DAG 실행

Author: Quantum Trading Platform
Created: 2025-09-06
"""

import sys
import requests
import json
import base64
import argparse
from datetime import datetime
from typing import List

class AirflowKISCollectionTrigger:
    """Airflow KIS 데이터 수집 DAG 트리거"""
    
    def __init__(self, airflow_url: str = "http://localhost:8081", 
                 username: str = "admin", password: str = "quantum123"):
        self.airflow_url = airflow_url
        self.username = username
        self.password = password
        self.dag_id = "kis_data_collection"
    
    def trigger_dag(self, symbols: List[str], data_types: List[str], 
                   chart_period: str = "D", chart_count: int = 100) -> bool:
        """DAG 실행 트리거"""
        
        print("🚀 KIS 데이터 수집 DAG 실행")
        print(f"📈 종목 코드: {symbols}")
        print(f"📊 데이터 타입: {data_types}")
        print(f"⏰ 차트 기간: {chart_period}")
        print(f"🔢 차트 개수: {chart_count}")
        print()
        
        # 실행 ID 생성
        timestamp = int(datetime.now().timestamp())
        dag_run_id = f"manual_kis_collection_{timestamp}"
        logical_date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S") + "Z"
        
        # 요청 페이로드
        payload = {
            "dag_run_id": dag_run_id,
            "logical_date": logical_date,
            "conf": {
                "symbols": ",".join(symbols),
                "data_types": ",".join(data_types),
                "chart_period": chart_period,
                "chart_count": chart_count
            }
        }
        
        # 인증 헤더
        auth_string = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth_string}"
        }
        
        # API 호출
        url = f"{self.airflow_url}/api/v1/dags/{self.dag_id}/dagRuns"
        
        try:
            print(f"📤 DAG 실행 요청 중... (ID: {dag_run_id})")
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print("✅ DAG 실행 성공!")
                result = response.json()
                print(f"📊 응답: {json.dumps(result, indent=2, ensure_ascii=False)}")
                print()
                
                # UI 링크 제공
                grid_url = f"{self.airflow_url}/dags/{self.dag_id}/grid"
                run_url = f"{self.airflow_url}/dags/{self.dag_id}/grid?dag_run_id={dag_run_id}"
                
                print("🌐 Airflow UI에서 진행상황을 확인하세요:")
                print(f"   전체 DAG: {grid_url}")
                print(f"   이번 실행: {run_url}")
                print()
                
                # 예상 데이터 계산
                total_requests = len(symbols) * len(data_types)
                print("📈 수집 예정 데이터:")
                print(f"   - 종목 수: {len(symbols)}")
                print(f"   - 데이터 타입 수: {len(data_types)}")
                print(f"   - 총 요청 수: {total_requests}")
                
                if "chart" in data_types:
                    chart_records = len(symbols) * chart_count
                    print(f"   - 예상 차트 레코드 수: {chart_records}")
                
                print(f"⏱️ 대기 시간: 약 2-5분 소요 예상")
                
                return True
                
            else:
                print(f"❌ DAG 실행 실패! (HTTP {response.status_code})")
                print(f"🔍 오류 응답: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 요청 실패: {e}")
            return False

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="KIS 데이터 수집 DAG 트리거")
    
    parser.add_argument("--symbols", "-s", 
                       default="005930,000660,035720",
                       help="종목 코드 (쉼표로 구분, 기본값: 005930,000660,035720)")
    
    parser.add_argument("--data-types", "-t", 
                       default="price,chart",
                       help="데이터 타입 (쉼표로 구분, 기본값: price,chart)")
    
    parser.add_argument("--chart-period", "-p", 
                       default="D",
                       help="차트 기간 (D/W/M/Y, 기본값: D)")
    
    parser.add_argument("--chart-count", "-c", 
                       type=int, default=100,
                       help="차트 데이터 개수 (기본값: 100)")
    
    parser.add_argument("--airflow-url", 
                       default="http://localhost:8081",
                       help="Airflow URL (기본값: http://localhost:8081)")
    
    args = parser.parse_args()
    
    # 파라미터 파싱
    symbols = [s.strip() for s in args.symbols.split(",")]
    data_types = [t.strip() for t in args.data_types.split(",")]
    
    # DAG 트리거 실행
    trigger = AirflowKISCollectionTrigger(airflow_url=args.airflow_url)
    success = trigger.trigger_dag(
        symbols=symbols,
        data_types=data_types,
        chart_period=args.chart_period,
        chart_count=args.chart_count
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()


# 사용 예제들
if __name__ == "__main__" and len(sys.argv) == 1:
    print("""
🚀 KIS 데이터 수집 DAG 트리거 사용법:

# 기본 실행 (삼성전자, SK하이닉스, 카카오)
python trigger_kis_collection.py

# 특정 종목 지정
python trigger_kis_collection.py --symbols "005930,373220,068270"

# 현재가만 수집
python trigger_kis_collection.py --data-types "price"

# 차트만 수집 (200개 데이터)
python trigger_kis_collection.py --data-types "chart" --chart-count 200

# 주봉 데이터 수집
python trigger_kis_collection.py --chart-period "W"

# 전체 옵션 지정
python trigger_kis_collection.py \
    --symbols "005930,000660,035420,035720" \
    --data-types "price,chart" \
    --chart-period "D" \
    --chart-count 150

🔍 지원하는 종목 코드 예시:
- 삼성전자: 005930
- SK하이닉스: 000660  
- NAVER: 035420
- 카카오: 035720
- 삼성바이오로직스: 207940
- 셀트리온: 068270
- LG에너지솔루션: 373220

📊 지원하는 데이터 타입:
- price: 현재가 정보
- chart: OHLCV 차트 데이터

⏰ 지원하는 차트 기간:
- D: 일봉
- W: 주봉
- M: 월봉
- Y: 년봉
    """)