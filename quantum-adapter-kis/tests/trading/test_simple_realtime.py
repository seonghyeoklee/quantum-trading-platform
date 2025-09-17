#!/usr/bin/env python3
"""
간단한 실시간 매매 테스트
실제 잔고 부족 상황에서 시스템 동작 확인
"""

import asyncio
import logging
from datetime import datetime

from realtime_auto_trader import RealtimeAutoTrader

async def test_simple_realtime():
    """간단한 실시간 테스트"""
    print("🚀 간단한 실시간 매매 테스트 시작")
    print("="*50)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)

    # 로깅 설정
    logging.basicConfig(level=logging.INFO)

    # 자동매매 시스템 생성 (모의투자, 수동 모드)
    trader = RealtimeAutoTrader(
        environment="vps",  # 모의투자
        auto_mode=False     # 수동 승인 모드
    )

    try:
        print("\n🔧 시스템 초기화 중...")

        # 초기화 (WebSocket 연결 없이)
        print("✅ 컴포넌트 초기화 완료")

        # KIS 인증 테스트
        print("\n🔑 KIS 인증 테스트...")
        auth_success = await trader.executor.authenticate()

        if auth_success:
            print("✅ KIS 인증 성공")

            # 계좌 정보 조회 테스트
            print("\n💰 계좌 정보 조회 테스트...")
            account_info = await trader.executor.get_account_summary()

            if account_info:
                print(f"✅ 계좌 조회 성공")
                print(f"   총 자산: {account_info.get('total_assets', 0):,}원")
                print(f"   사용 가능 현금: {account_info.get('available_cash', 0):,}원")
                print(f"   보유 종목 수: {account_info.get('stock_count', 0)}개")
                print(f"   환경: {account_info.get('environment', 'unknown')}")

                # 실제 주문 테스트 (1주만)
                print("\n📊 실제 주문 테스트 (1주)...")
                await test_single_order(trader)

            else:
                print("❌ 계좌 조회 실패 - 잔고 부족 시나리오 발생!")
                print("💡 이는 실제 계좌에 돈이 없거나 계좌 설정에 문제가 있을 때 나타납니다")

        else:
            print("❌ KIS 인증 실패")
            print("💡 이는 API 키 설정이나 네트워크 문제일 수 있습니다")

    except Exception as e:
        print(f"❌ 테스트 오류: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*50)
    print("✅ 간단한 실시간 테스트 완료")
    print("="*50)

async def test_single_order(trader):
    """단일 주문 테스트"""
    try:
        # 삼성전자 1주 주문 테스트
        symbol = "005930"
        quantity = 1
        price = 71000  # 대략적인 가격

        print(f"🎯 주문 테스트: {symbol} {quantity}주 @ {price:,}원")

        # 주문 조건 검증
        is_valid = await trader._validate_order_conditions(symbol, quantity, price)

        if is_valid:
            print("✅ 주문 조건 검증 통과")

            # 사용자 확인
            user_input = input("실제 주문을 실행하시겠습니까? (y/n): ").lower().strip()

            if user_input == 'y':
                print("🚀 실제 주문 실행...")
                order_result = await trader.executor.execute_buy_order(
                    symbol=symbol,
                    quantity=quantity,
                    price=price,
                    order_type="limit"
                )

                if order_result and order_result.get('success'):
                    print(f"✅ 주문 성공! 주문번호: {order_result.get('order_id')}")
                else:
                    error_msg = order_result.get('error_message', '알 수 없는 오류') if order_result else '주문 실패'
                    print(f"❌ 주문 실패: {error_msg}")

                    # 잔고 부족 체크
                    if order_result and ('40310000' in order_result.get('error_code', '') or '잔고부족' in error_msg):
                        print("💰 잔고 부족 확인됨!")
                        print("   - 이는 예상된 상황입니다")
                        print("   - 시스템이 올바르게 작동하고 있습니다")
            else:
                print("⏭️ 주문 건너뛰기")

        else:
            print("❌ 주문 조건 검증 실패")
            print("💡 이는 잔고 부족이나 기타 조건 문제입니다")

    except Exception as e:
        print(f"❌ 주문 테스트 오류: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_realtime())