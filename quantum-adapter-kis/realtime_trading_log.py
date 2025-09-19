#!/usr/bin/env python3
"""
실시간 자동매매 로그 스트림
명확한 표기 + 실제 매매 신호 및 주문 실행 포함
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

from overseas_trading_system.core.realtime_websocket_provider import RealtimeWebSocketProvider
from overseas_trading_system.core.overseas_trading_engine import OverseasTradingEngine
from overseas_trading_system.core.real_order_executor import RealOverseasOrderExecutor
from overseas_trading_system.strategies.momentum_strategy import MomentumStrategy
from overseas_trading_system.strategies.vwap_strategy import VWAPStrategy


async def realtime_trading_log(symbols, strategy_name='momentum'):
    """실시간 자동매매 로그 스트림"""
    symbol_display = ", ".join(symbols)
    strategy_display = {
        'momentum': '모멘텀 전략',
        'vwap': 'VWAP 전략'
    }.get(strategy_name, strategy_name)

    print(f'🚀 실시간 {symbol_display} 자동매매 로그 스트림')
    print('=' * 70)
    print('⚠️  실전투자 WebSocket 연결 + 실제 매매 기능')
    print(f'📊 {symbol_display} 실시간 가격 변동 및 자동매매 신호를 연속 출력')
    print(f'🎯 사용 전략: {strategy_display}')
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
    provider = RealtimeWebSocketProvider(appkey, appsecret, "prod")
    trading_engine = OverseasTradingEngine({
        'max_positions': 1,
        'default_quantity': 1,
        'min_confidence': 0.8
    })

    # 실제 주문 실행기
    real_executor = RealOverseasOrderExecutor({
        'account_number': config['my_acct_stock'],
        'account_product_code': config['my_prod'],
        'execution_delay': 0.1
    })

    # 거래 엔진 설정
    trading_engine.set_order_executor(real_executor.execute_order)

    # 각 종목에 대해 전략 추가
    for symbol in symbols:
        if strategy_name == 'vwap':
            strategy = VWAPStrategy({
                'std_multiplier': 2.0,
                'volume_threshold': 1.5,
                'min_confidence': 0.7,
                'price_deviation_threshold': 0.5
            })
        else:  # 기본값: momentum
            strategy = MomentumStrategy({
                'rsi_oversold': 25,
                'rsi_overbought': 75,
                'min_confidence': 0.8
            })

        trading_engine.add_stock(symbol, strategy)

    # 실시간 데이터 카운터
    data_count = {symbol: 0 for symbol in symbols}
    signal_count = {symbol: 0 for symbol in symbols}
    order_count = {symbol: 0 for symbol in symbols}
    start_time = datetime.now()
    last_price = {symbol: None for symbol in symbols}

    # 로그 디렉토리 설정
    log_dir = "logs/trading/signals"
    csv_log_dir = "logs/trading/data"
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(csv_log_dir, exist_ok=True)

    # 매매 신호 로그 파일 생성
    symbols_str = "_".join(symbols)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = os.path.join(log_dir, f"{symbols_str}_{strategy_name}_signals_{timestamp}.log")
    csv_filename = os.path.join(csv_log_dir, f"{symbols_str}_{strategy_name}_data_{timestamp}.csv")

    # 로그 레벨 설정
    LOG_LEVEL = {
        'DATA': True,      # 모든 가격 데이터
        'SIGNAL': True,    # 매매 신호
        'ORDER': True,     # 주문 실행
        'ANALYSIS': True,  # 전략 분석
        'STATS': True      # 통계 정보
    }

    def write_trading_log(message):
        """매매 신호를 파일에 기록"""
        with open(log_filename, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")

    def write_csv_log(data_dict):
        """CSV 형식으로 데이터 기록"""
        import csv
        file_exists = os.path.exists(csv_filename)

        with open(csv_filename, 'a', newline='', encoding='utf-8') as f:
            fieldnames = ['timestamp', 'symbol', 'price', 'volume', 'change_percent',
                         'rsi', 'bb_position', 'momentum', 'session', 'signal_type',
                         'confidence', 'reason']
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow(data_dict)

    # 로그 파일 시작 메시지
    write_trading_log(f"{symbol_display} 실시간 자동매매 로그 시작")
    write_trading_log(f"로그 파일: {log_filename}")
    write_trading_log("=" * 60)

    def create_data_callback(symbol):
        async def data_callback(market_data):
            nonlocal data_count, signal_count, order_count, start_time, last_price
            data_count[symbol] += 1

            current_time = datetime.now()
            time_str = current_time.strftime('%H:%M:%S')

            # 가격 변화 표시 (컬러 적용)
            price_change = ""
            if last_price[symbol]:
                if market_data.current_price > last_price[symbol]:
                    price_change = f" {Colors.GREEN}▲UP{Colors.END}"
                elif market_data.current_price < last_price[symbol]:
                    price_change = f" {Colors.RED}▼DOWN{Colors.END}"
                else:
                    price_change = f" {Colors.YELLOW}→SAME{Colors.END}"

            last_price[symbol] = market_data.current_price

            # 변동률 표시 (명확하게)
            if market_data.change_percent >= 0:
                change_text = f"+{market_data.change_percent:.2f}%"
            else:
                change_text = f"{market_data.change_percent:.2f}%"

            # KRW 가격 (직관적으로)
            krw_price = market_data.get_price_krw()
            if krw_price >= 1000000:
                krw_text = f"₩{krw_price/1000000:.1f}백만"
            elif krw_price >= 100000:
                krw_text = f"₩{krw_price/10000:.0f}만원"
            elif krw_price >= 10000:
                krw_text = f"₩{krw_price/10000:.1f}만원"
            elif krw_price >= 1000:
                krw_text = f"₩{krw_price:,.0f}원"
            else:
                krw_text = f"₩{krw_price:.0f}원"

            # 전략 분석 정보 (오른쪽 끝에 표시)
            strategy_info = ""
            try:
                # 모멘텀 전략에서 현재 상태 가져오기
                strategy = trading_engine.strategies.get(symbol)
                if strategy and hasattr(strategy, 'get_current_analysis'):
                    analysis = strategy.get_current_analysis()
                    if analysis:
                        rsi = analysis.get('rsi', 0)
                        bb_position = analysis.get('bb_position', 'MID')
                        momentum = analysis.get('momentum', 'NEUTRAL')

                        # RSI 상태 (한국어로)
                        if rsi > 70:
                            rsi_status = f"과열:{rsi:.0f}🔴"
                        elif rsi < 30:
                            rsi_status = f"침체:{rsi:.0f}🟢"
                        else:
                            rsi_status = f"보통:{rsi:.0f}⚪"

                        # 볼린저밴드 위치 (한국어로)
                        bb_dict = {"UPPER": "고점⬆️", "LOWER": "저점⬇️", "MID": "중간➡️"}
                        bb_status = bb_dict.get(bb_position, "중간➡️")

                        # 모멘텀 상태 (한국어로)
                        momentum_dict = {
                            "STRONG_UP": "급등🚀",
                            "UP": "상승📈",
                            "DOWN": "하락📉",
                            "STRONG_DOWN": "급락💥",
                            "NEUTRAL": "보합➖"
                        }
                        momentum_status = momentum_dict.get(momentum, "보합➖")

                        strategy_info = f" | {rsi_status} {bb_status} {momentum_status}"
                else:
                    # 기본 분석 (간단한 계산)
                    if data_count[symbol] >= 14:  # 분석을 위한 최소 데이터
                        # 간단한 추정 (변동률 기준)
                        if market_data.change_percent > 2:
                            strategy_info = " | 과열:고⚪🔴 고점⬆️ 급등🚀"
                        elif market_data.change_percent < -2:
                            strategy_info = " | 침체:저⚪🟢 저점⬇️ 급락💥"
                        elif market_data.change_percent > 0:
                            strategy_info = " | 보통:중⚪ 중간➡️ 상승📈"
                        else:
                            strategy_info = " | 보통:중⚪ 중간➡️ 하락📉"
                    else:
                        strategy_info = " | 분석중..."
            except:
                strategy_info = " | 전략분석 준비중"

            # 가격 변화에 따른 색상
            if market_data.change_percent > 0:
                price_color = Colors.GREEN
            elif market_data.change_percent < 0:
                price_color = Colors.RED
            else:
                price_color = Colors.YELLOW

            # 기본 가격 로그 + 전략 분석 (색상 적용)
            print(f"{Colors.CYAN}[{time_str}]{Colors.END} #{data_count[symbol]:4d} "
                  f"{Colors.BOLD}{symbol}{Colors.END} "
                  f"{price_color}${market_data.current_price:.2f}{Colors.END} "
                  f"{Colors.YELLOW}({krw_text}){Colors.END} "
                  f"{price_color}{change_text}{Colors.END}"
                  f"{price_change}"
                  f"{Colors.MAGENTA}{strategy_info}{Colors.END}")

            # 모든 데이터를 로그 파일에 기록 (분석용)
            if LOG_LEVEL['DATA']:
                # 전략 분석 데이터 추출
                strategy = trading_engine.strategies.get(symbol)
                rsi_val = 0
                bb_pos = "MID"
                momentum_val = "NEUTRAL"

                if strategy and hasattr(strategy, 'get_current_analysis'):
                    analysis = strategy.get_current_analysis()
                    if analysis:
                        rsi_val = analysis.get('rsi', 0)
                        bb_pos = analysis.get('bb_position', 'MID')
                        momentum_val = analysis.get('momentum', 'NEUTRAL')

                # CSV 로그 기록
                csv_data = {
                    'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'symbol': symbol,
                    'price': market_data.current_price,
                    'volume': market_data.volume,
                    'change_percent': market_data.change_percent,
                    'rsi': rsi_val,
                    'bb_position': bb_pos,
                    'momentum': momentum_val,
                    'session': getattr(market_data, 'trading_session', 'UNKNOWN'),
                    'signal_type': '',
                    'confidence': 0,
                    'reason': ''
                }
                write_csv_log(csv_data)

                # 전략별 추가 정보
                strategy_info_text = f"RSI:{rsi_val:.1f}|BB:{bb_pos}|Momentum:{momentum_val}"

                # VWAP 전략인 경우 VWAP 정보 추가
                if strategy_name == 'vwap' and hasattr(strategy, 'get_current_analysis'):
                    vwap_analysis = strategy.get_current_analysis()
                    if vwap_analysis and vwap_analysis.get('vwap', 0) > 0:
                        vwap_val = vwap_analysis.get('vwap', 0)
                        upper_band = vwap_analysis.get('upper_band', 0)
                        lower_band = vwap_analysis.get('lower_band', 0)
                        position = vwap_analysis.get('position', 'UNKNOWN')
                        strategy_info_text = f"VWAP:{vwap_val:.2f}|Upper:{upper_band:.2f}|Lower:{lower_band:.2f}|Pos:{position}"

                # 텍스트 로그 기록
                write_trading_log(f"DATA|{symbol}|{time_str}|{market_data.current_price:.2f}|{market_data.volume}|{market_data.change_percent:+.2f}%|{strategy_info_text}")

            # 자동매매 신호 처리
            try:
                signal = await trading_engine.update_market_data(symbol, market_data)

                if signal:
                    signal_count[symbol] += 1
                    if signal.signal_type.value == "SELL":
                        signal_type = f"{Colors.RED}🔴 매도{Colors.END}"
                        signal_color = Colors.RED
                        signal_text = "매도"
                    else:
                        signal_type = f"{Colors.GREEN}🟢 매수{Colors.END}"
                        signal_color = Colors.GREEN
                        signal_text = "매수"

                    # 화면 출력
                    print(f"    {Colors.BOLD}💡 [{time_str}] {symbol} 신호 #{signal_count[symbol]}:{Colors.END} {signal_type} "
                          f"{Colors.CYAN}신뢰도 {signal.confidence:.2f}{Colors.END} - {signal.reason}")

                    # 로그 파일에 기록
                    if LOG_LEVEL['SIGNAL']:
                        write_trading_log(f"SIGNAL|{symbol}|{signal_text}|{signal.confidence:.2f}|{signal.reason}")
                        write_trading_log(f"   가격: ${market_data.current_price:.2f} | 변동률: {market_data.change_percent:+.2f}%")

                    # CSV에 신호 정보 기록
                    if LOG_LEVEL['SIGNAL']:
                        # 전략 분석 데이터 추출
                        strategy = trading_engine.strategies.get(symbol)
                        rsi_val = 0
                        bb_pos = "MID"
                        momentum_val = "NEUTRAL"

                        if strategy and hasattr(strategy, 'get_current_analysis'):
                            analysis = strategy.get_current_analysis()
                            if analysis:
                                rsi_val = analysis.get('rsi', 0)
                                bb_pos = analysis.get('bb_position', 'MID')
                                momentum_val = analysis.get('momentum', 'NEUTRAL')

                        # 신호 CSV 데이터
                        signal_csv_data = {
                            'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                            'symbol': symbol,
                            'price': market_data.current_price,
                            'volume': market_data.volume,
                            'change_percent': market_data.change_percent,
                            'rsi': rsi_val,
                            'bb_position': bb_pos,
                            'momentum': momentum_val,
                            'session': getattr(market_data, 'trading_session', 'UNKNOWN'),
                            'signal_type': signal_text,
                            'confidence': signal.confidence,
                            'reason': signal.reason
                        }
                        write_csv_log(signal_csv_data)

                    # 높은 신뢰도 신호는 실제 주문 실행
                    if signal.confidence >= 0.8:
                        order_count[symbol] += 1
                        print(f"    {Colors.BOLD}{signal_color}⚡ [{time_str}] {symbol} 실제 주문 #{order_count[symbol]}:{Colors.END} {signal_type} 1주 실행 중...")

                        # 주문 실행 로그 파일에 기록
                        if LOG_LEVEL['ORDER']:
                            write_trading_log(f"ORDER|{symbol}|{signal_text}|1|{market_data.current_price:.2f}|{signal.confidence:.2f}|SIMULATION")

                        # 실제 주문 결과는 별도 로그로 출력됨

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

        print(f"✅ {symbol_display} 자동매매 시작")
        print("📊 실시간 가격 및 매매 로그:")
        print()

        # 무한 실행 (Ctrl+C로 종료)
        while True:
            await asyncio.sleep(1)

            # 30초마다 통계 출력
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
                print(f"    {Colors.GREEN}총 실제 주문:{Colors.END} {Colors.WHITE}{total_orders}개 실행{Colors.END}")
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
        print(f"  총 실제 주문: {total_orders}개")

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
        write_trading_log(f"총 실제 주문: {total_orders}개")
        for symbol in symbols:
            write_trading_log(f"{symbol}: 데이터 {data_count[symbol]}개, 신호 {signal_count[symbol]}개, 주문 {order_count[symbol]}개")
        if elapsed > 0:
            write_trading_log(f"평균 데이터 속도: {total_data/elapsed:.1f} msg/sec")
        write_trading_log("자동매매 시스템 종료")

        print(f"📁 로그 파일 저장됨: {log_filename}")
        print(f"📊 CSV 데이터 파일: {csv_filename}")
        print("👋 자동매매 시스템 종료")


def main():
    """메인 함수 - 종목 파라미터 처리"""
    parser = argparse.ArgumentParser(description='실시간 자동매매 로그 시스템')
    parser.add_argument(
        '--symbol', '-s',
        default='TSLA',
        help='모니터링할 종목 (기본값: TSLA, 여러 종목은 콤마로 구분: TSLA,AAPL,NVDA)'
    )
    parser.add_argument(
        '--strategy',
        choices=['momentum', 'vwap'],
        default='momentum',
        help='거래 전략 선택 (기본값: momentum)'
    )

    args = parser.parse_args()

    # 종목 리스트 파싱
    symbols = [symbol.strip().upper() for symbol in args.symbol.split(',')]
    strategy_name = args.strategy

    # 로깅 설정 (매매 관련 로그는 INFO로)
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )

    # 실시간 거래 로그 실행
    asyncio.run(realtime_trading_log(symbols, strategy_name))


if __name__ == "__main__":
    main()