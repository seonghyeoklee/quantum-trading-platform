"""
HTTP client utilities for external API calls.
"""

import httpx
from typing import Dict, Any, Optional
from urllib.parse import urlencode
import asyncio
from src.common.exceptions import ExternalAPIError


class HTTPClient:
    """Async HTTP client with error handling and timeouts."""
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform async GET request.
        
        Args:
            url: Request URL
            headers: HTTP headers
            params: Query parameters
            
        Returns:
            JSON response data
            
        Raises:
            ExternalAPIError: On request failure
        """
        if not self._client:
            raise RuntimeError("HTTPClient must be used as async context manager")
        
        try:
            # Build URL with parameters
            if params:
                query_string = urlencode(params, safe='', encoding='utf-8')
                url = f"{url}?{query_string}"
            
            response = await self._client.get(url, headers=headers)
            
            # Check for HTTP errors
            if response.status_code >= 400:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                raise ExternalAPIError(
                    message=error_msg,
                    status_code=response.status_code,
                    details={"url": url, "response": response.text}
                )
            
            # Parse JSON response
            return response.json()
            
        except httpx.TimeoutException as e:
            raise ExternalAPIError(
                message=f"Request timeout after {self.timeout}s",
                status_code=408,
                details={"url": url, "timeout": self.timeout}
            )
        except httpx.RequestError as e:
            raise ExternalAPIError(
                message=f"Request failed: {str(e)}",
                details={"url": url, "error": str(e)}
            )
        except Exception as e:
            if isinstance(e, ExternalAPIError):
                raise
            raise ExternalAPIError(
                message=f"Unexpected error: {str(e)}",
                details={"url": url, "error": str(e)}
            )