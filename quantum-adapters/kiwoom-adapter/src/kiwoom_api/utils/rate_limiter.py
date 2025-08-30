"""
키움증권 API Rate Limiting 유틸리티

키움증권 서버부하방지 제한 대응:
- 1초당 5회 조회 제한 (기본)
- 서버 상태에 따른 유동적 제한
- 429 에러 시 exponential backoff retry
"""

import asyncio
import time
from typing import Dict, Optional
import logging
from collections import deque
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate Limit 설정"""
    requests_per_second: int = 5  # 1초당 요청 수 (키움 기본 제한)
    retry_attempts: int = 3  # 재시도 횟수
    base_delay: float = 1.0  # 기본 대기 시간 (초)
    max_delay: float = 30.0  # 최대 대기 시간 (초)
    exponential_base: float = 2.0  # 지수 증가 배수


class APIRateLimiter:
    """API 호출 속도 제한 관리"""
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self.request_times: deque = deque()  # 요청 시간 기록
        self.api_counters: Dict[str, deque] = {}  # API별 호출 기록
        self._lock = asyncio.Lock()
        
        logger.info(f"🚦 Rate Limiter 초기화: {self.config.requests_per_second}req/sec")

    async def wait_for_slot(self, api_id: str) -> None:
        """요청 슬롯 대기"""
        async with self._lock:
            now = time.time()
            
            # API별 카운터 초기화
            if api_id not in self.api_counters:
                self.api_counters[api_id] = deque()
            
            api_times = self.api_counters[api_id]
            
            # 1초 이전 요청들 제거
            cutoff_time = now - 1.0
            while api_times and api_times[0] < cutoff_time:
                api_times.popleft()
            
            # 제한 초과 시 대기
            if len(api_times) >= self.config.requests_per_second:
                wait_time = 1.0 - (now - api_times[0])
                if wait_time > 0:
                    logger.warning(f"⏳ {api_id} Rate limit 대기: {wait_time:.2f}초")
                    await asyncio.sleep(wait_time)
            
            # 현재 요청 시간 기록
            api_times.append(now)

    async def execute_with_retry(self, api_id: str, api_call_func, *args, **kwargs):
        """재시도 로직이 포함된 API 호출"""
        for attempt in range(self.config.retry_attempts):
            try:
                # Rate limiting 적용
                await self.wait_for_slot(api_id)
                
                # API 호출
                logger.info(f"🔄 {api_id} 호출 시도 {attempt + 1}/{self.config.retry_attempts}")
                result = await api_call_func(*args, **kwargs)
                
                # 성공 시 결과 반환
                if result.get('Code') != 429:
                    if attempt > 0:
                        logger.info(f"✅ {api_id} 재시도 성공 (시도: {attempt + 1})")
                    return result
                
                # 429 에러 시 재시도
                logger.warning(f"⚠️ {api_id} 429 에러 - 재시도 {attempt + 1}")
                if attempt < self.config.retry_attempts - 1:
                    delay = self._calculate_backoff_delay(attempt)
                    logger.info(f"⏳ {delay:.2f}초 대기 후 재시도...")
                    await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"❌ {api_id} 호출 실패 (시도 {attempt + 1}): {str(e)}")
                if attempt < self.config.retry_attempts - 1:
                    delay = self._calculate_backoff_delay(attempt)
                    await asyncio.sleep(delay)
                else:
                    raise
        
        # 모든 재시도 실패
        logger.error(f"❌ {api_id} 모든 재시도 실패")
        return {
            'Code': 429,
            'Header': {'api-id': api_id, 'cont-yn': 'N', 'next-key': ''},
            'Body': {'error': f'Rate limit exceeded after {self.config.retry_attempts} attempts'}
        }

    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Exponential backoff 지연 시간 계산"""
        delay = self.config.base_delay * (self.config.exponential_base ** attempt)
        return min(delay, self.config.max_delay)

    async def get_stats(self) -> Dict:
        """Rate Limiter 통계 정보"""
        async with self._lock:
            now = time.time()
            cutoff_time = now - 1.0
            
            stats = {
                'config': {
                    'requests_per_second': self.config.requests_per_second,
                    'retry_attempts': self.config.retry_attempts,
                    'base_delay': self.config.base_delay,
                    'max_delay': self.config.max_delay
                },
                'api_stats': {}
            }
            
            for api_id, api_times in self.api_counters.items():
                # 최근 1초 내 요청 수
                recent_requests = sum(1 for t in api_times if t > cutoff_time)
                stats['api_stats'][api_id] = {
                    'recent_requests': recent_requests,
                    'total_requests': len(api_times),
                    'available_slots': max(0, self.config.requests_per_second - recent_requests)
                }
            
            return stats


# 전역 Rate Limiter 인스턴스
_rate_limiter = APIRateLimiter()

async def get_rate_limiter() -> APIRateLimiter:
    """전역 Rate Limiter 인스턴스 반환"""
    return _rate_limiter