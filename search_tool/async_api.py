"""异步搜索 API - 支持并发请求和缓存"""

import asyncio
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from search_tool.engines.base import SearchResult, EngineError
from search_tool.engines.search import get_search_engine, DuckDuckGoEngine
from search_tool.engines.news import get_news_engine, NewsEngine
from search_tool.engines.social import get_social_engine, get_all_social_engines, SOCIAL_ENGINES
from search_tool.utils.cache import get_cache
from search_tool.utils.health import get_health_checker
from search_tool.config import get_config


@dataclass
class AsyncSearchOptions:
    """异步搜索选项"""
    engines: List[str] = None
    limit: int = 10
    platform: Optional[str] = None
    max_concurrent: int = 5  # 最大并发数


# 线程池执行器（用于包装同步引擎）
_executor: ThreadPoolExecutor = None


def get_executor(max_workers: int = None) -> ThreadPoolExecutor:
    """获取或创建线程池执行器"""
    global _executor
    if _executor is None:
        config = get_config()
        max_workers = max_workers or config.max_concurrent_engines
        _executor = ThreadPoolExecutor(max_workers=max_workers)
    return _executor


async def async_search(
    query: str,
    engines: List[str] = None,
    limit: int = 10,
    platform: Optional[str] = None,
    max_concurrent: int = None,
    use_cache: bool = True,
    use_health_check: bool = True
) -> List[SearchResult]:
    """
    异步并发搜索多个引擎

    Args:
        query: 搜索关键词
        engines: 引擎类型列表 ["search", "news", "social", "all"]
        limit: 每个引擎的最大结果数
        platform: 特定平台
        max_concurrent: 最大并发数
        use_cache: 是否使用缓存
        use_health_check: 是否检查源健康状态

    Returns:
        SearchResult 列表

    Example:
        >>> results = await async_search("Python tutorial", engines=["search", "news"])
    """
    if engines is None:
        engines = ["search"]

    config = get_config()
    max_concurrent = max_concurrent or config.max_concurrent_engines

    # Handle "all" engine type
    if "all" in engines:
        engines = ["search", "news", "social"]

    # 检查缓存（整体缓存）
    if use_cache and config.cache_enabled:
        cache = get_cache()
        cached = cache.get("combined", query, limit, platform)
        if cached:
            return cached

    # 健康检测
    if use_health_check:
        checker = get_health_checker()
        if checker.needs_refresh():
            # 在后台检测，不阻塞当前搜索
            asyncio.create_task(_async_health_check())

    # 并发执行各引擎搜索
    loop = asyncio.get_event_loop()
    executor = get_executor(max_concurrent)

    async def _run_engine(engine_type: str) -> List[SearchResult]:
        """运行单个引擎"""
        try:
            return await loop.run_in_executor(
                executor,
                _search_with_cache,
                engine_type,
                query,
                limit,
                platform,
                use_cache
            )
        except Exception as e:
            print(f"Engine {engine_type} failed: {e}")
            return []

    # 使用 asyncio.gather 并发执行
    tasks = [_run_engine(e) for e in engines]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 合并结果（忽略异常）
    all_results = []
    for r in results:
        if isinstance(r, list):
            all_results.extend(r)

    # 去重
    all_results = _deduplicate(all_results)

    # 缓存合并结果
    if use_cache and config.cache_enabled:
        cache = get_cache()
        cache.set("combined", query, limit, all_results, platform)

    return all_results


def _search_with_cache(
    engine_type: str,
    query: str,
    limit: int,
    platform: Optional[str],
    use_cache: bool
) -> List[SearchResult]:
    """带缓存的同步搜索"""
    config = get_config()

    # 检查缓存
    if use_cache and config.cache_enabled:
        cache = get_cache()
        cached = cache.get(engine_type, query, limit, platform)
        if cached:
            return cached

    # 执行搜索
    results = []

    if engine_type == "search":
        results = _search_web_with_health(query, limit, platform)
    elif engine_type == "news":
        results = _search_news_with_health(query, limit, platform)
    elif engine_type == "social":
        results = _search_social_with_health(query, limit, platform)

    # 缓存结果
    if use_cache and config.cache_enabled:
        cache = get_cache()
        cache.set(engine_type, query, limit, results, platform)

    return results


def _search_web_with_health(query: str, limit: int, platform: Optional[str]) -> List[SearchResult]:
    """Web 搜索（考虑健康状态）"""
    if platform:
        engine = get_search_engine(platform)
        return engine.search(query, limit)
    else:
        engine = DuckDuckGoEngine()
        return engine.search(query, limit)


def _search_news_with_health(query: str, limit: int, platform: Optional[str]) -> List[SearchResult]:
    """新闻搜索（考虑健康状态）"""
    engine = get_news_engine()
    checker = get_health_checker()

    # 过滤不健康的源
    if platform:
        if checker.should_skip(platform):
            return []
        return engine.search_source(platform, limit)
    else:
        # 过滤不健康的 RSS 源
        healthy_sources = checker.get_healthy_sources(engine.RSS_SOURCES)
        if healthy_sources:
            engine.RSS_SOURCES = healthy_sources
        return engine.search(query, limit)


def _search_social_with_health(query: str, limit: int, platform: Optional[str]) -> List[SearchResult]:
    """社交媒体搜索（考虑健康状态）"""
    checker = get_health_checker()

    if platform:
        if checker.should_skip(platform):
            return []
        engine = get_social_engine(platform)
        return engine.search(query, limit)
    else:
        # 搜索所有健康的社交平台
        all_results = []
        for engine in get_all_social_engines():
            engine_name = engine.name
            if checker.should_skip(engine_name):
                continue
            try:
                results = engine.search(query, limit)
                all_results.extend(results)
            except EngineError as e:
                print(f"Social engine [{e.engine_name}] failed: {e.message}")
                continue

        return all_results


def _deduplicate(results: List[SearchResult]) -> List[SearchResult]:
    """去重"""
    seen_urls = set()
    unique = []
    for r in results:
        if r.url not in seen_urls:
            seen_urls.add(r.url)
            unique.append(r)
    return unique


async def _async_health_check():
    """异步健康检测"""
    checker = get_health_checker()
    await checker.check_all()


async def async_search_web(query: str, limit: int = 10) -> List[SearchResult]:
    """异步 Web 搜索"""
    return await async_search(query, engines=["search"], limit=limit)


async def async_search_news(query: str, limit: int = 10) -> List[SearchResult]:
    """异步新闻搜索"""
    return await async_search(query, engines=["news"], limit=limit)


async def async_search_social(query: str, limit: int = 10, platform: str = None) -> List[SearchResult]:
    """异步社交媒体搜索"""
    return await async_search(query, engines=["social"], limit=limit, platform=platform)


# 性能对比测试
async def benchmark_search(query: str, engines: List[str] = ["search", "news"], limit: int = 10):
    """性能对比测试"""
    import time

    # 同步搜索
    from search_tool.api import search
    start = time.time()
    sync_results = search(query, engines=engines, limit=limit)
    sync_time = time.time() - start

    # 异步搜索
    start = time.time()
    async_results = await async_search(query, engines=engines, limit=limit)
    async_time = time.time() - start

    return {
        "sync_time": sync_time,
        "async_time": async_time,
        "sync_results": len(sync_results),
        "async_results": len(async_results),
        "improvement": f"{(sync_time - async_time) / sync_time * 100:.1f}%"
    }


# For direct module usage
if __name__ == "__main__":
    import time

    async def test():
        print("Testing async search API...")

        # Test web search
        print("\n=== Async Web Search ===")
        start = time.time()
        results = await async_search_web("Python programming", limit=3)
        elapsed = time.time() - start
        for r in results:
            print(f"- {r.title}")
        print(f"Time: {elapsed:.2f}s")

        # Test concurrent search
        print("\n=== Concurrent Search (search + news) ===")
        start = time.time()
        results = await async_search("AI technology", engines=["search", "news"], limit=5)
        elapsed = time.time() - start
        print(f"Results: {len(results)}")
        print(f"Time: {elapsed:.2f}s")

        # Benchmark
        print("\n=== Benchmark ===")
        stats = await benchmark_search("MCP protocol", engines=["search", "news"], limit=5)
        print(f"Sync time: {stats['sync_time']:.2f}s")
        print(f"Async time: {stats['async_time']:.2f}s")
        print(f"Improvement: {stats['improvement']}")

    asyncio.run(test())