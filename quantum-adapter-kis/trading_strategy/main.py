#!/usr/bin/env python3
"""
Quantum Trading Strategy - 메인 실행 스크립트
실제 매매 없이 신호 감지 및 로깅만 수행
"""

import asyncio
import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime
import json

# 프로젝트 경로 추가
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))  # trading_strategy
sys.path.append(str(current_dir.parent))  # quantum-adapter-kis
sys.path.append(str(current_dir.parent / 'examples_llm'))  # KIS API 모듈

from monitor.signal_monitor import SignalMonitor, setup_logging

# 기본 종목 리스트 (변동성 다양한 종목들 + 테마주)
DEFAULT_SYMBOLS = {
    # 대형주 & IT
    "005930": "삼성전자",    # 대형주 안정성
    "000660": "SK하이닉스",  # 반도체
    "035420": "NAVER",      # IT 플랫폼
    "035720": "카카오",     # IT 플랫폼 고변동성
    
    # 화학 & 배터리
    "051910": "LG화학",     # 화학
    "006400": "삼성SDI",    # 배터리
    "373220": "LG에너지솔루션", # 배터리 신생대형주
    
    # 바이오
    "207940": "삼성바이오로직스", # 바이오
    "068270": "셀트리온",   # 바이오 고변동성
    
    # 건설 & 에너지
    "028260": "삼성물산",   # 건설/상사
    "096770": "SK이노베이션", # 에너지/화학
    "003550": "LG",         # 지주회사
    
    # 조선 테마 (고변동성)
    "009540": "HD한국조선해양", # 조선업계 1위
    "010620": "현대미포조선",   # 조선 중형주
    "241560": "두산밥캣",      # 건설기계
    
    # 방산 테마 (정부정책 민감)
    "012450": "한화에어로스페이스", # 방산/항공
    "272210": "한화시스템",    # 방산시스템
    "079550": "LIG넥스원",     # 방산전자
    
    # 원자력 테마 (SMR/신원전)
    "010060": "OCI",           # 폴리실리콘/원자력연료
    "001040": "CJ",            # 다각화/원자력관련
    "003200": "일신방직"       # 원자력안전/방사능방호
}

def print_banner():
    """시작 배너 출력"""
    banner = """
╔════════════════════════════════════════════════╗
║                                                ║
║    📊 Quantum Trading Strategy System 📊       ║
║                                                ║
║         Golden Cross Signal Monitor            ║
║              (Simulation Mode)                 ║
║                                                ║
╚════════════════════════════════════════════════╝
    """
    print(banner)

def load_config(config_file: str = "config.json") -> dict:
    """설정 파일 로드"""
    config_path = Path(config_file)
    
    if not config_path.exists():
        # 기본 설정 생성
        default_config = {
            "symbols": DEFAULT_SYMBOLS,
            "check_interval": 30,
            "investment_amount": 10000000,
            "simulation_mode": True,
            "logging": {
                "level": "INFO",
                "log_dir": "logs"
            }
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        
        return default_config
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_arguments():
    """명령줄 인자 파싱"""
    parser = argparse.ArgumentParser(
        description="Quantum Trading Strategy - 자동매매 신호 모니터링"
    )
    
    parser.add_argument(
        '--symbols',
        type=str,
        help='모니터링할 종목 코드 (콤마로 구분, 예: 005930,000660)'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='체크 간격 (초, 기본: 30)'
    )
    
    parser.add_argument(
        '--mode',
        choices=['simulation', 'live'],
        default='simulation',
        help='실행 모드 (기본: simulation)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.json',
        help='설정 파일 경로 (기본: config.json)'
    )
    
    return parser.parse_args()

async def main():
    """메인 실행 함수"""
    # 배너 출력
    print_banner()
    
    # 인자 파싱
    args = parse_arguments()
    
    # 설정 로드
    config = load_config(args.config)
    
    # 명령줄 인자로 설정 덮어쓰기
    if args.symbols:
        symbol_list = args.symbols.split(',')
        config['symbols'] = {s: f"종목_{s}" for s in symbol_list}
    
    if args.interval:
        config['check_interval'] = args.interval
    
    # 시뮬레이션 모드 확인
    simulation_mode = args.mode == 'simulation'
    
    print(f"📋 설정 정보:")
    print(f"  - 모드: {'시뮬레이션' if simulation_mode else '실전 (주의!)'}")
    print(f"  - 종목: {list(config['symbols'].values())}")
    print(f"  - 체크 간격: {config['check_interval']}초")
    print(f"  - 투자금액: {config.get('investment_amount', 10000000):,}원")
    print()
    
    if not simulation_mode:
        print("⚠️  경고: 실전 모드는 현재 지원되지 않습니다.")
        print("    시뮬레이션 모드로 전환합니다.")
        simulation_mode = True
    
    print("🚀 모니터링을 시작합니다...")
    print("   (종료하려면 Ctrl+C를 누르세요)")
    print()
    
    # 로깅 설정
    setup_logging("logs")
    today = datetime.now().strftime("%Y-%m-%d")
    print("")
    print("📄 로그 파일 저장 위치:")
    print(f"   📋 전체 로그: logs/all_{today}.log")
    print(f"   📊 시장 데이터: logs/market/market_{today}.log") 
    print(f"   🎯 신호 로그: logs/signals/ (신호 발생시 생성)")
    print(f"   💼 주문 로그: logs/orders/ (주문 발생시 생성)")
    print("")
    
    # 모니터링 시작
    monitor = SignalMonitor(
        symbols=config['symbols'],
        check_interval=config['check_interval'],
        simulation_mode=simulation_mode
    )
    
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\n")
        print("🛑 모니터링이 중지되었습니다.")
        
        # 요약 출력
        if hasattr(monitor, 'order_sim'):
            monitor.order_sim.print_summary()
        
        print("\n✅ 프로그램이 정상적으로 종료되었습니다.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        sys.exit(1)