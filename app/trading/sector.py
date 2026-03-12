"""섹터 모멘텀 스캐너 — 섹터 매핑, 스코어링, 대장주 선정

순수 함수 모듈 (외부 의존성 없음). strategy.py, regime.py 패턴.
"""

from __future__ import annotations

from typing import NamedTuple

from app.models import VolumeRankItem

# ── 종목코드 → 섹터 매핑 (~60개, 18개 섹터) ──
SECTOR_MAP: dict[str, str] = {
    # 반도체
    "005930": "반도체",   # 삼성전자
    "000660": "반도체",   # SK하이닉스
    "042700": "반도체",   # 한미반도체
    "403870": "반도체",   # HPSP
    # IT/플랫폼
    "035420": "IT/플랫폼",  # NAVER
    "035720": "IT/플랫폼",  # 카카오
    "259960": "IT/플랫폼",  # 크래프톤
    "263750": "IT/플랫폼",  # 펄어비스
    # 자동차
    "005380": "자동차",  # 현대차
    "000270": "자동차",  # 기아
    "012330": "자동차",  # 현대모비스
    "018880": "자동차",  # 한온시스템
    # 바이오
    "207940": "바이오",  # 삼성바이오로직스
    "068270": "바이오",  # 셀트리온
    "326030": "바이오",  # SK바이오팜
    "145020": "바이오",  # 휴젤
    # 금융
    "105560": "금융",    # KB금융
    "055550": "금융",    # 신한지주
    "086790": "금융",    # 하나금융지주
    "316140": "금융",    # 우리금융지주
    # 철강/소재
    "005490": "철강/소재",  # POSCO홀딩스
    "005010": "철강/소재",  # 휴스틸
    "004020": "철강/소재",  # 현대제철
    "010130": "철강/소재",  # 고려아연
    # 건설
    "000720": "건설",    # 현대건설
    "047040": "건설",    # 대우건설
    "006360": "건설",    # GS건설
    # 에너지/화학
    "051910": "에너지/화학",  # LG화학
    "096770": "에너지/화학",  # SK이노베이션
    "010950": "에너지/화학",  # S-Oil
    "006400": "에너지/화학",  # 삼성SDI
    # 방산/조선
    "009540": "방산/조선",   # HD한국조선해양
    "329180": "방산/조선",   # HD현대중공업
    "012450": "방산/조선",   # 한화에어로스페이스
    "064350": "방산/조선",   # 현대로템
    # 전력/전기장비
    "034020": "전력/전기장비",  # 두산에너빌리티
    "298040": "전력/전기장비",  # 효성중공업
    "010120": "전력/전기장비",  # LS일렉트릭
    "267260": "전력/전기장비",  # HD현대일렉트릭
    # 유통/소비재
    "004170": "유통/소비재",  # 신세계
    "023530": "유통/소비재",  # 롯데쇼핑
    "139480": "유통/소비재",  # 이마트
    "271560": "유통/소비재",  # 오리온
    # 통신
    "017670": "통신",    # SK텔레콤
    "030200": "통신",    # KT
    "032640": "통신",    # LG유플러스
    # 엔터/미디어
    "352820": "엔터/미디어",  # 하이브
    "041510": "엔터/미디어",  # SM
    "122870": "엔터/미디어",  # YG엔터
    # 운송/물류
    "003490": "운송/물류",   # 대한항공
    "020560": "운송/물류",   # 아시아나항공
    "028670": "운송/물류",   # 팬오션
    # 2차전지
    "373220": "2차전지",    # LG에너지솔루션
    "247540": "2차전지",    # 에코프로비엠
    "086520": "2차전지",    # 에코프로
    "006400": "2차전지",    # 삼성SDI (중복 — 에너지/화학에도)
    # 증권
    "039490": "증권",    # 키움증권
    "005940": "증권",    # NH투자증권
    "016360": "증권",    # 삼성증권
    # 로봇/AI
    "454910": "로봇/AI",    # 레인보우로보틱스
    "272210": "로봇/AI",    # 한화시스템
    "078930": "로봇/AI",    # GS
}


class SectorScore(NamedTuple):
    """섹터별 수급 스코어"""
    sector: str
    score: float
    stock_count: int
    avg_change_rate: float
    avg_vol_increase: float
    stocks: list[VolumeRankItem]


class ScannerPick(NamedTuple):
    """스캐너 선정 종목"""
    symbol: str
    name: str
    sector: str
    score: float          # 대장주 스코어
    current_price: float
    change_rate: float
    volume: int


def get_sector(symbol: str) -> str:
    """종목코드 → 섹터. 매핑 없으면 '기타'."""
    return SECTOR_MAP.get(symbol, "기타")


def score_sectors(
    items: list[VolumeRankItem],
    *,
    min_price: float = 1000.0,
    min_volume: int = 100_000,
    min_change_rate: float = 0.0,
) -> list[SectorScore]:
    """거래량 상위 종목들을 섹터별로 그룹핑하고 스코어링.

    필터: 동전주/저거래량/하락종목 제외.
    스코어: stock_count * 2.0 + avg_vol_increase * 0.01 + avg_change_rate * 0.5
    '기타' 섹터는 제외.
    """
    # 필터링
    filtered: list[VolumeRankItem] = []
    for item in items:
        if item.current_price < min_price:
            continue
        if item.volume < min_volume:
            continue
        if item.change_rate < min_change_rate:
            continue
        filtered.append(item)

    # 섹터별 그룹핑 (매핑 안 된 종목은 "기타"로 포함)
    sector_groups: dict[str, list[VolumeRankItem]] = {}
    for item in filtered:
        sector = get_sector(item.symbol)
        sector_groups.setdefault(sector, []).append(item)

    # 스코어 계산
    scores: list[SectorScore] = []
    for sector, stocks in sector_groups.items():
        count = len(stocks)
        avg_change = sum(s.change_rate for s in stocks) / count
        avg_vol_inc = sum(s.volume_increase_rate for s in stocks) / count
        score = count * 2.0 + avg_vol_inc * 0.01 + abs(avg_change) * 0.3
        scores.append(SectorScore(
            sector=sector,
            score=score,
            stock_count=count,
            avg_change_rate=avg_change,
            avg_vol_increase=avg_vol_inc,
            stocks=stocks,
        ))

    # 스코어 내림차순
    scores.sort(key=lambda s: s.score, reverse=True)
    return scores


def _leader_score(item: VolumeRankItem) -> float:
    """대장주 스코어: volume * (1 + change_rate/100) * (1 + vol_increase_rate/100)"""
    return item.volume * (1 + item.change_rate / 100) * (1 + item.volume_increase_rate / 100)


def select_leaders(
    sector_scores: list[SectorScore],
    *,
    top_n_sectors: int = 3,
    max_picks: int = 5,
) -> list[ScannerPick]:
    """상위 N개 섹터에서 대장주 1종목씩 선정.

    각 섹터 내 대장주 스코어 기준 1위 선정.
    전체 max_picks 이하로 제한.
    """
    picks: list[ScannerPick] = []

    for sector_info in sector_scores[:top_n_sectors]:
        if not sector_info.stocks:
            continue
        # 대장주 스코어 기준 정렬
        best = max(sector_info.stocks, key=_leader_score)
        picks.append(ScannerPick(
            symbol=best.symbol,
            name=best.name,
            sector=sector_info.sector,
            score=_leader_score(best),
            current_price=best.current_price,
            change_rate=best.change_rate,
            volume=best.volume,
        ))

        if len(picks) >= max_picks:
            break

    return picks
