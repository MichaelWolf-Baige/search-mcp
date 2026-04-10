"""Social platform search sources."""

from .hackernews import search_hackernews
from .reddit import search_reddit

__all__ = ["search_hackernews", "search_reddit"]