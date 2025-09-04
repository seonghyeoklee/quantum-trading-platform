#!/usr/bin/env python3
"""
섹터별 분산투자 수동 매매 시스템
2025년 유망섹터 기반 콘솔 자동매매 테스트

사용법:
    python manual_trader.py              # 모의투자 모드
    python manual_trader.py --prod       # 실전투자 모드 
    python manual_trader.py --analysis   # 분석만 수행
"""

import sys
import argparse
import logging
import asyncio
from pathlib import Path
from datetime import datetime
import pandas as pd
import time

# 프로젝트 경로 추가
current_dir = Path(__file__).parent
sys.path.append(str(current_dir.parent / 'examples_llm'))
sys.path.append(str(current_dir.parent / 'trading_strategy'))
sys.path.append(str(current_dir))  # 현재 디렉토리도 추가

# 로컬 모듈
from core.sector_portfolio import SectorPortfolio
from core.trade_logger import TradeLogger, TradeSignal
from core.manual_executor import ManualTradeExecutor
from core.enhanced_analyzer import EnhancedSectorAnalyzer
from core.smart_order_manager import SmartOrderManager

# 기술적 분석을 위한 기존 모듈 활용 (선택적)
try:
    from core.signal_detector import SignalDetector
except ImportError:
    # signal_detector가 없는 경우 None으로 설정
    SignalDetector = None

class SectorTradingConsole:
    """섹터 분산투자 콘솔 인터페이스"""
    
    def __init__(self, environment: str = "vps", analysis_only: bool = False):
        """
        초기화
        
        Args:
            environment: 거래 환경 (vps: 모의투자, prod: 실전투자)
            analysis_only: 분석만 수행 모드 (KIS API 사용하지 않음)
        """
        self.environment = environment
        self.analysis_only = analysis_only
        self.setup_logging()
        
        # 핵심 컴포넌트 초기화
        self.portfolio = SectorPortfolio()
        self.trade_logger = TradeLogger()
        self.executor = ManualTradeExecutor(self.portfolio, self.trade_logger)
        self.signal_detector = SignalDetector() if SignalDetector else None
        
        # Enhanced Analyzer 초기화 (분석 전용 모드에서는 KIS API 사용하지 않음)
        self.enhanced_analyzer = EnhancedSectorAnalyzer(use_kis_api=(not analysis_only))
        
        # Smart Order Manager 초기화
        self.smart_order_manager = SmartOrderManager()
        
        # 상태 변수
        self.is_running = True
        self.last_analysis_time = None
        
        print(f"\n🚀 섹터 분산투자 시스템 시작")
        print(f"📊 모드: {'실전투자' if environment == 'prod' else '모의투자'}")
        print(f"💼 초기 투자금: {self.portfolio.cash_balance:,}원")
        print("="*60)
    
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(
                    current_dir / 'logs' / f'console_{datetime.now().strftime("%Y%m%d")}.log',
                    encoding='utf-8'
                ),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def initialize_system(self):
        """시스템 초기화"""
        print("🔧 시스템 초기화 중...")
        
        if not self.analysis_only:
            # KIS API 인증 (매매 모드에만 필요)
            print("🔑 KIS API 인증...")
            self.executor.authenticate_kis(self.environment)
            
            if not self.executor.is_authenticated:
                print("❌ KIS API 인증 실패")
                return False
            
            # 기존 포트폴리오 상태 복원 (선택적)
            await self.load_existing_portfolio()
        else:
            print("📊 분석 전용 모드 - KIS API 인증 생략")
        
        # 시스템 상태 체크
        if not self.analysis_only:
            self.show_system_status()
        
        return True
    
    async def load_existing_portfolio(self):
        """기존 포트폴리오 상태 로드"""
        try:
            # 가장 최근 상태 파일 찾기
            log_dir = current_dir / 'logs'
            state_files = list(log_dir.glob('portfolio_state_*.json'))
            
            if state_files:
                latest_file = max(state_files, key=lambda x: x.stat().st_mtime)
                
                user_input = input(f"🔄 기존 포트폴리오 상태를 복원하시겠습니까? ({latest_file.name}) (y/n): ")
                if user_input.lower() == 'y':
                    self.portfolio.load_state(str(latest_file))
                    print("✅ 포트폴리오 상태 복원 완료")
                    
        except Exception as e:
            self.logger.warning(f"포트폴리오 상태 로드 실패: {e}")
    
    def show_system_status(self):
        """시스템 상태 표시"""
        print("\n" + "="*80)
        print("📊 시스템 상태")
        print("="*80)
        
        # 포트폴리오 요약
        summary = self.portfolio.get_portfolio_summary()
        print(f"💰 총 자산: {summary['total_value']:,.0f}원")
        print(f"💵 현금: {summary['cash_balance']:,.0f}원 ({summary['cash_ratio']:.1f}%)")
        print(f"💼 투자금: {summary['invested_amount']:,.0f}원")
        print(f"📈 총 수익률: {summary['total_return_pct']:+.2f}% ({summary['total_return_amount']:+,.0f}원)")
        print(f"📦 보유 종목: {summary['position_count']}개")
        
        # 섹터별 현황
        current_allocation = self.portfolio.calculate_current_allocation()
        target_allocation = self.portfolio.get_target_allocation()
        
        print(f"\n📊 섹터별 현황:")
        print("─" * 80)
        print(f"{'섹터':<12} {'현재비중':<8} {'목표비중':<8} {'차이':<8} {'상태'}")
        print("─" * 80)
        
        for sector in target_allocation:
            current = current_allocation[sector]
            target = target_allocation[sector]
            diff = current - target
            status = "⚖️" if abs(diff) < 2 else ("🔼" if diff > 0 else "🔽")
            
            print(f"{sector:<12} {current:>6.1f}% {target:>6.1f}% {diff:>+6.1f}% {status}")
        
        # 리스크 경고
        warnings = self.portfolio.check_risk_limits()
        if warnings:
            print(f"\n⚠️ 리스크 경고:")
            for warning in warnings:
                print(f"   {warning['type']}: {warning.get('symbol', warning.get('sector', ''))} "
                      f"({warning['current']:.1f}% > {warning['limit']:.1f}%)")
        
        print("="*80)
    
    async def analyze_market_signals(self):
        """Enhanced Analyzer를 활용한 시장 신호 분석"""
        print("\n🔍 Enhanced Market Analysis 시작...")
        
        try:
            # Enhanced Analyzer를 통한 전체 포트폴리오 분석
            portfolio_analysis = self.enhanced_analyzer.analyze_sector_portfolio(
                self.portfolio.sectors_config
            )
            
            # 포트폴리오 요약 정보 출력
            portfolio_summary = self.enhanced_analyzer.get_portfolio_summary(portfolio_analysis)
            
            print(f"\n📈 Portfolio Analysis Summary:")
            print(f"   총 종목: {portfolio_summary['total_stocks']}개")
            print(f"   매수 신호: {portfolio_summary['buy_signals']}개")
            print(f"   매도 신호: {portfolio_summary['sell_signals']}개")  
            print(f"   보유 신호: {portfolio_summary['hold_signals']}개")
            print(f"   평균 신뢰도: {portfolio_summary['avg_confidence']:.2f}")
            print(f"   고위험 종목: {portfolio_summary['high_risk_stocks']}개")
            
            # 섹터별 분석 결과 상세 출력
            signals = []
            for sector_name, analysis_results in portfolio_analysis.items():
                print(f"\n📊 {sector_name} 섹터:")
                
                for result in analysis_results:
                    # 출력 포맷 개선
                    price_str = f"{result.current_price:,}원" if result.current_price else "N/A"
                    
                    # 신호 이모지 설정
                    signal_emoji = {
                        "BUY": "🟢",
                        "SELL": "🔴", 
                        "HOLD": "🟡",
                        "ERROR": "⚪"
                    }.get(result.recommendation, "⚪")
                    
                    print(f"   {signal_emoji} {result.name}({result.symbol})")
                    print(f"      가격: {price_str}")
                    print(f"      추천: {result.recommendation} (신뢰도: {result.confidence_score:.2f})")
                    print(f"      위험도: {result.risk_score:.2f}")
                    
                    # 기술적 지표 요약
                    if result.technical_indicators:
                        rsi = result.technical_indicators.get('rsi')
                        if rsi:
                            print(f"      RSI: {rsi:.1f} ({result.technical_indicators.get('rsi_signal', 'N/A')})")
                    
                    # 매매 신호가 있는 경우만 signals에 추가
                    if result.recommendation in ['BUY', 'SELL']:
                        # Smart Order 추천 생성
                        order_recommendation = None
                        if result.current_price and result.technical_indicators:
                            try:
                                order_recommendation = self.smart_order_manager.get_optimal_order(
                                    symbol=result.symbol,
                                    action=result.recommendation,
                                    technical_indicators=result.technical_indicators,
                                    current_price=result.current_price
                                )
                                
                                # Smart Order 정보 출력
                                print(f"      🎯 Smart Order: {order_recommendation.order_type} "
                                      f"{order_recommendation.price:,}원 ({order_recommendation.strategy})")
                                print(f"      📝 근거: {order_recommendation.reasoning}")
                                
                            except Exception as e:
                                self.logger.warning(f"Smart Order 생성 실패 {result.symbol}: {e}")
                        
                        # TradeSignal 형식으로 변환
                        signal = TradeSignal(
                            timestamp=result.analysis_timestamp.isoformat(),
                            symbol=result.symbol,
                            name=result.name,
                            sector=result.sector,
                            signal_type=result.recommendation,
                            confidence=result.confidence_score,
                            strength=int(result.confidence_score * 100),
                            current_price=result.current_price or 0,
                            reasoning=[
                                f"Enhanced analysis: {len(result.trading_signals)} technical signals",
                                f"Risk score: {result.risk_score:.2f}",
                                f"Data quality: {result.data_quality}"
                            ],
                            technical_indicators=result.technical_indicators,
                            risk_assessment={
                                'risk_score': result.risk_score,
                                'data_quality': result.data_quality,
                                'signal_count': len(result.trading_signals)
                            },
                            market_conditions={},
                            # Smart Order 정보 추가
                            smart_order=order_recommendation.__dict__ if order_recommendation else None
                        )
                        signals.append(signal)
                        self.trade_logger.log_trade_signal(signal)
            
            self.last_analysis_time = datetime.now()
            print(f"\n✅ Enhanced Analysis 완료: {len(signals)}개 매매 신호 발견")
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Enhanced Analysis 실패: {e}")
            print(f"❌ 분석 실패: {e}")
            return []
    
    def generate_trading_signal(self, symbol: str, name: str, sector: str, 
                              current_price: float, stock_info: dict) -> TradeSignal:
        """
        매매 신호 생성 (단순화된 버전)
        실제로는 더 정교한 기술적 분석이 필요
        """
        import random
        
        # 현재 포지션 확인
        has_position = symbol in self.portfolio.positions
        
        # 섹터별 리밸런싱 신호 확인
        rebalancing_signals = self.portfolio.get_rebalancing_signals()
        needs_increase = sector in rebalancing_signals and rebalancing_signals[sector]['action'] == 'INCREASE'
        needs_decrease = sector in rebalancing_signals and rebalancing_signals[sector]['action'] == 'REDUCE'
        
        # 단순한 신호 로직 (실제로는 더 복잡해야 함)
        if needs_increase and not has_position:
            signal_type = "BUY"
            confidence = 0.7 + random.uniform(0, 0.2)
            strength = int(70 + random.uniform(0, 20))
            reasoning = [
                f"{sector} 섹터 비중 부족으로 리밸런싱 필요",
                f"2025년 {sector} 테마 유망",
                stock_info['reason']
            ]
        elif needs_decrease and has_position:
            signal_type = "SELL"
            confidence = 0.6 + random.uniform(0, 0.2)
            strength = int(60 + random.uniform(0, 20))
            reasoning = [
                f"{sector} 섹터 과투자로 리밸런싱 필요",
                f"포트폴리오 균형 조정",
                "이익 실현 적정 시점"
            ]
        else:
            signal_type = "HOLD"
            confidence = 0.5 + random.uniform(-0.1, 0.1)
            strength = int(40 + random.uniform(0, 20))
            reasoning = ["현재 적정 비중 유지", "추가 분석 필요"]
        
        # 기술적 지표 (모의 데이터)
        technical_indicators = {
            "현재가": current_price,
            "RSI": 30 + random.uniform(0, 40),
            "MACD": "골든크로스" if signal_type == "BUY" else "데드크로스" if signal_type == "SELL" else "중립",
            "거래량비율": 1.0 + random.uniform(-0.3, 0.7)
        }
        
        # 시장 조건 (모의 데이터)
        market_conditions = {
            "시장추세": "상승" if signal_type == "BUY" else "하락" if signal_type == "SELL" else "횡보",
            "섹터모멘텀": "강세" if needs_increase else "약세" if needs_decrease else "중립",
            "변동성": "보통"
        }
        
        # 리스크 평가
        risk_assessment = {
            "위험도": stock_info.get('market_cap', '중형주'),
            "섹터리스크": "보통",
            "유동성": "양호" if stock_info.get('market_cap') == '대형주' else "보통"
        }
        
        return TradeSignal(
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            name=name,
            sector=sector,
            signal_type=signal_type,
            confidence=confidence,
            strength=strength,
            technical_indicators=technical_indicators,
            market_conditions=market_conditions,
            reasoning=reasoning,
            risk_assessment=risk_assessment
        )
    
    async def execute_trading_signals(self, signals: list):
        """매매 신호 실행"""
        if not signals:
            print("📝 실행할 매매 신호가 없습니다.")
            return
        
        # BUY와 SELL 신호만 필터링
        actionable_signals = [s for s in signals if s.signal_type in ['BUY', 'SELL']]
        
        if not actionable_signals:
            print("📝 실행 가능한 매매 신호가 없습니다.")
            return
        
        print(f"\n🎯 {len(actionable_signals)}개 매매 신호 검토")
        
        for i, signal in enumerate(actionable_signals, 1):
            print(f"\n[{i}/{len(actionable_signals)}]")
            
            # 신호별 사용자 확인 및 실행
            executed = self.executor.execute_trade_with_confirmation(signal)
            
            if executed:
                print("✅ 매매 실행 완료")
                # 잠시 대기 (API 호출 간격)
                await asyncio.sleep(1)
            else:
                print("⏭️ 다음 신호로 이동")
            
            # 중간에 종료할 수 있는 옵션
            if i < len(actionable_signals):
                continue_input = input("\n계속하시겠습니까? (Enter: 계속, q: 종료): ")
                if continue_input.lower() == 'q':
                    break
    
    def show_main_menu(self):
        """메인 메뉴 표시"""
        print("\n" + "="*60)
        print("🎮 섹터 분산투자 수동 매매 시스템")
        print("="*60)
        print("1. 📊 시장 분석 및 매매 신호 확인")
        print("2. 📈 포트폴리오 현황 보기") 
        print("3. 📋 거래 기록 조회")
        print("4. ⚙️ 설정 및 리밸런싱")
        print("5. 📄 리포트 생성")
        print("6. 🔄 시스템 상태 새로고침")
        print("0. 🚪 종료")
        print("="*60)
    
    async def handle_menu_selection(self, choice: str):
        """메뉴 선택 처리"""
        if choice == '1':
            # 시장 분석 및 매매
            signals = await self.analyze_market_signals()
            if signals:
                await self.execute_trading_signals(signals)
        
        elif choice == '2':
            # 포트폴리오 현황
            self.show_portfolio_detail()
        
        elif choice == '3':
            # 거래 기록 조회
            self.show_trade_history()
        
        elif choice == '4':
            # 설정 및 리밸런싱
            await self.handle_rebalancing()
        
        elif choice == '5':
            # 리포트 생성
            self.generate_reports()
        
        elif choice == '6':
            # 시스템 상태 새로고침
            self.show_system_status()
        
        elif choice == '0':
            # 종료
            await self.shutdown()
            self.is_running = False
        
        else:
            print("❌ 잘못된 선택입니다.")
    
    def show_portfolio_detail(self):
        """포트폴리오 상세 현황"""
        print("\n" + "="*80)
        print("📊 포트폴리오 상세 현황")
        print("="*80)
        
        # 전체 성과
        summary = self.portfolio.get_portfolio_summary()
        sector_performance = self.portfolio.get_sector_performance()
        
        print(f"💰 총 자산: {summary['total_value']:,.0f}원")
        print(f"📈 총 수익률: {summary['total_return_pct']:+.2f}% ({summary['total_return_amount']:+,.0f}원)")
        
        # 섹터별 성과
        print(f"\n📊 섹터별 성과:")
        print("─" * 80)
        print(f"{'섹터':<12} {'투자금액':<12} {'평가금액':<12} {'손익':<12} {'수익률'}")
        print("─" * 80)
        
        for sector, perf in sector_performance.items():
            if perf['total_cost'] > 0:  # 투자된 섹터만
                print(f"{sector:<12} {perf['total_cost']:>10,.0f}원 "
                      f"{perf['market_value']:>10,.0f}원 "
                      f"{perf['unrealized_pnl']:>+10,.0f}원 "
                      f"{perf['return_pct']:>+7.2f}%")
        
        # 개별 종목 현황
        if self.portfolio.positions:
            print(f"\n📦 보유 종목:")
            print("─" * 80)
            print(f"{'종목명':<15} {'수량':<8} {'평균단가':<10} {'현재가':<10} {'손익률'}")
            print("─" * 80)
            
            for symbol, position in self.portfolio.positions.items():
                # 종목명 찾기
                stock_name = symbol
                for sector_data in self.portfolio.get_sector_info().values():
                    for stock_info in sector_data['stocks'].values():
                        if stock_info['symbol'] == symbol:
                            stock_name = stock_info['name']
                            break
                
                current_price = self.executor.get_current_price(symbol)
                return_rate = (position['unrealized_pnl'] / position['total_cost'] * 100) if position['total_cost'] > 0 else 0
                
                print(f"{stock_name:<15} {position['shares']:>6,}주 "
                      f"{position['avg_price']:>8,.0f}원 "
                      f"{current_price:>8,.0f}원 " if current_price else f"{'N/A':>10} "
                      f"{return_rate:>+7.2f}%")
        
        print("="*80)
    
    def show_trade_history(self):
        """거래 기록 조회"""
        print("\n📋 거래 기록 조회")
        
        # 통계 정보
        stats = self.trade_logger.get_statistics()
        
        print(f"📊 거래 통계:")
        print(f"   신호 발생: {stats['total_signals']}건")
        print(f"   거래 실행: {stats['total_executions']}건")
        print(f"   성공률: {stats.get('success_rate', 0):.1f}%")
        
        if 'total_amount' in stats:
            print(f"   총 거래금액: {stats['total_amount']:,.0f}원")
            print(f"   수수료: {stats['total_commission']:,.0f}원")
            print(f"   세금: {stats['total_tax']:,.0f}원")
        
        # 일일 리포트 생성 옵션
        generate_report = input("\n📄 일일 리포트를 생성하시겠습니까? (y/n): ")
        if generate_report.lower() == 'y':
            report = self.trade_logger.generate_daily_report()
            print("\n" + report)
    
    async def handle_rebalancing(self):
        """리밸런싱 처리"""
        print("\n⚙️ 포트폴리오 리밸런싱")
        
        rebalancing_signals = self.portfolio.get_rebalancing_signals()
        
        if not rebalancing_signals:
            print("✅ 현재 포트폴리오가 목표 배분에 적합합니다.")
            return
        
        print("\n📊 리밸런싱 필요 섹터:")
        for sector, signal in rebalancing_signals.items():
            print(f"   {sector}: {signal['action']} "
                  f"(현재 {signal['current_weight']:.1f}% → 목표 {signal['target_weight']:.1f}%)")
        
        proceed = input("\n리밸런싱을 진행하시겠습니까? (y/n): ")
        if proceed.lower() == 'y':
            # 리밸런싱 신호로 매매 신호 생성
            print("🔄 리밸런싱 매매 신호 생성 중...")
            # 실제로는 더 정교한 리밸런싱 로직 구현
            signals = await self.analyze_market_signals()
            await self.execute_trading_signals(signals)
    
    def generate_reports(self):
        """리포트 생성"""
        print("\n📄 리포트 생성")
        
        print("1. 📋 일일 거래 리포트")
        print("2. 📊 Excel 종합 리포트")
        print("3. 📈 성과 분석 리포트")
        
        choice = input("선택하세요 (1-3): ")
        
        if choice == '1':
            report = self.trade_logger.generate_daily_report()
            print("\n" + report)
        
        elif choice == '2':
            filename = self.trade_logger.export_to_excel()
            print(f"✅ Excel 리포트 생성: {filename}")
        
        elif choice == '3':
            # 성과 분석 (기본)
            self.show_portfolio_detail()
        
        else:
            print("❌ 잘못된 선택입니다.")
    
    async def shutdown(self):
        """시스템 종료"""
        print("\n🔄 시스템 종료 중...")
        
        # 포트폴리오 상태 저장
        self.portfolio.save_state()
        
        # 최종 리포트 생성
        final_report = self.trade_logger.generate_daily_report()
        print("\n📄 최종 거래 리포트:")
        print(final_report)
        
        print("✅ 시스템 종료 완료")
    
    async def run(self):
        """메인 실행 루프"""
        if not await self.initialize_system():
            return
        
        try:
            while self.is_running:
                self.show_main_menu()
                choice = input("메뉴를 선택하세요: ")
                
                await self.handle_menu_selection(choice)
                
                if self.is_running:
                    input("\nEnter를 눌러 계속...")
        
        except KeyboardInterrupt:
            print("\n⚠️ 사용자 종료 요청")
            await self.shutdown()
        
        except Exception as e:
            self.logger.error(f"시스템 오류: {e}")
            print(f"❌ 시스템 오류: {e}")
            await self.shutdown()


async def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='섹터 분산투자 수동 매매 시스템')
    parser.add_argument('--prod', action='store_true', help='실전투자 모드')
    parser.add_argument('--analysis', action='store_true', help='분석만 수행 (매매 없음)')
    
    args = parser.parse_args()
    
    # 환경 설정
    environment = "prod" if args.prod else "vps"
    
    if args.prod:
        confirm = input("⚠️ 실전투자 모드입니다. 정말 진행하시겠습니까? (yes 입력): ")
        if confirm != "yes":
            print("❌ 실전투자 모드 취소")
            return
    
    # 콘솔 시스템 시작 (analysis_only 옵션 추가)
    console = SectorTradingConsole(environment, analysis_only=args.analysis)
    
    if args.analysis:
        # 분석만 수행
        print("📊 분석 전용 모드 (KIS API 없이 다중 데이터 소스 활용)")
        if await console.initialize_system():
            signals = await console.analyze_market_signals()
            if signals:
                print(f"\n💡 매매 신호 요약:")
                for signal in signals:
                    print(f"   {signal.signal_type}: {signal.name}({signal.symbol}) - 신뢰도: {signal.confidence:.2f}")
    else:
        # 전체 시스템 실행
        await console.run()


if __name__ == "__main__":
    print("🚀 2025년 유망섹터 분산투자 시스템")
    print("=" * 60)
    
    asyncio.run(main())