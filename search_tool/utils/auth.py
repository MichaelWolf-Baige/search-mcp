"""Authentication utilities - Cookie management and session reuse"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from search_tool.config import get_config


class CookieManager:
    """Manage cookies for authenticated access"""

    def __init__(self):
        self.config = get_config()
        self.cookies_dir = self.config.cookies_dir

    def load_cookies(self, site: str) -> List[Dict[str, Any]]:
        """
        Load cookies for a specific site from file

        Args:
            site: Site name (e.g., "weibo", "zhihu")

        Returns:
            List of cookie dictionaries
        """
        cookie_file = self.cookies_dir / f"{site}.json"

        if not cookie_file.exists():
            return []

        try:
            content = cookie_file.read_text(encoding="utf-8")
            cookies = json.loads(content)
            return cookies if isinstance(cookies, list) else []
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading cookies for {site}: {e}")
            return []

    def save_cookies(self, site: str, cookies: List[Dict[str, Any]]) -> bool:
        """
        Save cookies for a site to file

        Args:
            site: Site name
            cookies: List of cookie dictionaries

        Returns:
            True if saved successfully
        """
        # Ensure directory exists
        self.cookies_dir.mkdir(parents=True, exist_ok=True)

        cookie_file = self.cookies_dir / f"{site}.json"

        try:
            content = json.dumps(cookies, indent=2, ensure_ascii=False)
            cookie_file.write_text(content, encoding="utf-8")
            return True
        except IOError as e:
            print(f"Error saving cookies for {site}: {e}")
            return False

    def inject_cookies_to_playwright(self, context, site: str):
        """
        Inject cookies into Playwright browser context

        Args:
            context: Playwright browser context
            site: Site name to load cookies for
        """
        cookies = self.load_cookies(site)

        if cookies:
            context.add_cookies(cookies)
            print(f"Injected {len(cookies)} cookies for {site}")

    def extract_cookies_from_playwright(self, context, site: str) -> bool:
        """
        Extract and save cookies from Playwright browser context

        Args:
            context: Playwright browser context
            site: Site name to save cookies for

        Returns:
            True if cookies were saved
        """
        cookies = context.cookies()

        # Filter cookies for the site domain
        # Convert to simpler format
        simplified_cookies = []
        for cookie in cookies:
            simplified_cookies.append({
                "name": cookie.get("name"),
                "value": cookie.get("value"),
                "domain": cookie.get("domain"),
                "path": cookie.get("path", "/"),
                "expires": cookie.get("expires"),
                "httpOnly": cookie.get("httpOnly", False),
                "secure": cookie.get("secure", False),
                "sameSite": cookie.get("sameSite", "Lax"),
            })

        return self.save_cookies(site, simplified_cookies)

    def has_cookies(self, site: str) -> bool:
        """Check if cookies exist for a site"""
        cookie_file = self.cookies_dir / f"{site}.json"
        return cookie_file.exists() and len(self.load_cookies(site)) > 0


class SessionManager:
    """Manage browser session reuse via CDP"""

    def __init__(self):
        self.config = get_config()
        self.debug_port = self.config.browser_debug_port

    def is_debug_browser_running(self) -> bool:
        """Check if a browser with debug port is running"""
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            result = sock.connect_ex(("localhost", self.debug_port))
            return result == 0
        except Exception:
            return False
        finally:
            sock.close()

    def connect_to_debug_browser(self, playwright):
        """
        Connect to existing browser with debug port

        Args:
            playwright: Playwright instance

        Returns:
            Browser object or None if connection failed
        """
        if not self.is_debug_browser_running():
            return None

        try:
            browser = playwright.chromium.connect_over_cdp(
                f"http://localhost:{self.debug_port}"
            )
            return browser
        except Exception as e:
            print(f"Failed to connect to debug browser: {e}")
            return None

    def get_or_create_context(self, browser) -> Any:
        """
        Get existing context or create new one

        Args:
            browser: Playwright browser instance

        Returns:
            Browser context
        """
        # Use existing context if available (has login state)
        if browser.contexts:
            return browser.contexts[0]

        # Create new context
        return browser.new_context()


def setup_authenticated_browser(playwright, site: str) -> tuple:
    """
    Setup browser with authentication for a site

    Args:
        playwright: Playwright instance
        site: Site name to load cookies for

    Returns:
        (browser, context, page) tuple
    """
    config = get_config()
    cookie_manager = CookieManager()
    session_manager = SessionManager()

    # Try to connect to existing debug browser first
    browser = session_manager.connect_to_debug_browser(playwright)

    if browser:
        # Use existing browser with login state
        context = session_manager.get_or_create_context(browser)
        page = context.new_page()
        return browser, context, page

    # Create new browser
    browser = playwright.chromium.launch(
        headless=config.playwright_headless,
        timeout=config.playwright_timeout,
        proxy={"server": config.proxy} if config.proxy else None,
    )

    context = browser.new_context()

    # Inject cookies if available
    cookie_manager.inject_cookies_to_playwright(context, site)

    page = context.new_page()
    return browser, context, page


def export_cookies_help():
    """Print help message for exporting cookies"""
    help_text = """
========================================
How to Export Cookies from Chrome
========================================

1. Open Chrome and login to the target website (e.g., weibo.com)

2. Press F12 to open Developer Tools

3. Go to Application (application) tab

4. Expand Cookies on the left sidebar

5. Click on the target domain

6. Select all cookies and copy them

7. Create a JSON file in cookies/ directory:
   D:\\search\\cookies\\weibo.json

8. Format the JSON file as follows:
   [
     {"name": "SUB", "value": "_2AkMj...", "domain": ".weibo.com", "path": "/"},
     {"name": "SUBP", "value": "001...", "domain": ".weibo.com", "path": "/"}
   ]

========================================
Alternative: Use Browser Debug Mode
========================================

1. Close all Chrome windows

2. Start Chrome in debug mode:
   chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\\chrome-debug-profile"

3. Login to websites in this Chrome instance

4. The tool will automatically connect to this browser
   and reuse your login state.

========================================
"""
    print(help_text)