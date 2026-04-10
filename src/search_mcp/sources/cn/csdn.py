"""CSDN search."""

from typing import List, Dict


def search_csdn(query: str, limit: int = 10) -> List[Dict]:
    """
    Search CSDN for technical blog content.

    Args:
        query: Search query string
        limit: Maximum number of results (0 returns empty list)

    Returns:
        List of blog post dictionaries
    """
    if limit <= 0:
        return []

    from ..web import search_web
    # Use DuckDuckGo to search CSDN content
    csdn_query = f"{query} site:csdn.net"
    return search_web(csdn_query, limit=limit)