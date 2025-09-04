#!/usr/bin/env python3
"""
간단한 테스트 실행 - pandas 없이 동작
"""

import sys
import asyncio
import logging
from datetime import datetime
import json
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

class SimpleSignalTest:
    """간단한 신호 테스트"""
    
    def __init__(self):
        self.symbols = {
            "005930": "삼성전자",
            "000660": "SK하이닉스"
        }
        
    async def simulate_monitoring(self):
        """모니터링 시뮬레이션"""
        logger.info("="*60)
        logger.info("📊 Quantum Trading Strategy - Signal Test")
        logger.info("="*60)
        logger.info(f"모니터링 종목: {list(self.symbols.values())}")
        logger.info(f"모드: 시뮬레이션 (실제 매매 없음)")
        logger.info("="*60)
        
        # 3번 신호 시뮬레이션
        for i in range(3):
            await self.simulate_signal_detection()
            await asyncio.sleep(2)  # 2초 대기
        
        logger.info("🏁 테스트 완료!")
    
    async def simulate_signal_detection(self):
        """신호 감지 시뮬레이션"""
        symbol = "005930"
        name = "삼성전자"
        price = 71000 + (hash(str(datetime.now())) % 1000)  # 랜덤 가격
        
        logger.info("")
        logger.info(f"🎯 신호 감지: {name}({symbol})")
        logger.info("─"*50)
        logger.info(f"📊 시장 데이터")
        logger.info(f"  현재가: {price:,}원")
        logger.info(f"  거래량: 1.45x (평균 대비)")
        logger.info("")
        logger.info(f"📈 기술적 지표")
        logger.info(f"  SMA(5):  {price-500:,}원")
        logger.info(f"  SMA(20): {price-800:,}원")
        logger.info(f"  스프레드: 1.2%")
        logger.info(f"  RSI(14): 55.0")
        logger.info("")
        logger.info(f"🎯 신호 정보")
        logger.info(f"  타입: 📈 GOLDEN_CROSS")
        logger.info(f"  확신도: CONFIRMED")
        logger.info(f"  확인일수: 3/3일")
        logger.info(f"  신호강도: 85/100 💪")
        logger.info("")
        
        # 매수 주문 시뮬레이션
        await self.simulate_buy_order(symbol, name, price)
    
    async def simulate_buy_order(self, symbol: str, name: str, price: float):
        """매수 주문 시뮬레이션"""
        investment = 10000000  # 1000만원
        quantity = int(investment * 0.98 / price)
        commission = int(quantity * price * 0.00015)
        total_cost = quantity * price + commission
        
        logger.info("💰 매수 주문 시뮬레이션")
        logger.info("┌─────────────────────────────────────┐")
        logger.info("│     💰 매수 주문 시뮬레이션         │")
        logger.info("├─────────────────────────────────────┤")
        logger.info(f"│ 종목: {name:>20} │")
        logger.info(f"│ 코드: {symbol:>20} │")
        logger.info(f"│ 매수가: {price:>17,.0f}원 │")
        logger.info(f"│ 수량: {quantity:>19,}주 │")
        logger.info("├─────────────────────────────────────┤")
        logger.info(f"│ 매수금액: {quantity * price:>15,.0f}원 │")
        logger.info(f"│ 수수료: {commission:>17,.0f}원 │")
        logger.info(f"│ 총 비용: {total_cost:>16,.0f}원 │")
        logger.info("├─────────────────────────────────────┤")
        logger.info("│ 🚫 실제 주문: 실행되지 않음        │")
        logger.info("│ 📝 시뮬레이션 기록만 저장됨        │")
        logger.info("└─────────────────────────────────────┘")
        
        # 로그 저장
        self.save_log({
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'name': name,
            'price': price,
            'quantity': quantity,
            'total_cost': total_cost,
            'simulation': True
        })
    
    def save_log(self, data: dict):
        """로그 저장"""
        log_dir = Path("logs/orders")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = log_dir / f"{today}_test.json"
        
        logs = []
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            except:
                logs = []
        
        logs.append(data)
        
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)

async def main():
    """메인 실행"""
    print("""
╔════════════════════════════════════════════════╗
║                                                ║
║    📊 Quantum Trading Strategy Test 📊         ║
║                                                ║
║         Signal Detection Simulation            ║
║              (No Real Trading)                 ║
║                                                ║
╚════════════════════════════════════════════════╝
    """)
    
    test = SimpleSignalTest()
    await test.simulate_monitoring()

if __name__ == "__main__":
    asyncio.run(main())