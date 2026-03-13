# HTML 报告设计规范

> 本文件定义日报 HTML 的视觉风格、布局结构、交互组件和内容质量标准。
> 渲染 Agent 生成 HTML 时查阅此文件。

---

## 目录

1. [设计哲学](#设计哲学)
2. [FT 风格色彩系统](#ft-风格色彩系统)
3. [排版规范](#排版规范)
4. [页面布局](#页面布局)
5. [顶部仪表盘横条](#顶部仪表盘横条)
6. [ECharts 图表规范](#echarts-图表规范)
7. [各模块可视化要求（详细）](#各模块可视化要求)
8. [交互设计规范](#交互设计规范)
9. [内容质量控制](#内容质量控制)

---

## 设计哲学

**参照物**：Financial Times 深度报道专题页 + Bloomberg Markets 数据可视化页

**核心原则**：
- **数据即视觉**：每一个数字都应有视觉对应——禁止纯文字罗列数据
- **深度优先**：每个模块至少含1个交互式图表，交互服务于「探索深层含义」而非装饰
- **结论前置**：每模块标题即核心结论，正文从「为什么」开始
- **量化到底**：所有判断必须附数字锚点，禁止使用无数字的形容词
- **看图即懂**：**必须生成完整的业务解释说明。绝对禁止挂出图表/徽章而没有对应的图例、文字描述或动态 tooltip 说明。图下方的`.insight-summary`是必须项。**
- **留白即呼吸**：模块间距充足，文字行高宽松，卡片投影轻盈

## 工程化布局约束

> 这是渲染 Agent 的硬约束，不是建议。目标是避免「看起来有设计，但组件互相打架」的成品。

- **先搭骨架再填内容**：先输出页面主栅格、模块容器、图表容器，再写正文与明细表。禁止边写内容边临时拼 CSS。
- **一个图表一个盒子**：每个 ECharts 容器都必须放在 `.chart-frame` 内，并带固定高度类；禁止把 `style="height:..."` 零散写在多个节点上。
- **一个模块一个主视觉**：每个模块只允许 1 个主图表 + 1-2 个次级组件。若信息过多，优先删次级组件，不要压缩主图表高度。
- **表格必须可滚动**：任何超过 4 列或 8 行的表格外层必须包裹 `.table-wrap`，移动端允许横向滚动，禁止压缩到文字重叠。
- **数字卡统一高度**：顶部指数卡、统计卡、情景卡采用统一最小高度，避免某列内容过长导致参差不齐。
- **移动端先于桌面端兜底**：当宽度不足时，一律改为单列或双列，不允许继续挤压桌面布局。
- **无数据时优雅降级**：图表无有效数据时输出 `.empty-state` 提示卡，而不是空白坐标轴或尺寸塌陷的容器。

---

## FT 风格色彩系统

固定采用 Financial Times 风格变体——三文鱼粉底色系的温暖权威感。

```css
:root {
  /* 页面底色 */
  --bg-page: #FAF7F2;
  --bg-card: #FFFFFF;
  --bg-card-alt: #FFF8F0;
  --bg-card-dark: #F5F0E8;
  --bg-header: #1C0F08;        /* 更深的espresso色 */
  --bg-header-accent: #2C1810;

  /* 语义色 */
  --color-up: #C0392B;         /* 上涨 / 利多 / 强调 */
  --color-up-light: #F8D7D3;   /* 上涨浅色背景 */
  --color-down: #1A2E3E;       /* 下跌 / 利空（更深沉） */
  --color-down-light: #D1DCE5; /* 下跌浅色背景 */
  --color-neutral: #7F8C8D;    /* 中性 */
  --color-warning: #D68910;    /* 警告（更暗的金色） */
  --color-warning-light: #FEF9E7;
  --color-positive: #1E8449;   /* 积极信号 */

  /* 文字色 */
  --text-primary: #1A1A1A;
  --text-secondary: #4A4A4A;
  --text-muted: #888888;
  --text-on-dark: #FAF7F2;
  --text-on-dark-secondary: rgba(250,247,242,0.65);

  /* 边框 */
  --border-light: #E6DDD4;
  --border-medium: #CFC5BB;
  --border-accent: #C0392B;

  /* 阴影 */
  --shadow-sm: 0 1px 4px rgba(0,0,0,0.06);
  --shadow-md: 0 4px 16px rgba(0,0,0,0.08);
  --shadow-lg: 0 8px 32px rgba(0,0,0,0.12);

  /* 图表色板（ECharts 用） */
  --chart-1: #C0392B;
  --chart-2: #1A2E3E;
  --chart-3: #D68910;
  --chart-4: #1E8449;
  --chart-5: #7D3C98;
  --chart-6: #2471A3;
  --chart-7: #CB4335;
  --chart-8: #2E86C1;
}
```

## 排版规范

```css
body {
  font-family: "Georgia", "Noto Serif SC", "Source Han Serif SC",
               -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
  font-size: 15px;
  line-height: 1.75;
  color: var(--text-primary);
}

/* 模块标题：严肃衬线感 */
h2.module-title {
  font-size: 21px; font-weight: 700;
  border-left: 4px solid var(--color-up);
  border-bottom: none;
  padding: 4px 0 4px 14px;
  margin-top: 0; margin-bottom: 6px;
  letter-spacing: -0.3px;
}

/* 结论句：橙黄醒目 */
.conclusion {
  font-size: 15px; font-style: italic;
  color: var(--color-warning); font-weight: 600;
  margin-bottom: 16px; padding-left: 14px;
  border-left: 2px solid var(--color-warning);
}

h3 { font-size: 16px; font-weight: 700; margin-top: 24px; margin-bottom: 10px; }

/* 辅助文字最小 11px */
.caption, .footnote, .axis-label { font-size: 11px; color: var(--text-muted); }

/* 数字统一等宽 */
.num, .metric {
  font-family: "SFMono-Regular", "Menlo", "Consolas", monospace;
  font-variant-numeric: tabular-nums;
}

/* 红绿着色辅助类 */
.up   { color: var(--color-up); }
.down { color: var(--color-down); }
.warn { color: var(--color-warning); }
```

## 页面布局

```css
html { background: var(--bg-page); }
* { box-sizing: border-box; }
body {
  max-width: 1180px;
  margin: 0 auto;
  padding: 40px 32px 72px;
  background: var(--bg-page);
}

.page-shell {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

/* 模块卡片 */
.module {
  background: var(--bg-card);
  border-radius: 18px;
  padding: 28px 30px 30px;
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border-light);
}

.module-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 20px;
  align-items: end;
  margin-bottom: 18px;
}

.module-kicker {
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-warning);
  margin-bottom: 8px;
}

.module-meta {
  font-size: 12px;
  color: var(--text-muted);
  text-align: right;
}

.viz-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.95fr);
  gap: 18px;
  align-items: stretch;
}

.viz-card,
.stat-card,
.note-card {
  background: linear-gradient(180deg, #fffdf9 0%, #fffaf4 100%);
  border: 1px solid var(--border-light);
  border-radius: 14px;
  padding: 16px 18px;
  min-height: 120px;
}

.chart-frame {
  position: relative;
  width: 100%;
  overflow: hidden;
  border-radius: 14px;
  background: linear-gradient(180deg, #fffdfa 0%, #f8f2ea 100%);
  border: 1px solid var(--border-light);
  padding: 10px;
}

.table-wrap {
  width: 100%;
  overflow-x: auto;
  border: 1px solid var(--border-light);
  border-radius: 12px;
}

.table-wrap table {
  width: 100%;
  min-width: 680px;
  border-collapse: collapse;
  background: #fff;
}

.empty-state {
  min-height: 120px;
  display: grid;
  place-items: center;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
  background: repeating-linear-gradient(
    -45deg,
    #fbf6ef,
    #fbf6ef 12px,
    #f6efe6 12px,
    #f6efe6 24px
  );
  border: 1px dashed var(--border-medium);
  border-radius: 12px;
}

/* 模块内分区 */
.module-section {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--border-light);
}

/* 双列网格 */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
/* 三列网格 */
.three-col { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
/* 四列网格 */
.four-col { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }

@media (max-width: 768px) {
  body { padding: 16px 14px 40px; }
  .module { padding: 20px 18px 22px; border-radius: 16px; }
  .module-header,
  .viz-grid,
  .two-col,
  .three-col,
  .four-col { grid-template-columns: 1fr; }
  .module-meta { text-align: left; }
}
```

**结构顺序**：

```
[顶部仪表盘横条]       ← 全宽深色 header
[Module 1] 宏观定价扫描
[Module 2] 市场情绪温度计
[Module 3] 板块结构性分析
[Module 4] 资金路线图
[Module 5] 技术形态与估值
[Module 6] 次日预判与历史镜像
[页脚]
```

每个模块用 `<section class="module">` 包裹，模块标题 (`h2.module-title`) 即核心结论。

## 顶部仪表盘横条

深色 espresso 底，三行布局：品牌行 → 指数卡网格 → 市场概览卡。禁止使用简单横向一排把 6 个指数强行压缩在一起。

```html
<header class="dashboard-strip">
  <!-- 顶栏 -->
  <div class="dashboard-top">
    <div class="dashboard-brand">
      <span class="dashboard-label">A股深度日报</span>
      <span class="dashboard-date">2026年3月12日 周四</span>
    </div>
    <div class="dashboard-headline">新能源强势但创业板大跌，市场分化加剧</div>
  </div>

  <!-- 指数行 -->
  <div class="index-row">
    <div class="index-card up">
      <span class="idx-name">上证指数</span>
      <span class="idx-val num">4129.10</span>
      <span class="idx-chg num up">-0.10%</span>
    </div>
    <!-- 深证、创指、沪深300、科创50、中证500 -->
    ...
  </div>

  <!-- 概览行 -->
  <div class="dashboard-stats">
    <div class="stat-item">
      <span class="stat-label">成交额</span>
      <span class="stat-value num">1.07万亿</span>
      <span class="stat-sub">20日均值1.12倍</span>
    </div>
    <div class="stat-item">
      <span class="stat-label">情绪温度</span>
      <div class="thermo-bar">
        <div class="thermo-fill" style="width:55%"></div>
      </div>
      <span class="stat-value num">55/100</span>
      <span class="stat-sub">中性</span>
    </div>
    <div class="stat-item">
      <span class="stat-label">涨停/跌停</span>
      <span class="stat-value num up">52</span>
      <span class="stat-value num"> / </span>
      <span class="stat-value num down">2</span>
    </div>
    <div class="stat-item">
      <span class="stat-label">北向资金</span>
      <span class="stat-value num">[净额]亿</span>
    </div>
  </div>
</header>
```

```css
.dashboard-strip {
  background: linear-gradient(135deg, var(--bg-header) 0%, #2C1810 100%);
  color: var(--text-on-dark);
  padding: 30px 30px 24px;
  border-radius: 22px;
  margin-bottom: 36px;
  box-shadow: var(--shadow-lg);
}

/* 顶行 */
.dashboard-top {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 18px;
  align-items: start;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(250,247,242,0.15);
}
.dashboard-label { font-size: 13px; opacity: 0.55; margin-right: 12px; }
.dashboard-date { font-size: 13px; opacity: 0.55; }
.dashboard-headline {
  font-size: 16px; font-weight: 600; color: #F0C75E;
  max-width: 420px; text-align: right;
}

/* 指数行 */
.index-row {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 18px;
}
.index-card {
  min-height: 96px;
  padding: 14px 12px 12px;
  text-align: left;
  border: 1px solid rgba(250,247,242,0.1);
  border-radius: 14px;
  background: rgba(255,255,255,0.04);
}
.idx-name { display: block; font-size: 11px; color: var(--text-on-dark-secondary); margin-bottom: 4px; }
.idx-val { display: block; font-size: 24px; font-weight: 700; line-height: 1.15; }
.idx-chg { display: block; font-size: 13px; margin-top: 2px; }
.idx-chg.up { color: #E05555; }
.idx-chg.down { color: #6BA3BE; }

/* 概览行 */
.dashboard-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}
.stat-item {
  min-height: 88px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 8px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(250,247,242,0.08);
}
.stat-label { font-size: 11px; color: var(--text-on-dark-secondary); }
.stat-value { font-size: 20px; font-weight: 700; }
.stat-sub { font-size: 11px; color: var(--text-on-dark-secondary); }

/* 温度条 */
.thermo-bar {
  width: 80px; height: 6px;
  background: rgba(255,255,255,0.2); border-radius: 3px;
  display: inline-block; vertical-align: middle;
}
.thermo-fill {
  height: 100%; border-radius: 3px;
  background: linear-gradient(90deg, #2471A3, #D68910, #C0392B);
}

@media (max-width: 900px) {
  .dashboard-top,
  .dashboard-stats { grid-template-columns: 1fr; }
  .index-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .dashboard-headline { max-width: none; text-align: left; }
}
```

## ECharts 图表规范

CDN 引入：
```html
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
```

**全局常量**（JS顶部声明一次）：
```javascript
const C = {
  UP:    '#C0392B',  DOWN:    '#1A2E3E',
  WARN:  '#D68910',  POS:     '#1E8449',
  MID:   '#7F8C8D',
  COLORS: ['#C0392B','#1A2E3E','#D68910','#1E8449','#7D3C98','#2471A3'],
  TOOLTIP_BG: 'rgba(28,15,8,0.92)',
  FONT: 'Georgia, "PingFang SC", "Microsoft YaHei", sans-serif'
};
// 通用grid
function grd(l=56,r=16,t=60,b=50) { return {left:l,right:r,top:t,bottom:b,containLabel:true}; }
// 通用tooltip (带明确的业务单位和说明格式)
function tip(fmt) { return {trigger:'axis',backgroundColor:C.TOOLTIP_BG,borderColor:'transparent',textStyle:{color:'#FAF7F2',fontSize:12},formatter:fmt}; }
// 通用DataZoom (必须启用，否则无法满足深度交互)
function zoom() { return [{type: 'inside', start: 0, end: 100}, {type: 'slider', start: 0, end: 100, height: 20, bottom: 5}]; }
```

**容器尺寸**：
```css
.chart-full  { width: 100%; height: 380px; }
.chart-tall  { width: 100%; height: 460px; } /* K线图、行业热力 */
.chart-half  { height: 280px; }              /* 搭配 .two-col 使用 */
.chart-mini  { width: 100%; height: 200px; } /* 迷你趋势图 */
.chart-gauge { height: 220px; }              /* 情绪仪表盘 */
```

**布局兜底规则**：
- gauge 容器最小宽度 260px；若双列宽度不足，改为纵向堆叠，不允许指针、刻度和数字重叠。
- K 线图与 Sankey 图必须单独占据一整行 `.viz-card`，禁止与表格或长文本并排。
- 表格上方必须留出标题或说明，避免图表和表格首行直接相撞。
- 若任一模块的数据缺失超过 50%，该模块主视觉降级为 stat card + insight-block + empty-state，不强行渲染复杂图表。

**通用图表样式增强**：
- 所有 axis 的 axisLine、splitLine 使用 `#E6DDD4`（与卡片底色协调）
- tooltip 使用深色 espresso 背景
- 横向分组条形图的数据标签始终显示在条形末端
- 时间轴格式：xAxis 用 `{MM}-{dd}` 短格式
- resize 监听：`window.addEventListener('resize', () => charts.forEach(c => c.resize()))`

## 各模块可视化要求（详细）

### Module 1: 宏观定价扫描

**必须包含（≥1种）**：

**0.5 预期差主叙事卡（新增，强烈建议固定展示）**：

> 当 `module1.expectation_gap` 存在时，优先展示第 1 条作为本页最重要的“市场在交易什么”摘要卡。它不是装饰，而是整份日报的研究主轴。

```html
<section class="thesis-card">
  <div class="thesis-topline">
    <span class="thesis-kicker">Market Thesis</span>
    <span class="thesis-badge partial">局部充分</span>
  </div>
  <h3 class="thesis-title">市场在交易政策表述升级，但只交易了高弹性链条</h3>
  <div class="thesis-grid">
    <div class="thesis-col">
      <div class="mini-label">市场原预期</div>
      <p>[market_prior]</p>
    </div>
    <div class="thesis-col">
      <div class="mini-label">今日新增信息</div>
      <p>[new_information]</p>
    </div>
    <div class="thesis-col thesis-wide">
      <div class="mini-label">盘面反应</div>
      <p>[market_reaction]</p>
    </div>
  </div>
  <div class="thesis-checks">
    <div class="check-box">
      <div class="mini-label">明日验证点</div>
      <ul>[tomorrow_checks li]</ul>
    </div>
    <div class="check-box danger">
      <div class="mini-label">证伪条件</div>
      <ul>[falsifiers li]</ul>
    </div>
  </div>
</section>
```

```css
.thesis-card {
  background: linear-gradient(135deg, #fff8f0 0%, #f7efe5 100%);
  border: 1px solid var(--border-medium);
  border-radius: 16px;
  padding: 18px 20px;
  margin: 18px 0 22px;
  box-shadow: var(--shadow-sm);
}
.thesis-topline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.thesis-kicker {
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-warning);
  font-weight: 700;
}
.thesis-title {
  font-size: 20px;
  line-height: 1.35;
  margin: 0 0 14px;
}
.thesis-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.thesis-col,
.check-box {
  background: rgba(255,255,255,0.72);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 12px 14px;
}
.thesis-col.thesis-wide { grid-column: 1 / -1; }
.mini-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.thesis-checks {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.check-box ul {
  margin: 0;
  padding-left: 18px;
}
.check-box.danger {
  background: #fff4f2;
  border-color: #f1c7c1;
}
.thesis-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}
.thesis-badge.underpriced { background: #eaf4ff; color: #1a5276; }
.thesis-badge.partial { background: #fef4de; color: #7d6608; }
.thesis-badge.overpriced { background: #fdecea; color: #922b21; }

@media (max-width: 900px) {
  .thesis-grid,
  .thesis-checks { grid-template-columns: 1fr; }
}
```

**① 事件定价热力表**（增强 HTML table）：
```html
<!-- 事件行：状态列用色块+文字组合，不只是文字颜色 -->
<tr>
  <td>[事件名]</td>
  <td>[传导路径]</td>
  <td>[盘面印证]</td>
  <td>
    <span class="pricing-badge pricing-full">已充分定价</span>
    <!-- 或 pricing-over, pricing-partial, pricing-pending -->
  </td>
</tr>
```
```css
.pricing-badge {
  display: inline-block; padding: 3px 10px;
  border-radius: 12px; font-size: 12px; font-weight: 600;
}
.pricing-full    { background: #D5EFDF; color: #1E5631; }
.pricing-over    { background: #FADBD8; color: #922B21; }
.pricing-partial { background: #FEF9E7; color: #7D6608; }
.pricing-pending { background: #EAF0F6; color: #1A5276; }
```

**② 宏观三维坐标雷达图（ECharts radar，可选）**：  
三轴（经济动能/流动性/风险偏好），满值5，当前值用标量填充。

**③ 外盘概览条（CSS 横向列表）**：
```css
.market-pills { display: flex; gap: 8px; flex-wrap: wrap; margin: 12px 0; }
.market-pill {
  padding: 6px 14px; border-radius: 20px;
  font-size: 13px; font-family: monospace;
  background: var(--bg-card-alt);
  border: 1px solid var(--border-light);
}
.market-pill .pill-name { font-size: 11px; color: var(--text-muted); display: block; }
```

---

### Module 2: 情绪温度计

**必须包含（全部）**：

**① 宽仪表盘 gauge（ECharts，全宽 350px height）**：  
主情绪分大表盘，下方并排两个小表盘（散户 / 机构），半宽各占 47%。

```javascript
// 主表盘（大）
{
  type: 'gauge',
  startAngle: 200, endAngle: -20,
  min: 0, max: 100, splitNumber: 5,
  radius: '78%', center: ['50%', '60%'],
  axisLine: {
    lineStyle: { width: 28, color: [
      [0.30, '#1A5276'], [0.60, '#D68910'], [1.00, '#C0392B']
    ]}
  },
  axisTick:  { splitNumber: 5, lineStyle: { color: '#fff', width: 1 } },
  splitLine: { length: 16, lineStyle: { color: '#fff', width: 2 } },
  axisLabel: { color: '#666', fontSize: 11, distance: 20 },
  pointer:   { length: '68%', width: 5, itemStyle: { color: 'auto' } },
  detail:    { formatter: '{value}', fontSize: 36, fontWeight: 700,
               color: '#1A1A1A', offsetCenter: [0, '30%'] },
  title:     { offsetCenter: [0, '55%'], fontSize: 13, color: '#888' },
  data:      [{ value: 55, name: '综合情绪分' }]
}
// 散户/机构：同结构，radius:'85%'，开角220/-40，字号24
```

**② 5日情绪趋势折线（迷你，chart-mini）**：  
带均线（5日、20日）和渐变面积，在情绪 > 75 时加「过热」红色标注区域（markArea）。

```javascript
// markArea 示例
markArea: {
  silent: true,
  data: [[ {yAxis: 75}, {yAxis: 100} ]],
  itemStyle: { color: 'rgba(192,57,43,0.06)' }
}
```

**③ 指标分项对比表**（HTML table，含分项得分进度条）：
```html
<tr>
  <td>成交额/20日均值</td>
  <td><div class="score-bar"><div class="score-fill" style="width:62%"></div></div></td>
  <td class="num">62</td>
  <td class="weight muted">权重20%</td>
</tr>
```
```css
.score-bar { width: 80px; height: 8px; background: #F0EBE4; border-radius: 4px; display:inline-block; vertical-align: middle; }
.score-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg,#2471A3,#D68910,#C0392B); }
```

---

### Module 3: 板块结构性分析

**必须包含（全部）**：

**① 行业涨跌幅横向条形图（ECharts bar，chart-tall 460px）**：
- 按涨跌幅从大到小排序（正值在上，负值在下）
- 正值条用 `#C0392B`，负值条用 `#1A2E3E`
- 每条末端显示数值标签（dataZoom: slider）
- Y轴行业名，X轴涨跌幅百分比
- 鼠标 hover tooltip 显示：行业名、涨跌幅、净流入额（如有）

**② 轮动周期5阶段进度条（CSS）**，当前阶段高亮 + 脉冲动画：
```css
.rotation-stages { display: flex; gap: 6px; margin: 16px 0; }
.rotation-stage {
  flex: 1; padding: 10px 6px; text-align: center;
  background: var(--bg-card-alt); border-radius: 8px;
  font-size: 12px; color: var(--text-muted);
  border: 2px solid transparent; transition: all .2s;
}
.rotation-stage.active {
  background: var(--color-up); color: #fff; font-weight: 700;
  border-color: #9B2335;
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%,100% { box-shadow: 0 0 0 0 rgba(192,57,43,.4); }
  50%      { box-shadow: 0 0 0 6px rgba(192,57,43,0); }
}
```

**③ 涨停生态雷达图（ECharts radar，chart-half）**：  
5 轴：涨停数/封板率/连板高度/首板占比/题材集中度；  
搭配文字说明卡片（右侧半宽）。

---

### Module 4: 资金路线图

**必须包含（全部）**：

**① 资金结构分组柱状图（ECharts bar，chart-full）**：
四组（超大单/大单/中单/小单），净流入为正时红色，负时蓝灰色。
标注合计机构资金（超大+大单）和散户资金（小单）。

**② 资金迁移桑基图（ECharts sankey，chart-full 380px）**：
```javascript
{
  type: 'sankey', layout: 'none',
  emphasis: { focus: 'adjacency' },
  nodeWidth: 24, nodePadding: 20,
  lineStyle: { color: 'gradient', opacity: 0.45, curveness: 0.5 },
  label:     { fontSize: 12, fontFamily: C.FONT },
  data: [
    // 来源节点（左）：["科技","医药","消费"]
    // 目标节点（右）：["新能源","化工","石油"]
  ],
  links: [
    // 每条流 { source:'科技', target:'新能源', value: 净流量(亿) }
  ]
}
// 若行业资金数据为空，用 CSS 箭头流向图代替（见下方备用方案）
```

**③ 主力资金30日走势折线（ECharts line，chart-mini）**：
超大单净流入历史序列，正值面积红色，负值面积蓝色（两段 areaStyle）。

```javascript
// 备用方案：无 sankey 数据时用 CSS 流向卡片
// .flow-card 左侧为来源（红字），箭头为中间，右侧为目标（深色字）
// 每条迁移路线一张卡片
```

---

### Module 5: 技术形态与估值

**必须包含（全部）**：

**① K线图（ECharts candlestick，chart-tall 460px，近60日）**：

```javascript
{
  // 沪深300 + 均线（MA5、MA20、MA60）+ 成交量（底部附图，15%空间）
  // 上方主图85%，下方量图15%，共用 xAxis[0]
  grid: [
    { left:60, right:16, top:44, bottom:'20%' },
    { left:60, right:16, top:'85%', bottom:30 }
  ],
  xAxis: [
    { gridIndex:0, type:'category', data: dates/*, ...交易日 */ },
    { gridIndex:1, type:'category', data: dates }
  ],
  yAxis: [
    { gridIndex:0, scale:true, splitLine:{ lineStyle:{ color:'#EDE5DC' } } },
    { gridIndex:1, scale:true, splitNumber:2 }
  ],
  series: [
    { type:'candlestick', data: kData,
      itemStyle:{ color: C.UP, color0: C.DOWN,
                  borderColor: C.UP, borderColor0: C.DOWN } },
    { type:'line', name:'MA5',  data: ma5,  smooth:true,
      lineStyle:{ color:'#D68910', width:1.5 } },
    { type:'line', name:'MA20', data: ma20, smooth:true,
      lineStyle:{ color:'#7D3C98', width:1.5 } },
    { type:'line', name:'MA60', data: ma60, smooth:true,
      lineStyle:{ color:'#2471A3', width:1.5 } },
    { type:'bar',  name:'成交量', xAxisIndex:1, yAxisIndex:1,
      data: vol,
      itemStyle:{ color: (params) => params.data[1] >= params.data[0] ? C.UP : C.DOWN } }
  ],
  dataZoom: [{ type:'inside', xAxisIndex:[0,1] }]
}
```

**② 多指数 PE 历史百分位轨道（CSS，4条，含标注）**：

```html
<div class="pe-track-group">
  <div class="pe-row">
    <span class="pe-name">沪深300</span>
    <div class="pe-track">
      <div class="pe-fill" style="width:88%"></div>
      <div class="pe-marker" style="left:88%"></div>
    </div>
    <span class="pe-detail num">P88 · PE 15.2x</span>
  </div>
  <!-- 中证500、中证1000、上证50 同结构 -->
</div>
```
```css
.pe-track-group { display: flex; flex-direction: column; gap: 12px; }
.pe-row { display: flex; align-items: center; gap: 12px; }
.pe-name { width: 70px; font-size: 13px; }
.pe-track {
  flex: 1; height: 20px; border-radius: 10px; position: relative;
  background: linear-gradient(90deg,#1E8449 0%,#D68910 50%,#C0392B 100%);
}
.pe-fill  { position: absolute; left:0; top:0; height:100%; border-radius:10px;
            background: rgba(255,255,255,0.35); }
.pe-marker { position:absolute; top:-5px; width:3px; height:30px;
              background: #1A1A1A; border-radius:2px; transform:translateX(-50%); }
.pe-detail { font-size: 13px; width: 100px; text-align: right; }
/* 危险区高亮 */
.pe-row[data-pct="high"] .pe-name { color: var(--color-up); font-weight:700; }
```

**③ ERP 双轴折线图（ECharts line，chart-full，近2年）**：
Y轴左：ERP(%)，Y轴右：沪深300 PE，X轴：月度。
画水平参考线（history mean）用 `markLine`。

---

### Module 6: 次日预判与历史镜像

**必须包含（全部）**：

**① 三情景概率分段条（CSS）**，标注概率百分比：
```html
<div class="scenario-bar">
  <div class="seg-bull"  style="flex:20">乐观 20%</div>
  <div class="seg-core"  style="flex:60">核心 60%</div>
  <div class="seg-bear"  style="flex:20">悲观 20%</div>
</div>
```
```css
.scenario-bar {
  display: flex; height: 44px; border-radius: 10px; overflow: hidden;
  margin: 20px 0; box-shadow: var(--shadow-sm);
}
.seg-bull, .seg-core, .seg-bear {
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 700; color: #fff; cursor: default;
  transition: flex .4s ease;
}
.seg-bull { background: var(--color-up); }
.seg-core { background: #6D7D8A; }
.seg-bear { background: var(--color-down); }
```

**② 情景卡片 accordion（三张，可展开）**：

```html
<div class="scenarios">
  <div class="scenario-card" data-type="bull" onclick="toggleScenario(this)">
    <div class="sc-header">
      <span class="sc-badge bull">乐观</span>
      <span class="sc-title">权重发力突破</span>
      <span class="sc-prob num">20%</span>
      <span class="sc-arrow">›</span>
    </div>
    <div class="sc-body">
      <p class="sc-desc">[情景描述，含区间]</p>
      <div class="sc-logic">
        <div class="logic-row">
          <span class="logic-label">验证叙事</span>
          <span class="logic-text">[validates]</span>
        </div>
        <div class="logic-row invalidation">
          <span class="logic-label">失效信号</span>
          <ul>[invalidation li]</ul>
        </div>
      </div>
      <div class="sc-triggers">
        <span class="trigger-label">触发条件</span>
        <ul>[li 每条触发条件]</ul>
      </div>
    </div>
  </div>
  <!-- core / bear 同结构 -->
</div>
```
```css
.scenario-card {
  background: var(--bg-card-alt);
  border-radius: 10px; margin: 8px 0;
  border: 1.5px solid var(--border-light);
  overflow: hidden; cursor: pointer;
  transition: box-shadow .2s;
}
.scenario-card:hover { box-shadow: var(--shadow-md); }
.sc-header {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 18px;
}
.sc-badge {
  padding: 3px 10px; border-radius: 12px;
  font-size: 12px; font-weight: 700;
}
.sc-badge.bull { background: #FADBD8; color: var(--color-up); }
.sc-badge.core { background: #EAEDED; color: #5D6D7E; }
.sc-badge.bear { background: #D6EAF8; color: var(--color-down); }
.sc-title { flex: 1; font-weight: 600; font-size: 15px; }
.sc-prob  { font-size: 20px; font-weight: 700; }
.sc-arrow { font-size: 20px; color: var(--text-muted); transition: transform .2s; }
.sc-body  { max-height: 0; overflow: hidden; transition: max-height .35s ease; }
.scenario-card.open .sc-body  { max-height: 520px; }
.scenario-card.open .sc-arrow { transform: rotate(90deg); }
.sc-body > * { padding: 0 18px; }
.sc-body > :last-child { padding-bottom: 16px; }
.trigger-label { font-size: 12px; font-weight: 600; color: var(--text-muted); }
.sc-logic {
  display: grid;
  gap: 10px;
  margin-bottom: 12px;
}
.logic-row {
  border: 1px solid var(--border-light);
  border-radius: 10px;
  background: #fff;
  padding: 10px 12px;
}
.logic-row.invalidation {
  background: #fff5f3;
  border-color: #f2c8c2;
}
.logic-label {
  display: block;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
  margin-bottom: 4px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.logic-text,
.logic-row ul {
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-secondary);
}
.logic-row ul {
  margin: 0;
  padding-left: 18px;
}

function toggleScenario(el) { el.classList.toggle('open'); }
```

**③ 关键观测清单交互表**：  
每行含「重要性」badge + 「应对策略」右侧展开。

---

## 交互设计规范

### 可用交互模式（根据模块选择）

| 交互类型 | 用途 | 实现方式 |
|---------|------|--------|
| Accordion 折叠 | 情景卡片、详细触发条件 | JS class toggle |
| Tab 切换 | 不同指数切换（K线图） | JS hidden/visible |
| DataZoom 缩放（强制）| 成交量/时间区间 | ECharts dataZoom |
| 业务解释提示框（强制）| 图表数据详情，带明确业务说明（上涨/流出代表什么），带有明确单位（%或亿元） | ECharts built-in tooltip |
| 图例 Legend（强制） | 区分重叠的多条时间序列/柱状图含义 | ECharts legend |
| Badge 点击过滤 | 行业分类筛选 | JS filter + class |
| 进度指示 | 概率条、PE百分位 | CSS transition |

### Tab 切换（指数K线）

```html
<div class="tab-bar">
  <button class="tab active" onclick="switchChart('csi300')">沪深300</button>
  <button class="tab" onclick="switchChart('chinext')">创业板指</button>
  <button class="tab" onclick="switchChart('star50')">科创50</button>
</div>
```
```css
.tab-bar { display: flex; gap: 4px; margin-bottom: 16px; }
.tab {
  padding: 6px 16px; border: none; background: var(--bg-card-alt);
  border-radius: 20px; font-size: 13px; cursor: pointer; color: var(--text-secondary);
  transition: all .15s;
}
.tab.active {
  background: var(--color-up); color: #fff; font-weight: 600;
}
```

### 数据看板悬停（统计卡片）

```css
.stat-card {
  background: var(--bg-card-alt);
  border: 1px solid var(--border-light);
  border-radius: 10px; padding: 16px 18px;
  transition: all .2s; cursor: default;
}
.stat-card:hover {
  border-color: var(--color-up);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}
.stat-card .label  { font-size: 12px; color: var(--text-muted); margin-bottom: 4px; }
.stat-card .value  { font-size: 24px; font-weight: 700; line-height: 1.2; }
.stat-card .trend  { font-size: 12px; margin-top: 4px; }
```

### ECharts Tooltip 增强

tooltip formatter 应输出多行数据，示例：
```javascript
formatter: function(params) {
  let lines = params.map(p =>
    `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${p.color};margin-right:6px"></span>
     ${p.seriesName}: <b>${p.value}</b>`
  );
  return `<div style="padding:6px">${params[0].axisValue}<br>${lines.join('<br>')}</div>`;
}
```

---

## 深度叙述区块（分析文字组件）

> 每个模块必须包含由 Subagent `analysis_text` 字段生成的叙述段落。叙述区块紧随图表之后，是报告质量的核心体现。

### 叙述区块 CSS 组件

```css
/* 深度分析区块 */
.insight-block {
  background: linear-gradient(135deg, #FFF8F0 0%, #FAF7F2 100%);
  border-left: 3px solid var(--color-warning);
  border-radius: 0 10px 10px 0;
  padding: 16px 20px;
  margin: 20px 0;
}
.insight-block .insight-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-warning);
  margin-bottom: 8px;
  display: block;
}
.insight-block p {
  font-size: 14px;
  line-height: 1.75;
  color: var(--text-secondary);
  margin: 0 0 8px 0;
}
.insight-block p:last-child { margin-bottom: 0; }
.insight-block strong { color: var(--text-primary); }

/* 双源标签：标注来源是AkShare数据还是Tavily新闻 */
.source-tag {
  display: inline-block;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 10px;
  margin-left: 4px;
  vertical-align: middle;
  font-weight: 600;
}
.source-tag.from-data { background: #D5E8D4; color: #2E7D32; }
.source-tag.from-news { background: #DAE8FC; color: #1565C0; }
```

### 叙述区块 HTML 模板

每个分析模块末尾放置 `.insight-block`，内容来自 Subagent JSON 中的 `analysis_text` 字段：

```html
<!-- Module 1 叙述区块 -->
<div class="insight-block">
  <span class="insight-label">深度解读</span>
  <p>[module1.analysis_text.event_interpretation 内容]</p>
  <p>[module1.analysis_text.macro_judgment 内容]</p>
  <p><strong>主叙事：</strong>[module1.analysis_text.pricing_core 内容]</p>
</div>

<!-- Module 2 叙述区块 -->
<div class="insight-block">
  <span class="insight-label">情绪解读</span>
  <p>[module2.analysis_text.emotion_portrait 内容]</p>
  <p>[module2.analysis_text.trend_insight 内容]</p>
</div>

<!-- Module 3 叙述区块（分两段） -->
<div class="insight-block">
  <span class="insight-label">板块解读</span>
  <p>[module3.analysis_text.sector_narrative 内容]</p>
  <p>[module3.analysis_text.ecology_insight 内容]</p>
</div>

<!-- Module 4 叙述区块 -->
<div class="insight-block">
  <span class="insight-label">资金解读</span>
  <p>[module4.analysis_text.fund_behavior_insight 内容]</p>
  <p>[module4.analysis_text.migration_narrative 内容]</p>
</div>

<!-- Module 5 叙述区块 -->
<div class="insight-block">
  <span class="insight-label">技术解读</span>
  <p>[module5.analysis_text.technical_narrative 内容]</p>
  <p>[module5.analysis_text.valuation_insight 内容]</p>
</div>
```

### 叙述区块放置位置规则

| 模块 | 叙述区块位置 |
|------|-----------|
| M1 宏观定价 | 预期差主叙事卡之后，事件表与宏观坐标之间 |
| M2 情绪温度计 | 情绪仪表盘之后，5日趋势折线之前 |
| M3 板块分析 | 行业条形图之后，TOP2解剖表之前 |
| M4 资金路线图 | 资金结构柱图之后，桑基图之前 |
| M5 技术+估值 | K线图之后，估值百分位轨道之前 |
| M6 情景预判 | 三情景概率条之后、情景卡之前；每张情景卡展开时同时显示 rationale、validates、invalidation |

### TOP2板块解剖卡新增字段

在 3.2 TOP 2 板块解剖的表格中，新增一行「深度解读」，内容来自 `top2_sectors[].deep_analysis`：

```html
<tr>
  <td style="vertical-align:top; white-space:nowrap;"><strong>深度解读</strong></td>
  <td colspan="4" class="insight-inline">[deep_analysis 内容]</td>
</tr>
```
```css
.insight-inline {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.7;
  font-style: italic;
}
```

---

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
