"""키움 API 인증 라우터

키움 API fn_au10001 함수 직접 호출 엔드포인트
"""

import logging
import sys
from pathlib import Path

from fastapi import APIRouter, Header

# Handle both relative and absolute imports for different execution contexts
try:
    from ..models.kiwoom_request import KiwoomApiResponse
    from ..functions.auth import fn_au10001
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from kiwoom_api.models.kiwoom_request import KiwoomApiResponse
    from kiwoom_api.functions.auth import fn_au10001

logger = logging.getLogger(__name__)

router = APIRouter(tags=["인증 API"])


@router.post(
    "/api/fn_au10001",
    response_model=KiwoomApiResponse,
    summary="키움증권 접근토큰 발급 (au10001)",
    description="Java에서 헤더로 전달받은 키로 토큰 발급 - 환경변수 의존성 완전 제거"
)
async def api_fn_au10001(
    kiwoom_app_key: str = Header(..., alias="X-Kiwoom-App-Key", description="Java에서 전달하는 키움 앱키"),
    kiwoom_app_secret: str = Header(..., alias="X-Kiwoom-App-Secret", description="Java에서 전달하는 키움 앱시크릿")
) -> KiwoomApiResponse:
    """키움증권 접근토큰 발급 (au10001)

    Java에서 헤더로 전달받은 모드별 앱키/시크릿키로 토큰 발급
    환경변수 의존성 완전 제거

    Headers:
        X-Kiwoom-App-Key: 키움 앱키 (Java에서 sandbox/real 모드에 따라 선택)
        X-Kiwoom-App-Secret: 키움 앱시크릿 (Java에서 sandbox/real 모드에 따라 선택)

    Returns:
        KiwoomApiResponse containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더
        - Body: 키움 API 응답 바디 (access_token 포함)
    """
    # Java에서 전달받은 키로 토큰 발급 (환경변수 의존성 완전 제거)
    result = await fn_au10001(kiwoom_app_key, kiwoom_app_secret)

    # KiwoomApiResponse 모델로 반환
    return KiwoomApiResponse(**result)