"""
키움 API 에러 코드 정의 및 분류

키움 공식 에러 코드를 분류하여 적절한 이벤트 처리 전략 수립
"""

from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass


class ErrorSeverity(Enum):
    """에러 심각도"""
    CRITICAL = "critical"    # 서비스 중단
    HIGH = "high"           # 즉시 대응 필요  
    MEDIUM = "medium"       # 모니터링 필요
    LOW = "low"            # 로그 기록


class ErrorCategory(Enum):
    """에러 카테고리"""
    API_REQUEST = "api_request"        # API 요청 오류
    AUTHENTICATION = "authentication"  # 인증/토큰 오류
    DATA_VALIDATION = "data_validation" # 데이터 검증 오류
    RATE_LIMIT = "rate_limit"         # API 제한 오류
    SYSTEM = "system"                 # 시스템 오류
    MARKET_DATA = "market_data"       # 시장 데이터 오류


@dataclass
class KiwoomError:
    """키움 에러 정보"""
    code: str
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    auto_retry: bool = False
    recovery_action: Optional[str] = None


class KiwoomErrorCodes:
    """키움 API 에러 코드 매핑"""
    
    ERRORS: Dict[str, KiwoomError] = {
        # API 요청 오류
        "1501": KiwoomError("1501", "API ID가 Null이거나 값이 없습니다", ErrorSeverity.HIGH, ErrorCategory.API_REQUEST),
        "1504": KiwoomError("1504", "해당 URI에서는 지원하는 API ID가 아닙니다", ErrorSeverity.HIGH, ErrorCategory.API_REQUEST),
        "1505": KiwoomError("1505", "해당 API ID는 존재하지 않습니다", ErrorSeverity.HIGH, ErrorCategory.API_REQUEST),
        "1511": KiwoomError("1511", "필수 입력 값에 값이 존재하지 않습니다", ErrorSeverity.MEDIUM, ErrorCategory.DATA_VALIDATION),
        "1512": KiwoomError("1512", "Http header에 값이 설정되지 않았거나 읽을 수 없습니다", ErrorSeverity.HIGH, ErrorCategory.API_REQUEST),
        "1513": KiwoomError("1513", "Http Header에 authorization 필드가 설정되어 있어야 합니다", ErrorSeverity.HIGH, ErrorCategory.AUTHENTICATION),
        "1514": KiwoomError("1514", "Http Header의 authorization 필드 형식이 맞지 않습니다", ErrorSeverity.HIGH, ErrorCategory.AUTHENTICATION),
        "1515": KiwoomError("1515", "Http Header의 authorization 필드 내 Grant Type이 미리 정의된 형식이 아닙니다", ErrorSeverity.HIGH, ErrorCategory.AUTHENTICATION),
        "1516": KiwoomError("1516", "Http Header의 authorization 필드 내 Token이 정의되어 있지 않습니다", ErrorSeverity.HIGH, ErrorCategory.AUTHENTICATION),
        "1517": KiwoomError("1517", "입력 값 형식이 올바르지 않습니다", ErrorSeverity.MEDIUM, ErrorCategory.DATA_VALIDATION),
        
        # 제한 및 시스템 오류
        "1687": KiwoomError("1687", "재귀 호출이 발생하여 API 호출을 제한합니다", ErrorSeverity.HIGH, ErrorCategory.RATE_LIMIT, recovery_action="exponential_backoff"),
        "1700": KiwoomError("1700", "허용된 요청 개수를 초과하였습니다", ErrorSeverity.HIGH, ErrorCategory.RATE_LIMIT, recovery_action="rate_limit_backoff"),
        
        # 시장 데이터 오류
        "1901": KiwoomError("1901", "시장 코드값이 존재하지 않습니다", ErrorSeverity.MEDIUM, ErrorCategory.MARKET_DATA),
        "1902": KiwoomError("1902", "종목 정보가 없습니다", ErrorSeverity.MEDIUM, ErrorCategory.MARKET_DATA),
        "1999": KiwoomError("1999", "예기치 못한 에러가 발생했습니다", ErrorSeverity.CRITICAL, ErrorCategory.SYSTEM),
        
        # 인증 오류 (토큰 재발급 가능)
        "8001": KiwoomError("8001", "App Key와 Secret Key 검증에 실패했습니다", ErrorSeverity.CRITICAL, ErrorCategory.AUTHENTICATION, auto_retry=True, recovery_action="reissue_token"),
        "8002": KiwoomError("8002", "App Key와 Secret Key 검증에 실패했습니다", ErrorSeverity.CRITICAL, ErrorCategory.AUTHENTICATION, auto_retry=True, recovery_action="reissue_token"),
        "8003": KiwoomError("8003", "Access Token을 조회하는데 실패했습니다", ErrorSeverity.CRITICAL, ErrorCategory.AUTHENTICATION, auto_retry=True, recovery_action="reissue_token"),
        "8005": KiwoomError("8005", "Token이 유효하지 않습니다", ErrorSeverity.HIGH, ErrorCategory.AUTHENTICATION, auto_retry=True, recovery_action="reissue_token"),
        "8006": KiwoomError("8006", "Access Token을 생성하는데 실패했습니다", ErrorSeverity.CRITICAL, ErrorCategory.AUTHENTICATION, auto_retry=True, recovery_action="reissue_token"),
        "8009": KiwoomError("8009", "Access Token을 발급하는데 실패했습니다", ErrorSeverity.CRITICAL, ErrorCategory.AUTHENTICATION, auto_retry=True, recovery_action="reissue_token"),
        "8010": KiwoomError("8010", "Token을 발급받은 IP와 서비스를 요청한 IP가 동일하지 않습니다", ErrorSeverity.CRITICAL, ErrorCategory.AUTHENTICATION),
        "8011": KiwoomError("8011", "Access Token을 발급하는데 실패했습니다. grant_type이 들어오지 않았습니다", ErrorSeverity.HIGH, ErrorCategory.AUTHENTICATION, auto_retry=True, recovery_action="reissue_token"),
        "8012": KiwoomError("8012", "Access Token을 발급하는데 실패했습니다. grant_type의 값이 맞지 않습니다", ErrorSeverity.HIGH, ErrorCategory.AUTHENTICATION, auto_retry=True, recovery_action="reissue_token"),
        "8015": KiwoomError("8015", "Access Token을 폐기하는데 실패했습니다", ErrorSeverity.MEDIUM, ErrorCategory.AUTHENTICATION),
        "8016": KiwoomError("8016", "Access Token을 폐기하는데 실패했습니다. Token이 들어오지 않았습니다", ErrorSeverity.MEDIUM, ErrorCategory.AUTHENTICATION),
        "8020": KiwoomError("8020", "입력파라미터로 appkey 또는 secretkey가 들어오지 않았습니다", ErrorSeverity.CRITICAL, ErrorCategory.AUTHENTICATION),
        "8030": KiwoomError("8030", "투자구분(실전/모의)이 달라서 Appkey를 사용할수가 없습니다", ErrorSeverity.CRITICAL, ErrorCategory.AUTHENTICATION),
        "8031": KiwoomError("8031", "투자구분(실전/모의)이 달라서 Token를 사용할수가 없습니다", ErrorSeverity.CRITICAL, ErrorCategory.AUTHENTICATION),
        "8040": KiwoomError("8040", "단말기 인증에 실패했습니다", ErrorSeverity.CRITICAL, ErrorCategory.AUTHENTICATION),
        "8050": KiwoomError("8050", "지정단말기 인증에 실패했습니다", ErrorSeverity.CRITICAL, ErrorCategory.AUTHENTICATION),
        "8103": KiwoomError("8103", "토큰 인증 또는 단말기인증에 실패했습니다", ErrorSeverity.CRITICAL, ErrorCategory.AUTHENTICATION, auto_retry=True, recovery_action="reissue_token"),
    }
    
    @classmethod
    def get_error(cls, code: str) -> Optional[KiwoomError]:
        """에러 코드로 에러 정보 조회"""
        return cls.ERRORS.get(code)
    
    @classmethod
    def is_auth_error(cls, code: str) -> bool:
        """인증 에러 여부 확인"""
        error = cls.get_error(code)
        return error and error.category == ErrorCategory.AUTHENTICATION
    
    @classmethod
    def is_retriable(cls, code: str) -> bool:
        """재시도 가능한 에러 여부 확인"""
        error = cls.get_error(code)
        return error and error.auto_retry
    
    @classmethod
    def get_critical_errors(cls) -> Dict[str, KiwoomError]:
        """심각한 에러 목록 조회"""
        return {code: error for code, error in cls.ERRORS.items() 
                if error.severity == ErrorSeverity.CRITICAL}


def get_recovery_strategy(error_code: str) -> Optional[str]:
    """에러 코드에 따른 복구 전략 반환"""
    error = KiwoomErrorCodes.get_error(error_code)
    if error:
        return error.recovery_action
    return None


def should_alert(error_code: str) -> bool:
    """알림이 필요한 에러인지 확인"""
    error = KiwoomErrorCodes.get_error(error_code)
    if not error:
        return True  # 알 수 없는 에러는 알림
    
    return error.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]