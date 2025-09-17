"""
디노테스트 가격분석 API 테스트 스크립트

실제 KIS API 데이터로 가격분석 점수 계산을 테스트합니다.
"""

import sys
import logging
import requests
import json
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_dino_price_api():
    """디노테스트 가격분석 API 테스트"""
    
    # API 엔드포인트
    base_url = "http://localhost:8000"
    
    # 테스트할 종목들
    test_stocks = [
        {"code": "005930", "name": "삼성전자"},
        {"code": "000660", "name": "SK하이닉스"},
        {"code": "035420", "name": "NAVER"},
        {"code": "207940", "name": "삼성바이오로직스"},
        {"code": "068270", "name": "셀트리온"}
    ]
    
    print("=" * 80)
    print("디노테스트 가격분석 API 테스트")
    print("=" * 80)
    
    for stock in test_stocks:
        stock_code = stock["code"]
        stock_name = stock["name"]
        
        print(f"\n📊 {stock_name} ({stock_code}) 가격분석 테스트")
        print("-" * 60)
        
        try:
            # API 호출
            url = f"{base_url}/dino-test/price/{stock_code}"
            response = requests.get(url, timeout=60)  # 60초 타임아웃
            
            if response.status_code == 200:
                result = response.json()
                
                print("✅ API 호출 성공")
                print(f"📈 총점: {result['total_score']}/5점")
                print(f"🔝 최고가 대비 점수: {result['high_ratio_score']}점 - {result['high_ratio_status']}")
                print(f"🔻 최저가 대비 점수: {result['low_ratio_score']}점 - {result['low_ratio_status']}")
                
                # 계산 근거 데이터 출력
                print("\n📋 계산 근거 데이터:")
                raw_data = result.get('raw_data', {})
                for key, value in raw_data.items():
                    print(f"   {key}: {value}")
                
                print(f"\n💬 메시지: {result.get('message', '')}")
                
            else:
                print(f"❌ API 호출 실패: {response.status_code}")
                print(f"응답: {response.text}")
                
        except requests.exceptions.Timeout:
            print("❌ API 호출 타임아웃 (60초 초과)")
        except requests.exceptions.RequestException as e:
            print(f"❌ API 호출 오류: {e}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON 디코딩 오류: {e}")
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
    
    print("\n" + "=" * 80)
    print("테스트 완료")
    print("=" * 80)

def test_single_stock(stock_code: str):
    """단일 종목 상세 테스트"""
    
    base_url = "http://localhost:8000"
    
    print("=" * 80)
    print(f"단일 종목 가격분석 상세 테스트: {stock_code}")
    print("=" * 80)
    
    try:
        # API 호출
        url = f"{base_url}/dino-test/price/{stock_code}"
        response = requests.get(url, timeout=120)  # 2분 타임아웃
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ API 호출 성공")
            print("\n📊 가격분석 결과:")
            print(f"   종목코드: {result['stock_code']}")
            print(f"   총점: {result['total_score']}/5점")
            print(f"   최고가 대비 점수: {result['high_ratio_score']}")
            print(f"   최저가 대비 점수: {result['low_ratio_score']}")
            print(f"   최고가 비율 상태: {result['high_ratio_status']}")
            print(f"   최저가 비율 상태: {result['low_ratio_status']}")
            
            print("\n📋 상세 계산 데이터:")
            raw_data = result.get('raw_data', {})
            for key, value in raw_data.items():
                print(f"   {key}: {value}")
            
            print(f"\n💬 응답 메시지: {result.get('message', '')}")
            
            # JSON 전체 응답 출력
            print("\n📄 전체 JSON 응답:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            print(f"응답 내용: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ API 호출 타임아웃 (120초 초과)")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 명령행 인수가 있으면 단일 종목 테스트
        stock_code = sys.argv[1]
        test_single_stock(stock_code)
    else:
        # 명령행 인수가 없으면 전체 테스트
        test_dino_price_api()