"""
Cache manager for LangChain caching
"""

from typing import Any, Optional, Dict
from langchain.cache import InMemoryCache, SQLiteCache
from langchain.globals import set_llm_cache
import os
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching for LLM responses"""
    
    def __init__(self):
        self.cache_type = settings.ENVIRONMENT
        self._setup_cache()
    
    def _setup_cache(self):
        """Setup appropriate cache based on environment"""
        if self.cache_type == "production":
            # Use SQLite cache for production
            cache_path = "/tmp/langchain_cache.db"
            cache = SQLiteCache(database_path=cache_path)
            logger.info(f"Using SQLite cache: {cache_path}")
        else:
            # Use in-memory cache for development
            cache = InMemoryCache()
            logger.info("Using in-memory cache")
        
        set_llm_cache(cache)
        self.cache = cache
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if hasattr(self.cache, 'get_stats'):
            return self.cache.get_stats()
        return {"cache_type": self.cache_type}
    
    def clear_cache(self):
        """Clear the cache"""
        if hasattr(self.cache, 'clear'):
            self.cache.clear()
            logger.info("Cache cleared")
    
    def get_cached_response(self, key: str) -> Optional[Any]:
        """Get cached response by key"""
        if hasattr(self.cache, 'lookup'):
            return self.cache.lookup(key)
        return None
    
    def cache_response(self, key: str, response: Any):
        """Cache a response"""
        if hasattr(self.cache, 'update'):
            self.cache.update(key, response)
            logger.debug(f"Cached response for key: {key}")


# Global cache manager instance
cache_manager = CacheManager()
