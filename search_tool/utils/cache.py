"""搜索结果缓存 - 评分随结果一并缓存"""

import time
import hashlib
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """缓存条目"""
    data: Any  # 包含评分的 SearchResult 列表
    timestamp: float
    ttl: int  # 秒


class SearchCache:
    """搜索结果缓存管理器"""

    def __init__(self, cache_dir: Path = None, default_ttl: int = 300):
        """
        初始化缓存

        Args:
            cache_dir: 缓存目录（暂未使用，仅内存缓存）
            default_ttl: 默认缓存过期时间（秒），默认 300 秒（5分钟）
        """
        self.cache_dir = cache_dir or Path.home() / ".search_tool_cache"
        self.default_ttl = default_ttl
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._hit_count = 0
        self._miss_count = 0

    def _make_key(self, engine: str, query: str, limit: int, platform: str = None) -> str:
        """
        生成缓存 key

        Args:
            engine: 引擎类型 (search/news/social)
            query: 搜索关键词
            limit: 结果数量限制
            platform: 平台名称（可选）

        Returns:
            MD5 hash 作为缓存 key
        """
        key_data = f"{engine}:{query}:{limit}:{platform or ''}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, engine: str, query: str, limit: int, platform: str = None) -> Optional[List]:
        """
        获取缓存（包含评分的结果）

        Args:
            engine: 引擎类型
            query: 搜索关键词
            limit: 结果数量限制
            platform: 平台名称

        Returns:
            缓存的结果列表（已包含评分），或 None 如果缓存不存在/过期
        """
        key = self._make_key(engine, query, limit, platform)
        entry = self._memory_cache.get(key)

        if entry and time.time() - entry.timestamp < entry.ttl:
            self._hit_count += 1
            return entry.data  # 返回已评分的结果

        self._miss_count += 1
        return None

    def set(self, engine: str, query: str, limit: int, data: List, platform: str = None, ttl: int = None):
        """
        设置缓存（数据应已包含评分）

        Args:
            engine: 引擎类型
            query: 搜索关键词
            limit: 结果数量限制
            data: 结果列表（应已包含评分）
            platform: 平台名称
            ttl: 过期时间（秒），默认使用 default_ttl
        """
        key = self._make_key(engine, query, limit, platform)
        self._memory_cache[key] = CacheEntry(
            data=data,
            timestamp=time.time(),
            ttl=ttl if ttl is not None else self.default_ttl
        )

    def clear(self):
        """清空所有缓存"""
        self._memory_cache.clear()
        self._hit_count = 0
        self._miss_count = 0

    def stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            包含 total_entries, valid_entries, hit_rate 的字典
        """
        valid_entries = [
            e for e in self._memory_cache.values()
            if time.time() - e.timestamp < e.ttl
        ]
        total_requests = self._hit_count + self._miss_count
        hit_rate = self._hit_count / total_requests if total_requests > 0 else 0

        return {
            "total_entries": len(self._memory_cache),
            "valid_entries": len(valid_entries),
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate": round(hit_rate, 2)
        }

    def invalidate(self, engine: str, query: str, limit: int, platform: str = None):
        """
        使特定缓存失效

        Args:
            engine: 引擎类型
            query: 搜索关键词
            limit: 结果数量限制
            platform: 平台名称
        """
        key = self._make_key(engine, query, limit, platform)
        if key in self._memory_cache:
            del self._memory_cache[key]


# 全局缓存实例
_cache: Optional[SearchCache] = None


def get_cache() -> SearchCache:
    """获取全局缓存实例"""
    global _cache
    if _cache is None:
        _cache = SearchCache()
    return _cache


def clear_cache():
    """清空全局缓存"""
    get_cache().clear()