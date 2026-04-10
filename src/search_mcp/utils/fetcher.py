"""Web content fetcher and extractor."""

import re
import os
import logging
from typing import Optional
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def _get_proxy() -> Optional[str]:
    """Get proxy setting from environment."""
    return os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")


def fetch_content(
    url: str,
    max_length: int = 8000,
    start_index: int = 0,
    timeout: int = 30
) -> str:
    """
    Fetch and extract main content from a webpage.

    Args:
        url: URL to fetch
        max_length: Maximum characters to return
        start_index: Character offset for pagination
        timeout: Request timeout in seconds

    Returns:
        Clean text content
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

        # Add Referer for Chinese sites
        if "csdn.net" in url:
            headers["Referer"] = "https://www.csdn.net/"
        elif "cnblogs.com" in url:
            headers["Referer"] = "https://www.cnblogs.com/"
        elif "zhihu.com" in url:
            headers["Referer"] = "https://www.zhihu.com/"

        proxy = _get_proxy()
        proxies = {"http": proxy, "https": proxy} if proxy else None

        response = requests.get(
            url,
            headers=headers,
            proxies=proxies,
            timeout=timeout,
            allow_redirects=True,
        )

        if response.status_code == 403:
            return f"Error: Access denied (403 Forbidden). The site may have anti-bot protection. URL: {url}"

        response.raise_for_status()
        html_content = response.text

        # Try multiple parsers
        parsers = ["lxml", "html.parser"]
        soup = None
        for parser in parsers:
            try:
                soup = BeautifulSoup(html_content, parser)
                if soup.find("body"):
                    break
            except Exception:
                continue

        if not soup:
            soup = BeautifulSoup(html_content, "html.parser")

        # Remove unwanted elements
        for elem in soup.find_all(["script", "style", "nav", "header", "footer", "aside", "iframe", "form", "noscript"]):
            elem.decompose()

        # Remove ads and navigation
        for elem in soup.find_all(class_=re.compile(r"ad|advertisement|sidebar|nav|header|footer|comment|social|share|related|popup|modal|cookie", re.I)):
            elem.decompose()

        # Remove hidden elements
        for elem in soup.find_all(style=re.compile(r"display:\s*none|visibility:\s*hidden", re.I)):
            elem.decompose()

        # Site-specific content selectors
        content_elem = None

        # CSDN
        if "csdn.net" in url:
            content_elem = (
                soup.find("article") or
                soup.find(id="article-content") or
                soup.find(class_="article-content") or
                soup.find(class_="markdown_views") or
                soup.find(class_="htmledit_views")
            )

        # CNBlogs
        elif "cnblogs.com" in url:
            content_elem = (
                soup.find(id="cnblogs_post_body") or
                soup.find(class_="postBody") or
                soup.find("article") or
                soup.find(class_="blogpost-body")
            )

        # Zhihu
        elif "zhihu.com" in url:
            content_elem = (
                soup.find(class_="RichContent-inner") or
                soup.find(class_="Post-RichText") or
                soup.find(class_="RichText") or
                soup.find("article")
            )

        # arXiv
        elif "arxiv.org" in url:
            content_elem = (
                soup.find(class_="abstract") or
                soup.find(id="abs") or
                soup.find("article")
            )

        # WeChat
        elif "mp.weixin.qq.com" in url:
            content_elem = (
                soup.find(id="js_content") or
                soup.find(class_="rich_media_content") or
                soup.find("article")
            )

        # Generic content extraction
        if not content_elem:
            content_elem = (
                soup.find("article") or
                soup.find("main") or
                soup.find(id="content") or
                soup.find(id="main") or
                soup.find(class_="content") or
                soup.find(class_="main") or
                soup.find(class_="post") or
                soup.find(class_="article") or
                soup.find("body")
            )

        # Extract text
        if content_elem:
            title_elem = soup.find("h1") or soup.find("title") or content_elem.find("h1")
            title = title_elem.get_text(strip=True) if title_elem else ""
            content = content_elem.get_text(separator="\n", strip=True)
            content = re.sub(r"\n\s*\n+", "\n\n", content)
            content = re.sub(r"[ \t]+", " ", content)
            result = f"{title}\n\n{content}"
        else:
            body = soup.find("body")
            if body:
                result = body.get_text(separator="\n", strip=True)
                result = re.sub(r"\n\s*\n+", "\n\n", result)
            else:
                result = soup.get_text(strip=True)

        # Pagination
        total_length = len(result)
        if start_index >= total_length:
            if total_length == 0:
                return f"[Error: No content extracted. URL: {url}]"
            return f"Content exhausted. Total length: {total_length} characters."

        end_index = min(start_index + max_length, total_length)
        result = result[start_index:end_index]

        if end_index < total_length:
            result += f"\n\n---\n[Showing {start_index}-{end_index} of {total_length} chars. Use start_index={end_index} for more.]"

        return result

    except requests.exceptions.Timeout:
        return f"Error: Request timed out. URL: {url}"
    except requests.exceptions.ConnectionError:
        return f"Error: Connection failed. URL: {url}"
    except Exception as e:
        return f"Error: {str(e)}"


async def async_fetch_content(
    url: str,
    max_length: int = 8000,
    start_index: int = 0,
    timeout: int = 30
) -> str:
    """
    Async version of fetch_content using aiohttp.
    """
    import aiohttp

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        proxy = _get_proxy()
        kwargs = {"headers": headers, "timeout": aiohttp.ClientTimeout(total=timeout)}
        if proxy:
            kwargs["proxy"] = proxy

        async with aiohttp.ClientSession() as session:
            async with session.get(url, **kwargs) as resp:
                if resp.status == 403:
                    return f"Error: Access denied (403 Forbidden). URL: {url}"
                if resp.status != 200:
                    return f"Error: HTTP {resp.status}. URL: {url}"
                html_content = await resp.text()

        # Parse and extract (same logic as sync version)
        soup = BeautifulSoup(html_content, "lxml" if "lxml" in str(BeautifulSoup) else "html.parser")

        for elem in soup.find_all(["script", "style", "nav", "header", "footer", "aside"]):
            elem.decompose()

        content_elem = soup.find("article") or soup.find("main") or soup.find("body")
        if content_elem:
            result = content_elem.get_text(separator="\n", strip=True)
        else:
            result = soup.get_text(strip=True)

        result = re.sub(r"\n\s*\n+", "\n\n", result)

        total_length = len(result)
        if start_index >= total_length:
            return f"Content exhausted. Total: {total_length} chars."

        end_index = min(start_index + max_length, total_length)
        result = result[start_index:end_index]

        if end_index < total_length:
            result += f"\n\n---\n[Showing {start_index}-{end_index} of {total_length} chars.]"

        return result

    except aiohttp.ClientError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"