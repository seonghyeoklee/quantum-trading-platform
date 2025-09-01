#!/usr/bin/env python3
"""
동적 모드 전환 기능 테스트 스크립트

Python Adapter가 Java에서 전송된 dry_run 파라미터에 따라
모의투자/실전투자 모드를 동적으로 전환하는지 테스트
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from kiwoom_api.config.dynamic_settings import get_dynamic_config, extract_dry_run


def test_dynamic_settings():
    """동적 설정 생성 테스트"""
    print("🧪 동적 설정 생성 테스트")
    print("=" * 50)
    
    # 1. 모의투자 모드 테스트
    print("\n1️⃣ 모의투자 모드 (dry_run=True)")
    config_mock = get_dynamic_config(dry_run=True)
    print(f"   URL: {config_mock.base_url}")
    print(f"   모드: {config_mock.mode_description}")
    print(f"   샌드박스: {config_mock.is_sandbox_mode}")
    
    # 2. 실전투자 모드 테스트
    print("\n2️⃣ 실전투자 모드 (dry_run=False)")
    config_prod = get_dynamic_config(dry_run=False)
    print(f"   URL: {config_prod.base_url}")
    print(f"   모드: {config_prod.mode_description}")
    print(f"   샌드박스: {config_prod.is_sandbox_mode}")
    
    # 3. 환경변수 기본값 테스트
    print("\n3️⃣ 환경변수 기본값 (dry_run=None)")
    config_default = get_dynamic_config(dry_run=None)
    print(f"   URL: {config_default.base_url}")
    print(f"   모드: {config_default.mode_description}")
    print(f"   샌드박스: {config_default.is_sandbox_mode}")


def test_dry_run_extraction():
    """dry_run 파라미터 추출 테스트"""
    print("\n\n🧪 dry_run 파라미터 추출 테스트")
    print("=" * 50)
    
    # 다양한 형태의 요청 데이터 테스트
    test_cases = [
        ({"dry_run": True}, True),
        ({"dry_run": False}, False),
        ({"dryRun": True}, True),
        ({"dry-run": False}, False),
        ({"mock_mode": True}, True),
        ({"dry_run": "true"}, True),
        ({"dry_run": "false"}, False),
        ({"dry_run": 1}, True),
        ({"dry_run": 0}, False),
        ({"stk_cd": "005930"}, None),  # dry_run 없음
    ]
    
    for i, (request_data, expected) in enumerate(test_cases, 1):
        result = extract_dry_run(request_data)
        status = "✅" if result == expected else "❌"
        print(f"{i:2d}. {request_data} → {result} {status}")


async def test_stock_function():
    """stock.py 함수 동적 모드 전환 테스트"""
    print("\n\n🧪 stock.py 함수 동적 모드 전환 테스트")
    print("=" * 50)
    
    try:
        from kiwoom_api.functions.stock import fn_ka10001
        
        # 테스트 요청 데이터
        test_data = {
            "stk_cd": "005930",  # 삼성전자
            "dry_run": True      # 모의투자 모드
        }
        
        print("\n📊 fn_ka10001 함수 테스트 (토큰 없이 - 실패 예상)")
        print(f"   요청 데이터: {test_data}")
        
        # 실제 API 호출은 토큰이 없어서 실패할 것이지만,
        # 동적 설정 생성 로직은 확인 가능
        try:
            result = await fn_ka10001(data=test_data, dry_run=True)
            print(f"   결과: {result}")
        except Exception as e:
            print(f"   예상된 실패: {str(e)}")
            
    except ImportError as e:
        print(f"   Import 오류: {e}")


def main():
    """메인 테스트 실행"""
    print("🚀 Python Adapter 동적 모드 전환 기능 테스트")
    print("=" * 70)
    
    # 동적 설정 테스트
    test_dynamic_settings()
    
    # dry_run 추출 테스트
    test_dry_run_extraction()
    
    # stock.py 함수 테스트
    asyncio.run(test_stock_function())
    
    print("\n" + "=" * 70)
    print("✅ 테스트 완료!")
    print("\n📋 다음 단계:")
    print("1. 환경변수 설정 확인 (KIWOOM_SANDBOX_APP_KEY, KIWOOM_PRODUCTION_APP_KEY)")
    print("2. Java에서 실제 API 호출로 통합 테스트")
    print("3. 모드별 토큰 캐싱 분리 처리")


if __name__ == "__main__":
    main()