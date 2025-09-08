"""
Pydantic models for Naver News API responses and requests.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from datetime import datetime
import re


class NewsSearchParams(BaseModel):
    """Parameters for Naver News search request."""
    
    query: str = Field(..., description="검색어 (필수)")
    display: int = Field(default=10, ge=1, le=100, description="한 번에 표시할 검색 결과 개수")
    start: int = Field(default=1, ge=1, le=1000, description="검색 시작 위치")
    sort: Literal["sim", "date"] = Field(default="sim", description="정렬 방법 (sim: 정확도순, date: 날짜순)")
    
    @validator('query')
    def validate_query(cls, v):
        """Validate search query."""
        if not v or len(v.strip()) == 0:
            raise ValueError("검색어는 필수입니다")
        if len(v) > 1000:
            raise ValueError("검색어는 1000자를 초과할 수 없습니다")
        return v.strip()


class NewsItem(BaseModel):
    """Individual news item from Naver API."""
    
    title: str = Field(..., description="뉴스 제목")
    original_link: str = Field(..., alias="originallink", description="뉴스 기사 원문 URL")
    link: str = Field(..., description="네이버 뉴스 URL")
    description: str = Field(..., description="뉴스 내용 요약")
    pub_date: str = Field(..., alias="pubDate", description="뉴스 게시 시간")
    
    class Config:
        """Pydantic configuration."""
        allow_population_by_field_name = True
    
    @validator('title', 'description')
    def clean_html_tags(cls, v):
        """Remove HTML tags and decode HTML entities from text fields."""
        if v:
            import html
            # Remove <b> tags and other HTML tags
            clean_text = re.sub(r'<[^>]+>', '', v)
            # Decode HTML entities like &quot; &lt; &gt; &amp;
            clean_text = html.unescape(clean_text)
            return clean_text.strip()
        return v
    
    @property
    def clean_title(self) -> str:
        """Get title without HTML tags and entities."""
        import html
        clean_text = re.sub(r'<[^>]+>', '', self.title)
        return html.unescape(clean_text).strip()
    
    @property
    def clean_description(self) -> str:
        """Get description without HTML tags and entities."""
        import html
        clean_text = re.sub(r'<[^>]+>', '', self.description)
        return html.unescape(clean_text).strip()


class NewsSearchResponse(BaseModel):
    """Response from Naver News search API."""
    
    last_build_date: str = Field(..., alias="lastBuildDate", description="검색 결과 생성 시간")
    total: int = Field(..., description="총 검색 결과 개수")
    start: int = Field(..., description="검색 시작 위치")
    display: int = Field(..., description="한 번에 표시한 검색 결과 개수")
    items: List[NewsItem] = Field(default=[], description="검색 결과 목록")
    
    class Config:
        """Pydantic configuration."""
        allow_population_by_field_name = True
    
    @property
    def has_more(self) -> bool:
        """Check if there are more results available."""
        return self.start + self.display <= self.total
    
    @property
    def next_start(self) -> Optional[int]:
        """Get the start parameter for the next page."""
        if self.has_more:
            return self.start + self.display
        return None


class NewsSearchRequest(BaseModel):
    """Request wrapper for news search."""
    
    params: NewsSearchParams
    
    def to_api_params(self) -> dict:
        """Convert to API parameter dictionary."""
        return {
            "query": self.params.query,
            "display": self.params.display,
            "start": self.params.start,
            "sort": self.params.sort
        }