"""结果质量评分系统 - 评分随结果缓存"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from search_tool.engines.base import SearchResult


@dataclass
class QualityScore:
    """质量评分结果"""
    overall: float  # 综合评分 0-1
    authority: float  # 来源权威性 0-1
    freshness: float  # 新鲜度 0-1
    completeness: float  # 完整性 0-1
    consistency: float  # 多源一致性 0-1
    reason: str  # 评分理由


class QualityScorer:
    """质量评分器"""

    # 权威性权重映射
    AUTHORITY_WEIGHTS = {
        # 搜索引擎
        "duckduckgo": 0.7,
        "google": 0.8,
        "bing": 0.7,
        # 新闻源
        "hacker_news": 0.85,
        "techcrunch": 0.8,
        "ars_technica": 0.8,
        "wired": 0.8,
        "the_verge": 0.8,
        "engadget": 0.75,
        # 学术/技术
        "arxiv": 0.95,
        "hackernews": 0.85,  # 注意：社交引擎中的 hackernews
        # 社交媒体
        "reddit": 0.65,
        "twitter": 0.55,
        "nitter": 0.55,
        # 中文平台
        "zhihu": 0.6,
        "cnblogs": 0.65,
        "csdn": 0.5,
    }

    # 默认权重
    DEFAULT_AUTHORITY = 0.5

    def __init__(self):
        """初始化评分器"""
        pass

    def score(self, result: SearchResult, all_results: List[SearchResult] = None) -> QualityScore:
        """
        计算单个结果的质量评分

        Args:
            result: 待评分的搜索结果
            all_results: 所有搜索结果（用于计算一致性）

        Returns:
            QualityScore 对象
        """
        # 1. 权威性评分
        authority = self.AUTHORITY_WEIGHTS.get(result.platform, self.DEFAULT_AUTHORITY)

        # 2. 新鲜度评分（基于时间戳）
        freshness = self._calc_freshness(result.timestamp)

        # 3. 完整性评分（基于 snippet 长度）
        completeness = self._calc_completeness(result.snippet)

        # 4. 多源一致性评分
        consistency = self._calc_consistency(result, all_results)

        # 5. 综合评分（加权平均）
        overall = (
            authority * 0.30 +
            freshness * 0.20 +
            completeness * 0.25 +
            consistency * 0.25
        )

        # 生成评分理由
        reason = self._generate_reason(authority, freshness, completeness, consistency)

        return QualityScore(
            overall=round(overall, 3),
            authority=round(authority, 3),
            freshness=round(freshness, 3),
            completeness=round(completeness, 3),
            consistency=round(consistency, 3),
            reason=reason
        )

    def score_and_enrich(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        评分并丰富结果的 extra 字段（用于缓存）

        Args:
            results: 搜索结果列表

        Returns:
            已评分并排序的结果列表
        """
        if not results:
            return results

        for r in results:
            score = self.score(r, results)
            r.extra["quality_score"] = score.overall
            r.extra["quality_reason"] = score.reason
            r.extra["quality_details"] = {
                "authority": score.authority,
                "freshness": score.freshness,
                "completeness": score.completeness,
                "consistency": score.consistency
            }

        # 按评分排序
        results.sort(key=lambda x: x.extra.get("quality_score", 0), reverse=True)
        return results

    def score_batch(self, results: List[SearchResult]) -> List[Dict[str, Any]]:
        """
        批量评分并返回详细结果（用于 score_results MCP 工具）

        Args:
            results: 搜索结果列表

        Returns:
            评分详情列表（按评分排序）
        """
        scored = []
        for r in results:
            score = self.score(r, results)
            scored.append({
                "title": r.title,
                "url": r.url,
                "platform": r.platform,
                "snippet": r.snippet[:100] + "..." if len(r.snippet) > 100 else r.snippet,
                "score": score.overall,
                "reason": score.reason,
                "details": {
                    "authority": score.authority,
                    "freshness": score.freshness,
                    "completeness": score.completeness,
                    "consistency": score.consistency
                }
            })

        # 按评分排序
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored

    def _calc_freshness(self, timestamp: Optional[str]) -> float:
        """
        计算新鲜度评分

        Args:
            timestamp: 时间戳字符串

        Returns:
            新鲜度评分 0-1
        """
        if not timestamp:
            return 0.5  # 无时间戳时给中等分

        timestamp_lower = timestamp.lower()

        # 相对时间格式
        if "hour" in timestamp_lower:
            return 1.0
        elif "day" in timestamp_lower:
            if "1 day" in timestamp_lower or "yesterday" in timestamp_lower:
                return 0.95
            return 0.85
        elif "week" in timestamp_lower:
            return 0.65
        elif "month" in timestamp_lower:
            return 0.45
        elif "year" in timestamp_lower:
            return 0.3

        # ISO 格式或其他格式
        return 0.5

    def _calc_completeness(self, snippet: Optional[str]) -> float:
        """
        计算完整性评分

        Args:
            snippet: 摘要文本

        Returns:
            完整性评分 0-1
        """
        if not snippet:
            return 0.1

        length = len(snippet)

        # 长度映射到评分
        if length >= 300:
            return 1.0
        elif length >= 200:
            return 0.85
        elif length >= 100:
            return 0.7
        elif length >= 50:
            return 0.5
        else:
            return 0.3

    def _calc_consistency(self, result: SearchResult, all_results: List[SearchResult]) -> float:
        """
        计算多源一致性评分

        检查是否有其他平台提到相似内容

        Args:
            result: 待评分结果
            all_results: 所有结果

        Returns:
            一致性评分 0-1
        """
        if not all_results or len(all_results) <= 1:
            return 0.5

        # 提取当前结果的关键词
        title_words = set(result.title.lower().split())
        snippet_words = set(result.snippet.lower().split()) if result.snippet else set()
        current_keywords = title_words | snippet_words

        # 过滤停用词
        stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                     "have", "has", "had", "do", "does", "did", "will", "would", "could",
                     "should", "may", "might", "must", "shall", "can", "need", "dare",
                     "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
                     "from", "as", "into", "through", "during", "before", "after",
                     "above", "below", "between", "under", "again", "further", "then",
                     "once", "here", "there", "when", "where", "why", "how", "all", "each",
                     "few", "more", "most", "other", "some", "such", "no", "nor", "not",
                     "only", "own", "same", "so", "than", "too", "very", "just", "and",
                     "but", "if", "or", "because", "until", "while", "this", "that", "these",
                     "those", "it", "its"}

        current_keywords = current_keywords - stopwords

        if not current_keywords:
            return 0.5

        # 检查其他平台是否有相似内容
        similar_count = 0
        for r in all_results:
            if r.platform == result.platform or r.url == result.url:
                continue

            other_words = set(r.title.lower().split())
            if r.snippet:
                other_words |= set(r.snippet.lower().split())
            other_keywords = other_words - stopwords

            # 计算关键词重叠度
            common = current_keywords & other_keywords
            if len(common) >= 3:  # 至少 3 个共同关键词
                similar_count += 1

        # 映射到评分
        if similar_count >= 3:
            return 1.0
        elif similar_count >= 2:
            return 0.85
        elif similar_count >= 1:
            return 0.7
        else:
            return 0.4

    def _generate_reason(self, authority: float, freshness: float,
                         completeness: float, consistency: float) -> str:
        """
        生成评分理由

        Args:
            authority: 权威性评分
            freshness: 新鲜度评分
            completeness: 完整性评分
            consistency: 一致性评分

        Returns:
            评分理由字符串
        """
        reasons = []

        if authority >= 0.8:
            reasons.append("权威来源")
        elif authority < 0.5:
            reasons.append("来源可信度较低")

        if freshness >= 0.8:
            reasons.append("内容新鲜")
        elif freshness < 0.4:
            reasons.append("内容较旧")

        if completeness >= 0.8:
            reasons.append("内容完整")
        elif completeness < 0.5:
            reasons.append("摘要简短")

        if consistency >= 0.7:
            reasons.append("多源验证")
        elif consistency < 0.4:
            reasons.append("单一来源")

        return " | ".join(reasons) if reasons else "评分中等"


# 全局实例
_scorer: Optional[QualityScorer] = None


def get_scorer() -> QualityScorer:
    """获取全局评分器实例"""
    global _scorer
    if _scorer is None:
        _scorer = QualityScorer()
    return _scorer