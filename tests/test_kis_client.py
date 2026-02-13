"""KIS API 호출 통합 테스트 (모의투자 환경)

실행 조건:
- ~/KIS/config/kis_devlp.yaml 에 모의투자 키가 설정되어 있어야 함
- KIS_APP_KEY, KIS_APP_SECRET 환경변수로도 설정 가능

실행:
    uv run pytest tests/test_kis_client.py -v -s
"""

import os

import pytest

from app.config import load_settings
from app.kis.auth import KISAuth
from app.kis.client import KISClient
from app.kis.market import KISMarketClient
from app.kis.order import KISOrderClient

# KIS API 키가 없으면 테스트 스킵
_settings = load_settings()
_skip = not _settings.kis.app_key
skip_reason = "KIS API 키가 설정되지 않았습니다. (kis_devlp.yaml 또는 환경변수)"


@pytest.fixture
def auth():
    client = KISClient(timeout=_settings.kis.timeout)
    return KISAuth(_settings.kis, client)


@pytest.fixture
def market(auth):
    return KISMarketClient(auth)


@pytest.fixture
def order(auth):
    return KISOrderClient(auth)


@pytest.mark.skipif(_skip, reason=skip_reason)
class TestKISAuth:
    async def test_get_token(self, auth: KISAuth):
        token = await auth.get_token()
        assert token is not None
        assert len(token) > 0
        assert auth.is_token_valid

    async def test_token_reuse(self, auth: KISAuth):
        token1 = await auth.get_token()
        token2 = await auth.get_token()
        assert token1 == token2


@pytest.mark.skipif(_skip, reason=skip_reason)
class TestKISMarket:
    async def test_current_price(self, market: KISMarketClient):
        price = await market.get_current_price("005930")
        assert price.symbol == "005930"
        assert price.current_price > 0

    async def test_daily_chart(self, market: KISMarketClient):
        chart = await market.get_daily_chart("005930", days=30)
        assert len(chart) > 0
        assert chart[0].close > 0
        # 날짜 오름차순
        dates = [c.date for c in chart]
        assert dates == sorted(dates)


@pytest.mark.skipif(_skip, reason=skip_reason)
class TestKISOrder:
    async def test_get_balance(self, order: KISOrderClient):
        positions, summary = await order.get_balance()
        assert isinstance(positions, list)
