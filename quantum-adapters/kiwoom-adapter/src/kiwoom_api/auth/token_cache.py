"""토큰 캐싱 시스템

키움 OAuth 토큰의 메모리 기반 캐싱 시스템
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

# Handle both relative and absolute imports for different execution contexts
try:
    from ..models.auth import CachedTokenInfo
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    from kiwoom_api.models.auth import CachedTokenInfo

logger = logging.getLogger(__name__)


class InMemoryTokenCache:
    """메모리 기반 토큰 캐시
    
    간단한 딕셔너리 기반 토큰 캐싱
    향후 Redis나 데이터베이스로 확장 가능
    """
    
    def __init__(self):
        self._cache: Dict[str, CachedTokenInfo] = {}
        self._default_key = "default"
        logger.info("토큰 캐시 초기화 완료")
    
    async def get_cached_token(self, app_key: str) -> Optional[CachedTokenInfo]:
        """캐시된 토큰 조회
        
        Args:
            app_key: 앱키
            
        Returns:
            CachedTokenInfo: 캐시된 토큰 정보 (없으면 None)
        """
        token_info = self._cache.get(app_key)
        
        if token_info is None:
            logger.info(f"캐시된 토큰 없음 - 앱키: {app_key}")
            return None
            
        if token_info.is_expired():
            logger.info(f"캐시된 토큰 만료 - 앱키: {app_key}")
            # 만료된 토큰은 캐시에서 제거
            del self._cache[app_key]
            return None
        
        logger.info(
            f"캐시된 토큰 조회 성공 - 앱키: {app_key}, "
            f"토큰: {token_info.token}, 발급시간: {token_info.issued_at}"
        )
        return token_info
    
    async def cache_token(self, token_info: CachedTokenInfo) -> None:
        """토큰 캐싱
        
        Args:
            token_info: 캐싱할 토큰 정보
        """
        self._cache[token_info.app_key] = token_info
        
        # 기본 키로도 저장
        self._cache[self._default_key] = token_info
        
        logger.info(
            f"토큰 캐시 저장 완료 - 앱키: {token_info.app_key}, "
            f"만료시간: {token_info.expires_at}"
        )
    
    async def get_default_token(self) -> Optional[CachedTokenInfo]:
        """기본 토큰 조회"""
        return await self.get_cached_token(self._default_key)
    
    async def clear_cache(self, app_key: Optional[str] = None) -> None:
        """캐시 삭제
        
        Args:
            app_key: 삭제할 앱키 (None이면 전체 삭제)
        """
        if app_key is None:
            self._cache.clear()
            logger.info("전체 토큰 캐시 삭제")
        else:
            self._cache.pop(app_key, None)
            logger.info(f"토큰 캐시 삭제 - 앱키: {app_key}")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """캐시 통계 정보"""
        total_count = len(self._cache)
        expired_count = sum(1 for token in self._cache.values() if token.is_expired())
        valid_count = total_count - expired_count
        
        return {
            "total_count": total_count,
            "valid_count": valid_count, 
            "expired_count": expired_count
        }


# 전역 토큰 캐시 인스턴스
token_cache = InMemoryTokenCache()