# Market Debrief CN (盘脉) 📈

**Market Debrief CN** 是一款专为 A 股市场设计的全自动、多智能体深度复盘与分析系统。与普通的行情播报工具不同，本项目的设计哲学在于**“不仅告诉你今天发生了什么，更要解释市场在定价什么、以及明天可能发生什么”**。系统通过自动抓取量化数据与财经新闻，经过多并行 Agent 的逻辑推演后，最终自动渲染生成具有 Financial Times (FT) / Bloomberg 风格的交互式数据可视化 HTML 看板。

## ✨ 核心特性

- 🤖 **全自动驱动**：无需提供任何本地数据表。系统自动通过 `akshare` 接口拉取当日行情、板块资金、历史估值等结构化数；通过 `tavily` 搜索拉取影响盘面的宏观/产业新闻及事件。
- 🧠 **四层 Agent 架构设计**：采用“主协调 -> 三域专家 -> 渲染器”的调度模式。
  - **Orchestrator**：负责环境感知、行情与资产新闻数据打包整理。
  - **Subagent A (宏观与情绪)**：负责从噪音中抽取有效事件，分析宏观坐标与情绪温度。
  - **Subagent B (板块与资金)**：负责资金迁徙推演、驱动生命周期定位及龙虎榜资金性质解剖。
  - **Subagent C (技术、估值与情景)**：结合量价关系、历史估值极值点推演出次日的高概率多维情景。
  - **Renderer**：归纳 JSON 并最终构建交互完整的前端报表。
- 📊 **出版级数据可视化 UI**：
  - 生成原生 HTML + 纯 CSS + ECharts，不依赖外部前端框架（除CDN注入外）。
  - 支持复杂 ECharts 深度交互（自带业务说明的丰富 Tooltip，强制开启缩放 DataZoom）。
  - 强制业务层解释：图表数据拒绝“裸奔”，每个可视化面板都会由大模型自带结论性质的“叙事摘要卡片”与“名词业务解释”。
- 🧩 **六大分析模型核心框架**：
  - Module 1. 宏观定价扫描（识别主叙事）
  - Module 2. 市场情绪温度计
  - Module 3. 板块结构性分析
  - Module 4. 资金路线图与龙虎生态
  - Module 5. 技术形态与估值水位
  - Module 6. 次日预判与历史镜像

## 📂 核心目录结构

```text
market-debrief-cn/
├── SKILL.md                # AI 驱动整个工作流的主 Prompt 与执行策略限制
├── README.md               # 项目介绍文档
├── scripts/                # 爬虫与数据计算引擎
│   ├── analyze_market.py   # 量化指标清洗与特征工程脚本 (如动量计算, 量价配合等)
│   ├── fetch_market_data.py# 基于 akshare 的 A股数据爬虫节点
│   └── search_news.py      # 基于 Tavily 的信息面检索节点
└── references/             # HTML UI、图表图例规范与后端量化逻辑方法论
    ├── html-design-spec.md # 定义生成的 HTML 前端样式（CSS 栅格、Echarts 等）
    └── analysis-framework.md# AI 进行市场分析的底层经济学/量价逻辑
```

## 🔑 前提准备

### Tavily API Key 配置

本系统使用 Tavily 进行财经新闻搜索，需要配置 API Key：

1. 访问 [https://app.tavily.com/](https://app.tavily.com/) 注册账号并获取 API Key
2. 配置环境变量：
   - **Windows (PowerShell)**:
     ```powershell
     $env:TAVILY_API_KEY="tvly-你的APIKey"
     ```
   - **Windows (CMD)**:
     ```
     set TAVILY_API_KEY=tvly-你的APIKey
     ```
   - **Linux / macOS**:
     ```bash
     export TAVILY_API_KEY="tvly-你的APIKey"
     ```

> 💡 建议将上述命令添加到 shell 配置文件（如 `.bashrc`、`.zshrc` 或 PowerShell `$PROFILE`）以永久生效。

## 🚀 如何触发

当你挂载了本项目作为你的智能体基础工作区后，你可以直接使用自然语言对话触发：
- **标准指令**：`"生成今日A股日报"` / `"出一期盘脉日报"`
- **特定日期指令**：`"帮我做2025年11月10日的市场复盘"`
- **快速概览**：`"A股复盘"`

系统将自动开始执行背景抓取与子 Agent 运算，耐心等待进度指示器走完，最终直接获得一份完整的 HTML 文档供预览或发布。

## 📊 输出样例

生成结果示例：[market-debrief-2026-03-13.html](assets/market-debrief-2026-03-13.html)

