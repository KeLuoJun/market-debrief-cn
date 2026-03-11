# Tavily API 参考

> 用于获取实时新闻、深度研究和网页内容提取的 LLM 优化搜索 API。

## 认证

从项目根目录 `.env` 文件读取 `TAVILY_API_KEY`。API Key 从 [tavily.com](https://tavily.com) 获取。

## 三种核心能力

### 1. Search（搜索）

获取与查询相关的网页搜索结果，返回标题、摘要、URL 和相关性评分。

```python
import requests

url = "https://api.tavily.com/search"
payload = {
    "query": "今日 A股 宏观政策 央行动态",
    "max_results": 10,
    "search_depth": "advanced",   # ultra-fast / fast / basic / advanced
    "time_range": "day",           # day / week / month / year
    "include_answer": True,
}
headers = {
    "Authorization": f"Bearer {TAVILY_API_KEY}",
    "Content-Type": "application/json",
}
resp = requests.post(url, json=payload, headers=headers, timeout=30)
data = resp.json()
```

**参数说明**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `query` | string | 必填 | 搜索查询（<400字符） |
| `max_results` | int | 10 | 最大结果数（0-20） |
| `search_depth` | string | `"basic"` | 搜索深度，`advanced` 精度最高 |
| `time_range` | string | null | `day` / `week` / `month` / `year` |
| `include_answer` | bool | false | 是否返回 AI 生成的摘要答案 |
| `include_domains` | array | [] | 限定搜索域名 |
| `exclude_domains` | array | [] | 排除搜索域名 |

**返回格式**：

```json
{
  "query": "...",
  "answer": "AI生成的摘要（include_answer=true时）",
  "results": [
    {
      "title": "页面标题",
      "url": "https://...",
      "content": "提取的文本片段",
      "score": 0.85
    }
  ]
}
```

**搜索深度对比**：

| 深度 | 延迟 | 精度 | 适用场景 |
|------|------|------|---------|
| `ultra-fast` | 最低 | 较低 | 实时补充 |
| `fast` | 低 | 良好 | 快速查询 |
| `basic` | 中 | 高 | 通用搜索 |
| `advanced` | 较高 | 最高 | 深度分析（推荐） |

### 2. Extract（提取）

从指定 URL 中提取干净的文本/Markdown 内容。适合从公告链接、研报网页中提取核心数据。

```python
url = "https://api.tavily.com/extract"
payload = {
    "urls": ["https://example.com/announcement"],
    "extract_depth": "advanced",    # basic / advanced（JS页面用advanced）
    "format": "markdown",           # markdown / text
}
resp = requests.post(url, json=payload, headers=headers, timeout=60)
```

**参数说明**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `urls` | array | 必填 | 待提取的URL（最多20个） |
| `extract_depth` | string | `"basic"` | `basic` 或 `advanced`（JS页面） |
| `query` | string | null | 按相关性重排提取的内容块 |
| `chunks_per_source` | int | 3 | 每个URL返回的内容块数（1-5） |

### 3. Research（研究）

端到端的 AI 驱动研究，自动搜索多源信息并合成分析报告。

```bash
# 通过脚本调用
./scripts/research.sh '{"input": "A股新质生产力政策全面解读", "model": "pro"}'
```

或通过 Python SDK：

```python
from tavily import TavilyClient

client = TavilyClient()
result = client.research(
    input="分析沪深300估值历史百分位与盈利预期修正方向",
    model="pro"    # mini(快速) / pro(深度) / auto(自动)
)
```

**模型选择**：

| 模型 | 适用场景 | 耗时 |
|------|---------|------|
| `mini` | 单一主题快速查询 | ~30秒 |
| `pro` | 多角度综合分析 | ~60-120秒 |

## 最佳实践

1. **查询拆分**：复杂问题拆为多个子查询并行执行，效果优于一个巨型查询
2. **结果过滤**：按 `score` 字段过滤（>0.7 为高质量）
3. **并行执行**：使用 `asyncio` + `aiohttp` 并行执行多个搜索请求
4. **时效控制**：新闻类查询始终设置 `time_range: "day"`
5. **域名限定**：财经新闻优先搜索 `eastmoney.com`、`cls.cn`、`finance.sina.com.cn` 等

## 在本 Skill 中的使用场景

| 场景 | 能力 | 说明 |
|------|------|------|
| 步骤二：新闻采集 | Search | `fetch_news.py` 并行搜索宏观/政策/国际新闻 |
| 分析阶段：事件溯源 | Search + Extract | Agent 对特定政策文件、公司公告进行溯源 |
| 分析阶段：深度研究 | Research | 对复杂事件（如产业政策解读）进行多源合流分析 |
| 分析阶段：盈利修正 | Search | 搜索最新券商研报中的盈利预期调整 |
| 分析阶段：情绪探测 | Search | 搜索社交平台极端情绪信号 |

## 安装

```bash
pip install requests aiohttp python-dotenv
# 可选：使用 SDK
pip install tavily-python
```
