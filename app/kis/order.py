"""KIS API 주문 - 매수/매도, 잔고 조회"""

import logging

from app.kis.auth import KISAuth
from app.models import Position

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

        # 모의투자 TR_ID
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

    async def get_balance(self) -> list[Position]:
        """잔고 조회 (모의투자)"""
        await self.auth.get_token()

        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
        headers = self.auth.get_base_headers()
        headers["tr_id"] = "VTTC8434R"

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

        data = await self._client.get(url, headers=headers, params=params)

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
                    current_price=int(item.get("prpr", 0)),
                    eval_amount=int(item.get("evlu_amt", 0)),
                    profit_loss=int(item.get("evlu_pfls_amt", 0)),
                    profit_loss_rate=float(item.get("evlu_pfls_rt", 0)),
                )
            )

        return positions

