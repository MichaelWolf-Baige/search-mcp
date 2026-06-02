"""News aggregation module."""

import logging
from typing import List, Dict, Optional, Set
from .web import search_news

logger = logging.getLogger(__name__)

# Valid source names for validation
VALID_SOURCES: Set[str] = set()


def search_news_articles(query: str, limit: int = 10) -> List[Dict]:
    """
    Search news articles.

    Args:
        query: Search query string
        limit: Maximum number of results (0 returns empty list)

    Returns:
        List of news articles
    """
    return search_news(query, limit=limit)


# RSS news sources for get_latest_news
# Note: Some sources may be blocked by certain networks/proxies
RSS_SOURCES = {
    # "bbc_world": "https://feeds.bbci.co.uk/news/world/rss.xml",  # Often blocked/fails
    "techcrunch": "https://techcrunch.com/feed/",
    "ars_technica": "https://feeds.arstechnica.com/arstechnica/index",
    "hacker_news": "https://hnrss.org/frontpage",  # May be slow (~8s response)
}

# Build valid sources set
VALID_SOURCES = set(RSS_SOURCES.keys())


async def get_latest_news(source: Optional[str] = None, limit: int = 20) -> List[Dict]:
    """
    Get latest news headlines from RSS sources.

    Args:
        source: Specific RSS source name. Valid sources: techcrunch, ars_technica, hacker_news.
                If source is invalid, returns error message in results.
        limit: Maximum number of results (1-100)

    Returns:
        List of news headlines, or list with error dict if source is invalid
    """
    import feedparser
    import aiohttp

    # Validate limit
    if limit is None or limit < 1:
        limit = 20
    limit = min(limit, 100)  # Cap at 100

    results = []
    errors = []

    # Validate source if specified
    if source is not None:
        if source not in RSS_SOURCES:
            return [{
                "error": f"Invalid source '{source}'. Valid sources: {', '.join(sorted(VALID_SOURCES))}",
                "valid_sources": sorted(VALID_SOURCES)
            }]
        sources_to_check = {source: RSS_SOURCES[source]}
    else:
        sources_to_check = RSS_SOURCES

    async with aiohttp.ClientSession() as session:
        for src_name, url in sources_to_check.items():
            try:
                # Increase timeout for known slow sources
                timeout = 15 if src_name == "hacker_news" else 10
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                    if resp.status != 200:
                        errors.append(f"{src_name}: HTTP {resp.status}")
                        continue
                    content = await resp.text()

                feed = feedparser.parse(content)
                if not feed.entries:
                    errors.append(f"{src_name}: No entries in feed")
                    continue

                for entry in feed.entries[:limit]:
                    results.append({
                        "title": entry.get("title", ""),
                        "url": entry.get("link", ""),
                        "snippet": entry.get("summary", "")[:200] if entry.get("summary") else "",
                        "source": src_name,
                        "published": entry.get("published", ""),
                    })

                if len(results) >= limit:
                    break

            except Exception as e:
                errors.append(f"{src_name}: {str(e)[:50]}")
                logger.warning(f"RSS fetch error for {src_name}: {e}")
                continue

    # If no results and had errors, include error info
    if not results and errors:
        results.append({
            "error": "Failed to fetch from all sources",
            "details": errors
        })

    return results[:limit]