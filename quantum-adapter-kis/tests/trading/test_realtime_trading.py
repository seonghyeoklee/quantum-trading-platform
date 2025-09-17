#!/usr/bin/env python3
"""
실시간 자동매매 시스템 테스트
각 모듈의 기능을 개별적으로 테스트하고 통합 테스트를 수행
"""

import asyncio
import logging
from datetime import datetime, timedelta
import random
from pathlib import Path

# 테스트할 모듈들
from realtime_ws_client import RealtimeWebSocketClient
from streaming_technical_analysis import StreamingTechnicalAnalysis
from trading_strategy_engine import TradingStrategyEngine
from realtime_auto_trader import RealtimeAutoTrader

class RealtimeTradingTester:
    """실시간 자동매매 시스템 테스트 클래스"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

    async def test_websocket_client(self):
        """WebSocket 클라이언트 테스트"""
        print("🔌 WebSocket 클라이언트 테스트 시작")
        print("="*50)

        client = RealtimeWebSocketClient("vps")

        # 가격 업데이트 콜백
        received_data = []

        async def on_price_update(data):
            received_data.append(data)
            symbol = data.get('symbol', 'N/A')
            price = data.get('current_price', 0)
            change = data.get('change', 0)
            sign = "+" if change >= 0 else ""
            print(f"📊 [{symbol}] {price:,}원 ({sign}{change:,})")

        client.set_price_callback(on_price_update)

        try:
            # 연결 테스트
            if await client.connect():
                print("✅ WebSocket 연결 성공")

                # 구독 테스트
                test_symbols = ['005930', '035420']  # 삼성전자, NAVER
                await client.subscribe_multiple(test_symbols)

                # 10초간 데이터 수신
                print("📡 10초간 실시간 데이터 수신...")
                await asyncio.sleep(10)

                print(f"✅ 수신된 데이터: {len(received_data)}건")

            else:
                print("❌ WebSocket 연결 실패")

        except Exception as e:
            print(f"❌ 테스트 오류: {e}")

        finally:
            await client.disconnect()

        print("✅ WebSocket 클라이언트 테스트 완료\n")

    def test_technical_analysis(self):
        """기술적 분석 모듈 테스트"""
        print("📊 기술적 분석 모듈 테스트 시작")
        print("="*50)

        analyzer = StreamingTechnicalAnalysis("005930")

        # 가상의 가격 데이터로 테스트
        print("📈 가상 가격 데이터로 지표 계산 테스트")

        base_price = 71000
        prices = []

        # 상승 패턴 생성
        for i in range(30):
            if i < 10:
                # 초기 하락
                price = base_price - (i * 100) + random.randint(-50, 50)
            elif i < 20:
                # 반등 상승 (골든크로스 유도)
                price = base_price - 1000 + ((i-10) * 150) + random.randint(-30, 30)
            else:
                # 지속 상승
                price = base_price + ((i-20) * 80) + random.randint(-40, 40)

            prices.append(price)
            analyzer.add_price_data(price, volume=1000 * (i + 1))

            # 5건마다 상태 출력
            if (i + 1) % 5 == 0:
                indicators = analyzer.get_current_indicators()
                patterns = analyzer.detect_patterns()

                print(f"\n--- Step {i+1}: 가격 {price:,}원 ---")
                print(f"RSI: {indicators.get('rsi', 'N/A')}")
                print(f"MA5: {indicators.get('ma5', 'N/A')}")
                print(f"MA20: {indicators.get('ma20', 'N/A')}")

                if patterns:
                    for pattern in patterns:
                        print(f"🎯 패턴: {pattern['pattern']} - {pattern['signal']} (신뢰도: {pattern['confidence']})")

        # 추세 분석
        trend = analyzer.get_trend_direction()
        print(f"\n📈 최종 추세: {trend['direction']} (신뢰도: {trend['confidence']:.2f})")

        # 지지/저항선
        levels = analyzer.get_support_resistance_levels()
        print(f"📊 저항선: {levels['resistance']}")
        print(f"📊 지지선: {levels['support']}")

        print("✅ 기술적 분석 모듈 테스트 완료\n")

    def test_strategy_engine(self):
        """전략 엔진 테스트"""
        print("🎯 전략 엔진 테스트 시작")
        print("="*50)

        # 설정 파일 경로
        config_path = Path(__file__).parent / "trading_strategies.yaml"
        engine = TradingStrategyEngine(str(config_path) if config_path.exists() else None)

        print(f"활성화된 전략: {[name for name, enabled in engine.get_strategy_status().items() if enabled]}")

        # 기술적 분석기 생성
        analyzer = StreamingTechnicalAnalysis("005930")

        # 골든크로스 시나리오 생성
        print("\n📈 골든크로스 시나리오 테스트")

        # MA5 < MA20 상태 생성
        prices = [70000, 69800, 69600, 69900, 70100]
        for price in prices:
            analyzer.add_price_data(price, volume=1000)

        # MA5 > MA20 돌파 상황 생성
        breakout_prices = [70300, 70600, 70900, 71200, 71500]
        for i, price in enumerate(breakout_prices):
            analyzer.add_price_data(price, volume=2000 + i*100)

            # 신호 생성
            signals = engine.generate_signals(analyzer)

            if signals:
                best_signal = engine.get_best_signal(signals)
                print(f"\n🎯 신호 발생!")
                print(f"   전략: {best_signal.strategy_name}")
                print(f"   타입: {best_signal.signal_type}")
                print(f"   신뢰도: {best_signal.confidence:.2f}")
                print(f"   가격: {best_signal.entry_price:,}원")
                print(f"   근거: {', '.join(best_signal.reasoning)}")

        # RSI 과매도 시나리오
        print("\n📉 RSI 과매도 시나리오 테스트")

        # 급락 시나리오
        crash_prices = [71500, 70800, 70200, 69500, 68900, 68300, 67800]
        for price in crash_prices:
            analyzer.add_price_data(price, volume=3000)

        signals = engine.generate_signals(analyzer)
        if signals:
            for signal in signals:
                print(f"🎯 {signal.strategy_name}: {signal.signal_type} (신뢰도: {signal.confidence:.2f})")

        # 성과 분석
        performance = engine.analyze_signal_performance()
        print(f"\n📊 성과 분석:")
        print(f"   총 신호: {performance.get('total_signals', 0)}건")
        print(f"   전략별: {performance.get('strategy_counts', {})}")

        print("✅ 전략 엔진 테스트 완료\n")

    async def test_integration(self):
        """통합 테스트 (실제 자동매매 시스템 시뮬레이션)"""
        print("🚀 통합 테스트 시작")
        print("="*50)

        # 설정 파일 사용
        config_path = Path(__file__).parent / "trading_strategies.yaml"

        # 자동매매 시스템 생성 (모의투자, 수동 모드)
        trader = RealtimeAutoTrader(
            environment="vps",
            config_path=str(config_path) if config_path.exists() else None,
            auto_mode=False  # 테스트에서는 수동 모드
        )

        # 초기화 테스트
        print("🔧 시스템 초기화 테스트...")
        try:
            # 실제 WebSocket 연결은 하지 않고 구성만 테스트
            trader.ws_client = None  # WebSocket 연결 비활성화
            trader.executor.is_authenticated = True  # 인증 시뮬레이션

            # 가상 종목 설정
            trader.target_symbols = ['005930', '035420']

            # 분석기 초기화
            for symbol in trader.target_symbols:
                trader.analyzers[symbol] = StreamingTechnicalAnalysis(symbol)

            print("✅ 초기화 완료")

        except Exception as e:
            print(f"❌ 초기화 실패: {e}")
            return

        # 가상 데이터로 신호 생성 테스트
        print("\n📊 가상 데이터로 신호 생성 테스트...")

        # 삼성전자 가격 변동 시뮬레이션
        samsung_prices = [71000, 71200, 71500, 71800, 72100, 72400, 72200, 72600]

        for i, price in enumerate(samsung_prices):
            symbol = "005930"
            analyzer = trader.analyzers[symbol]

            # 가격 데이터 추가
            analyzer.add_price_data(price, volume=1000 * (i + 1))

            # 신호 처리 시뮬레이션
            signals = trader.strategy_engine.generate_signals(analyzer)

            if signals:
                best_signal = trader.strategy_engine.get_best_signal(signals)
                print(f"\n🎯 Step {i+1}: 신호 발생!")
                print(f"   종목: {best_signal.symbol}")
                print(f"   가격: {price:,}원")
                print(f"   신호: {best_signal.signal_type}")
                print(f"   전략: {best_signal.strategy_name}")
                print(f"   신뢰도: {best_signal.confidence:.2f}")

                # 매매 조건 검증 테스트
                # is_valid = await trader._validate_trading_conditions(best_signal)
                # print(f"   매매 가능: {'✅' if is_valid else '❌'}")

        print("✅ 통합 테스트 완료\n")

    async def test_config_loading(self):
        """설정 파일 로딩 테스트"""
        print("⚙️ 설정 파일 로딩 테스트")
        print("="*50)

        config_path = Path(__file__).parent / "trading_strategies.yaml"

        if config_path.exists():
            print(f"✅ 설정 파일 발견: {config_path}")

            engine = TradingStrategyEngine(str(config_path))
            status = engine.get_strategy_status()

            print("전략 상태:")
            for name, enabled in status.items():
                status_icon = "🟢" if enabled else "🔴"
                print(f"   {status_icon} {name}: {'활성화' if enabled else '비활성화'}")

        else:
            print(f"⚠️ 설정 파일 없음: {config_path}")
            print("기본 설정으로 엔진 생성...")

            engine = TradingStrategyEngine()
            status = engine.get_strategy_status()

            print("기본 전략 상태:")
            for name, enabled in status.items():
                status_icon = "🟢" if enabled else "🔴"
                print(f"   {status_icon} {name}: {'활성화' if enabled else '비활성화'}")

        print("✅ 설정 파일 테스트 완료\n")

    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("🧪 실시간 자동매매 시스템 종합 테스트")
        print("="*60)
        print(f"테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        tests = [
            ("설정 파일 로딩", self.test_config_loading),
            ("기술적 분석 모듈", self.test_technical_analysis),
            ("전략 엔진", self.test_strategy_engine),
            ("통합 테스트", self.test_integration),
            # ("WebSocket 클라이언트", self.test_websocket_client),  # 실제 연결 필요
        ]

        for test_name, test_func in tests:
            try:
                print(f"\n🔍 {test_name} 테스트 실행 중...")
                if asyncio.iscoroutinefunction(test_func):
                    await test_func()
                else:
                    test_func()
                print(f"✅ {test_name} 테스트 통과")

            except Exception as e:
                print(f"❌ {test_name} 테스트 실패: {e}")
                import traceback
                traceback.print_exc()

        print("\n" + "="*60)
        print("🎉 모든 테스트 완료!")
        print("="*60)

        # 실제 자동매매 실행 안내
        print("\n📋 실제 자동매매 실행 방법:")
        print("   모의투자 (수동): python realtime_auto_trader.py")
        print("   모의투자 (자동): python realtime_auto_trader.py --auto")
        print("   실전투자 (수동): python realtime_auto_trader.py --prod")
        print("   실전투자 (자동): python realtime_auto_trader.py --prod --auto")
        print("   설정파일 지정: python realtime_auto_trader.py --config trading_strategies.yaml")

if __name__ == "__main__":
    tester = RealtimeTradingTester()
    asyncio.run(tester.run_all_tests())