"""Deep research module."""

import asyncio
import os
import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ResearchResult:
    """Deep research result."""
    topic: str
    summary: str
    key_findings: List[str]
    sources: List[Dict]
    related_questions: List[str]
    quality_score: float
    expanded_keywords: List[str]


class ClaudeAnalyzer:
    """Claude API analyzer - supports Anthropic-compatible APIs."""

    DEFAULT_MODEL = "claude-3-haiku-20240307"

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = None
    ):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.base_url = base_url or os.environ.get("ANTHROPIC_BASE_URL")
        self.model = model or os.environ.get("ANTHROPIC_MODEL") or self.DEFAULT_MODEL
        self._client = None

    def _get_client(self):
        """Get Claude client (lazy init)."""
        if self._client is None:
            if not self.api_key:
                raise ValueError("API key not set. Set ANTHROPIC_API_KEY environment variable.")
            try:
                import anthropic
                self._client = anthropic.Anthropic(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            except ImportError:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
        return self._client

    def analyze_content(self, topic: str, sources: List[Dict]) -> Dict:
        """Analyze content using Claude API."""
        client = self._get_client()

        content_parts = []
        for i, s in enumerate(sources[:5], 1):
            content_text = s.get('content', '') or s.get('snippet', '')
            if content_text and not content_text.startswith("Error"):
                content_parts.append(
                    f"【Source {i}: {s['title']} ({s.get('platform', 'web')})】\n"
                    f"{content_text[:800]}"
                )

        if not content_parts:
            return {
                "summary": f"Could not retrieve detailed content about {topic}.",
                "findings": [],
                "questions": []
            }

        content_text = "\n\n".join(content_parts)

        prompt = f"""Based on the following research materials, provide a comprehensive analysis about: {topic}

{content_text}

Please provide:
1. SUMMARY: A concise summary (150-200 words)
2. FINDINGS: 3-5 key findings (one line each)
3. QUESTIONS: 3 follow-up research questions

Format:
SUMMARY:
[summary content]

FINDINGS:
- [finding 1]
- [finding 2]

QUESTIONS:
- [question 1]
- [question 2]
"""

        try:
            message = client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = ""
            for block in message.content:
                if hasattr(block, 'text'):
                    response_text += block.text
                elif hasattr(block, 'type') and block.type == 'text':
                    response_text += getattr(block, 'text', '')

            return self._parse_response(response_text)

        except Exception as e:
            return {
                "summary": f"Analysis error: {str(e)}",
                "findings": [],
                "questions": []
            }

    def _parse_response(self, text: str) -> Dict:
        """Parse Claude response."""
        result = {"summary": "", "findings": [], "questions": []}

        lines = text.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith("SUMMARY:"):
                current_section = "summary"
                result["summary"] = line[8:].strip()
            elif line.startswith("FINDINGS:"):
                current_section = "findings"
            elif line.startswith("QUESTIONS:"):
                current_section = "questions"
            elif line.startswith("-") and current_section in ["findings", "questions"]:
                item = line[1:].strip()
                if item:
                    result[current_section].append(item)
            elif current_section == "summary" and line:
                result["summary"] += " " + line

        result["summary"] = result["summary"].strip()
        return result


async def multi_source_search(
    query: str,
    sources: List[str] = None,
    limit: int = 5,
) -> Dict[str, List[Dict]]:
    """Search across multiple sources."""
    from ..sources import (
        search_web, search_arxiv, search_hackernews,
        search_reddit, search_zhihu, search_csdn, search_cnblogs
    )

    if sources is None:
        sources = ["web", "arxiv", "hackernews"]

    if limit <= 0:
        return {}

    results = {}
    tasks = []

    source_map = {
        "web": lambda: search_web(query, limit),
        "arxiv": lambda: search_arxiv(query, limit),
        "hackernews": lambda: search_hackernews(query, limit),
        "reddit": lambda: search_reddit(query, limit=limit),
        "zhihu": lambda: search_zhihu(query, limit),
        "csdn": lambda: search_csdn(query, limit),
        "cnblogs": lambda: search_cnblogs(query, limit),
    }

    for source in sources:
        if source in source_map:
            if source in ["arxiv", "hackernews", "reddit"]:
                tasks.append((source, source_map[source]))
            else:
                results[source] = source_map[source]()

    # Run async tasks
    async_tasks = [t[1]() for t in tasks]
    if async_tasks:
        async_results = await asyncio.gather(*async_tasks, return_exceptions=True)
        for i, (source, _) in enumerate(tasks):
            if isinstance(async_results[i], Exception):
                results[source] = []
            else:
                results[source] = async_results[i]

    return results


async def _fetch_content_from_results(results: List[Dict]) -> List[str]:
    """Fetch content from URLs."""
    import aiohttp
    from bs4 import BeautifulSoup

    contents = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")

    async with aiohttp.ClientSession() as session:
        for result in results:
            url = result.get("url", "")
            if not url:
                continue
            try:
                kwargs = {"headers": headers, "timeout": aiohttp.ClientTimeout(total=10)}
                if proxy:
                    kwargs["proxy"] = proxy
                async with session.get(url, **kwargs) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        soup = BeautifulSoup(html, "html.parser")
                        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
                            tag.decompose()
                        text = soup.get_text(separator=" ", strip=True)
                        contents.append(text[:3000])
            except Exception:
                snippet = result.get("snippet", "")
                if snippet:
                    contents.append(snippet)

    return contents


def _extract_key_terms(content_list: List[str], original_topic: str) -> List[str]:
    """Extract key terms for follow-up searches."""
    combined = " ".join(content_list)
    words = re.findall(r"\b[A-Z][a-z]{3,}\b", combined)
    word_counts = {}
    for w in words:
        word_counts[w] = word_counts.get(w, 0) + 1

    top_terms = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    queries = [f"{original_topic} {term[0]}" for term in top_terms]

    return queries[:2]


async def deep_research(
    topic: str,
    depth: str = "standard",
    sources_per_round: int = 5,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    model: Optional[str] = None,
) -> ResearchResult:
    """
    Perform deep research on a topic.

    Args:
        topic: Research topic or question (should be specific, not generic like "test")
        depth: 'basic' (1 round), 'standard' (2 rounds), 'comprehensive' (3 rounds)
        sources_per_round: Sources to analyze per round (1-10)
        api_key: API key for analysis
        api_base: API base URL
        model: Model name

    Returns:
        ResearchResult object

    Note:
        Generic or very short topics (like "test", "hello") may return
        irrelevant results. Use specific research questions for best results.
    """
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    base = api_base or os.environ.get("ANTHROPIC_BASE_URL")
    mdl = model or os.environ.get("ANTHROPIC_MODEL")

    if not key:
        return ResearchResult(
            topic=topic,
            summary="Error: ANTHROPIC_API_KEY not set.",
            key_findings=[],
            sources=[],
            related_questions=[],
            quality_score=0.0,
            expanded_keywords=[]
        )

    # Validate and warn about generic topics
    GENERIC_TOPICS = {"test", "hello", "foo", "bar", "test topic", "example", "demo"}
    topic_lower = topic.lower().strip()
    is_generic = topic_lower in GENERIC_TOPICS or len(topic_lower) < 3

    if is_generic:
        return ResearchResult(
            topic=topic,
            summary=f"Warning: '{topic}' appears to be a generic test topic. For meaningful research, please provide a specific topic like 'machine learning trends 2024' or 'quantum computing applications'.",
            key_findings=["Please provide a more specific research topic for meaningful results."],
            sources=[],
            related_questions=["What specific aspect of this topic would you like to research?"],
            quality_score=0.0,
            expanded_keywords=[]
        )

    # Validate parameters
    sources_per_round = max(1, min(sources_per_round, 10))

    rounds_map = {"basic": 1, "standard": 2, "comprehensive": 3}
    num_rounds = rounds_map.get(depth, 2)

    all_content = []
    search_queries = [topic]
    all_sources = []

    for round_num in range(num_rounds):
        round_results = []
        for query in search_queries:
            results = await multi_source_search(
                query,
                sources=["web", "hackernews"],
                limit=sources_per_round,
            )
            for source_name, items in results.items():
                for item in items:
                    item["source"] = source_name
                    round_results.append(item)

        # Fetch content from top results
        content_texts = await _fetch_content_from_results(round_results[:sources_per_round])
        all_content.extend(content_texts)
        all_sources.extend(round_results[:sources_per_round])

        # Generate next round queries
        if round_num < num_rounds - 1:
            search_queries = _extract_key_terms(all_content, topic)

    # Analyze with LLM
    analyzer = ClaudeAnalyzer(api_key=key, base_url=base, model=mdl)
    analysis = await asyncio.to_thread(analyzer.analyze_content, topic, all_sources)

    # Calculate quality score
    quality = min(len(all_sources) / 10, 1.0) * 0.5 + min(len(all_content) / 5, 1.0) * 0.5

    return ResearchResult(
        topic=topic,
        summary=analysis.get("summary", ""),
        key_findings=analysis.get("findings", []),
        sources=all_sources[:10],
        related_questions=analysis.get("questions", []),
        quality_score=round(quality, 2),
        expanded_keywords=search_queries[:3]
    )