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
TR_BUYING_POWER = "VTTS3007R"


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

    async def get_buying_power(
        self, exchange: str | None = None
    ) -> float:
        """해외주식 매수가능금액 조회 (VTTS3007R)

        잔고조회(VTTS3012R)에서 예수금 필드가 누락되는 경우의 대안.
        Returns: 주문 가능 외화 금액 (USD)
        """
        await self.auth.get_token()

        url = f"{self.base_url}/uapi/overseas-stock/v1/trading/inquire-psamount"
        headers = self.auth.get_base_headers()
        headers["tr_id"] = TR_BUYING_POWER

        excg_cd = self._resolve_exchange(exchange) if exchange else "NASD"
        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.product_code,
            "OVRS_EXCG_CD": excg_cd,
            "OVRS_ORD_UNPR": "0",
            "ITEM_CD": "",
        }

        data = await self._client.get(url, headers=headers, params=params)
        if data.get("rt_cd") != "0":
            logger.warning(
                "해외 매수가능금액 조회 실패: %s - %s",
                data.get("msg_cd"), data.get("msg1"),
            )
            return 0.0

        output = data.get("output", {})
        return float(output.get("ovrs_ord_psbl_amt", 0))

    async def get_balance(
        self, exchange: str | None = None
    ) -> tuple[list[Position], AccountSummary]:
        """해외주식 잔고 조회 (모의투자)

        VTTS3012R로 보유종목 + 요약 조회 후, 예수금이 0이면
        VTTS3007R(매수가능금액)로 보완한다.
        """
        await self.auth.get_token()

        url = f"{self.base_url}/uapi/overseas-stock/v1/trading/inquire-balance"

        excg_cd = self._resolve_exchange(exchange) if exchange else "NASD"

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

        positions: list[Position] = []
        summary = AccountSummary()

        if data.get("rt_cd") == "0":
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

            output2 = data.get("output2", {})
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
        else:
            logger.warning(
                "해외 잔고 조회 실패: %s - %s (매수가능금액으로 보완)",
                data.get("msg_cd"), data.get("msg1"),
            )

        # 예수금이 0이면 매수가능금액 API로 보완
        if summary.deposit == 0:
            buying_power = await self.get_buying_power(exchange)
            if buying_power > 0:
                logger.info("해외 예수금 보완 (VTTS3007R): $%.2f", buying_power)
                summary.deposit = buying_power

        return positions, summary
