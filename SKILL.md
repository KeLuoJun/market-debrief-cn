---
name: market-debrief-cn
description: |
  A股收盘后深度日报自动生成工具。自动采集当日行情数据（AkShare）和新闻事件（Tavily），
  通过多 Agent 并行分析架构（宏观+情绪 / 板块+资金 / 技术+估值+预判），
  生成一份带量化锚点和独立判断的交互式 HTML 日报。
  固定 Financial Times 三文鱼粉风格，6个分析模块 + 顶部仪表盘横条。
  当用户提到以下内容时触发：「A股日报」「市场复盘」「盘脉日报」「A股复盘」「今日市场分析」
  「跑一期日报」「生成日报」「做今天的复盘」，或指定日期如「帮我做2026年3月11日的日报」。
---

# A股深度日报生成器

> 核心目标不是「描述今天发生了什么」，而是「理解今天市场在定价什么、定价是否合理、明天可能发生什么」。

## 执行流程

```
Phase 1: 确认日期 → 数据采集（akshare + tavily）
Phase 2: 三个 Subagent 并行分析
Phase 3: 渲染 Agent 整合输出 HTML
```

---

## Phase 1: 数据采集（主协调 Agent）

### Step 1: 确认目标日期

解析用户意图，确认目标交易日期。默认为最近一个已收盘的交易日。

### Step 2: 运行数据采集脚本

```bash
python scripts/fetch_market_data.py --date YYYYMMDD
```

脚本自动拉取 11 类数据（详见 `references/akshare-api.md`）：

- 指数日线（6大指数近一年）、指数PE估值、全A PB
- 全市场资金流向（超大/大/中/小单）、行业资金流向
- 涨停池/跌停池/炸板池/强势连板股
- 北向资金、两融余额、国债收益率、龙虎榜

脚本**自动写入** `assets/market_data_YYYY-MM-DD.json`（assets/ 目录不存在时自动创建）。

⚠️ 东方财富数据源偶尔限流导致个别接口失败（返回空数组）——脚本已内置容错，失败项会在 stderr 显示 `[WARN]`，并记录在输出 JSON 的 `_failed_items` 字段中。若关键数据缺失，可等待 10 秒后重跑。

### Step 3: 搜索新闻事件

使用 Tavily 搜索当日关键事件，自动执行 4 组查询，覆盖：A股政策新闻、板块热点、隔夜外盘、宏观经济数据。

**Windows（推荐，跨平台）**：

```bash
python scripts/search_news.py --date YYYY-MM-DD
```

**Linux / macOS**：

```bash
bash scripts/search_news.sh '{"date": "YYYY-MM-DD"}'
```

两个脚本输出格式完全相同，**自动写入** `assets/news_data_YYYY-MM-DD.json`，失败的查询记录在 `_failed_queries` 字段。

⚠️ 需要 Tavily API token。优先级：`TAVILY_API_KEY` 环境变量（支持 `tvly-...` 格式）→ `~/.mcp-auth/` JWT 缓存。若两者均不可用，脚本会报错退出——必须先解决认证问题再继续（见 Step 4 双源要求）。

### Step 3.5: 运行量化分析引擎（新增）

在完成行情数据采集后，运行分析脚本对原始数据做预处理，输出结构化量化指标：

```bash
python scripts/analyze_market.py --date YYYYMMDD
```

脚本**自动写入** `assets/analysis_YYYY-MM-DD.json`，包含：

| 模块        | 预计算内容                                                               |
| ----------- | ------------------------------------------------------------------------ |
| 情绪评分    | 综合分（0-100）、散户/机构拆解分、各分项得分、60日成交额百分位           |
| 技术矩阵    | 6指数 MA5/10/20/60/120/250 值及偏离度、均线排列判断、量比、K线形态识别   |
| 支撑/压力位 | MA位/斐波那契38.2%/50%/61.8%/VWAP30日/整数关口，距当前价%标注            |
| 涨跌拆解    | 隔夜涨幅=开盘/前收-1（反映消息面）、日内涨幅=收盘/开盘-1（反映盘中行为） |
| 行业分析    | 四分类强弱表、成长/价值均涨幅差、资金净流入 TOP3/BOTTOM3 行业            |
| 涨停生态    | 封板率、连板分布、最高连板数+名称、主题集中度、赚钱效应评级              |
| 资金结构    | 超大/大/中/小单净流入（亿元）、机构/散户行为类型判断、资金迁移类型       |
| 估值 & ERP  | 各指数 PE 历史百分位、全A PB、ERP%（含60日均值/标准差/信号）             |
| 北向资金    | 当日净额、20日序列、20日累计、趋势描述                                   |

若脚本运行失败（`numpy`/`pandas` 未安装等），可跳过此步——AI 将从原始 market_data JSON 直接分析，但准确度会有所下降。依赖：`pip install numpy pandas`

### Step 4: 准备数据包

读取 `assets/market_data_YYYY-MM-DD.json`、`assets/analysis_YYYY-MM-DD.json` 和 `assets/news_data_YYYY-MM-DD.json`，构建三个 Subagent 的数据子集。

**⚠️ 双源强制要求**：三个 Subagent 必须同时持有 akshare 行情数据和 tavily 新闻数据。若 `news_data` 文件不存在或为空，必须先执行 Step 3 搜索新闻，**不允许**跳过新闻采集直接进入 Phase 2。两类数据是报告深度的双支柱，缺少任一类都会导致分析仅停留在数字描述层面。

**检查采集状态**：

- 若 `market_data["_failed_items"]` 非空，记录失败项列表（例：`["index pe", "lhb"]`）
- 若 `news_data["_failed_queries"] > 0`，记录失败查询数
- 将以上信息汇总为 `data_warnings` 传递给渲染 Agent，用于最终回复告知用户

---

## Phase 2: 三 Subagent 并行分析

**使用 subagent 并行启动三个分析任务**。每个 subagent 的 prompt 包含：角色定义 + 对应数据子集 + 分析任务清单 + 输出格式。

分析框架详见 → `references/analysis-framework.md`

**所有 Subagent 的核心输出要求**：除了量化数据字段，每个模块必须输出 `analysis_text` 叙述字段（见 analysis-framework.md 各 Subagent JSON schema）。叙述字段必须双源融合——同时引用 akshare 数字和 tavily 新闻事件，推断市场参与者动机，不只描述现象。

### Subagent A: 宏观事件解读师 × 情绪量化分析师

**模块**: Module 1（宏观定价扫描）+ Module 2（市场情绪温度计）

**提供数据**: tavily 新闻、`analysis.sentiment`（各分项得分、综合分、散户/机构分、60日百分位）、`analysis.northbound`（趋势描述）、`market_data`（涨跌停原始数据、两融）

**核心任务**:

- 从新闻中筛选有效事件，判断定价完成度（已充分/未充分/过度）
- 更新宏观三维坐标（经济动能/流动性/风险偏好）
- **直接使用** `analysis.sentiment.composite_score` 作为综合情绪分（无需重算）
- 确认散户/机构分歧类型（使用 `analysis.sentiment.divergence_type`）
- 判断情绪趋势斜率（加速上行/高位走平/拐头下行/筑底反弹）

**输出**: JSON（结构见 analysis-framework.md「Subagent A」节）

### Subagent B: 板块策略师 × 资金流向分析师

**模块**: Module 3（板块结构性分析）+ Module 4（资金路线图）

**提供数据**: `analysis.industry`（四分类表、成长/价值风格、资金流向TOP/BOTTOM3、迁移类型）、`analysis.limit_up_ecology`（封板率、连板分布、主题集中度、赚钱效应）、`analysis.fund_structure`（机构/散户行为类型、超大单趋势）、龙虎榜

**核心任务**:

- **直接使用** `analysis.industry.heatmap` 做行业四分类（无需重算）
- **直接使用** `analysis.industry.style` 输出成长/价值量化对比
- TOP 2 板块深度解剖（驱动力/轮动周期/资金主体/持续性评级）
- **直接使用** `analysis.limit_up_ecology` 涨停板生态指标
- 基于 `analysis.fund_structure.behavior_type` + 龙虎榜席位解读资金意图

**输出**: JSON（结构见 analysis-framework.md「Subagent B」节）

- 龙虎榜席位解读

**输出**: JSON（结构见 analysis-framework.md「Subagent B」节）

### Subagent C: 技术分析师 × 估值研究员 × 情景规划师

**模块**: Module 5（技术形态与估值）+ Module 6（次日预判与历史镜像）

**提供数据**: `analysis.technical`（MA矩阵、均线排列、量比、K线形态、支撑/压力位、日内/隔夜拆解）、`analysis.valuation`（PE百分位、ERP信号）、指数原始日线序列（用于图表渲染）

**核心任务**:

- **直接使用** `analysis.technical[指数].ma_arrangement`、`ma_deviations`、`kline_pattern` 输出技术矩阵
- **直接使用** `analysis.technical[指数].supports/resistances` 列出支撑/压力位（已附计算依据）
- **直接使用** `analysis.valuation.erp.erp_signal` 输出 ERP 信号
- **直接使用** `analysis.valuation.index_pe[指数].pe_zone` 输出估值水位档位
- 基于以上量化锚点，构建三情景概率判断（概率之和=100%，各附可观测触发条件）
- 历史镜像匹配 + 上期预判回顾

**输出**: JSON（结构见 analysis-framework.md「Subagent C」节）

---

## Phase 3: 渲染 Agent 生成 HTML

收集三份 JSON 后，交给渲染 Agent。

HTML 设计规范详见 → `references/html-design-spec.md`

### 渲染要点

1. **冲突检查**：若三份 JSON 数据矛盾，以 Subagent C 数据为准
2. **统一视角**：最终报告不出现 Agent 角色名，以统一研究报告形式呈现
3. **模块标题用结论式句式**（如「资金从消费向科技大迁移，赚钱效应持续修复」）
4. **FT 风格固定**：三文鱼粉底色系（`#FAF7F2`），涨红（`#C0392B`）跌蓝深（`#1A2E3E`），espresso header（`#1C0F08`）
5. **字体**：`"Georgia", "Noto Serif SC", "PingFang SC"` 优先，展现权威感
6. **单文件输出**：不引用本地资源，ECharts 通过 CDN 加载
7. **body 最大宽度 1100px**，水平居中，内边距 48px/40px，辅助文字≥11px
8. **所有数字使用等宽字体**（`SFMono-Regular, Menlo, Consolas`）
9. **卡片圆角 12-16px**，投影 `0 4px 16px rgba(0,0,0,0.08)`
10. **必须渲染叙述区块**：每个模块必须包含来自 `analysis_text` 的 `.insight-block` 深度解读段落，禁止只渲染数字表格/图表而省略文字分析。叙述区块 CSS 组件见 `html-design-spec.md「深度叙述区块」`节。
11. **禁止排版漂移**：顶部仪表盘、图表区、表格区必须使用固定组件容器（`.dashboard-strip`、`.viz-card`、`.table-wrap`、`.chart-frame`），禁止裸露图表直接贴在模块根节点下。
12. **禁止元素重叠**：仪表盘 gauge、K 线图、Sankey、表格必须有明确高度；若数据不足导致图表拥挤，降级为 stat card / badge / 简化表，不允许文字与图表互相覆盖。
13. **响应式强制要求**：桌面端按 2-3 列信息栅格布局；当视口 < 900px 时统一降为单列，顶部指数卡改为 2 列网格，禁止 6 个指数横向挤压在一行。
14. **视觉层次强制要求**：每个模块必须遵循「标题区 → 一句话结论 → 核心图表区 → 深度解读 → 次级表格/清单」的顺序，禁止把图表、长段落、表格随机穿插。
15. **优先美观而非堆砌**：宁可减少一个次级组件，也要保证主图表和关键数字排版整齐、留白充足、模块高度均衡。

### 页面结构

```
[顶部仪表盘横条]  三行布局：品牌行 | 指数行（6个指数）| 概览行（成交/情绪/涨停/北向）
[Module 1] 宏观定价扫描       ← Subagent A
[Module 2] 市场情绪温度计     ← Subagent A
[Module 3] 板块结构性分析     ← Subagent B
[Module 4] 资金路线图         ← Subagent B
[Module 5] 技术形态与估值     ← Subagent C
[Module 6] 次日预判与历史镜像 ← Subagent C
[页脚] 数据来源声明 + 免责声明
```

### 可视化清单（强制要求）

| 模块 | 图表                                               | 引擎                | 尺寸          | 交互               |
| ---- | -------------------------------------------------- | ------------------- | ------------- | ------------------ |
| M1   | 事件定价状态徽章表                                 | CSS badge           | —             | —                  |
| M1   | 外盘市场胶囊行                                     | CSS pill            | —             | —                  |
| M2   | 综合情绪仪表盘（大） + 散户/机构仪表盘（小×2）     | ECharts gauge       | 350px / 220px | tooltip            |
| M2   | 5日情绪折线（含markArea过热区）                    | ECharts line        | 200px mini    | hover              |
| M2   | 分项评分进度条表                                   | CSS                 | —             | —                  |
| M3   | 行业涨跌幅横向条形图（全行业排序）                 | ECharts bar         | tall 460px    | dataZoom+tooltip   |
| M3   | 轮动5阶段进度条（含脉冲动画）                      | CSS                 | —             | —                  |
| M3   | 涨停生态雷达图                                     | ECharts radar       | half 280px    | tooltip            |
| M4   | 资金结构分组柱状图（四类资金）                     | ECharts bar         | full 380px    | tooltip            |
| M4   | 主力资金30日走势折线                               | ECharts line        | mini 200px    | hover              |
| M4   | 资金迁移桑基图                                     | ECharts sankey      | full 380px    | emphasis adjacency |
| M5   | K线图（60日，含MA5/20/60+量能附图，Tab切换三指数） | ECharts candlestick | tall 460px    | dataZoom+tab       |
| M5   | 多指数PE百分位彩色轨道（4条）                      | CSS                 | —             | hover data-pct     |
| M5   | ERP双轴折线（近2年）                               | ECharts line        | full 380px    | tooltip markLine   |
| M6   | 三情景概率分段条                                   | CSS                 | 44px          | —                  |
| M6   | 情景卡片accordion（3张可展开）                     | HTML/CSS/JS         | —             | click toggle       |
| M6   | 观测清单交互表（优先级badge）                      | CSS badge+table     | —             | —                  |

**原则**：每个模块至少含 **2个** 可视化组件（图表或交互组件），禁止出现纯文字罗列的模块。

### 输出文件

将最终 HTML 写入**项目根目录**：

```
market-debrief-YYYY-MM-DD.html
```

> 数据中间产物继续存放于 `assets/`，最终成品 HTML 单独放在项目根目录，便于直接预览、分享和版本比对：
>
> - `assets/market_data_YYYY-MM-DD.json` — 原始行情数据
> - `assets/analysis_YYYY-MM-DD.json` — 量化指标分析结果（新）
> - `assets/news_data_YYYY-MM-DD.json` — 新闻搜索结果
> - `market-debrief-YYYY-MM-DD.html` — 最终日报

**输出动作要求**：渲染完成后，必须显式执行“写入项目根目录 HTML 文件”这一步，不允许把最终 HTML 留在 `assets/`、临时目录或对话内联代码块中。

---

## 内容质量红线

**禁用表达**（出现即重写）：

| ❌ 禁止          | ✅ 替代                                  |
| ---------------- | ---------------------------------------- |
| 市场情绪有所回暖 | 情绪综合分从52升至65                     |
| 需关注风险       | 若明日上证跌破4050（MA20），触发悲观情景 |
| 可能震荡上行     | 核心情景（60%）：上证4100-4160区间震荡   |
| 技术面显示支撑   | MA60（3980点）构成近期强支撑，距当前3.8% |
| 资金面较为活跃   | 今日成交1.06万亿，为20日均值的1.12倍     |

**每期必含量化锚点**：

1. 情绪综合分（含散户/机构拆解）
2. 资金迁移净额
3. 沪深300 PE 历史百分位
4. 关键支撑/压力位 + 计算依据
5. 三情景概率（和=100%）+ 触发条件
6. 上期预判准确度（若有）

---

## 语言规范

**先说好还是不好，再说为什么。** 每个模块标题和首句即结论。

**保留英文**：PE、PB、ERP、MA、ETF、MLF、EPS、ROE、CPI、PMI

**必须中文**：所有分析结论、图表标题、评价性用语、方向性判断

**禁止出现**：「总而言之」「需要指出的是」「值得注意的是」「总体来看」「综上所述」

---

## 数据失败项告知（必须执行）

生成报告完毕后，在最终回复中**必须以中文明确告知用户**：

1. **若所有数据均采集成功**：说明「本期数据采集完整，所有 11 类行情数据和新闻查询均成功」
2. **若存在失败项**：列出具体失败内容，例如：

   > ⚠️ 本期数据采集部分失败，以下内容未能获取，相关模块分析准确度可能受影响：
   >
   > - **行情数据**：龙虎榜（lhb）、指数PE（index pe）
   > - **新闻查询**：2/4 个查询无有效返回

**来源**：读取 `assets/market_data_YYYY-MM-DD.json` 中的 `_failed_items` 字段，以及 `assets/news_data_YYYY-MM-DD.json` 中的 `_failed_queries` 字段。

---

## 参考文件索引

| 需要什么                            | 去哪找                             |
| ----------------------------------- | ---------------------------------- |
| AkShare 接口参数与字段              | `references/akshare-api.md`        |
| 六模块分析框架 + Subagent JSON 格式 | `references/analysis-framework.md` |
| HTML 设计规范 + 色彩/排版/组件      | `references/html-design-spec.md`   |

## 脚本索引

| 脚本                           | 用途                                              | 依赖             |
| ------------------------------ | ------------------------------------------------- | ---------------- |
| `scripts/fetch_market_data.py` | AkShare 行情原始数据一键采集 → JSON               | akshare, pandas  |
| `scripts/analyze_market.py`    | 量化指标计算引擎：情绪/技术/估值/行业/资金 → JSON | numpy, pandas    |
| `scripts/search_news.py`       | Tavily 新闻搜索 → JSON（Windows / 跨平台推荐）    | requests, Tavily |
| `scripts/search_news.sh`       | Tavily 新闻搜索 → JSON（Linux / macOS）           | jq, curl, Tavily |

依赖安装：`pip install akshare numpy pandas requests`、`jq` + `curl`（Bash，可选）、Tavily API token（可选）
