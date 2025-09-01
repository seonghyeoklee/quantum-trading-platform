"""
사용자별 런타임 설정 관리 모듈

사용자별로 다른 트레이딩 모드(모의투자/실전투자)를 설정할 수 있도록 하는 
런타임 설정 관리 시스템입니다.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
import logging
from threading import RLock
import json

# 이중 import 전략 적용
try:
    from .settings import settings
except ImportError:
    import sys
    from pathlib import Path
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from kiwoom_api.config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class UserTradingConfig:
    """사용자별 트레이딩 설정"""
    user_id: str
    sandbox_mode: bool
    kiwoom_account_id: Optional[str] = None
    max_daily_amount: Optional[float] = None
    risk_level: str = "MEDIUM"
    auto_trading_enabled: bool = False
    notifications_enabled: bool = True
    updated_at: datetime = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.expires_at is None:
            # 기본 만료시간: 24시간
            self.expires_at = datetime.now() + timedelta(hours=24)
    
    def is_expired(self) -> bool:
        """설정 만료 여부 확인"""
        return self.expires_at and datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        # datetime 객체를 문자열로 변환
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserTradingConfig':
        """딕셔너리로부터 생성"""
        # 문자열을 datetime 객체로 변환
        for key in ['updated_at', 'expires_at']:
            if key in data and isinstance(data[key], str):
                data[key] = datetime.fromisoformat(data[key])
        return cls(**data)


class UserTradingSettingsManager:
    """사용자별 트레이딩 설정 관리자"""
    
    def __init__(self):
        self._user_configs: Dict[str, UserTradingConfig] = {}
        self._lock = RLock()
        self._default_sandbox_mode = settings.KIWOOM_SANDBOX_MODE
        self._cleanup_task = None
        self._start_cleanup_task()
        
        logger.info("사용자별 트레이딩 설정 관리자 초기화됨 - 기본 모드: %s", 
                   "샌드박스" if self._default_sandbox_mode else "실전투자")
    
    def set_user_config(self, user_id: str, sandbox_mode: bool, 
                       kiwoom_account_id: Optional[str] = None,
                       max_daily_amount: Optional[float] = None,
                       risk_level: str = "MEDIUM",
                       auto_trading_enabled: bool = False,
                       notifications_enabled: bool = True,
                       ttl_hours: int = 24) -> None:
        """사용자별 트레이딩 설정"""
        with self._lock:
            config = UserTradingConfig(
                user_id=user_id,
                sandbox_mode=sandbox_mode,
                kiwoom_account_id=kiwoom_account_id,
                max_daily_amount=max_daily_amount,
                risk_level=risk_level,
                auto_trading_enabled=auto_trading_enabled,
                notifications_enabled=notifications_enabled,
                expires_at=datetime.now() + timedelta(hours=ttl_hours)
            )
            
            self._user_configs[user_id] = config
            
            logger.info("사용자 트레이딩 설정 업데이트: user_id=%s, sandbox_mode=%s, expires_in=%d시간", 
                       user_id, sandbox_mode, ttl_hours)
    
    def get_user_config(self, user_id: str) -> Optional[UserTradingConfig]:
        """사용자별 트레이딩 설정 조회"""
        with self._lock:
            config = self._user_configs.get(user_id)
            if config and config.is_expired():
                # 만료된 설정 제거
                del self._user_configs[user_id]
                logger.info("만료된 사용자 설정 제거: user_id=%s", user_id)
                return None
            return config
    
    def get_effective_sandbox_mode(self, user_id: Optional[str] = None) -> bool:
        """유효한 샌드박스 모드 반환"""
        if user_id:
            user_config = self.get_user_config(user_id)
            if user_config:
                return user_config.sandbox_mode
        
        return self._default_sandbox_mode
    
    def get_effective_settings(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """유효한 키움 설정값들 반환"""
        sandbox_mode = self.get_effective_sandbox_mode(user_id)
        
        # 기본 설정값들
        effective_settings = {
            'sandbox_mode': sandbox_mode,
            'base_url': settings.kiwoom_base_url if sandbox_mode == settings.KIWOOM_SANDBOX_MODE else 
                       ("https://mockapi.kiwoom.com" if sandbox_mode else "https://api.kiwoom.com"),
            'websocket_url': settings.kiwoom_websocket_url if sandbox_mode == settings.KIWOOM_SANDBOX_MODE else
                            ("wss://mockapi.kiwoom.com:10000/api/dostk/websocket" if sandbox_mode 
                             else "wss://api.kiwoom.com:10000/api/dostk/websocket"),
            'app_key': settings.KIWOOM_SANDBOX_APP_KEY if sandbox_mode else settings.KIWOOM_PRODUCTION_APP_KEY,
            'app_secret': settings.KIWOOM_SANDBOX_APP_SECRET if sandbox_mode else settings.KIWOOM_PRODUCTION_APP_SECRET,
        }
        
        # 사용자별 추가 설정
        if user_id:
            user_config = self.get_user_config(user_id)
            if user_config:
                effective_settings.update({
                    'user_id': user_id,
                    'kiwoom_account_id': user_config.kiwoom_account_id,
                    'max_daily_amount': user_config.max_daily_amount,
                    'risk_level': user_config.risk_level,
                    'auto_trading_enabled': user_config.auto_trading_enabled,
                    'notifications_enabled': user_config.notifications_enabled,
                })
        
        return effective_settings
    
    def remove_user_config(self, user_id: str) -> bool:
        """사용자 설정 제거"""
        with self._lock:
            if user_id in self._user_configs:
                del self._user_configs[user_id]
                logger.info("사용자 설정 제거됨: user_id=%s", user_id)
                return True
            return False
    
    def get_all_user_configs(self) -> Dict[str, UserTradingConfig]:
        """모든 사용자 설정 조회 (만료된 것 제외)"""
        with self._lock:
            active_configs = {}
            expired_users = []
            
            for user_id, config in self._user_configs.items():
                if config.is_expired():
                    expired_users.append(user_id)
                else:
                    active_configs[user_id] = config
            
            # 만료된 설정들 정리
            for user_id in expired_users:
                del self._user_configs[user_id]
                logger.info("만료된 사용자 설정 제거: user_id=%s", user_id)
            
            return active_configs
    
    def get_statistics(self) -> Dict[str, Any]:
        """설정 통계 정보"""
        with self._lock:
            active_configs = self.get_all_user_configs()
            
            sandbox_users = sum(1 for config in active_configs.values() if config.sandbox_mode)
            production_users = len(active_configs) - sandbox_users
            
            return {
                'total_users': len(active_configs),
                'sandbox_mode_users': sandbox_users,
                'production_mode_users': production_users,
                'default_mode': 'sandbox' if self._default_sandbox_mode else 'production',
                'active_configs': [config.to_dict() for config in active_configs.values()]
            }
    
    def cleanup_expired_configs(self) -> int:
        """만료된 설정들 정리"""
        with self._lock:
            expired_users = []
            
            for user_id, config in self._user_configs.items():
                if config.is_expired():
                    expired_users.append(user_id)
            
            for user_id in expired_users:
                del self._user_configs[user_id]
            
            if expired_users:
                logger.info("만료된 사용자 설정 %d개 정리됨: %s", len(expired_users), expired_users)
            
            return len(expired_users)
    
    def _start_cleanup_task(self):
        """정리 작업 백그라운드 태스크 시작"""
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(3600)  # 1시간마다 실행
                    self.cleanup_expired_configs()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error("설정 정리 작업 중 오류: %s", e)
        
        loop = asyncio.get_event_loop()
        self._cleanup_task = loop.create_task(cleanup_loop())
    
    def shutdown(self):
        """관리자 종료"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        logger.info("사용자별 트레이딩 설정 관리자 종료됨")


# 전역 인스턴스
user_trading_settings_manager = UserTradingSettingsManager()


# 편의 함수들
def get_user_sandbox_mode(user_id: Optional[str] = None) -> bool:
    """사용자별 샌드박스 모드 조회"""
    return user_trading_settings_manager.get_effective_sandbox_mode(user_id)


def get_user_kiwoom_settings(user_id: Optional[str] = None) -> Dict[str, Any]:
    """사용자별 키움 API 설정 조회"""
    return user_trading_settings_manager.get_effective_settings(user_id)


def set_user_trading_mode(user_id: str, sandbox_mode: bool, **kwargs) -> None:
    """사용자별 트레이딩 모드 설정"""
    user_trading_settings_manager.set_user_config(user_id, sandbox_mode, **kwargs)


def get_trading_statistics() -> Dict[str, Any]:
    """트레이딩 설정 통계"""
    return user_trading_settings_manager.get_statistics()


async def get_valid_token_for_user(user_id: Optional[str] = None) -> str:
    """사용자별 유효한 토큰 획득"""
    try:
        from ..auth.token_cache import token_cache
        from ..functions.auth import fn_au10001
    except ImportError:
        from kiwoom_api.auth.token_cache import token_cache
        from kiwoom_api.functions.auth import fn_au10001
    
    # 사용자별 설정 적용
    user_settings = get_user_kiwoom_settings(user_id)
    
    # 1. 캐시에서 유효한 토큰 확인 (사용자별)
    cache_key = f"user_{user_id}" if user_id else "default"
    cached_token = await token_cache.get_token(cache_key)
    if cached_token and not cached_token.is_expired():
        return cached_token.token
    
    # 2. 새 토큰 발급 (사용자별 설정으로)
    auth_result = await fn_au10001()
    if auth_result['Code'] == 200 and auth_result['Body'].get('token'):
        return auth_result['Body']['token']
    
    # 3. Fallback to environment variables
    return user_settings['app_key']