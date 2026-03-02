"""섹터 모멘텀 스캐너 — 순수 함수 테스트"""

import pytest

from app.models import VolumeRankItem
from app.trading.sector import (
    SECTOR_MAP,
    ScannerPick,
    SectorScore,
    get_sector,
    score_sectors,
    select_leaders,
)


# ─── get_sector ───


def test_get_sector_known():
    """매핑된 종목은 올바른 섹터를 반환"""
    assert get_sector("005930") == "반도체"
    assert get_sector("035420") == "IT/플랫폼"
    assert get_sector("105560") == "금융"


def test_get_sector_unknown():
    """매핑 없는 종목은 '기타' 반환"""
    assert get_sector("999999") == "기타"
    assert get_sector("") == "기타"


def test_get_sector_all_mapped_have_sector():
    """SECTOR_MAP의 모든 값이 빈 문자열이 아닌지 확인"""
    for symbol, sector in SECTOR_MAP.items():
        assert sector, f"{symbol} has empty sector"


# ─── score_sectors ───


def _make_item(
    symbol: str = "005930",
    name: str = "삼성전자",
    price: float = 70000.0,
    change_rate: float = 2.0,
    volume: int = 500_000,
    vol_increase: float = 50.0,
    trade_amount: float = 1e10,
) -> VolumeRankItem:
    return VolumeRankItem(
        symbol=symbol,
        name=name,
        current_price=price,
        change_rate=change_rate,
        volume=volume,
        volume_increase_rate=vol_increase,
        trade_amount=trade_amount,
    )


def test_score_sectors_basic():
    """기본 스코어링: 반도체 섹터에 2종목"""
    items = [
        _make_item("005930", "삼성전자", change_rate=3.0, vol_increase=100.0),
        _make_item("000660", "SK하이닉스", change_rate=2.0, vol_increase=80.0),
    ]
    scores = score_sectors(items)
    assert len(scores) == 1
    assert scores[0].sector == "반도체"
    assert scores[0].stock_count == 2
    assert scores[0].avg_change_rate == pytest.approx(2.5)
    assert scores[0].avg_vol_increase == pytest.approx(90.0)


def test_score_sectors_filter_low_price():
    """동전주(저가) 필터링"""
    items = [
        _make_item("005930", price=500.0),  # 1000원 미만 → 필터
    ]
    scores = score_sectors(items, min_price=1000.0)
    assert len(scores) == 0


def test_score_sectors_filter_low_volume():
    """저거래량 필터링"""
    items = [
        _make_item("005930", volume=50_000),  # 100,000 미만 → 필터
    ]
    scores = score_sectors(items, min_volume=100_000)
    assert len(scores) == 0


def test_score_sectors_filter_negative_change():
    """하락 종목 필터링 (min_change_rate)"""
    items = [
        _make_item("005930", change_rate=-2.0),
    ]
    # -2.0 < 0.0 → 필터됨
    scores = score_sectors(items, min_change_rate=0.0)
    assert len(scores) == 0

    # min_change_rate를 음수로 설정하면 통과
    scores2 = score_sectors(items, min_change_rate=-5.0)
    assert len(scores2) == 1


def test_score_sectors_excludes_unknown():
    """'기타' 섹터 종목은 제외"""
    items = [
        _make_item("999999", "알수없는회사"),
    ]
    scores = score_sectors(items)
    assert len(scores) == 0


def test_score_sectors_sorted_descending():
    """스코어 내림차순 정렬"""
    items = [
        _make_item("005930", change_rate=1.0, vol_increase=10.0),
        _make_item("105560", change_rate=5.0, vol_increase=200.0),
    ]
    scores = score_sectors(items)
    assert len(scores) == 2
    assert scores[0].score >= scores[1].score


def test_score_sectors_multiple_sectors():
    """여러 섹터 동시 스코어링"""
    items = [
        _make_item("005930", change_rate=3.0, vol_increase=100.0),
        _make_item("000660", change_rate=2.0, vol_increase=80.0),
        _make_item("105560", "KB금융", change_rate=1.0, vol_increase=30.0),
        _make_item("009540", "HD한국조선해양", change_rate=4.0, vol_increase=150.0),
    ]
    scores = score_sectors(items)
    assert len(scores) == 3  # 반도체, 금융, 방산/조선
    sectors = {s.sector for s in scores}
    assert "반도체" in sectors
    assert "금융" in sectors
    assert "방산/조선" in sectors


# ─── select_leaders ───


def test_select_leaders_basic():
    """기본 대장주 선정"""
    items = [
        _make_item("005930", change_rate=3.0, volume=1_000_000, vol_increase=100.0),
        _make_item("000660", change_rate=2.0, volume=500_000, vol_increase=80.0),
        _make_item("105560", "KB금융", change_rate=1.5, volume=300_000, vol_increase=50.0),
    ]
    scores = score_sectors(items)
    picks = select_leaders(scores, top_n_sectors=3)
    assert len(picks) >= 1
    # 반도체 대장주는 삼성전자 (거래량 더 높음)
    semi_pick = [p for p in picks if p.sector == "반도체"]
    assert len(semi_pick) == 1
    assert semi_pick[0].symbol == "005930"


def test_select_leaders_max_picks():
    """max_picks 제한"""
    items = [
        _make_item("005930", change_rate=3.0, vol_increase=100.0),
        _make_item("105560", "KB금융", change_rate=2.0, vol_increase=50.0),
        _make_item("009540", "HD한국조선해양", change_rate=4.0, vol_increase=150.0),
    ]
    scores = score_sectors(items)
    picks = select_leaders(scores, top_n_sectors=5, max_picks=2)
    assert len(picks) <= 2


def test_select_leaders_empty():
    """빈 스코어 → 빈 결과"""
    picks = select_leaders([], top_n_sectors=3)
    assert picks == []


def test_select_leaders_returns_scanner_pick():
    """반환 타입이 ScannerPick인지 확인"""
    items = [
        _make_item("005930", change_rate=3.0, vol_increase=100.0),
    ]
    scores = score_sectors(items)
    picks = select_leaders(scores)
    assert len(picks) == 1
    pick = picks[0]
    assert isinstance(pick, ScannerPick)
    assert pick.symbol == "005930"
    assert pick.sector == "반도체"
    assert pick.score > 0


def test_select_leaders_top_n_limit():
    """top_n_sectors=1이면 1개 섹터만"""
    items = [
        _make_item("005930", change_rate=3.0, vol_increase=200.0),
        _make_item("105560", "KB금융", change_rate=1.0, vol_increase=10.0),
    ]
    scores = score_sectors(items)
    picks = select_leaders(scores, top_n_sectors=1)
    assert len(picks) == 1
