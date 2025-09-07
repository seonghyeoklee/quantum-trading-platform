"""
Configuration settings for Quantum Adapter External.
Handles environment variables and API keys securely.
"""

from pydantic_settings import BaseSettings
from pydantic import validator
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings with validation and type safety."""
    
    # Server Configuration
    server_host: str = "0.0.0.0"
    server_port: int = 8001
    debug: bool = False
    
    # Naver API Configuration
    naver_client_id: str
    naver_client_secret: str
    
    # DART API Configuration
    dart_api_key: str
    
    # Future API Keys (optional)
    google_api_key: Optional[str] = None
    alpha_vantage_api_key: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    @validator('naver_client_id')
    def validate_naver_client_id(cls, v):
        """Validate Naver Client ID is present."""
        if not v or len(v.strip()) == 0:
            raise ValueError('NAVER_CLIENT_ID is required')
        return v.strip()
    
    @validator('naver_client_secret')
    def validate_naver_client_secret(cls, v):
        """Validate Naver Client Secret is present."""
        if not v or len(v.strip()) == 0:
            raise ValueError('NAVER_CLIENT_SECRET is required')
        return v.strip()
    
    @validator('dart_api_key')
    def validate_dart_api_key(cls, v):
        """Validate DART API Key is present."""
        if not v or len(v.strip()) == 0:
            raise ValueError('DART_API_KEY is required')
        return v.strip()
    
    @property
    def naver_headers(self) -> dict:
        """Return Naver API headers."""
        return {
            'X-Naver-Client-Id': self.naver_client_id,
            'X-Naver-Client-Secret': self.naver_client_secret,
            'User-Agent': 'Quantum-Trading-Platform/1.0'
        }
    
    @property
    def dart_headers(self) -> dict:
        """Return DART API headers."""
        return {
            'User-Agent': 'Quantum-Trading-Platform/1.0'
        }


# Global settings instance
try:
    settings = Settings()
    print(f"✅ Configuration loaded successfully")
    print(f"   - Server: {settings.server_host}:{settings.server_port}")
    print(f"   - Debug: {settings.debug}")
    print(f"   - Naver Client ID: {settings.naver_client_id[:8]}***")
    print(f"   - DART API Key: {settings.dart_api_key[:8]}***")
except Exception as e:
    print(f"❌ Configuration error: {e}")
    print("   Please check your .env file and ensure all required variables are set")
    raise