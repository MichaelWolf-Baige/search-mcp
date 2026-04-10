"""Search sources module."""

from .web import search_web, search_news
from .news import search_news_articles, get_latest_news, RSS_SOURCES
from .company import search_company
from .academic.arxiv import search_arxiv
from .social.hackernews import search_hackernews
from .social.reddit import search_reddit
from .cn import search_zhihu, search_csdn, search_cnblogs

__all__ = [
    # Web search
    "search_web",
    "search_news",
    # News
    "search_news_articles",
    "get_latest_news",
    "RSS_SOURCES",
    # Company
    "search_company",
    # Academic
    "search_arxiv",
    # Social
    "search_hackernews",
    "search_reddit",
    # Chinese platforms
    "search_zhihu",
    "search_csdn",
    "search_cnblogs",
]