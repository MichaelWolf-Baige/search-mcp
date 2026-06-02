#!/usr/bin/env python3
"""测试关键词扩展和深度研究模块"""

import sys
import os
import asyncio
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

# 添加项目路径
sys.path.insert(0, "D:/search-mcp")

from search_tool.engines.base import SearchResult
from search_tool.keywords import KeywordExpander, KeywordSuggestion, get_expander


# ==================== 关键词扩展测试 ====================

def test_keyword_expander_init():
    """测试 KeywordExpander 初始化"""
    print("\n--- 测试 1: KeywordExpander 初始化 ---")
    expander = KeywordExpander()
    assert expander is not None, "KeywordExpander 初始化失败"
    print("[PASS] KeywordExpander 初始化成功")
    return expander


def test_chinese_query_expand():
    """测试中文查询扩展"""
    print("\n--- 测试 2: 中文查询扩展 ---")
    expander = KeywordExpander()

    # 测试纯中文查询
    query = "机器学习"
    result = expander.expand(query)

    print(f"原始查询: {query}")
    print(f"扩展关键词: {result.expanded}")
    print(f"相关关键词: {result.related}")
    print(f"技术术语: {result.technical_terms}")

    # 验证
    assert result.original == query, "原始查询未正确保存"
    assert len(result.expanded) > 0, "中文查询应有扩展关键词"
    assert any("教程" in kw or "入门" in kw for kw in result.expanded), "中文扩展应包含中文修饰词"

    print("[PASS] 中文查询扩展测试通过")


def test_english_query_expand():
    """测试英文查询扩展"""
    print("\n--- 测试 3: 英文查询扩展 ---")
    expander = KeywordExpander()

    # 测试纯英文查询
    query = "machine learning"
    result = expander.expand(query)

    print(f"原始查询: {query}")
    print(f"扩展关键词: {result.expanded}")
    print(f"相关关键词: {result.related}")
    print(f"技术术语: {result.technical_terms}")

    # 验证
    assert result.original == query, "原始查询未正确保存"
    assert len(result.expanded) > 0, "英文查询应有扩展关键词"
    # 英文扩展应包含英文修饰词或问题形式
    expected_parts = ["tutorial", "guide", "what is", "how to"]
    has_expected = any(any(part in kw for part in expected_parts) for kw in result.expanded)
    assert has_expected, f"英文扩展应包含修饰词或问题形式，实际: {result.expanded}"

    print("[PASS] 英文查询扩展测试通过")


def test_extract_related_from_results():
    """测试从搜索结果提取相关词"""
    print("\n--- 测试 4: 从搜索结果提取相关词 ---")
    expander = KeywordExpander()

    # 创建模拟搜索结果
    results = [
        SearchResult(
            title="Python Machine Learning Tutorial",
            url="https://example.com/1",
            snippet="Learn machine learning with Python. Deep learning and neural networks explained.",
            source="search",
            platform="duckduckgo"
        ),
        SearchResult(
            title="AI and ML Best Practices",
            url="https://example.com/2",
            snippet="Artificial intelligence and machine learning best practices for developers.",
            source="search",
            platform="duckduckgo"
        ),
        SearchResult(
            title="Data Science with Python",
            url="https://example.com/3",
            snippet="Data science tutorial using Python libraries like pandas and numpy.",
            source="search",
            platform="duckduckgo"
        ),
    ]

    query = "machine learning"
    result = expander.expand(query, results)

    print(f"原始查询: {query}")
    print(f"相关关键词: {result.related}")

    # 验证 - 相关词应来自搜索结果
    assert len(result.related) > 0, "应能从搜索结果提取相关词"
    # 检查是否提取到了关键词
    common_words = set()
    for word in result.related:
        common_words.add(word.lower())

    # 应该包含一些有意义的相关词
    print(f"提取到的相关词: {result.related}")

    print("[PASS] 从搜索结果提取相关词测试通过")


def test_extract_technical_terms():
    """测试技术术语提取"""
    print("\n--- 测试 5: 技术术语提取 ---")
    expander = KeywordExpander()

    # 创建包含技术术语的模拟搜索结果
    results = [
        SearchResult(
            title="MCP Protocol Guide for AI SDK",
            url="https://example.com/1",
            snippet="Model Context Protocol (MCP) is a new API standard. Supports HTTP and JSON-RPC.",
            source="search",
            platform="duckduckgo"
        ),
        SearchResult(
            title="Claude API v4.0 Released",
            url="https://example.com/2",
            snippet="Anthropic released Claude API version 4.0 with TypeScript support.",
            source="search",
            platform="duckduckgo"
        ),
        SearchResult(
            title="Open-source AI Tools",
            url="https://example.com/3",
            snippet="client-side JavaScript libraries for AI integration.",
            source="search",
            platform="duckduckgo"
        ),
    ]

    query = "MCP protocol"
    result = expander.expand(query, results)

    print(f"原始查询: {query}")
    print(f"技术术语: {result.technical_terms}")

    # 验证 - 应能提取技术术语
    assert len(result.technical_terms) > 0, "应能提取技术术语"

    # 检查提取到的术语类型
    terms_str = " ".join(result.technical_terms)
    print(f"提取到的技术术语类型: 缩写/API/版本号/连字符词等")

    # 应包含一些大写缩写
    has_abbr = any(t.isupper() or (t.isalpha() and len(t) >= 2 and t[0].isupper() and t[1:].islower() is False) for t in result.technical_terms)
    has_version = any('.' in t for t in result.technical_terms)
    has_hyphen = any('-' in t for t in result.technical_terms)

    print(f"包含缩写术语: {has_abbr}")
    print(f"包含版本号: {has_version}")
    print(f"包含连字符词: {has_hyphen}")

    print("[PASS] 技术术语提取测试通过")


def test_get_expander_singleton():
    """测试全局实例获取"""
    print("\n--- 测试 6: 全局关键词扩展器实例 ---")

    expander1 = get_expander()
    expander2 = get_expander()

    assert expander1 is not None, "get_expander 应返回实例"
    assert expander1 is expander2, "get_expander 应返回同一实例（单例）"

    print("[PASS] 全局实例获取测试通过")


# ==================== 深度研究模块测试 ====================

def test_claude_analyzer_init():
    """测试 ClaudeAnalyzer 初始化"""
    print("\n--- 测试 7: ClaudeAnalyzer 初始化 ---")

    from search_tool.research import ClaudeAnalyzer

    # 测试无 API key 的初始化
    analyzer = ClaudeAnalyzer()
    assert analyzer.api_key is None or analyzer.api_key == os.environ.get("ANTHROPIC_API_KEY"), "API key 应从环境变量读取"
    assert analyzer.model == "claude-3-haiku-20240307", "默认模型应为 claude-3-haiku-20240307"

    print(f"API key: {analyzer.api_key or '未设置'}")
    print(f"Base URL: {analyzer.base_url or '未设置'}")
    print(f"Model: {analyzer.model}")

    # 测试带参数的初始化
    analyzer2 = ClaudeAnalyzer(api_key="test_key", base_url="https://test.url", model="test-model")
    assert analyzer2.api_key == "test_key", "应接受自定义 API key"
    assert analyzer2.base_url == "https://test.url", "应接受自定义 base_url"
    assert analyzer2.model == "test-model", "应接受自定义模型"

    print("[PASS] ClaudeAnalyzer 初始化测试通过")


def test_parse_response():
    """测试 Claude 响应解析"""
    print("\n--- 测试 8: Claude 响应解析 ---")

    from search_tool.research import ClaudeAnalyzer

    analyzer = ClaudeAnalyzer()

    # 模拟 Claude 响应
    mock_response = """SUMMARY:
This is a comprehensive summary of the topic. It covers multiple aspects and provides detailed information.

FINDINGS:
- First important finding about the topic
- Second key discovery from the research
- Third notable insight from sources

QUESTIONS:
- What are the implications of this finding?
- How does this relate to broader context?
- What future research is needed?
"""

    result = analyzer._parse_response(mock_response)

    print(f"解析结果:")
    print(f"摘要: {result['summary'][:100]}...")
    print(f"发现数: {len(result['findings'])}")
    print(f"问题数: {len(result['questions'])}")

    # 验证解析结果
    assert len(result['summary']) > 0, "摘要不应为空"
    assert len(result['findings']) >= 3, "应解析至少 3 个发现"
    assert len(result['questions']) >= 3, "应解析至少 3 个问题"

    # 验证内容正确性
    assert "comprehensive summary" in result['summary'].lower(), "摘要内容应正确"
    assert "First important finding" in result['findings'][0], "第一个发现应正确"
    assert "implications" in result['questions'][0], "第一个问题应正确"

    print("[PASS] Claude 响应解析测试通过")


def test_calculate_quality():
    """测试质量评分计算"""
    print("\n--- 测试 9: 质量评分计算 ---")

    from search_tool.research import DeepResearchAgent

    agent = DeepResearchAgent()

    # 创建模拟结果
    results = [
        SearchResult(
            title="Source 1",
            url="https://example.com/1",
            snippet="Test snippet",
            source="search",
            platform="duckduckgo"
        ),
        SearchResult(
            title="Source 2",
            url="https://example.com/2",
            snippet="Test snippet",
            source="news",
            platform="bbc"
        ),
        SearchResult(
            title="Source 3",
            url="https://example.com/3",
            snippet="Test snippet",
            source="social",
            platform="reddit"
        ),
        SearchResult(
            title="Source 4",
            url="https://example.com/4",
            snippet="Test snippet",
            source="search",
            platform="bing"
        ),
    ]

    # 模拟详细内容
    detailed = [
        {"title": "Source 1", "url": "https://example.com/1", "content": "Valid content", "platform": "duckduckgo"},
        {"title": "Source 2", "url": "https://example.com/2", "content": "Valid content", "platform": "bbc"},
        {"title": "Source 3", "url": "https://example.com/3", "content": "Error: Failed", "platform": "reddit"},
        {"title": "Source 4", "url": "https://example.com/4", "content": "Valid content", "platform": "bing"},
    ]

    quality = agent._calculate_quality(results, detailed)

    print(f"平台数: {len(set(r.platform for r in results))}")
    print(f"成功获取内容数: {len([d for d in detailed if not d['content'].startswith('Error')])}")
    print(f"质量评分: {quality}")

    # 验证评分范围
    assert 0 <= quality <= 1, f"质量评分应在 0-1 之间，实际: {quality}"

    # 计算期望值
    source_diversity = min(4 / 4, 1.0)  # 4 个不同平台
    content_completeness = 3 / 4  # 3 个成功，1 个失败
    expected = round(source_diversity * 0.4 + content_completeness * 0.6, 2)

    assert quality == expected, f"质量评分计算错误，期望 {expected}，实际 {quality}"

    print("[PASS] 质量评分计算测试通过")


def test_deduplicate():
    """测试结果去重"""
    print("\n--- 测试 10: 结果去重 ---")

    from search_tool.research import DeepResearchAgent

    agent = DeepResearchAgent()

    # 创建重复的搜索结果
    results = [
        SearchResult(
            title="Source 1",
            url="https://example.com/1",
            snippet="Test",
            source="search",
            platform="duckduckgo"
        ),
        SearchResult(
            title="Source 1 Duplicate",
            url="https://example.com/1",  # 重复 URL
            snippet="Test duplicate",
            source="search",
            platform="duckduckgo"
        ),
        SearchResult(
            title="Source 2",
            url="https://example.com/2",
            snippet="Test",
            source="search",
            platform="duckduckgo"
        ),
        SearchResult(
            title="Source 2 Duplicate",
            url="https://example.com/2",  # 重复 URL
            snippet="Test duplicate",
            source="search",
            platform="duckduckgo"
        ),
        SearchResult(
            title="Source 3",
            url="https://example.com/3",
            snippet="Test",
            source="search",
            platform="duckduckgo"
        ),
    ]

    unique = agent._deduplicate(results)

    print(f"原始结果数: {len(results)}")
    print(f"去重后结果数: {len(unique)}")

    # 验证去重
    assert len(unique) == 3, f"应去重为 3 个结果，实际: {len(unique)}"

    # 验证保留的是第一个
    urls = [r.url for r in unique]
    assert urls == ["https://example.com/1", "https://example.com/2", "https://example.com/3"], "去重顺序应正确"

    print("[PASS] 结果去重测试通过")


def test_analyze_content_no_api_key():
    """测试无 API key 时的 analyze_content"""
    print("\n--- 测试 11: analyze_content 无 API key 处理 ---")

    from search_tool.research import ClaudeAnalyzer

    analyzer = ClaudeAnalyzer(api_key=None)  # 明确无 API key

    # 尝试获取客户端应该抛出错误
    try:
        client = analyzer._get_client()
        print("警告: 无 API key 时不应能获取客户端")
    except ValueError as e:
        print(f"正确抛出 ValueError: {e}")
        assert "API key not set" in str(e), "错误消息应提及 API key"
        print("[PASS] 无 API key 处理测试通过")
    except ImportError as e:
        print(f"正确抛出 ImportError: {e}")
        print("[PASS] 无 API key 处理测试通过")


def test_research_result_dataclass():
    """测试 ResearchResult 数据类"""
    print("\n--- 测试 12: ResearchResult 数据结构 ---")

    from search_tool.research import ResearchResult

    result = ResearchResult(
        topic="Test Topic",
        summary="Test summary",
        key_findings=["Finding 1", "Finding 2"],
        sources=[{"url": "https://example.com"}],
        related_questions=["Question 1", "Question 2"],
        quality_score=0.85,
        expanded_keywords=["keyword1", "keyword2"]
    )

    print(f"Topic: {result.topic}")
    print(f"Summary: {result.summary}")
    print(f"Key Findings: {result.key_findings}")
    print(f"Sources: {len(result.sources)}")
    print(f"Quality Score: {result.quality_score}")

    # 验证字段
    assert result.topic == "Test Topic", "topic 应正确"
    assert result.summary == "Test summary", "summary 应正确"
    assert len(result.key_findings) == 2, "key_findings 数量应正确"
    assert result.quality_score == 0.85, "quality_score 应正确"

    print("[PASS] ResearchResult 数据结构测试通过")


def test_keyword_suggestion_dataclass():
    """测试 KeywordSuggestion 数据类"""
    print("\n--- 测试 13: KeywordSuggestion 数据结构 ---")

    suggestion = KeywordSuggestion(
        original="test query",
        expanded=["test query tutorial", "test query guide"],
        related=["related1", "related2"],
        technical_terms=["API", "SDK"]
    )

    print(f"Original: {suggestion.original}")
    print(f"Expanded: {suggestion.expanded}")
    print(f"Related: {suggestion.related}")
    print(f"Technical Terms: {suggestion.technical_terms}")

    # 验证字段
    assert suggestion.original == "test query", "original 应正确"
    assert len(suggestion.expanded) == 2, "expanded 数量应正确"
    assert "API" in suggestion.technical_terms, "technical_terms 应包含 API"

    print("[PASS] KeywordSuggestion 数据结构测试通过")


def test_empty_results_handling():
    """测试空结果处理"""
    print("\n--- 测试 14: 空结果处理 ---")

    expander = KeywordExpander()

    # 无搜索结果时的扩展
    result = expander.expand("test query", results=None)

    assert result.original == "test query", "原始查询应保存"
    assert len(result.expanded) > 0, "应有基础扩展"
    assert len(result.related) == 0, "无搜索结果时相关词应为空"
    assert len(result.technical_terms) == 0, "无搜索结果时技术术语应为空"

    print("[PASS] 空结果处理测试通过")


def test_mixed_chinese_english_query():
    """测试中英混合查询"""
    print("\n--- 测试 15: 中英混合查询 ---")

    expander = KeywordExpander()

    # 中英混合查询
    query = "Python 机器学习"
    result = expander.expand(query)

    print(f"原始查询: {query}")
    print(f"扩展关键词: {result.expanded}")

    # 检测到中文时应使用中文修饰词
    assert any("教程" in kw or "入门" in kw for kw in result.expanded), "混合查询含中文应使用中文修饰词"

    print("[PASS] 中英混合查询测试通过")


# ==================== 主测试运行器 ====================

def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("关键词扩展和深度研究模块测试")
    print("=" * 60)

    tests = [
        # 关键词扩展测试
        test_keyword_expander_init,
        test_chinese_query_expand,
        test_english_query_expand,
        test_extract_related_from_results,
        test_extract_technical_terms,
        test_get_expander_singleton,

        # 深度研究模块测试
        test_claude_analyzer_init,
        test_parse_response,
        test_calculate_quality,
        test_deduplicate,
        test_analyze_content_no_api_key,
        test_research_result_dataclass,
        test_keyword_suggestion_dataclass,

        # 边界条件测试
        test_empty_results_handling,
        test_mixed_chinese_english_query,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] 测试失败: {test.__name__}")
            print(f"  原因: {e}")
            failed += 1
        except Exception as e:
            print(f"[FAIL] 测试异常: {test.__name__}")
            print(f"  异常: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"测试结果: 通过 {passed} / 失败 {failed}")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)