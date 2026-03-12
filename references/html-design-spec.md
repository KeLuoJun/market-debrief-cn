# HTML 报告设计规范

> 本文件定义日报 HTML 的视觉风格、布局结构、交互组件和内容质量标准。
> 渲染 Agent 生成 HTML 时查阅此文件。

---

## 目录

1. [FT 风格色彩系统](#ft-风格色彩系统)
2. [排版规范](#排版规范)
3. [页面布局](#页面布局)
4. [顶部仪表盘横条](#顶部仪表盘横条)
5. [ECharts 图表规范](#echarts-图表规范)
6. [各模块可视化要求](#各模块可视化要求)
7. [内容质量控制](#内容质量控制)

---

## FT 风格色彩系统

固定采用 Financial Times 风格变体——三文鱼粉底色系的温暖权威感。

```css
:root {
  /* 页面色 */
  --bg-page: #FAF7F2;
  --bg-card: #FFFFFF;
  --bg-card-alt: #FFF8F0;
  --bg-header: #2C1810;

  /* 语义色 */
  --color-up: #C0392B;      /* 上涨 / 利多 / 强调 */
  --color-down: #2C3E50;    /* 下跌 / 利空 */
  --color-neutral: #95A5A6; /* 中性 / 辅助 */
  --color-warning: #E67E22; /* 警告 / 关注 */

  /* 文字色 */
  --text-primary: #1A1A1A;
  --text-secondary: #5D5D5D;
  --text-muted: #8B8B8B;
  --text-on-dark: #FAF7F2;

  /* 边框与分隔 */
  --border-light: #E8E0D8;
  --border-accent: #C0392B;

  /* 图表色板（ECharts 用） */
  --chart-1: #C0392B;
  --chart-2: #2C3E50;
  --chart-3: #E67E22;
  --chart-4: #27AE60;
  --chart-5: #8E44AD;
  --chart-6: #3498DB;
}
```

## 排版规范

```css
body {
  font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
  font-size: 15px;
  line-height: 1.7;
  color: var(--text-primary);
}

h1 { font-size: 28px; font-weight: 700; letter-spacing: -0.5px; }
h2 { font-size: 22px; font-weight: 700; border-bottom: 3px solid var(--color-up); padding-bottom: 8px; }
h3 { font-size: 17px; font-weight: 600; }

/* 辅助文字保底 11px（投屏可读） */
.caption, .footnote, .axis-label { font-size: 11px; color: var(--text-muted); }

/* 数字使用等宽字体 */
.num, .metric { font-family: "Menlo", "Consolas", monospace; font-variant-numeric: tabular-nums; }
```

## 页面布局

```css
html { background: var(--bg-page); }
body {
  max-width: 1100px;
  margin: 0 auto;
  padding: 40px;
  background: var(--bg-page);
}
```

**结构顺序**：

```
[顶部仪表盘横条]  ← 非 sticky，随页面滚动
[Module 1-6]     ← 各模块间距 48px
[页脚]           ← 数据来源声明 + 免责声明
```

每个模块用 `<section class="module">` 包裹，模块标题用**结论式句式**。

## 顶部仪表盘横条

设计要求：

```html
<header class="dashboard-strip">
  <div class="index-cards">
    <!-- 四个指数卡片：上证、深证、创指、科创50 -->
    <div class="index-card up/down">
      <span class="index-name">上证指数</span>
      <span class="index-value num">4133.43</span>
      <span class="index-change num">+0.25%</span>
    </div>
    ...
  </div>
  <div class="dashboard-meta">
    <div class="turnover">成交额: <span class="num">1.06万亿</span></div>
    <div class="emotion-bar">
      <span>情绪: </span>
      <div class="progress-bar"><div class="progress-fill" style="width:65%"></div></div>
      <span class="num">65/100 · 中性偏热</span>
    </div>
    <div class="headline">今日定性一句话</div>
  </div>
</header>
```

```css
.dashboard-strip {
  background: var(--bg-header);
  color: var(--text-on-dark);
  padding: 24px 32px;
  border-radius: 12px;
  margin-bottom: 48px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.index-cards { display: flex; gap: 24px; }
.index-card { text-align: center; }
.index-card .index-name { font-size: 12px; opacity: 0.7; display: block; }
.index-card .index-value { font-size: 20px; font-weight: 700; display: block; }
.index-card.up .index-change { color: #E74C3C; }
.index-card.down .index-change { color: #3498DB; }

.progress-bar {
  width: 120px; height: 8px;
  background: rgba(255,255,255,0.2);
  border-radius: 4px;
  display: inline-block;
  vertical-align: middle;
}
.progress-fill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, #3498DB, #E67E22, #C0392B);
}
```

## ECharts 图表规范

CDN 引入：
```html
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
```

**全局主题色**：
```javascript
const CHART_COLORS = ['#C0392B', '#2C3E50', '#E67E22', '#27AE60', '#8E44AD', '#3498DB'];
const CHART_UP = '#C0392B';
const CHART_DOWN = '#2C3E50';
```

**通用配置**：
```javascript
{
  backgroundColor: 'transparent',
  textStyle: { fontFamily: '-apple-system, PingFang SC, Microsoft YaHei' },
  grid: { left: 60, right: 20, top: 40, bottom: 40, containLabel: true },
  tooltip: { trigger: 'axis', backgroundColor: 'rgba(44,24,16,0.9)', textStyle: { color: '#FAF7F2' } }
}
```

**图表容器尺寸**：
- 全宽图表：`width: 100%; height: 360px;`
- 半宽图表：`width: 48%; height: 280px; display: inline-block;`
- 迷你图表：`width: 100%; height: 200px;`

## 各模块可视化要求

### Module 2: 情绪温度计

- **5日趋势折线图**（ECharts line，迷你尺寸）
- **散户/机构对比仪表盘**（两个并排 ECharts gauge，半宽）

```javascript
// 仪表盘配置骨架
{
  series: [{
    type: 'gauge',
    startAngle: 180, endAngle: 0,
    min: 0, max: 100,
    splitNumber: 5,
    axisLine: {
      lineStyle: {
        width: 20,
        color: [[0.3, '#2C3E50'], [0.7, '#E67E22'], [1, '#C0392B']]
      }
    },
    pointer: { length: '60%' },
    detail: { fontSize: 24, offsetCenter: [0, '40%'] },
    data: [{ value: 65, name: '散户情绪' }]
  }]
}
```

### Module 3: 板块分析

- **行业涨跌热力条形图**（ECharts bar，全宽，横向，按涨跌幅排序，涨红跌蓝）
- **轮动周期5阶段条**（纯CSS，高亮当前阶段）

```css
.rotation-stages {
  display: flex; gap: 4px;
}
.rotation-stage {
  flex: 1; padding: 8px; text-align: center;
  background: var(--bg-card-alt); border-radius: 4px;
  font-size: 12px; color: var(--text-muted);
}
.rotation-stage.active {
  background: var(--color-up); color: white; font-weight: 600;
}
```

### Module 4: 资金路线图

- **资金迁移桑基图或流向箭头**（ECharts sankey 或自行用 div+CSS 箭头）
- **超大单/小单对比分组柱状图**（ECharts bar，全宽）

### Module 5: 技术与估值

- **迷你K线图**（ECharts candlestick，近30日，全宽）
- **PE历史百分位轨道**（纯CSS水平滑块）

```css
.percentile-track {
  width: 100%; height: 24px; position: relative;
  background: linear-gradient(90deg, #27AE60 0%, #E67E22 50%, #C0392B 100%);
  border-radius: 12px; margin: 16px 0;
}
.percentile-marker {
  position: absolute; top: -4px; width: 4px; height: 32px;
  background: var(--text-primary); border-radius: 2px;
  transform: translateX(-50%);
}
```

- **ERP双轴折线图**（ECharts line，近2年，全宽）

### Module 6: 次日预判

- **三情景概率分段条**（CSS flex，三段不同颜色）

```css
.scenario-bar {
  display: flex; height: 32px; border-radius: 8px; overflow: hidden; margin: 16px 0;
}
.scenario-segment {
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 600; color: white;
}
.scenario-core { background: var(--color-neutral); }
.scenario-bull { background: var(--color-up); }
.scenario-bear { background: var(--color-down); }
```

- **情景卡片 accordion**（点击展开/收起触发条件）

```html
<div class="scenario-card" onclick="this.classList.toggle('expanded')">
  <div class="scenario-header">
    <span class="scenario-label">核心情景</span>
    <span class="scenario-prob num">60%</span>
    <span class="scenario-toggle">▶</span>
  </div>
  <div class="scenario-detail">
    <!-- 触发条件、区间、操作参考 -->
  </div>
</div>
```

## 内容质量控制

### 禁用表达（出现即重写）

| 禁止 | 替代要求 |
|------|---------|
| 市场情绪有所回暖 | 给出情绪分数值及变化量 |
| 需关注风险 | 指出具体风险和触发信号 |
| 可能震荡上行 | 给出概率和区间 |
| 技术面显示支撑 | 指出具体支撑位及计算依据 |
| 资金面较为活跃 | 给出成交额和与历史均值的比较 |
| 总而言之 / 需要指出的是 / 值得注意的是 / 总体来看 / 综上所述 | 直接删除 |

### 必须量化锚点

每份报告必须包含：
1. 情绪综合分（含散户/机构拆解）
2. 资金迁移净额（流出 vs 流入板块）
3. 沪深300当前 PE 历史百分位
4. 关键支撑/压力位（含计算依据）
5. 次日三情景概率（总和=100%，各附触发条件）
6. 上期预判准确度评级（若有历史记录）

### 模块标题规范

**用结论式句式**：
- ✅ 「资金从消费向科技大迁移，赚钱效应持续修复」
- ❌ 「板块资金分析」

**先说好还是不好，再说为什么**——每个模块首句即结论。

### 语言规范

**保留英文**：PE、PB、ERP、MA、ETF、MLF、EPS、ROE

**必须中文**：所有分析结论、图表标题、评价性用语、方向性判断

### 页脚

```html
<footer class="report-footer">
  <p>数据来源：AkShare（东方财富）、Tavily | 报告由 AI 自动生成，不构成投资建议</p>
  <p>盘脉日报 · YYYY年MM月DD日</p>
</footer>
```
