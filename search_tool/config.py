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
    proxy: Optional[str] = "http://127.0.0.1:7890"  # Proxy URL (e.g., "http://127.0.0.1:7890")

    # Playwright settings
    playwright_headless: bool = True
    playwright_timeout: int = 30000  # milliseconds

    # Browser debugging port (for session reuse)
    browser_debug_port: int = 9222

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

        return config


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = Config.load()
    return _config