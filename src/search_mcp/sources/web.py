"""DuckDuckGo web search using ddgs."""

import os
import logging
from ddgs import DDGS
from ddgs.exceptions import DDGSException
from typing import List, Dict

logger = logging.getLogger(__name__)


def _get_proxy() -> str:
    """Get proxy setting from environment."""
    return os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or None


def search_web(query: str, limit: int = 10) -> List[Dict]:
    """
    Search the web using DuckDuckGo.

    Args:
        query: Search query string
        limit: Maximum number of results (1-50, DuckDuckGo API has ~50 result limit)

    Returns:
        List of result dictionaries with title, url, snippet

    Note:
        DuckDuckGo API typically returns maximum ~50 results regardless of limit.
        For limit > 50, results may be fewer than requested.
    """
    # Validate and clamp limit
    if limit is None or limit < 1:
        return []
    limit = min(limit, 50)  # DuckDuckGo API limit

    proxy = _get_proxy()
    try:
        with DDGS(proxy=proxy) as ddgs:
            results = []
            raw = ddgs.text(query, max_results=limit)
            for r in raw or []:
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
            return results
    except DDGSException as e:
        logger.warning(f"DuckDuckGo web search error: {e}")
        return []
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return []


def search_news(query: str, limit: int = 10) -> List[Dict]:
    """
    Search news using DuckDuckGo.

    Args:
        query: Search query string
        limit: Maximum number of results (1-50, DuckDuckGo API has ~50 result limit)

    Returns:
        List of news result dictionaries

    Note:
        DuckDuckGo API typically returns maximum ~50 results regardless of limit.
    """
    # Validate and clamp limit
    if limit is None or limit < 1:
        return []
    limit = min(limit, 50)  # DuckDuckGo API limit

    proxy = _get_proxy()
    try:
        with DDGS(proxy=proxy) as ddgs:
            results = []
            raw = ddgs.news(query, max_results=limit)
            for r in raw or []:
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("body", ""),
                    "source": r.get("source", ""),
                    "date": r.get("date", ""),
                })
            return results
    except DDGSException as e:
        logger.warning(f"DuckDuckGo news search error: {e}")
        return []
    except Exception as e:
        logger.error(f"News search error: {e}")
        return []