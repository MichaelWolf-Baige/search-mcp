"""Reddit search."""

import os
import aiohttp
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def _get_proxy() -> str:
    """Get proxy setting from environment."""
    return os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or None


async def search_reddit(
    query: str,
    subreddit: str = "all",
    limit: int = 10,
) -> List[Dict]:
    """
    Search Reddit for discussions.

    Args:
        query: Search query string
        subreddit: Subreddit to search (default 'all')
        limit: Maximum number of results (0 returns empty list)

    Returns:
        List of post dictionaries with title, url, score, author, subreddit
    """
    if limit <= 0:
        return []

    search_url = f"https://www.reddit.com/r/{subreddit}/search.json?q={query}&restrict_sr=1&limit={limit}&sort=relevance"

    headers = {"User-Agent": "search-mcp/1.0.0"}
    proxy = _get_proxy()

    try:
        kwargs = {"headers": headers, "timeout": aiohttp.ClientTimeout(total=15)}
        if proxy:
            kwargs["proxy"] = proxy

        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, **kwargs) as resp:
                if resp.status != 200:
                    logger.warning(f"Reddit API returned status {resp.status}")
                    return []
                data = await resp.json()

            results = []
            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                results.append({
                    "title": post.get("title", ""),
                    "url": post.get("url", ""),
                    "selftext": post.get("selftext", "")[:300] if post.get("selftext") else "",
                    "score": post.get("score", 0),
                    "author": post.get("author", ""),
                    "subreddit": post.get("subreddit", ""),
                    "num_comments": post.get("num_comments", 0),
                    "permalink": f"https://reddit.com{post.get('permalink', '')}",
                })

            return results

    except aiohttp.ClientError as e:
        logger.error(f"Reddit connection error: {e}")
        return []
    except Exception as e:
        logger.error(f"Reddit search error: {e}")
        return []