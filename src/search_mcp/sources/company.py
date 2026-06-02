"""Company dynamics search - supports any company."""

from typing import List, Dict
from .web import search_news


def search_company(company: str, days: int = 7, limit: int = 10) -> List[Dict]:
    """
    Search news and updates about any company.

    Args:
        company: Company name (any company, supports Chinese and English names)
                 e.g., "华为", "OpenAI", "字节跳动", "Apple", "腾讯", "阿里"
        days: Number of days to look back (1-365, default 7)
        limit: Maximum number of results (1-50)

    Returns:
        List of news articles about the company

    Raises:
        ValueError: If days < 1 or limit < 1
    """
    # Validate parameters
    if days is None or days < 1:
        return []
    if limit is None or limit < 1:
        return []

    # Clamp values
    days = min(max(days, 1), 365)  # 1-365 days
    limit = min(max(limit, 1), 50)  # 1-50 results

    # Add "news" keyword for better results
    query = f"{company} news announcement"
    results = search_news(query, limit=limit)

    # Add company name to each result for context
    for r in results:
        r["company"] = company

    return results