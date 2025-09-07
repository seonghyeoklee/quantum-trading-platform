"""
DART (전자공시시스템) API client implementation.
"""

from typing import Dict, Any, Optional
from urllib.parse import urlencode
from config.settings import settings
from src.utils.http_client import HTTPClient
from src.dart.models import (
    DartListParams, DartListResponse, DartListRequest, 
    DartCompanyParams, DartCompanyInfo, DartCompanyRequest,
    DART_DISCLOSURE_TYPES, DART_CORP_TYPES
)
from src.common.exceptions import ExternalAPIError, APIKeyError, ValidationError
import logging

logger = logging.getLogger(__name__)


class DartDisclosureAPI:
    """Client for DART (전자공시시스템) Disclosure API."""
    
    BASE_URL = "https://opendart.fss.or.kr/api"
    LIST_ENDPOINT = f"{BASE_URL}/list.json"
    COMPANY_ENDPOINT = f"{BASE_URL}/company.json"
    
    def __init__(self):
        """Initialize the DART API client."""
        self.api_key = settings.dart_api_key
        self.headers = settings.dart_headers
    
    async def search_disclosures(self, params: DartListParams) -> DartListResponse:
        """
        Search disclosures using DART API.
        
        Args:
            params: Search parameters
            
        Returns:
            DartListResponse: Search results
            
        Raises:
            ExternalAPIError: On API errors
            ValidationError: On parameter validation errors
        """
        try:
            # Validate parameters and set API key
            params.crtfc_key = self.api_key
            request = DartListRequest(params=params)
            api_params = request.to_api_params()
            
            logger.info(f"Searching DART disclosures: corp_code={params.corp_code}, "
                       f"page={params.page_no}, count={params.page_count}")
            
            # Make API request
            async with HTTPClient(timeout=30.0) as client:
                response_data = await client.get(
                    url=self.LIST_ENDPOINT,
                    headers=self.headers,
                    params=api_params
                )
            
            # Parse response
            response = DartListResponse(**response_data)
            
            # Check for API errors
            if not response.is_success:
                if response.status == "010":
                    raise APIKeyError("dart", "Invalid DART API key")
                elif response.status == "020":
                    raise ValidationError(f"Invalid parameter: {response.message}")
                else:
                    raise ExternalAPIError(f"DART API error ({response.status}): {response.message}")
            
            logger.info(f"DART search completed: total={response.total_count}, "
                       f"returned={len(response.list)}")
            return response
            
        except ValidationError:
            raise
        except Exception as e:
            if hasattr(e, 'status_code'):
                # Handle HTTP errors
                if e.status_code == 401:
                    raise APIKeyError("dart", "Invalid DART API credentials")
                elif e.status_code == 429:
                    raise ExternalAPIError("Rate limit exceeded for DART API", e.status_code)
                elif e.status_code >= 500:
                    raise ExternalAPIError("DART API server error", e.status_code)
                else:
                    raise ExternalAPIError(f"DART API error: {str(e)}", e.status_code)
            else:
                raise ExternalAPIError(f"Unexpected error during DART search: {str(e)}")
    
    async def get_recent_disclosures(
        self, 
        corp_code: Optional[str] = None,
        days: int = 7,
        count: int = 20,
        disclosure_type: Optional[str] = None
    ) -> DartListResponse:
        """
        Get recent disclosures.
        
        Args:
            corp_code: Company unique code (8 digits)
            days: Number of days back to search
            count: Number of results to return
            disclosure_type: Disclosure type (A-J)
            
        Returns:
            DartListResponse: Recent disclosures
        """
        from datetime import datetime, timedelta
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        params = DartListParams(
            crtfc_key=self.api_key,
            corp_code=corp_code,
            bgn_de=start_date.strftime("%Y%m%d"),
            end_de=end_date.strftime("%Y%m%d"),
            pblntf_ty=disclosure_type,
            page_count=min(count, 100),  # API limit is 100
            sort="date",
            sort_mth="desc"
        )
        
        return await self.search_disclosures(params)
    
    async def get_company_disclosures(
        self,
        corp_code: str,
        days: int = 30,
        disclosure_type: Optional[str] = None,
        count: int = 50
    ) -> DartListResponse:
        """
        Get disclosures for a specific company.
        
        Args:
            corp_code: Company unique code (8 digits)
            days: Number of days back to search
            disclosure_type: Disclosure type (A-J)
            count: Number of results to return
            
        Returns:
            DartListResponse: Company disclosures
        """
        from datetime import datetime, timedelta
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        params = DartListParams(
            crtfc_key=self.api_key,
            corp_code=corp_code,
            bgn_de=start_date.strftime("%Y%m%d"),
            end_de=end_date.strftime("%Y%m%d"),
            pblntf_ty=disclosure_type,
            page_count=min(count, 100),
            sort="date",
            sort_mth="desc"
        )
        
        return await self.search_disclosures(params)
    
    async def get_periodic_disclosures(
        self,
        corp_code: Optional[str] = None,
        days: int = 7,
        count: int = 30
    ) -> DartListResponse:
        """
        Get periodic disclosures (정기공시).
        
        Args:
            corp_code: Company unique code (8 digits, optional)
            days: Number of days back to search
            count: Number of results to return
            
        Returns:
            DartListResponse: Periodic disclosures
        """
        return await self.get_recent_disclosures(
            corp_code=corp_code,
            days=days,
            count=count,
            disclosure_type="A"  # 정기공시
        )
    
    async def get_major_disclosures(
        self,
        corp_code: Optional[str] = None,
        days: int = 7,
        count: int = 30
    ) -> DartListResponse:
        """
        Get major disclosures (주요사항보고).
        
        Args:
            corp_code: Company unique code (8 digits, optional)
            days: Number of days back to search
            count: Number of results to return
            
        Returns:
            DartListResponse: Major disclosures
        """
        return await self.get_recent_disclosures(
            corp_code=corp_code,
            days=days,
            count=count,
            disclosure_type="B"  # 주요사항보고
        )
    
    async def search_by_keyword(
        self,
        keyword: str,
        days: int = 30,
        count: int = 50,
        disclosure_type: Optional[str] = None
    ) -> DartListResponse:
        """
        Search disclosures by company name keyword.
        Note: This searches in company names, not disclosure content.
        
        Args:
            keyword: Company name keyword
            days: Number of days back to search
            count: Number of results to return
            disclosure_type: Disclosure type (A-J, optional)
            
        Returns:
            DartListResponse: Search results
        """
        from datetime import datetime, timedelta
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        params = DartListParams(
            crtfc_key=self.api_key,
            bgn_de=start_date.strftime("%Y%m%d"),
            end_de=end_date.strftime("%Y%m%d"),
            pblntf_ty=disclosure_type,
            page_count=min(count, 100),
            sort="date",
            sort_mth="desc"
        )
        
        # Get all results and filter by keyword
        response = await self.search_disclosures(params)
        
        # Filter results by keyword in company name
        if keyword:
            keyword_lower = keyword.lower()
            filtered_items = [
                item for item in response.list
                if keyword_lower in item.corp_name.lower()
            ]
            response.list = filtered_items
            response.total_count = len(filtered_items)
            response.total_page = 1
        
        return response
    
    async def get_company_info(self, corp_code: str) -> DartCompanyInfo:
        """
        Get company information by corp_code.
        
        Args:
            corp_code: Company unique code (8 digits)
            
        Returns:
            DartCompanyInfo: Company information
            
        Raises:
            ExternalAPIError: On API errors
            ValidationError: On parameter validation errors
        """
        try:
            # Validate parameters
            params = DartCompanyParams(
                crtfc_key=self.api_key,
                corp_code=corp_code
            )
            request = DartCompanyRequest(params=params)
            api_params = request.to_api_params()
            
            logger.info(f"Getting company info: corp_code='{corp_code}'")
            
            # Make API request
            async with HTTPClient(timeout=30.0) as client:
                response_data = await client.get(
                    url=self.COMPANY_ENDPOINT,
                    headers=self.headers,
                    params=api_params
                )
            
            # Parse response
            company_info = DartCompanyInfo(**response_data)
            
            # Check for API errors
            if not company_info.is_success:
                if company_info.status == "010":
                    raise APIKeyError("dart", "Invalid DART API key")
                elif company_info.status == "020":
                    raise ValidationError(f"Invalid parameter: {company_info.message}")
                elif company_info.status == "013":
                    raise ValidationError("Company not found with given corp_code")
                else:
                    raise ExternalAPIError(f"DART API error ({company_info.status}): {company_info.message}")
            
            logger.info(f"Company info retrieved successfully: {company_info.corp_name}")
            return company_info
            
        except ValidationError:
            raise
        except Exception as e:
            if hasattr(e, 'status_code'):
                # Handle HTTP errors
                if e.status_code == 401:
                    raise APIKeyError("dart", "Invalid DART API credentials")
                elif e.status_code == 429:
                    raise ExternalAPIError("Rate limit exceeded for DART API", e.status_code)
                elif e.status_code >= 500:
                    raise ExternalAPIError("DART API server error", e.status_code)
                else:
                    raise ExternalAPIError(f"DART API error: {str(e)}", e.status_code)
            else:
                raise ExternalAPIError(f"Unexpected error during company info retrieval: {str(e)}")


# Global API client instance
dart_disclosure_api = DartDisclosureAPI()