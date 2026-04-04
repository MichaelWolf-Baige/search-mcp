"""Anti-bot utilities for web scraping"""

import random
import time
from typing import Dict, Optional
from functools import wraps

from search_tool.config import get_config


class UserAgentManager:
    """Manage user agent rotation"""

    # Common user agents for different browsers
    USER_AGENTS = [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        # Chrome on Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Firefox on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        # Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        # Safari on Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    ]

    def __init__(self):
        self._index = 0

    def get_random(self) -> str:
        """Get a random user agent"""
        return random.choice(self.USER_AGENTS)

    def get_next(self) -> str:
        """Get next user agent in rotation"""
        ua = self.USER_AGENTS[self._index]
        self._index = (self._index + 1) % len(self.USER_AGENTS)
        return ua


class RequestDelayer:
    """Manage request delays to avoid rate limiting"""

    def __init__(self, min_delay: float = 2.0, max_delay: float = 5.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self._last_request_time = 0

    def wait(self):
        """Wait before next request"""
        current_time = time.time()
        elapsed = current_time - self._last_request_time

        # Random delay
        delay = random.uniform(self.min_delay, self.max_delay)

        # If we've already waited enough, skip
        if elapsed < delay:
            time.sleep(delay - elapsed)

        self._last_request_time = time.time()

    def random_delay(self):
        """Apply random delay regardless of last request"""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)


def get_proxies() -> Optional[Dict[str, str]]:
    """Get proxy configuration from config"""
    config = get_config()
    if config.proxy:
        return {
            "http": config.proxy,
            "https": config.proxy,
        }
    return None


def get_common_headers() -> Dict[str, str]:
    """Get common browser headers"""
    ua_manager = UserAgentManager()
    return {
        "User-Agent": ua_manager.get_random(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


def get_playwright_headers() -> Dict[str, str]:
    """Get headers for Playwright browser context"""
    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }


def configure_playwright_stealth(page):
    """
    Configure Playwright page to hide automation features

    This applies stealth-like configurations to avoid detection
    """
    # Override navigator.webdriver
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)

    # Override navigator.plugins (fake plugin info)
    page.add_init_script("""
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                { name: 'Chrome PDF Viewer', filename: 'mhjjbmdhignlpnnpobgbnpjmnphgaeb' },
                { name: 'Native Client', filename: 'internal-nacl-plugin' }
            ]
        });
    """)

    # Override navigator.languages
    page.add_init_script("""
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en']
        });
    """)

    # Override WebGL vendor
    page.add_init_script("""
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) return 'Intel Inc.';
            if (parameter === 37446) return 'Intel Iris OpenGL Engine';
            return getParameter.call(this, parameter);
        };
    """)

    # Override Chrome detection
    page.add_init_script("""
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
    """)


def with_delay(min_delay: float = 2.0, max_delay: float = 5.0):
    """Decorator to add delay to function calls"""
    delayer = RequestDelayer(min_delay, max_delay)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delayer.wait()
            return func(*args, **kwargs)
        return wrapper

    return decorator