#!/usr/bin/env python3
"""
실시간 한국 주식 간단 로그
"""

import sys
import time
from datetime import datetime
sys.path.extend(['../..', '.'])
import kis_auth as ka
from inquire_price import inquire_price

def main():
    """실시간 로그"""
    # KIS 인증
    ka.auth(svr="prod", product="01")

    stocks = [
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스"),
        ("035720", "카카오")
    ]

    count = 0

    try:
        while True:
            count += 1
            current_time = datetime.now().strftime('%H:%M:%S')
            print(f"\n🇰🇷 실시간 현황 - {current_time} (#{count})")
            print("="*50)

            for code, name in stocks:
                try:
                    result = inquire_price("real", "J", code)
                    if result is not None and len(result) > 0:
                        data = result.iloc[0]

                        price = int(data['stck_prpr'])
                        change = int(data['prdy_vrss'])
                        change_pct = float(data['prdy_ctrt'])
                        volume = int(data['acml_vol'])

                        icon = "🟢" if change >= 0 else "🔴"
                        print(f"{icon} {name:8} {price:8,}원 {change:+6,}원 ({change_pct:+5.2f}%) {volume:8,}주")

                except Exception as e:
                    print(f"❌ {name:8} 오류: {str(e)[:30]}")

            print("="*50)
            time.sleep(5)

    except KeyboardInterrupt:
        print(f"\n⏹️ 종료 (총 {count}회 분석)")

if __name__ == "__main__":
    main()