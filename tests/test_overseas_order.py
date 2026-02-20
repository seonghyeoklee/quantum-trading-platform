"""해외주식 주문 클라이언트 단위 테스트"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.kis.overseas_order import (
    EXCHANGE_CODE_ORDER,
    TR_BALANCE,
    TR_BUY,
    TR_SELL,
    KISOverseasOrderClient,
)
from app.models import AccountSummary, Position


def _make_client():
    auth = MagicMock()
    auth.config.base_url = "https://test.example.com"
    auth.config.account_no = "12345678"
    auth.config.account_product_code = "01"
    auth.get_token = AsyncMock()
    auth.get_hashkey = AsyncMock(return_value="testhash")
    auth.get_base_headers.return_value = {
        "Content-Type": "application/json",
        "authorization": "Bearer test",
        "appkey": "key",
        "appsecret": "secret",
        "custtype": "P",
        "tr_cont": "",
        "personalseckey": "",
    }
    return KISOverseasOrderClient(auth)


class TestExchangeCodeMapping:
    def test_order_codes(self):
        assert EXCHANGE_CODE_ORDER["NAS"] == "NASD"
        assert EXCHANGE_CODE_ORDER["NYS"] == "NYSE"
        assert EXCHANGE_CODE_ORDER["AMS"] == "AMEX"

    def test_resolve_none_defaults_nasd(self):
        client = _make_client()
        assert client._resolve_exchange(None) == "NASD"


class TestTRIDs:
    def test_buy_tr_id(self):
        assert TR_BUY == "VTTT1002U"

    def test_sell_tr_id(self):
        assert TR_SELL == "VTTT1006U"

    def test_balance_tr_id(self):
        assert TR_BALANCE == "VTTS3012R"


class TestBuySell:
    @pytest.mark.asyncio
    async def test_buy_success(self):
        client = _make_client()
        client._client.post = AsyncMock(return_value={
            "rt_cd": "0",
            "output": {"ODNO": "US001"},
            "msg1": "ok",
        })

        result = await client.buy("AAPL", 5, exchange="NAS")

        assert result["success"] is True
        assert result["order_no"] == "US001"

        # TR_ID 확인
        call_kwargs = client._client.post.call_args
        headers = call_kwargs.kwargs["headers"]
        assert headers["tr_id"] == TR_BUY

        body = call_kwargs.kwargs["json"]
        assert body["PDNO"] == "AAPL"
        assert body["ORD_QTY"] == "5"
        assert body["OVRS_EXCG_CD"] == "NASD"

    @pytest.mark.asyncio
    async def test_sell_success(self):
        client = _make_client()
        client._client.post = AsyncMock(return_value={
            "rt_cd": "0",
            "output": {"ODNO": "US002"},
            "msg1": "ok",
        })

        result = await client.sell("AAPL", 3, exchange="NYS")

        assert result["success"] is True
        call_kwargs = client._client.post.call_args
        headers = call_kwargs.kwargs["headers"]
        assert headers["tr_id"] == TR_SELL

        body = call_kwargs.kwargs["json"]
        assert body["OVRS_EXCG_CD"] == "NYSE"
        assert body["SLL_TYPE"] == "00"

    @pytest.mark.asyncio
    async def test_buy_failure(self):
        client = _make_client()
        client._client.post = AsyncMock(return_value={
            "rt_cd": "1",
            "output": {},
            "msg1": "Insufficient balance",
        })

        result = await client.buy("TSLA", 10)
        assert result["success"] is False
        assert "Insufficient" in result["message"]

    @pytest.mark.asyncio
    async def test_hashkey_included(self):
        client = _make_client()
        client._client.post = AsyncMock(return_value={
            "rt_cd": "0", "output": {"ODNO": "1"}, "msg1": "",
        })

        await client.buy("NVDA", 1)
        call_kwargs = client._client.post.call_args
        assert call_kwargs.kwargs["headers"]["hashkey"] == "testhash"


class TestGetBalance:
    @pytest.mark.asyncio
    async def test_parse_positions(self):
        client = _make_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "0",
            "output1": [
                {
                    "ovrs_pdno": "AAPL",
                    "ovrs_item_name": "APPLE INC",
                    "ovrs_cblc_qty": "10",
                    "pchs_avg_pric": "175.50",
                    "now_pric2": "185.00",
                    "ovrs_stck_evlu_amt": "1850.00",
                    "frcr_evlu_pfls_amt": "95.00",
                    "evlu_pfls_rt": "5.41",
                },
            ],
            "output2": {
                "frcr_dncl_amt_2": "5000.00",
                "tot_evlu_pfls_amt": "1850.00",
                "ovrs_tot_pfls": "95.00",
                "tot_pftrt": "5.41",
            },
        })

        positions, summary = await client.get_balance()

        assert len(positions) == 1
        pos = positions[0]
        assert pos.symbol == "AAPL"
        assert pos.quantity == 10
        assert pos.avg_price == 175.50
        assert pos.current_price == 185.00
        assert pos.eval_amount == 1850.00

        assert summary.deposit == 5000.00
        assert summary.eval_profit_loss == 95.00

    @pytest.mark.asyncio
    async def test_empty_positions(self):
        client = _make_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "0",
            "output1": [],
            "output2": {},
        })

        positions, summary = await client.get_balance()
        assert positions == []
        assert summary.deposit == 0.0

    @pytest.mark.asyncio
    async def test_zero_qty_skipped(self):
        client = _make_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "0",
            "output1": [
                {"ovrs_pdno": "TSLA", "ovrs_cblc_qty": "0", "pchs_avg_pric": "0",
                 "now_pric2": "0", "ovrs_stck_evlu_amt": "0",
                 "frcr_evlu_pfls_amt": "0", "evlu_pfls_rt": "0"},
            ],
            "output2": {},
        })

        positions, _ = await client.get_balance()
        assert len(positions) == 0

    @pytest.mark.asyncio
    async def test_balance_error_returns_empty(self):
        """잔고조회 + 매수가능금액 모두 실패 시 빈 결과 반환 (에러 미발생)"""
        client = _make_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "1",
            "msg_cd": "ERR002",
            "msg1": "Server error",
        })

        positions, summary = await client.get_balance()
        assert positions == []
        assert summary.deposit == 0.0

    @pytest.mark.asyncio
    async def test_output2_list_format(self):
        """output2가 list 형식으로 오는 경우"""
        client = _make_client()
        client._client.get = AsyncMock(return_value={
            "rt_cd": "0",
            "output1": [],
            "output2": [{"frcr_dncl_amt_2": "3000", "tot_evlu_pfls_amt": "100",
                         "ovrs_tot_pfls": "50", "tot_pftrt": "1.5"}],
        })

        _, summary = await client.get_balance()
        assert summary.deposit == 3000.0
