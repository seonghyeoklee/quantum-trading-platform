#!/usr/bin/env python3
"""
실전모드 주문 테스트
실제 KIS API를 통한 주문 테스트 (매우 소량)
"""

import asyncio
import logging
from trading_strategy.core.kis_order_executor import KisOrderExecutor

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_prod_order():
    """실전모드에서 매우 소량 주문 테스트"""
    print("🚀 실전모드 주문 테스트 시작...")

    # 실전투자 환경으로 실행기 생성
    executor = KisOrderExecutor(environment="prod")

    # 1. 인증 테스트
    print("\n📍 1단계: 실전투자 인증 테스트")
    auth_result = await executor.authenticate()
    if not auth_result:
        print("❌ 인증 실패 - 테스트 중단")
        return

    # 2. 계좌 잔고 조회
    print("\n📍 2단계: 실전계좌 잔고 조회")
    account_info = await executor.get_account_summary()
    if account_info:
        print(f"💰 총 자산: {account_info['total_assets']:,}원")
        print(f"💵 사용가능현금: {account_info['available_cash']:,}원")
        print(f"📊 보유종목수: {account_info['stock_count']}개")
        print(f"🌍 거래환경: {account_info['environment']} (실전투자)")
    else:
        print("❌ 계좌 정보 조회 실패")
        return

    # 3. 매우 소량 매수 주문 테스트 (최소금액)
    print("\n📍 3단계: 소량 매수 주문 테스트")

    # 삼성전자 1주 매수 시도 (최소 주문 단위)
    symbol = "005930"  # 삼성전자
    quantity = 1       # 1주만
    price = 50000      # 5만원 지정가 (현재가보다 낮게 설정하여 실제 체결 방지)

    print(f"📝 주문 정보:")
    print(f"   종목: {symbol} (삼성전자)")
    print(f"   수량: {quantity}주")
    print(f"   가격: {price:,}원 (시장가보다 낮은 지정가)")
    print(f"   예상금액: {price * quantity:,}원")

    # 잔고 확인
    if account_info['available_cash'] < price * quantity:
        print(f"⚠️ 잔고부족 시나리오 테스트:")
        print(f"   필요금액: {price * quantity:,}원")
        print(f"   보유현금: {account_info['available_cash']:,}원")

    # 매수 주문 실행
    buy_result = await executor.execute_buy_order(symbol, quantity, price)

    print(f"\n📋 매수 주문 결과:")
    if buy_result.get("success"):
        print(f"✅ 주문 성공!")
        print(f"📄 주문번호: {buy_result.get('order_id')}")
        print(f"⏰ 주문시간: {buy_result.get('timestamp')}")
    else:
        print(f"❌ 주문 실패")
        print(f"🔧 오류코드: {buy_result.get('error_code')}")
        print(f"💬 오류메시지: {buy_result.get('error_message')}")

        # 잔고부족 오류인 경우 정상적인 시나리오
        if buy_result.get('error_code') == '40310000':
            print(f"✅ 잔고부족 오류 - 정상적인 시나리오입니다")

    # 4. 주문 상태 조회 (성공한 경우만)
    if buy_result.get("success"):
        print("\n📍 4단계: 주문 상태 조회")
        order_id = buy_result.get('order_id')
        order_status = await executor.get_order_status(order_id)

        if order_status:
            print(f"📊 주문 상태: {order_status['status']}")
            print(f"📈 종목: {order_status['symbol']}")
            print(f"📊 수량: {order_status['quantity']}주")
            print(f"💰 가격: {order_status['price']:,}원")

    print("\n🏁 실전모드 주문 테스트 완료")
    print("\n⚠️ 주의사항:")
    print("   - 이 테스트는 실제 계좌에서 실행됩니다")
    print("   - 낮은 지정가로 실제 체결을 방지했습니다")
    print("   - 실제 투자 시에는 신중하게 진행하세요")

if __name__ == "__main__":
    asyncio.run(test_prod_order())