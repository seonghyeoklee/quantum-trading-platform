"""
DB 기반 토큰 관리자 - PostgreSQL 직접 연결
KIS 토큰을 데이터베이스에서 직접 조회하고 관리합니다.
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

logger = logging.getLogger(__name__)

class DBTokenManager:
    """데이터베이스 직접 연결을 통한 KIS 토큰 관리"""
    
    def __init__(self, db_config: Dict[str, str] = None):
        """
        DBTokenManager 초기화
        
        Args:
            db_config: 데이터베이스 연결 정보
        """
        self.db_config = db_config or {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432"),
            "database": os.getenv("DB_NAME", "quantum_trading"),
            "user": os.getenv("DB_USER", "quantum"),
            "password": os.getenv("DB_PASSWORD", "quantum123")
        }
        self.available = PSYCOPG2_AVAILABLE
        
        if not self.available:
            logger.warning("psycopg2 not available - DB token management disabled")
    
    def get_connection(self):
        """데이터베이스 연결을 반환합니다."""
        if not self.available:
            return None
        
        try:
            return psycopg2.connect(
                host=self.db_config["host"],
                port=self.db_config["port"],
                database=self.db_config["database"],
                user=self.db_config["user"],
                password=self.db_config["password"],
                cursor_factory=RealDictCursor
            )
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    def get_active_token(self, user_id: int, environment: str = "LIVE") -> Optional[str]:
        """
        활성 KIS 토큰을 조회합니다.
        
        Args:
            user_id: 사용자 ID (기본값: 1 = admin)
            environment: KIS 환경 ("LIVE" 또는 "SANDBOX")
            
        Returns:
            액세스 토큰 문자열 또는 None
        """
        if not self.available:
            logger.warning("DB token manager not available")
            return None
        
        conn = self.get_connection()
        if not conn:
            logger.error("Cannot connect to database")
            return None
        
        try:
            with conn.cursor() as cursor:
                # 활성 토큰 조회
                query = """
                SELECT access_token, expires_at 
                FROM kis_tokens 
                WHERE user_id = %s 
                  AND environment = %s 
                  AND status = 'ACTIVE'
                  AND expires_at > NOW()
                ORDER BY created_at DESC
                LIMIT 1
                """
                
                cursor.execute(query, (user_id, environment))
                result = cursor.fetchone()
                
                if result:
                    logger.info(f"✅ DB에서 활성 토큰 조회 성공 - User: {user_id}, Env: {environment}")
                    logger.info(f"토큰 만료: {result['expires_at']}")
                    return result['access_token']
                else:
                    logger.warning(f"❌ DB에서 활성 토큰 없음 - User: {user_id}, Env: {environment}")
                    return None
                    
        except Exception as e:
            logger.error(f"DB token query failed: {e}")
            return None
        finally:
            conn.close()
    
    def get_token_status(self, user_id: int, environment: str = "LIVE") -> Optional[Dict[str, Any]]:
        """
        토큰 상태 정보를 조회합니다.
        
        Args:
            user_id: 사용자 ID
            environment: KIS 환경
            
        Returns:
            토큰 상태 정보 딕셔너리
        """
        if not self.available:
            return None
        
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cursor:
                query = """
                SELECT 
                    access_token,
                    expires_at,
                    created_at,
                    status,
                    refresh_count,
                    last_used_at,
                    EXTRACT(EPOCH FROM (expires_at - NOW())) / 60 as remaining_minutes
                FROM kis_tokens 
                WHERE user_id = %s 
                  AND environment = %s 
                  AND status = 'ACTIVE'
                ORDER BY created_at DESC
                LIMIT 1
                """
                
                cursor.execute(query, (user_id, environment))
                result = cursor.fetchone()
                
                if result:
                    return {
                        "has_token": True,
                        "is_valid": result['remaining_minutes'] > 0,
                        "expires_at": result['expires_at'],
                        "remaining_minutes": max(0, int(result['remaining_minutes'])),
                        "status": result['status'],
                        "environment": environment,
                        "needs_refresh": result['remaining_minutes'] < 60,  # 1시간 미만
                        "last_used": result['last_used_at'],
                        "refresh_count": result['refresh_count']
                    }
                else:
                    return {
                        "has_token": False,
                        "is_valid": False,
                        "environment": environment
                    }
                    
        except Exception as e:
            logger.error(f"DB token status query failed: {e}")
            return None
        finally:
            conn.close()
    
    def update_last_used(self, user_id: int, environment: str = "LIVE"):
        """
        토큰 최종 사용 시간을 업데이트합니다.
        
        Args:
            user_id: 사용자 ID
            environment: KIS 환경
        """
        if not self.available:
            return
        
        conn = self.get_connection()
        if not conn:
            return
        
        try:
            with conn.cursor() as cursor:
                query = """
                UPDATE kis_tokens 
                SET last_used_at = NOW(),
                    updated_at = NOW()
                WHERE user_id = %s 
                  AND environment = %s 
                  AND status = 'ACTIVE'
                """
                
                cursor.execute(query, (user_id, environment))
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.debug(f"Token usage updated for user {user_id}, env {environment}")
                    
        except Exception as e:
            logger.error(f"Failed to update token usage: {e}")
        finally:
            conn.close()


# 전역 토큰 관리자 인스턴스
db_token_manager = DBTokenManager()

def get_kis_token_from_db(user_id: int = 1, environment: str = "prod") -> Optional[str]:
    """
    DB에서 KIS 토큰을 조회하는 헬퍼 함수
    
    Args:
        user_id: 사용자 ID (기본값: 1 = admin 사용자)
        environment: 환경 ("prod" -> "LIVE", "vps" -> "SANDBOX")
        
    Returns:
        KIS 액세스 토큰 또는 None
    """
    # 환경 매핑
    db_environment = "LIVE" if environment == "prod" else "SANDBOX"
    
    token = db_token_manager.get_active_token(user_id, db_environment)
    
    if token:
        # 사용 시간 업데이트
        db_token_manager.update_last_used(user_id, db_environment)
        logger.info(f"🔑 DB에서 토큰 조회 성공: User {user_id}, Env {db_environment}")
    else:
        logger.warning(f"🔑 DB에서 토큰 조회 실패: User {user_id}, Env {db_environment}")
    
    return token

def get_token_status_from_db(user_id: int = 1, environment: str = "prod") -> Optional[Dict[str, Any]]:
    """
    DB에서 토큰 상태를 조회하는 헬퍼 함수
    
    Args:
        user_id: 사용자 ID
        environment: 환경
        
    Returns:
        토큰 상태 정보
    """
    db_environment = "LIVE" if environment == "prod" else "SANDBOX"
    return db_token_manager.get_token_status(user_id, db_environment)

def is_db_available() -> bool:
    """
    DB 토큰 관리자 사용 가능 여부 확인
    
    Returns:
        DB 연결 및 psycopg2 사용 가능 여부
    """
    if not db_token_manager.available:
        return False
    
    # 실제 DB 연결 테스트
    conn = db_token_manager.get_connection()
    if conn:
        conn.close()
        return True
    return False