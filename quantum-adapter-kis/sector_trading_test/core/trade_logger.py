"""
상세 거래 로깅 시스템
매매 결정부터 실행까지 모든 과정을 상세히 기록
"""

import logging
import json
import csv
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class TradeSignal:
    """매매 신호 데이터 클래스"""
    timestamp: str
    symbol: str
    name: str
    sector: str
    signal_type: str  # BUY, SELL, HOLD
    confidence: float  # 0.0 ~ 1.0
    strength: int     # 0 ~ 100
    
    # 기술적 분석 지표
    technical_indicators: Dict[str, Any]
    
    # 시장 상황
    market_conditions: Dict[str, Any]
    
    # 신호 근거
    reasoning: List[str]
    
    # 리스크 평가
    risk_assessment: Dict[str, Any]

@dataclass 
class TradeExecution:
    """매매 실행 데이터 클래스"""
    timestamp: str
    trade_id: str
    symbol: str
    name: str
    sector: str
    
    # 주문 정보
    action: str  # BUY, SELL
    order_type: str  # MARKET, LIMIT
    shares: int
    price: float
    total_amount: float
    
    # 수수료 및 세금
    commission: float
    tax: float
    net_amount: float
    
    # 포트폴리오 변화
    portfolio_before: Dict[str, Any]
    portfolio_after: Dict[str, Any]
    
    # 실행 결과
    execution_status: str  # SUCCESS, FAILED, PARTIAL
    execution_message: str

@dataclass
class PerformanceRecord:
    """성과 기록 데이터 클래스"""
    timestamp: str
    symbol: str
    name: str
    sector: str
    
    # 포지션 정보
    shares: int
    avg_price: float
    current_price: float
    market_value: float
    
    # 손익 정보
    unrealized_pnl: float
    unrealized_pnl_pct: float
    total_cost: float
    
    # 위험 지표
    volatility: float
    max_drawdown: float
    holding_days: int

class TradeLogger:
    """상세 거래 로깅 시스템"""
    
    def __init__(self, log_dir: Optional[Path] = None):
        """
        초기화
        
        Args:
            log_dir: 로그 디렉토리 경로
        """
        self.log_dir = log_dir or Path(__file__).parent.parent / 'logs'
        self.log_dir.mkdir(exist_ok=True)
        
        # 로거 설정
        self.logger = logging.getLogger(__name__)
        
        # 파일별 로거 설정
        self._setup_file_loggers()
        
        # 거래 기록 저장소
        self.trade_signals: List[TradeSignal] = []
        self.trade_executions: List[TradeExecution] = []
        self.performance_records: List[PerformanceRecord] = []
        
        self.logger.info("거래 로깅 시스템 초기화 완료")
    
    def _setup_file_loggers(self):
        """파일별 로거 설정"""
        # 일반 로그
        general_handler = logging.FileHandler(
            self.log_dir / f'trading_{datetime.now().strftime("%Y%m%d")}.log',
            encoding='utf-8'
        )
        general_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(general_handler)
        self.logger.setLevel(logging.INFO)
        
        # 거래 전용 로그
        self.trade_logger = logging.getLogger('trade_execution')
        trade_handler = logging.FileHandler(
            self.log_dir / f'executions_{datetime.now().strftime("%Y%m%d")}.log',
            encoding='utf-8'
        )
        trade_handler.setFormatter(
            logging.Formatter('%(asctime)s - TRADE - %(message)s')
        )
        self.trade_logger.addHandler(trade_handler)
        self.trade_logger.setLevel(logging.INFO)
        
        # 성과 전용 로그
        self.performance_logger = logging.getLogger('performance')
        performance_handler = logging.FileHandler(
            self.log_dir / f'performance_{datetime.now().strftime("%Y%m%d")}.log',
            encoding='utf-8'
        )
        performance_handler.setFormatter(
            logging.Formatter('%(asctime)s - PERF - %(message)s')
        )
        self.performance_logger.addHandler(performance_handler)
        self.performance_logger.setLevel(logging.INFO)
    
    def log_trade_signal(self, signal: TradeSignal):
        """매매 신호 로깅"""
        self.trade_signals.append(signal)
        
        # 콘솔 출력
        print(f"\n🚨 매매 신호 감지: {signal.name}({signal.symbol})")
        print(f"   신호: {signal.signal_type}")
        print(f"   확신도: {signal.confidence:.2f}")
        print(f"   강도: {signal.strength}/100")
        print(f"   섹터: {signal.sector}")
        
        # 상세 로깅
        self.logger.info(f"매매신호 - {signal.symbol}: {signal.signal_type}, 확신도: {signal.confidence:.2f}")
        
        # JSON으로 상세 정보 저장
        signal_file = self.log_dir / f'signals_{datetime.now().strftime("%Y%m%d")}.jsonl'
        with open(signal_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(signal), ensure_ascii=False, default=str) + '\n')
        
        # 신호 근거 상세 출력
        if signal.reasoning:
            print("   근거:")
            for i, reason in enumerate(signal.reasoning, 1):
                print(f"     {i}. {reason}")
        
        # 기술적 지표 출력
        if signal.technical_indicators:
            print("   기술적 지표:")
            for indicator, value in signal.technical_indicators.items():
                if isinstance(value, float):
                    print(f"     {indicator}: {value:.2f}")
                else:
                    print(f"     {indicator}: {value}")
    
    def log_trade_execution(self, execution: TradeExecution):
        """매매 실행 로깅"""
        self.trade_executions.append(execution)
        
        # 콘솔 출력
        action_emoji = "💰" if execution.action == "BUY" else "💸"
        print(f"\n{action_emoji} 매매 실행: {execution.name}({execution.symbol})")
        print(f"   동작: {execution.action}")
        print(f"   수량: {execution.shares:,}주")
        print(f"   가격: {execution.price:,}원")
        print(f"   총액: {execution.total_amount:,}원")
        print(f"   수수료: {execution.commission:,}원")
        print(f"   세금: {execution.tax:,}원")
        print(f"   순액: {execution.net_amount:,}원")
        print(f"   상태: {execution.execution_status}")
        
        # 거래 로그
        self.trade_logger.info(
            f"{execution.action} {execution.symbol} "
            f"{execution.shares}주 @{execution.price:,}원 "
            f"총액:{execution.total_amount:,}원 상태:{execution.execution_status}"
        )
        
        # CSV로 거래 기록 저장
        execution_file = self.log_dir / f'executions_{datetime.now().strftime("%Y%m%d")}.csv'
        
        # 헤더 체크 및 작성
        write_header = not execution_file.exists()
        
        with open(execution_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if write_header:
                writer.writerow([
                    'timestamp', 'trade_id', 'symbol', 'name', 'sector',
                    'action', 'order_type', 'shares', 'price', 'total_amount',
                    'commission', 'tax', 'net_amount', 'execution_status', 'execution_message'
                ])
            
            writer.writerow([
                execution.timestamp, execution.trade_id, execution.symbol, 
                execution.name, execution.sector, execution.action, execution.order_type,
                execution.shares, execution.price, execution.total_amount,
                execution.commission, execution.tax, execution.net_amount,
                execution.execution_status, execution.execution_message
            ])
        
        # 포트폴리오 변화 로깅
        if execution.portfolio_before and execution.portfolio_after:
            self._log_portfolio_change(execution.portfolio_before, execution.portfolio_after)
    
    def log_performance_record(self, record: PerformanceRecord):
        """성과 기록 로깅"""
        self.performance_records.append(record)
        
        # 성과 로그
        self.performance_logger.info(
            f"{record.symbol} 보유:{record.shares}주 "
            f"현재가:{record.current_price:,}원 "
            f"평가액:{record.market_value:,}원 "
            f"손익:{record.unrealized_pnl:+,}원({record.unrealized_pnl_pct:+.2f}%)"
        )
        
        # CSV로 성과 기록 저장
        performance_file = self.log_dir / f'performance_{datetime.now().strftime("%Y%m%d")}.csv'
        
        write_header = not performance_file.exists()
        
        with open(performance_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if write_header:
                writer.writerow([
                    'timestamp', 'symbol', 'name', 'sector', 'shares',
                    'avg_price', 'current_price', 'market_value', 
                    'unrealized_pnl', 'unrealized_pnl_pct', 'total_cost',
                    'volatility', 'max_drawdown', 'holding_days'
                ])
            
            writer.writerow([
                record.timestamp, record.symbol, record.name, record.sector,
                record.shares, record.avg_price, record.current_price, record.market_value,
                record.unrealized_pnl, record.unrealized_pnl_pct, record.total_cost,
                record.volatility, record.max_drawdown, record.holding_days
            ])
    
    def _log_portfolio_change(self, before: Dict[str, Any], after: Dict[str, Any]):
        """포트폴리오 변화 로깅"""
        print("\n📊 포트폴리오 변화:")
        
        # 총 자산 변화
        value_change = after.get('total_value', 0) - before.get('total_value', 0)
        print(f"   총 자산: {before.get('total_value', 0):,}원 → {after.get('total_value', 0):,}원 ({value_change:+,}원)")
        
        # 현금 변화
        cash_change = after.get('cash_balance', 0) - before.get('cash_balance', 0)
        print(f"   현금: {before.get('cash_balance', 0):,}원 → {after.get('cash_balance', 0):,}원 ({cash_change:+,}원)")
        
        # 현금 비중 변화
        cash_ratio_before = before.get('cash_ratio', 0)
        cash_ratio_after = after.get('cash_ratio', 0)
        print(f"   현금비중: {cash_ratio_before:.1f}% → {cash_ratio_after:.1f}%")
    
    def generate_daily_report(self, date: Optional[str] = None) -> str:
        """일일 거래 리포트 생성"""
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        
        # 해당 날짜 데이터 필터링
        daily_signals = [s for s in self.trade_signals if s.timestamp.startswith(date[:4] + '-' + date[4:6] + '-' + date[6:8])]
        daily_executions = [e for e in self.trade_executions if e.timestamp.startswith(date[:4] + '-' + date[4:6] + '-' + date[6:8])]
        
        # 리포트 생성
        report = f"""
=== 일일 거래 리포트 ({date}) ===

📊 거래 요약:
- 신호 발생: {len(daily_signals)}건
- 실행 거래: {len(daily_executions)}건
- 매수: {len([e for e in daily_executions if e.action == 'BUY'])}건
- 매도: {len([e for e in daily_executions if e.action == 'SELL'])}건

"""
        
        # 실행된 거래 상세
        if daily_executions:
            report += "🔄 실행된 거래:\n"
            for execution in daily_executions:
                status_emoji = "✅" if execution.execution_status == "SUCCESS" else "❌"
                report += f"{status_emoji} {execution.action} {execution.name}({execution.symbol}) "
                report += f"{execution.shares:,}주 @{execution.price:,}원\n"
        
        # 섹터별 신호 분석
        sector_signals = {}
        for signal in daily_signals:
            if signal.sector not in sector_signals:
                sector_signals[signal.sector] = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
            sector_signals[signal.sector][signal.signal_type] += 1
        
        if sector_signals:
            report += "\n📈 섹터별 신호 분석:\n"
            for sector, signals in sector_signals.items():
                report += f"- {sector}: 매수 {signals['BUY']}건, 매도 {signals['SELL']}건, 관망 {signals['HOLD']}건\n"
        
        # 리포트 저장
        report_file = self.log_dir / f'daily_report_{date}.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return report
    
    def export_to_excel(self, filename: Optional[str] = None):
        """Excel 파일로 전체 거래 기록 내보내기"""
        if not filename:
            filename = self.log_dir / f'trading_report_{datetime.now().strftime("%Y%m%d")}.xlsx'
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # 신호 데이터
            if self.trade_signals:
                signals_df = pd.DataFrame([asdict(s) for s in self.trade_signals])
                signals_df.to_excel(writer, sheet_name='매매신호', index=False)
            
            # 실행 데이터
            if self.trade_executions:
                executions_df = pd.DataFrame([asdict(e) for e in self.trade_executions])
                executions_df.to_excel(writer, sheet_name='매매실행', index=False)
            
            # 성과 데이터
            if self.performance_records:
                performance_df = pd.DataFrame([asdict(r) for r in self.performance_records])
                performance_df.to_excel(writer, sheet_name='성과기록', index=False)
        
        self.logger.info(f"Excel 리포트 생성: {filename}")
        return filename
    
    def get_statistics(self) -> Dict[str, Any]:
        """거래 통계 반환"""
        stats = {
            'total_signals': len(self.trade_signals),
            'total_executions': len(self.trade_executions),
            'total_performance_records': len(self.performance_records),
            'successful_executions': len([e for e in self.trade_executions if e.execution_status == 'SUCCESS']),
            'failed_executions': len([e for e in self.trade_executions if e.execution_status == 'FAILED']),
        }
        
        if self.trade_executions:
            successful_executions = [e for e in self.trade_executions if e.execution_status == 'SUCCESS']
            stats['success_rate'] = len(successful_executions) / len(self.trade_executions) * 100
            
            if successful_executions:
                total_amount = sum(e.total_amount for e in successful_executions)
                total_commission = sum(e.commission for e in successful_executions)
                total_tax = sum(e.tax for e in successful_executions)
                
                stats['total_amount'] = total_amount
                stats['total_commission'] = total_commission
                stats['total_tax'] = total_tax
                stats['avg_commission_rate'] = (total_commission / total_amount * 100) if total_amount > 0 else 0
        
        return stats


# 테스트 및 디버깅용
if __name__ == "__main__":
    # 로거 테스트
    logger = TradeLogger()
    
    # 샘플 신호 생성
    signal = TradeSignal(
        timestamp=datetime.now().isoformat(),
        symbol="005930",
        name="삼성전자",
        sector="반도체",
        signal_type="BUY",
        confidence=0.85,
        strength=78,
        technical_indicators={
            "RSI": 32.5,
            "MACD": "골든크로스",
            "볼린저밴드": "하단터치"
        },
        market_conditions={
            "시장추세": "상승",
            "거래량": "평균대비 1.8배"
        },
        reasoning=[
            "RSI 과매도 구간에서 반등 신호",
            "MACD 골든크로스 발생",
            "반도체 섹터 모멘텀 강화"
        ],
        risk_assessment={
            "위험도": "중간",
            "변동성": "높음",
            "손절가": 65000
        }
    )
    
    logger.log_trade_signal(signal)
    
    print("\n테스트 완료 - logs 폴더 확인")