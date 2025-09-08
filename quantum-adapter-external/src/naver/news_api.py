"""
Naver News API client implementation.
"""

from typing import Dict, Any
from config.settings import settings
from src.utils.http_client import HTTPClient
from src.naver.models import NewsSearchParams, NewsSearchResponse, NewsSearchRequest
from src.common.exceptions import NaverAPIError, APIKeyError, ValidationError
import logging

logger = logging.getLogger(__name__)


class NaverNewsAPI:
    """Client for Naver News Search API."""
    
    BASE_URL = "https://openapi.naver.com/v1/search"
    NEWS_ENDPOINT = f"{BASE_URL}/news.json"
    
    def __init__(self):
        """Initialize the Naver News API client."""
        self.client_id = settings.naver_client_id
        self.client_secret = settings.naver_client_secret
        self.headers = settings.naver_headers
    
    async def search_news(self, params: NewsSearchParams) -> NewsSearchResponse:
        """
        Search news using Naver API.
        
        Args:
            params: Search parameters
            
        Returns:
            NewsSearchResponse: Search results
            
        Raises:
            NaverAPIError: On API errors
            ValidationError: On parameter validation errors
        """
        try:
            # Validate parameters
            request = NewsSearchRequest(params=params)
            api_params = request.to_api_params()
            
            # No need to manually encode - HTTPClient handles URL encoding
            
            logger.info(f"Searching Naver News: query='{params.query}', display={params.display}, start={params.start}")
            
            # Make API request
            async with HTTPClient(timeout=30.0) as client:
                response_data = await client.get(
                    url=self.NEWS_ENDPOINT,
                    headers=self.headers,
                    params=api_params
                )
            
            # Parse response
            response = NewsSearchResponse(**response_data)
            
            logger.info(f"News search completed: total={response.total}, returned={len(response.items)}")
            return response
            
        except ValidationError:
            raise
        except Exception as e:
            if hasattr(e, 'status_code'):
                # Handle HTTP errors
                if e.status_code == 401:
                    raise APIKeyError("naver", "Invalid Naver API credentials")
                elif e.status_code == 429:
                    raise NaverAPIError("Rate limit exceeded for Naver API", e.status_code)
                elif e.status_code >= 500:
                    raise NaverAPIError("Naver API server error", e.status_code)
                else:
                    raise NaverAPIError(f"Naver API error: {str(e)}", e.status_code)
            else:
                raise NaverAPIError(f"Unexpected error during news search: {str(e)}")
    
    async def search_news_by_keyword(
        self, 
        keyword: str, 
        display: int = 10,
        start: int = 1,
        sort: str = "sim"
    ) -> NewsSearchResponse:
        """
        Convenience method to search news by keyword.
        
        Args:
            keyword: Search keyword
            display: Number of results to return (1-100)
            start: Start position (1-1000)  
            sort: Sort method ("sim" or "date")
            
        Returns:
            NewsSearchResponse: Search results
        """
        params = NewsSearchParams(
            query=keyword,
            display=display,
            start=start,
            sort=sort
        )
        return await self.search_news(params)
    
    async def get_latest_news(self, keyword: str, count: int = 20) -> NewsSearchResponse:
        """
        Get latest news for a keyword (sorted by date).
        
        Args:
            keyword: Search keyword
            count: Number of latest news to fetch
            
        Returns:
            NewsSearchResponse: Latest news results
        """
        params = NewsSearchParams(
            query=keyword,
            display=min(count, 100),  # API limit is 100
            start=1,
            sort="date"  # Sort by date for latest news
        )
        return await self.search_news(params)
    
    async def search_financial_news(self, symbol_or_company: str, days_back: int = 7) -> NewsSearchResponse:
        """
        Search for financial news related to a stock symbol or company.
        
        Args:
            symbol_or_company: Stock symbol or company name
            days_back: Not used in API, but could be used for filtering
            
        Returns:
            NewsSearchResponse: Financial news results
        """
        # Check if input is a stock code (6 digits) - use as-is for better results
        if symbol_or_company.isdigit() and len(symbol_or_company) == 6:
            query = symbol_or_company
            logger.info(f"Searching financial news with stock code: {query}")
        else:
            # For company names, add financial context
            query = f"{symbol_or_company} 주가"
            logger.info(f"Searching financial news with company name: {query}")
        
        params = NewsSearchParams(
            query=query,
            display=20,
            start=1,
            sort="sim"  # Relevance first
        )
        
        return await self.search_news(params)


# Global API client instance
naver_news_api = NaverNewsAPI()