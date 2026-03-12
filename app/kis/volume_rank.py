"""KIS API 거래량 순위 조회"""

import logging

from app.kis.auth import KISAuth
from app.models import VolumeRankItem

logger = logging.getLogger(__name__)


class KISVolumeRankClient:
    def __init__(self, auth: KISAuth):
        self.auth = auth

    @property
    def base_url(self) -> str:
        return self.auth.config.base_url

    @property
    def _client(self):
        return self.auth._client

    async def get_volume_ranking(self, top_n: int = 30) -> list[VolumeRankItem]:
        """거래량 상위 종목 조회 (TR_ID: FHPST01710000)"""
        await self.auth.get_token()

        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/volume-rank"
        headers = self.auth.get_base_headers()
        headers["tr_id"] = "FHPST01710000"

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",     # 주식
            "FID_COND_SCR_DIV_CODE": "20171",   # 거래량 순위 (공식 스펙)
            "FID_INPUT_ISCD": "0000",            # 전체
            "FID_DIV_CLS_CODE": "0",             # 전체
            "FID_BLNG_CLS_CODE": "0",            # 전체
            "FID_TRGT_CLS_CODE": "111111111",    # 전체
            "FID_TRGT_EXLS_CLS_CODE": "0000000000",  # 제외 없음 (10자리)
            "FID_INPUT_PRICE_1": "",              # 가격 조건 없음
            "FID_INPUT_PRICE_2": "",
            "FID_VOL_CNT": "",                    # 거래량 조건 없음
            "FID_INPUT_DATE_1": "",               # 날짜 조건 없음
        }

        data = await self._client.get(url, headers=headers, params=params)

        if data.get("rt_cd") != "0":
            logger.error(
                "KIS 거래량순위 조회 실패: rt_cd=%s, msg_cd=%s, msg1=%s",
                data.get("rt_cd"), data.get("msg_cd"), data.get("msg1"),
            )
            raise RuntimeError(
                f"KIS API 오류: {data.get('msg_cd')} - {data.get('msg1')}"
            )

        items: list[VolumeRankItem] = []
        for row in data.get("output", []):
            symbol = row.get("mksc_shrn_iscd", "")  # 종목코드 (6자리)
            if not symbol or len(symbol) != 6:
                continue
            # ETF/ETN 제외: 숫자 6자리인 일반 주식만
            if not symbol.isdigit():
                continue
            try:
                items.append(VolumeRankItem(
                    symbol=symbol,
                    name=row.get("hts_kor_isnm", ""),
                    current_price=float(row.get("stck_prpr", 0)),
                    change_rate=float(row.get("prdy_ctrt", 0)),
                    volume=int(row.get("acml_vol", 0)),
                    volume_increase_rate=float(row.get("vol_inrt", 0)),
                    trade_amount=float(row.get("acml_tr_pbmn", 0)),
                ))
            except (ValueError, TypeError):
                logger.warning("거래량순위 종목 파싱 실패: %s", symbol)
                continue
            if len(items) >= top_n:
                break

        return items
