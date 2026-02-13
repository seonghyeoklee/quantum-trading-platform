"""KIS API 인증 - 토큰 발급 및 메모리 캐싱"""

import logging
from datetime import datetime

from app.config import KISConfig
from app.kis.client import KISClient

logger = logging.getLogger(__name__)


class KISAuth:
    """KIS API 토큰 관리 (메모리 캐싱)"""

    def __init__(self, config: KISConfig, client: KISClient):
        self.config = config
        self._client = client
        self._token: str | None = None
        self._token_expires: datetime | None = None

    @property
    def is_token_valid(self) -> bool:
        if not self._token or not self._token_expires:
            return False
        # 만료 1시간 전에 갱신
        remaining = (self._token_expires - datetime.now()).total_seconds()
        return remaining > 3600

    async def get_token(self) -> str:
        """유효한 토큰을 반환. 만료 임박 시 자동 갱신."""
        if self.is_token_valid:
            return self._token  # type: ignore

        await self._issue_token()
        return self._token  # type: ignore

    async def _issue_token(self) -> None:
        """KIS API 토큰 발급"""
        url = f"{self.config.base_url}/oauth2/tokenP"
        payload = {
            "grant_type": "client_credentials",
            "appkey": self.config.app_key,
            "appsecret": self.config.app_secret,
        }

        data = await self._client.post(url, json=payload)

        self._token = data["access_token"]
        expires_str = data["access_token_token_expired"]
        self._token_expires = datetime.strptime(expires_str, "%Y-%m-%d %H:%M:%S")
        logger.info("KIS 토큰 발급 완료 (만료: %s)", self._token_expires)

    def get_base_headers(self) -> dict[str, str]:
        """KIS API 공통 헤더 (토큰 포함)"""
        return {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self._token}",
            "appkey": self.config.app_key,
            "appsecret": self.config.app_secret,
            "custtype": "P",
        }
