#!/usr/bin/env python3
"""
자동매매 시스템 간단 테스트 스크립트 (터미널 UI 없음)
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auto_trading_system.core.trading_engine import AutoTradingEngine
from auto_trading_system.core.order_executor import OrderExecutor
from auto_trading_system.core.risk_manager import RiskManager
from auto_trading_system.core.data_types import MarketData, SignalType
from auto_trading_system.strategies import create_strategy


def setup_test_logging():
    """테스트용 로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def test_trading_engine():
    """트레이딩 엔진 테스트"""
    print("=" * 60)
    print("트레이딩 엔진 테스트")
    print("=" * 60)

    # 엔진 생성
    engine_config = {
        'max_positions': 3,
        'default_quantity': 100,
        'execution_delay': 0.1
    }

    risk_config = {
        'max_daily_trades': 5,
        'min_confidence_threshold': 0.6
    }

    engine = AutoTradingEngine(engine_config)
    engine.config['risk_config'] = risk_config

    print(f"✓ 트레이딩 엔진 생성 완료")
    print(f"  - 최대 포지션: {engine.max_positions}")
    print(f"  - 기본 수량: {engine.default_quantity}")

    # 전략 생성 및 종목 추가
    golden_cross_strategy = create_strategy('golden_cross', {
        'fast_period': 5,
        'slow_period': 20,
        'min_confidence': 0.7
    })

    rsi_strategy = create_strategy('rsi', {
        'rsi_period': 14,
        'oversold_threshold': 30,
        'overbought_threshold': 70
    })

    engine.add_stock('005930', golden_cross_strategy)
    engine.add_stock('035420', rsi_strategy)

    print(f"✓ 종목 추가 완료")
    print(f"  - 005930: {golden_cross_strategy.name}")
    print(f"  - 035420: {rsi_strategy.name}")

    return engine


async def test_market_data_processing(engine):
    """시장 데이터 처리 테스트"""
    print("\n" + "=" * 60)
    print("시장 데이터 처리 테스트")
    print("=" * 60)

    # 샘플 데이터
    test_data = [
        ('005930', MarketData(
            symbol='005930',
            timestamp=datetime.now(),
            current_price=75000,
            open_price=74500,
            high_price=75500,
            low_price=74000,
            volume=1000000
        )),
        ('035420', MarketData(
            symbol='035420',
            timestamp=datetime.now(),
            current_price=190000,
            open_price=188000,
            high_price=192000,
            low_price=187000,
            volume=500000
        ))
    ]

    for symbol, market_data in test_data:
        print(f"\n📊 {symbol} 데이터 처리:")
        print(f"  현재가: {market_data.current_price:,}원")
        print(f"  거래량: {market_data.volume:,}주")

        # 신호 생성
        signal = await engine.update_market_data(symbol, market_data)

        if signal:
            print(f"  ✅ 신호: {signal.signal_type.value}")
            print(f"  신뢰도: {signal.confidence:.2f}")
            print(f"  이유: {signal.reason}")
        else:
            print(f"  ⏸️ 신호 없음")


async def test_order_executor():
    """주문 실행기 테스트"""
    print("\n" + "=" * 60)
    print("주문 실행기 테스트")
    print("=" * 60)

    executor_config = {
        'environment': 'vps',
        'dry_run': True,
        'execution_delay': 0.1
    }

    executor = OrderExecutor(executor_config)

    print(f"✓ 주문 실행기 생성 완료")
    print(f"  - 환경: {executor.environment}")
    print(f"  - 드라이런: {executor.dry_run}")
    print(f"  - 연결 상태: {executor.is_connected}")

    # 실행 통계 확인
    stats = executor.get_execution_stats()
    print(f"  - 총 주문: {stats['total_orders']}")
    print(f"  - 성공률: {stats['success_rate']:.1f}%")

    return executor


async def test_strategy_execution():
    """전략 실행 테스트"""
    print("\n" + "=" * 60)
    print("전략 실행 테스트")
    print("=" * 60)

    # Golden Cross 전략 테스트
    strategy = create_strategy('golden_cross', {
        'fast_period': 5,
        'slow_period': 20,
        'min_confidence': 0.7
    })

    print(f"✓ {strategy.name} 전략 생성")
    print(f"  - 단기 기간: {strategy.fast_period}")
    print(f"  - 장기 기간: {strategy.slow_period}")

    # 가격 데이터 시뮬레이션
    price_data = [72000, 73000, 74000, 75000, 76000, 77000, 78000, 79000, 80000, 81000]

    print("\n📈 가격 데이터로 신호 생성 테스트:")
    for i, price in enumerate(price_data):
        market_data = MarketData(
            symbol='TEST',
            timestamp=datetime.now(),
            current_price=price,
            open_price=price,
            high_price=price + 500,
            low_price=price - 500,
            volume=100000
        )

        signal = strategy.analyze_signal(market_data)

        if signal and signal.signal_type != SignalType.NONE:
            print(f"  Day {i+1}: {price:,}원 → {signal.signal_type.value} "
                  f"(신뢰도: {signal.confidence:.2f})")


async def test_risk_management():
    """리스크 관리 테스트"""
    print("\n" + "=" * 60)
    print("리스크 관리 테스트")
    print("=" * 60)

    risk_config = {
        'max_daily_trades': 5,
        'max_position_size': 1000000,
        'min_confidence_threshold': 0.6,
        'trading_start_time': '09:00',
        'trading_end_time': '15:30'
    }

    risk_manager = RiskManager(risk_config)

    print(f"✓ 리스크 관리자 생성 완료")
    print(f"  - 일일 최대 거래: {risk_manager.max_daily_trades}")
    print(f"  - 최대 포지션: {risk_manager.max_position_size:,}원")
    print(f"  - 최소 신뢰도: {risk_manager.min_confidence_threshold}")
    print(f"  - 거래 허용: {risk_manager.is_trading_allowed()}")

    # 리스크 지표 조회
    metrics = risk_manager.get_risk_metrics()
    print(f"\n📊 리스크 지표:")
    print(f"  - 거래 허용 상태: {metrics['is_trading_allowed']}")
    print(f"  - 일일 거래 사용률: {metrics['daily_trade_usage']:.1f}%")
    print(f"  - 총 위반 건수: {metrics['total_violations']}")


async def main():
    """메인 테스트 함수"""
    print("🚀 자동매매 시스템 간단 테스트 시작")
    print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    setup_test_logging()

    try:
        # 1. 트레이딩 엔진 테스트
        engine = await test_trading_engine()

        # 2. 시장 데이터 처리 테스트
        await test_market_data_processing(engine)

        # 3. 주문 실행기 테스트
        await test_order_executor()

        # 4. 전략 실행 테스트
        await test_strategy_execution()

        # 5. 리스크 관리 테스트
        await test_risk_management()

        print("\n" + "=" * 60)
        print("✅ 모든 테스트 완료!")
        print("=" * 60)

        print("\n📝 테스트 결과:")
        print("  - 트레이딩 엔진: ✅")
        print("  - 데이터 처리: ✅")
        print("  - 주문 실행기: ✅")
        print("  - 전략 시스템: ✅")
        print("  - 리스크 관리: ✅")

        print(f"\n🎯 자동매매 시스템이 정상적으로 작동합니다!")

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        logging.exception("테스트 중 오류 발생")
        return False

    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ 테스트 중단됨")
        sys.exit(1)