"""
골든크로스 백테스팅 시스템 (Backtrader 기반)
종목별 최적 확정 기간 분석을 위한 전문 백테스팅
"""

import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class GoldenCrossStrategy(bt.Strategy):
    """골든크로스 전략 (확정 기간 적용)"""
    
    params = (
        ('fast_period', 5),           # SMA5
        ('slow_period', 20),          # SMA20  
        ('confirmation_days', 1),     # 확정 기간
        ('commission', 0.00015),      # 수수료 0.015%
    )
    
    def log(self, txt, dt=None):
        """로깅 함수"""
        dt = dt or self.datas[0].datetime.date(0)
        logger.info(f'{dt.isoformat()}: {txt}')
    
    def __init__(self):
        """전략 초기화"""
        self.dataclose = self.datas[0].close
        
        # 이동평균선 계산
        self.sma_fast = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.fast_period)
        self.sma_slow = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.slow_period)
        
        # 크로스오버 지표 (즉시 감지용)
        self.crossover = bt.indicators.CrossOver(self.sma_fast, self.sma_slow)
        
        # 확정 기간 추적 변수
        self.golden_cross_days = 0    # 골든크로스 연속 일수
        self.dead_cross_days = 0      # 데드크로스 연속 일수
        
        # 주문 추적
        self.order = None
        
    def notify_order(self, order):
        """주문 상태 알림"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'📈 매수 체결: 가격={order.executed.price:.0f}, '
                        f'수량={order.executed.size}, 수수료={order.executed.comm:.0f}')
            else:
                self.log(f'📉 매도 체결: 가격={order.executed.price:.0f}, '
                        f'수량={order.executed.size}, 수수료={order.executed.comm:.0f}')
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'❌ 주문 실패: {order.status}')
        
        self.order = None
    
    def notify_trade(self, trade):
        """거래 완료 알림"""
        if not trade.isclosed:
            return
        
        self.log(f'💰 거래 완료: 손익={trade.pnl:.0f}원, 수익률={trade.pnl/trade.price*100:.2f}%')
    
    def next(self):
        """매일 실행되는 전략 로직"""
        # 현재 상태 확인
        current_fast = self.sma_fast[0]
        current_slow = self.sma_slow[0]
        
        # 골든크로스 상태 (SMA5 > SMA20) 연속 일수 계산
        if current_fast > current_slow:
            self.golden_cross_days += 1
            self.dead_cross_days = 0
        # 데드크로스 상태 (SMA5 < SMA20) 연속 일수 계산  
        elif current_fast < current_slow:
            self.dead_cross_days += 1
            self.golden_cross_days = 0
        else:
            # 같은 경우는 연속 일수 유지
            pass
        
        # 진행 중인 주문이 있으면 대기
        if self.order:
            return
        
        # 매수 조건: 골든크로스 상태가 확정 기간만큼 지속
        if (self.golden_cross_days >= self.params.confirmation_days and 
            not self.position):
            
            self.log(f'🎯 매수 신호: 골든크로스 {self.golden_cross_days}일 확정 '
                    f'(SMA5: {current_fast:.0f}, SMA20: {current_slow:.0f})')
            
            # 전체 현금으로 매수
            self.order = self.buy()
            
        # 매도 조건: 데드크로스 상태가 확정 기간만큼 지속
        elif (self.dead_cross_days >= self.params.confirmation_days and 
              self.position):
            
            self.log(f'🎯 매도 신호: 데드크로스 {self.dead_cross_days}일 확정 '
                    f'(SMA5: {current_fast:.0f}, SMA20: {current_slow:.0f})')
            
            # 보유 주식 전량 매도
            self.order = self.sell()

class GoldenCrossBacktester:
    """골든크로스 백테스터 (Backtrader 기반)"""
    
    def __init__(self, initial_cash: float = 10_000_000, commission: float = 0.00015):
        self.initial_cash = initial_cash
        self.commission = commission
        
    def prepare_data(self, df: pd.DataFrame, symbol: str) -> bt.feeds.PandasData:
        """
        pandas DataFrame을 Backtrader 데이터 형식으로 변환
        
        Args:
            df: OHLCV 데이터 (index: datetime)
            symbol: 종목 코드
            
        Returns:
            Backtrader 데이터 피드
        """
        # 필수 컬럼 확인
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"필수 컬럼이 없습니다: {required_cols}")
        
        # Backtrader 데이터 형식으로 변환
        data = bt.feeds.PandasData(
            dataname=df,
            datetime=None,  # 인덱스 사용
            open='open',
            high='high', 
            low='low',
            close='close',
            volume='volume',
            openinterest=None,
            name=symbol
        )
        
        return data
        
    def run_single_test(self, 
                       data: bt.feeds.PandasData,
                       symbol: str,
                       symbol_name: str,
                       confirmation_days: int = 1) -> Dict:
        """
        단일 종목, 특정 확정 기간으로 백테스팅 실행
        
        Args:
            data: Backtrader 데이터 피드
            symbol: 종목 코드
            symbol_name: 종목명
            confirmation_days: 확정 기간
            
        Returns:
            백테스팅 결과 딕셔너리
        """
        logger.info(f"🔍 백테스트: {symbol_name}({symbol}) - {confirmation_days}일 확정")
        
        # Cerebro 엔진 초기화
        cerebro = bt.Cerebro()
        
        # 전략 추가
        cerebro.addstrategy(
            GoldenCrossStrategy,
            confirmation_days=confirmation_days,
            commission=self.commission
        )
        
        # 데이터 추가
        cerebro.adddata(data)
        
        # 초기 자금 설정
        cerebro.broker.setcash(self.initial_cash)
        
        # 수수료 설정
        cerebro.broker.setcommission(commission=self.commission)
        
        # 백테스팅 실행
        start_value = cerebro.broker.getvalue()
        result = cerebro.run()
        final_value = cerebro.broker.getvalue()
        
        # 결과 계산
        total_return = (final_value - start_value) / start_value * 100
        
        # 거래 내역 가져오기
        strategy = result[0]
        
        # 성과 지표 계산
        analyzers_results = {}
        
        result_dict = {
            'symbol': symbol,
            'symbol_name': symbol_name,
            'confirmation_days': confirmation_days,
            'initial_value': start_value,
            'final_value': final_value,
            'total_return': total_return,
            'analyzers': analyzers_results
        }
        
        logger.info(f"✅ 결과: {total_return:+.2f}% "
                   f"({start_value:,.0f}원 → {final_value:,.0f}원)")
        
        return result_dict
    
    def compare_confirmation_periods(self, 
                                   df: pd.DataFrame,
                                   symbol: str, 
                                   symbol_name: str,
                                   periods: List[int] = [1, 2, 3, 5, 7]) -> Dict:
        """
        여러 확정 기간 비교 백테스팅
        
        Args:
            df: OHLCV 데이터
            symbol: 종목 코드
            symbol_name: 종목명
            periods: 테스트할 확정 기간 리스트
            
        Returns:
            확정 기간별 결과 딕셔너리
        """
        logger.info(f"🔄 다중 기간 백테스트: {symbol_name}({symbol})")
        
        # 데이터 준비
        data = self.prepare_data(df, symbol)
        
        results = {}
        
        for period in periods:
            try:
                # 매번 새로운 데이터 생성 (Backtrader 요구사항)
                data_copy = self.prepare_data(df.copy(), symbol)
                result = self.run_single_test(data_copy, symbol, symbol_name, period)
                results[period] = result
                
            except Exception as e:
                logger.error(f"❌ {period}일 백테스트 실패: {e}")
                continue
        
        return results
    
    def print_comparison_table(self, results: Dict):
        """비교 결과 테이블 출력"""
        if not results:
            print("❌ 백테스팅 결과가 없습니다.")
            return
            
        # 첫 번째 결과에서 종목 정보 가져오기
        first_result = list(results.values())[0]
        symbol_name = first_result['symbol_name']
        symbol = first_result['symbol']
        
        print(f"\n📊 {symbol_name}({symbol}) 확정 기간별 비교 결과 (전문 백테스터)")
        print("="*80)
        print(f"{'확정기간':<8} {'총수익률':<12} {'시작자금':<12} {'최종자금':<12}")
        print("-"*80)
        
        for period in sorted(results.keys()):
            result = results[period]
            print(f"{period}일{'':<5} {result['total_return']:+9.2f}%   "
                  f"{result['initial_value']:>10,.0f}원   "
                  f"{result['final_value']:>10,.0f}원")
        
        # 최적 결과 표시
        best_period = max(results.keys(), key=lambda k: results[k]['total_return'])
        best_result = results[best_period]
        
        print("-"*80)
        print(f"🏆 최적: {best_period}일 확정 "
              f"(수익률: {best_result['total_return']:+.2f}%)")

def convert_kis_data(output2_data) -> pd.DataFrame:
    """
    KIS API output2 데이터를 Backtrader 형식으로 변환
    
    Args:
        output2_data: KIS API inquire_daily_itemchartprice의 output2
        
    Returns:
        Backtrader용 OHLCV DataFrame
    """
    df = pd.DataFrame()
    df['date'] = pd.to_datetime(output2_data['stck_bsop_date'])
    df['close'] = pd.to_numeric(output2_data['stck_clpr'])
    df['open'] = pd.to_numeric(output2_data['stck_oprc'])
    df['high'] = pd.to_numeric(output2_data['stck_hgpr'])
    df['low'] = pd.to_numeric(output2_data['stck_lwpr'])
    df['volume'] = pd.to_numeric(output2_data['acml_vol'])
    
    # 날짜를 인덱스로 설정하고 정렬
    df.set_index('date', inplace=True)
    df.sort_index(inplace=True)
    
    return df