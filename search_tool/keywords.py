"""关键词扩展模块"""

from typing import List, Optional
from dataclasses import dataclass
import re
from collections import Counter

from search_tool.engines.base import SearchResult


@dataclass
class KeywordSuggestion:
    """关键词建议结果"""
    original: str              # 原始查询
    expanded: List[str]        # 扩展关键词
    related: List[str]         # 相关关键词
    technical_terms: List[str] # 技术术语


class KeywordExpander:
    """关键词扩展器"""

    # 常见修饰词
    MODIFIERS_EN = [
        "tutorial",
        "guide",
        "best practices",
        "examples",
        "how to",
        "introduction",
        "advanced",
        "beginners",
    ]

    MODIFIERS_ZH = [
        "教程",
        "入门",
        "实践",
        "原理",
        "实现",
        "最佳实践",
        "最新",
    ]

    # 问题形式
    QUESTION_FORMS = [
        "what is",
        "how to",
        "why",
        "when to use",
        "comparison",
    ]

    def __init__(self):
        """初始化关键词扩展器"""
        pass

    def expand(
        self,
        query: str,
        results: Optional[List[SearchResult]] = None
    ) -> KeywordSuggestion:
        """
        扩展关键词

        Args:
            query: 原始查询
            results: 可选的搜索结果（用于提取相关词）

        Returns:
            KeywordSuggestion 对象
        """
        # 基础扩展：添加修饰词
        expanded = self._basic_expand(query)

        # 相关词：从结果中提取
        related = []
        technical_terms = []

        if results:
            related = self._extract_related_from_results(results)
            technical_terms = self._extract_technical_terms(results)

        return KeywordSuggestion(
            original=query,
            expanded=expanded,
            related=related,
            technical_terms=technical_terms
        )

    def _basic_expand(self, query: str) -> List[str]:
        """
        基础关键词扩展

        Args:
            query: 原始查询

        Returns:
            扩展后的关键词列表
        """
        expanded = []

        # 检测是否为中文查询
        is_chinese = self._contains_chinese(query)

        if is_chinese:
            # 中文修饰词
            for m in self.MODIFIERS_ZH[:3]:
                expanded.append(f"{query} {m}")
        else:
            # 英文修饰词
            for m in self.MODIFIERS_EN[:2]:
                expanded.append(f"{query} {m}")

            # 问题形式
            for q in self.QUESTION_FORMS[:2]:
                expanded.append(f"{q} {query}")

        # 去重并限制数量
        return list(dict.fromkeys(expanded))[:5]

    def _extract_related_from_results(self, results: List[SearchResult]) -> List[str]:
        """
        从搜索结果中提取相关关键词

        Args:
            results: 搜索结果列表

        Returns:
            相关关键词列表
        """
        all_words = []

        for r in results[:15]:
            # 从标题提取
            title_words = self._extract_words(r.title)
            all_words.extend(title_words)

            # 从摘要提取
            if r.snippet:
                snippet_words = self._extract_words(r.snippet)
                all_words.extend(snippet_words)

        # 过滤停用词
        stopwords = self._get_stopwords()
        all_words = [w for w in all_words if w not in stopwords and len(w) > 3]

        # 统计频率并返回高频词
        word_freq = Counter(all_words)
        return [w for w, _ in word_freq.most_common(8)]

    def _extract_technical_terms(self, results: List[SearchResult]) -> List[str]:
        """
        提取技术术语

        Args:
            results: 搜索结果列表

        Returns:
            技术术语列表
        """
        technical_patterns = [
            r'\b[A-Z]{2,}\b',           # 缩写如 API, MCP, SDK, HTTP
            r'\b[A-Za-z]+-[A-Za-z]+\b',  # 连字符词如 client-side, open-source
            r'\b\d+\.\d+(?:\.\d+)?\b',   # 版本号如 4.0, 2.5.1
            r'\b[A-Z][a-z]+[A-Z][a-z]+\b', # 驼峰词如 JavaScript, TypeScript
        ]

        terms = []
        for r in results[:15]:
            text = r.title + " " + (r.snippet or "")
            for pattern in technical_patterns:
                found = re.findall(pattern, text)
                terms.extend(found)

        # 去重并过滤常见词
        common_words = {"The", "This", "That", "And", "For", "With", "From", "About"}
        terms = [t for t in set(terms) if t not in common_words]

        return terms[:8]

    def _extract_words(self, text: str) -> List[str]:
        """
        从文本中提取单词

        Args:
            text: 输入文本

        Returns:
            单词列表
        """
        if not text:
            return []

        # 提取英文单词
        words = re.findall(r'\b[A-Za-z]{3,}\b', text.lower())

        # 提取中文词（简单的字组）
        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', text)
        words.extend([c for c in chinese_chars if len(c) >= 2])

        return words

    def _contains_chinese(self, text: str) -> bool:
        """检测文本是否包含中文"""
        return bool(re.search(r'[\u4e00-\u9fff]', text))

    def _get_stopwords(self) -> set:
        """获取停用词集合"""
        return {
            # 英文停用词
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "must", "shall", "can", "need", "dare",
            "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
            "from", "as", "into", "through", "during", "before", "after",
            "above", "below", "between", "under", "again", "further", "then",
            "once", "here", "there", "when", "where", "why", "how", "all", "each",
            "few", "more", "most", "other", "some", "such", "no", "nor", "not",
            "only", "own", "same", "so", "than", "too", "very", "just", "and",
            "but", "if", "or", "because", "until", "while", "this", "that", "these",
            "those", "it", "its", "they", "them", "their", "we", "our", "you", "your",
            "about", "which", "who", "what", "where", "when", "how",
            # 常见无意义词
            "new", "get", "make", "use", "using", "used", "one", "two", "also",
            "like", "time", "year", "know", "take", "come", "good", "first", "last",
        }


# 全局实例
_expander: Optional[KeywordExpander] = None


def get_expander() -> KeywordExpander:
    """获取全局关键词扩展器实例"""
    global _expander
    if _expander is None:
        _expander = KeywordExpander()
    return _expander