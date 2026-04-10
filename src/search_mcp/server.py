"""
Search MCP Server - Unified MCP for web search, academic research, and tech news.
"""

import asyncio
import os
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import search functions
from .sources import (
    search_web, search_news, search_arxiv,
    search_hackernews, search_reddit, search_zhihu,
    search_csdn, search_cnblogs, search_company,
    get_latest_news, search_news_articles
)
from .utils.fetcher import fetch_content
from .utils.cache import get_cache, clear_cache
from .utils.health import get_health_checker
from .utils.keywords import get_expander
from .utils.formatter import (
    format_results, format_arxiv, format_hn, format_reddit,
    format_cn, format_company, format_health, format_cache_stats,
    format_keywords, format_research, format_engine_list
)
from .research import deep_research

# Create MCP server
server = Server("search-mcp")


# Define tools
TOOLS = [
    Tool(
        name="search_web",
        description="Quick web search using DuckDuckGo. Fast and privacy-friendly.",
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
        description="Search news sources for recent articles.",
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
        name="search_arxiv",
        description="Search arXiv for academic papers using real arXiv API.",
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
        name="search_hackernews",
        description="Search HackerNews for tech discussions.",
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
        name="search_reddit",
        description="Search Reddit for community discussions.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "subreddit": {"type": "string", "default": "all", "description": "Subreddit to search"},
                "limit": {"type": "integer", "default": 10, "description": "Maximum results"}
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="search_cn",
        description="Search Chinese tech content (Zhihu, CSDN, CNBlogs).",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "source": {
                    "type": "string",
                    "default": "all",
                    "enum": ["all", "zhihu", "csdn", "cnblogs"],
                    "description": "Platform to search"
                },
                "limit": {"type": "integer", "default": 10, "description": "Maximum results"}
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="search_company",
        description="Search news about any company (supports Chinese/English names).",
        inputSchema={
            "type": "object",
            "properties": {
                "company": {"type": "string", "description": "Company name"},
                "days": {"type": "integer", "default": 7, "description": "Days to look back"},
                "limit": {"type": "integer", "default": 10, "description": "Maximum results"}
            },
            "required": ["company"]
        }
    ),
    Tool(
        name="fetch_content",
        description="Extract main content from a webpage URL. Strips navigation, scripts, styles to return clean text.",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"},
                "max_length": {"type": "integer", "default": 8000, "description": "Maximum characters"},
                "start_index": {"type": "integer", "default": 0, "description": "Start index for pagination"}
            },
            "required": ["url"]
        }
    ),
    Tool(
        name="get_latest_news",
        description="Get latest news headlines from RSS sources.",
        inputSchema={
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Specific source (bbc_world, techcrunch, etc.)"},
                "limit": {"type": "integer", "default": 20, "description": "Maximum results"}
            }
        }
    ),
    Tool(
        name="check_health",
        description="Check health status of all search sources.",
        inputSchema={"type": "object", "properties": {}}
    ),
    Tool(
        name="cache_stats",
        description="Get cache statistics (hit rate, entries, etc.).",
        inputSchema={"type": "object", "properties": {}}
    ),
    Tool(
        name="clear_cache",
        description="Clear the search result cache.",
        inputSchema={"type": "object", "properties": {}}
    ),
    Tool(
        name="deep_research",
        description="Perform deep research on a topic with AI analysis. Requires ANTHROPIC_API_KEY.",
        inputSchema={
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Research topic"},
                "depth": {
                    "type": "string",
                    "default": "standard",
                    "enum": ["basic", "standard", "comprehensive"],
                    "description": "Research depth"
                },
                "sources": {"type": "integer", "default": 5, "description": "Sources per round"}
            },
            "required": ["topic"]
        }
    ),
    Tool(
        name="suggest_keywords",
        description="Suggest expanded keywords for better search coverage.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Original search query"}
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="list_engines",
        description="List all available search engines and platforms.",
        inputSchema={"type": "object", "properties": {}}
    ),
]


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Return list of available tools."""
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    cache = get_cache()

    try:
        if name == "search_web":
            query = arguments.get("query")
            limit = arguments.get("limit", 10)
            # Check cache first
            cached = cache.get("web", query, limit)
            if cached:
                return [TextContent(type="text", text=format_results(cached, "Web Search (cached)"))]
            results = search_web(query, limit)
            cache.set("web", query, limit, results)
            return [TextContent(type="text", text=format_results(results, "Web Search"))]

        elif name == "search_news":
            query = arguments.get("query")
            limit = arguments.get("limit", 10)
            cached = cache.get("news", query, limit)
            if cached:
                return [TextContent(type="text", text=format_results(cached, "News (cached)"))]
            results = search_news(query, limit)
            cache.set("news", query, limit, results)
            return [TextContent(type="text", text=format_results(results, "News"))]

        elif name == "search_arxiv":
            query = arguments.get("query")
            limit = arguments.get("limit", 10)
            cached = cache.get("arxiv", query, limit)
            if cached:
                return [TextContent(type="text", text=format_arxiv(cached))]
            results = await search_arxiv(query, limit)
            cache.set("arxiv", query, limit, results)
            return [TextContent(type="text", text=format_arxiv(results))]

        elif name == "search_hackernews":
            query = arguments.get("query")
            limit = arguments.get("limit", 10)
            cached = cache.get("hackernews", query, limit)
            if cached:
                return [TextContent(type="text", text=format_hn(cached))]
            results = await search_hackernews(query, limit)
            cache.set("hackernews", query, limit, results)
            return [TextContent(type="text", text=format_hn(results))]

        elif name == "search_reddit":
            query = arguments.get("query")
            subreddit = arguments.get("subreddit", "all")
            limit = arguments.get("limit", 10)
            cached = cache.get("reddit", query, limit, subreddit)
            if cached:
                return [TextContent(type="text", text=format_reddit(cached))]
            results = await search_reddit(query, subreddit, limit)
            cache.set("reddit", query, limit, results, subreddit)
            return [TextContent(type="text", text=format_reddit(results))]

        elif name == "search_cn":
            query = arguments.get("query")
            source = arguments.get("source", "all")
            limit = arguments.get("limit", 10)

            if source == "all":
                # Search all Chinese platforms - check cache for each
                results = []
                for platform, search_func, platform_name in [
                    ("zhihu", search_zhihu, "Zhihu"),
                    ("csdn", search_csdn, "CSDN"),
                    ("cnblogs", search_cnblogs, "CNBlogs")
                ]:
                    cached = cache.get(platform, query, limit // 3 + 1)
                    if cached:
                        results.extend(cached)
                    else:
                        platform_results = search_func(query, limit // 3 + 1)
                        cache.set(platform, query, limit // 3 + 1, platform_results)
                        results.extend(platform_results)
                results = results[:limit]
                source_name = "Chinese Platforms"
            else:
                # Single platform search
                cached = cache.get(source, query, limit)
                if cached:
                    results = cached
                else:
                    platform_map = {
                        "zhihu": (search_zhihu, "Zhihu"),
                        "csdn": (search_csdn, "CSDN"),
                        "cnblogs": (search_cnblogs, "CNBlogs"),
                    }
                    search_func, source_name = platform_map.get(source, (search_zhihu, "Zhihu"))
                    results = search_func(query, limit)
                    cache.set(source, query, limit, results)

            return [TextContent(type="text", text=format_cn(results, source_name))]

        elif name == "search_company":
            company = arguments.get("company")
            days = arguments.get("days", 7)
            limit = arguments.get("limit", 10)
            cached = cache.get("company", company, limit, platform=str(days))
            if cached:
                return [TextContent(type="text", text=format_company(cached, company))]
            results = search_company(company, days, limit)
            cache.set("company", company, limit, results, platform=str(days))
            return [TextContent(type="text", text=format_company(results, company))]

        elif name == "fetch_content":
            url = arguments.get("url")
            max_length = arguments.get("max_length", 8000)
            start_index = arguments.get("start_index", 0)
            # Cache content fetch with URL as key
            cached = cache.get("fetch", url, max_length, platform=str(start_index))
            if cached:
                return [TextContent(type="text", text=cached)]
            result = fetch_content(url, max_length, start_index)
            # Only cache successful results
            if not result.startswith("Error"):
                cache.set("fetch", url, max_length, result, platform=str(start_index), ttl=600)
            return [TextContent(type="text", text=result)]

        elif name == "get_latest_news":
            source = arguments.get("source")
            limit = arguments.get("limit", 20)
            results = await get_latest_news(source, limit)
            return [TextContent(type="text", text=format_results(results, "Latest News"))]

        elif name == "check_health":
            checker = get_health_checker()
            status = await checker.check_all()
            return [TextContent(type="text", text=format_health(status))]

        elif name == "cache_stats":
            cache = get_cache()
            stats = cache.stats()
            return [TextContent(type="text", text=format_cache_stats(stats))]

        elif name == "clear_cache":
            clear_cache()
            return [TextContent(type="text", text="Cache cleared successfully.")]

        elif name == "deep_research":
            topic = arguments.get("topic")
            depth = arguments.get("depth", "standard")
            sources = arguments.get("sources", 5)

            api_key = os.environ.get("ANTHROPIC_API_KEY")
            base_url = os.environ.get("ANTHROPIC_BASE_URL")
            model = os.environ.get("ANTHROPIC_MODEL")

            if not api_key:
                return [TextContent(type="text", text="Error: ANTHROPIC_API_KEY not set.")]

            result = await deep_research(topic, depth, sources, api_key, base_url, model)
            return [TextContent(type="text", text=format_research(result))]

        elif name == "suggest_keywords":
            query = arguments.get("query")
            cached = cache.get("keywords", query, 15)
            if cached:
                return [TextContent(type="text", text=format_keywords(cached))]
            results = search_web(query, limit=15)
            expander = get_expander()
            suggestion = expander.expand(query, results)
            cache.set("keywords", query, 15, suggestion)
            return [TextContent(type="text", text=format_keywords(suggestion))]

        elif name == "list_engines":
            return [TextContent(type="text", text=format_engine_list())]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def run_server():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    """Main entry point."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()