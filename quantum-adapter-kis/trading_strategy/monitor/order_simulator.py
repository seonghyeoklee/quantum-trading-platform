"""
주문 시뮬레이터
실제 매매 없이 주문 플로우만 시뮬레이션하고 상세 로깅
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class OrderSimulator:
    """주문 시뮬레이션 (실제 주문 없음)"""
    
    def __init__(self, commission_rate: float = 0.00015, tax_rate: float = 0.0023):
        """
        Args:
            commission_rate: 수수료율 (기본 0.015%)
            tax_rate: 거래세율 (기본 0.23%, 매도시만)
        """
        self.commission_rate = commission_rate
        self.tax_rate = tax_rate
        self.order_history = []
    
    def simulate_buy_order(self, 
                          symbol: str,
                          symbol_name: str,
                          price: float,
                          investment_amount: float) -> Dict[str, Any]:
        """
        매수 주문 시뮬레이션
        
        Args:
            symbol: 종목 코드
            symbol_name: 종목명
            price: 현재가
            investment_amount: 투자 금액
        
        Returns:
            주문 시뮬레이션 결과
        """
        # 매수 가능 수량 계산 (수수료 고려)
        available_amount = investment_amount * 0.98  # 98% 사용
        quantity = int(available_amount / price)
        
        if quantity == 0:
            logger.warning(f"매수 가능 수량이 0입니다. 투자금액: {investment_amount}, 가격: {price}")
            return {}
        
        # 실제 매수 금액
        order_amount = quantity * price
        commission = order_amount * self.commission_rate
        total_cost = order_amount + commission
        
        order = {
            'type': 'BUY',
            'symbol': symbol,
            'symbol_name': symbol_name,
            'price': price,
            'quantity': quantity,
            'order_amount': order_amount,
            'commission': commission,
            'tax': 0,  # 매수시 세금 없음
            'total_cost': total_cost,
            'timestamp': datetime.now().isoformat()
        }
        
        self.order_history.append(order)
        
        self._log_buy_simulation(order)
        
        return order
    
    def simulate_sell_order(self,
                          symbol: str,
                          symbol_name: str,
                          price: float,
                          quantity: int,
                          avg_buy_price: float) -> Dict[str, Any]:
        """
        매도 주문 시뮬레이션
        
        Args:
            symbol: 종목 코드
            symbol_name: 종목명  
            price: 현재가
            quantity: 매도 수량
            avg_buy_price: 평균 매수가
        
        Returns:
            주문 시뮬레이션 결과
        """
        # 매도 금액
        order_amount = quantity * price
        commission = order_amount * self.commission_rate
        tax = order_amount * self.tax_rate
        net_revenue = order_amount - commission - tax
        
        # 수익 계산
        buy_cost = quantity * avg_buy_price
        profit = net_revenue - buy_cost
        profit_rate = (profit / buy_cost) * 100
        
        order = {
            'type': 'SELL',
            'symbol': symbol,
            'symbol_name': symbol_name,
            'price': price,
            'quantity': quantity,
            'order_amount': order_amount,
            'commission': commission,
            'tax': tax,
            'net_revenue': net_revenue,
            'avg_buy_price': avg_buy_price,
            'profit': profit,
            'profit_rate': profit_rate,
            'timestamp': datetime.now().isoformat()
        }
        
        self.order_history.append(order)
        
        self._log_sell_simulation(order)
        
        return order
    
    def _log_buy_simulation(self, order: Dict[str, Any]):
        """매수 시뮬레이션 상세 로깅"""
        logger.info("")
        logger.info("┌─────────────────────────────────────┐")
        logger.info("│     💰 매수 주문 시뮬레이션         │")
        logger.info("├─────────────────────────────────────┤")
        logger.info(f"│ 종목: {order['symbol_name']:>20} │")
        logger.info(f"│ 코드: {order['symbol']:>20} │")
        logger.info(f"│ 매수가: {order['price']:>17,}원 │")
        logger.info(f"│ 수량: {order['quantity']:>19,}주 │")
        logger.info("├─────────────────────────────────────┤")
        logger.info(f"│ 매수금액: {order['order_amount']:>15,}원 │")
        logger.info(f"│ 수수료: {order['commission']:>17,.0f}원 │")
        logger.info(f"│ 총 비용: {order['total_cost']:>16,}원 │")
        logger.info("├─────────────────────────────────────┤")
        logger.info("│ 🚫 실제 주문: 실행되지 않음        │")
        logger.info("│ 📝 시뮬레이션 기록만 저장됨        │")
        logger.info("└─────────────────────────────────────┘")
    
    def _log_sell_simulation(self, order: Dict[str, Any]):
        """매도 시뮬레이션 상세 로깅"""
        profit_emoji = "📈" if order['profit'] > 0 else "📉"
        profit_color = "🟢" if order['profit'] > 0 else "🔴"
        
        logger.info("")
        logger.info("┌─────────────────────────────────────┐")
        logger.info("│     💸 매도 주문 시뮬레이션         │")
        logger.info("├─────────────────────────────────────┤")
        logger.info(f"│ 종목: {order['symbol_name']:>20} │")
        logger.info(f"│ 코드: {order['symbol']:>20} │")
        logger.info(f"│ 매도가: {order['price']:>17,}원 │")
        logger.info(f"│ 수량: {order['quantity']:>19,}주 │")
        logger.info("├─────────────────────────────────────┤")
        logger.info(f"│ 매도금액: {order['order_amount']:>15,}원 │")
        logger.info(f"│ 수수료: {order['commission']:>17,.0f}원 │")
        logger.info(f"│ 세금: {order['tax']:>19,.0f}원 │")
        logger.info(f"│ 순수익: {order['net_revenue']:>17,}원 │")
        logger.info("├─────────────────────────────────────┤")
        logger.info(f"│ 평균매수가: {order['avg_buy_price']:>13,}원 │")
        logger.info(f"│ {profit_emoji} 손익: {profit_color} {order['profit']:>15,}원 │")
        logger.info(f"│ {profit_emoji} 수익률: {profit_color} {order['profit_rate']:>13.2f}% │")
        logger.info("├─────────────────────────────────────┤")
        logger.info("│ 🚫 실제 주문: 실행되지 않음        │")
        logger.info("│ 📝 시뮬레이션 기록만 저장됨        │")
        logger.info("└─────────────────────────────────────┘")
    
    def log_order_decision_process(self, 
                                  signal_type: str,
                                  symbol: str,
                                  conditions: Dict[str, bool]):
        """
        주문 결정 과정 로깅
        
        Args:
            signal_type: 신호 타입 (BUY/SELL)
            symbol: 종목 코드
            conditions: 조건 체크 결과
        """
        logger.info("")
        logger.info(f"🎯 === 매{'수' if signal_type == 'BUY' else '도'} 결정 프로세스 ===")
        
        all_conditions_met = all(conditions.values())
        
        for condition, met in conditions.items():
            status = "✅" if met else "❌"
            logger.info(f"  {status} {condition}")
        
        logger.info("")
        if all_conditions_met:
            logger.info(f"  ✅ 모든 조건 충족 → 매{'수' if signal_type == 'BUY' else '도'} 결정")
        else:
            logger.info(f"  ❌ 조건 미충족 → 매{'수' if signal_type == 'BUY' else '도'} 보류")
        
        return all_conditions_met
    
    def get_order_summary(self) -> Dict[str, Any]:
        """주문 시뮬레이션 요약"""
        if not self.order_history:
            return {
                'total_orders': 0,
                'buy_orders': 0,
                'sell_orders': 0,
                'total_profit': 0,
                'win_rate': 0
            }
        
        buy_orders = [o for o in self.order_history if o['type'] == 'BUY']
        sell_orders = [o for o in self.order_history if o['type'] == 'SELL']
        
        total_profit = sum(o.get('profit', 0) for o in sell_orders)
        winning_trades = [o for o in sell_orders if o.get('profit', 0) > 0]
        
        return {
            'total_orders': len(self.order_history),
            'buy_orders': len(buy_orders),
            'sell_orders': len(sell_orders),
            'total_profit': total_profit,
            'win_rate': len(winning_trades) / len(sell_orders) * 100 if sell_orders else 0,
            'winning_trades': len(winning_trades),
            'losing_trades': len(sell_orders) - len(winning_trades)
        }
    
    def print_summary(self):
        """시뮬레이션 요약 출력"""
        summary = self.get_order_summary()
        
        logger.info("")
        logger.info("="*60)
        logger.info("📊 주문 시뮬레이션 요약")
        logger.info("="*60)
        logger.info(f"총 주문 횟수: {summary['total_orders']}회")
        logger.info(f"  - 매수: {summary['buy_orders']}회")
        logger.info(f"  - 매도: {summary['sell_orders']}회")
        
        if summary['sell_orders'] > 0:
            logger.info(f"총 손익: {summary['total_profit']:,.0f}원")
            logger.info(f"승률: {summary['win_rate']:.1f}%")
            logger.info(f"  - 수익 거래: {summary['winning_trades']}회")
            logger.info(f"  - 손실 거래: {summary['losing_trades']}회")
        logger.info("="*60)