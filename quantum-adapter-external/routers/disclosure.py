"""
DART (전자공시시스템) API endpoints for disclosure information.
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional, Literal
from src.dart.disclosure_api import dart_disclosure_api
from src.dart.models import DartListResponse, DartListParams, DartCompanyInfo, DART_DISCLOSURE_TYPES, DART_CORP_TYPES
from src.common.exceptions import ExternalAPIError, APIKeyError, ValidationError, RateLimitError
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/disclosure", tags=["Disclosure"])


@router.get(
    "/search",
    response_model=DartListResponse,
    summary="공시정보 검색",
    description="DART 전자공시시스템을 통해 공시정보를 검색합니다.",
    responses={
        200: {"description": "검색 성공"},
        400: {"description": "잘못된 요청 파라미터"},
        401: {"description": "API 인증 실패"},
        429: {"description": "API 호출 한도 초과"},
        500: {"description": "서버 오류"}
    }
)
async def search_disclosures(
    corp_code: Optional[str] = Query(None, description="고유번호 (8자리)", regex=r"^\d{8}$"),
    bgn_de: Optional[str] = Query(None, description="시작일 (YYYYMMDD)", regex=r"^\d{8}$"),
    end_de: Optional[str] = Query(None, description="종료일 (YYYYMMDD)", regex=r"^\d{8}$"),
    last_reprt_at: Optional[Literal["Y", "N"]] = Query("N", description="최종보고서 검색여부"),
    pblntf_ty: Optional[Literal["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]] = Query(
        None, description="공시유형 (A:정기공시, B:주요사항보고, C:발행공시, D:지분공시, E:기타공시)"
    ),
    corp_cls: Optional[Literal["Y", "K", "N", "E"]] = Query(
        None, description="법인구분 (Y:유가, K:코스닥, N:코넥스, E:기타)"
    ),
    page_no: int = Query(1, ge=1, le=1000, description="페이지 번호"),
    page_count: int = Query(10, ge=1, le=100, description="페이지당 건수")
):
    """
    DART 공시정보 검색 API
    
    DART(전자공시시스템)에서 공시정보를 검색합니다.
    
    - **corp_code**: 회사 고유번호 (8자리) - 특정 회사의 공시만 검색
    - **bgn_de**: 검색 시작일 (YYYYMMDD 형식)
    - **end_de**: 검색 종료일 (YYYYMMDD 형식)
    - **pblntf_ty**: 공시유형 필터링
    - **corp_cls**: 법인구분 필터링 (유가증권/코스닥/코넥스/기타)
    - **page_no**: 페이지 번호 (1부터 시작)
    - **page_count**: 한 페이지당 결과 수 (최대 100)
    """
    try:
        # Create search parameters
        params = DartListParams(
            crtfc_key="",  # Will be set by API client
            corp_code=corp_code,
            bgn_de=bgn_de,
            end_de=end_de,
            last_reprt_at=last_reprt_at,
            pblntf_ty=pblntf_ty,
            corp_cls=corp_cls,
            page_no=page_no,
            page_count=page_count
        )
        
        # Perform search
        result = await dart_disclosure_api.search_disclosures(params)
        
        logger.info(f"DART search successful: corp_code='{corp_code}', results={len(result.list)}")
        return result
        
    except ValidationError as e:
        logger.warning(f"Validation error in disclosure search: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"잘못된 요청: {e.message}"
        )
    except APIKeyError as e:
        logger.error(f"API key error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API 인증에 실패했습니다. 관리자에게 문의하세요."
        )
    except RateLimitError as e:
        logger.warning(f"Rate limit exceeded: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="API 호출 한도를 초과했습니다. 잠시 후 다시 시도하세요."
        )
    except ExternalAPIError as e:
        logger.error(f"DART API error: {e.message}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"공시정보 검색 중 오류가 발생했습니다: {e.message}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in disclosure search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="서버 내부 오류가 발생했습니다."
        )


@router.get(
    "/recent",
    response_model=DartListResponse,
    summary="최근 공시정보 조회",
    description="최근 공시정보를 날짜순으로 조회합니다."
)
async def get_recent_disclosures(
    days: int = Query(7, ge=1, le=90, description="조회 기간 (일 단위)"),
    count: int = Query(20, ge=1, le=100, description="조회할 건수"),
    disclosure_type: Optional[Literal["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]] = Query(
        None, description="공시유형 필터"
    )
):
    """
    최근 공시정보 조회
    
    지정된 기간 동안의 최근 공시정보를 날짜순으로 가져옵니다.
    
    - **days**: 조회 기간 (1-90일)
    - **count**: 가져올 건수 (1-100)
    - **disclosure_type**: 공시유형 필터링 (선택사항)
    """
    try:
        result = await dart_disclosure_api.get_recent_disclosures(
            days=days,
            count=count,
            disclosure_type=disclosure_type
        )
        logger.info(f"Recent disclosures retrieval successful: days={days}, results={len(result.list)}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting recent disclosures: {str(e)}")
        if isinstance(e, (ValidationError, APIKeyError, RateLimitError, ExternalAPIError)):
            # Re-raise known exceptions
            raise HTTPException(
                status_code=getattr(e, 'status_code', status.HTTP_500_INTERNAL_SERVER_ERROR),
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="최근 공시정보 조회 중 오류가 발생했습니다."
            )


@router.get(
    "/company/{corp_code}",
    response_model=DartListResponse,
    summary="회사별 공시정보 조회",
    description="특정 회사의 공시정보를 조회합니다."
)
async def get_company_disclosures(
    corp_code: str,
    days: int = Query(30, ge=1, le=90, description="조회 기간 (일 단위)"),
    disclosure_type: Optional[Literal["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]] = Query(
        None, description="공시유형 필터"
    ),
    count: int = Query(50, ge=1, le=100, description="조회할 건수")
):
    """
    회사별 공시정보 조회
    
    특정 회사의 공시정보를 조회합니다.
    
    - **corp_code**: 회사 고유번호 (8자리)
    - **days**: 조회 기간 (1-90일)
    - **disclosure_type**: 공시유형 필터링 (선택사항)
    - **count**: 가져올 건수 (1-100)
    """
    try:
        result = await dart_disclosure_api.get_company_disclosures(
            corp_code=corp_code,
            days=days,
            disclosure_type=disclosure_type,
            count=count
        )
        logger.info(f"Company disclosures retrieval successful: corp_code='{corp_code}', results={len(result.list)}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting company disclosures: {str(e)}")
        if isinstance(e, (ValidationError, APIKeyError, RateLimitError, ExternalAPIError)):
            raise HTTPException(
                status_code=getattr(e, 'status_code', status.HTTP_500_INTERNAL_SERVER_ERROR),
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="회사 공시정보 조회 중 오류가 발생했습니다."
            )


@router.get(
    "/periodic",
    response_model=DartListResponse,
    summary="정기공시 조회",
    description="정기공시(분기보고서, 반기보고서, 사업보고서 등)를 조회합니다."
)
async def get_periodic_disclosures(
    days: int = Query(7, ge=1, le=90, description="조회 기간 (일 단위)"),
    count: int = Query(30, ge=1, le=100, description="조회할 건수"),
    corp_code: Optional[str] = Query(None, description="회사 고유번호 (8자리)", regex=r"^\d{8}$")
):
    """
    정기공시 조회
    
    정기공시(사업보고서, 반기보고서, 분기보고서 등)를 조회합니다.
    
    - **days**: 조회 기간 (1-90일)
    - **count**: 가져올 건수 (1-100)
    - **corp_code**: 특정 회사만 조회 (선택사항)
    """
    try:
        result = await dart_disclosure_api.get_periodic_disclosures(
            corp_code=corp_code,
            days=days,
            count=count
        )
        logger.info(f"Periodic disclosures retrieval successful: results={len(result.list)}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting periodic disclosures: {str(e)}")
        if isinstance(e, (ValidationError, APIKeyError, RateLimitError, ExternalAPIError)):
            raise HTTPException(
                status_code=getattr(e, 'status_code', status.HTTP_500_INTERNAL_SERVER_ERROR),
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="정기공시 조회 중 오류가 발생했습니다."
            )


@router.get(
    "/major",
    response_model=DartListResponse,
    summary="주요사항보고 조회",
    description="주요사항보고(합병, 분할, 자본감소 등)를 조회합니다."
)
async def get_major_disclosures(
    days: int = Query(7, ge=1, le=90, description="조회 기간 (일 단위)"),
    count: int = Query(30, ge=1, le=100, description="조회할 건수"),
    corp_code: Optional[str] = Query(None, description="회사 고유번호 (8자리)", regex=r"^\d{8}$")
):
    """
    주요사항보고 조회
    
    주요사항보고(합병, 분할, 자본감소, 영업양수도 등)를 조회합니다.
    
    - **days**: 조회 기간 (1-90일)
    - **count**: 가져올 건수 (1-100)
    - **corp_code**: 특정 회사만 조회 (선택사항)
    """
    try:
        result = await dart_disclosure_api.get_major_disclosures(
            corp_code=corp_code,
            days=days,
            count=count
        )
        logger.info(f"Major disclosures retrieval successful: results={len(result.list)}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting major disclosures: {str(e)}")
        if isinstance(e, (ValidationError, APIKeyError, RateLimitError, ExternalAPIError)):
            raise HTTPException(
                status_code=getattr(e, 'status_code', status.HTTP_500_INTERNAL_SERVER_ERROR),
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="주요사항보고 조회 중 오류가 발생했습니다."
            )


@router.get(
    "/search-company/{keyword}",
    response_model=DartListResponse,
    summary="회사명 키워드 검색",
    description="회사명 키워드로 공시정보를 검색합니다."
)
async def search_by_company_keyword(
    keyword: str,
    days: int = Query(30, ge=1, le=90, description="조회 기간 (일 단위)"),
    count: int = Query(50, ge=1, le=100, description="조회할 건수"),
    disclosure_type: Optional[Literal["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]] = Query(
        None, description="공시유형 필터"
    )
):
    """
    회사명 키워드 검색
    
    회사명에 특정 키워드가 포함된 회사들의 공시정보를 검색합니다.
    
    - **keyword**: 검색할 회사명 키워드
    - **days**: 조회 기간 (1-90일)
    - **count**: 가져올 건수 (1-100)
    - **disclosure_type**: 공시유형 필터링 (선택사항)
    """
    try:
        result = await dart_disclosure_api.search_by_keyword(
            keyword=keyword,
            days=days,
            count=count,
            disclosure_type=disclosure_type
        )
        logger.info(f"Keyword search successful: keyword='{keyword}', results={len(result.list)}")
        return result
        
    except Exception as e:
        logger.error(f"Error searching by keyword: {str(e)}")
        if isinstance(e, (ValidationError, APIKeyError, RateLimitError, ExternalAPIError)):
            raise HTTPException(
                status_code=getattr(e, 'status_code', status.HTTP_500_INTERNAL_SERVER_ERROR),
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="키워드 검색 중 오류가 발생했습니다."
            )


@router.get(
    "/types",
    summary="공시유형 목록",
    description="사용 가능한 공시유형 목록을 조회합니다."
)
async def get_disclosure_types():
    """
    공시유형 목록 조회
    
    DART에서 사용 가능한 공시유형 목록을 반환합니다.
    """
    return {
        "disclosure_types": DART_DISCLOSURE_TYPES,
        "corp_types": DART_CORP_TYPES,
        "description": "공시유형과 법인구분 코드 목록"
    }


@router.get(
    "/company-info/{corp_code}",
    response_model=DartCompanyInfo,
    summary="기업개황 조회",
    description="회사 고유번호로 기업의 상세 정보를 조회합니다.",
    responses={
        200: {"description": "조회 성공"},
        400: {"description": "잘못된 고유번호 또는 회사를 찾을 수 없음"},
        401: {"description": "API 인증 실패"},
        429: {"description": "API 호출 한도 초과"},
        500: {"description": "서버 오류"}
    }
)
async def get_company_info(corp_code: str):
    """
    기업개황 조회
    
    회사 고유번호(8자리)를 사용해 기업의 상세 정보를 조회합니다.
    
    - **corp_code**: 회사 고유번호 (8자리 숫자)
    
    **반환 정보**:
    - 정식명칭, 영문명칭, 종목명, 종목코드
    - 대표자명, 법인구분, 법인/사업자등록번호  
    - 주소, 홈페이지, IR홈페이지, 연락처
    - 업종코드, 설립일, 결산월
    """
    # Validate corp_code format
    if not corp_code.isdigit() or len(corp_code) != 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="고유번호는 8자리 숫자여야 합니다."
        )
    
    try:
        result = await dart_disclosure_api.get_company_info(corp_code)
        logger.info(f"Company info retrieval successful: corp_code='{corp_code}', company='{result.corp_name}'")
        return result
        
    except ValidationError as e:
        logger.warning(f"Validation error in company info: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"잘못된 요청: {e.message}"
        )
    except APIKeyError as e:
        logger.error(f"API key error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API 인증에 실패했습니다. 관리자에게 문의하세요."
        )
    except RateLimitError as e:
        logger.warning(f"Rate limit exceeded: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="API 호출 한도를 초과했습니다. 잠시 후 다시 시도하세요."
        )
    except ExternalAPIError as e:
        logger.error(f"DART API error: {e.message}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"기업정보 조회 중 오류가 발생했습니다: {e.message}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in company info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="서버 내부 오류가 발생했습니다."
        )