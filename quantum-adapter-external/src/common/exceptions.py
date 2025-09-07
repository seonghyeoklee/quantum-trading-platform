"""
Common exceptions for the Quantum Adapter External.
"""

from typing import Optional, Dict, Any


class ExternalAPIError(Exception):
    """Base exception for external API errors."""
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        provider: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.provider = provider
        self.details = details or {}
        super().__init__(self.message)


class NaverAPIError(ExternalAPIError):
    """Exception for Naver API specific errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code, "naver", details)


class RateLimitError(ExternalAPIError):
    """Exception for API rate limit errors."""
    
    def __init__(self, provider: str, message: str = "Rate limit exceeded"):
        super().__init__(message, 429, provider)


class APIKeyError(ExternalAPIError):
    """Exception for API key related errors."""
    
    def __init__(self, provider: str, message: str = "Invalid API key"):
        super().__init__(message, 401, provider)


class ValidationError(ExternalAPIError):
    """Exception for request validation errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 400, None, details)