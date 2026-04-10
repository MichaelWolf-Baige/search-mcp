"""Test search sources."""

import pytest


def test_web_search():
    """Test web search."""
    from search_mcp.sources import search_web

    results = search_web("Python programming", limit=3)
    assert isinstance(results, list)
    assert len(results) <= 3

    if results:
        assert "title" in results[0]
        assert "url" in results[0]


def test_news_search():
    """Test news search."""
    from search_mcp.sources import search_news

    results = search_news("technology", limit=3)
    assert isinstance(results, list)
    assert len(results) <= 3


@pytest.mark.asyncio
async def test_arxiv_search():
    """Test arXiv search."""
    from search_mcp.sources import search_arxiv

    results = await search_arxiv("machine learning", max_results=3)
    assert isinstance(results, list)
    assert len(results) <= 3

    if results:
        assert "title" in results[0]
        assert "authors" in results[0]


@pytest.mark.asyncio
async def test_hackernews_search():
    """Test HackerNews search."""
    from search_mcp.sources import search_hackernews

    results = await search_hackernews("python", limit=3)
    assert isinstance(results, list)
    assert len(results) <= 3


@pytest.mark.asyncio
async def test_reddit_search():
    """Test Reddit search."""
    from search_mcp.sources import search_reddit

    results = await search_reddit("programming", limit=3)
    assert isinstance(results, list)
    assert len(results) <= 3


def test_cn_search():
    """Test Chinese platform search."""
    from search_mcp.sources import search_zhihu, search_csdn, search_cnblogs

    results = search_zhihu("人工智能", limit=3)
    assert isinstance(results, list)

    results = search_csdn("Python", limit=3)
    assert isinstance(results, list)

    results = search_cnblogs("编程", limit=3)
    assert isinstance(results, list)


def test_company_search():
    """Test company search."""
    from search_mcp.sources import search_company

    results = search_company("OpenAI", days=7, limit=3)
    assert isinstance(results, list)
    assert len(results) <= 3


def test_cache():
    """Test cache module."""
    from search_mcp.utils.cache import get_cache, clear_cache

    cache = get_cache()
    clear_cache()

    # Test set and get
    cache.set("test_engine", "test_query", 10, [{"title": "test"}])
    result = cache.get("test_engine", "test_query", 10)
    assert result is not None
    assert len(result) == 1

    # Test stats
    stats = cache.stats()
    assert "hit_rate" in stats
    assert "total_entries" in stats

    clear_cache()


def test_keywords():
    """Test keyword expansion."""
    from search_mcp.utils.keywords import get_expander

    expander = get_expander()
    suggestion = expander.expand("Python")

    assert suggestion.original == "Python"
    assert len(suggestion.expanded) > 0
    assert isinstance(suggestion.related, list)
    assert isinstance(suggestion.technical_terms, list)


def test_formatter():
    """Test formatter functions."""
    from search_mcp.utils.formatter import (
        format_results, format_arxiv, format_hn,
        format_reddit, format_cn, format_company
    )

    # Test format_results
    results = [{"title": "Test", "url": "https://example.com", "snippet": "Test snippet"}]
    output = format_results(results, "Test")
    assert "Test" in output
    assert "Test" in output

    # Test format_arxiv
    papers = [{"title": "Paper", "url": "https://arxiv.org/abs/123", "authors": ["Author"]}]
    output = format_arxiv(papers)
    assert "arXiv" in output

    # Test format_hn
    stories = [{"title": "Story", "url": "https://news.ycombinator.com", "points": 100, "author": "user"}]
    output = format_hn(stories)
    assert "HackerNews" in output

    # Test format_reddit
    posts = [{"title": "Post", "url": "https://reddit.com", "score": 50, "subreddit": "python"}]
    output = format_reddit(posts)
    assert "Reddit" in output

    # Test format_cn
    output = format_cn(results, "zhihu")
    assert "Zhihu" in output

    # Test format_company
    news = [{"title": "News", "url": "https://example.com", "source": "BBC"}]
    output = format_company(news, "OpenAI")
    assert "OpenAI" in output


@pytest.mark.asyncio
async def test_health_check():
    """Test health checker."""
    from search_mcp.utils.health import get_health_checker

    checker = get_health_checker()
    status = await checker.check_all()

    assert isinstance(status, dict)
    assert len(status) > 0

    summary = checker.get_summary()
    assert "healthy" in summary
    assert "unhealthy" in summary