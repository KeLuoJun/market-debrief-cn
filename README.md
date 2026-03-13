# Market Debrief CN (盘脉) - Agent Skill

> A股收盘后深度复盘与日报自动生成工具

## 何时使用

当用户需要分析 A 股市场时触发此 Skill：
- **日常复盘**：`"生成今日A股日报"` / `"出一期盘脉日报"` / `"A股复盘"`
- **历史回溯**：`"帮我做2025年11月10日的市场复盘"`
- **指定日期**：`"做2026年3月12日的复盘"`

## 功能特性

- **自动数据采集**：通过 akshare 拉取行情数据，通过 Tavily 搜索财经新闻
- **多 Agent 分析**：宏观+情绪 / 板块+资金 / 技术+估值 三路并行推理
- **FT 风格输出**：生成交互式 HTML 可视化报表，包含 6 大分析模块

## 前置要求

### Tavily API Key

1. 访问 [https://app.tavily.com/](https://app.tavily.com/) 注册并获取 API Key
2. 配置环境变量：
   - **Windows (PowerShell)**: `$env:TAVILY_API_KEY="tvly-xxx"`
   - **Windows (CMD)**: `set TAVILY_API_KEY=tvly-xxx`
   - **Linux/macOS**: `export TAVILY_API_KEY="tvly-xxx"`

## 输出示例

生成结果示例：[market-debrief-2026-03-13.html](assets/market-debrief-2026-03-13.html)

