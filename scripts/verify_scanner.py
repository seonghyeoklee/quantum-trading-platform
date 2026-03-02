"""섹터 모멘텀 스캐너 E2E 검증 스크립트

실제 KIS API를 호출하여 거래량 순위 → 섹터 스코어링 → 대장주 선정 전체 흐름 검증.
장외 시간에는 시뮬레이션 데이터로 파이프라인 동작을 검증.
"""

import asyncio
import sys

from app.config import load_settings
from app.kis.auth import KISAuth
from app.kis.client import KISClient
from app.kis.volume_rank import KISVolumeRankClient
from app.models import VolumeRankItem
from app.trading.sector import (
    get_sector,
    score_sectors,
    select_leaders,
)


def _build_simulation_data() -> list[VolumeRankItem]:
    """장외 시간용 현실적인 시뮬레이션 데이터 (30종목)"""
    raw = [
        # 반도체 수급 집중 (3종목)
        ("005930", "삼성전자", 72000, 3.21, 18_500_000, 185.3, 1.33e12),
        ("000660", "SK하이닉스", 182000, 4.57, 8_200_000, 220.1, 1.49e12),
        ("042700", "한미반도체", 95000, 5.89, 3_100_000, 310.5, 2.95e11),
        # 방산/조선 수급 집중 (4종목)
        ("009540", "HD한국조선해양", 165000, 6.12, 4_500_000, 280.7, 7.43e11),
        ("329180", "HD현대중공업", 210000, 5.43, 3_800_000, 250.2, 7.98e11),
        ("012450", "한화에어로스페이스", 320000, 4.87, 2_900_000, 195.8, 9.28e11),
        ("064350", "현대로템", 58000, 7.23, 6_200_000, 340.1, 3.60e11),
        # 전력/전기장비 (3종목)
        ("034020", "두산에너빌리티", 22000, 3.77, 12_000_000, 175.4, 2.64e11),
        ("298040", "효성중공업", 310000, 2.98, 1_500_000, 130.2, 4.65e11),
        ("010120", "LS일렉트릭", 175000, 4.12, 2_200_000, 160.8, 3.85e11),
        # 2차전지 (2종목)
        ("373220", "LG에너지솔루션", 380000, 1.87, 1_800_000, 90.3, 6.84e11),
        ("247540", "에코프로비엠", 105000, 2.43, 2_500_000, 110.7, 2.63e11),
        # 바이오 (2종목)
        ("207940", "삼성바이오로직스", 890000, 1.23, 500_000, 65.2, 4.45e11),
        ("068270", "셀트리온", 180000, 1.98, 1_200_000, 85.4, 2.16e11),
        # 금융 (2종목)
        ("105560", "KB금융", 82000, 0.87, 1_500_000, 45.3, 1.23e11),
        ("055550", "신한지주", 52000, 0.65, 1_100_000, 38.7, 5.72e10),
        # IT/플랫폼 (2종목)
        ("035420", "NAVER", 195000, -0.51, 1_800_000, 55.2, 3.51e11),
        ("035720", "카카오", 42000, -1.23, 3_500_000, 80.1, 1.47e11),
        # 자동차 (2종목)
        ("005380", "현대차", 230000, 0.43, 1_200_000, 30.5, 2.76e11),
        ("000270", "기아", 115000, 0.21, 1_500_000, 35.8, 1.73e11),
        # 철강/소재 (1종목)
        ("005490", "POSCO홀딩스", 320000, -0.31, 800_000, 20.1, 2.56e11),
        # 에너지/화학 (1종목)
        ("051910", "LG화학", 290000, -0.87, 600_000, 15.3, 1.74e11),
        # 건설 (1종목)
        ("000720", "현대건설", 35000, 0.57, 900_000, 25.4, 3.15e10),
        # 통신 (1종목)
        ("017670", "SK텔레콤", 58000, 0.17, 400_000, 10.2, 2.32e10),
        # 엔터/미디어 (1종목)
        ("352820", "하이브", 215000, 1.42, 1_100_000, 70.8, 2.37e11),
        # 기타 (미매핑 종목 — 기타 섹터 테스트)
        ("196170", "알테오젠", 250000, 8.50, 5_000_000, 400.2, 1.25e12),
        ("460860", "에이피알", 85000, 6.30, 4_200_000, 350.1, 3.57e11),
        ("003670", "포스코퓨처엠", 195000, 3.10, 1_900_000, 120.5, 3.71e11),
        ("028300", "HLB", 65000, 9.20, 7_000_000, 450.3, 4.55e11),
        ("090430", "아모레퍼시픽", 110000, 2.10, 700_000, 55.8, 7.70e10),
    ]
    return [
        VolumeRankItem(
            symbol=r[0], name=r[1], current_price=r[2],
            change_rate=r[3], volume=r[4],
            volume_increase_rate=r[5], trade_amount=r[6],
        )
        for r in raw
    ]


async def main():
    settings = load_settings()
    client = KISClient(timeout=settings.kis.timeout)
    auth = KISAuth(settings.kis, client)
    volume_rank = KISVolumeRankClient(auth)

    print("=" * 70)
    print("  섹터 모멘텀 스캐너 E2E 검증")
    print("=" * 70)

    # ── Step 1: 거래량 순위 API 호출 ──
    print("\n[1] KIS 거래량 순위 API 호출 (상위 30종목)...")
    is_simulation = False
    try:
        items = await volume_rank.get_volume_ranking(top_n=30)
        if not items:
            print("  ⚠️  장외 시간 — 시뮬레이션 데이터로 검증합니다")
            items = _build_simulation_data()
            is_simulation = True
    except Exception as e:
        print(f"  ⚠️  API 호출 실패 ({e}) — 시뮬레이션 데이터로 검증합니다")
        items = _build_simulation_data()
        is_simulation = True

    source = "시뮬레이션" if is_simulation else "실시간"
    print(f"  ✅ {len(items)}개 종목 조회 완료 ({source})\n")

    print(f"  {'순위':>4}  {'종목코드':<8} {'종목명':<16} {'현재가':>10} {'등락률':>8} {'거래량':>14} {'거래량증가':>10} {'섹터':<14}")
    print("  " + "-" * 96)
    for i, item in enumerate(items, 1):
        sector = get_sector(item.symbol)
        print(
            f"  {i:>4}  {item.symbol:<8} {item.name:<16} "
            f"{item.current_price:>10,.0f} {item.change_rate:>+7.2f}% "
            f"{item.volume:>14,} {item.volume_increase_rate:>+9.1f}% "
            f"{sector:<14}"
        )

    # ── Step 2: 섹터 스코어링 ──
    print(f"\n[2] 섹터 스코어링 (min_price=1000, min_volume=100,000)...")
    sector_scores = score_sectors(
        items,
        min_price=1000.0,
        min_volume=100_000,
        min_change_rate=0.0,
    )

    if not sector_scores:
        print("  ⚠️  스코어링 결과 없음")
    else:
        print(f"  ✅ {len(sector_scores)}개 섹터 감지\n")
        print(f"  {'순위':>4}  {'섹터':<14} {'스코어':>8} {'종목수':>6} {'평균등락':>8} {'평균거래량증가':>14}")
        print("  " + "-" * 62)
        for i, s in enumerate(sector_scores, 1):
            bar = "█" * min(int(s.score / 2), 30)
            print(
                f"  {i:>4}  {s.sector:<14} {s.score:>8.1f} "
                f"{s.stock_count:>6} {s.avg_change_rate:>+7.2f}% "
                f"{s.avg_vol_increase:>+13.1f}%  {bar}"
            )

    # ── Step 3: 대장주 선정 ──
    print(f"\n[3] 대장주 선정 (상위 3개 섹터, 최대 5종목)...")
    picks = select_leaders(sector_scores, top_n_sectors=3, max_picks=5)

    if not picks:
        print("  ⚠️  선정된 종목 없음")
    else:
        print(f"  ✅ {len(picks)}개 종목 선정\n")
        print(f"  {'섹터':<14} {'종목코드':<8} {'종목명':<16} {'현재가':>10} {'등락률':>8} {'대장주스코어':>16}")
        print("  " + "-" * 76)
        for p in picks:
            print(
                f"  {p.sector:<14} {p.symbol:<8} {p.name:<16} "
                f"{p.current_price:>10,.0f} {p.change_rate:>+7.2f}% "
                f"{p.score:>16,.0f}"
            )

    # ── Step 4: 엔진 매매 대상 시뮬레이션 ──
    print(f"\n[4] 엔진 매매 대상 시뮬레이션...")
    scanner_symbols = [p.symbol for p in picks]

    # 시나리오 A: 보유 종목 없음
    held_a: list[str] = []
    all_a = list(dict.fromkeys(scanner_symbols + held_a))
    print(f"\n  [시나리오 A] 신규 진입 (보유 종목 없음)")
    print(f"    스캔 종목:    {scanner_symbols}")
    print(f"    보유 종목:    {held_a}")
    print(f"    → 매매 대상:  {all_a}")

    # 시나리오 B: 이전 스캔에서 매수한 종목이 이번 스캔에서 빠진 경우
    # KB금융(105560)을 이전에 매수했다고 가정
    held_b = ["105560"]
    all_b = list(dict.fromkeys(scanner_symbols + held_b))
    print(f"\n  [시나리오 B] 보유 종목이 스캔에서 빠진 경우")
    print(f"    스캔 종목:    {scanner_symbols}")
    print(f"    보유 종목:    {held_b} (이전 스캔에서 매수)")
    print(f"    → 매매 대상:  {all_b}")
    in_scan = "105560" in scanner_symbols
    print(f"    → KB금융(105560): 스캔 {'포함' if in_scan else '미포함'}, 보유 중이므로 매도/손절 관리 계속")

    # ── 결과 요약 ──
    print("\n" + "=" * 70)
    print("  검증 결과 요약")
    print("=" * 70)
    print(f"  데이터 소스:      {'📡 실시간 KIS API' if not is_simulation else '🔧 시뮬레이션 (장외시간)'}")
    print(f"  거래량 순위:      ✅ {len(items)}종목")
    print(f"  섹터 감지:        ✅ {len(sector_scores)}개 섹터 ('기타' 제외)")
    print(f"  수급 집중 섹터:   {', '.join(s.sector for s in sector_scores[:3])}")
    print(f"  대장주 선정:      ✅ {len(picks)}종목")
    for p in picks:
        print(f"    → {p.sector} 대장주: {p.name}({p.symbol}) {p.change_rate:+.2f}%")
    print()

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
