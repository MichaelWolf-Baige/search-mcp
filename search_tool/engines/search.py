"""DuckDuckGo search engine implementation"""

from typing import List

from ddgs import DDGS

from search_tool.engines.base import BaseEngine, SearchResult, EngineError
from search_tool.utils.antibot import RequestDelayer


class DuckDuckGoEngine(BaseEngine):
    """DuckDuckGo search engine - free, no API required"""

    name = "duckduckgo"
    source_type = "search"

    def __init__(self):
        self._delayer = RequestDelayer(min_delay=1.0, max_delay=3.0)

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """
        Search DuckDuckGo for given query

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        results = []

        try:
            # Add delay to avoid rate limiting
            self._delayer.wait()

            with DDGS() as ddgs:
                # Use text search
                search_results = list(ddgs.text(query, max_results=limit))

                if not search_results:
                    return results

                for r in search_results:
                    result = SearchResult(
                        title=r.get("title", ""),
                        url=r.get("href", ""),
                        snippet=r.get("body", ""),
                        source=self.source_type,
                        platform=self.name,
                    )
                    results.append(result)

        except Exception as e:
            raise EngineError(self.name, f"Search failed: {str(e)}")

        return results

    def is_available(self) -> bool:
        """DuckDuckGo is always available (no API key required)"""
        return True


class GoogleEngine(BaseEngine):
    """
    Google search engine (via DuckDuckGo as fallback)

    Note: Direct Google scraping is difficult due to anti-bot measures.
    This implementation uses DuckDuckGo results as a fallback.
    """

    name = "google"
    source_type = "search"

    def __init__(self):
        self._ddg = DuckDuckGoEngine()

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """
        Search using DuckDuckGo (Google fallback)

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        # Use DuckDuckGo as fallback
        results = self._ddg.search(query, limit)

        # Mark as Google source (for display purposes)
        for r in results:
            r.platform = self.name

        return results

    def is_available(self) -> bool:
        """Available via DuckDuckGo fallback"""
        return True


class BingEngine(BaseEngine):
    """
    Bing search engine (via DuckDuckGo as fallback)

    Note: DuckDuckGo uses Bing as one of its sources.
    """

    name = "bing"
    source_type = "search"

    def __init__(self):
        self._ddg = DuckDuckGoEngine()

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """
        Search using DuckDuckGo (Bing fallback)

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        results = self._ddg.search(query, limit)

        # Mark as Bing source
        for r in results:
            r.platform = self.name

        return results

    def is_available(self) -> bool:
        """Available via DuckDuckGo fallback"""
        return True


# Default search engine
DEFAULT_ENGINE = DuckDuckGoEngine()


def get_search_engine(name: str = "duckduckgo") -> BaseEngine:
    """
    Get search engine by name

    Args:
        name: Engine name (duckduckgo/google/bing)

    Returns:
        Search engine instance
    """
    engines = {
        "duckduckgo": DuckDuckGoEngine,
        "google": GoogleEngine,
        "bing": BingEngine,
    }

    engine_class = engines.get(name, DuckDuckGoEngine)
    return engine_class()