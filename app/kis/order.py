"""KIS API 주문 - 매수/매도, 잔고 조회, 체결 확인"""

import logging
from datetime import datetime

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

    async def get_order_status(self, order_date: str, order_no: str) -> dict:
        """주문 체결 내역 조회 (모의투자).

        Args:
            order_date: 주문일자 (YYYYMMDD)
            order_no: 주문번호

        Returns:
            {
                "filled_quantity": int,   # 체결수량
                "filled_price": int,      # 체결단가
                "remaining_quantity": int, # 미체결수량
                "order_status": str,      # "filled" | "partial" | "pending"
            }
        """
        await self.auth.get_token()

        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-daily-ccld"
        headers = self.auth.get_base_headers()
        headers["tr_id"] = "VTTC8001R"

        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.product_code,
            "INQR_STRT_DT": order_date,
            "INQR_END_DT": order_date,
            "SLL_BUY_DVSN_CD": "00",  # 전체
            "INQR_DVSN": "00",
            "PDNO": "",
            "CCLD_DVSN": "00",
            "ORD_GNO_BRNO": "",
            "ODNO": order_no,
            "INQR_DVSN_3": "00",
            "INQR_DVSN_1": "",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }

        data = await self._client.get(url, headers=headers, params=params)

        if data.get("rt_cd") != "0":
            logger.warning(
                "체결 조회 오류: %s - %s", data.get("msg_cd"), data.get("msg1")
            )
            return {
                "filled_quantity": 0,
                "filled_price": 0,
                "remaining_quantity": 0,
                "order_status": "unknown",
            }

        # output1에서 해당 주문번호 찾기
        for item in data.get("output1", []):
            if item.get("odno") == order_no:
                filled_qty = int(item.get("tot_ccld_qty", 0))
                filled_price = int(float(item.get("avg_prvs", 0)))
                remaining_qty = int(item.get("rmn_qty", 0))

                if remaining_qty == 0 and filled_qty > 0:
                    status = "filled"
                elif filled_qty > 0:
                    status = "partial"
                else:
                    status = "pending"

                return {
                    "filled_quantity": filled_qty,
                    "filled_price": filled_price,
                    "remaining_quantity": remaining_qty,
                    "order_status": status,
                }

        return {
            "filled_quantity": 0,
            "filled_price": 0,
            "remaining_quantity": 0,
            "order_status": "not_found",
        }
