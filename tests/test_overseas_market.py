"""해외주식 시세 클라이언트 단위 테스트"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.kis.overseas_market import (
    DEFAULT_EXCHANGE,
    EXCHANGE_CODE_QUOTE,
    KISOverseasMarketClient,
)
from app.models import ChartData, StockPrice


def _make_client():
    """KISOverseasMarketClient 인스턴스를 mock auth로 생성"""
    auth = MagicMock()
    auth.config.base_url = "https://test.example.com"
    auth.get_token = AsyncMock()
    auth.get_base_headers.return_value = {
        "Content-Type": "application/json",
        "authorization": "Bearer test",
        "appkey": "key",
        "appsecret": "secret",
        "custtype": "P",
        "tr_cont": "",
        "personalseckey": "",
    }
    client = KISOverseasMarketClient(auth)
    return client


class TestExchangeCodeMapping:
    def test_default_exchange(self):
        assert DEFAULT_EXCHANGE == "NAS"

    def test_nasd_to_nas(self):
        assert EXCHANGE_CODE_QUOTE["NASD"] == "NAS"

    def test_nyse_to_nys(self):
        assert EXCHANGE_CODE_QUOTE["NYSE"] == "NYS"

    def test_amex_to_ams(self):
        assert EXCHANGE_CODE_QUOTE["AMEX"] == "AMS"

    def test_resolve_none(self):
        client = _make_client()
        assert client._resolve_exchange(None) == "NAS"

    def test_resolve_case_insensitive(self):
        client = _make_client()
        assert client._resolve_exchange("nasd") == "NAS"
        assert client._resolve_exchange("nyse") == "NYS"


class TestGetCurrentPrice:
    @pytest.mark.asyncio
    async def test_parse_price(self):
        client = _make_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "0",
            "output": {
                "rsym": "DNASAAPL",
                "last": "185.50",
                "diff": "2.30",
                "rate": "1.26",
                "tvol": "52340000",
                "high": "186.10",
                "low": "183.20",
                "open": "184.00",
            },
        })

        price = await client.get_current_price("AAPL")

        assert isinstance(price, StockPrice)
        assert price.symbol == "AAPL"
        assert price.current_price == 185.50
        assert price.change == 2.30
        assert price.volume == 52340000
        assert price.high == 186.10
        assert price.low == 183.20

    @pytest.mark.asyncio
    async def test_api_error_raises(self):
        client = _make_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "1",
            "msg_cd": "ERR001",
            "msg1": "Not found",
        })

        with pytest.raises(RuntimeError, match="KIS 해외시세 오류"):
            await client.get_current_price("INVALID")

    @pytest.mark.asyncio
    async def test_exchange_param_passed(self):
        client = _make_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "0",
            "output": {"last": "100"},
        })

        await client.get_current_price("IBM", exchange="NYS")

        call_kwargs = client._client.get.call_args
        assert call_kwargs.kwargs["params"]["EXCD"] == "NYS"


class TestGetDailyChart:
    @pytest.mark.asyncio
    async def test_parse_daily(self):
        client = _make_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "0",
            "output2": [
                {"xymd": "20260210", "open": "180.0", "high": "185.0",
                 "low": "179.0", "clos": "183.5", "tvol": "1000000"},
                {"xymd": "20260211", "open": "183.5", "high": "186.0",
                 "low": "182.0", "clos": "185.0", "tvol": "1200000"},
            ],
        })

        chart = await client.get_daily_chart("AAPL", days=30)

        assert len(chart) == 2
        assert chart[0].date == "20260210"
        assert chart[0].close == 183.5
        assert chart[1].open == 183.5

    @pytest.mark.asyncio
    async def test_sorted_ascending(self):
        client = _make_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "0",
            "output2": [
                {"xymd": "20260211", "open": "1", "high": "1",
                 "low": "1", "clos": "185.0", "tvol": "100"},
                {"xymd": "20260210", "open": "1", "high": "1",
                 "low": "1", "clos": "183.0", "tvol": "100"},
            ],
        })

        chart = await client.get_daily_chart("TSLA", days=10)
        assert chart[0].date < chart[1].date


class TestGetMinuteChart:
    @pytest.mark.asyncio
    async def test_parse_minute(self):
        client = _make_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "0",
            "output1": {},
            "output2": [
                {"xymd": "20260210", "xhms": "093000", "open": "180.0",
                 "high": "181.0", "low": "179.5", "last": "180.5",
                 "evol": "500"},
                {"xymd": "20260210", "xhms": "093100", "open": "180.5",
                 "high": "181.5", "low": "180.0", "last": "181.0",
                 "evol": "600"},
            ],
        })

        chart = await client.get_minute_chart("AAPL", minutes=120)

        assert len(chart) == 2
        assert chart[0].date == "20260210 093000"
        assert chart[0].close == 180.5
        assert chart[0].volume == 500

    @pytest.mark.asyncio
    async def test_dedup_and_sort(self):
        """중복 시간 제거 + 오름차순 정렬"""
        client = _make_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "0",
            "output1": {},
            "output2": [
                {"xymd": "20260210", "xhms": "093100", "open": "1",
                 "high": "1", "low": "1", "last": "181", "evol": "1"},
                {"xymd": "20260210", "xhms": "093000", "open": "1",
                 "high": "1", "low": "1", "last": "180", "evol": "1"},
                {"xymd": "20260210", "xhms": "093000", "open": "1",
                 "high": "1", "low": "1", "last": "180", "evol": "1"},
            ],
        })

        chart = await client.get_minute_chart("AAPL", minutes=120)
        assert len(chart) == 2
        assert chart[0].date < chart[1].date
