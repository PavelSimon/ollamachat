"""
OLLAMA Client Connection Pool Manager

This module provides connection pooling and caching for OLLAMA clients
to improve performance and reduce resource usage.
"""

import time
import threading
from typing import Dict, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass
from ollama_client import OllamaClient
import logging

logger = logging.getLogger(__name__)


@dataclass
class PooledClient:
    """Container for pooled OLLAMA client with metadata."""
    client: OllamaClient
    last_used: float
    created_at: float
    use_count: int = 0


class OllamaConnectionPool:
    """
    Connection pool for OLLAMA clients with LRU eviction and health checking.
    
    Features:
    - Per-host connection pooling
    - LRU eviction based on configurable TTL
    - Health checking for stale connections
    - Thread-safe operations
    - Usage statistics
    """
    
    def __init__(
        self,
        max_connections_per_host: int = 5,
        connection_ttl: int = 300,  # 5 minutes
        cleanup_interval: int = 60   # 1 minute
    ):
        self.max_connections_per_host = max_connections_per_host
        self.connection_ttl = connection_ttl
        self.cleanup_interval = cleanup_interval
        
        # Thread-safe storage
        self._lock = threading.RLock()
        self._pools: Dict[str, Dict[int, PooledClient]] = defaultdict(dict)
        self._next_id = 0
        
        # Statistics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'health_checks': 0,
            'failed_health_checks': 0
        }
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
            name="OllamaPoolCleanup"
        )
        self._cleanup_thread.start()
        
        logger.info(
            f"OLLAMA connection pool initialized: "
            f"max_per_host={max_connections_per_host}, "
            f"ttl={connection_ttl}s, cleanup_interval={cleanup_interval}s"
        )
    
    def get_client(self, host: str) -> OllamaClient:
        """
        Get an OLLAMA client for the specified host.
        
        Returns either a pooled client or creates a new one.
        """
        with self._lock:
            current_time = time.time()
            host_pool = self._pools[host]
            
            # Try to find a healthy client in the pool
            for client_id, pooled in list(host_pool.items()):
                # Check if client is still valid
                if current_time - pooled.last_used > self.connection_ttl:
                    # Client is too old, remove it
                    del host_pool[client_id]
                    self._stats['evictions'] += 1
                    continue
                
                # Check if client is still healthy
                if self._is_client_healthy(pooled.client):
                    # Update usage stats and return
                    pooled.last_used = current_time
                    pooled.use_count += 1
                    self._stats['hits'] += 1
                    
                    logger.debug(
                        f"Reusing pooled client for {host} "
                        f"(id={client_id}, uses={pooled.use_count})"
                    )
                    return pooled.client
                else:
                    # Client is unhealthy, remove it
                    del host_pool[client_id]
                    self._stats['failed_health_checks'] += 1
                    logger.debug(f"Removed unhealthy client for {host} (id={client_id})")
            
            # No healthy client found, create a new one
            self._stats['misses'] += 1
            client = OllamaClient(host)
            
            # Add to pool if there's space
            if len(host_pool) < self.max_connections_per_host:
                client_id = self._next_id
                self._next_id += 1
                
                pooled = PooledClient(
                    client=client,
                    last_used=current_time,
                    created_at=current_time,
                    use_count=1
                )
                host_pool[client_id] = pooled
                
                logger.debug(
                    f"Created new pooled client for {host} "
                    f"(id={client_id}, pool_size={len(host_pool)})"
                )
            else:
                # Pool is full, evict LRU client
                lru_id = min(host_pool.keys(), key=lambda k: host_pool[k].last_used)
                del host_pool[lru_id]
                self._stats['evictions'] += 1
                
                # Add new client
                client_id = self._next_id
                self._next_id += 1
                
                pooled = PooledClient(
                    client=client,
                    last_used=current_time,
                    created_at=current_time,
                    use_count=1
                )
                host_pool[client_id] = pooled
                
                logger.debug(
                    f"Created new pooled client for {host} after LRU eviction "
                    f"(id={client_id}, evicted={lru_id})"
                )
            
            return client
    
    def _is_client_healthy(self, client: OllamaClient) -> bool:
        """Check if a client is still healthy by testing connection."""
        try:
            # Quick health check
            healthy = client.test_connection()
            self._stats['health_checks'] += 1
            return healthy
        except Exception as e:
            logger.debug(f"Health check failed for client {client.base_url}: {e}")
            self._stats['failed_health_checks'] += 1
            return False
    
    def _cleanup_loop(self):
        """Background cleanup thread to remove stale connections."""
        while True:
            try:
                time.sleep(self.cleanup_interval)
                self._cleanup_stale_connections()
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    def _cleanup_stale_connections(self):
        """Remove stale connections from all pools."""
        with self._lock:
            current_time = time.time()
            total_removed = 0
            
            for host, host_pool in list(self._pools.items()):
                stale_ids = []
                
                for client_id, pooled in host_pool.items():
                    if current_time - pooled.last_used > self.connection_ttl:
                        stale_ids.append(client_id)
                
                # Remove stale clients
                for client_id in stale_ids:
                    del host_pool[client_id]
                    total_removed += 1
                    self._stats['evictions'] += 1
                
                # Remove empty host pools
                if not host_pool:
                    del self._pools[host]
            
            if total_removed > 0:
                logger.debug(f"Cleaned up {total_removed} stale connections")
    
    def get_stats(self) -> Dict:
        """Get connection pool statistics."""
        with self._lock:
            pool_stats = {}
            total_connections = 0
            
            for host, host_pool in self._pools.items():
                pool_stats[host] = {
                    'active_connections': len(host_pool),
                    'clients': [
                        {
                            'id': client_id,
                            'use_count': pooled.use_count,
                            'age_seconds': time.time() - pooled.created_at,
                            'last_used_seconds_ago': time.time() - pooled.last_used
                        }
                        for client_id, pooled in host_pool.items()
                    ]
                }
                total_connections += len(host_pool)
            
            return {
                'global_stats': self._stats.copy(),
                'total_active_connections': total_connections,
                'pools_by_host': pool_stats,
                'configuration': {
                    'max_connections_per_host': self.max_connections_per_host,
                    'connection_ttl': self.connection_ttl,
                    'cleanup_interval': self.cleanup_interval
                }
            }
    
    def invalidate_host(self, host: str):
        """Invalidate all connections for a specific host."""
        with self._lock:
            if host in self._pools:
                count = len(self._pools[host])
                del self._pools[host]
                self._stats['evictions'] += count
                logger.info(f"Invalidated {count} connections for host {host}")
    
    def clear_all(self):
        """Clear all connections from the pool."""
        with self._lock:
            total = sum(len(pool) for pool in self._pools.values())
            self._pools.clear()
            self._stats['evictions'] += total
            logger.info(f"Cleared all {total} connections from pool")


# Global connection pool instance
_connection_pool: Optional[OllamaConnectionPool] = None
_pool_lock = threading.Lock()


def get_connection_pool() -> OllamaConnectionPool:
    """Get the global connection pool instance (singleton)."""
    global _connection_pool
    
    if _connection_pool is None:
        with _pool_lock:
            if _connection_pool is None:
                _connection_pool = OllamaConnectionPool()
    
    return _connection_pool


def get_pooled_client(host: str) -> OllamaClient:
    """
    Get a pooled OLLAMA client for the specified host.
    
    This is the main entry point for getting OLLAMA clients
    with connection pooling enabled.
    """
    pool = get_connection_pool()
    return pool.get_client(host)


def get_pool_stats() -> Dict:
    """Get connection pool statistics."""
    pool = get_connection_pool()
    return pool.get_stats()


def invalidate_host_connections(host: str):
    """Invalidate all pooled connections for a specific host."""
    pool = get_connection_pool()
    pool.invalidate_host(host)


def clear_connection_pool():
    """Clear all connections from the pool."""
    pool = get_connection_pool()
    pool.clear_all()