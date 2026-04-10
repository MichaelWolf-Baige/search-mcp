"""arXiv academic paper search."""

import arxiv
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


async def search_arxiv(
    query: str,
    max_results: int = 10,
    categories: Optional[List[str]] = None,
) -> List[Dict]:
    """
    Search arXiv for academic papers.

    Args:
        query: Search query string
        max_results: Maximum number of results (0 returns empty list)
        categories: Optional arXiv categories filter (e.g., ['cs.AI', 'cs.LG'])

    Returns:
        List of paper dictionaries with title, authors, abstract, url, published
    """
    if max_results <= 0:
        return []

    try:
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,
        )

        results = []
        for result in search.results():
            paper = {
                "title": result.title,
                "authors": [a.name for a in result.authors],
                "abstract": result.summary.replace("\n", " ").strip()[:500],
                "url": result.entry_id,
                "pdf_url": result.pdf_url,
                "published": result.published.strftime("%Y-%m-%d"),
                "categories": list(result.categories) if result.categories else [],
            }
            results.append(paper)

        return results

    except arxiv.HTTPError as e:
        if e.status == 429:
            logger.warning("arXiv rate limit exceeded, try again later")
        else:
            logger.error(f"arXiv HTTP error: {e}")
        return []
    except Exception as e:
        logger.error(f"arXiv search error: {e}")
        return []