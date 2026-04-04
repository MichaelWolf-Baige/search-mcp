"""Base engine classes for all search engines"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class SearchResult:
    """Unified search result structure"""

    title: str
    url: str
    snippet: str
    source: str  # search/news/social
    platform: str  # duckduckgo/weibo/zhihu/reddit etc.
    timestamp: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "platform": self.platform,
            "timestamp": self.timestamp,
            "extra": self.extra,
        }

    def __str__(self) -> str:
        """Simple string representation"""
        return f"[{self.platform}] {self.title}\n    {self.url}\n    {self.snippet[:100]}..."


class BaseEngine(ABC):
    """Abstract base class for all search engines"""

    name: str = "base"
    source_type: str = "unknown"

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """
        Execute search and return results

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of SearchResult objects
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if engine is available and properly configured

        Returns:
            True if engine can be used, False otherwise
        """
        pass

    def _format_timestamp(self, dt: Optional[datetime]) -> Optional[str]:
        """Format datetime to ISO string"""
        if dt is None:
            return None
        return dt.isoformat()


class EngineError(Exception):
    """Exception raised when engine fails"""

    def __init__(self, engine_name: str, message: str):
        self.engine_name = engine_name
        self.message = message
        super().__init__(f"[{engine_name}] {message}")


class EngineNotAvailableError(EngineError):
    """Exception when engine is not available"""

    def __init__(self, engine_name: str):
        super().__init__(engine_name, "Engine is not available or properly configured")


class RateLimitError(EngineError):
    """Exception when rate limit is hit"""

    def __init__(self, engine_name: str, retry_after: Optional[int] = None):
        message = "Rate limit exceeded"
        if retry_after:
            message += f", retry after {retry_after} seconds"
        super().__init__(engine_name, message)
        self.retry_after = retry_after


class CaptchaError(EngineError):
    """Exception when captcha is detected"""

    def __init__(self, engine_name: str):
        super().__init__(engine_name, "Captcha detected, requires manual intervention")