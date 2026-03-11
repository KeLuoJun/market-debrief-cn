# 盘脉 v2.0 HTML报告设计系统

> Goldman Sachs + Financial Times 混合风格 — 信息密度+温暖权威感

## 设计哲学

- **信息优先** — 设计服务于数据，标题是结论而非描述
- **信号灯系统** — 红=风险/过热，黄=关注，绿=健康，灰=参考
- **A股习惯** — 涨红跌绿，沿用投资者最熟悉的配色
- **10米可读** — 大数字、大标题、斑马纹表格，兼顾投影场景

## 色彩体系

```css
:root {
  /* 主色调 — 深海蓝+暖金 */
  --color-primary: #1B2A4A;
  --color-primary-light: #2D4A7A;
  --color-accent: #C8975E;
  --color-accent-light: #E8C99B;

  /* 页面背景 */
  --color-bg: #F2F4F7;
  --color-surface: #FFFFFF;
  --color-surface-alt: #F8F9FB;

  /* 涨跌色（A股习惯） */
  --color-up: #CF3039;
  --color-up-bg: rgba(207, 48, 57, 0.08);
  --color-down: #1F8A3D;
  --color-down-bg: rgba(31, 138, 61, 0.08);

  /* 情绪信号色 */
  --color-hot: #E8453C;
  --color-optimistic: #F5A623;
  --color-neutral: #7B8794;
  --color-pessimistic: #4A90D9;
  --color-cold: #5C6AC4;

  /* 文本层级 */
  --text-primary: #1A202C;
  --text-secondary: #4A5568;
  --text-tertiary: #A0AEC0;
  --text-inverse: #FFFFFF;

  /* 边框与分隔 */
  --border-light: #E2E8F0;
  --border-medium: #CBD5E0;

  /* 阴影 */
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.06);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.12);

  /* 圆角 */
  --radius-sm: 6px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 20px;
}
```

## 字体系统

```css
/* 通过 Google Fonts CDN 引入 */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 15px;
  line-height: 1.7;
}

/* 字号体系 */
--font-display: 48px;     /* 超大数字（封面指数） */
--font-hero: 36px;        /* 大标题 */
--font-h1: 24px;          /* Section标题 */
--font-h2: 18px;          /* 子标题 */
--font-body: 15px;        /* 正文 */
--font-small: 13px;       /* 辅助文字 */
--font-caption: 11px;     /* 标注 */
```

## 组件库

### 1. 页面骨架

```css
html { background: var(--color-bg); }
body { max-width: 1200px; margin: 0 auto; padding: 32px 40px; }
```

### 2. 封面仪表盘 (Section 0)

```
┌────────────────────────────────────────────────────────────┐
│  glassmorphism 头部                                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 📊 盘脉日报    YYYY-MM-DD    期号    [情绪Badge]      │  │
│  │                                                      │  │
│  │   沪指 X,XXX.XX   ▲+X.XX%                           │  │
│  │   [4个迷你指数卡片 并排]                               │  │
│  │   [情绪弧形仪表盘]  [今日定性一句话]                    │  │
│  │   [3个关键词Tag]   [明日核心情景]                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌─ 快速导航 ──────────────────────────────────────────┐  │
│  │ 01 宏观 | 02 情绪 | 03 盘中 | 04 板块 | 05 资金 |    │  │
│  │ 06 技术 | 07 估值 | 08 预判 | 09 验证                  │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

- 头部背景：`linear-gradient(135deg, #1B2A4A 0%, #2D4A7A 60%, #3D5A8A 100%)`
- Glassmorphism效果：`backdrop-filter: blur(20px); background: rgba(27,42,74,0.92);`
- 情绪Badge：圆角胶囊，背景色根据情绪等级变化
- 迷你指数卡片：半透明白色背景，`background: rgba(255,255,255,0.1)`

### 3. Section 卡片

```css
.section-card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: 32px;
  margin-bottom: 20px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-light);
  transition: box-shadow 0.3s ease;
}
.section-card:hover {
  box-shadow: var(--shadow-md);
}
```

每个Section顶部有：
- **编号标记**（01-09）— 暖金色小圆角标签
- **信号灯**（🔴🟡🟢）— 该Section的总体信号
- **折叠/展开按钮** — 右侧 ▾/▸ 图标

### 4. 数据表格

```css
.data-table {
  width: 100%;
  border-collapse: collapse;
}
.data-table th {
  background: var(--color-primary);
  color: var(--text-inverse);
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 600;
  text-align: left;
  letter-spacing: 0.5px;
}
.data-table td {
  padding: 10px 16px;
  border-bottom: 1px solid var(--border-light);
  font-size: 14px;
}
.data-table tr:nth-child(even) {
  background: var(--color-surface-alt);
}
.data-table tr:hover td {
  background: rgba(200, 151, 94, 0.06); /* 暖金色hover */
}
```

### 5. 情绪仪表盘（ECharts Gauge）

使用 ECharts gauge 系列：
- 弧度 225° 到 -45°
- 色段：0-20蓝色，20-40浅蓝，40-60灰色，60-80橙色，80-100红色
- 中央大字显示分数

### 6. K线图（ECharts Candlestick）

- 涨K线：`#CF3039`（填充+边框）
- 跌K线：`#1F8A3D`（填充+边框）
- 均线：MA5 `#F5A623`, MA20 `#4A90D9`, MA60 `#8B5CF6`
- 成交量：涨日红色，跌日绿色，透明度0.6
- 支撑/压力位：水平虚线 + 标注文字

### 7. Treemap 热力图（板块强弱）

- 面积代表成交额
- 颜色代表涨跌幅（红-灰-绿渐变）
- Hover显示详情

### 8. 资金流向 Sankey 图

- 左侧流出板块（绿色节点）
- 右侧流入板块（红色节点）
- 流量线宽度代表金额

### 9. 预判情景卡片

三列布局，每列一个情景：
- 核心情景：暖金色左边框 `border-left: 4px solid var(--color-accent);`
- 乐观情景：红色左边框 `border-left: 4px solid var(--color-up);`  
- 悲观情景：绿色左边框 `border-left: 4px solid var(--color-down);`

### 10. 页面底部

```html
<footer>
  <p>本报告由AI自动生成，仅供参考，不构成任何投资建议。投资有风险，入市需谨慎。</p>
  <p style="font-size:6.5pt;color:#BBB;">Ctrl/Cmd + P 导出PDF</p>
</footer>
```

## 交互设计

| 交互 | 实现方式 | 说明 |
|------|---------|------|
| Section折叠/展开 | 纯JS toggle | 默认展开全部 |
| 图表Hover Tooltip | ECharts内置 | 显示详细数据 |
| 顶部锚点导航 | CSS sticky + smooth scroll | 快速跳转 |
| 数字动画 | CSS counter + requestAnimationFrame | 页面加载时数字滚动 |
| 卡片Hover上浮 | CSS transform + shadow | 微交互增强 |

## 响应式断点

```css
@media (max-width: 768px) {
  body { padding: 16px; }
  .section-card { padding: 20px; }
  .stats-grid { grid-template-columns: 1fr 1fr; }
  .prediction-cards { flex-direction: column; }
}
```

## ECharts CDN

```html
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
```

所有图表通过CDN引入ECharts，无本地依赖，保持单文件HTML输出。
