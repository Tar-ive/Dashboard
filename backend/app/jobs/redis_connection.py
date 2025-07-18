"""Redis connection management for job queue system."""

import redis
from typing import Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class RedisConnection:
    """Manages Redis connection for job queue system."""
    
    _instance: Optional[redis.Redis] = None
    
    @classmethod
    def get_connection(cls) -> redis.Redis:
        """Get Redis connection instance (singleton pattern)."""
        if cls._instance is None:
            try:
                cls._instance = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                # Test connection
                cls._instance.ping()
                logger.info(f"Redis connection established: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            except redis.ConnectionError as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error connecting to Redis: {e}")
                raise
        
        return cls._instance
    
    @classmethod
    def test_connection(cls) -> bool:
        """Test Redis connection health."""
        try:
            conn = cls.get_connection()
            conn.ping()
            return True
        except Exception as e:
            logger.error(f"Redis connection test failed: {e}")
            return False
    
    @classmethod
    def close_connection(cls) -> None:
        """Close Redis connection."""
        if cls._instance:
            cls._instance.close()
            cls._instance = None
            logger.info("Redis connection closed")

# Convenience function for getting Redis connection
def get_redis() -> redis.Redis:
    """Get Redis connection instance."""
    return RedisConnection.get_connection()