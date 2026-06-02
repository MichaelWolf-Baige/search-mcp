"""News engine - RSS feeds and news article extraction"""

import feedparser
from typing import List, Dict, Any
from datetime import datetime

from search_tool.engines.base import BaseEngine, SearchResult, EngineError
from search_tool.utils.antibot import RequestDelayer, get_common_headers, get_proxies, get_session
from search_tool.config import get_config

import requests
from bs4 import BeautifulSoup


class NewsEngine(BaseEngine):
    """
    News aggregation engine

    Supports:
    - RSS/Atom feed parsing
    - News article extraction
    """

    name = "news"
    source_type = "news"

    # Predefined RSS sources
    RSS_SOURCES: Dict[str, str] = {
        # International tech news - working sources
        "hacker_news": "https://hnrss.org/frontpage",
        "techcrunch": "https://techcrunch.com/feed/",
        "ars_technica": "https://feeds.arstechnica.com/arstechnica/index",
        "wired": "https://www.wired.com/feed/rss",

        # More tech sources
        "the_verge": "https://www.theverge.com/rss/index.xml",
        "engadget": "https://www.engadget.com/rss.xml",

        # Note: BBC and Reuters feeds have connectivity/SSL issues with some proxies
        # "bbc_world": "https://feeds.bbci.co.uk/news/world/rss.xml",
        # "bbc_tech": "https://feeds.bbci.co.uk/news/technology/rss.xml",
        # "reuters_world": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",

        # Chinese news sources (may require China IP or no proxy)
        # "36kr": "https://36kr.com/feed",
        # "ifeng": "https://news.ifeng.com/rss/index.xml",
        # "zhihu_daily": "https://www.zhihu.com/rss",
    }

    def __init__(self):
        self._delayer = RequestDelayer(min_delay=2.0, max_delay=5.0)
        self.config = get_config()

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """
        Search news sources for given query

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        results = []

        # Fetch from multiple RSS sources
        all_articles = self._fetch_all_rss()

        # Multi-keyword matching (supports space-separated keywords)
        keywords = [kw.strip().lower() for kw in query.split() if kw.strip()]
        matched = []

        # If no keywords (empty query), return all articles without filtering
        if not keywords:
            matched = all_articles[:limit]
        else:
            for article in all_articles:
                title = article.get("title", "").lower()
                summary = article.get("summary", "").lower()
                content = title + " " + summary

                # Match if ANY keyword is found (OR logic)
                if any(kw in content for kw in keywords):
                    matched.append(article)

            # Limit results
            matched = matched[:limit]

        # Convert to SearchResult
        for article in matched:
            result = SearchResult(
                title=article.get("title", ""),
                url=article.get("link", ""),
                snippet=article.get("summary", "")[:300],
                source=self.source_type,
                platform=article.get("source", "rss"),
                timestamp=article.get("published"),
            )
            results.append(result)

        return results

    def search_source(self, source: str, limit: int = 10) -> List[SearchResult]:
        """
        Get news from specific RSS source

        Args:
            source: RSS source name (e.g., "bbc_world")
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        results = []

        rss_url = self.RSS_SOURCES.get(source)
        if not rss_url:
            raise EngineError(self.name, f"Unknown source: {source}")

        articles = self._parse_rss(rss_url, source)

        for article in articles[:limit]:
            result = SearchResult(
                title=article.get("title", ""),
                url=article.get("link", ""),
                snippet=article.get("summary", "")[:300],
                source=self.source_type,
                platform=source,
                timestamp=article.get("published"),
            )
            results.append(result)

        return results

    def _fetch_all_rss(self) -> List[Dict[str, Any]]:
        """Fetch articles from all RSS sources"""
        all_articles = []

        for source_name, rss_url in self.RSS_SOURCES.items():
            try:
                self._delayer.wait()
                articles = self._parse_rss(rss_url, source_name)
                all_articles.extend(articles)
            except Exception as e:
                # Skip failed sources
                print(f"Failed to fetch {source_name}: {e}")
                continue

        return all_articles

    def _parse_rss(self, url: str, source_name: str) -> List[Dict[str, Any]]:
        """
        Parse RSS/Atom feed

        Args:
            url: RSS feed URL
            source_name: Source identifier

        Returns:
            List of article dictionaries
        """
        articles = []

        try:
            headers = get_common_headers()
            session = get_session()
            response = session.get(
                url,
                headers=headers,
                timeout=self.config.request_timeout,
            )
            response.raise_for_status()

            feed = feedparser.parse(response.content)

            for entry in feed.entries:
                article = {
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", entry.get("description", "")),
                    "published": entry.get("published", entry.get("updated", "")),
                    "source": source_name,
                }
                articles.append(article)

        except Exception as e:
            raise EngineError(self.name, f"RSS parse error for {url}: {str(e)}")

        return articles

    def get_latest(self, source: str = None, limit: int = 20) -> List[SearchResult]:
        """
        Get latest news (no query, just recent articles)

        Args:
            source: Optional specific source name
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        if source:
            return self.search_source(source, limit)

        # Get from all sources
        all_articles = self._fetch_all_rss()
        all_articles = all_articles[:limit]

        results = []
        for article in all_articles:
            result = SearchResult(
                title=article.get("title", ""),
                url=article.get("link", ""),
                snippet=article.get("summary", "")[:300],
                source=self.source_type,
                platform=article.get("source", "rss"),
                timestamp=article.get("published"),
            )
            results.append(result)

        return results

    def is_available(self) -> bool:
        """News engine is always available"""
        return True


class WebNewsScraper(BaseEngine):
    """
    Scrapes news from specific news websites
    Uses BeautifulSoup for static pages
    """

    name = "web_news"
    source_type = "news"

    def __init__(self):
        self._delayer = RequestDelayer(min_delay=3.0, max_delay=6.0)
        self.config = get_config()

    def scrape_site(self, url: str, platform: str = "web") -> List[SearchResult]:
        """
        Scrape news articles from a specific URL

        Args:
            url: Website URL to scrape
            platform: Platform name for results

        Returns:
            List of SearchResult objects
        """
        results = []

        try:
            self._delayer.wait()

            headers = get_common_headers()
            session = get_session()
            response = session.get(
                url,
                headers=headers,
                timeout=self.config.request_timeout,
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "lxml")

            # Common article patterns
            articles = soup.find_all("article") or soup.find_all(class_="article")

            for article in articles[:10]:
                # Try to extract title
                title_elem = (
                    article.find("h1") or
                    article.find("h2") or
                    article.find("h3") or
                    article.find(class_="title")
                )

                # Try to extract link
                link_elem = article.find("a")

                # Try to extract summary
                summary_elem = (
                    article.find("p") or
                    article.find(class_="summary") or
                    article.find(class_="description")
                )

                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    link = link_elem.get("href", "")

                    # Handle relative URLs
                    if link.startswith("/"):
                        from urllib.parse import urljoin
                        link = urljoin(url, link)

                    summary = summary_elem.get_text(strip=True) if summary_elem else ""

                    result = SearchResult(
                        title=title,
                        url=link,
                        snippet=summary[:300],
                        source=self.source_type,
                        platform=platform,
                    )
                    results.append(result)

        except Exception as e:
            raise EngineError(self.name, f"Scrape error: {str(e)}")

        return results

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """
        Not implemented for web scraper - use scrape_site instead
        """
        return []

    def is_available(self) -> bool:
        """Web scraper is available"""
        return True


# Default news engine
DEFAULT_ENGINE = NewsEngine()


def get_news_engine() -> NewsEngine:
    """Get default news engine"""
    return DEFAULT_ENGINE