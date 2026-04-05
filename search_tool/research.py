"""深度研究模块 - 集成 Claude API 分析"""

import asyncio
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from search_tool.engines.base import SearchResult
from search_tool.async_api import async_search
from search_tool.scoring import get_scorer
from search_tool.keywords import get_expander


@dataclass
class ResearchResult:
    """深度研究结果"""
    topic: str
    summary: str                    # Claude 生成的综合摘要
    key_findings: List[str]         # Claude 提取的关键发现
    sources: List[Dict]             # 详细来源列表
    related_questions: List[str]    # Claude 生成的相关问题
    quality_score: float            # 研究质量评分
    expanded_keywords: List[str]    # 扩展的关键词


class ClaudeAnalyzer:
    """Claude API 分析器 - 支持兼容 Anthropic 协议的接口"""

    # 默认模型
    DEFAULT_MODEL = "claude-3-haiku-20240307"

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = None
    ):
        """
        初始化分析器

        Args:
            api_key: API 密钥，默认从环境变量 ANTHROPIC_API_KEY 读取
            base_url: API 基础 URL，默认从环境变量 ANTHROPIC_BASE_URL 读取
            model: 模型名称，默认 claude-3-haiku-20240307
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.base_url = base_url or os.environ.get("ANTHROPIC_BASE_URL")
        self.model = model or self.DEFAULT_MODEL
        self._client = None

    def _get_client(self):
        """获取 Claude 客户端（延迟初始化）"""
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "API key not set. Please set ANTHROPIC_API_KEY environment variable "
                    "or pass api_key parameter."
                )
            try:
                import anthropic
                self._client = anthropic.Anthropic(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            except ImportError:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
        return self._client

    def analyze_content(self, topic: str, sources: List[Dict]) -> Dict[str, Any]:
        """
        调用 Claude API 分析内容

        Args:
            topic: 研究主题
            sources: 来源列表

        Returns:
            分析结果字典
        """
        client = self._get_client()

        # 构建内容文本
        content_parts = []
        for i, s in enumerate(sources[:5], 1):
            content_text = s.get('content', '') or s.get('snippet', '')
            if content_text and not content_text.startswith("Error"):
                content_parts.append(
                    f"【来源 {i}: {s['title']} ({s['platform']})】\n"
                    f"{content_text[:800]}"
                )

        if not content_parts:
            return {
                "summary": f"无法获取关于 {topic} 的详细内容，请检查来源是否可访问。",
                "findings": [],
                "questions": []
            }

        content_text = "\n\n".join(content_parts)

        # 构建 prompt
        prompt = f"""请对以下关于"{topic}"的多个来源内容进行综合分析：

{content_text}

请输出：
1. 综合摘要（150-200字，整合各来源的核心信息）
2. 关键发现（3-5条，每条一句话，提炼重要观点或事实）
3. 相关问题（3个后续研究问题，帮助深入了解该领域）

请严格按照以下格式输出：

SUMMARY:
[综合摘要内容]

FINDINGS:
- [发现1]
- [发现2]
- [发现3]

QUESTIONS:
- [问题1]
- [问题2]
- [问题3]
"""

        try:
            # 调用 Claude API（使用配置的模型）
            message = client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            # 提取文本内容（兼容 ThinkingBlock 和 TextBlock）
            response_text = ""
            for block in message.content:
                if hasattr(block, 'text'):
                    response_text += block.text
                elif hasattr(block, 'type') and block.type == 'text':
                    response_text += getattr(block, 'text', '')

            if not response_text:
                return {
                    "summary": "API 返回了空响应",
                    "findings": [],
                    "questions": []
                }

            return self._parse_response(response_text)

        except Exception as e:
            return {
                "summary": f"分析过程中出现错误: {str(e)}",
                "findings": [],
                "questions": []
            }

    def _parse_response(self, text: str) -> Dict[str, Any]:
        """
        解析 Claude 响应

        Args:
            text: Claude 返回的文本

        Returns:
            解析后的字典
        """
        result = {
            "summary": "",
            "findings": [],
            "questions": []
        }

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
                # 摘要多行拼接
                result["summary"] += " " + line

        # 清理摘要
        result["summary"] = result["summary"].strip()

        return result


class DeepResearchAgent:
    """深度研究 Agent"""

    def __init__(
        self,
        max_rounds: int = 2,
        sources_per_round: int = 5,
        api_key: str = None,
        base_url: str = None,
        model: str = None
    ):
        """
        初始化研究 Agent

        Args:
            max_rounds: 最大搜索轮次
            sources_per_round: 每轮获取的来源数
            api_key: API 密钥（可选，默认从环境变量读取）
            base_url: API 基础 URL（可选，默认使用阿里云 DashScope）
            model: 模型名称（可选）
        """
        self.max_rounds = max_rounds
        self.sources_per_round = sources_per_round
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._analyzer: Optional[ClaudeAnalyzer] = None

    @property
    def analyzer(self) -> ClaudeAnalyzer:
        """获取 Claude 分析器（延迟初始化）"""
        if self._analyzer is None:
            self._analyzer = ClaudeAnalyzer(
                api_key=self.api_key,
                base_url=self.base_url,
                model=self.model
            )
        return self._analyzer

    async def research(self, topic: str) -> ResearchResult:
        """
        执行深度研究

        Args:
            topic: 研究主题

        Returns:
            ResearchResult 对象
        """
        # 第一轮：初始搜索
        initial_results = await async_search(
            topic,
            engines=["search", "news"],
            limit=self.sources_per_round,
            use_cache=True,
            use_health_check=True
        )

        # 提取扩展关键词
        expander = get_expander()
        keyword_suggestion = expander.expand(topic, initial_results)
        expanded_keywords = keyword_suggestion.expanded[:3]

        # 第二轮：扩展搜索
        expanded_results = []
        if self.max_rounds >= 2:
            for kw in expanded_keywords[:2]:
                try:
                    results = await async_search(
                        kw,
                        engines=["search"],
                        limit=3,
                        use_cache=True
                    )
                    expanded_results.extend(results)
                except Exception:
                    continue

        # 合并并去重
        all_results = self._deduplicate(initial_results + expanded_results)

        # 对关键结果获取详细内容
        detailed_sources = await self._fetch_details(all_results[:self.sources_per_round])

        # 使用 Claude 分析内容
        analysis = await asyncio.get_event_loop().run_in_executor(
            None,
            self.analyzer.analyze_content,
            topic,
            detailed_sources
        )

        # 计算质量评分
        quality = self._calculate_quality(all_results, detailed_sources)

        return ResearchResult(
            topic=topic,
            summary=analysis["summary"],
            key_findings=analysis["findings"],
            sources=detailed_sources,
            related_questions=analysis["questions"],
            quality_score=quality,
            expanded_keywords=expanded_keywords
        )

    def _deduplicate(self, results: List[SearchResult]) -> List[SearchResult]:
        """去重"""
        seen_urls = set()
        unique = []
        for r in results:
            if r.url not in seen_urls:
                seen_urls.add(r.url)
                unique.append(r)
        return unique

    async def _fetch_details(self, results: List[SearchResult]) -> List[Dict]:
        """获取详细内容"""
        detailed = []

        # 使用线程池并发获取
        loop = asyncio.get_event_loop()

        async def fetch_one(r: SearchResult) -> Dict:
            try:
                # 使用 mcp_server 中的 fetch_content 逻辑
                content = await loop.run_in_executor(
                    None,
                    self._fetch_url_content,
                    r.url
                )
                return {
                    "title": r.title,
                    "url": r.url,
                    "snippet": r.snippet,
                    "content": content,
                    "platform": r.platform,
                    "timestamp": r.timestamp
                }
            except Exception as e:
                return {
                    "title": r.title,
                    "url": r.url,
                    "snippet": r.snippet,
                    "content": f"Error: {str(e)}",
                    "platform": r.platform,
                    "timestamp": r.timestamp
                }

        tasks = [fetch_one(r) for r in results]
        detailed = await asyncio.gather(*tasks)

        return detailed

    def _fetch_url_content(self, url: str, max_length: int = 2000) -> str:
        """获取 URL 内容"""
        import requests
        from search_tool.config import get_config

        config = get_config()
        proxies = {"http": config.proxy, "https": config.proxy} if config.proxy else None

        try:
            response = requests.get(
                url,
                timeout=15,
                proxies=proxies,
                headers={"User-Agent": "Mozilla/5.0 (compatible; SearchTool/1.0)"}
            )

            if response.status_code == 200:
                # 简单的 HTML 提取
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')

                # 移除脚本和样式
                for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                    element.decompose()

                text = soup.get_text(separator=' ', strip=True)
                # 清理多余空白
                text = ' '.join(text.split())

                return text[:max_length] if len(text) > max_length else text
            else:
                return f"Error: HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            return "Error: Request timed out"
        except requests.exceptions.ConnectionError:
            return "Error: Connection failed"
        except Exception as e:
            return f"Error: {str(e)[:100]}"

    def _calculate_quality(self, results: List[SearchResult], detailed: List[Dict]) -> float:
        """计算研究质量评分"""
        if not results:
            return 0.0

        # 来源多样性
        platforms = set(r.platform for r in results)
        source_diversity = min(len(platforms) / 4, 1.0)  # 最多 4 个平台

        # 内容完整性
        successful_fetches = len([
            d for d in detailed
            if d.get("content") and not d["content"].startswith("Error")
        ])
        content_completeness = successful_fetches / len(detailed) if detailed else 0

        # 综合评分
        return round(source_diversity * 0.4 + content_completeness * 0.6, 2)


# 便捷函数
async def deep_research(
    topic: str,
    depth: str = "standard",
    sources: int = 5,
    api_key: str = None,
    base_url: str = None,
    model: str = None
) -> ResearchResult:
    """
    执行深度研究

    Args:
        topic: 研究主题
        depth: 深度级别 (basic=1轮, standard=2轮, comprehensive=3轮)
        sources: 每轮来源数
        api_key: API 密钥（可选，默认从环境变量 ANTHROPIC_API_KEY 读取）
        base_url: API 基础 URL（可选，默认使用阿里云 DashScope）
        model: 模型名称（可选）

    Returns:
        ResearchResult 对象
    """
    depth_map = {"basic": 1, "standard": 2, "comprehensive": 3}
    max_rounds = depth_map.get(depth, 2)

    agent = DeepResearchAgent(
        max_rounds=max_rounds,
        sources_per_round=sources,
        api_key=api_key,
        base_url=base_url,
        model=model
    )
    return await agent.research(topic)


# For direct module usage
if __name__ == "__main__":
    async def test():
        print("Testing deep research...")

        result = await deep_research("MCP protocol", depth="basic", sources=3)

        print(f"\nTopic: {result.topic}")
        print(f"Quality Score: {result.quality_score}")
        print(f"\nSummary:\n{result.summary}")
        print(f"\nKey Findings:")
        for f in result.key_findings:
            print(f"  - {f}")
        print(f"\nRelated Questions:")
        for q in result.related_questions:
            print(f"  - {q}")

    asyncio.run(test())