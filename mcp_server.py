"""
MCP Server for Search Tool

This module provides an MCP (Model Context Protocol) server that allows
Claude to use the search tool directly via MCP tools.
"""

import asyncio
import sys
import json
import re
from typing import Any

import requests
from bs4 import BeautifulSoup

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Add parent directory to path for imports
sys.path.insert(0, str(__file__).rsplit("\\", 1)[0])

from search_tool.api import (
    search,
    search_web,
    search_news,
    search_social,
    get_latest_news,
    list_available_engines,
)
from search_tool.async_api import async_search
from search_tool.research import deep_research
from search_tool.scoring import get_scorer
from search_tool.keywords import get_expander
from search_tool.utils.formatter import format_results
from search_tool.utils.cache import get_cache, clear_cache
from search_tool.utils.health import get_health_checker
from search_tool.config import get_config


def _fetch_content(url: str, max_length: int = 8000, start_index: int = 0) -> str:
    """
    Fetch and extract main content from a webpage.

    Args:
        url: URL to fetch
        max_length: Maximum characters to return
        start_index: Character offset for pagination

    Returns:
        Clean text content
    """
    config = get_config()

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

        # 添加 Referer
        if "csdn.net" in url:
            headers["Referer"] = "https://www.csdn.net/"
        elif "cnblogs.com" in url:
            headers["Referer"] = "https://www.cnblogs.com/"
        elif "zhihu.com" in url:
            headers["Referer"] = "https://www.zhihu.com/"

        proxies = {"http": config.proxy, "https": config.proxy} if config.proxy else None

        response = requests.get(
            url,
            headers=headers,
            proxies=proxies,
            timeout=config.request_timeout,
            allow_redirects=True,
        )

        if response.status_code == 403:
            return f"Error: Access denied (403 Forbidden). The site may have anti-bot protection. URL: {url}"

        response.raise_for_status()

        soup = BeautifulSoup(response.content, "lxml")

        # 移除不需要的元素
        for elem in soup.find_all(["script", "style", "nav", "header", "footer", "aside", "iframe", "form", "noscript"]):
            elem.decompose()

        # 移除广告和导航元素
        for elem in soup.find_all(class_=re.compile(r"ad|advertisement|sidebar|nav|header|footer|comment|social|share|related|popup|modal|cookie", re.I)):
            elem.decompose()

        # 移除隐藏元素
        for elem in soup.find_all(style=re.compile(r"display:\s*none|visibility:\s*hidden", re.I)):
            elem.decompose()

        # 根据不同网站选择主要内容区域
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

        # 博客园
        elif "cnblogs.com" in url:
            content_elem = (
                soup.find(id="cnblogs_post_body") or
                soup.find(class_="postBody") or
                soup.find("article") or
                soup.find(class_="blogpost-body")
            )

        # 知乎
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

        # 微信公众号
        elif "mp.weixin.qq.com" in url:
            content_elem = (
                soup.find(id="js_content") or
                soup.find(class_="rich_media_content") or
                soup.find("article")
            )

        # 通用内容提取
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

        # 提取文本
        if content_elem:
            # 提取标题
            title_elem = (
                soup.find("h1") or
                soup.find("title") or
                content_elem.find("h1")
            )
            title = title_elem.get_text(strip=True) if title_elem else ""

            # 提取内容
            content = content_elem.get_text(separator="\n", strip=True)

            # 清理内容
            # 移除多余空白行
            content = re.sub(r"\n\s*\n+", "\n\n", content)
            # 移除行内多余空白
            content = re.sub(r"[ \t]+", " ", content)

            # 组合结果
            result = f"{title}\n\n{content}"

        else:
            # 使用整个 body
            body = soup.find("body")
            if body:
                result = body.get_text(separator="\n", strip=True)
                result = re.sub(r"\n\s*\n+", "\n\n", result)
            else:
                result = soup.get_text(strip=True)

        # 分页处理
        total_length = len(result)
        if start_index >= total_length:
            return f"Content exhausted. Total length: {total_length} characters."

        end_index = min(start_index + max_length, total_length)
        result = result[start_index:end_index]

        # 添加分页信息
        if end_index < total_length:
            result += f"\n\n---\n[Content info: Showing characters {start_index}-{end_index} of {total_length} total. Use start_index={end_index} to see more.]"

        return result

    except requests.exceptions.Timeout:
        return f"Error: Request timed out. URL: {url}"
    except requests.exceptions.ConnectionError:
        return f"Error: Connection failed. URL: {url}"
    except Exception as e:
        return f"Error: {str(e)}"


# Create MCP server instance
server = Server("search-tool")


# Define available tools
TOOLS = [
    Tool(
        name="web_search",
        description="""Search the web for information across web, news, and social media.

Use this tool to search for information across web, news, and social media.

Examples:
- web_search("Python tutorial")
- web_search("AI news", engine="news")
- web_search("hot topics", engine="social", limit=5)""",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string"
                },
                "engine": {
                    "type": "string",
                    "enum": ["search", "news", "social", "all"],
                    "default": "search",
                    "description": "Engine type: search (web), news, social, or all"
                },
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum number of results"
                }
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="search_web",
        description="Quick web search using DuckDuckGo",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "default": 10, "description": "Maximum results"}
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="search_news",
        description="Search news sources",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "default": 10, "description": "Maximum results"}
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="search_social",
        description="Search social media platforms (hackernews, reddit, twitter, nitter, zhihu, cnblogs, csdn, arxiv)",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "platform": {
                    "type": "string",
                    "description": "Specific platform (hackernews, reddit, twitter, nitter, zhihu, cnblogs, csdn, arxiv)",
                    "enum": ["hackernews", "reddit", "twitter", "nitter", "zhihu", "cnblogs", "csdn", "arxiv"]
                },
                "limit": {"type": "integer", "default": 10, "description": "Maximum results"}
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="fetch_content",
        description="Fetch and extract main content from a webpage URL. Strips navigation, headers, footers, scripts and styles to return clean readable text.",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to fetch content from"},
                "max_length": {"type": "integer", "default": 8000, "description": "Maximum characters to return"},
                "start_index": {"type": "integer", "default": 0, "description": "Character offset to start reading from (for pagination)"}
            },
            "required": ["url"]
        }
    ),
    Tool(
        name="get_latest_news",
        description="Get latest news headlines from various sources",
        inputSchema={
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Optional news source (bbc_world, hacker_news, etc.)"
                },
                "limit": {"type": "integer", "default": 20, "description": "Maximum results"}
            }
        }
    ),
    Tool(
        name="list_engines",
        description="List all available search engines and platforms",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    # P0 新增工具
    Tool(
        name="check_health",
        description="Check health status of all search sources (RSS feeds, social platforms)",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    Tool(
        name="clear_cache",
        description="Clear the search result cache",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    Tool(
        name="cache_stats",
        description="Get cache statistics (hit rate, entries, etc.)",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    # P1 新增工具
    Tool(
        name="deep_research",
        description="""Perform deep research on a topic by combining multiple search rounds,
content fetching, and AI-powered analysis. Use this for comprehensive research on new domains.

This tool will:
1. Search across multiple engines (web + news)
2. Extract and analyze content from top sources
3. Generate a comprehensive summary using Claude AI
4. Identify key findings and suggest follow-up questions

Requires ANTHROPIC_API_KEY environment variable for AI analysis.""",
        inputSchema={
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Research topic or question"
                },
                "depth": {
                    "type": "string",
                    "enum": ["basic", "standard", "comprehensive"],
                    "default": "standard",
                    "description": "Research depth: basic (1 round), standard (2 rounds), comprehensive (3 rounds)"
                },
                "sources": {
                    "type": "integer",
                    "default": 5,
                    "minimum": 3,
                    "maximum": 15,
                    "description": "Number of sources to analyze per round"
                }
            },
            "required": ["topic"]
        }
    ),
    Tool(
        name="suggest_keywords",
        description="Suggest expanded and related keywords for better search coverage",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Original search query"
                }
            },
            "required": ["query"]
        }
    ),
]


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Return list of available tools"""
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""

    try:
        if name == "web_search":
            query = arguments.get("query")
            engine = arguments.get("engine", "search")
            limit = arguments.get("limit", 10)

            if engine == "all":
                engines = ["search", "news", "social"]
            else:
                engines = [engine]

            results = search(query=query, engines=engines, limit=limit)
            output = format_results(results, query, "mcp")
            return [TextContent(type="text", text=output)]

        elif name == "search_web":
            query = arguments.get("query")
            limit = arguments.get("limit", 10)
            results = search_web(query, limit)
            output = format_results(results, query, "mcp")
            return [TextContent(type="text", text=output)]

        elif name == "search_news":
            query = arguments.get("query")
            limit = arguments.get("limit", 10)
            results = search_news(query, limit)
            output = format_results(results, query, "mcp")
            return [TextContent(type="text", text=output)]

        elif name == "search_social":
            query = arguments.get("query")
            platform = arguments.get("platform")
            limit = arguments.get("limit", 10)
            results = search_social(query, limit, platform)
            output = format_results(results, query, "mcp")
            return [TextContent(type="text", text=output)]

        elif name == "get_latest_news":
            source = arguments.get("source")
            limit = arguments.get("limit", 20)
            results = get_latest_news(source, limit)
            output = format_results(results, "Latest News", "mcp")
            return [TextContent(type="text", text=output)]

        elif name == "list_engines":
            engines = list_available_engines()
            lines = ["AVAILABLE SEARCH ENGINES", "=" * 40, ""]
            for engine_type, platforms in engines.items():
                lines.append(f"{engine_type.upper()}:")
                for p in platforms:
                    lines.append(f"  - {p}")
                lines.append("")
            output = "\n".join(lines)
            return [TextContent(type="text", text=output)]

        elif name == "fetch_content":
            url = arguments.get("url")
            max_length = arguments.get("max_length", 8000)
            start_index = arguments.get("start_index", 0)
            output = _fetch_content(url, max_length, start_index)
            return [TextContent(type="text", text=output)]

        # P0 新增工具处理
        elif name == "check_health":
            checker = get_health_checker()
            status = await checker.check_all()

            lines = ["SOURCE HEALTH STATUS", "=" * 50, ""]
            for source_name, health in status.items():
                status_icon = {
                    "healthy": "✓",
                    "degraded": "⚠",
                    "unhealthy": "✗",
                    "unknown": "?"
                }.get(health.status.value, "?")

                lines.append(f"{status_icon} {source_name}: {health.status.value}")
                if health.response_time > 0:
                    lines.append(f"    Response time: {health.response_time:.0f}ms")
                if health.error_message:
                    lines.append(f"    Error: {health.error_message}")

            lines.append("")
            summary = checker.get_summary()
            lines.append(f"Summary: {summary['healthy']} healthy, {summary['degraded']} degraded, {summary['unhealthy']} unhealthy")

            output = "\n".join(lines)
            return [TextContent(type="text", text=output)]

        elif name == "clear_cache":
            clear_cache()
            return [TextContent(type="text", text="Cache cleared successfully.")]

        elif name == "cache_stats":
            cache = get_cache()
            stats = cache.stats()
            lines = [
                "CACHE STATISTICS",
                "=" * 30,
                f"Total entries: {stats['total_entries']}",
                f"Valid entries: {stats['valid_entries']}",
                f"Hit count: {stats['hit_count']}",
                f"Miss count: {stats['miss_count']}",
                f"Hit rate: {stats['hit_rate']:.1%}",
            ]
            output = "\n".join(lines)
            return [TextContent(type="text", text=output)]

        # P1 新增工具处理
        elif name == "deep_research":
            topic = arguments.get("topic")
            depth = arguments.get("depth", "standard")
            sources = arguments.get("sources", 5)

            # 从配置读取 API 设置
            config = get_config()
            result = await deep_research(
                topic,
                depth=depth,
                sources=sources,
                api_key=config.anthropic_api_key,
                base_url=config.anthropic_base_url,
                model=config.anthropic_model
            )

            lines = [
                f"DEEP RESEARCH: {result.topic}",
                "=" * 50,
                "",
                "SUMMARY:",
                result.summary,
                "",
                "KEY FINDINGS:",
            ]
            for f in result.key_findings:
                lines.append(f"  • {f}")

            lines.append("")
            lines.append("RELATED QUESTIONS:")
            for q in result.related_questions:
                lines.append(f"  • {q}")

            lines.append("")
            lines.append("SOURCES ANALYZED:")
            for i, s in enumerate(result.sources[:5], 1):
                content_preview = (s.get('content') or s.get('snippet', ''))[:100]
                lines.append(f"  [{i}] {s['title']}")
                lines.append(f"      URL: {s['url']}")
                lines.append(f"      Platform: {s['platform']}")
                lines.append(f"      Preview: {content_preview}...")

            lines.append("")
            lines.append(f"Quality Score: {result.quality_score:.2f}")
            lines.append(f"Expanded Keywords: {', '.join(result.expanded_keywords)}")

            output = "\n".join(lines)
            return [TextContent(type="text", text=output)]

        elif name == "suggest_keywords":
            query = arguments.get("query")

            # 先执行搜索获取结果，以便提取相关术语
            results = search_web(query, limit=15)

            expander = get_expander()
            suggestion = expander.expand(query, results)

            lines = [
                f"KEYWORD SUGGESTIONS FOR: {suggestion.original}",
                "=" * 50,
                "",
                "EXPANDED KEYWORDS:",
            ]
            for kw in suggestion.expanded:
                lines.append(f"  • {kw}")

            lines.append("")
            lines.append("RELATED TERMS:")
            for kw in suggestion.related:
                lines.append(f"  • {kw}")

            lines.append("")
            lines.append("TECHNICAL TERMS:")
            for kw in suggestion.technical_terms:
                lines.append(f"  • {kw}")

            output = "\n".join(lines)
            return [TextContent(type="text", text=output)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def run_server():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    """Main entry point"""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()