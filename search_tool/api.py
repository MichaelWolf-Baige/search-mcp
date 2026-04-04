"""Unified search API - Main entry point for all search functionality"""

from typing import List, Optional, Union
from dataclasses import dataclass

from search_tool.engines.base import SearchResult, EngineError
from search_tool.engines.search import get_search_engine, DuckDuckGoEngine
from search_tool.engines.news import get_news_engine, NewsEngine
from search_tool.engines.social import get_social_engine, get_all_social_engines, SOCIAL_ENGINES
from search_tool.utils.formatter import format_results


@dataclass
class SearchOptions:
    """Options for search operations"""

    engines: List[str] = None  # search, news, social, all
    limit: int = 10
    platform: Optional[str] = None  # Specific platform (weibo, reddit, etc.)
    format: str = "mcp"  # Output format


def search(
    query: str,
    engines: List[str] = None,
    limit: int = 10,
    platform: Optional[str] = None,
) -> List[SearchResult]:
    """
    Unified search function - Main API entry point

    Args:
        query: Search query string
        engines: List of engine types to use ("search", "news", "social", "all")
                 Default: ["search"]
        limit: Maximum results per engine
        platform: Specific platform to search (e.g., "weibo", "reddit")

    Returns:
        List of SearchResult objects

    Example:
        >>> results = search("Python tutorial")
        >>> results = search("AI news", engines=["news"])
        >>> results = search("hot topics", engines=["social"], platform="weibo")
    """
    if engines is None:
        engines = ["search"]

    all_results = []

    # Handle "all" engine type
    if "all" in engines:
        engines = ["search", "news", "social"]

    for engine_type in engines:
        try:
            if engine_type == "search":
                results = _search_web(query, limit, platform)
            elif engine_type == "news":
                results = _search_news(query, limit, platform)
            elif engine_type == "social":
                results = _search_social(query, limit, platform)
            else:
                print(f"Unknown engine type: {engine_type}")
                continue

            all_results.extend(results)

        except EngineError as e:
            print(f"Engine error [{e.engine_name}]: {e.message}")
            continue
        except Exception as e:
            print(f"Unexpected error: {e}")
            continue

    return all_results


def _search_web(query: str, limit: int, platform: Optional[str]) -> List[SearchResult]:
    """Search web using search engines"""
    if platform:
        # Use specific search platform
        engine = get_search_engine(platform)
        return engine.search(query, limit)
    else:
        # Default to DuckDuckGo
        engine = DuckDuckGoEngine()
        return engine.search(query, limit)


def _search_news(query: str, limit: int, platform: Optional[str]) -> List[SearchResult]:
    """Search news sources"""
    engine = get_news_engine()

    if platform:
        # Search specific news source
        return engine.search_source(platform, limit)
    else:
        return engine.search(query, limit)


def _search_social(query: str, limit: int, platform: Optional[str]) -> List[SearchResult]:
    """Search social media"""
    if platform:
        # Use specific social platform
        engine = get_social_engine(platform)
        return engine.search(query, limit)
    else:
        # Search all social platforms
        all_results = []
        for engine in get_all_social_engines():
            try:
                results = engine.search(query, limit)
                all_results.extend(results)
            except EngineError as e:
                print(f"Social engine [{e.engine_name}] failed: {e.message}")
                continue

        return all_results


def search_web(query: str, limit: int = 10) -> List[SearchResult]:
    """Quick web search (convenience function)"""
    return search(query, engines=["search"], limit=limit)


def search_news(query: str, limit: int = 10) -> List[SearchResult]:
    """Quick news search (convenience function)"""
    return search(query, engines=["news"], limit=limit)


def search_social(query: str, limit: int = 10, platform: str = None) -> List[SearchResult]:
    """Quick social search (convenience function)"""
    return search(query, engines=["social"], limit=limit, platform=platform)


def get_latest_news(source: str = None, limit: int = 20) -> List[SearchResult]:
    """
    Get latest news headlines

    Args:
        source: Optional specific news source
        limit: Maximum results

    Returns:
        List of SearchResult objects
    """
    engine = get_news_engine()
    return engine.get_latest(source, limit)


def list_available_engines() -> dict:
    """
    List all available engines and platforms

    Returns:
        Dictionary of engine types and their platforms
    """
    return {
        "search": ["duckduckgo", "google", "bing"],
        "news": list(NewsEngine.RSS_SOURCES.keys()),
        "social": list(SOCIAL_ENGINES.keys()),
    }


# For direct module usage
if __name__ == "__main__":
    # Demo
    print("Testing search API...")

    # Test web search
    print("\n=== Web Search ===")
    results = search_web("Python programming", limit=3)
    for r in results:
        print(f"- {r.title}")

    # Test news search
    print("\n=== News Search ===")
    results = search_news("AI technology", limit=3)
    for r in results:
        print(f"- {r.title}")

    # Test social search
    print("\n=== Social Search (Hacker News) ===")
    results = search_social("startup", limit=3, platform="hackernews")
    for r in results:
        print(f"- {r.title}")