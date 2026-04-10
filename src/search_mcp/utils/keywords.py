"""Keyword expansion module."""

from typing import List, Optional
from dataclasses import dataclass
import re
from collections import Counter


@dataclass
class KeywordSuggestion:
    """Keyword suggestion result."""
    original: str
    expanded: List[str]
    related: List[str]
    technical_terms: List[str]


class KeywordExpander:
    """Keyword expander."""

    MODIFIERS_EN = ["tutorial", "guide", "best practices", "examples", "how to", "introduction"]
    MODIFIERS_ZH = ["教程", "入门", "实践", "原理", "实现", "最佳实践"]
    QUESTION_FORMS = ["what is", "how to", "why", "when to use"]

    def expand(self, query: str, results: Optional[List[dict]] = None) -> KeywordSuggestion:
        """Expand keywords."""
        expanded = self._basic_expand(query)
        related = []
        technical_terms = []

        if results:
            related = self._extract_related(results)
            technical_terms = self._extract_technical(results)

        return KeywordSuggestion(
            original=query, expanded=expanded,
            related=related, technical_terms=technical_terms
        )

    def _basic_expand(self, query: str) -> List[str]:
        expanded = []
        is_chinese = bool(re.search(r'[\u4e00-\u9fff]', query))

        if is_chinese:
            for m in self.MODIFIERS_ZH[:3]:
                expanded.append(f"{query} {m}")
        else:
            for m in self.MODIFIERS_EN[:2]:
                expanded.append(f"{query} {m}")
            for q in self.QUESTION_FORMS[:2]:
                expanded.append(f"{q} {query}")

        return list(dict.fromkeys(expanded))[:5]

    def _extract_related(self, results: List[dict]) -> List[str]:
        all_words = []
        for r in results[:15]:
            title = r.get("title", "")
            snippet = r.get("snippet", "")
            all_words.extend(re.findall(r'\b[A-Za-z]{3,}\b', (title + " " + snippet).lower()))

        stopwords = {"the", "a", "is", "are", "was", "were", "have", "has", "for", "with", "from", "this", "that"}
        all_words = [w for w in all_words if w not in stopwords and len(w) > 3]
        word_freq = Counter(all_words)
        return [w for w, _ in word_freq.most_common(8)]

    def _extract_technical(self, results: List[dict]) -> List[str]:
        patterns = [r'\b[A-Z]{2,}\b', r'\b[A-Za-z]+-[A-Za-z]+\b', r'\b\d+\.\d+(?:\.\d+)?\b']
        terms = []
        for r in results[:15]:
            text = r.get("title", "") + " " + r.get("snippet", "")
            for p in patterns:
                terms.extend(re.findall(p, text))
        return list(set(terms))[:8]


_expander: Optional[KeywordExpander] = None


def get_expander() -> KeywordExpander:
    global _expander
    if _expander is None:
        _expander = KeywordExpander()
    return _expander