"""토큰 자동 관리 시스템

키움 API 호출 시 자동으로 토큰을 관리하는 시스템
- 캐시된 토큰 자동 조회
- 토큰 만료 시 자동 재발급
- 토큰 없을 시 자동 발급
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Handle both relative and absolute imports for different execution contexts
try:
    from ..auth.token_cache import token_cache
    from ..config.settings import settings
    from ..models.auth import CachedTokenInfo
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    from kiwoom_api.auth.token_cache import token_cache
    from kiwoom_api.config.settings import settings
    from kiwoom_api.models.auth import CachedTokenInfo

logger = logging.getLogger(__name__)


class TokenManager:
    """토큰 자동 관리 클래스"""
    
    def __init__(self):
        self._app_key = settings.KIWOOM_APP_KEY
        logger.info("토큰 매니저 초기화 완료")
    
    async def get_valid_token(self) -> str:
        """유효한 토큰 자동 획득
        
        1. 캐시에서 유효한 토큰 조회
        2. 없거나 만료된 경우 자동 재발급
        3. 발급된 토큰 반환
        
        Returns:
            str: 유효한 Bearer 토큰
            
        Raises:
            Exception: 토큰 발급 실패 시
        """
        logger.info("🔍 유효한 토큰 조회 시작")
        
        # 1. 캐시에서 유효한 토큰 조회
        cached_token = await token_cache.get_cached_token(self._app_key)
        
        if cached_token and not cached_token.is_expired():
            logger.info(f"✅ 캐시된 유효한 토큰 사용: {cached_token.token[:20]}...")
            return cached_token.token
        
        # 2. 토큰이 없거나 만료된 경우 자동 재발급
        logger.info("🔄 토큰 자동 재발급 시작")
        return await self._refresh_token()
    
    async def _refresh_token(self) -> str:
        """토큰 자동 재발급
        
        Returns:
            str: 새로 발급된 Bearer 토큰
            
        Raises:
            Exception: 토큰 발급 실패 시
        """
        try:
            # fn_au10001을 동적으로 import하여 순환 import 방지
            try:
                from ..functions.auth import fn_au10001
            except ImportError:
                from kiwoom_api.functions.auth import fn_au10001
            
            # 토큰 발급 요청
            result = await fn_au10001()
            
            if result['Code'] != 200:
                error_msg = f"토큰 발급 실패: {result.get('Body', {}).get('error', 'Unknown error')}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            token = result['Body'].get('token')
            if not token:
                error_msg = "토큰 발급 응답에 토큰이 없음"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            logger.info(f"✅ 토큰 자동 재발급 성공: {token[:20]}...")
            return token
            
        except Exception as e:
            error_msg = f"토큰 자동 재발급 실패: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)
    
    async def ensure_token_valid(self, token: Optional[str] = None) -> str:
        """토큰 유효성 보장
        
        Args:
            token: 기존 토큰 (선택적)
            
        Returns:
            str: 유효한 Bearer 토큰
        """
        if token:
            # 제공된 토큰이 있으면 해당 토큰 사용 (검증은 하지 않음)
            logger.info(f"🎯 제공된 토큰 사용: {token[:20]}...")
            return token
        
        # 토큰이 없으면 자동 관리 시스템 사용
        return await self.get_valid_token()


# 전역 토큰 매니저 인스턴스
token_manager = TokenManager()