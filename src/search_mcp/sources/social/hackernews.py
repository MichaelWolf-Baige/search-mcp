"""HackerNews search."""

import os
import aiohttp
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def _get_proxy() -> str:
    """Get proxy setting from environment."""
    return os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or None


async def _fetch_json(session: aiohttp.ClientSession, url: str) -> Dict:
    """Fetch JSON from URL."""
    proxy = _get_proxy()
    kwargs = {"timeout": aiohttp.ClientTimeout(total=15)}
    if proxy:
        kwargs["proxy"] = proxy
    async with session.get(url, **kwargs) as resp:
        if resp.status != 200:
            return {}
        return await resp.json()


async def search_hackernews(
    query: str,
    limit: int = 10,
) -> List[Dict]:
    """
    Search HackerNews for tech news and discussions.

    Args:
        query: Search query string
        limit: Maximum number of results (0 returns empty list)

    Returns:
        List of story dictionaries with title, url, points, author, time
    """
    if limit <= 0:
        return []

    # Use Algolia HN search API
    search_url = f"https://hn.algolia.com/api/v1/search?query={query}&tags=story&hitsPerPage={limit}"

    try:
        async with aiohttp.ClientSession() as session:
            data = await _fetch_json(session, search_url)

            results = []
            for hit in data.get("hits", []):
                story = {
                    "title": hit.get("title", ""),
                    "url": hit.get("url", "") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}",
                    "points": hit.get("points", 0),
                    "author": hit.get("author", ""),
                    "time": hit.get("created_at", ""),
                    "comments": hit.get("num_comments", 0),
                }
                results.append(story)

            return results

    except aiohttp.ClientError as e:
        logger.error(f"HackerNews connection error: {e}")
        return []
    except Exception as e:
        logger.error(f"HackerNews search error: {e}")
        return []