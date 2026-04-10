"""Result formatting utilities."""


def format_results(results: list, title: str) -> str:
    """Format search results as Markdown."""
    if not results:
        return f"## {title}\n\nNo results found."

    lines = [f"## {title}\n"]
    for i, r in enumerate(results, 1):
        title_text = r.get("title", "Untitled")
        url = r.get("url", "")
        snippet = r.get("snippet", "")[:200] if r.get("snippet") else ""

        if url:
            lines.append(f"{i}. [{title_text}]({url})")
        else:
            lines.append(f"{i}. {title_text}")

        if snippet:
            lines.append(f"   {snippet}...")
        lines.append("")

    return "\n".join(lines)


def format_arxiv(papers: list) -> str:
    """Format arXiv papers."""
    if not papers:
        return "## arXiv Results\n\nNo papers found."

    lines = ["## arXiv Papers\n"]
    for i, p in enumerate(papers, 1):
        title = p.get("title", "Untitled")
        url = p.get("url", "")
        authors = p.get("authors", [])
        published = p.get("published", "")
        abstract = p.get("abstract", "")[:300] if p.get("abstract") else ""

        if url:
            lines.append(f"{i}. [{title}]({url})")
        else:
            lines.append(f"{i}. {title}")

        if authors:
            lines.append(f"   Authors: {', '.join(authors[:3])}")
        if published:
            lines.append(f"   Published: {published}")
        if abstract:
            lines.append(f"   {abstract}...")
        lines.append("")

    return "\n".join(lines)


def format_hn(stories: list) -> str:
    """Format HackerNews stories."""
    if not stories:
        return "## HackerNews Results\n\nNo stories found."

    lines = ["## HackerNews Stories\n"]
    for i, s in enumerate(stories, 1):
        title = s.get("title", "Untitled")
        url = s.get("url", "")
        points = s.get("points", 0)
        author = s.get("author", "")

        if url:
            lines.append(f"{i}. [{title}]({url})")
        else:
            lines.append(f"{i}. {title}")

        lines.append(f"   {points} points by {author}")
        lines.append("")

    return "\n".join(lines)


def format_reddit(posts: list) -> str:
    """Format Reddit posts."""
    if not posts:
        return "## Reddit Results\n\nNo posts found."

    lines = ["## Reddit Posts\n"]
    for i, p in enumerate(posts, 1):
        title = p.get("title", "Untitled")
        url = p.get("url", "")
        score = p.get("score", 0)
        subreddit = p.get("subreddit", "")
        permalink = p.get("permalink", "")

        if url:
            lines.append(f"{i}. [{title}]({url})")
        else:
            lines.append(f"{i}. {title}")

        lines.append(f"   r/{subreddit} | {score} points")
        if permalink:
            lines.append(f"   [Discussion]({permalink})")
        lines.append("")

    return "\n".join(lines)


def format_cn(results: list, source: str) -> str:
    """Format Chinese platform results."""
    if not results:
        return f"## {source} Results\n\nNo results found."

    lines = [f"## {source.capitalize()} Results\n"]
    for i, r in enumerate(results, 1):
        title = r.get("title", "Untitled")
        url = r.get("url", "")
        snippet = r.get("snippet", "")[:150] if r.get("snippet") else ""

        if url:
            lines.append(f"{i}. [{title}]({url})")
        else:
            lines.append(f"{i}. {title}")

        if snippet:
            lines.append(f"   {snippet}...")
        lines.append("")

    return "\n".join(lines)


def format_company(news: list, company: str) -> str:
    """Format company news."""
    if not news:
        return f"## {company} News\n\nNo news found."

    lines = [f"## {company} News\n"]
    for i, n in enumerate(news, 1):
        title = n.get("title", "Untitled")
        url = n.get("url", "")
        source = n.get("source", "")
        date = n.get("date", "")

        if url:
            lines.append(f"{i}. [{title}]({url})")
        else:
            lines.append(f"{i}. {title}")

        meta = []
        if source:
            meta.append(source)
        if date:
            meta.append(date)
        if meta:
            lines.append(f"   {' | '.join(meta)}")
        lines.append("")

    return "\n".join(lines)


def format_health(status: dict) -> str:
    """Format health status."""
    lines = ["## Source Health Status\n"]

    status_icons = {
        "healthy": "✓",
        "degraded": "⚠",
        "unhealthy": "✗",
        "unknown": "?"
    }

    for source_name, health in status.items():
        icon = status_icons.get(health.status.value if hasattr(health.status, 'value') else str(health.status), "?")
        status_val = health.status.value if hasattr(health.status, 'value') else str(health.status)
        lines.append(f"{icon} {source_name}: {status_val}")

        if hasattr(health, 'response_time') and health.response_time > 0:
            lines.append(f"    Response time: {health.response_time:.0f}ms")
        if hasattr(health, 'error_message') and health.error_message:
            lines.append(f"    Error: {health.error_message}")

    return "\n".join(lines)


def format_cache_stats(stats: dict) -> str:
    """Format cache statistics."""
    lines = [
        "## Cache Statistics\n",
        f"- Total entries: {stats.get('total_entries', 0)}",
        f"- Valid entries: {stats.get('valid_entries', 0)}",
        f"- Hit count: {stats.get('hit_count', 0)}",
        f"- Miss count: {stats.get('miss_count', 0)}",
        f"- Hit rate: {stats.get('hit_rate', 0):.1%}",
    ]
    return "\n".join(lines)


def format_keywords(suggestion) -> str:
    """Format keyword suggestions."""
    lines = [f"## Keyword Suggestions for: {suggestion.original}\n"]

    lines.append("### Expanded Keywords:")
    for kw in suggestion.expanded:
        lines.append(f"- {kw}")

    lines.append("\n### Related Terms:")
    for kw in suggestion.related:
        lines.append(f"- {kw}")

    if suggestion.technical_terms:
        lines.append("\n### Technical Terms:")
        for kw in suggestion.technical_terms:
            lines.append(f"- {kw}")

    return "\n".join(lines)


def format_research(result) -> str:
    """Format deep research result."""
    lines = [
        f"## Deep Research: {result.topic}\n",
        "### Summary:",
        result.summary,
        "",
        "### Key Findings:",
    ]
    for f in result.key_findings:
        lines.append(f"- {f}")

    lines.append("\n### Related Questions:")
    for q in result.related_questions:
        lines.append(f"- {q}")

    lines.append(f"\n### Quality Score: {result.quality_score:.2f}")

    if result.expanded_keywords:
        lines.append(f"\n### Expanded Keywords: {', '.join(result.expanded_keywords)}")

    return "\n".join(lines)


def format_engine_list() -> str:
    """List all available engines."""
    lines = [
        "## Available Search Engines\n",
        "### Web Search:",
        "- DuckDuckGo (default)",
        "",
        "### Academic:",
        "- arXiv",
        "",
        "### Social:",
        "- HackerNews",
        "- Reddit",
        "",
        "### Chinese Platforms:",
        "- Zhihu (知乎)",
        "- CSDN",
        "- CNBlogs (博客园)",
        "",
        "### News:",
        "- BBC World",
        "- TechCrunch",
        "- Ars Technica",
        "- Hacker News RSS",
    ]
    return "\n".join(lines)