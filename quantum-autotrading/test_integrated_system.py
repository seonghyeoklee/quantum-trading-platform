"""
실제 KIS API가 통합된 자동매매 시스템 테스트

quantum-autotrading 시스템에 실제 KIS API를 적용하여 테스트합니다.
"""

import asyncio
import sys
import os
from datetime import datetime

# 프로젝트 경로 추가
sys.path.append('/Users/admin/study/quantum-trading-platform/quantum-autotrading')

from app.utils.kis_client import KISClient, KISResponse
from app.config import settings

async def test_integrated_kis_client():
    """통합된 KIS 클라이언트 테스트"""
    
    print("🚀 === 실제 KIS API 통합 시스템 테스트 ===")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 설정 정보 출력
    print("📋 시스템 설정:")
    print(f"   App Name: {settings.app_name}")
    print(f"   KIS Base URL: {settings.kis_base_url}")
    print(f"   KIS Use Mock: {settings.KIS_USE_MOCK}")
    print(f"   Account: {settings.KIS_CANO}")
    print()
    
    results = []
    
    try:
        # KIS 클라이언트 생성 및 초기화
        print("1️⃣ === KIS 클라이언트 초기화 ===")
        
        async with KISClient() as client:
            print("✅ KIS 클라이언트 생성 완료")
            
            # 2. 인증 테스트
            print("\n2️⃣ === KIS API 인증 테스트 ===")
            auth_success = await client.authenticate()
            results.append(("KIS API 인증", auth_success))
            
            if not auth_success:
                print("❌ 인증 실패로 테스트를 중단합니다.")
                return
            
            # 3. 현재가 조회 테스트
            print("\n3️⃣ === 현재가 조회 테스트 ===")
            
            # 삼성전자 현재가 조회
            print("📊 삼성전자(005930) 현재가 조회 중...")
            samsung_response = await client.get_current_price("005930")
            
            if samsung_response.success:
                output = samsung_response.data.get("output", {})
                current_price = output.get("stck_prpr", "N/A")
                change_rate = output.get("prdy_ctrt", "N/A")
                
                print(f"✅ 삼성전자 현재가 조회 성공")
                print(f"   💹 현재가: {current_price}원")
                print(f"   📈 등락률: {change_rate}%")
                results.append(("삼성전자 현재가", True))
            else:
                print(f"❌ 삼성전자 현재가 조회 실패: {samsung_response.error_message}")
                results.append(("삼성전자 현재가", False))
            
            # 4. 호가창 조회 테스트
            print("\n4️⃣ === 호가창 조회 테스트 ===")
            print("📊 삼성전자(005930) 호가창 조회 중...")
            
            orderbook_response = await client.get_order_book("005930")
            
            if orderbook_response.success:
                print("✅ 호가창 조회 성공")
                # 호가창 데이터 간단히 출력
                output = orderbook_response.data.get("output1", {})
                bid1_price = output.get("bidp1", "N/A")
                ask1_price = output.get("askp1", "N/A")
                
                print(f"   💰 1호가 매수: {bid1_price}원")
                print(f"   💰 1호가 매도: {ask1_price}원")
                results.append(("호가창 조회", True))
            else:
                print(f"❌ 호가창 조회 실패: {orderbook_response.error_message}")
                results.append(("호가창 조회", False))
            
            # 5. 계좌 잔고 조회 테스트
            print("\n5️⃣ === 계좌 잔고 조회 테스트 ===")
            print("💰 계좌 잔고 조회 중...")
            
            balance_response = await client.get_account_balance()
            
            if balance_response.success:
                print("✅ 계좌 잔고 조회 성공")
                output2 = balance_response.data.get("output2", [{}])[0]
                total_balance = output2.get("tot_evlu_amt", "N/A")
                cash_balance = output2.get("dnca_tot_amt", "N/A")
                
                print(f"   💵 총 평가금액: {total_balance}원")
                print(f"   💰 예수금: {cash_balance}원")
                results.append(("계좌 잔고", True))
            else:
                print(f"❌ 계좌 잔고 조회 실패: {balance_response.error_message}")
                results.append(("계좌 잔고", False))
            
            # 6. 연결 상태 확인
            print("\n6️⃣ === 연결 상태 확인 ===")
            connection_ok = await client.check_connection()
            results.append(("연결 상태", connection_ok))
            
            if connection_ok:
                print("✅ KIS API 연결 상태 양호")
            else:
                print("❌ KIS API 연결 상태 불량")
    
    except Exception as e:
        print(f"❌ 시스템 테스트 오류: {e}")
        results.append(("시스템 오류", False))
    
    # 7. 결과 요약
    print("\n🎯 === 통합 시스템 테스트 결과 ===")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\n📊 총 테스트: {total_tests}")
    print(f"📊 성공: {passed_tests}")
    print(f"📊 실패: {total_tests - passed_tests}")
    print(f"📊 성공률: {(passed_tests/total_tests*100):.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 모든 테스트가 성공했습니다!")
        print("   quantum-autotrading 시스템이 실제 KIS API와 완벽하게 통합되었습니다!")
        print("   🚀 이제 실제 자동매매를 시작할 준비가 되었습니다!")
    elif passed_tests >= total_tests * 0.8:
        print(f"\n✅ 대부분의 테스트가 성공했습니다! ({(passed_tests/total_tests*100):.1f}%)")
        print("   시스템이 정상적으로 작동하고 있습니다.")
    else:
        print(f"\n⚠️ {total_tests - passed_tests}개의 테스트가 실패했습니다.")
        print("   시스템 설정을 확인하고 다시 시도해주세요.")
    
    print(f"\n완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def main():
    """메인 함수"""
    await test_integrated_kis_client()

if __name__ == "__main__":
    asyncio.run(main())
