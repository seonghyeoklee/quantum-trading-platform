"""KIS API 인증 - 토큰 발급, hashkey, 파일 캐싱"""

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

import httpx

from app.config import KISConfig
from app.kis.client import KISClient

logger = logging.getLogger(__name__)

# KST (UTC+9)
_KST = timezone(timedelta(hours=9))

# 만료 전 갱신 여유 시간 (초)
_TOKEN_REFRESH_MARGIN = 3600

# 토큰 캐시 파일 경로
_TOKEN_CACHE_DIR = Path.home() / ".cache" / "kis"
_TOKEN_CACHE_FILE = _TOKEN_CACHE_DIR / "token.json"


class KISAuth:
    """KIS API 토큰 관리 (파일 캐싱)"""

    def __init__(self, config: KISConfig, client: KISClient):
        self.config = config
        self._client = client
        self._token: str | None = None
        self._token_expires: datetime | None = None
        self._load_cached_token()

    def _load_cached_token(self) -> None:
        """파일에서 캐시된 토큰 로드"""
        if not _TOKEN_CACHE_FILE.exists():
            return
        try:
            data = json.loads(_TOKEN_CACHE_FILE.read_text())
            # 같은 앱키로 발급된 토큰만 사용
            if data.get("app_key") != self.config.app_key:
                return
            self._token = data["access_token"]
            self._token_expires = datetime.strptime(
                data["expires"], "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=_KST)
            if self.is_token_valid:
                logger.info("캐시된 토큰 로드 완료 (만료: %s)", self._token_expires)
            else:
                self._token = None
                self._token_expires = None
        except (json.JSONDecodeError, KeyError, ValueError):
            logger.warning("토큰 캐시 파일 손상 — 무시")

    def _save_token_cache(self) -> None:
        """토큰을 파일에 저장"""
        _TOKEN_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "app_key": self.config.app_key,
            "access_token": self._token,
            "expires": self._token_expires.strftime("%Y-%m-%d %H:%M:%S"),  # type: ignore
        }
        _TOKEN_CACHE_FILE.write_text(json.dumps(data))
        logger.debug("토큰 캐시 저장 완료")

    @property
    def is_token_valid(self) -> bool:
        if not self._token or not self._token_expires:
            return False
        remaining = (self._token_expires - datetime.now(_KST)).total_seconds()
        return remaining > _TOKEN_REFRESH_MARGIN

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
        self._token_expires = datetime.strptime(
            expires_str, "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=_KST)
        self._save_token_cache()
        logger.info("KIS 토큰 발급 완료 (만료: %s)", self._token_expires)

    def get_base_headers(self) -> dict[str, str]:
        """KIS API 공통 헤더 (토큰 포함)

        공식 스펙 기반 (kis_auth.py _getBaseHeader + _url_fetch):
        - Content-Type, authorization, appkey, appsecret: 기본 헤더
        - custtype: 개인("P") / 법인("B")
        - tr_cont: 연속조회 키 (초기값 빈 문자열)
        """
        return {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self._token}",
            "appkey": self.config.app_key,
            "appsecret": self.config.app_secret,
            "custtype": "P",
            "tr_cont": "",
            "personalseckey": "",
        }

    async def get_hashkey(self, body: dict) -> str:
        """주문 API용 hashkey 발급

        공식 스펙: POST /uapi/hashkey 에 주문 body를 보내면
        HASH 값을 반환. 주문 변조 방지용.
        """
        url = f"{self.config.base_url}/uapi/hashkey"
        headers = {
            "Content-Type": "application/json",
            "appkey": self.config.app_key,
            "appsecret": self.config.app_secret,
        }

        data = await self._client.post(url, headers=headers, json=body)
        return data.get("HASH", "")
