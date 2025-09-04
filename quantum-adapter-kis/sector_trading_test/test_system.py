#!/usr/bin/env python3
"""
시스템 테스트 스크립트
실제 KIS API 없이 시스템의 기본 동작을 테스트
"""

import sys
from pathlib import Path

# 모듈 경로 추가
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from core.sector_portfolio import SectorPortfolio
from core.trade_logger import TradeLogger, TradeSignal
from datetime import datetime

def test_portfolio_system():
    """포트폴리오 시스템 테스트"""
    print("🧪 포트폴리오 시스템 테스트")
    print("="*50)
    
    # 포트폴리오 초기화
    portfolio = SectorPortfolio()
    
    # 기본 정보 확인
    print("✅ 포트폴리오 초기화 완료")
    print(f"   초기 자금: {portfolio.cash_balance:,}원")
    print(f"   섹터 수: {len(portfolio.get_sector_info())}")
    
    # 목표 배분 확인
    target_allocation = portfolio.get_target_allocation()
    print(f"\n📊 목표 섹터 배분:")
    for sector, weight in target_allocation.items():
        print(f"   {sector}: {weight:.1f}%")
    
    # 모의 거래 실행
    print(f"\n💰 모의 거래 테스트:")
    
    # 삼성전자 매수
    portfolio.update_position("005930", 10, 70000, "BUY")
    print(f"   삼성전자 10주 매수 (70,000원)")
    
    # 네이버 매수  
    portfolio.update_position("035420", 5, 180000, "BUY")
    print(f"   네이버 5주 매수 (180,000원)")
    
    # 포트폴리오 상태 확인
    summary = portfolio.get_portfolio_summary()
    print(f"\n📈 포트폴리오 요약:")
    print(f"   총 자산: {summary['total_value']:,}원")
    print(f"   현금: {summary['cash_balance']:,}원")
    print(f"   투자금: {summary['invested_amount']:,}원")
    print(f"   보유 종목: {summary['position_count']}개")
    
    # 섹터별 현황
    current_allocation = portfolio.calculate_current_allocation()
    print(f"\n🎯 현재 섹터 배분:")
    for sector, weight in current_allocation.items():
        if weight > 0:
            print(f"   {sector}: {weight:.1f}%")
    
    # 리밸런싱 신호
    rebalancing_signals = portfolio.get_rebalancing_signals()
    if rebalancing_signals:
        print(f"\n⚖️ 리밸런싱 신호:")
        for sector, signal in rebalancing_signals.items():
            print(f"   {sector}: {signal['action']} (차이: {signal['difference']:+.1f}%)")
    
    print("✅ 포트폴리오 시스템 테스트 완료\n")
    return portfolio

def test_logging_system():
    """로깅 시스템 테스트"""
    print("🧪 로깅 시스템 테스트") 
    print("="*50)
    
    # 로거 초기화
    trade_logger = TradeLogger()
    print("✅ 로거 초기화 완료")
    
    # 샘플 신호 생성
    signal = TradeSignal(
        timestamp=datetime.now().isoformat(),
        symbol="012450",
        name="한화에어로스페이스",
        sector="방산",
        signal_type="BUY",
        confidence=0.78,
        strength=82,
        technical_indicators={
            "RSI": 28.3,
            "MACD": "골든크로스",
            "거래량": "평균 대비 2.1배"
        },
        market_conditions={
            "시장추세": "상승",
            "섹터모멘텀": "강세",
            "변동성": "높음"
        },
        reasoning=[
            "KF-21 양산 본격화",
            "폴란드 추가 수주 기대",
            "방산 수출 정책 지원"
        ],
        risk_assessment={
            "위험도": "중간",
            "정책리스크": "낮음",
            "유동성": "양호"
        }
    )
    
    # 신호 로깅
    trade_logger.log_trade_signal(signal)
    print("✅ 매매 신호 로깅 완료")
    
    # 통계 확인
    stats = trade_logger.get_statistics()
    print(f"\n📊 로깅 통계:")
    print(f"   신호 기록: {stats['total_signals']}건")
    print(f"   실행 기록: {stats['total_executions']}건")
    
    print("✅ 로깅 시스템 테스트 완료\n")
    return trade_logger

def test_integration():
    """통합 테스트"""
    print("🧪 통합 시스템 테스트")
    print("="*50)
    
    # 시스템 컴포넌트 초기화
    portfolio = SectorPortfolio()
    trade_logger = TradeLogger()
    
    print("✅ 시스템 컴포넌트 초기화 완료")
    
    # 6개 섹터별 모의 신호 생성
    sectors_info = portfolio.get_sector_info()
    
    for sector_name, sector_data in sectors_info.items():
        primary_stock = sector_data['stocks']['primary']
        
        # 모의 신호 생성
        signal = TradeSignal(
            timestamp=datetime.now().isoformat(),
            symbol=primary_stock['symbol'],
            name=primary_stock['name'],
            sector=sector_name,
            signal_type="BUY",
            confidence=0.65 + (hash(primary_stock['symbol']) % 20) / 100,  # 0.65-0.84
            strength=60 + (hash(primary_stock['symbol']) % 30),  # 60-89
            technical_indicators={
                "현재가": "시장가",
                "추세": "상승" if hash(primary_stock['symbol']) % 2 else "횡보"
            },
            market_conditions={
                "테마": sector_data['theme']
            },
            reasoning=[primary_stock['reason']],
            risk_assessment={"위험도": "보통"}
        )
        
        trade_logger.log_trade_signal(signal)
        print(f"   📊 {sector_name} 신호 생성: {primary_stock['name']}")
    
    # 최종 통계
    stats = trade_logger.get_statistics()
    summary = portfolio.get_portfolio_summary()
    
    print(f"\n🎯 통합 테스트 결과:")
    print(f"   생성된 신호: {stats['total_signals']}건")
    print(f"   대상 섹터: {len(sectors_info)}개")
    print(f"   포트폴리오 준비: ✅")
    print(f"   로깅 시스템: ✅")
    
    print("✅ 통합 시스템 테스트 완료\n")

def main():
    """메인 테스트 실행"""
    print("🚀 섹터 분산투자 시스템 테스트")
    print("="*60)
    print("ℹ️ 실제 KIS API 연동 없이 시스템 기능만 테스트합니다.")
    print("="*60)
    
    try:
        # 개별 컴포넌트 테스트
        portfolio = test_portfolio_system()
        trade_logger = test_logging_system()
        
        # 통합 테스트
        test_integration()
        
        print("🎉 모든 테스트 완료!")
        print("="*60)
        print("✅ 시스템이 정상적으로 작동합니다.")
        print("📝 실제 매매 테스트는 manual_trader.py로 진행하세요.")
        print("   - 모의투자: python manual_trader.py")
        print("   - 분석만: python manual_trader.py --analysis")
        print("="*60)
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()