---
name: market-debrief-cn
description: |
  A股每日收盘深度分析报告skill。采用多Agent并行分析架构，生成具有10层分析结构的机构级HTML日报。
  核心方法论：5个专家Agent（宏观策略分析师、情绪量化分析师、板块资金分析师、技术面分析师、估值研究员）并行分析，
  由协调Agent整合为统一报告。输出为可视化可交互HTML文件，包含：
  封面仪表盘（30秒扫读版）、宏观定价扫描（事件→传导→定价完成度判断）、
  市场情绪温度计（8维量化+散户/机构拆解+5日趋势）、盘中时序解剖（6时段行为分解）、
  板块结构性分析（轮动生命周期+产业链穿透+涨停生态）、资金路线图（超大单归因+Sankey迁移图）、
  技术形态诊断（量价关系+日内/隔夜收益分解）、估值锚点追踪（PE百分位+ERP+盈利预期修正）、
  次日多情景预判（三情景+触发条件+可证伪）、历史镜像与预判验证（累计准确率自校准）。
  当用户提到以下场景时使用此skill：
  "A股日报"、"收盘分析"、"市场复盘"、"今日盘面"、"A股分析报告"、"每日收盘"、
  "市场温度计"、"资金流向分析"、"板块轮动"、"生成A股报告"、"今天市场怎么样"、
  "分析当前A股形势"、"给我看看今天的行情"、"帮我做一份股市日报"、"盘脉日报"、
  "做一份深度市场分析"、"帮我分析今天A股"、"生成市场复盘报告"。
---

# A股深度日报

> **核心理念**：从"描述今天发生了什么" → "理解今天的市场在定价什么，以及定价是否正确"

## 报告结构：10层分析框架

```
层级总览
────────────────────────────────────────────────────
 0   封面仪表盘          ← 30秒扫读版，关键数字 + 今日定性
 1   宏观定价扫描        ← 事件→传导→盘面印证的因果链
 2   市场情绪温度计      ← 8维量化评分，含散户/机构拆解+5日趋势
 3 ★ 盘中时序解剖        ← 上午/下午/尾盘三时段行为拆解
 4   板块结构性分析      ← 产业链穿透+轮动生命周期+涨停生态
 5   资金路线图          ← 超大单归因+龙虎榜席位+资金迁移图
 6   技术形态诊断        ← 量价关系+K线形态+日内/隔夜分解
 7 ★ 估值锚点追踪        ← PE百分位+ERP+盈利预期修正
 8   次日多情景预判      ← 三情景+概率+触发条件+可证伪
 9   历史镜像与预判验证  ← 类比历史期+累计准确率自校准
────────────────────────────────────────────────────
```

## 工作流程

### 步骤一：获取行情数据（增强版）

```bash
python scripts/fetch_market_data.py --output market_data.json --days 60 --top 30
```

获取：市场总貌（含集合竞价偏离、20cm涨停统计）、多指数K线（上证/深成/创业板/科创50/中证500）、行业板块、概念板块、北向资金、两融数据、龙虎榜、板块资金流向、指数估值PE/PB、涨停板生态、资金流向拆分、国债收益率。

### 步骤二：多源资讯合流与深度追踪

```bash
python scripts/fetch_news.py --output news_data.json
```

> 必须在项目根目录 `.env` 配置 `TAVILY_API_KEY`。各专家Agent在分析阶段可按需调用 Tavily（详见各Agent prompt模板）。

### 步骤三：多 Agent 深度分析（核心步骤）

采用多专家并行分析架构。读取 `market_data.json` 和 `news_data.json` 后：

#### Phase 1: 数据理解

读取所有数据，输出概览摘要（各指数涨跌、成交额、涨停数、北向资金、关键变化等）。

#### Phase 2: 分配5个专家Agent

| Agent          | 角色           | 负责Section | Prompt模板                                         |
| -------------- | -------------- | ----------- | -------------------------------------------------- |
| 宏观策略分析师 | 高盛首席策略师 | Sec 0,1,8,9 | `references/agent-prompts/macro-strategist.md`     |
| 情绪量化分析师 | 量化基金研究员 | Sec 2,3     | `references/agent-prompts/sentiment-quant.md`      |
| 板块资金分析师 | 卖方行业研究员 | Sec 4,5     | `references/agent-prompts/sector-fund.md`          |
| 技术面分析师   | 私募量化交易员 | Sec 6       | `references/agent-prompts/technical-analyst.md`    |
| 估值研究员     | 保险资管研究员 | Sec 7       | `references/agent-prompts/valuation-researcher.md` |

#### Phase 3: 并行深度分析

**每个专家Agent使用独立的subagent并行执行**（5个Agent同时启动）。

每个subagent的prompt包含：

1. 角色定义（从prompt模板读取）
2. 数据摘要（从Phase 1提取该Agent相关数据）
3. 具体分析任务（prompt模板中的任务清单）
4. 输出格式要求（JSON结构，含写作规范）

每个Agent将分析结果输出为JSON格式。

#### Phase 4: 统一综合呈现

**关键原则：最终报告不出现任何专家Agent角色名。**

协调Agent收集所有分析结果，整合为 `analysis` 对象（以下为完整结构）：

```json
{
  "dashboard": {
    "today_summary": "30字今日定性",
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "core_scenario_brief": "15字明日核心情景"
  },
  "macro": {
    "effective_events": [...],
    "macro_coordinates": {...}
  },
  "sentiment": {
    "overall_score": 65,
    "retail_score": 58,
    "institutional_score": 72,
    "indicators": [...],
    "trend_5d": [...]
  },
  "intraday": {
    "periods": [...],
    "pattern_type": "A/B/C/D",
    "anomaly_count": 15
  },
  "sectors": {
    "top_sectors": [...],
    "limit_up_ecology": {...}
  },
  "fund_flow": {
    "order_breakdown": {...},
    "migration": {...},
    "northbound": {...},
    "lhb": {...}
  },
  "technical": {
    "index_matrix": [...],
    "kline_interpretation": {...},
    "key_levels": {...},
    "volume_price": {...}
  },
  "valuation": {
    "market_valuation": [...],
    "earnings_revision": {...},
    "erp": {...}
  },
  "prediction": {
    "scenarios": [...],
    "observation_list": [...]
  },
  "history": {
    "similar_period": {...},
    "prev_validation": {...}
  }
}
```

### 步骤四：合并数据并生成报告

```python
import json

combined = {
    "date": market_data.get("date"),
    "market_data": market_data,
    "news_data": news_data,
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

| 脚本                           | 功能                                            | 主要依赖                    |
| ------------------------------ | ----------------------------------------------- | --------------------------- |
| `scripts/fetch_market_data.py` | 获取AkShare行情数据（含估值/涨停生态/资金拆分） | `akshare`, `pandas`         |
| `scripts/fetch_news.py`        | 获取Tavily宏观新闻                              | `requests`, `python-dotenv` |
| `scripts/generate_report.py`   | 生成HTML报告（10层+ECharts可视化）              | 无额外依赖                  |

安装依赖：

```bash
pip install akshare pandas requests python-dotenv
```

AkShare接口详情参见 [references/akshare-api.md](references/akshare-api.md)

---

## 分析质量要求

> 禁用表达黑名单与量化锚点要求详见 `references/analysis-methodology.md`

---

## 参考文件

| 需要什么             | 去哪找                                             |
| -------------------- | -------------------------------------------------- |
| 分析方法论           | `references/analysis-methodology.md`               |
| AkShare接口          | `references/akshare-api.md`                        |
| Tavily API参考       | `references/tavily-api.md`                         |
| HTML报告设计规范     | `references/report-design-system.md`               |
| 宏观策略Agent prompt | `references/agent-prompts/macro-strategist.md`     |
| 情绪量化Agent prompt | `references/agent-prompts/sentiment-quant.md`      |
| 板块资金Agent prompt | `references/agent-prompts/sector-fund.md`          |
| 技术面Agent prompt   | `references/agent-prompts/technical-analyst.md`    |
| 估值研究Agent prompt | `references/agent-prompts/valuation-researcher.md` |
