"""CNBlogs search."""

from typing import List, Dict


def search_cnblogs(query: str, limit: int = 10) -> List[Dict]:
    """
    Search CNBlogs (博客园) for technical content.

    Args:
        query: Search query string
        limit: Maximum number of results (0 returns empty list)

    Returns:
        List of blog post dictionaries
    """
    if limit <= 0:
        return []

    from ..web import search_web
    # Use DuckDuckGo to search CNBlogs content
    cnblogs_query = f"{query} site:cnblogs.com"
    return search_web(cnblogs_query, limit=limit)