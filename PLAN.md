# Search-Tool 与 Scholar-MCP 合并优化计划

## 一、项目背景

### 1.1 问题分析

用户有两个MCP搜索工具项目：
- **search-tool** (D:\search) - 功能丰富，包含缓存、健康检测、内容提取等高级功能
- **scholar-mcp** (D:\scholar-mcp) - 结构简洁，使用真实arxiv API，已发布pip包

存在的问题：
1. 两个项目功能重叠严重 (web_search, hackernews, reddit, 中文平台, deep_research)
2. search-tool 用 DDG 站内搜索 arXiv，不如真实 API 准确
3. scholar-mcp 缺少缓存、健康检测、内容提取等高级功能
4. 项目结构不一致，不便维护和开源

### 1.2 合并目标

- 统一为一个 MCP 项目
- 功能完整不冗余
- 支持 pip/uvx 安装
- 结构清晰，易于开源

---

## 二、两个项目详细分析

### 2.1 Search-Tool MCP (D:\search)

#### 项目结构
```
D:\search\
├── search_tool/
│   ├── __init__.py
│   ├── api.py                    # 同步搜索 API
│   ├── async_api.py              # 异步搜索 API
│   ├── cli.py                    # CLI 工具
│   ├── config.py                 # 配置管理
│   ├── research.py               # 深度研究模块
│   ├── scoring.py                # 结果质量评分
│   ├── keywords.py               # 关键词扩展
│   ├── engines/
│   │   ├── base.py               # 基类
│   │   ├── search.py             # 网页搜索 (DDG)
│   │   ├── news.py               # RSS 新闻
│   │   └── social.py             # 社交媒体
│   └── utils/
│       ├── cache.py              # 缓存管理
│       ├── health.py             # 健康检测
│       ├── formatter.py          # 输出格式化
│       ├── antibot.py            # 反爬虫处理
│       └── auth.py               # 认证管理
├── mcp_server.py                 # MCP 服务器入口
├── requirements.txt
└── README.md
```

#### 工具列表 (12个)
| 工具名称 | 功能描述 |
|---------|---------|
| web_search | 综合搜索 (web/news/social/all) |
| search_web | DuckDuckGo 网页搜索 |
| search_news | RSS 新闻搜索 |
| search_social | 社交平台搜索 (hackernews/reddit/twitter/nitter/zhihu/cnblogs/csdn/arxiv) |
| fetch_content | 网页内容提取 (支持CSDN/知乎/博客园等中文网站) |
| get_latest_news | 最新新闻头条 |
| list_engines | 列出可用引擎 |
| check_health | 健康检测 |
| clear_cache | 清空缓存 |
| cache_stats | 缓存统计 |
| deep_research | AI 深度研究 |
| suggest_keywords | 关键词扩展 |

#### 核心特性
- **缓存系统**: 内存缓存，TTL 支持，命中率统计
- **健康检测**: 异步检测 RSS 源和社交平台状态
- **内容提取**: 针对中文网站优化的 CSS 选择器
- **质量评分**: 权威性/新鲜度/完整性/一致性评分
- **关键词扩展**: 中英文修饰词、技术术语提取

### 2.2 Scholar-MCP (D:\scholar-mcp)

#### 项目结构
```
D:\scholar-mcp\
├── src/
│   └── scholar_mcp/
│       ├── __init__.py
│       ├── server.py             # MCP 服务器入口
│       ├── search.py             # 搜索聚合
│       ├── company.py            # 公司动态
│       └── sources/
│           ├── arxiv.py          # arXiv 真实 API
│           ├── hackernews.py     # HackerNews (Algolia)
│           ├── reddit.py         # Reddit JSON API
│           ├── web.py            # DuckDuckGo
│           ├── news.py           # 公司新闻
│           └── cn/
│               ├── zhihu.py
│               ├── csdn.py
│               └── cnblogs.py
├── tests/
├── pyproject.toml                # pip 安装配置
└── README.md
```

#### 工具列表 (7个)
| 工具名称 | 功能描述 |
|---------|---------|
| search_arxiv | arXiv 论文搜索 (真实 API) |
| search_hackernews | HackerNews 科技热点 |
| search_reddit | Reddit 技术讨论 |
| search_web | DuckDuckGo 网页搜索 |
| search_cn | 中文平台搜索 (知乎/CSDN/博客园) |
| search_company | 公司动态搜索 |
| deep_research | AI 深度研究 |

#### 核心特性
- **arXiv 真实 API**: 使用 `arxiv` 库，不是 DDG 站内搜索
- **公司动态搜索**: 支持任意公司中英文名搜索
- **项目结构简洁**: 使用 pyproject.toml，已发布 pip 包
- **异步实现**: 使用 aiohttp 异步请求

### 2.3 功能重叠分析

| 功能 | search-tool | scholar-mcp | 重叠程度 |
|------|-------------|-------------|---------|
| 网页搜索 | web_search, search_web | search_web | 完全重叠 |
| HackerNews | search_social | search_hackernews | 完全重叠 |
| Reddit | search_social | search_reddit | 完全重叠 |
| 中文平台 | search_social | search_cn | 完全重叠 |
| arXiv | search_social (DDG) | search_arxiv (API) | 功能重叠，实现不同 |
| deep_research | 有 | 有 | 完全重叠 |
| 缓存 | 有 | 无 | search-tool 独有 |
| 健康检测 | 有 | 无 | search-tool 独有 |
| 内容提取 | 有 | 无 | search-tool 独有 |
| 公司搜索 | 无 | 有 | scholar-mcp 独有 |

---

## 三、合并后项目设计

### 3.1 项目结构

```
search-mcp/
├── pyproject.toml              # pip 安装配置
├── README.md                   # 使用文档
├── LICENSE                     # MIT 许可证
├── src/
│   └── search_mcp/
│       ├── __init__.py         # 版本导出
│       ├── server.py           # MCP 服务器入口
│       ├── config.py           # 配置管理
│       │
│       ├── sources/            # 数据源模块
│       │   ├── __init__.py
│       │   ├── base.py         # 基类 SearchResult
│       │   ├── web.py          # DuckDuckGo 搜索
│       │   ├── news.py         # RSS 新闻聚合
│       │   ├── company.py      # 公司动态搜索
│       │   │
│       │   ├── academic/       # 学术搜索
│       │   │   ├── __init__.py
│       │   │   └── arxiv.py    # arXiv 真实 API
│       │   │
│       │   ├── social/         # 社交平台
│       │   │   ├── __init__.py
│       │   │   ├── hackernews.py
│       │   │   └── reddit.py
│       │   │
│       │   └── cn/             # 中文平台
│       │       ├── __init__.py
│       │       ├── base.py     # CNSiteEngine 基类
│       │       ├── zhihu.py
│       │       ├── csdn.py
│       │       └── cnblogs.py
│       │
│       ├── utils/              # 工具模块
│       │   ├── __init__.py
│       │   ├── cache.py        # 缓存系统
│       │   ├── health.py       # 健康检测
│       │   ├── keywords.py     # 关键词扩展
│       │   └── content.py      # 内容提取
│       │
│       └── research/           # 深度研究
│           ├── __init__.py
│           └── deep_research.py
│
└── tests/
    ├── __init__.py
    ├── test_sources.py
    ├── test_utils.py
    └── test_integration.py
```

### 3.2 工具列表 (14个，去重优化)

| 工具名 | 功能 | 来源 | 变化 |
|--------|------|------|------|
| `search_web` | DuckDuckGo 网页搜索 | scholar-mcp | 保留 |
| `search_news` | RSS 新闻聚合 | search-tool | 保留 |
| `search_arxiv` | arXiv 论文 (真实 API) | scholar-mcp | **替换 DDG 站内搜索** |
| `search_hackernews` | HackerNews 科技热点 | 合并 | 保留异步实现 |
| `search_reddit` | Reddit 技术讨论 | scholar-mcp | 保留 |
| `search_cn` | 中文平台 (知乎/CSDN/博客园) | 合并 | 统一接口 |
| `search_company` | 公司动态搜索 | scholar-mcp | **新增功能** |
| `fetch_content` | 网页内容提取 | search-tool | 保留 |
| `get_latest_news` | 最新新闻头条 | search-tool | 保留 |
| `deep_research` | AI 深度研究 | 合并 | 优化实现 |
| `suggest_keywords` | 关键词扩展 | search-tool | 保留 |
| `check_health` | 源健康检测 | search-tool | **核心特性** |
| `cache_stats` | 缓存统计 | search-tool | 保留 |
| `clear_cache` | 清空缓存 | search-tool | 保留 |

**删除的工具:**
- `web_search` - 与 search_web 重复，功能合并
- `list_engines` - 功能简单，可内置到其他工具描述中

---

## 四、关键代码修改

### 4.1 合并 server.py

**源文件:**
- `D:\search\mcp_server.py`
- `D:\scholar-mcp\src\scholar_mcp\server.py`

**目标文件:** `D:\search-mcp\src\search_mcp\server.py`

**关键修改:**
1. 合并两个 TOOLS 定义，保留 14 个工具
2. 统一 call_tool 处理逻辑
3. 添加 arXiv 和 company 搜索工具处理
4. 保留内容提取功能
5. 保留缓存和健康检测功能

### 4.2 修复 arXiv 搜索

**问题:** search-tool 使用 DDG 站内搜索 arXiv，不准确

**解决方案:** 使用 scholar-mcp 的真实 arxiv 库 API

**源文件:** `D:\scholar-mcp\src\scholar_mcp\sources\arxiv.py`

**目标文件:** `D:\search-mcp\src\search_mcp\sources\academic\arxiv.py`

```python
import arxiv
from typing import List, Dict

async def search_arxiv(query: str, limit: int = 10) -> List[Dict]:
    """Search arXiv using official API."""
    search = arxiv.Search(query=query, max_results=limit, sort_by=arxiv.SortCriterion.Relevance)
    
    results = []
    for paper in search.results():
        results.append({
            "title": paper.title,
            "url": paper.entry_id,
            "snippet": paper.summary[:500],
            "source": "academic",
            "platform": "arxiv",
            "authors": [a.name for a in paper.authors],
            "published": paper.published.strftime("%Y-%m-%d"),
            "pdf_url": paper.pdf_url,
        })
    return results
```

### 4.3 统一中文平台搜索

**问题:** 两个项目都有知乎/CSDN/博客园搜索，实现类似但代码重复

**解决方案:** 创建 CNSiteEngine 基类

**目标文件:** `D:\search-mcp\src\search_mcp\sources\cn\base.py`

```python
from ddgs import DDGS
from typing import List, Dict

class CNSiteEngine:
    """Base class for Chinese site search via DDG."""
    
    def __init__(self, site: str, name: str):
        self.site = site    # e.g., "zhihu.com"
        self.name = name    # e.g., "zhihu"
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        if limit <= 0:
            return []
        
        site_query = f"{query} site:{self.site}"
        
        with DDGS() as ddgs:
            raw = ddgs.text(site_query, max_results=limit)
        
        results = []
        for r in raw or []:
            results.append({
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", "")[:300],
                "source": "cn",
                "platform": self.name,
            })
        return results

# 实例化各平台引擎
zhihu_engine = CNSiteEngine("zhihu.com", "zhihu")
csdn_engine = CNSiteEngine("csdn.net", "csdn")
cnblogs_engine = CNSiteEngine("cnblogs.com", "cnblogs")
```

### 4.4 提取内容提取模块

**问题:** _fetch_content 函数嵌入在 mcp_server.py 中，不易复用

**解决方案:** 提取为独立模块

**源文件:** `D:\search\mcp_server.py` 第 59-262 行

**目标文件:** `D:\search-mcp\src\search_mcp\utils\content.py`

**关键功能:**
1. 移除导航、脚本、样式、广告等
2. 针对中文网站优化的 CSS 选择器:
   - CSDN: `article`, `.markdown_views`, `.htmledit_views`
   - 知乎: `.RichContent-inner`, `.Post-RichText`
   - 博客园: `#cnblogs_post_body`, `.postBody`
   - 微信公众号: `#js_content`, `.rich_media_content`
   - arXiv: `.abstract`, `#abs`
3. 支持分页 (start_index 参数)
4. 错误处理和超时

### 4.5 缓存系统

**源文件:** `D:\search\search_tool\utils\cache.py`

**目标文件:** `D:\search-mcp\src\search_mcp\utils\cache.py`

**核心功能:**
```python
class SearchCache:
    def __init__(self, default_ttl: int = 300):
        self._cache: Dict[str, CacheEntry] = {}
    
    def get(self, engine: str, query: str, limit: int, platform: str = None) -> Optional[List]
    def set(self, engine: str, query: str, limit: int, data: List, platform: str = None)
    def clear(self)
    def stats(self) -> Dict

def get_cache() -> SearchCache
def clear_cache()
```

### 4.6 健康检测系统

**源文件:** `D:\search\search_tool\utils\health.py`

**目标文件:** `D:\search-mcp\src\search_mcp\utils\health.py`

**核心功能:**
```python
class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class HealthChecker:
    async def check_all(self) -> Dict[str, SourceHealth]
    def get_status(self, source_name: str) -> HealthStatus
    def should_skip(self, source_name: str) -> bool
    def get_summary(self) -> Dict

def get_health_checker() -> HealthChecker
```

### 4.7 关键词扩展模块

**源文件:** `D:\search\search_tool\keywords.py`

**目标文件:** `D:\search-mcp\src\search_mcp\utils\keywords.py`

**核心功能:**
```python
@dataclass
class KeywordSuggestion:
    original: str
    expanded: List[str]
    related: List[str]
    technical_terms: List[str]

class KeywordExpander:
    def expand(self, query: str, results: Optional[List[dict]] = None) -> KeywordSuggestion

def get_expander() -> KeywordExpander
```

---

## 五、安装部署配置

### 5.1 pyproject.toml

**目标文件:** `D:\search-mcp\pyproject.toml`

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "search-mcp"
version = "1.0.0"
description = "Unified MCP server for web search, academic research, and tech news"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"
keywords = ["mcp", "search", "arxiv", "news", "hackernews", "duckduckgo"]

dependencies = [
    "mcp>=1.0.0",
    "ddgs>=9.0.0",           # DuckDuckGo 搜索
    "arxiv>=2.0.0",          # arXiv 真实 API
    "feedparser>=6.0.0",     # RSS 解析
    "aiohttp>=3.9.0",        # 异步 HTTP
    "httpx>=0.25.0",
    "beautifulsoup4>=4.12.0",
    "lxml>=4.9.0",
    "requests>=2.31.0",
    "anthropic>=0.18.0",     # AI 分析 (可选)
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "ruff>=0.7.0",
]

[project.scripts]
search-mcp = "search_mcp.server:main"

[project.urls]
Homepage = "https://github.com/yourname/search-mcp"
Repository = "https://github.com/yourname/search-mcp"

[tool.hatch.build.targets.wheel]
packages = ["src/search_mcp"]

[tool.ruff]
line-length = 100
target-version = "py310"
```

### 5.2 安装方式

```bash
# pip 安装
pip install search-mcp

# uvx 直接运行
uvx search-mcp

# 从源码安装
pip install git+https://github.com/yourname/search-mcp.git
```

### 5.3 MCP 客户端配置

**Claude Desktop (claude_desktop_config.json):**
```json
{
  "mcpServers": {
    "search-mcp": {
      "command": "search-mcp"
    }
  }
}
```

**Claude Code:**
```bash
claude mcp add search-mcp
```

**深度研究配置 (可选):**
```json
{
  "mcpServers": {
    "search-mcp": {
      "command": "search-mcp",
      "env": {
        "ANTHROPIC_API_KEY": "your-api-key",
        "ANTHROPIC_BASE_URL": "https://api.anthropic.com"
      }
    }
  }
}
```

---

## 六、README 文档结构

**目标文件:** `D:\search-mcp\README.md`

参考 GitHub 热门 MCP 项目最佳实践，内容结构：

```markdown
# Search MCP

统一的 MCP 搜索服务器，支持网页搜索、学术文献、科技新闻、社交平台。

## 功能特性

| 工具 | 功能 | 数据源 |
|------|------|--------|
| search_web | 网页搜索 | DuckDuckGo |
| search_news | 新闻聚合 | RSS 源 |
| search_arxiv | 学术论文 | arXiv |
| search_hackernews | 科技热点 | HackerNews |
| search_reddit | 技术讨论 | Reddit |
| search_cn | 中文平台 | 知乎/CSDN/博客园 |
| search_company | 公司动态 | DuckDuckGo News |
| fetch_content | 内容提取 | 任意网页 |
| get_latest_news | 最新头条 | RSS 源 |
| deep_research | AI 深度研究 | 多源聚合 |
| suggest_keywords | 关键词扩展 | - |
| check_health | 健康检测 | - |
| cache_stats | 缓存统计 | - |
| clear_cache | 清空缓存 | - |

## 安装

## 配置

### Claude Desktop
### Claude Code
### Cursor

## 使用示例

## 环境变量

## 许可证

MIT
```

---

## 七、实现步骤

### 7.1 任务分解

| # | 任务 | 负责人 | 状态 |
|---|------|--------|------|
| 1 | 创建项目目录结构 | team-lead | 完成 |
| 2 | 完成 utils 工具模块 (cache/health/keywords) | utils-agent | 待完成 |
| 3 | 创建中文平台搜索模块 (cn/) | cn-sources-agent | 待完成 |
| 4 | 创建学术和社交搜索模块 (academic/social) | academic-social-agent | 待完成 |
| 5 | 创建基础搜索模块 (web/news/company) | web-news-agent | 待完成 |
| 6 | 提取内容提取模块 content.py | content-agent | 待完成 |
| 7 | 合并 MCP 服务器 server.py | team-lead | 待完成 |
| 8 | 创建 pyproject.toml | config-agent | 待完成 |
| 9 | 创建 README.md | readme-agent | 待完成 |
| 10 | 编写测试文件 | team-lead | 待完成 |
| 11 | Bug 检测与修复 | team-lead | 待完成 |

### 7.2 关键文件映射表

| 操作 | 源文件 | 目标文件 |
|------|--------|----------|
| 合并 server | D:\search\mcp_server.py, D:\scholar-mcp\src\scholar_mcp\server.py | src/search_mcp/server.py |
| arXiv API | D:\scholar-mcp\src\scholar_mcp\sources\arxiv.py | src/search_mcp/sources/academic/arxiv.py |
| 缓存系统 | D:\search\search_tool\utils\cache.py | src/search_mcp/utils/cache.py |
| 健康检测 | D:\search\search_tool\utils\health.py | src/search_mcp/utils/health.py |
| 关键词扩展 | D:\search\search_tool\keywords.py | src/search_mcp/utils/keywords.py |
| 公司搜索 | D:\scholar-mcp\src\scholar_mcp\sources\news.py | src/search_mcp/sources/company.py |
| 内容提取 | D:\search\mcp_server.py:_fetch_content | src/search_mcp/utils/content.py |
| pyproject | D:\scholar-mcp\pyproject.toml | pyproject.toml (扩展依赖) |
| HN 搜索 | D:\scholar-mcp\src\scholar_mcp\sources\hackernews.py | src/search_mcp/sources/social/hackernews.py |
| Reddit 搜索 | D:\scholar-mcp\src\scholar_mcp\sources\reddit.py | src/search_mcp/sources/social/reddit.py |
| Web 搜索 | D:\scholar-mcp\src\scholar_mcp\sources\web.py | src/search_mcp/sources/web.py |
| RSS 新闻 | D:\search\search_tool\engines\news.py | src/search_mcp/sources/news.py |
| 中文平台 | D:\scholar-mcp\src\scholar_mcp\sources\cn/ | src/search_mcp/sources/cn/ |

---

## 八、验证方案

### 8.1 安装测试

```bash
# 进入项目目录
cd D:/search-mcp

# 安装开发模式
pip install -e .

# 验证命令可用
search-mcp --help
```

### 8.2 工具功能测试

```python
# 测试各工具可用性
search_web("python")              # DuckDuckGo 搜索
search_arxiv("machine learning")  # arXiv 论文
search_hackernews("AI")           # HackerNews
search_reddit("programming")      # Reddit
search_cn("大模型", "zhihu")      # 知乎
search_company("OpenAI", 7)       # 公司动态
fetch_content(url)                # 内容提取
check_health()                    # 健康检测
cache_stats()                     # 缓存统计
```

### 8.3 MCP 服务器测试

```bash
# 运行 MCP 服务器
search-mcp

# 在另一个终端测试
# 使用 MCP Inspector 或 Claude Code 连接测试
```

---

## 九、GitHub 开源最佳实践参考

基于 firecrawl、exa、tavily、brave-search、duckduckgo 等热门 MCP 项目的分析：

### 9.1 项目结构最佳实践

**TypeScript 项目:**
- 使用 `@modelcontextprotocol/sdk`
- 提供 npx 直接运行方式

**Python 项目:**
- 使用 `pyproject.toml` (PEP 621)
- 提供 uvx 直接运行方式
- 配置 `[project.scripts]` entry point

### 9.2 传输模式支持

| 模式 | 说明 | 支持项目 |
|------|------|---------|
| stdio | 默认模式 | 所有项目 |
| HTTP/SSE | 远程服务器 | firecrawl, tavily, exa |
| Streamable HTTP | 新版 MCP | duckduckgo-mcp |

### 9.3 文档最佳实践

- 环境变量表格 (变量名、描述、默认值、必需)
- 多客户端配置示例 (Claude Desktop, Claude Code, Cursor)
- 使用示例代码
- 远程 MCP 服务器选项

### 9.4 部署选项

1. **本地安装**: `pip install` 或 `npx`
2. **Docker**: 提供 Dockerfile
3. **远程服务器**: 提供 HTTP 端点
4. **Smithery**: 提供 smithery.yaml

---

## 十、注意事项

1. **模型配置**: 所有 agent 使用 `glm-5` 模型 (兼容阿里云 DashScope)
2. **异步实现**: hackernews、reddit、arxiv 使用异步 aiohttp
3. **代理支持**: 从环境变量读取 HTTP_PROXY/HTTPS_PROXY
4. **错误处理**: 所有网络请求需要 try-catch
5. **依赖版本**: 保持与原项目兼容

---

## 十一、后续工作

1. 完成所有模块代码
2. 运行测试验证功能
3. 修复发现的 Bug
4. 发布到 PyPI
5. 创建 GitHub 仓库
6. 添加 CI/CD 配置
7. 编写详细使用文档