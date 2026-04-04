# Search MCP

一个基于 MCP (Model Context Protocol) 的搜索工具，支持网页、新闻、社交媒体等多源搜索。

## 功能

- **web_search** - 综合搜索（网页、新闻、社交媒体）
- **search_web** - DuckDuckGo 网页搜索
- **search_news** - 新闻搜索
- **search_social** - 社交媒体搜索（知乎、CSDN、博客园、Reddit、HackerNews、arXiv 等）
- **fetch_content** - 抓取网页正文内容，自动提取主要内容区域
- **get_latest_news** - 获取最新新闻头条
- **list_engines** - 列出所有可用的搜索引擎

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

# 安装依赖
pip install -r requirements.txt

# 安装 playwright 浏览器（可选，用于部分功能）
playwright install chromium
```

## 配置到 Claude Code

在 `~/.claude/settings.json` 中添加：

```json
{
  "mcpServers": {
    "search-tool": {
      "command": "python",
      "args": ["<path-to-search-mcp>/mcp_server.py"],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

或使用虚拟环境的 Python：

```json
{
  "mcpServers": {
    "search-tool": {
      "command": "<path-to-search-mcp>/venv/Scripts/python.exe",
      "args": ["<path-to-search-mcp>/mcp_server.py"]
    }
  }
}
```

配置后重启 Claude Code 即可使用。

## 使用示例

```
# 网页搜索
web_search("Python tutorial")

# 新闻搜索
web_search("AI news", engine="news")

# 社交媒体搜索
search_social("hot topics", platform="hackernews")
search_social("机器学习", platform="zhihu")

# 抓取网页内容
fetch_content("https://example.com/article")

# 获取最新新闻
get_latest_news(limit=10)
```

## 依赖

- duckduckgo-search
- requests
- beautifulsoup4
- lxml
- feedparser
- newspaper3k
- playwright
- click
- rich
- fake-useragent
- mcp

## License

MIT