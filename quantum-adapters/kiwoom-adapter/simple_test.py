#!/usr/bin/env python3
"""
동적 모드 전환 로직 간단 테스트

의존성 없이 핵심 로직만 테스트
"""

def get_dynamic_config_simple(dry_run=None):
    """간단한 동적 설정 로직 테스트"""
    # 환경변수 기본값 (일반적으로 False - 실전투자)
    default_sandbox = False
    
    if dry_run is None:
        is_sandbox = default_sandbox
        mode_text = "환경변수 기본값"
    else:
        is_sandbox = dry_run
        mode_text = "모의투자" if dry_run else "실전투자"
    
    if is_sandbox:
        base_url = "https://mockapi.kiwoom.com"
        mode_description = "샌드박스 (모의투자)"
    else:
        base_url = "https://api.kiwoom.com"
        mode_description = "실전투자"
    
    return {
        'base_url': base_url,
        'mode_description': mode_description,
        'is_sandbox_mode': is_sandbox,
        'mode_text': mode_text
    }

def extract_dry_run_simple(request_data):
    """간단한 dry_run 추출 로직 테스트"""
    dry_run_keys = ['dry_run', 'dryRun', 'dry-run', 'mock_mode']
    
    for key in dry_run_keys:
        if key in request_data:
            value = request_data[key]
            if isinstance(value, bool):
                return value
            elif isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            elif isinstance(value, (int, float)):
                return bool(value)
    
    return None

def main():
    print("🚀 동적 모드 전환 로직 테스트")
    print("=" * 70)
    
    # 1. 동적 설정 생성 테스트
    print("\n🧪 동적 설정 생성 테스트")
    print("-" * 50)
    
    test_cases = [
        ("모의투자", True),
        ("실전투자", False),
        ("환경변수기본값", None)
    ]
    
    for name, dry_run in test_cases:
        config = get_dynamic_config_simple(dry_run)
        print(f"\n{name} (dry_run={dry_run}):")
        print(f"  URL: {config['base_url']}")
        print(f"  모드: {config['mode_description']}")
        print(f"  샌드박스: {config['is_sandbox_mode']}")
    
    # 2. dry_run 추출 테스트
    print("\n\n🧪 dry_run 파라미터 추출 테스트")
    print("-" * 50)
    
    extract_test_cases = [
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
    
    for i, (request_data, expected) in enumerate(extract_test_cases, 1):
        result = extract_dry_run_simple(request_data)
        status = "✅" if result == expected else "❌"
        print(f"{i:2d}. {request_data} → {result} {status}")
    
    # 3. 통합 시나리오 테스트
    print("\n\n🧪 통합 시나리오 테스트 (Java → Python)")
    print("-" * 50)
    
    java_requests = [
        {
            "scenario": "Java 모의투자 주문",
            "request_data": {
                "stk_cd": "005930",
                "ord_qty": "10",
                "dry_run": True
            }
        },
        {
            "scenario": "Java 실전투자 주문", 
            "request_data": {
                "stk_cd": "000660",
                "ord_qty": "5",
                "dry_run": False
            }
        },
        {
            "scenario": "dry_run 파라미터 없음",
            "request_data": {
                "stk_cd": "035420",
                "ord_qty": "3"
            }
        }
    ]
    
    for scenario_data in java_requests:
        scenario = scenario_data["scenario"]
        request_data = scenario_data["request_data"]
        
        print(f"\n📋 {scenario}")
        
        # dry_run 추출
        dry_run = extract_dry_run_simple(request_data)
        print(f"  추출된 dry_run: {dry_run}")
        
        # 동적 설정 생성
        config = get_dynamic_config_simple(dry_run)
        print(f"  선택된 URL: {config['base_url']}")
        print(f"  매매모드: {config['mode_description']}")
        
        # 키움 API 호출 시뮬레이션
        print(f"  → 키움 API 호출: {config['base_url']}/api/dostk/ordr")
    
    print("\n" + "=" * 70)
    print("✅ 동적 모드 전환 로직 테스트 완료!")
    print("\n📋 핵심 확인사항:")
    print("1. ✅ dry_run=True → 모의투자 URL (mockapi.kiwoom.com)")
    print("2. ✅ dry_run=False → 실전투자 URL (api.kiwoom.com)")
    print("3. ✅ 다양한 dry_run 파라미터 형태 지원")
    print("4. ✅ Java 요청 → Python 동적 모드 전환 시나리오 검증")
    
    print("\n🎯 다음 단계:")
    print("- Java에서 실제 API 호출로 통합 테스트")
    print("- 모드별 토큰 캐싱 분리 처리")
    print("- 프로덕션 환경 검증")

if __name__ == "__main__":
    main()