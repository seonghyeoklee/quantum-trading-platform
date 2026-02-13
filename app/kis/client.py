"""KIS API HTTP 클라이언트 래퍼 — 타임아웃, 재시도, rate limit"""

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

# 재시도 대상 HTTP 상태 코드
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}

# 재시도 백오프 (초)
_BACKOFF = [1, 2, 4]


class KISClient:
    """httpx 기반 KIS API 전용 HTTP 클라이언트.

    - 커넥션 풀 재사용
    - 요청당 타임아웃 10초
    - 실패 시 최대 3회 재시도 (지수 백오프)
    - Rate limit: Semaphore + sleep으로 초당 2회 제한
    """

    def __init__(self, timeout: float = 10.0) -> None:
        self._http = httpx.AsyncClient(timeout=timeout)
        # 동시 요청 1개 + 요청 간 0.5초 대기 → 초당 최대 2회
        self._semaphore = asyncio.Semaphore(1)

    async def close(self) -> None:
        await self._http.aclose()

    async def get(
        self,
        url: str,
        *,
        headers: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        return await self._request("GET", url, headers=headers, params=params)

    async def post(
        self,
        url: str,
        *,
        headers: dict | None = None,
        json: dict | None = None,
    ) -> dict:
        return await self._request("POST", url, headers=headers, json=json)

    async def _request(
        self,
        method: str,
        url: str,
        *,
        headers: dict | None = None,
        params: dict | None = None,
        json: dict | None = None,
    ) -> dict:
        last_exc: Exception | None = None

        for attempt in range(len(_BACKOFF) + 1):  # 0, 1, 2, 3 → 최초 + 3회 재시도
            async with self._semaphore:
                try:
                    resp = await self._http.request(
                        method, url, headers=headers, params=params, json=json
                    )
                    # rate limit 준수: 요청 후 0.5초 대기
                    await asyncio.sleep(0.5)

                    if resp.status_code in _RETRYABLE_STATUS:
                        logger.warning(
                            "KIS API %s %s → %d (시도 %d/%d)",
                            method, url, resp.status_code, attempt + 1, len(_BACKOFF) + 1,
                        )
                        last_exc = httpx.HTTPStatusError(
                            f"HTTP {resp.status_code}",
                            request=resp.request,
                            response=resp,
                        )
                    else:
                        resp.raise_for_status()
                        return resp.json()

                except (httpx.TimeoutException, httpx.ConnectError) as exc:
                    logger.warning(
                        "KIS API %s %s 네트워크 오류 (시도 %d/%d): %s",
                        method, url, attempt + 1, len(_BACKOFF) + 1, exc,
                    )
                    last_exc = exc

            # 백오프 대기 (마지막 시도 후에는 대기 없이 바로 raise)
            if attempt < len(_BACKOFF):
                await asyncio.sleep(_BACKOFF[attempt])

        raise last_exc  # type: ignore[misc]
