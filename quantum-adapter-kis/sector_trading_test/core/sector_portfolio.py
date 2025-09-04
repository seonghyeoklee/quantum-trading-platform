"""
섹터별 포트폴리오 관리 시스템
2025년 유망섹터 기반 분산투자 포트폴리오 관리
"""

import sys
import yaml
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

# KIS API 모듈 경로 추가
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir.parent / 'examples_llm'))
import kis_auth as ka

# 설정 파일 로드
config_dir = current_dir / 'config'

class SectorPortfolio:
    """섹터별 포트폴리오 관리 클래스"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        초기화
        
        Args:
            config_path: 설정 파일 경로 (기본값: config 폴더)
        """
        self.logger = logging.getLogger(__name__)
        
        # 설정 로드
        if config_path:
            self.config_dir = Path(config_path)
        else:
            self.config_dir = config_dir
            
        self.sectors_config = self._load_config('sectors_2025.yaml')
        self.strategy_config = self._load_config('strategy_config.yaml')
        self.risk_config = self._load_config('risk_management.yaml')
        
        # 포트폴리오 상태 초기화
        self.positions = {}  # 현재 보유 포지션
        self.cash_balance = self.strategy_config['position_management']['initial_investment']
        self.total_value = self.cash_balance
        self.sector_weights = {}
        
        # 성과 추적
        self.performance_history = []
        self.trade_history = []
        
        self.logger.info("섹터 포트폴리오 매니저 초기화 완료")
    
    def _load_config(self, filename: str) -> dict:
        """설정 파일 로드"""
        config_path = self.config_dir / filename
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"설정 파일 로드 실패 {filename}: {e}")
            return {}
    
    def get_sector_info(self) -> Dict[str, Dict]:
        """섹터 정보 반환"""
        return self.sectors_config['sectors']
    
    def get_target_allocation(self) -> Dict[str, float]:
        """목표 섹터별 비중 반환"""
        sectors = self.sectors_config['sectors']
        total_weight = sum(sector['target_weight'] for sector in sectors.values())
        
        return {
            sector_name: sector_data['target_weight'] / total_weight * 100
            for sector_name, sector_data in sectors.items()
        }
    
    def calculate_current_allocation(self) -> Dict[str, float]:
        """현재 섹터별 비중 계산"""
        if not self.positions:
            return {sector: 0.0 for sector in self.get_sector_info().keys()}
        
        total_value = self.get_total_portfolio_value()
        current_allocation = {}
        
        for sector_name, sector_data in self.get_sector_info().items():
            sector_value = 0.0
            
            # 주요 종목 가치 계산
            for stock_type in ['primary', 'secondary']:
                if stock_type in sector_data['stocks']:
                    symbol = sector_data['stocks'][stock_type]['symbol']
                    if symbol in self.positions:
                        sector_value += self.positions[symbol].get('market_value', 0.0)
            
            current_allocation[sector_name] = (sector_value / total_value * 100) if total_value > 0 else 0.0
        
        return current_allocation
    
    def get_rebalancing_signals(self) -> Dict[str, Dict]:
        """리밸런싱 신호 계산"""
        target_allocation = self.get_target_allocation()
        current_allocation = self.calculate_current_allocation()
        threshold = self.strategy_config['position_management']['rebalancing_threshold']
        
        signals = {}
        
        for sector_name in target_allocation:
            target = target_allocation[sector_name]
            current = current_allocation[sector_name]
            difference = current - target
            
            if abs(difference) > threshold:
                action = "REDUCE" if difference > 0 else "INCREASE"
                signals[sector_name] = {
                    'action': action,
                    'target_weight': target,
                    'current_weight': current,
                    'difference': difference,
                    'priority': abs(difference)
                }
        
        # 우선순위 정렬
        if signals:
            signals = dict(sorted(signals.items(), key=lambda x: x[1]['priority'], reverse=True))
        
        return signals
    
    def get_sector_stocks(self, sector_name: str) -> List[Dict]:
        """특정 섹터의 종목 리스트 반환"""
        if sector_name not in self.sectors_config['sectors']:
            return []
        
        sector_data = self.sectors_config['sectors'][sector_name]
        stocks = []
        
        for stock_type, stock_info in sector_data['stocks'].items():
            stocks.append({
                'type': stock_type,
                'symbol': stock_info['symbol'],
                'name': stock_info['name'],
                'reason': stock_info['reason'],
                'market_cap': stock_info['market_cap']
            })
        
        return stocks
    
    def update_position(self, symbol: str, shares: int, price: float, action: str):
        """포지션 업데이트"""
        if symbol not in self.positions:
            self.positions[symbol] = {
                'shares': 0,
                'avg_price': 0.0,
                'total_cost': 0.0,
                'market_value': 0.0,
                'unrealized_pnl': 0.0,
                'last_update': datetime.now()
            }
        
        position = self.positions[symbol]
        
        if action.upper() == 'BUY':
            # 매수 처리
            total_shares = position['shares'] + shares
            total_cost = position['total_cost'] + (shares * price)
            
            position['shares'] = total_shares
            position['avg_price'] = total_cost / total_shares if total_shares > 0 else 0.0
            position['total_cost'] = total_cost
            
            # 현금 차감
            self.cash_balance -= shares * price
            
        elif action.upper() == 'SELL':
            # 매도 처리
            if position['shares'] >= shares:
                position['shares'] -= shares
                realized_pnl = shares * (price - position['avg_price'])
                
                # 현금 증가
                self.cash_balance += shares * price
                
                # 전량 매도시 포지션 제거
                if position['shares'] == 0:
                    del self.positions[symbol]
                    return realized_pnl
            else:
                self.logger.warning(f"매도 수량 초과: {symbol}, 보유: {position['shares']}, 매도: {shares}")
                return 0.0
        
        # 시장가치 업데이트
        position['market_value'] = position['shares'] * price
        position['unrealized_pnl'] = position['market_value'] - position['total_cost']
        position['last_update'] = datetime.now()
        
        return 0.0  # 매수의 경우 realized_pnl = 0
    
    def get_total_portfolio_value(self) -> float:
        """전체 포트폴리오 가치 계산"""
        portfolio_value = self.cash_balance
        
        for position in self.positions.values():
            portfolio_value += position['market_value']
        
        return portfolio_value
    
    def get_portfolio_summary(self) -> Dict:
        """포트폴리오 요약 정보"""
        total_value = self.get_total_portfolio_value()
        initial_investment = self.strategy_config['position_management']['initial_investment']
        
        total_return = ((total_value - initial_investment) / initial_investment * 100) if initial_investment > 0 else 0.0
        
        return {
            'total_value': total_value,
            'cash_balance': self.cash_balance,
            'invested_amount': total_value - self.cash_balance,
            'cash_ratio': (self.cash_balance / total_value * 100) if total_value > 0 else 100.0,
            'total_return_pct': total_return,
            'total_return_amount': total_value - initial_investment,
            'position_count': len(self.positions),
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_sector_performance(self) -> Dict[str, Dict]:
        """섹터별 성과 분석"""
        sector_performance = {}
        
        for sector_name, sector_data in self.get_sector_info().items():
            sector_value = 0.0
            sector_cost = 0.0
            sector_pnl = 0.0
            position_count = 0
            
            for stock_type in ['primary', 'secondary']:
                if stock_type in sector_data['stocks']:
                    symbol = sector_data['stocks'][stock_type]['symbol']
                    if symbol in self.positions:
                        position = self.positions[symbol]
                        sector_value += position['market_value']
                        sector_cost += position['total_cost']
                        sector_pnl += position['unrealized_pnl']
                        position_count += 1
            
            sector_return = ((sector_value - sector_cost) / sector_cost * 100) if sector_cost > 0 else 0.0
            
            sector_performance[sector_name] = {
                'market_value': sector_value,
                'total_cost': sector_cost,
                'unrealized_pnl': sector_pnl,
                'return_pct': sector_return,
                'position_count': position_count,
                'theme': sector_data['theme']
            }
        
        return sector_performance
    
    def check_risk_limits(self) -> List[Dict]:
        """리스크 한도 체크"""
        warnings = []
        total_value = self.get_total_portfolio_value()
        
        # 포트폴리오 레벨 체크
        portfolio_config = self.risk_config['portfolio_risk']
        current_allocation = self.calculate_current_allocation()
        
        # 섹터 집중도 체크
        max_sector_concentration = portfolio_config['max_sector_concentration']
        for sector_name, weight in current_allocation.items():
            if weight > max_sector_concentration:
                warnings.append({
                    'type': 'SECTOR_CONCENTRATION',
                    'sector': sector_name,
                    'current': weight,
                    'limit': max_sector_concentration,
                    'severity': 'HIGH'
                })
        
        # 종목 집중도 체크
        max_stock_concentration = portfolio_config['max_stock_concentration']
        for symbol, position in self.positions.items():
            stock_weight = (position['market_value'] / total_value * 100) if total_value > 0 else 0.0
            if stock_weight > max_stock_concentration:
                warnings.append({
                    'type': 'STOCK_CONCENTRATION',
                    'symbol': symbol,
                    'current': stock_weight,
                    'limit': max_stock_concentration,
                    'severity': 'HIGH'
                })
        
        return warnings
    
    def save_state(self, filepath: Optional[str] = None):
        """포트폴리오 상태 저장"""
        if not filepath:
            filepath = self.config_dir.parent / 'logs' / f'portfolio_state_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        state = {
            'timestamp': datetime.now().isoformat(),
            'positions': self.positions,
            'cash_balance': self.cash_balance,
            'total_value': self.get_total_portfolio_value(),
            'portfolio_summary': self.get_portfolio_summary(),
            'sector_performance': self.get_sector_performance(),
            'current_allocation': self.calculate_current_allocation(),
            'risk_warnings': self.check_risk_limits()
        }
        
        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2, default=str)
        
        self.logger.info(f"포트폴리오 상태 저장: {filepath}")
    
    def load_state(self, filepath: str):
        """포트폴리오 상태 로드"""
        import json
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            self.positions = state.get('positions', {})
            self.cash_balance = state.get('cash_balance', self.strategy_config['position_management']['initial_investment'])
            
            # datetime 객체 복원
            for position in self.positions.values():
                if 'last_update' in position:
                    position['last_update'] = datetime.fromisoformat(position['last_update'])
            
            self.logger.info(f"포트폴리오 상태 로드: {filepath}")
            
        except Exception as e:
            self.logger.error(f"포트폴리오 상태 로드 실패: {e}")


# 테스트 및 디버깅용 함수
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 포트폴리오 매니저 테스트
    portfolio = SectorPortfolio()
    
    print("=== 2025년 유망섹터 포트폴리오 ===")
    print("\n📊 섹터 정보:")
    for sector_name, sector_data in portfolio.get_sector_info().items():
        print(f"\n{sector_name}: {sector_data['sector_name']}")
        print(f"  테마: {sector_data['theme']}")
        print(f"  목표 비중: {sector_data['target_weight']:.1f}%")
        
        for stock_type, stock_info in sector_data['stocks'].items():
            print(f"  {stock_type}: {stock_info['name']}({stock_info['symbol']})")
    
    print(f"\n💰 초기 투자금액: {portfolio.cash_balance:,}원")
    print(f"📈 목표 배분: {portfolio.get_target_allocation()}")