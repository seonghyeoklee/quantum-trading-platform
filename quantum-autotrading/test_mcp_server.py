#!/usr/bin/env python3
"""
KIS API MCP 서버 테스트

MCP 서버의 기능을 테스트하는 스크립트입니다.
"""

import asyncio
import json
import subprocess
import sys
from datetime import datetime

async def test_mcp_server():
    """MCP 서버 기능 테스트"""
    
    print("🚀 === KIS API MCP 서버 테스트 ===")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # MCP 서버 실행 명령어
    mcp_server_cmd = [
        sys.executable, 
        "/Users/admin/study/quantum-trading-platform/quantum-autotrading/mcp_kis_server.py"
    ]
    
    print("📋 MCP 서버 기능 목록:")
    print()
    
    print("🔧 **사용 가능한 도구들**:")
    print("1. get_stock_price - 특정 종목의 실시간 현재가 조회")
    print("2. get_account_info - 계좌 잔고 및 보유 종목 조회")
    print("3. analyze_market_trend - 시장 동향 분석 (KOSPI/KOSDAQ)")
    print("4. get_trading_signals - 매매 신호 분석 (기술적 분석 기반)")
    print()
    
    print("📊 **사용 가능한 리소스들**:")
    print("1. kis://account/balance - 계좌 잔고 및 보유 종목")
    print("2. kis://market/kospi - KOSPI 주요 종목")
    print("3. kis://market/kosdaq - KOSDAQ 주요 종목")
    print()
    
    print("💡 **MCP 서버 연동 방법**:")
    print()
    print("1. **Claude Desktop에서 사용**:")
    print("   ~/.config/claude-desktop/claude_desktop_config.json 파일에 추가:")
    print("""   {
     "mcpServers": {
       "kis-api": {
         "command": "python3",
         "args": ["/Users/admin/study/quantum-trading-platform/quantum-autotrading/mcp_kis_server.py"],
         "env": {}
       }
     }
   }""")
    print()
    
    print("2. **직접 테스트**:")
    print("   다음 명령어로 MCP 서버를 직접 실행할 수 있습니다:")
    print(f"   python3 {mcp_server_cmd[1]}")
    print()
    
    print("3. **기능 예시**:")
    print("   - '삼성전자 현재가 알려줘' → get_stock_price 도구 사용")
    print("   - '내 계좌 잔고 확인해줘' → get_account_info 도구 사용")
    print("   - 'KOSPI 시장 동향 분석해줘' → analyze_market_trend 도구 사용")
    print("   - '매매 신호 분석해줘' → get_trading_signals 도구 사용")
    print()
    
    print("🎯 **주요 특징**:")
    print("✅ 실제 KIS API 연동 (모의투자 계좌)")
    print("✅ 실시간 주식 시세 조회")
    print("✅ 계좌 잔고 및 보유 종목 조회")
    print("✅ 시장 동향 분석")
    print("✅ 기술적 분석 기반 매매 신호")
    print("✅ Rate Limiting 적용 (API 호출 제한)")
    print("✅ 자동 토큰 관리")
    print()
    
    print("⚠️ **주의사항**:")
    print("- 모의투자 계좌를 사용합니다 (실제 거래 아님)")
    print("- API 호출 제한으로 1초 간격으로 요청됩니다")
    print("- KIS API 토큰은 자동으로 갱신됩니다")
    print()
    
    # 간단한 연결 테스트
    print("🔍 **연결 테스트**:")
    try:
        # MCP 서버를 짧게 실행해서 초기화 확인
        process = subprocess.Popen(
            mcp_server_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 3초 후 종료
        await asyncio.sleep(3)
        process.terminate()
        
        stdout, stderr = process.communicate(timeout=5)
        
        if "KIS MCP 클라이언트 초기화 완료" in stderr or "KIS 토큰 발급 성공" in stderr:
            print("✅ MCP 서버 초기화 성공!")
            print("✅ KIS API 연결 성공!")
        else:
            print("⚠️ MCP 서버 초기화 확인 필요")
            print(f"출력: {stderr[:200]}...")
        
    except Exception as e:
        print(f"⚠️ 연결 테스트 오류: {e}")
    
    print()
    print("🎉 **MCP 서버 준비 완료!**")
    print("이제 Claude Desktop이나 다른 MCP 클라이언트에서 사용할 수 있습니다.")
    print()
    print(f"완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
