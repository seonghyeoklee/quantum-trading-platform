"""
거래 모드 동기화 기능

Java 백엔드와 연동하여 사용자의 실제 거래 모드를 키움증권 API 키 패턴 기반으로 판단하고 동기화합니다.
"""

import asyncio
import re
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import httpx

try:
    from ..config.settings import settings
    from ..models.common import APIResponse
except ImportError:
    from kiwoom_api.config.settings import settings
    from kiwoom_api.models.common import APIResponse

logger = logging.getLogger(__name__)

class TradingMode(Enum):
    """거래 모드 열거형"""
    REAL = "REAL"
    SANDBOX = "SANDBOX" 
    UNKNOWN = "UNKNOWN"

@dataclass
class KeyPatternAnalysis:
    """API 키 패턴 분석 결과"""
    trading_mode: TradingMode
    confidence_score: float
    app_key_pattern: str
    secret_key_pattern: str
    detection_reasons: list[str]

@dataclass
class TradingModeInfo:
    """거래 모드 정보"""
    user_id: str
    trading_mode: TradingMode
    detection_status: str
    message: str
    confidence_score: float = 0.0
    detected_at: Optional[str] = None

class TradingModeDetector:
    """거래 모드 자동 탐지기"""
    
    # 키움증권 API 키 패턴 (실제 패턴은 키움증권 문서 확인 필요)
    PRODUCTION_APPKEY_PATTERN = re.compile(r'^PS[A-Z0-9]{32}$')
    SANDBOX_APPKEY_PATTERN = re.compile(r'^PS[A-Z0-9]{32}_SB$')
    PRODUCTION_SECRET_PATTERN = re.compile(r'^[A-Za-z0-9+/]{64}={0,2}$')
    SANDBOX_SECRET_PATTERN = re.compile(r'^[A-Za-z0-9+/]{64}={0,2}_TEST$')
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".TradingModeDetector")
    
    def analyze_key_patterns(self, app_key: str, secret_key: str) -> KeyPatternAnalysis:
        """
        API 키 패턴을 분석하여 거래 모드를 판단합니다.
        
        Args:
            app_key: 키움증권 App Key
            secret_key: 키움증권 Secret Key
            
        Returns:
            KeyPatternAnalysis: 분석 결과
        """
        try:
            self.logger.debug(f"API 키 패턴 분석 시작: app_key={self._mask_key(app_key)}")
            
            reasons = []
            
            # 1. 모의투자 패턴 먼저 확인 (더 구체적)
            if self._is_sandbox_pattern(app_key, secret_key):
                reasons.extend(self._get_sandbox_reasons(app_key, secret_key))
                return KeyPatternAnalysis(
                    trading_mode=TradingMode.SANDBOX,
                    confidence_score=0.95,
                    app_key_pattern=self._extract_pattern(app_key),
                    secret_key_pattern=self._extract_pattern(secret_key),
                    detection_reasons=reasons
                )
            
            # 2. 실전투자 패턴 확인
            if self._is_production_pattern(app_key, secret_key):
                reasons.extend(self._get_production_reasons(app_key, secret_key))
                return KeyPatternAnalysis(
                    trading_mode=TradingMode.REAL,
                    confidence_score=0.90,
                    app_key_pattern=self._extract_pattern(app_key),
                    secret_key_pattern=self._extract_pattern(secret_key),
                    detection_reasons=reasons
                )
            
            # 3. 패턴을 정확히 판단할 수 없는 경우
            reasons.append("API 키 패턴을 인식할 수 없습니다")
            return KeyPatternAnalysis(
                trading_mode=TradingMode.UNKNOWN,
                confidence_score=0.0,
                app_key_pattern=self._extract_pattern(app_key),
                secret_key_pattern=self._extract_pattern(secret_key),
                detection_reasons=reasons
            )
            
        except Exception as e:
            self.logger.error(f"API 키 패턴 분석 중 오류 발생: {e}")
            return KeyPatternAnalysis(
                trading_mode=TradingMode.UNKNOWN,
                confidence_score=0.0,
                app_key_pattern="ERROR",
                secret_key_pattern="ERROR",
                detection_reasons=[f"분석 중 오류 발생: {str(e)}"]
            )
    
    def _is_sandbox_pattern(self, app_key: str, secret_key: str) -> bool:
        """모의투자 패턴 확인"""
        # 패턴 1: 키 자체에 sandbox 표시자 포함
        sandbox_indicators = ['_SB', '_TEST', '_DEMO', '_SANDBOX']
        for indicator in sandbox_indicators:
            if indicator in app_key or indicator in secret_key:
                return True
        
        # 패턴 2: 모의투자 전용 접두사/접미사
        if (app_key.startswith('TEST_') or app_key.startswith('DEMO_') or
            app_key.endswith('_TEST') or app_key.endswith('_DEMO')):
            return True
        
        # 패턴 3: 정규표현식 매칭
        return (self.SANDBOX_APPKEY_PATTERN.match(app_key) or
                self.SANDBOX_SECRET_PATTERN.match(secret_key))
    
    def _is_production_pattern(self, app_key: str, secret_key: str) -> bool:
        """실전투자 패턴 확인"""
        # 패턴 1: 실전투자용 키 길이 및 형식 확인
        if len(app_key) >= 32 and len(secret_key) >= 32:
            # 실전투자 키는 일반적으로 더 긴 형식
            return (self.PRODUCTION_APPKEY_PATTERN.match(app_key) and
                    self.PRODUCTION_SECRET_PATTERN.match(secret_key))
        
        # 패턴 2: 키움증권 실전투자 표준 패턴
        return (re.match(r'^[A-Z0-9]{32,}$', app_key) and 
                re.match(r'^[A-Za-z0-9+/]{32,}={0,2}$', secret_key) and
                not self._is_sandbox_pattern(app_key, secret_key))
    
    def _get_sandbox_reasons(self, app_key: str, secret_key: str) -> list[str]:
        """모의투자 판단 근거"""
        reasons = []
        sandbox_indicators = ['_SB', '_TEST', '_DEMO', '_SANDBOX']
        
        for indicator in sandbox_indicators:
            if indicator in app_key:
                reasons.append(f"App Key에 모의투자 표시자 '{indicator}' 포함")
            if indicator in secret_key:
                reasons.append(f"Secret Key에 모의투자 표시자 '{indicator}' 포함")
        
        if app_key.startswith('TEST_') or app_key.startswith('DEMO_'):
            reasons.append("App Key가 테스트용 접두사로 시작")
            
        return reasons
    
    def _get_production_reasons(self, app_key: str, secret_key: str) -> list[str]:
        """실전투자 판단 근거"""
        reasons = []
        
        if len(app_key) >= 32:
            reasons.append(f"App Key 길이가 실전투자 표준 (길이: {len(app_key)})")
        if len(secret_key) >= 32:
            reasons.append(f"Secret Key 길이가 실전투자 표준 (길이: {len(secret_key)})")
        if self.PRODUCTION_APPKEY_PATTERN.match(app_key):
            reasons.append("App Key가 실전투자 패턴과 일치")
        if self.PRODUCTION_SECRET_PATTERN.match(secret_key):
            reasons.append("Secret Key가 실전투자 패턴과 일치")
            
        return reasons
    
    def _extract_pattern(self, key: str) -> str:
        """키 패턴 추출 (로깅용)"""
        if not key or len(key) < 8:
            return "INVALID"
        
        return f"{key[:4]}***{key[-4:]} (길이: {len(key)})"
    
    def _mask_key(self, key: str) -> str:
        """키 마스킹 (로깅용)"""
        if not key or len(key) < 8:
            return "INVALID_KEY"
        return f"{key[:4]}****{key[-4:]}"


class TradingModeSync:
    """거래 모드 동기화 클래스"""
    
    def __init__(self):
        self.detector = TradingModeDetector()
        self.logger = logging.getLogger(__name__ + ".TradingModeSync")
        self.java_backend_url = getattr(settings, 'JAVA_BACKEND_URL', 'http://localhost:10101')
    
    async def detect_trading_mode_from_keys(self, app_key: str, secret_key: str, user_id: str = None) -> TradingModeInfo:
        """
        API 키를 기반으로 거래 모드를 탐지합니다.
        
        Args:
            app_key: 키움증권 App Key
            secret_key: 키움증권 Secret Key
            user_id: 사용자 ID (옵션)
            
        Returns:
            TradingModeInfo: 탐지된 거래 모드 정보
        """
        try:
            self.logger.info(f"사용자 {user_id} API 키 기반 거래 모드 탐지 시작")
            
            # API 키 패턴 분석
            analysis = self.detector.analyze_key_patterns(app_key, secret_key)
            
            return TradingModeInfo(
                user_id=user_id or "unknown",
                trading_mode=analysis.trading_mode,
                detection_status="SUCCESS" if analysis.confidence_score > 0.5 else "LOW_CONFIDENCE",
                message=f"거래 모드: {analysis.trading_mode.value}, 신뢰도: {analysis.confidence_score:.2f}",
                confidence_score=analysis.confidence_score,
                detected_at=self._get_current_timestamp()
            )
            
        except Exception as e:
            self.logger.error(f"거래 모드 탐지 중 오류 발생: {e}")
            return TradingModeInfo(
                user_id=user_id or "unknown",
                trading_mode=TradingMode.UNKNOWN,
                detection_status="ERROR",
                message=f"탐지 중 오류 발생: {str(e)}",
                confidence_score=0.0,
                detected_at=self._get_current_timestamp()
            )
    
    async def sync_with_java_backend(self, user_id: str, app_key: str, secret_key: str) -> Dict[str, Any]:
        """
        Java 백엔드와 거래 모드 동기화
        
        Args:
            user_id: 사용자 ID
            app_key: 키움증권 App Key  
            secret_key: 키움증권 Secret Key
            
        Returns:
            Dict[str, Any]: 동기화 결과
        """
        try:
            self.logger.info(f"사용자 {user_id} Java 백엔드와 거래 모드 동기화 시작")
            
            # 1. 로컬에서 거래 모드 탐지
            mode_info = await self.detect_trading_mode_from_keys(app_key, secret_key, user_id)
            
            # 2. Java 백엔드에 동기화 요청
            sync_result = await self._send_sync_request_to_backend(user_id, mode_info)
            
            return {
                "user_id": user_id,
                "detected_mode": mode_info.trading_mode.value,
                "confidence_score": mode_info.confidence_score,
                "sync_status": sync_result.get("status", "UNKNOWN"),
                "sync_message": sync_result.get("message", ""),
                "synced_at": self._get_current_timestamp()
            }
            
        except Exception as e:
            self.logger.error(f"Java 백엔드 동기화 중 오류 발생: {e}")
            return {
                "user_id": user_id,
                "detected_mode": TradingMode.UNKNOWN.value,
                "confidence_score": 0.0,
                "sync_status": "ERROR", 
                "sync_message": f"동기화 중 오류 발생: {str(e)}",
                "synced_at": self._get_current_timestamp()
            }
    
    async def _send_sync_request_to_backend(self, user_id: str, mode_info: TradingModeInfo) -> Dict[str, Any]:
        """Java 백엔드에 동기화 요청 전송"""
        try:
            sync_url = f"{self.java_backend_url}/api/v1/trading-mode/sync"
            
            payload = {
                "user_id": user_id,
                "trading_mode": mode_info.trading_mode.value,
                "detection_status": mode_info.detection_status,
                "confidence_score": mode_info.confidence_score,
                "message": mode_info.message,
                "detected_at": mode_info.detected_at
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(sync_url, json=payload)
                
                if response.status_code == 200:
                    return {
                        "status": "SUCCESS",
                        "message": "Java 백엔드와 성공적으로 동기화되었습니다"
                    }
                else:
                    self.logger.warning(f"Java 백엔드 동기화 실패: {response.status_code}")
                    return {
                        "status": "BACKEND_ERROR",
                        "message": f"백엔드 응답 오류: {response.status_code}"
                    }
                    
        except httpx.TimeoutException:
            self.logger.error("Java 백엔드 동기화 타임아웃")
            return {
                "status": "TIMEOUT",
                "message": "백엔드 연결 시간 초과"
            }
        except Exception as e:
            self.logger.error(f"백엔드 동기화 요청 중 오류: {e}")
            return {
                "status": "REQUEST_ERROR", 
                "message": f"요청 중 오류 발생: {str(e)}"
            }
    
    def _get_current_timestamp(self) -> str:
        """현재 타임스탬프 반환"""
        import datetime
        return datetime.datetime.now().isoformat()


# 모듈 레벨 인스턴스
trading_mode_sync = TradingModeSync()

# 편의 함수들
async def detect_trading_mode(app_key: str, secret_key: str, user_id: str = None) -> TradingModeInfo:
    """API 키 기반 거래 모드 탐지"""
    return await trading_mode_sync.detect_trading_mode_from_keys(app_key, secret_key, user_id)

async def sync_trading_mode_with_backend(user_id: str, app_key: str, secret_key: str) -> Dict[str, Any]:
    """Java 백엔드와 거래 모드 동기화"""
    return await trading_mode_sync.sync_with_java_backend(user_id, app_key, secret_key)

async def validate_keys_for_mode(app_key: str, secret_key: str) -> KeyPatternAnalysis:
    """API 키 패턴 유효성 검증"""
    detector = TradingModeDetector()
    return detector.analyze_key_patterns(app_key, secret_key)