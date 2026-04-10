"""Search result cache with TTL support."""

import time
import hashlib
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """Cache entry with TTL."""
    data: Any
    timestamp: float
    ttl: int


class SearchCache:
    """Search result cache manager."""

    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache.

        Args:
            default_ttl: Default TTL in seconds (default: 5 minutes)
        """
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._hit_count = 0
        self._miss_count = 0

    def _make_key(self, engine: str, query: str, limit: int, platform: str = None) -> str:
        """Generate cache key."""
        key_data = f"{engine}:{query}:{limit}:{platform or ''}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, engine: str, query: str, limit: int, platform: str = None) -> Optional[List]:
        """Get cached results."""
        key = self._make_key(engine, query, limit, platform)
        entry = self._cache.get(key)

        if entry and time.time() - entry.timestamp < entry.ttl:
            self._hit_count += 1
            return entry.data

        self._miss_count += 1
        return None

    def set(self, engine: str, query: str, limit: int, data: List, platform: str = None, ttl: int = None):
        """Set cache entry."""
        key = self._make_key(engine, query, limit, platform)
        self._cache[key] = CacheEntry(
            data=data,
            timestamp=time.time(),
            ttl=ttl or self.default_ttl
        )

    def clear(self):
        """Clear all cache."""
        self._cache.clear()
        self._hit_count = 0
        self._miss_count = 0

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        valid_entries = [
            e for e in self._cache.values()
            if time.time() - e.timestamp < e.ttl
        ]
        total_requests = self._hit_count + self._miss_count
        hit_rate = self._hit_count / total_requests if total_requests > 0 else 0

        return {
            "total_entries": len(self._cache),
            "valid_entries": len(valid_entries),
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate": round(hit_rate, 2)
        }


# Global cache instance
_cache: Optional[SearchCache] = None


def get_cache() -> SearchCache:
    """Get global cache instance."""
    global _cache
    if _cache is None:
        _cache = SearchCache()
    return _cache


def clear_cache():
    """Clear global cache."""
    get_cache().clear()