"""
실시간 신호 모니터링 및 로깅 시스템
실제 매매 없이 신호만 감지하고 상세 로깅
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import json
import pandas as pd

# 프로젝트 경로 추가
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir.parent))  # quantum-adapter-kis 루트
sys.path.append(str(current_dir.parent / 'examples_llm'))  # KIS API 모듈
sys.path.append(str(current_dir))  # trading_strategy

# KIS API 모듈 import
import kis_auth as ka
from domestic_stock.inquire_daily_itemchartprice.inquire_daily_itemchartprice import inquire_daily_itemchartprice

# trading_strategy 모듈 import
from core.technical_analysis import TechnicalAnalyzer
from core.signal_detector import SignalDetector, SignalType, ConfidenceLevel, TradingSignal
from monitor.order_simulator import OrderSimulator

# 로깅 설정
def setup_logging(log_dir: str = "logs"):
    """로깅 설정 - 여러 종류의 로그 파일 생성"""
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # 각 종류별 로그 디렉토리
    signals_dir = log_path / "signals"
    market_dir = log_path / "market"
    orders_dir = log_path / "orders"
    
    signals_dir.mkdir(exist_ok=True)
    market_dir.mkdir(exist_ok=True)
    orders_dir.mkdir(exist_ok=True)
    
    # 오늘 날짜로 로그 파일 생성
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 메인 로거 설정 (모든 로그)
    main_logger = logging.getLogger()
    main_logger.setLevel(logging.INFO)
    
    # 포맷터
    detailed_formatter = logging.Formatter(
        '[%(asctime)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 기존 핸들러 제거
    main_logger.handlers.clear()
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(detailed_formatter)
    
    # 전체 로그 파일 핸들러
    main_file_handler = logging.FileHandler(
        log_path / f"all_{today}.log", 
        encoding='utf-8'
    )
    main_file_handler.setLevel(logging.INFO)
    main_file_handler.setFormatter(detailed_formatter)
    
    # 시장 데이터 로그 파일 핸들러
    market_file_handler = logging.FileHandler(
        market_dir / f"market_{today}.log",
        encoding='utf-8'
    )
    market_file_handler.setLevel(logging.INFO)
    market_file_handler.setFormatter(detailed_formatter)
    
    # 핸들러 추가
    main_logger.addHandler(console_handler)
    main_logger.addHandler(main_file_handler)
    
    # 시장 데이터 전용 로거 생성
    market_logger = logging.getLogger('market_data')
    market_logger.addHandler(market_file_handler)
    market_logger.setLevel(logging.INFO)
    
    return main_logger

# 로거 참조
logger = logging.getLogger()

class SignalMonitor:
    """실시간 신호 모니터링"""
    
    def __init__(self, 
                 symbols: Dict[str, str],
                 check_interval: int = 30,
                 simulation_mode: bool = True):
        """
        Args:
            symbols: 모니터링할 종목 딕셔너리 {코드: 이름}
            check_interval: 체크 간격 (초)
            simulation_mode: 시뮬레이션 모드 (True면 실제 매매 안함)
        """
        self.symbols = symbols
        self.check_interval = check_interval
        self.simulation_mode = simulation_mode
        
        # KIS API 인증 초기화
        try:
            logger.info("🔐 KIS API 인증 시작...")
            ka.auth(svr="prod", product="01")  # 실전 계좌 인증
            logger.info("✅ KIS API 인증 성공")
        except Exception as e:
            logger.error(f"❌ KIS API 인증 실패: {e}")
            logger.info("🔄 더미 데이터 모드로 동작")
        
        self.analyzer = TechnicalAnalyzer()
        self.detector = SignalDetector()
        self.order_sim = OrderSimulator()
        
        self.last_signals: Dict[str, Optional[TradingSignal]] = {}
        self.positions: Dict[str, dict] = {}  # 가상 포지션
        
        logger.info("="*60)
        logger.info("📊 신호 모니터링 시스템 시작")
        logger.info(f"모니터링 종목: {list(symbols.values())}")
        logger.info(f"체크 간격: {check_interval}초")
        logger.info(f"모드: {'시뮬레이션' if simulation_mode else '실전'}")
        logger.info("="*60)
    
    async def start_monitoring(self):
        """모니터링 시작"""
        logger.info("🚀 실시간 모니터링 시작...")
        
        while True:
            try:
                await self._check_all_symbols()
                await asyncio.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("⏹️ 모니터링 중지됨")
                break
            except Exception as e:
                logger.error(f"❌ 모니터링 오류: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_all_symbols(self):
        """모든 종목 체크"""
        for symbol, name in self.symbols.items():
            try:
                await self._check_symbol(symbol, name)
            except Exception as e:
                logger.error(f"종목 체크 실패 {symbol}: {e}")
    
    async def _check_symbol(self, symbol: str, name: str):
        """개별 종목 체크"""
        # KIS API에서 실제 시장 데이터 조회
        df = self._get_real_kis_data(symbol)
        
        # 기술적 지표 계산
        df = self.analyzer.calculate_all_indicators(df)
        
        # 디버그: 현재 기술적 지표 상태 출력
        if not df.empty:
            latest = df.iloc[-1]
            
            logger.info("")
            logger.info(f"{'='*15} {name}({symbol}) {'='*15}")
            logger.info(f"💰 현재가: {latest['close']:,.0f}원")
            logger.info(f"📊 SMA5:  {latest['sma5']:,.0f}원")
            logger.info(f"📊 SMA20: {latest['sma20']:,.0f}원")
            logger.info(f"📈 차이:  {latest['sma5']-latest['sma20']:+,.0f}원")
            
            # 크로스 상태 확인
            if len(df) >= 2:
                prev = df.iloc[-2]
                current_diff = latest['sma5'] - latest['sma20']  
                prev_diff = prev['sma5'] - prev['sma20']
                
                if prev_diff <= 0 and current_diff > 0:
                    logger.info("🚨🚨 골든크로스 조건 감지! (SMA5가 SMA20 위로) 🚨🚨")
                elif prev_diff >= 0 and current_diff < 0:
                    logger.info("🚨🚨 데드크로스 조건 감지! (SMA5가 SMA20 아래로) 🚨🚨")
                else:
                    cross_status = "위" if current_diff > 0 else "아래"
                    trend = "상승추세" if current_diff > 0 else "하락추세"
                    logger.info(f"📍 현재상태: SMA5가 SMA20 {cross_status} ({trend})")
            
            logger.info(f"{'='*45}")
        
        # 신호 감지
        signal = self.detector.detect_golden_cross(df, symbol, name)
        
        if signal:
            self._process_signal(signal)
    
    def _process_signal(self, signal: TradingSignal):
        """신호 처리"""
        symbol = signal.symbol
        
        # 이전 신호와 비교
        last_signal = self.last_signals.get(symbol)
        
        # 새로운 신호이거나 변경된 경우만 처리
        if not last_signal or last_signal.signal_type != signal.signal_type:
            self._log_signal_detection(signal)
            
            # 확정된 신호만 주문 시뮬레이션
            if signal.confidence == ConfidenceLevel.CONFIRMED:
                self._simulate_order(signal)
            
            self.last_signals[symbol] = signal
    
    def _log_signal_detection(self, signal: TradingSignal):
        """신호 감지 로깅"""
        logger.info("")
        logger.info(f"{'='*60}")
        logger.info(f"🎯 신호 감지: {signal.symbol_name}({signal.symbol})")
        logger.info(f"{'='*60}")
        logger.info(f"📊 시장 데이터")
        logger.info(f"  현재가: {signal.price:,.0f}원")
        logger.info(f"  거래량: {signal.volume_ratio:.2f}x (평균 대비)")
        logger.info("")
        logger.info(f"📈 기술적 지표")
        logger.info(f"  SMA(5):  {signal.sma5:,.0f}원")
        logger.info(f"  SMA(20): {signal.sma20:,.0f}원")
        logger.info(f"  스프레드: {signal.spread_percent:.2f}%")
        if signal.rsi:
            logger.info(f"  RSI(14): {signal.rsi:.1f}")
        logger.info("")
        logger.info(f"🎯 신호 정보")
        logger.info(f"  타입: {self._get_signal_emoji(signal.signal_type)} {signal.signal_type.value}")
        logger.info(f"  확신도: {signal.confidence.value}")
        logger.info(f"  확인일수: {signal.confirmation_days}/3일")
        logger.info(f"  신호강도: {signal.strength:.0f}/100 {'💪' if signal.strength >= 70 else '👍' if signal.strength >= 50 else '👌'}")
        logger.info(f"  이유: {signal.reason}")
        logger.info(f"{'='*60}")
    
    def _simulate_order(self, signal: TradingSignal):
        """주문 시뮬레이션 (실제 주문 없음)"""
        symbol = signal.symbol
        position = self.positions.get(symbol, {})
        
        # 매수 신호
        if signal.signal_type == SignalType.GOLDEN_CROSS and not position:
            order = self.order_sim.simulate_buy_order(
                symbol=signal.symbol,
                symbol_name=signal.symbol_name,
                price=signal.price,
                investment_amount=10000000  # 1000만원
            )
            
            # 가상 포지션 업데이트
            self.positions[symbol] = {
                'quantity': order['quantity'],
                'avg_price': order['price'],
                'total_cost': order['total_cost']
            }
            
            self._log_order_simulation(order, signal)
            
        # 매도 신호
        elif signal.signal_type == SignalType.DEAD_CROSS and position:
            order = self.order_sim.simulate_sell_order(
                symbol=signal.symbol,
                symbol_name=signal.symbol_name,
                price=signal.price,
                quantity=position['quantity'],
                avg_buy_price=position['avg_price']
            )
            
            # 포지션 청산
            del self.positions[symbol]
            
            self._log_order_simulation(order, signal)
    
    def _log_order_simulation(self, order: dict, signal: TradingSignal):
        """주문 시뮬레이션 로깅"""
        logger.info("")
        logger.info(f"{'💰 매수 주문 시뮬레이션' if order['type'] == 'BUY' else '💸 매도 주문 시뮬레이션'}")
        logger.info(f"{'─'*50}")
        logger.info(f"📝 주문 정보")
        logger.info(f"  종목: {order['symbol_name']}({order['symbol']})")
        logger.info(f"  수량: {order['quantity']:,}주")
        logger.info(f"  가격: {order['price']:,}원")
        logger.info(f"  금액: {order['quantity'] * order['price']:,}원")
        
        if order['type'] == 'BUY':
            logger.info(f"  수수료: {order['commission']:,}원")
            logger.info(f"  총 비용: {order['total_cost']:,}원")
        else:
            logger.info(f"  수수료: {order['commission']:,}원")
            logger.info(f"  세금: {order['tax']:,}원")
            logger.info(f"  순 수익: {order['net_revenue']:,}원")
            logger.info(f"  수익률: {order['profit_rate']:.2f}%")
        
        logger.info("")
        logger.info(f"🚫 실제 주문 상태: 차단됨 (시뮬레이션 모드)")
        logger.info(f"📊 기록만 저장되었습니다")
        logger.info(f"{'─'*50}")
        
        # JSON 로그 저장
        self._save_order_log(order, signal)
    
    def _save_order_log(self, order: dict, signal: TradingSignal):
        """주문 로그 JSON 저장"""
        log_dir = Path("logs/orders")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = log_dir / f"{today}.json"
        
        # 기존 로그 읽기
        logs = []
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                try:
                    logs = json.load(f)
                except:
                    logs = []
        
        # 새 로그 추가
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'order': order,
            'signal': signal.to_dict()
        }
        logs.append(log_entry)
        
        # 저장
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    
    def _get_signal_emoji(self, signal_type: SignalType) -> str:
        """신호 타입별 이모지"""
        emojis = {
            SignalType.GOLDEN_CROSS: "📈",
            SignalType.DEAD_CROSS: "📉",
            SignalType.HOLD: "⏸️",
            SignalType.NONE: "⚫"
        }
        return emojis.get(signal_type, "❓")
    
    def _get_real_kis_data(self, symbol: str) -> pd.DataFrame:
        """KIS API에서 실제 시장 데이터 조회"""
        try:
            # 1년간 데이터 조회 (최근 365일)
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
            
            # KIS API 호출 (로그 간소화)
            output1, output2 = inquire_daily_itemchartprice(
                env_dv="real",
                fid_cond_mrkt_div_code="J",  # KRX
                fid_input_iscd=symbol,
                fid_input_date_1=start_date,
                fid_input_date_2=end_date,
                fid_period_div_code="D",  # 일봉
                fid_org_adj_prc="1"  # 원주가
            )
            
            if output2.empty:
                logger.warning(f"⚠️ {symbol} 데이터 없음, 더미 데이터 사용")
                return self._get_fallback_data(symbol)
            
            # KIS 데이터를 trading system 형식으로 변환
            df = pd.DataFrame()
            df['date'] = pd.to_datetime(output2['stck_bsop_date'])
            df['close'] = pd.to_numeric(output2['stck_clpr'])
            df['open'] = pd.to_numeric(output2['stck_oprc']) 
            df['high'] = pd.to_numeric(output2['stck_hgpr'])
            df['low'] = pd.to_numeric(output2['stck_lwpr'])
            df['volume'] = pd.to_numeric(output2['acml_vol'])
            
            df.set_index('date', inplace=True)
            df = df.sort_index()  # 날짜 순으로 정렬
            
            return df
            
        except Exception as e:
            logger.error(f"❌ KIS API 호출 실패 {symbol}: {e}")
            logger.info(f"🔄 더미 데이터로 대체")
            return self._get_fallback_data(symbol)
    
    def _get_fallback_data(self, symbol: str) -> pd.DataFrame:
        """API 실패시 대체 더미 데이터"""
        import numpy as np
        
        logger.info(f"📊 {symbol} 더미 데이터 생성")
        
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        np.random.seed(hash(symbol) % 100000)
        base_price = 70000 if symbol == "005930" else 50000
        
        prices = []
        price = base_price
        
        for i in range(100):
            if i < 30:
                change = np.random.uniform(-0.02, 0.01)  # 하락 추세
            elif i < 60:
                change = np.random.uniform(-0.01, 0.02)  # 상승 전환
            else:
                change = np.random.uniform(0, 0.02)  # 상승 추세
            
            price *= (1 + change)
            prices.append(price)
        
        df = pd.DataFrame({
            'date': dates,
            'close': prices,
            'open': [p * 0.99 for p in prices],
            'high': [p * 1.01 for p in prices],
            'low': [p * 0.98 for p in prices],
            'volume': np.random.randint(1000000, 5000000, 100)
        })
        
        df.set_index('date', inplace=True)
        return df

if __name__ == "__main__":
    # 테스트 실행
    symbols = {
        "005930": "삼성전자",
        "000660": "SK하이닉스"
    }
    
    monitor = SignalMonitor(symbols, check_interval=10)
    asyncio.run(monitor.start_monitoring())