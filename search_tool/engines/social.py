"""Social media engine - Weibo, Reddit, Hacker News, etc."""

import os
from typing import List, Dict, Any
import time

from search_tool.engines.base import BaseEngine, SearchResult, EngineError, CaptchaError
from search_tool.utils.antibot import (
    RequestDelayer,
    get_common_headers,
    get_proxies,
    get_session,
    configure_playwright_stealth,
)
from search_tool.utils.auth import CookieManager, setup_authenticated_browser
from search_tool.config import get_config

import requests
from bs4 import BeautifulSoup

# 使用 ddgs 库进行 DuckDuckGo 搜索
try:
    from ddgs import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False


def _setup_ddgs_proxy():
    """为 ddgs 库设置代理（通过环境变量）"""
    config = get_config()
    if config.proxy:
        os.environ['HTTP_PROXY'] = config.proxy
        os.environ['HTTPS_PROXY'] = config.proxy


class HackerNewsEngine(BaseEngine):
    """
    Hacker News search engine

    Uses official Hacker News API (no authentication required)
    """

    name = "hackernews"
    source_type = "social"

    BASE_URL = "https://hn.algolia.com/api/v1"

    def __init__(self):
        self._delayer = RequestDelayer(min_delay=1.0, max_delay=2.0)
        self.config = get_config()

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """
        Search Hacker News via Algolia API

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        results = []

        try:
            self._delayer.wait()

            # Use Algolia search API
            url = f"{self.BASE_URL}/search"
            params = {
                "query": query,
                "hitsPerPage": limit,
                "tags": "story",
            }

            session = get_session()
            response = session.get(
                url,
                params=params,
                timeout=self.config.request_timeout,
            )
            response.raise_for_status()

            data = response.json()

            for hit in data.get("hits", []):
                result = SearchResult(
                    title=hit.get("title", ""),
                    url=hit.get("url", "") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}",
                    snippet=hit.get("text", "")[:300] or f"Points: {hit.get('points', 0)}, Comments: {hit.get('num_comments', 0)}",
                    source=self.source_type,
                    platform=self.name,
                    timestamp=self._format_hn_time(hit.get("created_at")),
                    extra={
                        "points": hit.get("points", 0),
                        "comments": hit.get("num_comments", 0),
                        "author": hit.get("author", ""),
                    },
                )
                results.append(result)

        except Exception as e:
            raise EngineError(self.name, f"Search failed: {str(e)}")

        return results

    def _format_hn_time(self, timestamp: str) -> str:
        """Format Hacker News timestamp"""
        if not timestamp:
            return None
        # Already in ISO format usually
        return timestamp[:19] if len(timestamp) > 19 else timestamp

    def is_available(self) -> bool:
        """Hacker News API is always available"""
        return True


class TwitterXEngine(BaseEngine):
    """
    Twitter/X 搜索引擎

    使用 ddgs 库进行 DuckDuckGo 站内搜索
    """

    name = "twitter"
    source_type = "social"

    def __init__(self):
        self._delayer = RequestDelayer(min_delay=1.0, max_delay=2.0)
        self.config = get_config()

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        results = []

        if not HAS_DDGS:
            return results

        try:
            self._delayer.wait()
            _setup_ddgs_proxy()

            with DDGS(timeout=20) as ddgs:
                # 搜索 twitter.com 和 x.com
                search_results = list(ddgs.text(f"{query} site:twitter.com OR site:x.com", max_results=limit))

                for r in search_results:
                    url = r.get("href", "")
                    if "twitter.com" not in url and "x.com" not in url:
                        continue

                    result = SearchResult(
                        title=r.get("title", ""),
                        url=url,
                        snippet=r.get("body", "")[:300],
                        source=self.source_type,
                        platform=self.name,
                    )
                    results.append(result)

        except Exception as e:
            raise EngineError(self.name, f"Search failed: {str(e)}")

        return results

    def is_available(self) -> bool:
        return HAS_DDGS


class RedditEngine(BaseEngine):
    """
    Reddit search engine

    Uses old.reddit.com for easier scraping (no JS required)
    """

    name = "reddit"
    source_type = "social"

    SEARCH_URL = "https://old.reddit.com/search?q={query}&limit={limit}"

    def __init__(self):
        self._delayer = RequestDelayer(min_delay=2.0, max_delay=4.0)
        self.config = get_config()

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """
        Search Reddit via old.reddit.com

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        results = []

        try:
            self._delayer.wait()

            headers = get_common_headers()
            # Add Reddit-specific headers
            headers["Accept"] = "text/html,application/xhtml+xml"

            url = self.SEARCH_URL.format(query=query, limit=limit)

            session = get_session()
            response = session.get(
                url,
                headers=headers,
                timeout=self.config.request_timeout,
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "lxml")

            # Parse search results
            search_results = soup.find_all(class_="search-result")

            for result_elem in search_results[:limit]:
                try:
                    # Extract title
                    title_elem = result_elem.find(class_="search-title")
                    title = title_elem.get_text(strip=True) if title_elem else ""

                    # Extract link
                    link_elem = result_elem.find("a", class_="search-link")
                    link = link_elem.get("href", "") if link_elem else ""

                    # Extract snippet
                    snippet_elem = result_elem.find(class_="search-body")
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                    # Extract metadata
                    meta_elem = result_elem.find(class_="search-meta")
                    meta = meta_elem.get_text(strip=True) if meta_elem else ""

                    result = SearchResult(
                        title=title,
                        url=link,
                        snippet=snippet[:300],
                        source=self.source_type,
                        platform=self.name,
                        timestamp=meta,
                    )
                    results.append(result)

                except Exception:
                    continue

        except Exception as e:
            raise EngineError(self.name, f"Search failed: {str(e)}")

        return results

    def is_available(self) -> bool:
        """Reddit is available via old.reddit.com"""
        return True


class NitterEngine(BaseEngine):
    """
    Twitter/X search via Nitter instances

    Nitter is a Twitter frontend that doesn't require JavaScript
    """

    name = "nitter"
    source_type = "social"

    # Public Nitter instances (updated 2024 - many instances have shut down)
    # Check https://github.com/zedeus/nitter/wiki/Instances for working ones
    NITTER_INSTANCES = [
        "https://nitter.privacydev.net",
        "https://nitter.net",
        "https://nitter.poast.org",
    ]

    def __init__(self):
        self._delayer = RequestDelayer(min_delay=3.0, max_delay=5.0)
        self.config = get_config()
        self._current_instance = 0

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """
        Search Twitter via Nitter

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        results = []

        # Try multiple instances
        for i, instance in enumerate(self.NITTER_INSTANCES):
            if i > 0:
                self._delayer.wait()

            try:
                search_url = f"{instance}/search?f=tweets&q={query}"

                headers = get_common_headers()
                session = get_session()
                response = session.get(
                    search_url,
                    headers=headers,
                    timeout=self.config.request_timeout,
                )
                response.raise_for_status()

                soup = BeautifulSoup(response.content, "lxml")

                # Parse tweets
                tweets = soup.find_all(class_="tweet-content")

                for tweet_elem in tweets[:limit]:
                    try:
                        # Get tweet text
                        text = tweet_elem.get_text(strip=True)

                        # Get tweet link
                        parent = tweet_elem.find_parent(class_="tweet")
                        link_elem = parent.find("a", class_="tweet-link") if parent else None
                        link = link_elem.get("href", "") if link_elem else ""
                        if link:
                            link = instance + link

                        # Get author info
                        author_elem = parent.find(class_="fullname") if parent else None
                        author = author_elem.get_text(strip=True) if author_elem else "Unknown"

                        result = SearchResult(
                            title=f"@{author}: {text[:50]}...",
                            url=link,
                            snippet=text[:300],
                            source=self.source_type,
                            platform="twitter",
                            extra={"author": author, "instance": instance},
                        )
                        results.append(result)

                    except Exception:
                        continue

                if results:
                    break  # Got results, don't try other instances

            except Exception:
                continue  # Try next instance

        return results

    def is_available(self) -> bool:
        """Nitter availability depends on instances"""
        return True


class CnblogsEngine(BaseEngine):
    """
    博客园 (cnblogs.com) 搜索引擎

    使用 ddgs 库进行 DuckDuckGo 站内搜索
    """

    name = "cnblogs"
    source_type = "social"

    def __init__(self):
        self._delayer = RequestDelayer(min_delay=1.0, max_delay=2.0)
        self.config = get_config()

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        results = []

        if not HAS_DDGS:
            return results

        try:
            self._delayer.wait()
            _setup_ddgs_proxy()

            with DDGS(timeout=20) as ddgs:
                search_results = list(ddgs.text(f"{query} site:cnblogs.com", max_results=limit))

                for r in search_results:
                    url = r.get("href", "")
                    if "cnblogs.com" not in url:
                        continue

                    result = SearchResult(
                        title=r.get("title", ""),
                        url=url,
                        snippet=r.get("body", "")[:300],
                        source=self.source_type,
                        platform=self.name,
                    )
                    results.append(result)

        except Exception as e:
            raise EngineError(self.name, f"Search failed: {str(e)}")

        return results

    def is_available(self) -> bool:
        return HAS_DDGS


class CSDNEngine(BaseEngine):
    """
    CSDN (csdn.net) 搜索引擎

    使用 ddgs 库进行 DuckDuckGo 站内搜索
    """

    name = "csdn"
    source_type = "social"

    def __init__(self):
        self._delayer = RequestDelayer(min_delay=1.0, max_delay=2.0)
        self.config = get_config()

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        results = []

        if not HAS_DDGS:
            return results

        try:
            self._delayer.wait()
            _setup_ddgs_proxy()

            with DDGS(timeout=20) as ddgs:
                search_results = list(ddgs.text(f"{query} site:csdn.net", max_results=limit))

                for r in search_results:
                    url = r.get("href", "")
                    if "csdn.net" not in url:
                        continue

                    result = SearchResult(
                        title=r.get("title", ""),
                        url=url,
                        snippet=r.get("body", "")[:300],
                        source=self.source_type,
                        platform=self.name,
                    )
                    results.append(result)

        except Exception as e:
            raise EngineError(self.name, f"Search failed: {str(e)}")

        return results

    def is_available(self) -> bool:
        return HAS_DDGS


class ArxivEngine(BaseEngine):
    """
    arXiv 学术论文搜索引擎

    使用 ddgs 库进行 DuckDuckGo 站内搜索
    """

    name = "arxiv"
    source_type = "social"

    def __init__(self):
        self._delayer = RequestDelayer(min_delay=1.0, max_delay=2.0)
        self.config = get_config()

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        results = []

        if not HAS_DDGS:
            return results

        try:
            self._delayer.wait()
            _setup_ddgs_proxy()

            with DDGS(timeout=20) as ddgs:
                search_results = list(ddgs.text(f"{query} site:arxiv.org", max_results=limit))

                for r in search_results:
                    url = r.get("href", "")
                    if "arxiv.org" not in url:
                        continue

                    result = SearchResult(
                        title=r.get("title", ""),
                        url=url,
                        snippet=r.get("body", "")[:300],
                        source=self.source_type,
                        platform=self.name,
                    )
                    results.append(result)

        except Exception as e:
            raise EngineError(self.name, f"Search failed: {str(e)}")

        return results

    def is_available(self) -> bool:
        return HAS_DDGS


class ZhihuEngine(BaseEngine):
    """
    知乎搜索引擎

    使用 ddgs 库进行 DuckDuckGo 站内搜索
    """

    name = "zhihu"
    source_type = "social"

    def __init__(self):
        self._delayer = RequestDelayer(min_delay=1.0, max_delay=2.0)
        self.config = get_config()

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        results = []

        if not HAS_DDGS:
            return results

        try:
            self._delayer.wait()
            _setup_ddgs_proxy()

            with DDGS(timeout=20) as ddgs:
                search_results = list(ddgs.text(f"{query} site:zhihu.com", max_results=limit))

                for r in search_results:
                    url = r.get("href", "")
                    if "zhihu.com" not in url:
                        continue

                    result = SearchResult(
                        title=r.get("title", ""),
                        url=url,
                        snippet=r.get("body", "")[:300],
                        source=self.source_type,
                        platform=self.name,
                    )
                    results.append(result)

        except Exception as e:
            raise EngineError(self.name, f"Search failed: {str(e)}")

        return results

    def is_available(self) -> bool:
        return HAS_DDGS


# Engine registry
SOCIAL_ENGINES = {
    "hackernews": HackerNewsEngine,
    "twitter": TwitterXEngine,
    "reddit": RedditEngine,
    "nitter": NitterEngine,
    "zhihu": ZhihuEngine,
    "cnblogs": CnblogsEngine,
    "csdn": CSDNEngine,
    "arxiv": ArxivEngine,
}


def get_social_engine(name: str) -> BaseEngine:
    """
    Get social media engine by name

    Args:
        name: Engine name

    Returns:
        Social engine instance
    """
    engine_class = SOCIAL_ENGINES.get(name)
    if not engine_class:
        raise EngineError("social", f"Unknown engine: {name}")

    return engine_class()


def get_all_social_engines() -> List[BaseEngine]:
    """
    Get all available social engines

    Returns:
        List of engine instances
    """
    return [cls() for cls in SOCIAL_ENGINES.values()]