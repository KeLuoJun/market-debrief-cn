---
name: market-debrief-cn
description: |
  A股每日收盘深度分析报告skill，生成具有7层分析结构的专业HTML日报。
  输出为可视化可交互HTML文件，包含：宏观背景速递（事件→传导路径→盘面印证）、
  市场情绪温度计（0-100量化评分+档位判断）、板块结构性分析（驱动逻辑+资金来源识别）、
  资金路线图（北向/两融/龙虎榜精细归因）、技术形态诊断（均线+量价+K线形态）、
  次日预判（60%/25%/15%三情景置信区间）、可回测的历史对比（相似期+概率分布+预判验证）。
  当用户提到以下场景时使用此skill：
  "A股日报"、"收盘分析"、"市场复盘"、"今日盘面"、"A股分析报告"、"每日收盘"、
  "市场温度计"、"资金流向分析"、"板块轮动"、"生成A股报告"、"今天市场怎么样"、
  "分析当前A股形势"、"给我看看今天的行情"、"帮我做一份股市日报"。
---

# A股每日深度分析报告

## 工作流程

### 步骤一：获取行情数据

```bash
python scripts/fetch_market_data.py --output market_data.json --days 60 --top 30
```

获取：市场总貌、多指数K线(上证/深成/创业板/科创50)、行业板块、概念板块、北向资金、两融数据、龙虎榜、板块资金流向。

### 步骤二：获取宏观新闻（需TAVILY_API_KEY）

```bash
python scripts/fetch_news.py --output news_data.json
```

从项目根目录 `.env` 文件读取 `TAVILY_API_KEY`。若Key未配置，新闻部分显示占位提示，其他层正常生成。

### 步骤三：Claude进行7层分析

读取 `market_data.json` 和 `news_data.json`，结合数据进行分析，生成 `analysis` 对象：

```json
{
  "macro_analysis": "【事件→传导路径→盘面印证】的因果链条叙述（markdown格式）",
  "sector_analysis": "主线板块驱动逻辑、资金来源识别、产业链传导方向",
  "fund_analysis": "大单/超大单净流入拆解、主力vs散户行为判断、资金迁移路线图",
  "technical_analysis": "均线位置判断、量价关系、支撑压力位分析",
  "core_prediction": "核心情景（60%）：具体指数区间 + 依据",
  "optimistic_prediction": "乐观情景（25%）：突破条件 + 触发因子",
  "pessimistic_prediction": "悲观情景（15%）：下行风险 + 触发条件",
  "similar_periods": "当前市场与历史哪些时期最相似及依据",
  "probability_distribution": "类似历史情境下后续5/10日表现的历史频率",
  "previous_validation": "上一期（若有）预判的实际验证结果"
}
```

**分析指引：** 参见 [references/analysis-methodology.md](references/analysis-methodology.md)

### 步骤四：合并数据并生成报告

```python
import json

# 合并数据
market_data = json.load(open('market_data.json'))
news_data = json.load(open('news_data.json'))  # 若有

combined = {
    "date": market_data.get("date"),
    "market_data": market_data,
    "news_data": news_data,   # 无Tavily时可省略或传{}
    "analysis": { ... }       # 步骤三生成的analysis对象
}

json.dump(combined, open('combined.json', 'w'), ensure_ascii=False)
```

```bash
python scripts/generate_report.py --input combined.json --output market_debrief.html
```

最终输出 `market_debrief.html`，在浏览器打开即可查看完整报告。

---

## 脚本说明

| 脚本                           | 功能                | 主要依赖                    |
| ------------------------------ | ------------------- | --------------------------- |
| `scripts/fetch_market_data.py` | 获取AkShare行情数据 | `akshare`, `pandas`         |
| `scripts/fetch_news.py`        | 获取Tavily宏观新闻  | `requests`, `python-dotenv` |
| `scripts/generate_report.py`   | 生成HTML报告        | 无额外依赖                  |

安装依赖：

```bash
pip install akshare pandas requests python-dotenv
```

AkShare接口详情参见 [references/akshare-api.md](references/akshare-api.md)

---

## 分析质量要求

- **第一层**：建立"事件→传导路径→今日盘面印证"的因果链，而非列新闻清单
- **第二层**：情绪评分已脚本自动计算，Claude只需解读趋势和异常
- **第三层**：识别领涨板块是"政策催化/业绩驱动/主题炒作"，判断轮动阶段
- **第四层**：拆解资金大单/超大单，区分主力建仓vs洗盘，绘制资金迁移路线
- **第五层**：均线位置和K线形态已脚本自动识别，Claude补充支撑压力位和背离信号
- **第六层**：预判必须带具体指数区间和触发条件，不允许模糊表述如"可能震荡上行"
- **第七层**：引用历史相似时期时需说明相似的具体指标（换手率/涨停比/成交额等）
