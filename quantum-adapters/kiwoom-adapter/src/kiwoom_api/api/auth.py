"""키움 API 인증 라우터

키움 API fn_au10001 함수 직접 호출 엔드포인트
"""

import logging
import sys
from pathlib import Path

from fastapi import APIRouter

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
    description="환경변수 기반 자동 토큰 발급 - 사용자 입력 불필요"
)
async def api_fn_au10001() -> KiwoomApiResponse:
    """키움증권 접근토큰 발급 (au10001)

    환경변수에서 자동으로 앱키/시크릿키를 읽어서 토큰 발급
    사용자가 별도로 입력할 데이터 없음

    Returns:
        KiwoomApiResponse containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더
        - Body: 키움 API 응답 바디 (토큰 정보)
    """
    # fn_au10001 함수 직접 호출 (환경변수 기반 자동 설정)
    result = await fn_au10001()

    # KiwoomApiResponse 모델로 반환
    return KiwoomApiResponse(**result)