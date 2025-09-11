#!/usr/bin/env python3
"""
종합 DINO 테스트 시스템 테스트

데이터베이스 저장 및 조회 기능을 검증합니다.
"""

import logging
import asyncio
import requests
from datetime import date

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_comprehensive_dino_analysis():
    """종합 DINO 분석 테스트"""
    
    print("🚀 종합 DINO 테스트 시스템 검증 시작\n")
    
    # 1. 직접 ComprehensiveDinoAnalyzer 테스트
    print("=" * 60)
    print("1. ComprehensiveDinoAnalyzer 직접 테스트")
    print("=" * 60)
    
    try:
        from dino_test.comprehensive_analyzer import ComprehensiveDinoAnalyzer
        
        analyzer = ComprehensiveDinoAnalyzer()
        print("✅ ComprehensiveDinoAnalyzer 초기화 성공")
        
        # 삼성전자 종합 분석 (강제 재실행)
        print(f"\n🔍 삼성전자(005930) 종합 DINO 분석 시작...")
        result = analyzer.run_comprehensive_analysis(
            stock_code="005930", 
            company_name="삼성전자",
            force_rerun=True
        )
        
        if result:
            print(f"\n🎉 삼성전자 종합 DINO 분석 결과:")
            print(f"   📊 D001 재무분석: {result.finance_score}점")
            print(f"   🎯 D002 테마분석: {result.theme_score}점")  
            print(f"   💰 D003 소재분석: {result.material_score}점")
            print(f"   📅 D001 이벤트분석: {result.event_score}점")
            print(f"   📈 D008 호재뉴스: {result.positive_news_score}점")
            print(f"   🏦 D009 이자보상배율: {result.interest_coverage_score}점")
            print(f"   🏆 총점: {result.total_score}점")
            print(f"   📅 분석일: {result.analysis_date}")
            print(f"   ✅ 상태: {result.status}")
        else:
            print("❌ 삼성전자 분석 실패 또는 이미 분석됨")
            
    except Exception as e:
        print(f"❌ ComprehensiveDinoAnalyzer 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. 기존 분석 조회 테스트
    print(f"\n" + "=" * 60)
    print("2. 분석 결과 조회 테스트")
    print("=" * 60)
    
    try:
        analyzer = ComprehensiveDinoAnalyzer()
        
        # 모든 결과 조회 (최대 10건)
        print(f"\n📊 모든 분석 결과 조회 (최대 10건)")
        all_results = analyzer.get_analysis_results(limit=10)
        print(f"✅ 조회된 결과: {len(all_results)}건")
        
        for i, result in enumerate(all_results[:3], 1):  # 상위 3건만 출력
            print(f"   {i}. {result['company_name']} ({result['stock_code']}): "
                  f"총점 {result['total_score']}점, 등급 {result['analysis_grade']}")
        
        # 삼성전자 결과 조회
        print(f"\n🔍 삼성전자(005930) 결과 조회")
        samsung_results = analyzer.get_analysis_results(stock_code="005930", limit=1)
        if samsung_results:
            result = samsung_results[0]
            print(f"✅ 최신 결과: 총점 {result['total_score']}점, "
                  f"등급 {result['analysis_grade']}, 분석일 {result['analysis_date']}")
        else:
            print("❌ 삼성전자 결과 없음")
        
        # 오늘 날짜 결과 조회
        today = date.today()
        print(f"\n📅 오늘({today}) 분석 결과 조회")
        today_results = analyzer.get_analysis_results(analysis_date=today, limit=5)
        print(f"✅ 오늘 분석 결과: {len(today_results)}건")
        
    except Exception as e:
        print(f"❌ 결과 조회 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. 중복 분석 제한 테스트
    print(f"\n" + "=" * 60)
    print("3. 중복 분석 제한 테스트")
    print("=" * 60)
    
    try:
        analyzer = ComprehensiveDinoAnalyzer()
        
        # 같은 종목 재분석 시도 (force_rerun=False)
        print(f"\n🔍 삼성전자 재분석 시도 (force_rerun=False)")
        result = analyzer.run_comprehensive_analysis(
            stock_code="005930", 
            company_name="삼성전자",
            force_rerun=False
        )
        
        if result is None:
            print("✅ 중복 분석 제한 정상 작동 (오늘 이미 분석됨)")
        else:
            print("⚠️ 중복 분석 제한이 작동하지 않음")
            
    except Exception as e:
        print(f"❌ 중복 분석 제한 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n" + "=" * 60)
    print("🎉 종합 DINO 테스트 시스템 검증 완료")
    print("=" * 60)

def test_api_endpoints():
    """FastAPI 엔드포인트 테스트 (서버가 실행 중인 경우)"""
    
    print(f"\n🌐 FastAPI 엔드포인트 테스트")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    try:
        # Health check
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 서버 연결 확인")
            
            # 1. 종합 DINO 분석 API 테스트
            print(f"\n🚀 POST /dino-test/comprehensive API 테스트")
            
            payload = {
                "stock_code": "005930",
                "company_name": "삼성전자",
                "force_rerun": False
            }
            
            response = requests.post(
                f"{base_url}/dino-test/comprehensive", 
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 종합 분석 API 성공: 총점 {data.get('total_score', 0)}점")
            else:
                print(f"⚠️ 종합 분석 API 응답: {response.status_code} - {response.text}")
            
            # 2. 결과 조회 API 테스트
            print(f"\n📊 GET /dino-test/results API 테스트")
            
            response = requests.get(f"{base_url}/dino-test/results?limit=5", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 결과 조회 API 성공: {data.get('total_count', 0)}건")
                
                for result in data.get('results', [])[:2]:  # 상위 2건만 출력
                    print(f"   - {result.get('company_name')} ({result.get('stock_code')}): "
                          f"총점 {result.get('total_score', 0)}점")
            else:
                print(f"⚠️ 결과 조회 API 응답: {response.status_code} - {response.text}")
                
            # 3. 최신 결과 조회 API 테스트
            print(f"\n🔍 GET /dino-test/results/005930/latest API 테스트")
            
            response = requests.get(f"{base_url}/dino-test/results/005930/latest", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {})
                print(f"✅ 최신 결과 API 성공: 총점 {result.get('total_score', 0)}점")
            else:
                print(f"⚠️ 최신 결과 API 응답: {response.status_code} - {response.text}")
        
        else:
            print(f"❌ 서버 연결 실패: {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        print("⚠️ 서버가 실행되지 않음 - API 테스트 건너뜀")
        print("   서버 실행: cd quantum-adapter-kis && uv run python main.py")
    except Exception as e:
        print(f"❌ API 테스트 실패: {e}")

if __name__ == "__main__":
    # 1. 직접 분석기 테스트
    test_comprehensive_dino_analysis()
    
    # 2. API 엔드포인트 테스트 (서버가 실행 중인 경우)
    test_api_endpoints()
    
    print(f"\n✨ 모든 테스트 완료")