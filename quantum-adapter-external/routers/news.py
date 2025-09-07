"""
News API endpoints for external news sources.
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional, Literal
from src.naver.news_api import naver_news_api
from src.naver.models import NewsSearchResponse, NewsSearchParams
from src.common.exceptions import NaverAPIError, APIKeyError, ValidationError, RateLimitError
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/news", tags=["News"])


@router.get(
    "/search",
    response_model=NewsSearchResponse,
    summary="뉴스 검색",
    description="네이버 뉴스 API를 통해 뉴스를 검색합니다.",
    responses={
        200: {"description": "검색 성공"},
        400: {"description": "잘못된 요청 파라미터"},
        401: {"description": "API 인증 실패"},
        429: {"description": "API 호출 한도 초과"},
        500: {"description": "서버 오류"}
    }
)
async def search_news(
    query: str = Query(..., description="검색어", example="삼성전자"),
    display: int = Query(10, ge=1, le=100, description="한 번에 표시할 검색 결과 개수"),
    start: int = Query(1, ge=1, le=1000, description="검색 시작 위치"),
    sort: Literal["sim", "date"] = Query("sim", description="정렬 방법 (sim: 정확도순, date: 날짜순)")
):
    """
    네이버 뉴스 검색 API
    
    주어진 검색어로 네이버 뉴스를 검색합니다.
    
    - **query**: 검색하고자 하는 키워드
    - **display**: 한 번에 가져올 뉴스 개수 (1-100)
    - **start**: 검색 시작 위치 (1-1000)  
    - **sort**: 정렬 방법 (sim: 정확도순, date: 날짜순)
    """
    try:
        # Create search parameters
        params = NewsSearchParams(
            query=query,
            display=display,
            start=start,
            sort=sort
        )
        
        # Perform search
        result = await naver_news_api.search_news(params)
        
        logger.info(f"News search successful: query='{query}', results={len(result.items)}")
        return result
        
    except ValidationError as e:
        logger.warning(f"Validation error in news search: {e.message}")
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
    except NaverAPIError as e:
        logger.error(f"Naver API error: {e.message}")
        raise HTTPException(
            status_code=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"뉴스 검색 중 오류가 발생했습니다: {e.message}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in news search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="서버 내부 오류가 발생했습니다."
        )


@router.get(
    "/latest/{keyword}",
    response_model=NewsSearchResponse,
    summary="최신 뉴스 조회",
    description="특정 키워드의 최신 뉴스를 날짜순으로 조회합니다."
)
async def get_latest_news(
    keyword: str,
    count: int = Query(20, ge=1, le=100, description="조회할 뉴스 개수")
):
    """
    최신 뉴스 조회
    
    특정 키워드의 최신 뉴스를 날짜순으로 가져옵니다.
    
    - **keyword**: 검색 키워드
    - **count**: 가져올 뉴스 개수 (1-100)
    """
    try:
        result = await naver_news_api.get_latest_news(keyword, count)
        logger.info(f"Latest news retrieval successful: keyword='{keyword}', results={len(result.items)}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting latest news: {str(e)}")
        if isinstance(e, (ValidationError, APIKeyError, RateLimitError, NaverAPIError)):
            # Re-raise known exceptions
            raise HTTPException(
                status_code=getattr(e, 'status_code', status.HTTP_500_INTERNAL_SERVER_ERROR),
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="최신 뉴스 조회 중 오류가 발생했습니다."
            )


@router.get(
    "/financial/{symbol}",
    response_model=NewsSearchResponse,
    summary="금융 뉴스 조회",
    description="특정 종목이나 회사의 금융 관련 뉴스를 조회합니다."
)
async def get_financial_news(
    symbol: str,
    days_back: int = Query(7, ge=1, le=30, description="조회할 일수 (현재는 API 한계로 실제 필터링되지 않음)")
):
    """
    금융 뉴스 조회
    
    특정 종목이나 회사명으로 금융 관련 뉴스를 검색합니다.
    
    - **symbol**: 종목 코드나 회사명 (예: 삼성전자, 005930)
    - **days_back**: 조회 기간 (일 단위, 현재는 참고용)
    """
    try:
        result = await naver_news_api.search_financial_news(symbol, days_back)
        logger.info(f"Financial news retrieval successful: symbol='{symbol}', results={len(result.items)}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting financial news: {str(e)}")
        if isinstance(e, (ValidationError, APIKeyError, RateLimitError, NaverAPIError)):
            raise HTTPException(
                status_code=getattr(e, 'status_code', status.HTTP_500_INTERNAL_SERVER_ERROR),
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="금융 뉴스 조회 중 오류가 발생했습니다."
            )