"""뉴스 조회 API 엔드포인트

종목별 뉴스 조회, 카테고리별 뉴스 필터링, 뉴스 상세 정보 제공
"""

import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime

# Handle both relative and absolute imports for different execution contexts
try:
    from ..external.enhanced_news_crawler import EnhancedNewsCrawler
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from kiwoom_api.external.enhanced_news_crawler import EnhancedNewsCrawler

router = APIRouter(prefix="/api/v1", tags=["news"])


class NewsArticle(BaseModel):
    """뉴스 기사 모델"""
    title: str = Field(..., description="뉴스 제목")
    link: Optional[str] = Field(None, description="뉴스 링크")
    content: Optional[str] = Field(None, description="뉴스 내용")
    source: str = Field(..., description="뉴스 출처")
    date: str = Field(..., description="발행 날짜")
    sentiment: str = Field("중립", description="감정 분석 (긍정/부정/중립)")
    category: Optional[str] = Field(None, description="뉴스 카테고리")


class NewsResponse(BaseModel):
    """뉴스 검색 응답 모델"""
    success: bool = Field(True, description="요청 성공 여부")
    query: str = Field(..., description="검색어")
    total_count: int = Field(0, description="총 뉴스 건수")
    articles: List[NewsArticle] = Field([], description="뉴스 기사 목록")
    category_stats: Dict[str, int] = Field({}, description="카테고리별 뉴스 건수")
    crawling_info: Dict[str, Any] = Field({}, description="검색 정보")




@router.get("/news/info",
           summary="뉴스 검색 API 정보",
           description="네이버 뉴스 검색 API 사용 가능한 파라미터와 옵션을 제공합니다.")
async def get_news_info():
    """뉴스 검색 API 정보 조회"""
    return {
        "success": True,
        "api_info": {
            "service": "네이버 뉴스 검색 API",
            "version": "v1",
            "daily_limit": 25000,
            "max_display": 100,
            "max_start": 1000
        },
        "parameters": {
            "query": "검색어 (종목명, 종목코드 등)",
            "display": "결과 개수 (1~100, 기본: 20)",
            "start": "검색 시작 위치 (1~1000, 기본: 1)",
            "sort": "정렬 방식 (sim: 정확도순, date: 날짜순)"
        },
        "sort_options": {
            "sim": "정확도순 정렬 (기본값)",
            "date": "날짜순 정렬 (최신순)"
        },
        "sentiment_types": ["긍정", "부정", "중립"],
        "supported_stocks": {
            "005930": "삼성전자",
            "000660": "SK하이닉스",
            "035420": "NAVER",
            "207940": "삼성바이오로직스",
            "005380": "현대차"
        },
        "usage_examples": {
            "종목 검색": "/api/v1/news/search?query=삼성전자",
            "종목코드 검색": "/api/v1/news/search?query=005930",
            "키워드 검색": "/api/v1/news/search?query=반도체",
            "많은 결과": "/api/v1/news/search?query=삼성전자&display=50",
            "정확도순": "/api/v1/news/search?query=삼성전자&sort=sim",
            "실적 뉴스": "/api/v1/news/search?query=삼성전자 실적",
            "페이지네이션": "/api/v1/news/search?query=삼성전자&start=21&display=20"
        }
    }


@router.get("/news/search", 
           response_model=NewsResponse,
           summary="뉴스 검색",
           description="네이버 뉴스 검색 API를 통해 키워드로 뉴스를 검색합니다.")
async def search_news(
    query: str = Query(..., description="검색어 (종목명, 종목코드, 키워드 등)"),
    display: int = Query(20, ge=1, le=100, description="결과 개수 (최대 100개)"),
    start: int = Query(1, ge=1, le=1000, description="검색 시작 위치"),
    sort: str = Query("date", description="정렬방식 (sim: 정확도순, date: 날짜순)"),
    sentiment: Optional[str] = Query(None, description="감정 필터 (긍정/부정/중립)")
) -> NewsResponse:
    """
    네이버 뉴스 검색 API를 통한 범용 뉴스 검색
    
    - **query**: 검색어 (종목명, 종목코드, 키워드 등)
    - **display**: 결과 개수 (1~100)
    - **start**: 검색 시작 위치 (1~1000)
    - **sort**: 정렬 방식 (sim: 정확도순, date: 날짜순)
    - **sentiment**: 감정 필터링 (긍정/부정/중립)
    """
    try:
        # 네이버 뉴스 API 클라이언트 초기화
        from ..external.naver_news_client import NaverNewsClient
        from ..config.settings import settings
        
        client = NaverNewsClient(
            client_id=settings.NAVER_CLIENT_ID,
            client_secret=settings.NAVER_CLIENT_SECRET
        )
        
        # 검색어는 사용자가 제공한 query 파라미터 사용
        search_query = query
        
        # 네이버 뉴스 검색 API 호출
        api_response = await client.search_news(
            query=search_query,
            display=display,
            start=start,
            sort=sort
        )
        
        if not api_response.get("items"):
            return NewsResponse(
                success=False,
                query=search_query,
                total_count=0,
                articles=[],
                category_stats={},
                crawling_info={"error": "검색 결과가 없습니다"}
            )
        
        # API 응답을 NewsArticle 형식으로 변환
        articles = []
        for item in api_response.get("items", []):
            clean_title = client.clean_html_tags(item.get("title", ""))
            clean_description = client.clean_html_tags(item.get("description", ""))
            
            article_sentiment = client.analyze_sentiment(clean_title, clean_description)
            
            # 감정 필터링
            if sentiment and article_sentiment != sentiment:
                continue
            
            articles.append({
                "title": clean_title,
                "link": item.get("link", item.get("originallink", "")),
                "content": clean_description,
                "source": "네이버뉴스API",
                "date": client.parse_pubdate(item.get("pubDate", "")),
                "sentiment": article_sentiment,
                "category": "검색결과"
            })
        
        # NewsArticle 모델로 변환
        news_articles = []
        for article in articles:
            news_articles.append(NewsArticle(
                title=article.get('title', '제목없음'),
                link=article.get('link', ''),
                content=article.get('content', ''),
                source=article.get('source', '출처없음'),
                date=article.get('date', datetime.now().strftime('%Y-%m-%d')),
                sentiment=article.get('sentiment', '중립'),
                category=article.get('category')
            ))
        
        return NewsResponse(
            success=True,
            query=search_query,
            total_count=len(news_articles),
            articles=news_articles,
            category_stats={"네이버뉴스API": len(news_articles)},
            crawling_info={
                "crawling_method": "네이버 뉴스 검색 API",
                "api_version": "v1",
                "search_method": "키워드 기반 검색",
                "search_query": search_query,
                "parameters": {
                    "display": display,
                    "start": start,
                    "sort": sort
                },
                "total_available": api_response.get('total', 0),
                "collected_count": len(news_articles),
                "last_updated": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"뉴스 조회 중 오류 발생: {str(e)}"
        )


