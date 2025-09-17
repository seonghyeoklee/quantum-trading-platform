#!/usr/bin/env python3
"""
한국 주식 실시간 모니터 - 최종 버전
간단하고 확실하게 작동하는 버전
"""

import sys
import time
from datetime import datetime
sys.path.extend(['../..', '.'])
import kis_auth as ka
from inquire_price import inquire_price

def show_live_data():
    """실시간 데이터 1회 표시"""
    stocks = [
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스"),
        ("035720", "카카오")
    ]

    current_time = datetime.now().strftime('%H:%M:%S')
    print(f"\n🇰🇷 한국 주식 LIVE - {current_time}")
    print("="*55)

    for code, name in stocks:
        try:
            result = inquire_price("real", "J", code)
            if result is not None and len(result) > 0:
                data = result.iloc[0]

                price = int(data['stck_prpr'])      # 현재가
                change = int(data['prdy_vrss'])     # 전일대비
                change_pct = float(data['prdy_ctrt']) # 전일대비율
                volume = int(data['acml_vol'])      # 거래량

                # 신호 판단
                if change_pct >= 2.0:
                    signal = "🔵 강력매수"
                elif change_pct >= 1.0:
                    signal = "🔵 매수"
                elif change_pct <= -2.0:
                    signal = "🔴 강력매도"
                elif change_pct <= -1.0:
                    signal = "🔴 매도"
                else:
                    signal = "⚪ 관망"

                icon = "🟢" if change >= 0 else "🔴"
                print(f"{icon} {name:8} {price:8,}원 {change:+6,}원 ({change_pct:+5.2f}%) {signal}")
                print(f"   거래량: {volume:,}주")

        except Exception as e:
            print(f"❌ {name:8} 오류: {e}")

    print("="*55)

def main():
    """메인 - 선택 가능한 실행"""
    # KIS 인증
    try:
        ka.auth(svr="prod", product="01")
        print("✅ KIS API 인증 성공")
    except Exception as e:
        print(f"❌ 인증 실패: {e}")
        return

    print("\n🚀 한국 주식 실시간 모니터")
    print("1: 1회 조회")
    print("2: 실시간 루프 (5초)")

    choice = input("선택 (1 또는 2): ").strip()

    if choice == "1":
        show_live_data()
    elif choice == "2":
        print("\n💡 Ctrl+C로 중단")
        count = 0
        try:
            while True:
                count += 1
                show_live_data()
                print(f"📊 분석 #{count} - 5초 후 다시...")
                time.sleep(5)
        except KeyboardInterrupt:
            print(f"\n⏹️ 종료 (총 {count}회)")
    else:
        print("❌ 잘못된 선택")

if __name__ == "__main__":
    main()