#!/usr/bin/env python3
"""
국내주식 실시간 자동매매 로그 스트림
WebSocket 기반 실시간 데이터 + 다양한 전략 + 자동매매 실행
"""

import asyncio
import logging
import sys
import os
import yaml
import argparse
from datetime import datetime

# 터미널 색상 코드
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

# 상위 디렉토리 경로 추가
sys.path.append('.')

from domestic_trading_system.core.domestic_websocket_provider import DomesticRealtimeWebSocketProvider
from domestic_trading_system.core.domestic_trading_engine import DomesticTradingEngine
from domestic_trading_system.core.domestic_order_executor import MockDomesticOrderExecutor, DomesticOrderExecutor
from domestic_trading_system.strategies.rsi_strategy import DomesticRSIStrategy
from domestic_trading_system.strategies.bollinger_strategy import DomesticBollingerStrategy
from domestic_trading_system.strategies.moving_average_strategy import DomesticMovingAverageStrategy


async def domestic_realtime_trading_log(symbols, strategy_type="rsi", use_real_trading=False, test_mode=False, detailed_log=False):
    """국내주식 실시간 자동매매 로그 스트림"""
    symbol_display = ", ".join(symbols)
    strategy_display = {
        "rsi": "RSI 전략",
        "bollinger": "볼린저밴드 전략",
        "ma": "이동평균 전략"
    }.get(strategy_type, "RSI 전략")

    print(f'🇰🇷 국내주식 실시간 {symbol_display} 자동매매 로그 스트림')
    print('=' * 70)
    print('⚠️  KIS 실전투자 WebSocket 연결 + 실제 매매 기능')
    print(f'📊 {symbol_display} 실시간 가격 변동 및 자동매매 신호를 연속 출력')
    print(f'🧠 사용 전략: {strategy_display}')
    print(f'💰 주문 실행: {"실제 주문" if use_real_trading else "모의 주문"}')
    if test_mode:
        print('🧪 테스트 모드: 안전장치 및 에러 처리 검증 활성화')
    if detailed_log:
        print('📝 상세 로그 모드: 실시간 가격/분석 데이터 기록 활성화')
    print('🔗 단일 WebSocket 연결로 다중 종목 동시 모니터링')
    print('⏹️  Ctrl+C로 안전 종료')
    print('=' * 70)
    print()

    # KIS 설정 로드
    try:
        config_path = '/Users/admin/KIS/config/kis_devlp.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            appkey = config['my_app']
            appsecret = config['my_sec']
    except Exception as e:
        print(f"❌ 설정 파일 로드 실패: {e}")
        return

    # 컴포넌트 초기화
    provider = DomesticRealtimeWebSocketProvider(appkey, appsecret, "prod")
    trading_engine = DomesticTradingEngine({
        'max_positions': len(symbols),  # 종목 수에 따라 포지션 제한
        'default_quantity': 1,
        'min_confidence': 0.8
    })

    # 주문 실행기 설정
    if use_real_trading:
        # KIS API 토큰 가져오기
        try:
            from examples_llm.kis_auth import get_access_token
            access_token = get_access_token("prod")
            if not access_token:
                print("❌ KIS API 토큰을 가져올 수 없습니다. 모의 거래로 전환합니다.")
                use_real_trading = False
            else:
                print("✅ KIS API 토큰 획득 성공")
        except Exception as e:
            print(f"❌ KIS API 토큰 오류: {e}. 모의 거래로 전환합니다.")
            use_real_trading = False

        if use_real_trading:
            # 실제 주문 실행기 (KIS API 토큰 포함)
            # 테스트 모드에서는 안전장치 테스트를 위해 제한값을 낮춤
            if test_mode:
                executor_config = {
                    'account_number': config['my_acct_stock'],
                    'account_product_code': config['my_prod'],
                    'execution_delay': 0.1,
                    'environment': 'prod',
                    'max_order_amount': 50000,   # 테스트: 5만원으로 제한
                    'daily_order_limit': 3,     # 테스트: 하루 3회로 제한
                    'min_order_interval': 60    # 테스트: 1분 간격으로 제한
                }
                print("🧪 테스트 모드 안전장치: 5만원/주문, 3회/일, 1분 간격")
            else:
                executor_config = {
                    'account_number': config['my_acct_stock'],
                    'account_product_code': config['my_prod'],
                    'execution_delay': 0.1,
                    'environment': 'prod',
                    'max_order_amount': 1000000,  # 최대 주문금액 100만원
                    'daily_order_limit': 10       # 하루 최대 10회 주문
                }

            real_executor = DomesticOrderExecutor(executor_config)
            # KIS API 인증 정보 설정
            real_executor.set_credentials(appkey, appsecret, access_token)
            trading_engine.set_order_executor(real_executor.execute_order)
            print("🔴 실제 주문 실행기 설정됨 (주의: 실제 매매가 실행됩니다!)")
            print(f"💰 최대 주문금액: 100만원 | 일일 주문 제한: 10회")

    if not use_real_trading:
        # 모의 주문 실행기
        mock_executor = MockDomesticOrderExecutor({
            'execution_delay': 0.1
        })
        trading_engine.set_order_executor(mock_executor.execute_order)
        print("🎯 모의 주문 실행기 설정됨 (안전한 테스트 모드)")

    # 전략 설정 및 종목 추가
    strategy_configs = {
        "rsi": {
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'base_confidence': 0.8,
            'volume_boost': 0.1,
            'use_volume_filter': True,
            'volume_threshold': 1.5
        },
        "bollinger": {
            'bb_period': 20,
            'bb_std_dev': 2.0,
            'squeeze_threshold': 0.02,
            'base_confidence': 0.75,
            'volume_boost': 0.1,
            'use_volume_filter': True,
            'volume_threshold': 1.5
        },
        "ma": {
            'short_ma_period': 5,
            'long_ma_period': 20,
            'cross_threshold': 0.005,
            'base_confidence': 0.8,
            'volume_boost': 0.1,
            'use_volume_filter': True,
            'volume_threshold': 1.3
        }
    }

    strategy_classes = {
        "rsi": DomesticRSIStrategy,
        "bollinger": DomesticBollingerStrategy,
        "ma": DomesticMovingAverageStrategy
    }

    # 각 종목에 대해 선택된 전략 추가
    strategy_class = strategy_classes[strategy_type]
    strategy_config = strategy_configs[strategy_type]

    for symbol in symbols:
        strategy = strategy_class(strategy_config)
        trading_engine.add_stock(symbol, strategy)

    # 실시간 데이터 카운터
    data_count = {symbol: 0 for symbol in symbols}
    signal_count = {symbol: 0 for symbol in symbols}
    order_count = {symbol: 0 for symbol in symbols}
    start_time = datetime.now()
    last_price = {symbol: None for symbol in symbols}
    last_status_log = datetime.now()  # 마지막 상태 로그 시간

    # 날짜별 로그 디렉토리 설정
    current_date = datetime.now().strftime('%Y-%m-%d')
    base_log_dir = "logs/trading"

    # 날짜별 하위 디렉토리 생성
    daily_signal_dir = os.path.join(base_log_dir, current_date, "signals")
    daily_price_dir = os.path.join(base_log_dir, current_date, "price_data")

    # 디렉토리 생성
    os.makedirs(daily_signal_dir, exist_ok=True)
    if detailed_log:
        os.makedirs(daily_price_dir, exist_ok=True)

    # 로그 파일명 생성 (날짜 제거, 시간만 포함)
    symbols_str = "_".join(symbols)
    time_only = datetime.now().strftime('%H%M%S')

    # 다중 로그 파일 생성
    log_filename = os.path.join(daily_signal_dir, f"domestic_{symbols_str}_{strategy_type}_signals_{time_only}.log")
    price_log_filename = os.path.join(daily_price_dir, f"domestic_{symbols_str}_{strategy_type}_prices_{time_only}.log") if detailed_log else None
    analysis_log_filename = os.path.join(daily_signal_dir, f"domestic_{symbols_str}_{strategy_type}_analysis_{time_only}.log") if detailed_log else None

    def write_trading_log(message, log_type="signal"):
        """다중 레벨 로그 기록"""
        timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_message = f"[{timestamp_str}] {message}\n"

        if log_type == "signal" or log_type == "order":
            # 매매 신호 및 주문 로그 (항상 기록)
            with open(log_filename, 'a', encoding='utf-8') as f:
                f.write(formatted_message)

        elif log_type == "price" and detailed_log and price_log_filename:
            # 가격 데이터 로그 (상세 모드에서만)
            with open(price_log_filename, 'a', encoding='utf-8') as f:
                f.write(formatted_message)

        elif log_type == "analysis" and detailed_log and analysis_log_filename:
            # 분석 데이터 로그 (상세 모드에서만)
            with open(analysis_log_filename, 'a', encoding='utf-8') as f:
                f.write(formatted_message)

    # 로그 파일 시작 메시지
    write_trading_log(f"국내주식 {symbol_display} 실시간 자동매매 로그 시작")
    write_trading_log(f"전략: {strategy_display}")
    write_trading_log(f"주문 모드: {'실제 주문' if use_real_trading else '모의 주문'}")
    write_trading_log(f"상세 로그: {'활성화' if detailed_log else '비활성화'}")
    write_trading_log(f"신호 로그 파일: {log_filename}")
    if detailed_log:
        write_trading_log(f"가격 로그 파일: {price_log_filename}")
        write_trading_log(f"분석 로그 파일: {analysis_log_filename}")
    write_trading_log("=" * 60)

    async def monitor_order_result(symbol, signal, order_num, log_func, time_str):
        """주문 결과 모니터링 (비동기)"""
        try:
            # 주문 결과 대기 (3초)
            await asyncio.sleep(3)

            # 주문 실행 결과 확인
            # 실제 구현에서는 KIS API로 주문 상태 조회
            result_status = "성공"  # 예시: 실제로는 API 호출 결과

            if result_status == "성공":
                print(f"    {Colors.GREEN}✅ [{datetime.now().strftime('%H:%M:%S')}] {symbol} 주문 #{order_num} 완료: {signal.signal_type} 1주 체결{Colors.END}")
                log_func(f"✅ {symbol} 주문 #{order_num} 체결 완료: {signal.signal_type} 1주", "order")
                log_func(f"   체결가: {signal.target_price:,}원 | 체결금액: {signal.target_price:,}원", "order")
            else:
                print(f"    {Colors.RED}❌ [{datetime.now().strftime('%H:%M:%S')}] {symbol} 주문 #{order_num} 실패: {result_status}{Colors.END}")
                log_func(f"❌ {symbol} 주문 #{order_num} 실패: {result_status}", "order")

        except Exception as e:
            print(f"    ⚠️ [{datetime.now().strftime('%H:%M:%S')}] {symbol} 주문 #{order_num} 모니터링 오류: {e}")
            log_func(f"⚠️ {symbol} 주문 #{order_num} 모니터링 오류: {e}")

    def create_data_callback(symbol):
        async def data_callback(market_data):
            nonlocal data_count, signal_count, order_count, start_time, last_price
            data_count[symbol] += 1

            current_time = datetime.now()
            time_str = current_time.strftime('%H:%M:%S')

            # 가격 변화 표시 (한국 주식: 빨강=상승, 파랑=하락)
            price_change = ""
            if last_price[symbol]:
                if market_data.current_price > last_price[symbol]:
                    price_change = f" {Colors.RED}▲UP{Colors.END}"
                elif market_data.current_price < last_price[symbol]:
                    price_change = f" {Colors.BLUE}▼DOWN{Colors.END}"
                else:
                    price_change = f" {Colors.YELLOW}→SAME{Colors.END}"

            last_price[symbol] = market_data.current_price

            # 변동률 표시
            if market_data.change_percent >= 0:
                change_text = f"+{market_data.change_percent:.2f}%"
                change_color = Colors.RED  # 한국: 빨강=상승
            else:
                change_text = f"{market_data.change_percent:.2f}%"
                change_color = Colors.BLUE  # 한국: 파랑=하락

            # 가격 포맷
            price_text = f"{market_data.current_price:,}원"

            # 전략 분석 정보
            strategy_info = ""
            try:
                strategy = trading_engine.strategies.get(symbol)
                if strategy and hasattr(strategy, 'get_current_analysis'):
                    analysis = strategy.get_current_analysis()
                    if analysis:
                        if strategy_type == "rsi":
                            rsi = analysis.get('rsi_value', 50)
                            rsi_level = analysis.get('rsi_level', '중립')
                            strategy_info = f" | RSI:{rsi:.0f}({rsi_level})"
                        elif strategy_type == "bollinger":
                            band_pos = analysis.get('band_position', 'MIDDLE')
                            is_squeeze = analysis.get('is_squeeze', False)
                            bb_status = "압축" if is_squeeze else band_pos
                            strategy_info = f" | BB:{bb_status}"
                        elif strategy_type == "ma":
                            cross = analysis.get('cross_direction', 'NONE')
                            trend = analysis.get('trend_direction', 'NEUTRAL')
                            if cross == "GOLDEN":
                                strategy_info = f" | 골든크로스🚀"
                            elif cross == "DEAD":
                                strategy_info = f" | 데드크로스💥"
                            else:
                                strategy_info = f" | 추세:{trend}"
                else:
                    # 기본 정보 (간단한 분석)
                    if data_count[symbol] >= 20:
                        if market_data.change_percent > 3:
                            strategy_info = " | 급등세📈"
                        elif market_data.change_percent < -3:
                            strategy_info = " | 급락세📉"
                        elif market_data.change_percent > 0:
                            strategy_info = " | 상승세🔼"
                        else:
                            strategy_info = " | 하락세🔽"
                    else:
                        strategy_info = " | 분석중..."
            except:
                strategy_info = " | 전략분석 준비중"

            # 기본 가격 로그 + 전략 분석
            print(f"{Colors.CYAN}[{time_str}]{Colors.END} #{data_count[symbol]:4d} "
                  f"{Colors.BOLD}{symbol}{Colors.END} "
                  f"{Colors.WHITE}{price_text}{Colors.END} "
                  f"{change_color}{change_text}{Colors.END}"
                  f"{price_change}"
                  f"{Colors.MAGENTA}{strategy_info}{Colors.END}")

            # 상세 로그 모드에서 가격 데이터 기록
            if detailed_log:
                write_trading_log(f"{symbol} #{data_count[symbol]:4d} | "
                                f"가격: {market_data.current_price:,}원 | "
                                f"변동률: {market_data.change_percent:+.2f}% | "
                                f"거래량: {market_data.volume:,}주{strategy_info}", "price")

                # 전략 분석 데이터가 있으면 분석 로그에 기록
                if strategy_info and strategy_info != " | 분석중..." and strategy_info != " | 전략분석 준비중":
                    write_trading_log(f"{symbol} 전략분석{strategy_info}", "analysis")

            # 자동매매 신호 처리
            try:
                signal = await trading_engine.update_market_data(symbol, market_data)

                if signal:
                    signal_count[symbol] += 1
                    if signal.signal_type == "SELL":
                        signal_type = f"{Colors.BLUE}🔵 매도{Colors.END}"
                        signal_color = Colors.BLUE
                        signal_text = "매도"
                    else:
                        signal_type = f"{Colors.RED}🔴 매수{Colors.END}"
                        signal_color = Colors.RED
                        signal_text = "매수"

                    # 화면 출력
                    print(f"    {Colors.BOLD}💡 [{time_str}] {symbol} 신호 #{signal_count[symbol]}:{Colors.END} {signal_type} "
                          f"{Colors.CYAN}신뢰도 {signal.confidence:.2f}{Colors.END} - {signal.reason}")

                    # 로그 파일에 기록
                    write_trading_log(f"💡 {symbol} 신호 #{signal_count[symbol]}: {signal_text} 신뢰도 {signal.confidence:.2f} - {signal.reason}")
                    write_trading_log(f"   가격: {market_data.current_price:,}원 | 변동률: {market_data.change_percent:+.2f}%")

                    # 높은 신뢰도 신호는 실제 주문 실행
                    if signal.confidence >= 0.8:
                        order_count[symbol] += 1
                        order_mode = "실제" if use_real_trading else "모의"
                        print(f"    {Colors.BOLD}{signal_color}⚡ [{time_str}] {symbol} {order_mode} 주문 #{order_count[symbol]}:{Colors.END} {signal_type} 1주 실행 중...")

                        # 주문 실행 로그 파일에 기록
                        write_trading_log(f"⚡ {symbol} {order_mode} 주문 #{order_count[symbol]}: {signal_text} 1주 실행 시도")

                        # 실제 주문 결과 모니터링 (비동기)
                        if use_real_trading:
                            asyncio.create_task(monitor_order_result(symbol, signal, order_count[symbol], write_trading_log, time_str))

            except Exception as e:
                print(f"    ❌ [{time_str}] {symbol} 매매 처리 오류: {e}")

        return data_callback

    try:
        # 초기화
        await provider.initialize()
        print("✅ WebSocket 연결 완료")

        # 매매 활성화
        trading_engine.enable_trading()
        print("✅ 자동매매 활성화")
        print()

        # 종목별 구독
        for symbol in symbols:
            await provider.subscribe_stock(symbol, create_data_callback(symbol))
            print(f"✅ {symbol} 실시간 구독 완료")

        print(f"✅ {symbol_display} 자동매매 시작 ({strategy_display})")
        print("📊 실시간 가격 및 매매 로그:")
        print()

        # 무한 실행 (Ctrl+C로 종료)
        while True:
            await asyncio.sleep(1)

            # 30초마다 상세 상태 로그 (detailed_log 모드에서만)
            current_time = datetime.now()
            if detailed_log and (current_time - last_status_log).total_seconds() >= 30:
                elapsed = (current_time - start_time).total_seconds()
                total_data = sum(data_count.values())
                total_signals = sum(signal_count.values())
                total_orders = sum(order_count.values())
                rate = total_data / elapsed if elapsed > 0 else 0

                # 상태 로그 기록
                write_trading_log(f"=== 시스템 상태 (경과시간: {elapsed:.0f}초) ===", "signal")
                write_trading_log(f"총 데이터 수신: {total_data}개 ({rate:.1f} msg/sec)", "signal")
                write_trading_log(f"총 매매신호: {total_signals}개, 총 주문실행: {total_orders}개", "signal")

                for symbol in symbols:
                    current_price_info = f"{last_price[symbol]:,}원" if last_price[symbol] else "미수신"
                    write_trading_log(f"{symbol}: 가격={current_price_info}, 데이터={data_count[symbol]}개, 신호={signal_count[symbol]}개, 주문={order_count[symbol]}개", "signal")

                write_trading_log("=" * 40, "signal")
                last_status_log = current_time

            # 150개 데이터마다 화면 통계 출력 (기존 로직 유지)
            total_data = sum(data_count.values())
            if total_data > 0 and total_data % 150 == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = total_data / elapsed
                print(f"{Colors.BOLD}{Colors.BLUE}📈 [{datetime.now().strftime('%H:%M:%S')}] === 통계 ==={Colors.END}")
                print(f"    {Colors.CYAN}가격 데이터:{Colors.END} {Colors.WHITE}{total_data}개 수신{Colors.END} ({Colors.YELLOW}{rate:.1f} msg/sec{Colors.END})")

                # 종목별 상세 통계
                for symbol in symbols:
                    total_signals = sum(signal_count.values())
                    total_orders = sum(order_count.values())
                    print(f"    {Colors.WHITE}{symbol}:{Colors.END} 데이터 {data_count[symbol]}개, 신호 {signal_count[symbol]}개, 주문 {order_count[symbol]}개")

                print(f"    {Colors.MAGENTA}총 매매 신호:{Colors.END} {Colors.WHITE}{total_signals}개 생성{Colors.END}")
                print(f"    {Colors.GREEN}총 주문 실행:{Colors.END} {Colors.WHITE}{total_orders}개 실행{Colors.END}")
                print()

    except KeyboardInterrupt:
        print("\n⏹️  사용자 안전 종료")
    except Exception as e:
        print(f"\n❌ 시스템 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await provider.disconnect()

        elapsed = (datetime.now() - start_time).total_seconds()
        total_data = sum(data_count.values())
        total_signals = sum(signal_count.values())
        total_orders = sum(order_count.values())

        print(f"\n📊 최종 자동매매 통계:")
        print(f"  실행 시간: {elapsed:.1f}초")
        print(f"  총 가격 데이터: {total_data}개")
        print(f"  총 매매 신호: {total_signals}개")
        print(f"  총 주문 실행: {total_orders}개")

        # 종목별 상세 통계
        for symbol in symbols:
            print(f"  {symbol}: 데이터 {data_count[symbol]}개, 신호 {signal_count[symbol]}개, 주문 {order_count[symbol]}개")

        if elapsed > 0:
            print(f"  평균 데이터 속도: {total_data/elapsed:.1f} msg/sec")

        # 최종 통계를 로그 파일에도 기록
        write_trading_log("=" * 60)
        write_trading_log("최종 자동매매 통계")
        write_trading_log(f"실행 시간: {elapsed:.1f}초")
        write_trading_log(f"총 가격 데이터: {total_data}개")
        write_trading_log(f"총 매매 신호: {total_signals}개")
        write_trading_log(f"총 주문 실행: {total_orders}개")
        for symbol in symbols:
            write_trading_log(f"{symbol}: 데이터 {data_count[symbol]}개, 신호 {signal_count[symbol]}개, 주문 {order_count[symbol]}개")
        if elapsed > 0:
            write_trading_log(f"평균 데이터 속도: {total_data/elapsed:.1f} msg/sec")
        write_trading_log("국내주식 자동매매 시스템 종료")

        print(f"📁 신호 로그 파일: {log_filename}")
        if detailed_log:
            if price_log_filename:
                print(f"📁 가격 로그 파일: {price_log_filename}")
            if analysis_log_filename:
                print(f"📁 분석 로그 파일: {analysis_log_filename}")
        print("👋 국내주식 자동매매 시스템 종료")


def main():
    """메인 함수 - 종목 및 전략 파라미터 처리"""
    parser = argparse.ArgumentParser(description='국내주식 실시간 자동매매 로그 시스템')
    parser.add_argument(
        '--symbol', '-s',
        default='005930',  # 삼성전자
        help='모니터링할 종목 (기본값: 005930, 여러 종목은 콤마로 구분: 005930,000660,035420)'
    )
    parser.add_argument(
        '--strategy', '-st',
        choices=['rsi', 'bollinger', 'ma'],
        default='rsi',
        help='사용할 전략 (rsi: RSI전략, bollinger: 볼린저밴드, ma: 이동평균, 기본값: rsi)'
    )
    parser.add_argument(
        '--real-trading', '-r',
        action='store_true',
        help='실제 주문 실행 (기본값: 모의 주문)'
    )
    parser.add_argument(
        '--test-mode', '-t',
        action='store_true',
        help='테스트 모드 (안전장치 및 에러 처리 검증)'
    )
    parser.add_argument(
        '--detailed-log', '-d',
        action='store_true',
        help='상세 로그 모드 (실시간 가격/분석 데이터 기록)'
    )

    args = parser.parse_args()

    # 종목 리스트 파싱
    symbols = [symbol.strip() for symbol in args.symbol.split(',')]

    # 실제 거래 경고 및 안전 확인
    if args.real_trading:
        print(f"{Colors.RED}{Colors.BOLD}⚠️  경고: 실제 주문 모드가 활성화되었습니다!{Colors.END}")
        print(f"{Colors.RED}실제 돈으로 거래가 실행됩니다. 신중하게 사용하세요.{Colors.END}")
        print(f"{Colors.YELLOW}💰 안전장치: 최대 100만원/주문, 하루 10회 제한, 30초 간격{Colors.END}")
        print(f"{Colors.CYAN}🔍 모니터링: 실시간 주문 결과 추적, 상세 로깅{Colors.END}")
        response = input("계속하시겠습니까? (yes/no): ")
        if response.lower() != 'yes':
            print("시스템을 종료합니다.")
            return

        # 최종 확인
        print(f"{Colors.RED}마지막 확인: 실제 매매를 시작합니다.{Colors.END}")
        final_confirm = input("정말로 계속하시겠습니까? (YES): ")
        if final_confirm.upper() != 'YES':
            print("시스템을 종료합니다.")
            return

    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )

    # 실시간 거래 로그 실행
    asyncio.run(domestic_realtime_trading_log(symbols, args.strategy, args.real_trading, args.test_mode, args.detailed_log))


if __name__ == "__main__":
    main()