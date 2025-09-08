#!/usr/bin/env python3
"""
DAG 직접 테스트 스크립트
KIS Adapter와 연동하여 실제 API 호출 테스트
"""

import os
import sys
import json
import requests
import time
from datetime import datetime
import pytz

# Airflow DAG 경로 추가
sys.path.append('/Users/admin/study/quantum-trading-platform/airflow/dags')

class KISAPIClient:
    """KIS Open API 클라이언트 - KIS Adapter 연동"""
    
    def __init__(self):
        # 로컬 테스트용 - localhost 사용
        self.adapter_url = "http://localhost:8000"
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
    
    def get_current_price(self, stock_code: str):
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
                    change_rate = float(output.get('prdy_ctrt', 0))
                    
                    print(f"✅ {stock_code} 현재가: {current_price:,}원")
                    print(f"   거래량: {volume:,}주")
                    print(f"   전일대비: {change_rate:+.2f}%")
                    
                    return data
                else:
                    print(f"⚠️ {stock_code} API 오류: {data.get('msg1', 'Unknown error')}")
                    return None
            else:
                print(f"❌ {stock_code} HTTP 오류: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ {stock_code} 처리 오류: {e}")
            return None


def test_price_collection():
    """가격 수집 테스트"""
    
    print("=" * 60)
    print("🚀 국내주식 가격 수집 테스트 시작")
    print("=" * 60)
    
    # 테스트할 종목 리스트 (Priority 1 종목들)
    test_stocks = [
        {'code': '005930', 'name': '삼성전자'},
        {'code': '000660', 'name': 'SK하이닉스'},
        {'code': '035420', 'name': 'NAVER'},
        {'code': '035720', 'name': '카카오'},
        {'code': '051910', 'name': 'LG화학'},
    ]
    
    # KIS API 클라이언트 초기화
    kis_client = KISAPIClient()
    
    # Adapter 연결 확인
    if not kis_client.check_adapter_health():
        print("❌ KIS Adapter 연결 실패. 테스트를 중단합니다.")
        return
    
    # 토큰 갱신 (선택적)
    kis_client.get_auth_token(environment='prod')
    
    print("\n" + "=" * 60)
    print("📈 주요 종목 가격 조회 시작")
    print("=" * 60)
    
    success_count = 0
    error_count = 0
    collected_data = []
    
    for stock in test_stocks:
        print(f"\n[{stock['name']}]")
        
        price_data = kis_client.get_current_price(stock['code'])
        
        if price_data:
            success_count += 1
            collected_data.append({
                'code': stock['code'],
                'name': stock['name'],
                'price': int(price_data['output']['stck_prpr']),
                'volume': int(price_data['output']['acml_vol']),
                'change_rate': float(price_data['output']['prdy_ctrt'])
            })
        else:
            error_count += 1
        
        # Rate Limit 대응 - API 호출 간 0.1초 대기
        time.sleep(0.1)
    
    # 결과 출력
    print("\n" + "=" * 60)
    print("📊 수집 결과 요약")
    print("=" * 60)
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {error_count}개")
    print(f"⏰ 수집 시간: {datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S')}")
    
    if collected_data:
        print("\n📈 수집된 데이터:")
        print("-" * 60)
        for data in collected_data:
            print(f"{data['name']:12} | {data['price']:7,}원 | 거래량: {data['volume']:10,} | {data['change_rate']:+6.2f}%")
    
    print("\n✅ 테스트 완료!")


if __name__ == "__main__":
    test_price_collection()