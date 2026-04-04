"""Output formatting utilities"""

import json
from typing import List, Optional
from datetime import datetime

from search_tool.engines.base import SearchResult


class OutputFormatter:
    """Format search results for display"""

    def format_table(self, results: List[SearchResult], query: str) -> str:
        """Format results as a table (for terminal display)"""
        if not results:
            return f"No results found for: {query}"

        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"  Search Results: '{query}' ({len(results)} items)")
        lines.append(f"{'='*60}\n")

        for i, result in enumerate(results, 1):
            lines.append(f"[{i}] {result.title}")
            lines.append(f"    Platform: {result.platform}")
            lines.append(f"    URL: {result.url}")
            lines.append(f"    {result.snippet[:150]}...")
            if result.timestamp:
                lines.append(f"    Time: {result.timestamp}")
            lines.append("")
            lines.append("-" * 60)
            lines.append("")

        return "\n".join(lines)

    def format_json(self, results: List[SearchResult], query: str) -> str:
        """Format results as JSON"""
        data = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "count": len(results),
            "results": [r.to_dict() for r in results],
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def format_simple(self, results: List[SearchResult], query: str) -> str:
        """Format results in simple text format"""
        if not results:
            return f"No results found for: {query}"

        lines = []
        lines.append(f"Search: {query} ({len(results)} results)")
        lines.append("")

        for i, result in enumerate(results, 1):
            lines.append(f"[{i}] {result.title}")
            lines.append(f"    {result.url}")
            lines.append(f"    {result.snippet[:100]}...")
            lines.append("")

        return "\n".join(lines)

    def format_markdown(self, results: List[SearchResult], query: str) -> str:
        """Format results as Markdown"""
        if not results:
            return f"## No results found for: `{query}`"

        lines = []
        lines.append(f"## Search Results: `{query}`")
        lines.append(f"Found {len(results)} results")
        lines.append("")

        for i, result in enumerate(results, 1):
            lines.append(f"### {i}. {result.title}")
            lines.append(f"- **Platform**: {result.platform}")
            lines.append(f"- **URL**: [{result.url}]({result.url})")
            lines.append(f"- **Snippet**: {result.snippet[:200]}...")
            if result.timestamp:
                lines.append(f"- **Time**: {result.timestamp}")
            lines.append("")

        return "\n".join(lines)

    def format_for_mcp(self, results: List[SearchResult], query: str) -> str:
        """Format results for MCP tool return (optimized for LLM consumption)"""
        if not results:
            return f"No results found for query: {query}"

        lines = []
        lines.append(f"SEARCH RESULTS FOR: {query}")
        lines.append(f"Total: {len(results)} results")
        lines.append("---")

        for i, result in enumerate(results, 1):
            source_tag = f"[{result.source}:{result.platform}]"
            lines.append(f"{i}. {source_tag} {result.title}")
            lines.append(f"   URL: {result.url}")
            lines.append(f"   Content: {result.snippet}")
            if result.timestamp:
                lines.append(f"   Time: {result.timestamp}")
            lines.append("")

        return "\n".join(lines)


def format_results(
    results: List[SearchResult],
    query: str,
    format_type: str = "table"
) -> str:
    """
    Format results using specified format type

    Args:
        results: List of search results
        query: Original query string
        format_type: Format type (table/json/simple/markdown/mcp)

    Returns:
        Formatted string
    """
    formatter = OutputFormatter()

    format_map = {
        "table": formatter.format_table,
        "json": formatter.format_json,
        "simple": formatter.format_simple,
        "markdown": formatter.format_markdown,
        "mcp": formatter.format_for_mcp,
    }

    format_func = format_map.get(format_type, formatter.format_table)
    return format_func(results, query)


def print_results(
    results: List[SearchResult],
    query: str,
    format_type: str = "table"
):
    """Print formatted results to console"""
    output = format_results(results, query, format_type)
    print(output)