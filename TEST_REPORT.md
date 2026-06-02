# Search-MCP 测试报告与优化方案

## 测试概述

测试日期: 2026-04-10
项目位置: D:\search-mcp
测试方式: Agent Team 并行测试 + 手动验证

---

## 一、发现的Bug与修复

### Bug #1: 系统代理设置干扰HTTP请求 (严重)

**问题描述:**
`requests`库默认启用`trust_env=True`，会自动从系统环境读取代理设置。即使环境变量中没有配置代理，Windows系统代理设置仍然会影响HTTP请求，导致连接失败。

**影响范围:**
- `search_tool/engines/social.py` - HackerNewsEngine, RedditEngine, NitterEngine
- `search_tool/engines/news.py` - NewsEngine._parse_rss, WebNewsScraper
- `search_tool/utils/health.py` - HealthChecker._check_url_sync
- `search_tool/research.py` - DeepResearchAgent._fetch_url_content

**修复方案:**
使用`get_session()`函数创建Session对象，当没有配置代理时设置`trust_env=False`来禁用系统代理检测。

**修复状态:** ✅ 已修复

**修复代码示例:**
```python
# 修复前
response = requests.get(url, proxies=get_proxies(), timeout=timeout)

# 修复后
session = get_session()
response = session.get(url, timeout=timeout)
```

---

## 二、测试结果汇总

| 模块 | 状态 | 发现问题 | 备注 |
|------|------|----------|------|
| DuckDuckGoEngine | ✅ 通过 | 无 | 基本功能正常 |
| NewsEngine | ✅ 通过 | 代理问题(已修复) | RSS解析正常 |
| HackerNewsEngine | ✅ 通过 | 代理问题(已修复) | Algolia API正常 |
| RedditEngine | ⚠️ 部分通过 | old.reddit.com可能被限制 | 需要更多测试 |
| ZhihuEngine/CSDN/Cnblogs | ✅ 通过 | 无 | 依赖ddgs库 |
| TwitterXEngine/NitterEngine | ⚠️ 部分通过 | Nitter实例不稳定 | 需要维护实例列表 |
| SearchCache | ✅ 通过 | 无 | TTL过期机制正常 |
| HealthChecker | ✅ 通过 | 代理问题(已修复) | 12/14源健康 |
| KeywordExpander | ✅ 通过 | 无 | 中英文扩展正常 |
| DeepResearch | ✅ 通过 | 代理问题(已修复) | 需要API Key |
| async_api | ✅ 通过 | 无 | 并发搜索正常 |
| QualityScorer | ✅ 通过 | 无 | 边界情况处理正常 |

---

## 三、优化方案建议

### 1. 架构优化

#### 1.1 统一HTTP客户端
**现状:** 代码中混用`requests.get()`和`session.get()`
**建议:** 创建统一的HTTP客户端管理类，所有HTTP请求都通过统一入口

```python
# 建议新增: search_tool/utils/http_client.py
class HttpClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._session = None
        return cls._instance
    
    @property
    def session(self):
        if self._session is None:
            self._session = get_session()
        return self._session
    
    def get(self, url, **kwargs):
        return self.session.get(url, **kwargs)
```

#### 1.2 引擎注册机制优化
**现状:** 社交引擎使用字典硬编码注册
**建议:** 使用装饰器模式实现自动注册

```python
# 建议实现
class EngineRegistry:
    _engines = {}
    
    @classmethod
    def register(cls, name):
        def decorator(engine_class):
            cls._engines[name] = engine_class
            return engine_class
        return decorator
    
    @classmethod
    def get(cls, name):
        return cls._engines.get(name)

@EngineRegistry.register('hackernews')
class HackerNewsEngine(BaseEngine):
    ...
```

### 2. 性能优化

#### 2.1 RSS源并行获取
**现状:** RSS源串行获取，耗时长
**建议:** 使用`asyncio.gather()`并行获取

```python
# 建议优化
async def _fetch_all_rss_async(self):
    tasks = [self._parse_rss_async(url, name) for name, url in self.RSS_SOURCES.items()]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    ...
```

#### 2.2 缓存优化
**现状:** 仅内存缓存，重启后丢失
**建议:** 添加持久化缓存支持

```python
# 建议新增
class PersistentCache(SearchCache):
    def __init__(self, cache_file: Path = None):
        super().__init__()
        self.cache_file = cache_file or Path.home() / ".search_mcp_cache.json"
        self._load_from_disk()
    
    def _load_from_disk(self):
        if self.cache_file.exists():
            import json
            with open(self.cache_file) as f:
                data = json.load(f)
                ...
```

#### 2.3 连接池复用
**现状:** 每次请求可能创建新连接
**建议:** 使用全局Session对象复用连接

### 3. 错误处理优化

#### 3.1 重试机制
**现状:** 无自动重试，一次失败即返回错误
**建议:** 添加指数退避重试

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def search_with_retry(self, query: str, limit: int = 10):
    return self.search(query, limit)
```

#### 3.2 优雅降级
**现状:** 单个源失败可能导致整体失败
**建议:** 实现多源备份和优雅降级

### 4. 功能增强建议

#### 4.1 添加更多搜索引擎
- Google Custom Search API (需要API Key)
- Bing Web Search API (需要API Key)
- SearXNG (开源元搜索引擎)

#### 4.2 添加更多RSS源
- GitHub Trending
- ProductHunt
- Dev.to
- Medium

#### 4.3 增强社交媒体支持
- Mastodon API
- LinkedIn (需要认证)
- Discord社区搜索

#### 4.4 添加结果去重和合并
**现状:** 简单URL去重
**建议:** 基于内容相似度的智能去重

```python
from difflib import SequenceMatcher

def content_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def smart_deduplicate(results: List[SearchResult], threshold: float = 0.8):
    # 基于标题和内容相似度去重
    ...
```

### 5. 代码质量改进

#### 5.1 类型注解完善
**现状:** 部分函数缺少类型注解
**建议:** 添加完整的类型注解

```python
def search(
    self, 
    query: str, 
    limit: int = 10
) -> List[SearchResult]:
    ...
```

#### 5.2 单元测试覆盖
**现状:** 测试文件存在但不完整
**建议:** 提高测试覆盖率到80%+

```python
# 建议新增测试
def test_duckduckgo_empty_query():
    engine = DuckDuckGoEngine()
    with pytest.raises(EngineError):
        engine.search("", limit=10)

def test_cache_expiry():
    cache = SearchCache(default_ttl=1)
    cache.set("test", "q", 10, [{"title": "test"}])
    time.sleep(2)
    assert cache.get("test", "q", 10) is None
```

#### 5.3 日志系统
**现状:** 使用print输出错误信息
**建议:** 使用标准logging模块

```python
import logging
logger = logging.getLogger(__name__)

# 替换 print(f"Error: {e}") 为
logger.error(f"Search failed: {e}")
```

### 6. MCP工具增强

#### 6.1 添加批量搜索工具
```python
@mcp.tool()
async def batch_search(queries: List[str], engines: List[str] = None) -> Dict[str, List[Dict]]:
    """批量搜索多个查询"""
    ...
```

#### 6.2 添加搜索历史工具
```python
@mcp.tool()
async def get_search_history(limit: int = 10) -> List[Dict]:
    """获取搜索历史"""
    ...
```

#### 6.3 添加源管理工具
```python
@mcp.tool()
async def enable_source(source_name: str) -> bool:
    """启用特定搜索源"""
    ...

@mcp.tool()
async def disable_source(source_name: str) -> bool:
    """禁用特定搜索源"""
    ...
```

---

## 四、优先级建议

| 优先级 | 优化项 | 预期收益 |
|--------|--------|----------|
| P0 | 修复代理问题 | 已完成 |
| P1 | 添加重试机制 | 提高稳定性 |
| P1 | 统一HTTP客户端 | 减少代码重复 |
| P2 | RSS并行获取 | 提升性能50%+ |
| P2 | 日志系统 | 提高可调试性 |
| P2 | 持久化缓存 | 改善用户体验 |
| P3 | 类型注解完善 | 代码质量 |
| P3 | 测试覆盖率提升 | 代码质量 |

---

## 五、总结

Search-MCP是一个功能完整的MCP搜索工具，经过测试发现并修复了一个严重的代理设置问题。主要模块功能正常，代码架构清晰。建议按照优先级列表逐步实施优化方案，重点关注稳定性和性能提升。