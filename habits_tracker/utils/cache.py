"""Caching utilities for HabitsTracker performance optimization."""

import time
from typing import Any, Dict, Optional, Callable, Union
from functools import wraps
from datetime import datetime, timedelta


class SimpleCache:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        """Initialize cache with default TTL in seconds."""
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        if time.time() > entry["expires"]:
            del self.cache[key]
            return None
        
        entry["hits"] += 1
        entry["last_accessed"] = time.time()
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        if ttl is None:
            ttl = self.default_ttl
        
        self.cache[key] = {
            "value": value,
            "expires": time.time() + ttl,
            "created": time.time(),
            "last_accessed": time.time(),
            "hits": 0
        }
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time > entry["expires"]
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.cache:
            return {
                "size": 0,
                "total_hits": 0,
                "avg_hits_per_entry": 0,
                "expired_entries": 0
            }
        
        current_time = time.time()
        total_hits = sum(entry["hits"] for entry in self.cache.values())
        expired_count = sum(
            1 for entry in self.cache.values() 
            if current_time > entry["expires"]
        )
        
        return {
            "size": len(self.cache),
            "total_hits": total_hits,
            "avg_hits_per_entry": total_hits / len(self.cache) if self.cache else 0,
            "expired_entries": expired_count
        }


# Global cache instances
habit_cache = SimpleCache(default_ttl=180)  # 3 minutes for habit data
stats_cache = SimpleCache(default_ttl=60)   # 1 minute for stats
query_cache = SimpleCache(default_ttl=30)   # 30 seconds for query results


def cached(cache_instance: SimpleCache, ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """Decorator for caching function results."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Simple key generation based on function name and arguments
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
                cache_key = "|".join(key_parts)
            
            # Try to get from cache
            cached_result = cache_instance.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_instance.set(cache_key, result, ttl)
            
            return result
        
        # Add cache management methods to wrapper
        wrapper.cache_clear = lambda: cache_instance.clear()
        wrapper.cache_stats = lambda: cache_instance.get_stats()
        wrapper.cache_cleanup = lambda: cache_instance.cleanup_expired()
        
        return wrapper
    
    return decorator


def cache_key_for_habit_stats(habit_name: str, period: str = "all") -> str:
    """Generate cache key for habit statistics."""
    # Include current date to ensure daily stats refresh
    today = datetime.now().strftime("%Y-%m-%d")
    return f"habit_stats|{habit_name}|{period}|{today}"


def cache_key_for_overall_stats(period: str = "all") -> str:
    """Generate cache key for overall statistics."""
    today = datetime.now().strftime("%Y-%m-%d")
    hour = datetime.now().hour  # Refresh hourly
    return f"overall_stats|{period}|{today}|{hour}"


def cache_key_for_today_status() -> str:
    """Generate cache key for today's status."""
    today = datetime.now().strftime("%Y-%m-%d")
    return f"today_status|{today}"


class QueryResultCache:
    """Specialized cache for database query results."""
    
    def __init__(self, max_size: int = 100):
        self.cache = SimpleCache(default_ttl=60)  # 1 minute TTL
        self.max_size = max_size
    
    def cache_query_result(self, query_hash: str, result: Any, ttl: int = 60) -> None:
        """Cache a query result."""
        # Implement LRU eviction if cache is full
        if len(self.cache.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(
                self.cache.cache.keys(),
                key=lambda k: self.cache.cache[k]["last_accessed"]
            )
            self.cache.delete(oldest_key)
        
        self.cache.set(query_hash, result, ttl)
    
    def get_query_result(self, query_hash: str) -> Optional[Any]:
        """Get cached query result."""
        return self.cache.get(query_hash)
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching a pattern."""
        matching_keys = [
            key for key in self.cache.cache.keys()
            if pattern in key
        ]
        
        for key in matching_keys:
            self.cache.delete(key)
        
        return len(matching_keys)


# Global query cache
query_result_cache = QueryResultCache()


def invalidate_habit_caches(habit_name: Optional[str] = None) -> None:
    """Invalidate caches when habit data changes."""
    if habit_name:
        # Invalidate specific habit caches
        stats_cache.clear()  # Clear all stats as they may be affected
        query_result_cache.invalidate_pattern(f"habit_stats|{habit_name}")
    else:
        # Invalidate all habit-related caches
        habit_cache.clear()
        stats_cache.clear()
        query_cache.clear()


def invalidate_tracking_caches() -> None:
    """Invalidate caches when tracking data changes."""
    stats_cache.clear()  # All stats may be affected
    query_result_cache.invalidate_pattern("today_status")
    query_result_cache.invalidate_pattern("overall_stats")


def get_cache_report() -> Dict[str, Any]:
    """Get comprehensive cache performance report."""
    return {
        "habit_cache": habit_cache.get_stats(),
        "stats_cache": stats_cache.get_stats(),
        "query_cache": query_cache.get_stats(),
        "query_result_cache": {
            "size": len(query_result_cache.cache.cache),
            "max_size": query_result_cache.max_size,
            "utilization": len(query_result_cache.cache.cache) / query_result_cache.max_size
        }
    }


def cleanup_all_caches() -> Dict[str, int]:
    """Clean up expired entries from all caches."""
    return {
        "habit_cache_expired": habit_cache.cleanup_expired(),
        "stats_cache_expired": stats_cache.cleanup_expired(),
        "query_cache_expired": query_cache.cleanup_expired(),
        "query_result_cache_expired": query_result_cache.cache.cleanup_expired()
    }