"""
Rate limiting implementation
"""

import time
from typing import Dict, Any, Optional, Tuple
from collections import defaultdict, deque
import logging

from app.core.config import settings
from app.core.exceptions import RateLimitExceededError
from app.core.logging import logger


class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self):
        self.rate_limit_per_minute = settings.RATE_LIMIT_PER_MINUTE
        self.rate_limit_burst = settings.RATE_LIMIT_BURST
        
        # Store request timestamps for each user/IP
        self.request_history = defaultdict(lambda: deque())
        
        # Cleanup old entries periodically
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
    
    def is_allowed(self, identifier: str, limit_type: str = "standard") -> Tuple[bool, Dict[str, Any]]:
        """Check if request is allowed based on rate limits"""
        try:
            current_time = time.time()
            
            # Cleanup old entries periodically
            if current_time - self.last_cleanup > self.cleanup_interval:
                self._cleanup_old_entries()
                self.last_cleanup = current_time
            
            # Get rate limits based on type
            limits = self._get_limits_for_type(limit_type)
            
            # Get request history for identifier
            history = self.request_history[identifier]
            
            # Remove old entries (older than 1 minute)
            while history and current_time - history[0] > 60:
                history.popleft()
            
            # Check if limit exceeded
            if len(history) >= limits["per_minute"]:
                logger.warning(f"Rate limit exceeded for {identifier}: {len(history)} requests in last minute")
                return False, {
                    "allowed": False,
                    "limit_type": limit_type,
                    "requests_in_minute": len(history),
                    "limit_per_minute": limits["per_minute"],
                    "retry_after": 60 - (current_time - history[0]) if history else 0
                }
            
            # Add current request
            history.append(current_time)
            
            return True, {
                "allowed": True,
                "limit_type": limit_type,
                "requests_in_minute": len(history),
                "limit_per_minute": limits["per_minute"],
                "remaining_requests": limits["per_minute"] - len(history)
            }
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail open for safety
            return True, {"allowed": True, "error": str(e)}
    
    def _get_limits_for_type(self, limit_type: str) -> Dict[str, int]:
        """Get rate limits for specific type"""
        limits = {
            "standard": {
                "per_minute": self.rate_limit_per_minute,
                "burst": self.rate_limit_burst
            },
            "strict": {
                "per_minute": self.rate_limit_per_minute // 2,
                "burst": self.rate_limit_burst // 2
            },
            "image_upload": {
                "per_minute": 5,
                "burst": 2
            },
            "report_generation": {
                "per_minute": 10,
                "burst": 3
            },
            "admin": {
                "per_minute": self.rate_limit_per_minute * 2,
                "burst": self.rate_limit_burst * 2
            }
        }
        
        return limits.get(limit_type, limits["standard"])
    
    def _cleanup_old_entries(self):
        """Clean up old entries from request history"""
        try:
            current_time = time.time()
            cutoff_time = current_time - 300  # 5 minutes ago
            
            # Remove old entries
            for identifier in list(self.request_history.keys()):
                history = self.request_history[identifier]
                
                # Remove old timestamps
                while history and history[0] < cutoff_time:
                    history.popleft()
                
                # Remove empty histories
                if not history:
                    del self.request_history[identifier]
            
            logger.info(f"Rate limiter cleanup completed. Active identifiers: {len(self.request_history)}")
            
        except Exception as e:
            logger.error(f"Rate limiter cleanup error: {e}")
    
    def get_rate_limit_info(self, identifier: str) -> Dict[str, Any]:
        """Get rate limit information for identifier"""
        try:
            current_time = time.time()
            history = self.request_history[identifier]
            
            # Remove old entries
            while history and current_time - history[0] > 60:
                history.popleft()
            
            return {
                "identifier": identifier,
                "requests_in_minute": len(history),
                "limit_per_minute": self.rate_limit_per_minute,
                "remaining_requests": max(0, self.rate_limit_per_minute - len(history)),
                "reset_time": history[0] + 60 if history else current_time
            }
            
        except Exception as e:
            logger.error(f"Rate limit info error: {e}")
            return {"error": str(e)}
    
    def reset_rate_limit(self, identifier: str) -> bool:
        """Reset rate limit for identifier"""
        try:
            if identifier in self.request_history:
                del self.request_history[identifier]
                logger.info(f"Rate limit reset for {identifier}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Rate limit reset error: {e}")
            return False
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global rate limiting statistics"""
        try:
            current_time = time.time()
            active_identifiers = 0
            total_requests = 0
            
            for identifier, history in self.request_history.items():
                # Count recent requests
                recent_requests = sum(1 for timestamp in history if current_time - timestamp <= 60)
                if recent_requests > 0:
                    active_identifiers += 1
                    total_requests += recent_requests
            
            return {
                "active_identifiers": active_identifiers,
                "total_requests_last_minute": total_requests,
                "rate_limit_per_minute": self.rate_limit_per_minute,
                "rate_limit_burst": self.rate_limit_burst,
                "memory_usage": len(self.request_history)
            }
            
        except Exception as e:
            logger.error(f"Global stats error: {e}")
            return {"error": str(e)}


# Global rate limiter instance
rate_limiter = RateLimiter()
