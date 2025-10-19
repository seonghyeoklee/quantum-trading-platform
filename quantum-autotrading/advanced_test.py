"""
고급 시나리오 테스트

실제 단타 매매 상황을 시뮬레이션합니다.
"""

import asyncio
import httpx
import json
from datetime import datetime
import time

async def simulate_day_trading():
    """하루 단타 매매 시뮬레이션"""
    
    print("🚀 === 하루 단타 매매 시뮬레이션 시작 ===")
    print(f"시작 시간: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    async with httpx.AsyncClient() as client:
        base_url = "http://localhost:8001"
        
        # 1. 시장 개장 전 준비
        print("📋 1. 시장 개장 전 준비")
        
        # 계좌 잔고 확인
        response = await client.get(f"{base_url}/system/balance")
        balance = response.json()
        print(f"   💰 시작 잔고: {balance['total_balance']:,}원")
        
        # 관심종목 리스트
        watchlist = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, NAVER
        
        print(f"   📊 관심종목: {', '.join(watchlist)}")
        print()
        
        # 2. 자동매매 시작
        print("🚀 2. 자동매매 시작")
        response = await client.post(f"{base_url}/trading/start")
        print(f"   ✅ 자동매매 상태: {response.json()['status']}")
        print()
        
        # 3. 실시간 모니터링 및 매매 (5분간 시뮬레이션)
        print("📈 3. 실시간 매매 시뮬레이션 (30초간)")
        
        for minute in range(6):  # 6번 반복 (30초간)
            print(f"\n⏰ {minute+1}분차 상황:")
            
            # 각 종목별 현재가 및 기술적 지표 확인
            for symbol in watchlist:
                # 현재가 조회
                price_response = await client.get(f"{base_url}/market-data/stocks/{symbol}/price")
                price_data = price_response.json()
                
                # 기술적 지표 조회
                indicator_response = await client.get(f"{base_url}/market-data/stocks/{symbol}/indicators")
                indicators = indicator_response.json()
                
                print(f"   📊 {symbol}: {price_data['current_price']:,}원 "
                      f"({price_data['change_percent']:+.2f}%) "
                      f"RSI:{indicators['rsi']:.1f}")
                
                # 매매 신호 확인
                signal_response = await client.get(f"{base_url}/trading/signals?symbol={symbol}&limit=1")
                signals = signal_response.json()
                
                if signals:
                    signal = signals[0]
                    signal_strength = signal['strength']
                    confidence = signal['confidence']
                    
                    # 강한 매수 신호 (강도 > 0.8, 신뢰도 > 0.85)
                    if (signal['signal_type'] == 'buy' and 
                        signal_strength > 0.8 and confidence > 0.85):
                        
                        print(f"   🔥 강한 매수 신호 감지! 강도:{signal_strength:.2f}, 신뢰도:{confidence:.2f}")
                        
                        # 매수 주문 실행
                        order_data = {
                            "symbol": symbol,
                            "side": "buy",
                            "order_type": "market",
                            "quantity": 10
                        }
                        
                        try:
                            order_response = await client.post(f"{base_url}/trading/order", json=order_data)
                            if order_response.status_code == 200:
                                order_result = order_response.json()
                                print(f"   ✅ 매수 주문 체결: {order_result['order_id']}")
                            else:
                                print(f"   ❌ 주문 실패: {order_response.json().get('detail', 'Unknown error')}")
                        except Exception as e:
                            print(f"   ❌ 주문 오류: {e}")
                    
                    # 강한 매도 신호 또는 익절/손절 조건
                    elif signal['signal_type'] == 'sell' and signal_strength > 0.7:
                        print(f"   📉 매도 신호: 강도:{signal_strength:.2f}")
            
            # 현재 포지션 상태 확인
            positions_response = await client.get(f"{base_url}/trading/positions")
            positions = positions_response.json()
            
            if positions:
                print(f"   📈 현재 포지션 {len(positions)}개:")
                total_pnl = 0
                for pos in positions:
                    pnl = pos['unrealized_pnl']
                    pnl_percent = pos['unrealized_pnl_percent']
                    total_pnl += pnl
                    
                    status_emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
                    print(f"      {status_emoji} {pos['symbol']}: {pos['quantity']}주, "
                          f"손익 {pnl:+,.0f}원 ({pnl_percent:+.2f}%)")
                
                print(f"   💰 총 평가손익: {total_pnl:+,.0f}원")
                
                # 손절/익절 체크
                for pos in positions:
                    pnl_percent = pos['unrealized_pnl_percent']
                    
                    # 손절 조건: -2% 이하
                    if pnl_percent <= -2.0:
                        print(f"   🚨 {pos['symbol']} 손절 조건 도달! ({pnl_percent:.2f}%)")
                        
                        # 손절 매도 주문
                        sell_order = {
                            "symbol": pos['symbol'],
                            "side": "sell",
                            "order_type": "market",
                            "quantity": pos['quantity']
                        }
                        
                        sell_response = await client.post(f"{base_url}/trading/order", json=sell_order)
                        if sell_response.status_code == 200:
                            print(f"   ✅ 손절 매도 완료: {pos['symbol']}")
                    
                    # 익절 조건: +3% 이상
                    elif pnl_percent >= 3.0:
                        print(f"   🎯 {pos['symbol']} 익절 조건 도달! ({pnl_percent:.2f}%)")
                        
                        # 익절 매도 주문
                        sell_order = {
                            "symbol": pos['symbol'],
                            "side": "sell", 
                            "order_type": "market",
                            "quantity": pos['quantity']
                        }
                        
                        sell_response = await client.post(f"{base_url}/trading/order", json=sell_order)
                        if sell_response.status_code == 200:
                            print(f"   ✅ 익절 매도 완료: {pos['symbol']}")
            else:
                print("   📊 현재 포지션 없음")
            
            # 5초 대기 (실제로는 5분)
            await asyncio.sleep(5)
        
        # 4. 장 마감 전 정리
        print("\n🕐 4. 장 마감 전 정리")
        
        # 남은 포지션 확인
        final_positions_response = await client.get(f"{base_url}/trading/positions")
        final_positions = final_positions_response.json()
        
        if final_positions:
            print(f"   📊 마감 전 포지션 {len(final_positions)}개:")
            
            for pos in final_positions:
                pnl = pos['unrealized_pnl']
                pnl_percent = pos['unrealized_pnl_percent']
                
                print(f"      {pos['symbol']}: {pos['quantity']}주, "
                      f"손익 {pnl:+,.0f}원 ({pnl_percent:+.2f}%)")
                
                # 마감 전 전량 매도 (데이트레이딩)
                close_order = {
                    "symbol": pos['symbol'],
                    "side": "sell",
                    "order_type": "market", 
                    "quantity": pos['quantity']
                }
                
                close_response = await client.post(f"{base_url}/trading/order", json=close_order)
                if close_response.status_code == 200:
                    print(f"      ✅ {pos['symbol']} 마감 매도 완료")
        else:
            print("   📊 마감할 포지션 없음")
        
        # 5. 일일 성과 분석
        print("\n📊 5. 일일 성과 분석")
        
        # 거래 내역 조회
        history_response = await client.get(f"{base_url}/trading/history?limit=20")
        trades = history_response.json()
        
        print(f"   📋 총 거래 건수: {len(trades)}건")
        
        # 성과 지표 조회
        performance_response = await client.get(f"{base_url}/system/performance/daily")
        performance = performance_response.json()
        
        print(f"   💰 일일 손익: {performance['total_pnl']:+,}원 ({performance['total_pnl_percent']:+.2f}%)")
        print(f"   🎯 승률: {performance['win_rate']:.1f}%")
        print(f"   🏆 최고 수익: +{performance['best_trade']:,}원")
        print(f"   📉 최대 손실: {performance['worst_trade']:,}원")
        
        # 6. 자동매매 중지
        print("\n🛑 6. 자동매매 중지")
        stop_response = await client.post(f"{base_url}/trading/stop")
        print(f"   ✅ 자동매매 상태: {stop_response.json()['status']}")
        
        print(f"\n🏁 시뮬레이션 완료: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(simulate_day_trading())
