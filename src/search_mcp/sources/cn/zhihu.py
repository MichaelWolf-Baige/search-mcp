"""Zhihu search."""

import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def _get_proxy() -> str:
    """Get proxy setting from environment."""
    return os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or None


def search_zhihu(query: str, limit: int = 10) -> List[Dict]:
    """
    Search Zhihu for Q&A content.

    Args:
        query: Search query string
        limit: Maximum number of results (0 returns empty list)

    Returns:
        List of answer/question dictionaries
    """
    if limit <= 0:
        return []

    from ..web import search_web
    # Use DuckDuckGo to search Zhihu content
    zhihu_query = f"{query} site:zhihu.com"
    return search_web(zhihu_query, limit=limit)