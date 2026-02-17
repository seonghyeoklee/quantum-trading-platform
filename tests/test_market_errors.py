"""KIS 시세 API 에러 응답 처리 테스트 (국내 + 해외)"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.kis.market import KISMarketClient
from app.kis.overseas_market import KISOverseasMarketClient


def _make_domestic_client():
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
    return KISMarketClient(auth)


def _make_overseas_client():
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
    return KISOverseasMarketClient(auth)


# ─── 국내 현재가: output 필드 누락 ───


class TestDomesticCurrentPriceMissingOutput:
    @pytest.mark.asyncio
    async def test_output_none(self):
        """rt_cd=0이지만 output이 없는 비정상 응답"""
        client = _make_domestic_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "0",
        })
        with pytest.raises(RuntimeError, match="output 필드 없음"):
            await client.get_current_price("005930")

    @pytest.mark.asyncio
    async def test_output_empty_dict(self):
        """rt_cd=0이지만 output이 빈 dict"""
        client = _make_domestic_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "0",
            "output": {},
        })
        with pytest.raises(RuntimeError, match="output 필드 없음"):
            await client.get_current_price("005930")


# ─── 국내 현재가: rt_cd 에러 ───


class TestDomesticCurrentPriceRtCdError:
    @pytest.mark.asyncio
    async def test_rt_cd_error_raises(self):
        client = _make_domestic_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "1",
            "msg_cd": "EGW00123",
            "msg1": "종목코드 오류",
        })
        with pytest.raises(RuntimeError, match="KIS API 오류.*EGW00123"):
            await client.get_current_price("INVALID")


# ─── 국내 일봉: 빈 output2 ───


class TestDomesticDailyChartEmpty:
    @pytest.mark.asyncio
    async def test_empty_output2(self):
        """output2가 빈 리스트 → 빈 차트 반환"""
        client = _make_domestic_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "0",
            "output2": [],
        })
        chart = await client.get_daily_chart("005930", days=30)
        assert chart == []

    @pytest.mark.asyncio
    async def test_missing_output2(self):
        """output2 키 자체가 없음 → 빈 차트 반환"""
        client = _make_domestic_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "0",
        })
        chart = await client.get_daily_chart("005930", days=30)
        assert chart == []

    @pytest.mark.asyncio
    async def test_rt_cd_error(self):
        client = _make_domestic_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "1",
            "msg_cd": "EGW00201",
            "msg1": "조회 실패",
        })
        with pytest.raises(RuntimeError, match="KIS API 오류"):
            await client.get_daily_chart("005930")


# ─── 국내 분봉: 빈 응답 ───


class TestDomesticMinuteChartEmpty:
    @pytest.mark.asyncio
    async def test_empty_output2(self):
        client = _make_domestic_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "0",
            "output2": [],
        })
        chart = await client.get_minute_chart("005930", minutes=60)
        assert chart == []

    @pytest.mark.asyncio
    async def test_rt_cd_error(self):
        client = _make_domestic_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "1",
            "msg_cd": "EGW00301",
            "msg1": "분봉 조회 실패",
        })
        with pytest.raises(RuntimeError, match="KIS API 오류"):
            await client.get_minute_chart("005930")


# ─── 해외 현재가: output 필드 누락 ───


class TestOverseasCurrentPriceMissingOutput:
    @pytest.mark.asyncio
    async def test_output_none(self):
        client = _make_overseas_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "0",
        })
        with pytest.raises(RuntimeError, match="output 필드 없음"):
            await client.get_current_price("AAPL")

    @pytest.mark.asyncio
    async def test_output_empty_dict(self):
        client = _make_overseas_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "0",
            "output": {},
        })
        with pytest.raises(RuntimeError, match="output 필드 없음"):
            await client.get_current_price("AAPL")


# ─── 해외 일봉: 빈 응답 ───


class TestOverseasDailyChartEmpty:
    @pytest.mark.asyncio
    async def test_empty_output2(self):
        client = _make_overseas_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "0",
            "output2": [],
        })
        chart = await client.get_daily_chart("AAPL", days=30)
        assert chart == []

    @pytest.mark.asyncio
    async def test_missing_output2(self):
        client = _make_overseas_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "0",
        })
        chart = await client.get_daily_chart("AAPL", days=30)
        assert chart == []

    @pytest.mark.asyncio
    async def test_rt_cd_error_logs_and_raises(self):
        client = _make_overseas_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "1",
            "msg_cd": "ERR_DAILY",
            "msg1": "일봉 오류",
        })
        with pytest.raises(RuntimeError, match="KIS 해외일봉 오류.*ERR_DAILY"):
            await client.get_daily_chart("AAPL")


# ─── 해외 분봉: 빈 응답 ───


class TestOverseasMinuteChartEmpty:
    @pytest.mark.asyncio
    async def test_empty_output2(self):
        client = _make_overseas_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "0",
            "output1": {},
            "output2": [],
        })
        chart = await client.get_minute_chart("AAPL", minutes=60)
        assert chart == []

    @pytest.mark.asyncio
    async def test_rt_cd_error(self):
        client = _make_overseas_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "1",
            "msg_cd": "ERR_MIN",
            "msg1": "분봉 조회 실패",
        })
        with pytest.raises(RuntimeError, match="KIS 해외분봉 오류"):
            await client.get_minute_chart("AAPL")
