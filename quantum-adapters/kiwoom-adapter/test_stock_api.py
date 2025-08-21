"""
키움 종목정보 API 테스트 스크립트

사용법:
python test_stock_api.py
"""
import asyncio
import os
import sys
from pathlib import Path

# src 경로를 Python path에 추가
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from kiwoom_api.functions.stock import fn_ka10001, get_stock_info, get_multiple_stock_info
from kiwoom_api.functions.auth import get_valid_access_token


async def test_fn_ka10001():
    """fn_ka10001 함수 직접 테스트"""
    print("=== fn_ka10001 함수 테스트 ===")
    
    try:
        # 1. 토큰 발급
        print("🔑 토큰 발급 중...")
        token = await get_valid_access_token()
        print(f"✅ 토큰 발급 성공: {token[:20]}...")
        
        # 2. 삼성전자 종목정보 조회
        print("\n📊 삼성전자(005930) 종목정보 조회 중...")
        result = await fn_ka10001(
            token=token,
            data={"stk_cd": "005930"}
        )
        
        print(f"응답 코드: {result['Code']}")
        if result['Code'] == 200:
            body = result['Body']
            print(f"종목명: {body.get('stk_nm', 'N/A')}")
            print(f"현재가: {body.get('cur_prc', 'N/A')}")
            print(f"전일대비: {body.get('pred_pre', 'N/A')}")
            print(f"등락율: {body.get('flu_rt', 'N/A')}%")
            print(f"PER: {body.get('per', 'N/A')}")
            print(f"PBR: {body.get('pbr', 'N/A')}")
        else:
            print(f"❌ 오류: {result['Body']}")
            
    except Exception as e:
        print(f"❌ fn_ka10001 테스트 실패: {str(e)}")


async def test_get_stock_info():
    """get_stock_info 함수 테스트"""
    print("\n=== get_stock_info 함수 테스트 ===")
    
    try:
        # SK하이닉스 종목정보 조회
        print("📊 SK하이닉스(000660) 종목정보 조회 중...")
        result = await get_stock_info("000660")
        
        print(f"응답 코드: {result.return_code}")
        print(f"응답 메시지: {result.return_msg}")
        
        if result.return_code == 0 and result.data:
            data = result.data
            print(f"종목명: {data.stk_nm}")
            print(f"현재가: {data.cur_prc}")
            print(f"전일대비: {data.pred_pre}")
            print(f"등락율: {data.flu_rt}%")
            print(f"거래량: {data.trde_qty}")
            print(f"시가총액: {data.mac}")
        else:
            print(f"❌ 오류: {result.return_msg}")
            
    except Exception as e:
        print(f"❌ get_stock_info 테스트 실패: {str(e)}")


async def test_multiple_stock_info():
    """여러 종목 일괄 조회 테스트"""
    print("\n=== 일괄 종목정보 조회 테스트 ===")
    
    try:
        stock_codes = ["005930", "000660", "035420", "035720", "051910"]
        stock_names = ["삼성전자", "SK하이닉스", "NAVER", "카카오", "LG화학"]
        
        print(f"📊 {len(stock_codes)}개 종목 일괄 조회 중...")
        results = await get_multiple_stock_info(stock_codes)
        
        print("\n조회 결과:")
        print("-" * 80)
        print(f"{'종목코드':<10} {'종목명':<15} {'현재가':<10} {'등락율':<8} {'PER':<8} {'PBR':<8}")
        print("-" * 80)
        
        for i, (stk_cd, result) in enumerate(results.items()):
            if result.return_code == 0 and result.data:
                data = result.data
                print(f"{stk_cd:<10} {data.stk_nm:<15} {data.cur_prc:<10} {data.flu_rt:<8} {data.per:<8} {data.pbr:<8}")
            else:
                expected_name = stock_names[i] if i < len(stock_names) else "알 수 없음"
                print(f"{stk_cd:<10} {expected_name:<15} {'오류':<10} {'N/A':<8} {'N/A':<8} {'N/A':<8}")
                
        print("-" * 80)
        
        # 성공/실패 통계
        success_count = sum(1 for r in results.values() if r.return_code == 0)
        failure_count = len(results) - success_count
        print(f"✅ 성공: {success_count}개, ❌ 실패: {failure_count}개")
        
    except Exception as e:
        print(f"❌ 일괄 조회 테스트 실패: {str(e)}")


async def test_invalid_stock_code():
    """잘못된 종목코드 테스트"""
    print("\n=== 잘못된 종목코드 테스트 ===")
    
    try:
        print("📊 존재하지 않는 종목코드(999999) 조회 중...")
        result = await get_stock_info("999999")
        
        print(f"응답 코드: {result.return_code}")
        print(f"응답 메시지: {result.return_msg}")
        
        if result.return_code != 0:
            print("✅ 예상대로 오류 응답을 받았습니다.")
        else:
            print("⚠️ 예상과 다르게 성공 응답을 받았습니다.")
            
    except Exception as e:
        print(f"❌ 잘못된 종목코드 테스트 실패: {str(e)}")


async def test_performance():
    """성능 테스트"""
    print("\n=== 성능 테스트 ===")
    
    try:
        import time
        
        # 개별 조회 성능 테스트
        print("📊 개별 조회 성능 테스트 (5회)...")
        start_time = time.time()
        
        for i in range(5):
            result = await get_stock_info("005930")
            if result.return_code == 0:
                print(f"  조회 {i+1}: 성공")
            else:
                print(f"  조회 {i+1}: 실패")
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 5
        print(f"평균 응답시간: {avg_time:.2f}초")
        
        # 일괄 조회 성능 테스트
        print("\n📊 일괄 조회 성능 테스트 (3개 종목)...")
        start_time = time.time()
        
        results = await get_multiple_stock_info(["005930", "000660", "035420"])
        
        end_time = time.time()
        batch_time = end_time - start_time
        success_count = sum(1 for r in results.values() if r.return_code == 0)
        
        print(f"일괄 조회 시간: {batch_time:.2f}초")
        print(f"성공한 종목: {success_count}/3개")
        print(f"종목당 평균 시간: {batch_time/3:.2f}초")
        
    except Exception as e:
        print(f"❌ 성능 테스트 실패: {str(e)}")


def print_help():
    """도움말 출력"""
    print("""
=== 키움 종목정보 API 테스트 ===

이 스크립트는 키움 종목정보 API(ka10001)의 기본 기능을 테스트합니다.

사전 요구사항:
1. 환경변수 설정:
   - KIWOOM_SANDBOX_APP_KEY (모의투자용)
   - KIWOOM_SANDBOX_APP_SECRET
   또는
   - KIWOOM_PRODUCTION_APP_KEY (실제 투자용)
   - KIWOOM_PRODUCTION_APP_SECRET

2. 올바른 키움증권 OAuth 토큰

테스트 내용:
- fn_ka10001 함수 직접 호출 테스트
- get_stock_info 래퍼 함수 테스트
- 여러 종목 일괄 조회 테스트
- 잘못된 종목코드 처리 테스트
- API 성능 테스트

사용법:
    python test_stock_api.py
    """)


async def main():
    """메인 함수"""
    print_help()
    
    try:
        # 모든 테스트 실행
        await test_fn_ka10001()
        await test_get_stock_info()
        await test_multiple_stock_info()
        await test_invalid_stock_code()
        await test_performance()
        
        print("\n" + "=" * 60)
        print("🎉 모든 테스트 완료!")
        print("\n📝 추가 테스트 방법:")
        print("   1. 브라우저에서 http://localhost:8100/docs 접속")
        print("   2. 'Stock API' 섹션에서 종목정보 API 테스트")
        print("   3. Swagger UI를 통한 대화형 API 테스트")
        
    except KeyboardInterrupt:
        print("\n👋 사용자에 의해 테스트 중단됨")
    except Exception as e:
        print(f"\n💥 테스트 실행 중 오류: {str(e)}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 테스트 스크립트 종료")
    except Exception as e:
        print(f"\n💥 스크립트 실행 오류: {str(e)}")
        sys.exit(1)