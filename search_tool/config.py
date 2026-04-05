"""Configuration management for search tool"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    """Global configuration for search tool"""

    # Paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    cookies_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "cookies")

    # Request settings
    request_delay_min: float = 2.0  # Minimum delay between requests (seconds)
    request_delay_max: float = 5.0  # Maximum delay between requests (seconds)
    request_timeout: int = 30  # Request timeout (seconds)

    # Proxy settings
    proxy: Optional[str] = None  # Proxy URL, set via HTTP_PROXY/HTTPS_PROXY env var

    # Playwright settings
    playwright_headless: bool = True
    playwright_timeout: int = 30000  # milliseconds

    # Browser debugging port (for session reuse)
    browser_debug_port: int = 9222

    # Cache settings (新增)
    cache_enabled: bool = True
    cache_ttl: int = 300  # Cache TTL in seconds (5 minutes)
    cache_dir: Path = field(default_factory=lambda: Path.home() / ".search_tool_cache")

    # Health check settings (新增)
    health_check_interval: int = 300  # Health check interval in seconds (5 minutes)
    health_timeout: int = 10  # Health check timeout in seconds
    health_degraded_threshold: float = 2000  # Response time threshold for degraded status (ms)

    # Concurrent settings (新增)
    max_concurrent_engines: int = 5  # Max concurrent engine searches
    max_concurrent_rss: int = 6  # Max concurrent RSS fetches

    # Deep Research API settings (新增)
    anthropic_api_key: Optional[str] = None  # API key from ANTHROPIC_API_KEY env var
    anthropic_base_url: Optional[str] = None  # API base URL from ANTHROPIC_BASE_URL env var
    anthropic_model: str = "claude-3-haiku-20240307"  # Model for deep research analysis

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from environment or defaults"""
        import os
        config = cls()

        # Load proxy from environment
        if os.environ.get("HTTP_PROXY"):
            config.proxy = os.environ.get("HTTP_PROXY")
        elif os.environ.get("HTTPS_PROXY"):
            config.proxy = os.environ.get("HTTPS_PROXY")

        # Load API settings from environment
        if os.environ.get("ANTHROPIC_API_KEY"):
            config.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        if os.environ.get("ANTHROPIC_BASE_URL"):
            config.anthropic_base_url = os.environ.get("ANTHROPIC_BASE_URL")
        if os.environ.get("ANTHROPIC_MODEL"):
            config.anthropic_model = os.environ.get("ANTHROPIC_MODEL")

        return config


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = Config.load()
    return _config