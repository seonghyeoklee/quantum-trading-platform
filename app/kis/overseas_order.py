"""KIS API 해외주식 주문 - 매수/매도, 잔고 조회 (미국 모의투자)"""

import asyncio
import logging

from app.kis.auth import KISAuth
from app.models import AccountSummary, Position

logger = logging.getLogger(__name__)

# 주문 API 거래소 코드 (시세 API와 다름)
EXCHANGE_CODE_ORDER: dict[str, str] = {
    "NAS": "NASD",
    "NYS": "NYSE",
    "AMS": "AMEX",
    "NASD": "NASD",
    "NYSE": "NYSE",
    "AMEX": "AMEX",
}

# 모의투자 TR_ID (미국)
TR_BUY = "VTTT1002U"
TR_SELL = "VTTT1006U"
TR_BALANCE = "VTTS3012R"


class KISOverseasOrderClient:
    """해외주식(미국) 주문 클라이언트 — 모의투자 전용"""

    def __init__(self, auth: KISAuth):
        self.auth = auth

    @property
    def base_url(self) -> str:
        return self.auth.config.base_url

    @property
    def account_no(self) -> str:
        return self.auth.config.account_no

    @property
    def product_code(self) -> str:
        return self.auth.config.account_product_code

    @property
    def _client(self):
        return self.auth._client

    def _resolve_exchange(self, exchange: str | None) -> str:
        """주문 API용 거래소 코드로 변환"""
        if exchange is None:
            return "NASD"
        return EXCHANGE_CODE_ORDER.get(exchange.upper(), exchange.upper())

    async def buy(
        self, symbol: str, quantity: int, exchange: str | None = None
    ) -> dict:
        """시장가 매수 주문 (미국 모의투자)"""
        return await self._order(symbol, quantity, side="buy", exchange=exchange)

    async def sell(
        self, symbol: str, quantity: int, exchange: str | None = None
    ) -> dict:
        """시장가 매도 주문 (미국 모의투자)"""
        return await self._order(symbol, quantity, side="sell", exchange=exchange)

    async def _order(
        self, symbol: str, quantity: int, side: str, exchange: str | None = None
    ) -> dict:
        """주문 실행"""
        await self.auth.get_token()

        url = f"{self.base_url}/uapi/overseas-stock/v1/trading/order"
        headers = self.auth.get_base_headers()

        if side == "buy":
            headers["tr_id"] = TR_BUY
        else:
            headers["tr_id"] = TR_SELL

        excg_cd = self._resolve_exchange(exchange)
        body = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.product_code,
            "OVRS_EXCG_CD": excg_cd,
            "PDNO": symbol,
            "ORD_QTY": str(quantity),
            "OVRS_ORD_UNPR": "0",  # 시장가
            "CTAC_TLNO": "",
            "MGCO_APTM_ODNO": "",
            "SLL_TYPE": "" if side == "buy" else "00",
            "ORD_SVR_DVSN_CD": "0",
            "ORD_DVSN": "00",
        }

        # hashkey 발급
        hashkey = await self.auth.get_hashkey(body)
        headers["hashkey"] = hashkey

        data = await self._client.post(url, headers=headers, json=body)

        success = data.get("rt_cd") == "0"
        output = data.get("output", {})

        result = {
            "success": success,
            "order_no": output.get("ODNO", ""),
            "message": data.get("msg1", ""),
        }

        if success:
            logger.info(
                "해외 %s 주문 성공: %s %d주 (주문번호: %s)",
                "매수" if side == "buy" else "매도",
                symbol,
                quantity,
                result["order_no"],
            )
        else:
            logger.warning(
                "해외 %s 주문 실패: %s - %s",
                "매수" if side == "buy" else "매도",
                symbol,
                result["message"],
            )

        return result

    async def get_balance(
        self, exchange: str | None = None
    ) -> tuple[list[Position], AccountSummary]:
        """해외주식 잔고 조회 (모의투자)"""
        await self.auth.get_token()

        url = f"{self.base_url}/uapi/overseas-stock/v1/trading/inquire-balance"

        # 거래소 빈값이면 전체 해외 잔고
        excg_cd = self._resolve_exchange(exchange) if exchange else ""

        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.product_code,
            "OVRS_EXCG_CD": excg_cd,
            "TR_CRCY_CD": "USD",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": "",
        }

        # OPSQ2000 재시도 (국내와 동일 패턴)
        _RETRY_DELAYS = [1, 2]
        data = None
        for attempt in range(len(_RETRY_DELAYS) + 1):
            headers = self.auth.get_base_headers()
            headers["tr_id"] = TR_BALANCE
            data = await self._client.get(url, headers=headers, params=params)
            if data.get("rt_cd") == "0":
                break
            if attempt < len(_RETRY_DELAYS) and data.get("msg_cd") == "OPSQ2000":
                delay = _RETRY_DELAYS[attempt]
                logger.warning(
                    "해외 잔고 조회 OPSQ2000 오류 — %d초 후 재시도 (%d/%d)",
                    delay, attempt + 1, len(_RETRY_DELAYS),
                )
                await asyncio.sleep(delay)

        if data.get("rt_cd") != "0":
            raise RuntimeError(
                f"해외 잔고 조회 오류: {data.get('msg_cd')} - {data.get('msg1')}"
            )

        positions: list[Position] = []
        for item in data.get("output1", []):
            qty = int(float(item.get("ovrs_cblc_qty", 0)))
            if qty <= 0:
                continue
            positions.append(
                Position(
                    symbol=item.get("ovrs_pdno", ""),
                    name=item.get("ovrs_item_name", ""),
                    quantity=qty,
                    avg_price=float(item.get("pchs_avg_pric", 0)),
                    current_price=float(item.get("now_pric2", 0)),
                    eval_amount=float(item.get("ovrs_stck_evlu_amt", 0)),
                    profit_loss=float(item.get("frcr_evlu_pfls_amt", 0)),
                    profit_loss_rate=float(item.get("evlu_pfls_rt", 0)),
                )
            )

        summary = AccountSummary()
        output2 = data.get("output2", {})
        # output2가 dict인 경우 (해외 잔고)
        if isinstance(output2, dict) and output2:
            summary = AccountSummary(
                deposit=float(output2.get("frcr_dncl_amt_2", 0)),
                total_eval=float(output2.get("tot_evlu_pfls_amt", 0)),
                eval_profit_loss=float(output2.get("ovrs_tot_pfls", 0)),
                eval_profit_loss_rate=float(output2.get("tot_pftrt", 0)),
            )
        elif isinstance(output2, list) and output2:
            o2 = output2[0]
            summary = AccountSummary(
                deposit=float(o2.get("frcr_dncl_amt_2", 0)),
                total_eval=float(o2.get("tot_evlu_pfls_amt", 0)),
                eval_profit_loss=float(o2.get("ovrs_tot_pfls", 0)),
                eval_profit_loss_rate=float(o2.get("tot_pftrt", 0)),
            )

        return positions, summary
