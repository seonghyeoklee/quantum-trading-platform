"""
자동매매 시스템 시나리오 테스트

실제 매매 상황을 시뮬레이션하여 시스템을 테스트합니다.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import httpx
from decimal import Decimal

class TradingSystemTester:
    """자동매매 시스템 테스터"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
        
        # 테스트 상태 추적
        self.test_results = []
        self.current_positions = {}
        self.order_history = []
        
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_test(self, test_name: str, status: str, details: Dict[str, Any] = None):
        """테스트 결과 로깅"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "test_name": test_name,
            "status": status,
            "details": details or {}
        }
        self.test_results.append(result)
        
        status_emoji = {"PASS": "✅", "FAIL": "❌", "INFO": "ℹ️"}.get(status, "📋")
        print(f"{status_emoji} [{test_name}] {status}")
        if details:
            print(f"   세부사항: {details}")
    
    async def test_system_health(self) -> bool:
        """시스템 헬스체크 테스트"""
        
        try:
            print("\n🔍 === 시스템 헬스체크 테스트 ===")
            
            # 1. 서버 응답 확인
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                self.log_test("서버 응답", "PASS", {"status_code": response.status_code})
            else:
                self.log_test("서버 응답", "FAIL", {"status_code": response.status_code})
                return False
            
            # 2. 시스템 상태 확인
            response = await self.client.get(f"{self.base_url}/system/status")
            if response.status_code == 200:
                status_data = response.json()
                self.log_test("시스템 상태", "PASS", status_data)
            else:
                self.log_test("시스템 상태", "FAIL", {"status_code": response.status_code})
                return False
            
            # 3. 계좌 잔고 확인
            response = await self.client.get(f"{self.base_url}/system/balance")
            if response.status_code == 200:
                balance_data = response.json()
                self.log_test("계좌 잔고", "PASS", balance_data)
            else:
                self.log_test("계좌 잔고", "FAIL", {"status_code": response.status_code})
                return False
            
            return True
            
        except Exception as e:
            self.log_test("시스템 헬스체크", "FAIL", {"error": str(e)})
            return False
    
    async def test_market_data(self) -> bool:
        """시장 데이터 테스트"""
        
        try:
            print("\n📊 === 시장 데이터 테스트 ===")
            
            test_symbol = "005930"  # 삼성전자
            
            # 1. 현재가 조회
            response = await self.client.get(f"{self.base_url}/market-data/stocks/{test_symbol}/price")
            if response.status_code == 200:
                price_data = response.json()
                self.log_test("현재가 조회", "PASS", {"symbol": test_symbol, "price": price_data.get("current_price")})
            else:
                self.log_test("현재가 조회", "FAIL", {"status_code": response.status_code})
                return False
            
            # 2. 호가창 조회
            response = await self.client.get(f"{self.base_url}/market-data/stocks/{test_symbol}/orderbook")
            if response.status_code == 200:
                orderbook_data = response.json()
                self.log_test("호가창 조회", "PASS", {"symbol": test_symbol, "bid_count": len(orderbook_data.get("bids", []))})
            else:
                self.log_test("호가창 조회", "FAIL", {"status_code": response.status_code})
                return False
            
            # 3. 기술적 지표 조회
            response = await self.client.get(f"{self.base_url}/market-data/stocks/{test_symbol}/indicators")
            if response.status_code == 200:
                indicators_data = response.json()
                self.log_test("기술적 지표", "PASS", {"symbol": test_symbol, "indicators": list(indicators_data.keys())})
            else:
                self.log_test("기술적 지표", "FAIL", {"status_code": response.status_code})
                return False
            
            return True
            
        except Exception as e:
            self.log_test("시장 데이터 테스트", "FAIL", {"error": str(e)})
            return False
    
    async def test_trading_scenario_samsung(self) -> bool:
        """삼성전자 단타 매매 시나리오 테스트"""
        
        try:
            print("\n🚀 === 삼성전자 단타 매매 시나리오 ===")
            
            symbol = "005930"
            
            # 1. 자동매매 시작
            response = await self.client.post(f"{self.base_url}/trading/start")
            if response.status_code == 200:
                self.log_test("자동매매 시작", "PASS")
            else:
                self.log_test("자동매매 시작", "FAIL", {"status_code": response.status_code})
                return False
            
            # 2. 매매 신호 생성 대기 (시뮬레이션)
            print("   📡 매매 신호 생성 대기 중...")
            await asyncio.sleep(3)
            
            # 3. 매매 신호 조회
            response = await self.client.get(f"{self.base_url}/trading/signals?symbol={symbol}&limit=5")
            if response.status_code == 200:
                signals = response.json()
                self.log_test("매매 신호 조회", "PASS", {"signal_count": len(signals)})
                
                if signals:
                    latest_signal = signals[0]
                    self.log_test("최신 신호", "INFO", {
                        "type": latest_signal.get("signal_type"),
                        "strength": latest_signal.get("strength"),
                        "confidence": latest_signal.get("confidence")
                    })
            else:
                self.log_test("매매 신호 조회", "FAIL", {"status_code": response.status_code})
            
            # 4. 수동 매수 주문 테스트
            buy_order_data = {
                "symbol": symbol,
                "side": "buy",
                "order_type": "limit",
                "quantity": 10,
                "price": 75000
            }
            
            response = await self.client.post(f"{self.base_url}/trading/order", json=buy_order_data)
            if response.status_code == 200:
                order_result = response.json()
                order_id = order_result.get("order_id")
                self.log_test("매수 주문", "PASS", {"order_id": order_id, "symbol": symbol})
                self.order_history.append(order_result)
            else:
                self.log_test("매수 주문", "FAIL", {"status_code": response.status_code})
                return False
            
            # 5. 주문 상태 확인
            await asyncio.sleep(2)
            response = await self.client.get(f"{self.base_url}/trading/orders?symbol={symbol}")
            if response.status_code == 200:
                orders = response.json()
                self.log_test("주문 상태 확인", "PASS", {"order_count": len(orders)})
            else:
                self.log_test("주문 상태 확인", "FAIL", {"status_code": response.status_code})
            
            # 6. 포지션 확인
            response = await self.client.get(f"{self.base_url}/trading/positions")
            if response.status_code == 200:
                positions = response.json()
                self.log_test("포지션 확인", "PASS", {"position_count": len(positions)})
                self.current_positions = {pos["symbol"]: pos for pos in positions}
            else:
                self.log_test("포지션 확인", "FAIL", {"status_code": response.status_code})
            
            # 7. 매도 주문 테스트 (익절)
            if symbol in self.current_positions:
                position = self.current_positions[symbol]
                sell_price = int(position["avg_price"] * 1.02)  # 2% 익절
                
                sell_order_data = {
                    "symbol": symbol,
                    "side": "sell",
                    "order_type": "limit",
                    "quantity": position["quantity"],
                    "price": sell_price
                }
                
                response = await self.client.post(f"{self.base_url}/trading/order", json=sell_order_data)
                if response.status_code == 200:
                    order_result = response.json()
                    self.log_test("매도 주문 (익절)", "PASS", {"order_id": order_result.get("order_id")})
                else:
                    self.log_test("매도 주문 (익절)", "FAIL", {"status_code": response.status_code})
            
            return True
            
        except Exception as e:
            self.log_test("삼성전자 매매 시나리오", "FAIL", {"error": str(e)})
            return False
    
    async def test_risk_management(self) -> bool:
        """리스크 관리 시나리오 테스트"""
        
        try:
            print("\n⚠️ === 리스크 관리 테스트 ===")
            
            # 1. 최대 포지션 수 테스트
            symbols = ["005930", "000660", "035420", "051910"]  # 4개 종목
            
            for i, symbol in enumerate(symbols):
                order_data = {
                    "symbol": symbol,
                    "side": "buy",
                    "order_type": "market",
                    "quantity": 5
                }
                
                response = await self.client.post(f"{self.base_url}/trading/order", json=order_data)
                if i < 3:  # 최대 3개 포지션까지만 허용
                    if response.status_code == 200:
                        self.log_test(f"포지션 {i+1} 생성", "PASS", {"symbol": symbol})
                    else:
                        self.log_test(f"포지션 {i+1} 생성", "FAIL", {"symbol": symbol})
                else:  # 4번째는 거부되어야 함
                    if response.status_code == 400:
                        self.log_test("최대 포지션 수 제한", "PASS", {"rejected_symbol": symbol})
                    else:
                        self.log_test("최대 포지션 수 제한", "FAIL", {"symbol": symbol})
            
            # 2. 손절 시나리오 테스트
            response = await self.client.post(f"{self.base_url}/trading/test-stop-loss", json={"symbol": "005930", "loss_percent": -3.0})
            if response.status_code == 200:
                self.log_test("손절 시나리오", "PASS")
            else:
                self.log_test("손절 시나리오", "FAIL", {"status_code": response.status_code})
            
            # 3. 계좌 보호 테스트
            response = await self.client.get(f"{self.base_url}/system/risk-status")
            if response.status_code == 200:
                risk_data = response.json()
                self.log_test("리스크 상태", "PASS", risk_data)
            else:
                self.log_test("리스크 상태", "FAIL", {"status_code": response.status_code})
            
            return True
            
        except Exception as e:
            self.log_test("리스크 관리 테스트", "FAIL", {"error": str(e)})
            return False
    
    async def test_performance_analysis(self) -> bool:
        """성과 분석 테스트"""
        
        try:
            print("\n📈 === 성과 분석 테스트 ===")
            
            # 1. 일일 성과 조회
            response = await self.client.get(f"{self.base_url}/system/performance/daily")
            if response.status_code == 200:
                daily_perf = response.json()
                self.log_test("일일 성과", "PASS", daily_perf)
            else:
                self.log_test("일일 성과", "FAIL", {"status_code": response.status_code})
            
            # 2. 주간 성과 조회
            response = await self.client.get(f"{self.base_url}/system/performance/weekly")
            if response.status_code == 200:
                weekly_perf = response.json()
                self.log_test("주간 성과", "PASS", weekly_perf)
            else:
                self.log_test("주간 성과", "FAIL", {"status_code": response.status_code})
            
            # 3. 거래 히스토리 조회
            response = await self.client.get(f"{self.base_url}/trading/history?limit=10")
            if response.status_code == 200:
                history = response.json()
                self.log_test("거래 히스토리", "PASS", {"trade_count": len(history)})
            else:
                self.log_test("거래 히스토리", "FAIL", {"status_code": response.status_code})
            
            return True
            
        except Exception as e:
            self.log_test("성과 분석 테스트", "FAIL", {"error": str(e)})
            return False
    
    async def test_emergency_stop(self) -> bool:
        """긴급 정지 테스트"""
        
        try:
            print("\n🛑 === 긴급 정지 테스트 ===")
            
            # 1. 긴급 정지 실행
            response = await self.client.post(f"{self.base_url}/trading/emergency-stop")
            if response.status_code == 200:
                self.log_test("긴급 정지", "PASS")
            else:
                self.log_test("긴급 정지", "FAIL", {"status_code": response.status_code})
                return False
            
            # 2. 시스템 상태 확인
            await asyncio.sleep(2)
            response = await self.client.get(f"{self.base_url}/trading/status")
            if response.status_code == 200:
                status = response.json()
                if status.get("is_running") == False:
                    self.log_test("정지 상태 확인", "PASS")
                else:
                    self.log_test("정지 상태 확인", "FAIL", {"still_running": True})
            else:
                self.log_test("정지 상태 확인", "FAIL", {"status_code": response.status_code})
            
            return True
            
        except Exception as e:
            self.log_test("긴급 정지 테스트", "FAIL", {"error": str(e)})
            return False
    
    def print_test_summary(self):
        """테스트 결과 요약 출력"""
        
        print("\n" + "="*60)
        print("🎯 테스트 결과 요약")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        
        print(f"총 테스트: {total_tests}")
        print(f"성공: {passed_tests} ✅")
        print(f"실패: {failed_tests} ❌")
        print(f"성공률: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 실패한 테스트:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"   - {result['test_name']}: {result.get('details', {})}")
        
        print("\n📊 주요 지표:")
        if self.current_positions:
            print(f"   현재 포지션: {len(self.current_positions)}개")
        if self.order_history:
            print(f"   주문 내역: {len(self.order_history)}건")
        
        # 테스트 결과를 JSON 파일로 저장
        with open("test_results.json", "w", encoding="utf-8") as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": passed_tests/total_tests*100
                },
                "results": self.test_results,
                "positions": self.current_positions,
                "orders": self.order_history
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 상세 결과가 test_results.json에 저장되었습니다.")

async def run_all_scenarios():
    """모든 테스트 시나리오 실행"""
    
    print("🚀 자동매매 시스템 시나리오 테스트 시작")
    print("="*60)
    
    async with TradingSystemTester() as tester:
        
        # 1. 시스템 헬스체크
        if not await tester.test_system_health():
            print("❌ 시스템 헬스체크 실패. 테스트를 중단합니다.")
            return
        
        # 2. 시장 데이터 테스트
        await tester.test_market_data()
        
        # 3. 매매 시나리오 테스트
        await tester.test_trading_scenario_samsung()
        
        # 4. 리스크 관리 테스트
        await tester.test_risk_management()
        
        # 5. 성과 분석 테스트
        await tester.test_performance_analysis()
        
        # 6. 긴급 정지 테스트
        await tester.test_emergency_stop()
        
        # 결과 요약
        tester.print_test_summary()

if __name__ == "__main__":
    # 테스트 실행
    asyncio.run(run_all_scenarios())
