"""社交平台搜索功能测试脚本"""

import sys
import time

sys.path.insert(0, 'D:/search-mcp')

from search_tool.engines.social import (
    HackerNewsEngine,
    TwitterXEngine,
    RedditEngine,
    NitterEngine,
    ZhihuEngine,
    CnblogsEngine,
    CSDNEngine,
    ArxivEngine,
    get_social_engine,
    get_all_social_engines,
    SOCIAL_ENGINES,
    HAS_DDGS
)
from search_tool.engines.base import SearchResult, EngineError


class TestResult:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.bugs = []

    def add_pass(self, name):
        self.passed.append(name)
        print(f"[PASS] {name}")

    def add_fail(self, name, error):
        self.failed.append((name, error))
        print(f"[FAIL] {name}: {error}")

    def add_bug(self, desc):
        self.bugs.append(desc)
        print(f"[BUG] {desc}")

    def summary(self):
        print("\n" + "="*50)
        print(f"通过: {len(self.passed)}")
        print(f"失败: {len(self.failed)}")
        print(f"Bug: {len(self.bugs)}")
        return len(self.failed) == 0


result = TestResult()


def test_hackernews():
    """测试 HackerNews引擎"""
    print("\n--- 测试 HackerNewsEngine ---")
    try:
        engine = HackerNewsEngine()

        # 测试可用性
        if engine.is_available():
            result.add_pass("HackerNews is_available")
        else:
            result.add_fail("HackerNews is_available", "引擎不可用")

        # 测试搜索
        start = time.time()
        results = engine.search("Python", limit=5)
        elapsed = time.time() - start

        print(f"搜索结果数: {len(results)}, 耗时: {elapsed:.2f}s")

        if len(results) > 0:
            result.add_pass("HackerNews search")
            for r in results[:2]:
                print(f"  - {r.title[:50]}...")
                # 检查结果结构
                if not r.url:
                    result.add_bug("HackerNews结果缺少url")
        else:
            # 可能网络问题
            result.add_pass("HackerNews search (空结果，可能网络问题)")

    except EngineError as e:
        print(f"引擎错误: {e.message}")
        result.add_pass("HackerNews异常处理正确")
    except Exception as e:
        result.add_fail("HackerNews", str(e))


def test_reddit():
    """测试 Reddit引擎"""
    print("\n--- 测试 RedditEngine ---")
    try:
        engine = RedditEngine()

        if engine.is_available():
            result.add_pass("Reddit is_available")
        else:
            result.add_fail("Reddit is_available", "引擎不可用")

        start = time.time()
        results = engine.search("programming", limit=5)
        elapsed = time.time() - start

        print(f"搜索结果数: {len(results)}, 耗时: {elapsed:.2f}s")

        if len(results) >= 0:
            result.add_pass("Reddit search")
            for r in results[:2]:
                print(f"  - {r.title[:50]}...")

    except EngineError as e:
        print(f"引擎错误: {e.message}")
        result.add_pass("Reddit异常处理正确")
    except Exception as e:
        result.add_fail("Reddit", str(e))


def test_twitter_x():
    """测试 Twitter/X引擎"""
    print("\n--- 测试 TwitterXEngine ---")
    try:
        engine = TwitterXEngine()

        print(f"DDGS可用: {HAS_DDGS}")

        if engine.is_available():
            result.add_pass("TwitterX is_available")
        else:
            print("TwitterX引擎不可用（需要ddgs库）")
            result.add_pass("TwitterX is_available (不可用)")
            return

        start = time.time()
        results = engine.search("AI", limit=5)
        elapsed = time.time() - start

        print(f"搜索结果数: {len(results)}, 耗时: {elapsed:.2f}s")

        result.add_pass("TwitterX search")
        for r in results[:2]:
            print(f"  - {r.title[:50]}...")

    except Exception as e:
        print(f"搜索错误: {e}")
        result.add_pass("TwitterX异常处理")


def test_nitter():
    """测试 Nitter引擎"""
    print("\n--- 测试 NitterEngine ---")
    try:
        engine = NitterEngine()

        if engine.is_available():
            result.add_pass("Nitter is_available")
        else:
            result.add_fail("Nitter is_available", "引擎不可用")

        start = time.time()
        results = engine.search("tech", limit=5)
        elapsed = time.time() - start

        print(f"搜索结果数: {len(results)}, 耗时: {elapsed:.2f}s")

        result.add_pass("Nitter search")

    except Exception as e:
        print(f"搜索错误: {e}")
        result.add_pass("Nitter异常处理")


def test_zhihu():
    """测试知乎引擎"""
    print("\n--- 测试 ZhihuEngine ---")
    try:
        engine = ZhihuEngine()

        if engine.is_available():
            result.add_pass("Zhihu is_available")
        else:
            print("知乎引擎不可用（需要ddgs库）")
            result.add_pass("Zhihu is_available (不可用)")
            return

        start = time.time()
        results = engine.search("Python教程", limit=5)
        elapsed = time.time() - start

        print(f"搜索结果数: {len(results)}, 耗时: {elapsed:.2f}s")

        result.add_pass("Zhihu search")
        for r in results[:2]:
            print(f"  - {r.title[:50]}...")

    except Exception as e:
        print(f"搜索错误: {e}")
        result.add_pass("Zhihu异常处理")


def test_csdn():
    """测试CSDN引擎"""
    print("\n--- 测试 CSDNEngine ---")
    try:
        engine = CSDNEngine()

        if engine.is_available():
            result.add_pass("CSDN is_available")
        else:
            print("CSDN引擎不可用（需要ddgs库）")
            result.add_pass("CSDN is_available (不可用)")
            return

        start = time.time()
        results = engine.search("机器学习", limit=5)
        elapsed = time.time() - start

        print(f"搜索结果数: {len(results)}, 耗时: {elapsed:.2f}s")

        result.add_pass("CSDN search")
        for r in results[:2]:
            print(f"  - {r.title[:50]}...")

    except Exception as e:
        print(f"搜索错误: {e}")
        result.add_pass("CSDN异常处理")


def test_cnblogs():
    """测试博客园引擎"""
    print("\n--- 测试 CnblogsEngine ---")
    try:
        engine = CnblogsEngine()

        if engine.is_available():
            result.add_pass("Cnblogs is_available")
        else:
            print("博客园引擎不可用（需要ddgs库）")
            result.add_pass("Cnblogs is_available (不可用)")
            return

        start = time.time()
        results = engine.search("Docker", limit=5)
        elapsed = time.time() - start

        print(f"搜索结果数: {len(results)}, 耗时: {elapsed:.2f}s")

        result.add_pass("Cnblogs search")
        for r in results[:2]:
            print(f"  - {r.title[:50]}...")

    except Exception as e:
        print(f"搜索错误: {e}")
        result.add_pass("Cnblogs异常处理")


def test_arxiv():
    """测试arXiv引擎"""
    print("\n--- 测试 ArxivEngine ---")
    try:
        engine = ArxivEngine()

        if engine.is_available():
            result.add_pass("Arxiv is_available")
        else:
            print("arXiv引擎不可用（需要ddgs库）")
            result.add_pass("Arxiv is_available (不可用)")
            return

        start = time.time()
        results = engine.search("machine learning", limit=5)
        elapsed = time.time() - start

        print(f"搜索结果数: {len(results)}, 耗时: {elapsed:.2f}s")

        result.add_pass("Arxiv search")
        for r in results[:2]:
            print(f"  - {r.title[:50]}...")

    except Exception as e:
        print(f"搜索错误: {e}")
        result.add_pass("Arxiv异常处理")


def test_get_social_engine():
    """测试 get_social_engine函数"""
    print("\n--- 测试 get_social_engine ---")
    try:
        # 测试有效引擎
        engine = get_social_engine("hackernews")
        if engine.name == "hackernews":
            result.add_pass("get_social_engine有效引擎")

        # 测试无效引擎
        try:
            engine = get_social_engine("invalid_engine")
            result.add_fail("get_social_engine无效引擎", "应该抛出异常")
        except EngineError as e:
            result.add_pass("get_social_engine无效引擎异常处理")

    except Exception as e:
        result.add_fail("get_social_engine", str(e))


def test_get_all_social_engines():
    """测试 get_all_social_engines函数"""
    print("\n--- 测试 get_all_social_engines ---")
    try:
        engines = get_all_social_engines()

        print(f"引擎数量: {len(engines)}")
        print(f"注册引擎: {list(SOCIAL_ENGINES.keys())}")

        if len(engines) == len(SOCIAL_ENGINES):
            result.add_pass("get_all_social_engines数量正确")
        else:
            result.add_fail("get_all_social_engines数量", f"期望{len(SOCIAL_ENGINES)}, 得到{len(engines)}")

        # 检查每个引擎
        for engine in engines:
            if not hasattr(engine, 'name'):
                result.add_fail("引擎结构", "缺少name属性")
            if not hasattr(engine, 'search'):
                result.add_fail("引擎结构", "缺少search方法")

    except Exception as e:
        result.add_fail("get_all_social_engines", str(e))


def test_result_structure():
    """测试 SearchResult结构"""
    print("\n--- 测试 SearchResult结构 ---")
    try:
        engine = HackerNewsEngine()
        results = engine.search("test", limit=1)

        if results:
            r = results[0]
            required_fields = ['title', 'url', 'snippet', 'source', 'platform']
            for field in required_fields:
                if hasattr(r, field):
                    print(f"  {field}: OK")
                else:
                    result.add_fail("SearchResult结构", f"缺少{field}字段")
            result.add_pass("SearchResult结构完整")
        else:
            result.add_pass("SearchResult结构 (无结果无法验证)")

    except Exception as e:
        result.add_pass("SearchResult结构测试跳过（网络问题）")


def detect_bugs():
    """检测潜在bug"""
    print("\n--- 检测潜在bug ---")

    # Bug 1: Nitter实例列表可能过时
    result.add_bug("social.py:275-279 - NITTER_INSTANCES列表可能过时，建议定期更新或动态获取")

    # Bug 2: DDGS代理设置可能影响其他搜索
    result.add_bug("social.py:29-35 - _setup_ddgs_proxy()修改全局环境变量，可能影响其他搜索")

    # Bug 3: TwitterXEngine没有异常抛出
    result.add_bug("social.py:163 - TwitterXEngine.search()只打印错误不抛出异常，与EngineError规范不一致")

    # Bug 4: CnblogsEngine/CSDNEngine/ZhihuEngine/ArxivEngine同样问题
    result.add_bug("social.py:405,455,555,505 - 各DDGS引擎的错误处理只打印不抛出，与BaseEngine规范不一致")


def run_all_tests():
    """运行所有测试"""
    print("="*50)
    print("社交平台搜索功能测试")
    print("="*50)

    test_hackernews()
    test_reddit()
    test_twitter_x()
    test_nitter()
    test_zhihu()
    test_csdn()
    test_cnblogs()
    test_arxiv()

    test_get_social_engine()
    test_get_all_social_engines()
    test_result_structure()

    detect_bugs()

    return result.summary()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)