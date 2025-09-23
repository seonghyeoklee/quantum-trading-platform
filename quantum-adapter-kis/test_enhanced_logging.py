#!/usr/bin/env python3
"""
Enhanced Logging System Test Script
국내주식 실시간 거래 로그 시스템의 새로운 기능들을 테스트합니다.
"""

import asyncio
import os
import argparse
from datetime import datetime

def test_basic_logging():
    """기본 로그 시스템 테스트 (기존 기능)"""
    print("🔍 테스트 1: 기본 로그 시스템 (--detailed-log 없음)")
    print("명령어: uv run python domestic_realtime_trading_log.py --symbol 005930 --strategy ma")
    print("예상 결과:")
    print("  - logs/trading/signals/ 디렉토리에 신호 로그 파일 1개만 생성")
    print("  - 매매 신호 발생시에만 로그 기록")
    print("  - 30초마다 상태 로그 없음")
    print()

def test_detailed_logging():
    """상세 로그 시스템 테스트 (새로운 기능)"""
    print("🔍 테스트 2: 상세 로그 시스템 (--detailed-log 포함)")
    print("명령어: uv run python domestic_realtime_trading_log.py --symbol 005930 --strategy ma --detailed-log")
    print("예상 결과:")
    print("  - logs/trading/2025-09-23/signals/ 디렉토리에 신호 로그 파일 생성")
    print("  - logs/trading/2025-09-23/price_data/ 디렉토리에 가격 로그 파일 생성")
    print("  - logs/trading/2025-09-23/signals/ 디렉토리에 분석 로그 파일 생성")
    print("  - 파일명: domestic_005930_ma_signals_140736.log (날짜 제거)")
    print("  - 실시간으로 모든 가격 데이터 기록")
    print("  - 30초마다 시스템 상태 로그 기록")
    print("  - 전략 분석 결과 별도 기록")
    print()

def test_multi_symbol_logging():
    """다중 종목 상세 로그 테스트"""
    print("🔍 테스트 3: 다중 종목 상세 로그")
    print("명령어: uv run python domestic_realtime_trading_log.py --symbol 005930,000660 --strategy rsi --detailed-log")
    print("예상 결과:")
    print("  - 파일명에 '005930_000660' 포함")
    print("  - 두 종목의 가격 데이터 모두 기록")
    print("  - 종목별 분석 결과 구분하여 기록")
    print("  - 30초 상태 로그에 두 종목 정보 포함")
    print()

def check_log_directories():
    """로그 디렉토리 구조 확인 (날짜별 폴더 포함)"""
    print("📁 로그 디렉토리 구조 확인:")

    base_dir = "logs/trading"

    if os.path.exists(base_dir):
        # 날짜별 디렉토리 확인
        date_dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]

        if date_dirs:
            print(f"  📂 {base_dir}: {len(date_dirs)}개 날짜 폴더")

            # 최근 3개 날짜 폴더만 표시
            for date_dir in sorted(date_dirs)[-3:]:
                date_path = os.path.join(base_dir, date_dir)
                print(f"    📅 {date_dir}/")

                # signals 디렉토리 확인
                signal_dir = os.path.join(date_path, "signals")
                if os.path.exists(signal_dir):
                    signal_files = os.listdir(signal_dir)
                    print(f"      📂 signals/: {len(signal_files)}개 파일")
                    for file in sorted(signal_files)[-2:]:  # 최근 2개만
                        file_path = os.path.join(signal_dir, file)
                        size = os.path.getsize(file_path)
                        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        print(f"        📄 {file} ({size:,} bytes, {mtime.strftime('%H:%M:%S')})")

                # price_data 디렉토리 확인
                price_dir = os.path.join(date_path, "price_data")
                if os.path.exists(price_dir):
                    price_files = os.listdir(price_dir)
                    print(f"      📊 price_data/: {len(price_files)}개 파일")
                    for file in sorted(price_files)[-2:]:  # 최근 2개만
                        file_path = os.path.join(price_dir, file)
                        size = os.path.getsize(file_path)
                        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        print(f"        📄 {file} ({size:,} bytes, {mtime.strftime('%H:%M:%S')})")
        else:
            print(f"  📂 {base_dir}: 날짜 폴더 없음")
    else:
        print(f"  📂 {base_dir}: 디렉토리 없음")

    # 기존 구조도 확인 (호환성)
    old_signal_dir = "logs/trading/signals"
    if os.path.exists(old_signal_dir):
        old_files = [f for f in os.listdir(old_signal_dir) if f.endswith('.log')]
        if old_files:
            print(f"  📂 {old_signal_dir} (기존): {len(old_files)}개 파일")

    print()

def show_log_file_content(file_pattern="*signals*"):
    """최근 로그 파일 내용 일부 표시 (날짜별 폴더 포함)"""
    import glob

    # 새로운 날짜별 구조에서 찾기
    signal_pattern = "logs/trading/*/signals/*signals*.log"
    signal_files = glob.glob(signal_pattern)

    # 기존 구조에서도 찾기 (호환성)
    old_signal_pattern = "logs/trading/signals/*signals*.log"
    old_signal_files = glob.glob(old_signal_pattern)

    all_signal_files = signal_files + old_signal_files

    if all_signal_files:
        latest_signal = max(all_signal_files, key=os.path.getmtime)
        print(f"📖 최근 신호 로그 파일 내용 (상위 10줄): {latest_signal}")
        try:
            with open(latest_signal, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:10]
                for i, line in enumerate(lines, 1):
                    print(f"  {i:2d}: {line.rstrip()}")
        except Exception as e:
            print(f"  ❌ 파일 읽기 오류: {e}")
    else:
        print("📖 신호 로그 파일 없음")
    print()

    # 새로운 날짜별 구조에서 가격 로그 찾기
    price_pattern = "logs/trading/*/price_data/*prices*.log"
    price_files = glob.glob(price_pattern)

    # 기존 구조에서도 찾기 (호환성)
    old_price_pattern = "logs/trading/price_data/*prices*.log"
    old_price_files = glob.glob(old_price_pattern)

    all_price_files = price_files + old_price_files

    if all_price_files:
        latest_price = max(all_price_files, key=os.path.getmtime)
        print(f"📊 최근 가격 로그 파일 내용 (상위 5줄): {latest_price}")
        try:
            with open(latest_price, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:5]
                for i, line in enumerate(lines, 1):
                    print(f"  {i:2d}: {line.rstrip()}")
        except Exception as e:
            print(f"  ❌ 파일 읽기 오류: {e}")
    else:
        print("📊 가격 로그 파일 없음")
    print()

def main():
    """메인 테스트 함수"""
    parser = argparse.ArgumentParser(description='Enhanced Logging System Test')
    parser.add_argument(
        '--check-logs', '-c',
        action='store_true',
        help='기존 로그 파일들 확인'
    )
    parser.add_argument(
        '--show-content', '-s',
        action='store_true',
        help='최근 로그 파일 내용 표시'
    )

    args = parser.parse_args()

    print("🧪 Enhanced Logging System Test")
    print("=" * 50)
    print()

    if args.check_logs:
        check_log_directories()

    if args.show_content:
        show_log_file_content()

    if not args.check_logs and not args.show_content:
        print("📋 테스트 계획:")
        print()
        test_basic_logging()
        test_detailed_logging()
        test_multi_symbol_logging()

        print("🔧 테스트 실행 방법:")
        print("1. 위의 명령어들을 각각 실행 (짧은 시간, 1-2분)")
        print("2. Ctrl+C로 안전 종료")
        print("3. 로그 파일 확인: python test_enhanced_logging.py --check-logs")
        print("4. 로그 내용 확인: python test_enhanced_logging.py --show-content")
        print()

        print("✅ 예상 개선사항:")
        print("  - 기존: 매매 신호 발생시에만 로그 (6줄 정도)")
        print("  - 개선: 실시간 가격 데이터 + 분석 결과 + 30초 상태 요약")
        print("  - 구조: 신호/가격/분석 로그 파일 분리")
        print("  - 📅 날짜별 폴더: logs/trading/YYYY-MM-DD/signals|price_data/")
        print("  - 📄 파일명 간소화: 날짜 제거, 시간만 포함 (HHMMSS)")
        print("  - 모니터링: 상세한 시스템 상태 추적 가능")

if __name__ == "__main__":
    main()