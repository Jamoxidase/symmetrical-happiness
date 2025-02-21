"""Cache module supporting both Redis and in-memory caching."""

import os
import json
import pickle
import traceback
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
import redis
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class BaseCache(ABC):
    """Abstract base class for cache implementations."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, expiry: Optional[int] = None) -> None:
        """Set a value in the cache with optional expiry in seconds."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete a value from the cache."""
        pass

class RedisCache(BaseCache):
    """Redis-based cache implementation."""
    
    def __init__(self, redis_url: str):
        """Initialize Redis cache.
        
        Args:
            redis_url: Redis connection URL
        """
        try:
            self.redis = redis.from_url(redis_url)
            # Test connection
            self.redis.ping()
            logger.info("Successfully connected to Redis")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def get(self, key: str) -> Optional[Any]:
        try:
            value = self.redis.get(key)
            if not value:
                return None
            try:
                # Try JSON deserialization first
                return json.loads(value.decode('utf-8'))
            except json.JSONDecodeError:
                # Fall back to pickle if not JSON
                return pickle.loads(value)
        except Exception as e:
            logger.error(f"Error getting key {key} from Redis: {e}")
            return None
    
    def set(self, key: str, value: Any, expiry: Optional[int] = None) -> None:
        try:
            # Try to serialize as JSON first
            try:
                serialized = json.dumps(value)
            except (TypeError, json.JSONEncodeError):
                # Fall back to pickle if not JSON serializable
                serialized = pickle.dumps(value)
            
            if expiry:
                self.redis.setex(key, expiry, serialized)
            else:
                self.redis.set(key, serialized)
        except Exception as e:
            logger.error(f"Error setting key {key} in Redis: {e}")
            logger.error(traceback.format_exc())
    
    def delete(self, key: str) -> None:
        try:
            self.redis.delete(key)
        except Exception as e:
            logger.error(f"Error deleting key {key} from Redis: {e}")

class InMemoryCache(BaseCache):
    """Simple in-memory cache implementation using a dictionary."""
    
    def __init__(self):
        """Initialize in-memory cache."""
        self._cache: Dict[str, Any] = {}
        logger.info("Using in-memory cache")
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the in-memory cache."""
        try:
            value = self._cache.get(key)
            if value is None:
                return None
            
            # If value is already deserialized, return it
            if not isinstance(value, (str, bytes)):
                return value
                
            try:
                # Try JSON deserialization first
                if isinstance(value, str):
                    return json.loads(value)
                # Try pickle if it's bytes
                return pickle.loads(value)
            except (json.JSONDecodeError, pickle.UnpicklingError) as e:
                logger.error(f"Error deserializing value for key {key}: {e}")
                return None
        except Exception as e:
            logger.error(f"Error getting key {key} from in-memory cache: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def set(self, key: str, value: Any, expiry: Optional[int] = None) -> None:
        """Set a value in the in-memory cache.
        
        Note: expiry parameter is ignored in this simple implementation
        """
        try:
            # Try to serialize as JSON first
            try:
                serialized = json.dumps(value)
            except (TypeError, json.JSONEncodeError):
                # Fall back to pickle if not JSON serializable
                serialized = pickle.dumps(value)
            self._cache[key] = serialized
        except Exception as e:
            logger.error(f"Error setting key {key} in in-memory cache: {e}")
            logger.error(traceback.format_exc())
            # Store the original value as fallback
            self._cache[key] = value
    
    def delete(self, key: str) -> None:
        """Delete a value from the in-memory cache."""
        try:
            self._cache.pop(key, None)
        except Exception as e:
            logger.error(f"Error deleting key {key} from in-memory cache: {e}")
            logger.error(traceback.format_exc())

def get_cache() -> BaseCache:
    """Factory function to get the appropriate cache implementation based on settings."""
    use_redis = os.getenv('USE_REDIS', 'false').lower() == 'true'
    
    if use_redis:
        try:
            return RedisCache(settings.REDIS_URL)
        except Exception as e:
            logger.warning(f"Failed to initialize Redis cache: {e}. Falling back to in-memory cache.")
            return InMemoryCache()
    else:
        return InMemoryCache()

# Global cache instance
cache = get_cache()