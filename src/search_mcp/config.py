"""Configuration management."""

from dataclasses import dataclass, field
from typing import Optional
import os


@dataclass
class Config:
    """Global configuration."""

    # Request settings
    request_timeout: int = 30

    # Proxy settings
    proxy: Optional[str] = None

    # Cache settings
    cache_enabled: bool = True
    cache_ttl: int = 300

    # Deep Research API settings
    anthropic_api_key: Optional[str] = None
    anthropic_base_url: Optional[str] = None
    anthropic_model: str = "claude-3-haiku-20240307"

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from environment."""
        config = cls()

        # Load proxy
        config.proxy = os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY")

        # Load API settings
        config.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        config.anthropic_base_url = os.environ.get("ANTHROPIC_BASE_URL")
        if os.environ.get("ANTHROPIC_MODEL"):
            config.anthropic_model = os.environ.get("ANTHROPIC_MODEL")

        return config


_config: Optional[Config] = None


def get_config() -> Config:
    """Get global config instance."""
    global _config
    if _config is None:
        _config = Config.load()
    return _config