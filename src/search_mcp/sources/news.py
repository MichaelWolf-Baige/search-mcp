"""News aggregation module."""

from typing import List, Dict, Optional
from .web import search_news


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
RSS_SOURCES = {
    "bbc_world": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "techcrunch": "https://techcrunch.com/feed/",
    "ars_technica": "https://feeds.arstechnica.com/arstechnica/index",
    "hacker_news": "https://hnrss.org/frontpage",
}


async def get_latest_news(source: Optional[str] = None, limit: int = 20) -> List[Dict]:
    """
    Get latest news headlines from RSS sources.

    Args:
        source: Specific RSS source name (optional)
        limit: Maximum number of results

    Returns:
        List of news headlines
    """
    import feedparser
    import aiohttp

    results = []

    if source and source in RSS_SOURCES:
        sources_to_check = {source: RSS_SOURCES[source]}
    else:
        sources_to_check = RSS_SOURCES

    async with aiohttp.ClientSession() as session:
        for src_name, url in sources_to_check.items():
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        continue
                    content = await resp.text()

                feed = feedparser.parse(content)
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

            except Exception:
                continue

    return results[:limit]