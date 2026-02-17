"""KIS API 해외주식 시세 조회 - 현재가, 일봉/분봉 차트 (미국 시장)"""

import logging
from datetime import datetime, timedelta

from app.kis.auth import KISAuth
from app.models import ChartData, StockPrice

logger = logging.getLogger(__name__)

# 시세 API 거래소 코드 매핑
EXCHANGE_CODE_QUOTE: dict[str, str] = {
    "NASD": "NAS",
    "NYSE": "NYS",
    "AMEX": "AMS",
    # 편의: 축약형도 허용
    "NAS": "NAS",
    "NYS": "NYS",
    "AMS": "AMS",
}

DEFAULT_EXCHANGE = "NAS"  # NASDAQ


class KISOverseasMarketClient:
    """해외주식(미국) 시세 클라이언트"""

    def __init__(self, auth: KISAuth):
        self.auth = auth

    @property
    def base_url(self) -> str:
        return self.auth.config.base_url

    @property
    def _client(self):
        return self.auth._client

    def _resolve_exchange(self, exchange: str | None) -> str:
        """거래소 코드를 시세 API 코드로 변환"""
        if exchange is None:
            return DEFAULT_EXCHANGE
        return EXCHANGE_CODE_QUOTE.get(exchange.upper(), exchange.upper())

    async def get_current_price(
        self, symbol: str, exchange: str | None = None
    ) -> StockPrice:
        """해외주식 현재가 조회"""
        await self.auth.get_token()

        url = f"{self.base_url}/uapi/overseas-price/v1/quotations/price"
        headers = self.auth.get_base_headers()
        headers["tr_id"] = "HHDFS00000300"

        excd = self._resolve_exchange(exchange)
        params = {
            "AUTH": "",
            "EXCD": excd,
            "SYMB": symbol,
        }

        data = await self._client.get(url, headers=headers, params=params)

        if data.get("rt_cd") != "0":
            logger.error(
                "KIS 해외 현재가 조회 실패: %s (rt_cd=%s, msg_cd=%s, msg1=%s)",
                symbol, data.get("rt_cd"), data.get("msg_cd"), data.get("msg1"),
            )
            raise RuntimeError(
                f"KIS 해외시세 오류: {data.get('msg_cd')} - {data.get('msg1')}"
            )

        output = data.get("output")
        if not output:
            raise RuntimeError(
                f"KIS 해외 현재가 응답에 output 필드 없음: {symbol} (rt_cd={data.get('rt_cd')})"
            )
        return StockPrice(
            symbol=symbol,
            name=output.get("rsym", ""),
            current_price=float(output.get("last", 0)),
            change=float(output.get("diff", 0)),
            change_rate=float(output.get("rate", 0)),
            volume=int(float(output.get("tvol", 0))),
            high=float(output.get("high", 0)),
            low=float(output.get("low", 0)),
            opening=float(output.get("open", 0)),
        )

    async def get_daily_chart(
        self, symbol: str, exchange: str | None = None, days: int = 30
    ) -> list[ChartData]:
        """해외주식 일봉 차트 조회"""
        await self.auth.get_token()

        url = f"{self.base_url}/uapi/overseas-price/v1/quotations/dailyprice"
        headers = self.auth.get_base_headers()
        headers["tr_id"] = "HHDFS76240000"

        excd = self._resolve_exchange(exchange)
        end_date = datetime.now().strftime("%Y%m%d")
        # bymd 기준일 (이 날짜까지의 데이터를 역순으로 반환)

        params = {
            "AUTH": "",
            "EXCD": excd,
            "SYMB": symbol,
            "GUBN": "0",  # 일봉
            "BYMD": end_date,
            "MODP": "1",  # 수정주가
        }

        chart: list[ChartData] = []
        # 연속조회로 충분한 데이터 확보 (1회 최대 약 100건)
        max_calls = (days // 100) + 1
        for call_idx in range(max_calls):
            data = await self._client.get(url, headers=headers, params=params)

            if data.get("rt_cd") != "0":
                logger.error(
                    "KIS 해외 일봉 조회 실패: %s (rt_cd=%s, msg_cd=%s, msg1=%s)",
                    symbol, data.get("rt_cd"), data.get("msg_cd"), data.get("msg1"),
                )
                raise RuntimeError(
                    f"KIS 해외일봉 오류: {data.get('msg_cd')} - {data.get('msg1')}"
                )

            items = data.get("output2", [])
            if not items:
                break

            for item in items:
                date_str = item.get("xymd", "")
                if not date_str:
                    continue
                chart.append(
                    ChartData(
                        date=date_str,
                        open=float(item.get("open", 0)),
                        high=float(item.get("high", 0)),
                        low=float(item.get("low", 0)),
                        close=float(item.get("clos", 0)),
                        volume=int(float(item.get("tvol", 0))),
                    )
                )

            # 연속조회 여부 확인
            tr_cont = data.get("tr_cont", "")
            if tr_cont not in ("M", "F"):
                break
            if len(chart) >= days:
                break

            # 다음 페이지: 마지막 항목의 날짜를 기준으로
            headers["tr_cont"] = "N"
            params["BYMD"] = items[-1].get("xymd", "")

        # 날짜 오름차순 정렬 + days 제한
        chart.sort(key=lambda c: c.date)
        return chart[-days:] if len(chart) > days else chart

    async def get_minute_chart(
        self, symbol: str, exchange: str | None = None, minutes: int = 120
    ) -> list[ChartData]:
        """해외주식 분봉(1분) 차트 조회"""
        await self.auth.get_token()

        url = f"{self.base_url}/uapi/overseas-price/v1/quotations/inquire-time-itemchartprice"

        excd = self._resolve_exchange(exchange)
        chart: list[ChartData] = []
        next_key = ""
        max_calls = (minutes // 120) + 2  # nrec=120이므로

        for call_idx in range(max_calls):
            headers = self.auth.get_base_headers()
            headers["tr_id"] = "HHDFS76950200"
            if call_idx > 0:
                headers["tr_cont"] = "N"

            params = {
                "AUTH": "",
                "EXCD": excd,
                "SYMB": symbol,
                "NMIN": "1",
                "PINC": "1",  # 전일 포함
                "NEXT": "" if call_idx == 0 else "1",
                "NREC": "120",
                "FILL": "",
                "KEYB": next_key,
            }

            data = await self._client.get(url, headers=headers, params=params)

            if data.get("rt_cd") != "0":
                logger.error(
                    "KIS 해외 분봉 조회 실패: %s (rt_cd=%s, msg_cd=%s, msg1=%s)",
                    symbol, data.get("rt_cd"), data.get("msg_cd"), data.get("msg1"),
                )
                raise RuntimeError(
                    f"KIS 해외분봉 오류: {data.get('msg_cd')} - {data.get('msg1')}"
                )

            items = data.get("output2", [])
            if not items:
                break

            for item in items:
                # xhms: 현지시간 HHMMSS, xymd: 현지일자
                xhms = item.get("xhms", "")
                xymd = item.get("xymd", "")
                if not xhms:
                    continue
                date_str = f"{xymd} {xhms}" if xymd else xhms
                chart.append(
                    ChartData(
                        date=date_str,
                        open=float(item.get("open", 0)),
                        high=float(item.get("high", 0)),
                        low=float(item.get("low", 0)),
                        close=float(item.get("last", 0)),
                        volume=int(float(item.get("evol", 0))),
                    )
                )

            # 연속조회
            tr_cont = data.get("tr_cont", "")
            if tr_cont not in ("M", "F"):
                break
            if len(chart) >= minutes:
                break

            # 페이지네이션 키
            output1 = data.get("output1", {})
            next_key = output1.get("next", "")
            if not next_key:
                break

        # 시간 오름차순 정렬 + 중복 제거
        seen: set[str] = set()
        unique: list[ChartData] = []
        for c in chart:
            if c.date not in seen:
                seen.add(c.date)
                unique.append(c)
        unique.sort(key=lambda c: c.date)
        return unique[-minutes:] if len(unique) > minutes else unique
