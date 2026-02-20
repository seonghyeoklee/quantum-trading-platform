"""KIS API 시세 조회 - 현재가, 일봉/분봉 차트"""

import logging
from datetime import datetime, timedelta

from app.kis.auth import KISAuth
from app.models import ChartData, StockPrice

logger = logging.getLogger(__name__)


class KISMarketClient:
    def __init__(self, auth: KISAuth):
        self.auth = auth

    @property
    def base_url(self) -> str:
        return self.auth.config.base_url

    @property
    def _client(self):
        return self.auth._client

    async def get_current_price(self, symbol: str) -> StockPrice:
        """주식 현재가 조회"""
        await self.auth.get_token()

        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = self.auth.get_base_headers()
        headers["tr_id"] = "FHKST01010100"

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol,
        }

        data = await self._client.get(url, headers=headers, params=params)

        if data.get("rt_cd") != "0":
            logger.error(
                "KIS 현재가 조회 실패: %s (rt_cd=%s, msg_cd=%s, msg1=%s)",
                symbol, data.get("rt_cd"), data.get("msg_cd"), data.get("msg1"),
            )
            raise RuntimeError(
                f"KIS API 오류: {data.get('msg_cd')} - {data.get('msg1')}"
            )

        output = data.get("output")
        if not output:
            raise RuntimeError(
                f"KIS API 현재가 응답에 output 필드 없음: {symbol} (rt_cd={data.get('rt_cd')})"
            )
        return StockPrice(
            symbol=symbol,
            name=output.get("hts_kor_isnm", ""),
            current_price=float(output.get("stck_prpr", 0)),
            change=float(output.get("prdy_vrss", 0)),
            change_rate=float(output.get("prdy_ctrt", 0)),
            volume=int(output.get("acml_vol", 0)),
            high=float(output.get("stck_hgpr", 0)),
            low=float(output.get("stck_lwpr", 0)),
            opening=float(output.get("stck_oprc", 0)),
        )

    async def get_daily_chart(
        self, symbol: str, days: int = 30
    ) -> list[ChartData]:
        """일봉 차트 조회"""
        await self.auth.get_token()

        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        headers = self.auth.get_base_headers()
        headers["tr_id"] = "FHKST03010100"

        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days + 30)).strftime("%Y%m%d")

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol,
            "FID_INPUT_DATE_1": start_date,
            "FID_INPUT_DATE_2": end_date,
            "FID_PERIOD_DIV_CODE": "D",
            "FID_ORG_ADJ_PRC": "0",  # 수정주가
        }

        data = await self._client.get(url, headers=headers, params=params)

        if data.get("rt_cd") != "0":
            logger.error(
                "KIS 일봉 조회 실패: %s (rt_cd=%s, msg_cd=%s, msg1=%s)",
                symbol, data.get("rt_cd"), data.get("msg_cd"), data.get("msg1"),
            )
            raise RuntimeError(
                f"KIS API 오류: {data.get('msg_cd')} - {data.get('msg1')}"
            )

        chart: list[ChartData] = []
        for item in data.get("output2", []):
            date = item.get("stck_bsop_date", "")
            if not date:
                continue
            chart.append(
                ChartData(
                    date=date,
                    open=float(item.get("stck_oprc", 0)),
                    high=float(item.get("stck_hgpr", 0)),
                    low=float(item.get("stck_lwpr", 0)),
                    close=float(item.get("stck_clpr", 0)),
                    volume=int(item.get("acml_vol", 0)),
                )
            )

        # 날짜 오름차순 정렬
        chart.sort(key=lambda c: c.date)
        return chart

    async def get_minute_chart(
        self, symbol: str, minutes: int = 120
    ) -> list[ChartData]:
        """분봉(1분) 차트 조회. 최대 30건씩 반복 호출로 minutes분 데이터 수집."""
        await self.auth.get_token()

        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"
        chart: list[ChartData] = []
        query_time = datetime.now().strftime("%H%M%S")
        max_calls = (minutes // 30) + 1

        for _ in range(max_calls):
            headers = self.auth.get_base_headers()
            headers["tr_id"] = "FHKST03010200"

            params = {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": symbol,
                "FID_INPUT_HOUR_1": query_time,
                "FID_PW_DATA_INCU_YN": "Y",
                "FID_ETC_CLS_CODE": "",
            }

            data = await self._client.get(url, headers=headers, params=params)

            if data.get("rt_cd") != "0":
                logger.error(
                    "KIS 분봉 조회 실패: %s (rt_cd=%s, msg_cd=%s, msg1=%s)",
                    symbol, data.get("rt_cd"), data.get("msg_cd"), data.get("msg1"),
                )
                raise RuntimeError(
                    f"KIS API 오류: {data.get('msg_cd')} - {data.get('msg1')}"
                )

            items = data.get("output2", [])
            if not items:
                break

            for item in items:
                hour = item.get("stck_cntg_hour", "")
                if not hour:
                    continue
                chart.append(
                    ChartData(
                        date=hour,
                        open=float(item.get("stck_oprc", 0)),
                        high=float(item.get("stck_hgpr", 0)),
                        low=float(item.get("stck_lwpr", 0)),
                        close=float(item.get("stck_prpr", 0)),
                        volume=int(item.get("cntg_vol", 0)),
                    )
                )

            if len(items) < 30:
                break

            # 마지막 봉의 시간을 다음 조회 시작점으로
            query_time = items[-1].get("stck_cntg_hour", "")
            if not query_time:
                break

            if len(chart) >= minutes:
                break

        # 시간 오름차순 정렬 + 중복 제거
        seen: set[str] = set()
        unique: list[ChartData] = []
        for c in chart:
            if c.date not in seen:
                seen.add(c.date)
                unique.append(c)
        unique.sort(key=lambda c: c.date)
        return unique
