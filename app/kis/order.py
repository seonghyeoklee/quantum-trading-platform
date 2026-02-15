"""KIS API 주문 - 매수/매도, 잔고 조회"""

import asyncio
import logging

from app.kis.auth import KISAuth
from app.models import AccountSummary, Position

logger = logging.getLogger(__name__)


class KISOrderClient:
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

    async def buy(self, symbol: str, quantity: int) -> dict:
        """시장가 매수 주문 (모의투자)"""
        return await self._order(symbol, quantity, side="buy")

    async def sell(self, symbol: str, quantity: int) -> dict:
        """시장가 매도 주문 (모의투자)"""
        return await self._order(symbol, quantity, side="sell")

    async def _order(self, symbol: str, quantity: int, side: str) -> dict:
        """주문 실행"""
        await self.auth.get_token()

        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"
        headers = self.auth.get_base_headers()

        # 모의투자 TR_ID (공식 스펙: VTTC0802U=매수, VTTC0801U=매도)
        if side == "buy":
            headers["tr_id"] = "VTTC0802U"
        else:
            headers["tr_id"] = "VTTC0801U"

        body = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.product_code,
            "PDNO": symbol,
            "ORD_DVSN": "01",  # 시장가
            "ORD_QTY": str(quantity),
            "ORD_UNPR": "0",  # 시장가는 0
        }

        # hashkey 발급 (주문 변조 방지 — 공식 스펙 필수)
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
                "%s 주문 성공: %s %d주 (주문번호: %s)",
                "매수" if side == "buy" else "매도",
                symbol,
                quantity,
                result["order_no"],
            )
        else:
            logger.warning(
                "%s 주문 실패: %s - %s",
                "매수" if side == "buy" else "매도",
                symbol,
                result["message"],
            )

        return result

    async def get_balance(self) -> tuple[list[Position], AccountSummary]:
        """잔고 조회 (모의투자) — 보유종목 + 계좌요약 반환"""
        await self.auth.get_token()

        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"

        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.product_code,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",  # 종목별
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "00",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }

        # KIS 모의투자 서버가 빠른 연속 요청 시 OPSQ2000 오류를 간헐적으로
        # 반환하는 문제가 있어 최대 2회 재시도
        _RETRY_DELAYS = [1, 2]
        data = None
        for attempt in range(len(_RETRY_DELAYS) + 1):
            headers = self.auth.get_base_headers()
            headers["tr_id"] = "VTTC8434R"
            data = await self._client.get(url, headers=headers, params=params)
            if data.get("rt_cd") == "0":
                break
            if attempt < len(_RETRY_DELAYS) and data.get("msg_cd") == "OPSQ2000":
                delay = _RETRY_DELAYS[attempt]
                logger.warning("잔고 조회 OPSQ2000 오류 — %d초 후 재시도 (%d/%d)", delay, attempt + 1, len(_RETRY_DELAYS))
                await asyncio.sleep(delay)

        if data.get("rt_cd") != "0":
            raise RuntimeError(
                f"잔고 조회 오류: {data.get('msg_cd')} - {data.get('msg1')}"
            )

        positions: list[Position] = []
        for item in data.get("output1", []):
            qty = int(item.get("hldg_qty", 0))
            if qty <= 0:
                continue
            positions.append(
                Position(
                    symbol=item.get("pdno", ""),
                    name=item.get("prdt_name", ""),
                    quantity=qty,
                    avg_price=float(item.get("pchs_avg_pric", 0)),
                    current_price=float(item.get("prpr", 0)),
                    eval_amount=float(item.get("evlu_amt", 0)),
                    profit_loss=float(item.get("evlu_pfls_amt", 0)),
                    profit_loss_rate=float(item.get("evlu_pfls_rt", 0)),
                )
            )

        summary = AccountSummary()
        output2 = data.get("output2", [])
        if output2:
            o2 = output2[0]
            summary = AccountSummary(
                deposit=float(o2.get("dnca_tot_amt", 0)),
                total_eval=float(o2.get("tot_evlu_amt", 0)),
                net_asset=float(o2.get("nass_amt", 0)),
                purchase_total=float(o2.get("pchs_amt_smtl_amt", 0)),
                eval_profit_loss=float(o2.get("evlu_pfls_smtl_amt", 0)),
                eval_profit_loss_rate=float(o2.get("asst_icdc_erng_rt", 0)),
            )

        return positions, summary

