# Search MCP

一个基于 MCP (Model Context Protocol) 的统一搜索工具，支持网页、学术、新闻、社交媒体等多源搜索。

## 功能

### 搜索工具
| 工具 | 功能 |
|------|------|
| `search_web` | DuckDuckGo 网页搜索 |
| `search_news` | 新闻搜索 |
| `search_arxiv` | arXiv 学术论文搜索（真实 API） |
| `search_hackernews` | HackerNews 技术讨论 |
| `search_reddit` | Reddit 社区讨论 |
| `search_cn` | 中文平台搜索（知乎、CSDN、博客园） |
| `search_company` | 公司动态新闻 |

### 内容工具
| 工具 | 功能 |
|------|------|
| `fetch_content` | 网页正文提取 |
| `get_latest_news` | RSS 最新新闻 |
| `suggest_keywords` | 关键词扩展建议 |

### 系统工具
| 工具 | 功能 |
|------|------|
| `check_health` | 搜索源健康检测 |
| `cache_stats` | 缓存统计 |
| `clear_cache` | 清空缓存 |
| `list_engines` | 列出所有引擎 |

### 高级功能
| 工具 | 功能 |
|------|------|
| `deep_research` | AI 深度研究（多轮搜索 + AI 分析） |

## 安装

```bash
# 克隆仓库
git clone https://github.com/Michael-art-cmd/search-mcp.git
cd search-mcp

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装（editable 模式）
pip install -e .
```

## 配置

### 环境变量（可选）

深度研究功能需要设置以下环境变量：

```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY = "your-api-key"

# Linux/macOS
export ANTHROPIC_API_KEY="your-api-key"
```

代理设置（如需要）：

```bash
export HTTP_PROXY="http://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"
```

### 配置到 Claude Code

在 `~/.claude/.mcp.json` 中添加：

```json
{
  "mcpServers": {
    "search-mcp": {
      "command": "<path-to-search-mcp>/venv/Scripts/python.exe",
      "args": ["-m", "search_mcp.server"],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "HTTP_PROXY": "http://127.0.0.1:7890",
        "HTTPS_PROXY": "http://127.0.0.1:7890"
      }
    }
  }
}
```

配置后重启 Claude Code 即可使用。

## 项目结构

```
search-mcp/
├── src/search_mcp/
│   ├── server.py           # MCP 入口
│   ├── sources/            # 搜索源实现
│   │   ├── web.py          # DuckDuckGo
│   │   ├── news.py         # 新闻搜索
│   │   ├── academic/       # arXiv
│   │   ├── social/         # HackerNews, Reddit
│   │   └── cn/             # 中文平台
│   ├── utils/              # 工具函数
│   │   ├── cache.py        # 缓存系统
│   │   ├── health.py       # 健康检测
│   │   ├── fetcher.py      # 网页抓取
│   │   └── formatter.py    # 结果格式化
│   └── research/           # 深度研究
└── tests/                  # 测试文件
```

## 特性

- **智能缓存**: 自动缓存搜索结果，提升响应速度
- **健康检测**: 实时监控各搜索源状态
- **代理支持**: 支持 HTTP/HTTPS 代理
- **中文支持**: 知乎、CSDN、博客园等中文平台

## 依赖

- mcp >= 1.0.0
- ddgs >= 9.0.0
- arxiv >= 2.0.0
- aiohttp >= 3.9.0
- beautifulsoup4 >= 4.12.0
- feedparser >= 6.0.0
- requests >= 2.31.0

## License

MIT
