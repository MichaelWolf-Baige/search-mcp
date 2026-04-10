"""Source health checking."""

import asyncio
import time
import os
import aiohttp
from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum


class HealthStatus(Enum):
    """Health status enum."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class SourceHealth:
    """Source health status."""
    name: str
    status: HealthStatus
    last_check: float
    response_time: float
    error_message: Optional[str] = None


# RSS sources to check
RSS_SOURCES = {
    "bbc_world": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "techcrunch": "https://techcrunch.com/feed/",
    "hacker_news": "https://hnrss.org/frontpage",
}


class HealthChecker:
    """Source health checker."""

    def __init__(self, timeout: int = 10, degraded_threshold: float = 2000):
        self.timeout = timeout
        self.degraded_threshold = degraded_threshold
        self._health_status: Dict[str, SourceHealth] = {}
        self._last_check_time: float = 0

    async def check_all(self) -> Dict[str, SourceHealth]:
        """Check all sources asynchronously."""
        results = {}

        # Check RSS sources
        tasks = []
        names = []
        for name, url in RSS_SOURCES.items():
            tasks.append(self._check_url(name, url))
            names.append(name)

        rss_results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, name in enumerate(names):
            if isinstance(rss_results[i], SourceHealth):
                results[name] = rss_results[i]
            else:
                results[name] = SourceHealth(
                    name=name, status=HealthStatus.UNHEALTHY,
                    last_check=time.time(), response_time=0,
                    error_message=str(rss_results[i])
                )

        # Check social APIs
        social_tasks = [
            self._check_url("hackernews", "https://hn.algolia.com/api/v1/search?query=test"),
            self._check_url("reddit", "https://www.reddit.com/.json"),
        ]
        social_results = await asyncio.gather(*social_tasks, return_exceptions=True)

        for i, name in enumerate(["hackernews", "reddit"]):
            if isinstance(social_results[i], SourceHealth):
                results[name] = social_results[i]
            else:
                results[name] = SourceHealth(
                    name=name, status=HealthStatus.UNHEALTHY,
                    last_check=time.time(), response_time=0,
                    error_message=str(social_results[i])
                )

        self._health_status = results
        self._last_check_time = time.time()
        return results

    async def _check_url(self, name: str, url: str) -> SourceHealth:
        """Check URL availability."""
        start = time.time()
        proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            kwargs = {"timeout": timeout}
            if proxy:
                kwargs["proxy"] = proxy

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, **kwargs) as resp:
                    elapsed = (time.time() - start) * 1000

                    if resp.status == 200:
                        if elapsed < self.degraded_threshold:
                            status = HealthStatus.HEALTHY
                            error_msg = None
                        else:
                            status = HealthStatus.DEGRADED
                            error_msg = f"Slow response: {elapsed:.0f}ms"
                    else:
                        status = HealthStatus.UNHEALTHY
                        error_msg = f"Status: {resp.status}"

                    return SourceHealth(
                        name=name, status=status,
                        last_check=time.time(), response_time=elapsed,
                        error_message=error_msg
                    )

        except asyncio.TimeoutError:
            return SourceHealth(
                name=name, status=HealthStatus.UNHEALTHY,
                last_check=time.time(), response_time=self.timeout * 1000,
                error_message="Timeout"
            )
        except Exception as e:
            return SourceHealth(
                name=name, status=HealthStatus.UNHEALTHY,
                last_check=time.time(), response_time=0,
                error_message=str(e)[:100]
            )

    def get_status(self, source_name: str) -> HealthStatus:
        """Get status for a source."""
        health = self._health_status.get(source_name)
        return health.status if health else HealthStatus.UNKNOWN

    def should_skip(self, source_name: str) -> bool:
        """Check if source should be skipped."""
        return self.get_status(source_name) == HealthStatus.UNHEALTHY

    def get_summary(self) -> Dict[str, Any]:
        """Get health summary."""
        healthy = sum(1 for h in self._health_status.values() if h.status == HealthStatus.HEALTHY)
        degraded = sum(1 for h in self._health_status.values() if h.status == HealthStatus.DEGRADED)
        unhealthy = sum(1 for h in self._health_status.values() if h.status == HealthStatus.UNHEALTHY)

        return {
            "healthy": healthy, "degraded": degraded, "unhealthy": unhealthy,
            "total": len(self._health_status), "last_check": self._last_check_time
        }


# Global instance
_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get global health checker instance."""
    global _checker
    if _checker is None:
        _checker = HealthChecker()
    return _checker