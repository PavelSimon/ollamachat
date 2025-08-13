"""
Response Caching Module for OLLAMA Chat

This module provides TTL-based caching for expensive operations like
fetching model lists from OLLAMA servers.
"""

import time
import threading
import hashlib
import json
from typing import Any, Optional, Dict, Callable, Tuple
from dataclasses import dataclass
from functools import wraps
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Container for cached data with metadata."""
    data: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: float = 300  # 5 minutes default


class TTLCache:
    """
    Thread-safe TTL (Time To Live) cache with automatic cleanup.
    
    Features:
    - TTL-based expiration
    - LRU eviction when max size is reached
    - Background cleanup thread
    - Thread-safe operations
    - Cache statistics
    """
    
    def __init__(
        self,
        max_size: int = 100,
        default_ttl: float = 300,  # 5 minutes
        cleanup_interval: float = 60  # 1 minute
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        
        # Thread-safe storage
        self._lock = threading.RLock()
        self._cache: Dict[str, CacheEntry] = {}
        
        # Statistics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0,
            'cache_size': 0
        }
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
            name="TTLCacheCleanup"
        )
        self._cleanup_thread.start()
        
        logger.info(
            f"TTL cache initialized: max_size={max_size}, "
            f"default_ttl={default_ttl}s, cleanup_interval={cleanup_interval}s"
        )
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache, returns None if not found or expired."""
        with self._lock:
            current_time = time.time()
            
            if key not in self._cache:
                self._stats['misses'] += 1
                return None
            
            entry = self._cache[key]
            
            # Check if expired
            if current_time - entry.created_at > entry.ttl:
                del self._cache[key]
                self._stats['expirations'] += 1
                self._stats['misses'] += 1
                self._update_cache_size()
                return None
            
            # Update access stats
            entry.last_accessed = current_time
            entry.access_count += 1
            self._stats['hits'] += 1
            
            logger.debug(f"Cache hit for key: {key[:50]}...")
            return entry.data
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set item in cache with optional TTL override."""
        with self._lock:
            current_time = time.time()
            ttl = ttl or self.default_ttl
            
            # If cache is full, evict LRU item
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()
            
            # Create cache entry
            entry = CacheEntry(
                data=value,
                created_at=current_time,
                last_accessed=current_time,
                ttl=ttl
            )
            
            self._cache[key] = entry
            self._update_cache_size()
            
            logger.debug(f"Cached item with key: {key[:50]}... (TTL: {ttl}s)")
    
    def delete(self, key: str) -> bool:
        """Delete item from cache. Returns True if item was found and deleted."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._update_cache_size()
                logger.debug(f"Deleted cache entry: {key[:50]}...")
                return True
            return False
    
    def clear(self) -> None:
        """Clear all items from cache."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._stats['evictions'] += count
            self._update_cache_size()
            logger.info(f"Cleared {count} items from cache")
    
    def _evict_lru(self) -> None:
        """Evict least recently used item."""
        if not self._cache:
            return
        
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed
        )
        del self._cache[lru_key]
        self._stats['evictions'] += 1
        logger.debug(f"Evicted LRU cache entry: {lru_key[:50]}...")
    
    def _cleanup_loop(self):
        """Background cleanup thread to remove expired entries."""
        while True:
            try:
                time.sleep(self.cleanup_interval)
                self._cleanup_expired()
            except Exception as e:
                logger.error(f"Error in cache cleanup loop: {e}")
    
    def _cleanup_expired(self):
        """Remove expired entries from cache."""
        with self._lock:
            current_time = time.time()
            expired_keys = []
            
            for key, entry in self._cache.items():
                if current_time - entry.created_at > entry.ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                self._stats['expirations'] += 1
            
            if expired_keys:
                self._update_cache_size()
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def _update_cache_size(self):
        """Update cache size in stats."""
        self._stats['cache_size'] = len(self._cache)
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        with self._lock:
            return {
                **self._stats.copy(),
                'hit_rate': (
                    self._stats['hits'] / (self._stats['hits'] + self._stats['misses'])
                    if (self._stats['hits'] + self._stats['misses']) > 0
                    else 0.0
                ),
                'configuration': {
                    'max_size': self.max_size,
                    'default_ttl': self.default_ttl,
                    'cleanup_interval': self.cleanup_interval
                }
            }


# Global cache instances
_model_cache: Optional[TTLCache] = None
_general_cache: Optional[TTLCache] = None
_cache_lock = threading.Lock()


def get_model_cache() -> TTLCache:
    """Get the global model cache instance (singleton)."""
    global _model_cache
    
    if _model_cache is None:
        with _cache_lock:
            if _model_cache is None:
                _model_cache = TTLCache(
                    max_size=50,  # 50 different host configurations
                    default_ttl=300,  # 5 minutes for model lists
                    cleanup_interval=60
                )
    
    return _model_cache


def get_general_cache() -> TTLCache:
    """Get the general purpose cache instance (singleton)."""
    global _general_cache
    
    if _general_cache is None:
        with _cache_lock:
            if _general_cache is None:
                _general_cache = TTLCache(
                    max_size=100,
                    default_ttl=60,  # 1 minute for general data
                    cleanup_interval=30
                )
    
    return _general_cache


def create_cache_key(*args, **kwargs) -> str:
    """Create a deterministic cache key from arguments."""
    # Convert arguments to a stable string representation
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items()) if kwargs else {}
    }
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    
    # Create hash for consistent key length
    return hashlib.sha256(key_string.encode()).hexdigest()


def cached_models(ttl: float = 300):
    """
    Decorator for caching model list responses.
    
    Args:
        ttl: Time to live in seconds (default: 5 minutes)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key based on function arguments
            cache_key = f"models:{create_cache_key(*args, **kwargs)}"
            cache = get_model_cache()
            
            # Try to get from cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Model cache hit for: {func.__name__}")
                return cached_result
            
            # Cache miss - execute function
            logger.debug(f"Model cache miss for: {func.__name__}")
            result = func(*args, **kwargs)
            
            # Cache the result
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def cached_response(cache_name: str = "general", ttl: float = 60):
    """
    General purpose response caching decorator.
    
    Args:
        cache_name: Which cache to use ("general" or "models")
        ttl: Time to live in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Choose cache instance
            if cache_name == "models":
                cache = get_model_cache()
            else:
                cache = get_general_cache()
            
            # Create cache key
            cache_key = f"{func.__name__}:{create_cache_key(*args, **kwargs)}"
            
            # Try cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for: {func.__name__}")
                return cached_result
            
            # Execute function
            logger.debug(f"Cache miss for: {func.__name__}")
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def invalidate_models_cache(host: str = None):
    """
    Invalidate cached model data.
    
    Args:
        host: If provided, only invalidate cache for specific host.
              If None, clear all model cache.
    """
    cache = get_model_cache()
    
    if host is None:
        cache.clear()
        logger.info("Cleared all model cache")
    else:
        # Find and remove entries for specific host
        with cache._lock:
            keys_to_remove = []
            for key in cache._cache.keys():
                if host in key:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                cache.delete(key)
            
            logger.info(f"Invalidated model cache for host: {host}")


def get_cache_stats() -> Dict:
    """Get statistics for all caches."""
    return {
        'model_cache': get_model_cache().get_stats(),
        'general_cache': get_general_cache().get_stats()
    }