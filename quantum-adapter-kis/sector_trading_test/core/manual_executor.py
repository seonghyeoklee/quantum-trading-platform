"""
수동 매매 실행기
사용자 승인 후 실제 매매를 실행하는 시스템
"""

import sys
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd

# KIS API 모듈 경로 추가
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir.parent / 'examples_llm'))
import kis_auth as ka

# 국내 주식 API 함수들
from domestic_stock.order_cash.order_cash import order_cash
from domestic_stock.inquire_price.inquire_price import inquire_price
from domestic_stock.inquire_balance.inquire_balance import inquire_balance

# 로컬 모듈
from .sector_portfolio import SectorPortfolio
from .trade_logger import TradeLogger, TradeSignal, TradeExecution

class ManualTradeExecutor:
    """수동 매매 실행기"""
    
    def __init__(self, portfolio: SectorPortfolio, logger: TradeLogger):
        """
        초기화
        
        Args:
            portfolio: 섹터 포트폴리오 관리자
            logger: 거래 로거
        """
        self.portfolio = portfolio
        self.trade_logger = logger
        self.logger = logging.getLogger(__name__)
        
        # KIS API 설정
        self.is_authenticated = False
        
        self.logger.info("수동 매매 실행기 초기화 완료")
    
    def authenticate_kis(self, environment: str = "vps"):
        """
        KIS API 인증
        
        Args:
            environment: 환경 (vps: 모의투자, prod: 실전투자)
        """
        try:
            # 모의투자는 vps, 실전투자는 prod
            ka.auth(svr=environment, product="01")
            self.trenv = ka.getTREnv()
            self.is_authenticated = True
            self.environment = environment
            
            env_name = "모의투자" if environment == "vps" else "실전투자"
            self.logger.info(f"KIS API 인증 완료: {env_name}")
            print(f"✅ KIS API 인증 성공 ({env_name})")
            
        except Exception as e:
            self.logger.error(f"KIS API 인증 실패: {e}")
            print(f"❌ KIS API 인증 실패: {e}")
            self.is_authenticated = False
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """현재가 조회"""
        if not self.is_authenticated:
            self.logger.warning("KIS API 인증이 필요합니다")
            return None
        
        try:
            # 실제 환경 설정
            env_dv = "real" if self.environment == "prod" else "demo"
            
            result = inquire_price(
                env_dv=env_dv,
                fid_cond_mrkt_div_code="J",  # 주식
                fid_input_iscd=symbol
            )
            
            # DataFrame이 아닌 dict인지 확인
            if result is not None and isinstance(result, dict) and 'output' in result:
                current_price = float(result['output']['stck_prpr'])
                return current_price
            # DataFrame인 경우 처리
            elif result is not None and hasattr(result, 'empty') and not result.empty:
                if 'stck_prpr' in result.columns:
                    current_price = float(result.iloc[0]['stck_prpr'])
                    return current_price
            
        except Exception as e:
            self.logger.error(f"현재가 조회 실패 {symbol}: {e}")
        
        return None
    
    def get_account_balance(self) -> Dict[str, float]:
        """계좌 잔고 조회"""
        if not self.is_authenticated:
            self.logger.warning("KIS API 인증이 필요합니다")
            return {}
        
        try:
            env_dv = "real" if self.environment == "prod" else "demo"
            
            result = inquire_balance(
                env_dv=env_dv,
                cano=self.trenv.my_acct,
                acnt_prdt_cd=self.trenv.my_prod,
                afhr_flpr_yn="N",  # 시간외단일가여부
                fncg_amt_auto_rdpt_yn="N",  # 융자금액자동상환여부
                fund_sttl_icld_yn="N",  # 펀드결제분포함여부
                prcs_dvsn="01",  # 처리구분
                ctx_area_fk100="",  # 연속조회검색조건
                ctx_area_nk100=""   # 연속조회키
            )
            
            if result and 'output2' in result:
                output = result['output2'][0]  # 첫 번째 계좌 정보
                
                return {
                    'cash_balance': float(output.get('dnca_tot_amt', '0')),  # 예수금총액
                    'total_asset': float(output.get('tot_evlu_amt', '0')),   # 총평가금액
                    'total_profit_loss': float(output.get('evlu_pfls_smtl_amt', '0')),  # 평가손익합계금액
                    'total_return_rate': float(output.get('tot_evlu_pfls_rt', '0'))     # 총수익률
                }
                
        except Exception as e:
            self.logger.error(f"계좌 잔고 조회 실패: {e}")
        
        return {}
    
    def calculate_order_amount(self, symbol: str, target_amount: float) -> Tuple[int, float]:
        """
        주문 수량 계산
        
        Args:
            symbol: 종목코드
            target_amount: 목표 투자금액
            
        Returns:
            (수량, 예상 총액)
        """
        current_price = self.get_current_price(symbol)
        if not current_price:
            return 0, 0.0
        
        # 수량 계산 (1주 단위)
        shares = int(target_amount // current_price)
        
        # 실제 투자금액
        actual_amount = shares * current_price
        
        return shares, actual_amount
    
    def execute_buy_order(self, symbol: str, shares: int, price: Optional[float] = None) -> Dict[str, Any]:
        """
        매수 주문 실행
        
        Args:
            symbol: 종목코드
            shares: 수량
            price: 지정가 (None이면 시장가)
            
        Returns:
            실행 결과
        """
        if not self.is_authenticated:
            return {"status": "FAILED", "message": "KIS API 인증이 필요합니다"}
        
        try:
            env_dv = "real" if self.environment == "prod" else "demo"
            
            # 시장가 주문
            if price is None:
                current_price = self.get_current_price(symbol)
                if not current_price:
                    return {"status": "FAILED", "message": "현재가 조회 실패"}
                price = current_price
            
            result = order_cash(
                env_dv=env_dv,
                ord_dv="buy",
                cano=self.trenv.my_acct,
                acnt_prdt_cd=self.trenv.my_prod,
                pdno=symbol,
                ord_qty=str(shares),
                ord_unpr=str(int(price)),  # 주문단가 (정수)
                ord_dvsn="01"  # 시장가
            )
            
            if result and result.get('rt_cd') == '0':
                # 성공
                order_no = result['output'].get('KRX_FWDG_ORD_ORGNO', '')
                return {
                    "status": "SUCCESS",
                    "order_no": order_no,
                    "message": "매수 주문 성공",
                    "shares": shares,
                    "price": price,
                    "total_amount": shares * price
                }
            else:
                # 실패
                error_msg = result.get('msg1', '알 수 없는 오류')
                return {
                    "status": "FAILED",
                    "message": f"매수 주문 실패: {error_msg}"
                }
                
        except Exception as e:
            self.logger.error(f"매수 주문 실행 오류: {e}")
            return {"status": "FAILED", "message": f"매수 주문 오류: {str(e)}"}
    
    def execute_sell_order(self, symbol: str, shares: int, price: Optional[float] = None) -> Dict[str, Any]:
        """
        매도 주문 실행
        
        Args:
            symbol: 종목코드
            shares: 수량
            price: 지정가 (None이면 시장가)
            
        Returns:
            실행 결과
        """
        if not self.is_authenticated:
            return {"status": "FAILED", "message": "KIS API 인증이 필요합니다"}
        
        try:
            env_dv = "real" if self.environment == "prod" else "demo"
            
            # 시장가 주문
            if price is None:
                current_price = self.get_current_price(symbol)
                if not current_price:
                    return {"status": "FAILED", "message": "현재가 조회 실패"}
                price = current_price
            
            result = order_cash(
                env_dv=env_dv,
                ord_dv="sell",
                cano=self.trenv.my_acct,
                acnt_prdt_cd=self.trenv.my_prod,
                pdno=symbol,
                ord_qty=str(shares),
                ord_unpr=str(int(price)),
                ord_dvsn="01"  # 시장가
            )
            
            if result and result.get('rt_cd') == '0':
                # 성공
                order_no = result['output'].get('KRX_FWDG_ORD_ORGNO', '')
                return {
                    "status": "SUCCESS",
                    "order_no": order_no,
                    "message": "매도 주문 성공",
                    "shares": shares,
                    "price": price,
                    "total_amount": shares * price
                }
            else:
                # 실패
                error_msg = result.get('msg1', '알 수 없는 오류')
                return {
                    "status": "FAILED",
                    "message": f"매도 주문 실패: {error_msg}"
                }
                
        except Exception as e:
            self.logger.error(f"매도 주문 실행 오류: {e}")
            return {"status": "FAILED", "message": f"매도 주문 오류: {str(e)}"}
    
    def execute_trade_with_confirmation(self, signal: TradeSignal) -> bool:
        """
        사용자 승인 후 매매 실행
        
        Args:
            signal: 매매 신호
            
        Returns:
            실행 여부
        """
        # 신호 정보 출력
        print("\n" + "="*60)
        print(f"🎯 매매 추천: {signal.name}({signal.symbol})")
        print(f"📍 섹터: {signal.sector}")
        print(f"📈 신호: {signal.signal_type}")
        print(f"🎲 확신도: {signal.confidence:.2f} ({signal.strength}/100)")
        print("="*60)
        
        # 현재가 정보
        current_price = self.get_current_price(signal.symbol)
        if current_price:
            print(f"💰 현재가: {current_price:,}원")
        
        # 근거 표시
        if signal.reasoning:
            print("\n📋 매매 근거:")
            for i, reason in enumerate(signal.reasoning, 1):
                print(f"   {i}. {reason}")
        
        # 기술적 지표 표시
        if signal.technical_indicators:
            print("\n📊 기술적 지표:")
            for indicator, value in signal.technical_indicators.items():
                if isinstance(value, float):
                    print(f"   {indicator}: {value:.2f}")
                else:
                    print(f"   {indicator}: {value}")
        
        # 리스크 평가 표시
        if signal.risk_assessment:
            print("\n⚠️ 리스크 평가:")
            for key, value in signal.risk_assessment.items():
                print(f"   {key}: {value}")
        
        # 매수/매도별 추가 정보
        if signal.signal_type == "BUY":
            # 투자 금액 계산
            target_weight = self.portfolio.get_target_allocation().get(signal.sector, 16.67)
            total_value = self.portfolio.get_total_portfolio_value()
            target_amount = total_value * (target_weight / 100) / 2  # 섹터당 2종목 가정
            
            if current_price:
                shares, actual_amount = self.calculate_order_amount(signal.symbol, target_amount)
                print(f"\n💵 투자 계획:")
                print(f"   목표 금액: {target_amount:,.0f}원")
                print(f"   매수 수량: {shares:,}주")
                print(f"   실제 금액: {actual_amount:,.0f}원")
        
        elif signal.signal_type == "SELL":
            # 현재 보유 포지션 확인
            if signal.symbol in self.portfolio.positions:
                position = self.portfolio.positions[signal.symbol]
                print(f"\n📦 보유 현황:")
                print(f"   보유 수량: {position['shares']:,}주")
                print(f"   평균 단가: {position['avg_price']:,}원")
                print(f"   현재 손익: {position['unrealized_pnl']:+,.0f}원 ({position['unrealized_pnl']/position['total_cost']*100:+.2f}%)")
        
        # 사용자 확인
        print("\n" + "-"*60)
        while True:
            user_input = input("실행하시겠습니까? (y/n/d): ").lower()
            
            if user_input == 'y':
                print("✅ 매매 실행을 진행합니다...")
                return self._execute_confirmed_trade(signal, current_price)
            
            elif user_input == 'n':
                print("❌ 매매를 취소합니다.")
                self.trade_logger.logger.info(f"매매 취소: {signal.symbol} {signal.signal_type}")
                return False
            
            elif user_input == 'd':
                print("ℹ️ 상세 정보를 표시합니다...")
                self._show_detailed_analysis(signal)
                continue
            
            else:
                print("y(실행), n(취소), d(상세정보) 중 하나를 선택해주세요.")
    
    def _execute_confirmed_trade(self, signal: TradeSignal, current_price: float) -> bool:
        """승인된 매매 실행"""
        portfolio_before = self.portfolio.get_portfolio_summary()
        
        try:
            if signal.signal_type == "BUY":
                # 매수 실행
                target_weight = self.portfolio.get_target_allocation().get(signal.sector, 16.67)
                total_value = self.portfolio.get_total_portfolio_value()
                target_amount = total_value * (target_weight / 100) / 2
                
                shares, actual_amount = self.calculate_order_amount(signal.symbol, target_amount)
                
                if shares == 0:
                    print("❌ 매수 가능 수량이 없습니다.")
                    return False
                
                # 실제 주문 실행
                result = self.execute_buy_order(signal.symbol, shares, current_price)
                
            elif signal.signal_type == "SELL":
                # 매도 실행
                if signal.symbol not in self.portfolio.positions:
                    print("❌ 보유 포지션이 없습니다.")
                    return False
                
                position = self.portfolio.positions[signal.symbol]
                shares = position['shares']
                
                # 실제 주문 실행
                result = self.execute_sell_order(signal.symbol, shares, current_price)
            
            else:
                print("❌ 지원하지 않는 신호 타입입니다.")
                return False
            
            # 실행 결과 처리
            if result['status'] == 'SUCCESS':
                print(f"✅ {signal.signal_type} 주문 성공!")
                print(f"   주문번호: {result.get('order_no', 'N/A')}")
                
                # 포트폴리오 업데이트
                action = signal.signal_type
                self.portfolio.update_position(signal.symbol, shares, current_price, action)
                
                # 실행 로그 작성
                portfolio_after = self.portfolio.get_portfolio_summary()
                
                execution = TradeExecution(
                    timestamp=datetime.now().isoformat(),
                    trade_id=result.get('order_no', f"MANUAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                    symbol=signal.symbol,
                    name=signal.name,
                    sector=signal.sector,
                    action=action,
                    order_type="MARKET",
                    shares=shares,
                    price=current_price,
                    total_amount=shares * current_price,
                    commission=shares * current_price * 0.00015,  # 수수료 0.015%
                    tax=shares * current_price * 0.0023 if action == "SELL" else 0,  # 매도세 0.23%
                    net_amount=shares * current_price * (1 - 0.00015 - (0.0023 if action == "SELL" else 0)),
                    portfolio_before=portfolio_before,
                    portfolio_after=portfolio_after,
                    execution_status="SUCCESS",
                    execution_message=result['message']
                )
                
                self.trade_logger.log_trade_execution(execution)
                
                # 포트폴리오 상태 저장
                self.portfolio.save_state()
                
                return True
            
            else:
                print(f"❌ 주문 실패: {result['message']}")
                
                # 실패 로그 작성
                execution = TradeExecution(
                    timestamp=datetime.now().isoformat(),
                    trade_id=f"FAILED_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    symbol=signal.symbol,
                    name=signal.name,
                    sector=signal.sector,
                    action=signal.signal_type,
                    order_type="MARKET",
                    shares=shares if 'shares' in locals() else 0,
                    price=current_price,
                    total_amount=0,
                    commission=0,
                    tax=0,
                    net_amount=0,
                    portfolio_before=portfolio_before,
                    portfolio_after=portfolio_before,
                    execution_status="FAILED",
                    execution_message=result['message']
                )
                
                self.trade_logger.log_trade_execution(execution)
                
                return False
                
        except Exception as e:
            self.logger.error(f"매매 실행 오류: {e}")
            print(f"❌ 매매 실행 중 오류 발생: {e}")
            return False
    
    def _show_detailed_analysis(self, signal: TradeSignal):
        """상세 분석 정보 표시"""
        print("\n" + "="*80)
        print(f"📊 상세 분석: {signal.name}({signal.symbol})")
        print("="*80)
        
        # 시장 상황
        if signal.market_conditions:
            print("\n🌍 시장 상황:")
            for key, value in signal.market_conditions.items():
                print(f"   {key}: {value}")
        
        # 섹터 정보
        sector_info = None
        for sector_name, sector_data in self.portfolio.get_sector_info().items():
            if sector_name == signal.sector:
                sector_info = sector_data
                break
        
        if sector_info:
            print(f"\n🏢 섹터 정보:")
            print(f"   섹터명: {sector_info['sector_name']}")
            print(f"   테마: {sector_info['theme']}")
            print(f"   목표 비중: {sector_info['target_weight']:.1f}%")
        
        # 현재 포트폴리오 상황
        current_allocation = self.portfolio.calculate_current_allocation()
        target_allocation = self.portfolio.get_target_allocation()
        
        print(f"\n📈 포트폴리오 현황:")
        print(f"   현재 {signal.sector} 비중: {current_allocation.get(signal.sector, 0.0):.1f}%")
        print(f"   목표 {signal.sector} 비중: {target_allocation.get(signal.sector, 0.0):.1f}%")
        
        # 리밸런싱 신호
        rebalancing_signals = self.portfolio.get_rebalancing_signals()
        if signal.sector in rebalancing_signals:
            rebal_info = rebalancing_signals[signal.sector]
            print(f"   리밸런싱 신호: {rebal_info['action']} (차이: {rebal_info['difference']:+.1f}%)")
        
        print("="*80)


# 테스트 및 디버깅용
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 테스트용 포트폴리오와 로거
    portfolio = SectorPortfolio()
    trade_logger = TradeLogger()
    
    # 수동 실행기 테스트
    executor = ManualTradeExecutor(portfolio, trade_logger)
    
    print("수동 매매 실행기 테스트")
    print("실제 KIS API 연동 테스트는 manual_trader.py에서 수행하세요.")