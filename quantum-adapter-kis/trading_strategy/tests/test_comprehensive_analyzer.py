#!/usr/bin/env python3
"""
분석 시스템 테스트 스크립트
소규모 종목으로 시스템 동작 확인

Author: Quantum Trading Platform
"""

import asyncio
import sys
from pathlib import Path

# 현재 폴더 경로 추가
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from comprehensive_batch_analyzer import ComprehensiveBatchAnalyzer

async def test_small_batch():
    """소규모 배치 테스트"""
    print("🔍 분석 시스템 테스트 시작")
    
    # 테스트 종목 (국내 2개, 해외 2개)
    test_symbols = [
        "005930",  # 삼성전자
        "035720",  # 카카오
        "AAPL",    # Apple
        "MSFT"     # Microsoft
    ]
    
    analyzer = ComprehensiveBatchAnalyzer()
    
    print(f"📊 테스트 종목: {test_symbols}")
    
    # 분석 실행
    results = await analyzer.run_comprehensive_analysis(test_symbols)
    
    # 결과 출력
    print(f"\n🎯 테스트 결과:")
    for result in results:
        print(f"   {result['symbol']} ({result['symbol_name']})")
        print(f"      점수: {result['investment_score']:.1f}")
        print(f"      추천: {result['recommendation']}")
        print(f"      신호: {result['signal']['type']}")
        print()
    
    return results

if __name__ == "__main__":
    results = asyncio.run(test_small_batch())
    print(f"✅ 테스트 완료! {len(results)}개 종목 분석됨")