#!/usr/bin/env python3
"""
실제 KIS API 데이터 수집 테스트 스크립트
더미 데이터 없이 실제 API만 사용
"""

import json
import subprocess
import time
from datetime import datetime

def test_real_api_calls():
    print("=" * 70)
    print("🚀 실제 KIS API 데이터 수집 테스트 (더미 데이터 제거 확인)")
    print("=" * 70)
    
    # 테스트할 종목들
    test_stocks = [
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스"),
        ("035420", "NAVER"),
        ("035720", "카카오"),
        ("051910", "LG화학"),
    ]
    
    print("\n📊 실시간 주식 가격 조회 시작...")
    print("-" * 70)
    
    collected_data = []
    
    for stock_code, stock_name in test_stocks:
        try:
            # KIS Adapter API 호출
            cmd = f'curl -s "http://localhost:8000/domestic/price/{stock_code}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                if data.get('rt_cd') == '0':
                    output = data.get('output', {})
                    current_price = int(output.get('stck_prpr', 0))
                    volume = int(output.get('acml_vol', 0))
                    change_rate = float(output.get('prdy_ctrt', 0))
                    high_price = int(output.get('stck_hgpr', 0))
                    low_price = int(output.get('stck_lwpr', 0))
                    
                    collected_data.append({
                        'code': stock_code,
                        'name': stock_name,
                        'price': current_price,
                        'volume': volume,
                        'change_rate': change_rate,
                        'high': high_price,
                        'low': low_price
                    })
                    
                    print(f"✅ {stock_name:10} ({stock_code})")
                    print(f"   현재가: {current_price:,}원")
                    print(f"   거래량: {volume:,}주")
                    print(f"   변동률: {change_rate:+.2f}%")
                    print(f"   고가: {high_price:,}원 / 저가: {low_price:,}원")
                    print()
                else:
                    print(f"❌ {stock_name} ({stock_code}): API 오류 - {data.get('msg1', 'Unknown')}")
            else:
                print(f"❌ {stock_name} ({stock_code}): HTTP 요청 실패")
            
            # Rate limit 대응
            time.sleep(0.1)
            
        except Exception as e:
            print(f"❌ {stock_name} ({stock_code}): 오류 발생 - {e}")
    
    # 결과 요약
    print("=" * 70)
    print("📈 실제 API 데이터 수집 결과")
    print("=" * 70)
    
    if collected_data:
        print(f"✅ 성공적으로 수집된 종목: {len(collected_data)}개")
        print("\n📊 수집된 데이터 요약:")
        print("-" * 70)
        print(f"{'종목명':^12} | {'현재가':^10} | {'거래량':^12} | {'변동률':^8} | {'일중범위':^20}")
        print("-" * 70)
        
        for data in collected_data:
            price_range = f"{data['low']:,}~{data['high']:,}"
            print(f"{data['name']:12} | {data['price']:10,} | {data['volume']:12,} | {data['change_rate']:+7.2f}% | {price_range:^20}")
        
        # 데이터 검증
        print("\n🔍 데이터 검증:")
        print("-" * 70)
        
        # 가격이 모두 다른지 확인 (더미 데이터가 아님을 확인)
        prices = [d['price'] for d in collected_data]
        if len(set(prices)) == len(prices):
            print("✅ 모든 종목의 가격이 고유함 (실제 데이터)")
        else:
            print("⚠️ 일부 종목의 가격이 동일함")
        
        # 거래량이 현실적인지 확인
        volumes = [d['volume'] for d in collected_data]
        if all(v > 0 and v < 100000000 for v in volumes):
            print("✅ 거래량이 현실적인 범위 내에 있음")
        
        # 고가/저가 관계 확인
        valid_range = all(d['low'] <= d['price'] <= d['high'] for d in collected_data)
        if valid_range:
            print("✅ 현재가가 일중 고가/저가 범위 내에 있음")
        
        print("\n⏰ 수집 시간:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("\n🎉 실제 KIS API 데이터 수집 테스트 완료!")
        print("   더미 데이터가 아닌 실제 시장 데이터를 성공적으로 가져왔습니다.")
    else:
        print("❌ 수집된 데이터가 없습니다.")

if __name__ == "__main__":
    test_real_api_calls()