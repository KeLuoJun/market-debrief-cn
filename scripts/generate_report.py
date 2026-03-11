#!/usr/bin/env python3
"""
A股日报HTML报告生成脚本
从JSON数据生成可视化交互式HTML报告，包含7层分析结构

用法：
  python scripts/generate_report.py --input data.json --output report.html
  python scripts/generate_report.py -i data.json -o report.html --title "A股市场日报"

输入JSON结构：
{
  "date": "2025-03-10",
  "market_data": { ... },   // fetch_market_data.py输出
  "news_data": { ... },     // fetch_news.py输出
  "analysis": { ... }       // AI分析结论（可选，由Claude填充）
}
"""
import json
import argparse
import sys
import html as html_lib
from datetime import datetime
from pathlib import Path


def safe_float(val, default=0.0):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def safe_int(val, default=0):
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def escape(text):
    """HTML转义"""
    if not isinstance(text, str):
        text = str(text)
    return html_lib.escape(text)


def format_amount_yi(val):
    """格式化金额（亿元）"""
    v = safe_float(val)
    if abs(v) >= 1e12:
        return f"{v/1e12:.2f}万亿"
    elif abs(v) >= 1e8:
        return f"{v/1e8:.1f}亿"
    elif abs(v) >= 1e4:
        return f"{v/1e4:.1f}万"
    return f"{v:.0f}"


def sign_str(val):
    """带正负号的字符串"""
    v = safe_float(val)
    return f"+{v:.2f}" if v >= 0 else f"{v:.2f}"


def color_class(val):
    """根据正负返回CSS类名"""
    return "up" if safe_float(val) >= 0 else "down"


def generate_html_report(data, output_path="market_debrief.html", title=None):
    """生成完整的HTML可视化报告"""

    # 提取数据
    market_data = data.get('market_data', data)  # 兼容直接传fetch_market_data输出
    news_data = data.get('news_data', {})
    analysis = data.get('analysis', {})
    report_date = data.get('date', market_data.get(
        'date', datetime.now().strftime('%Y-%m-%d')))

    market = market_data.get('market_overview', {})
    index_data = market_data.get('index_kline', {})
    industry = market_data.get('industry_boards', [])
    concept = market_data.get('concept_boards', [])
    northbound = market_data.get('northbound_flow', {})
    margin = market_data.get('margin_data', {})
    lhb = market_data.get('lhb_data', {})
    sector_flow = market_data.get('sector_fund_flow', [])

    # 主指数数据（上证指数）
    sh_index = index_data.get('000001', {}).get(
        'data', []) if isinstance(index_data, dict) else index_data
    if isinstance(sh_index, list) and sh_index:
        latest_k = sh_index[-1]
        prev_k = sh_index[-2] if len(sh_index) > 1 else latest_k
    else:
        latest_k = {}
        prev_k = {}

    current_price = safe_float(latest_k.get('收盘', 0))
    prev_close = safe_float(prev_k.get('收盘', current_price))
    change_pct = (current_price - prev_close) / \
        prev_close * 100 if prev_close > 0 else 0
    change_abs = current_price - prev_close

    # 情绪评分
    sentiment_score = calculate_sentiment_score(market, northbound, margin)
    sentiment_level = get_sentiment_level(sentiment_score)

    # K线图数据
    kline_recent = sh_index[-30:] if isinstance(sh_index, list) else []
    kline_dates = json.dumps([str(k.get('日期', ''))
                             for k in kline_recent], ensure_ascii=False)
    kline_opens = json.dumps([safe_float(k.get('开盘')) for k in kline_recent])
    kline_closes = json.dumps([safe_float(k.get('收盘')) for k in kline_recent])
    kline_lows = json.dumps([safe_float(k.get('最低')) for k in kline_recent])
    kline_highs = json.dumps([safe_float(k.get('最高')) for k in kline_recent])
    kline_volumes = json.dumps([safe_float(k.get('成交量'))
                               for k in kline_recent])

    # 板块数据
    industry_top = industry[:10] if industry else []
    industry_names = json.dumps([escape(i.get('板块名称', ''))
                                for i in industry_top][::-1], ensure_ascii=False)
    industry_changes = json.dumps(
        [safe_float(i.get('涨跌幅', 0)) for i in industry_top][::-1])

    # 报告标题
    report_title = title or f"A股市场日报 - {report_date}"

    # 生成各section HTML
    macro_html = build_macro_section(news_data, analysis)
    sentiment_html = build_sentiment_section(
        market, northbound, margin, sentiment_score, sentiment_level)
    sector_html = build_sector_section(industry, concept, analysis)
    fund_html = build_fund_section(
        northbound, margin, lhb, sector_flow, analysis)
    tech_html = build_technical_section(sh_index, index_data, analysis)
    prediction_html = build_prediction_section(analysis)
    history_html = build_history_section(analysis)

    # 完整HTML
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(report_title)}</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
    <style>
{CSS_STYLES}
    </style>
</head>
<body>
<div class="container">

    <!-- Header -->
    <header class="report-header">
        <div class="header-top">
            <h1>{escape(report_title)}</h1>
            <span class="badge sentiment-{sentiment_level['css']}">{sentiment_level['icon']} {sentiment_level['text']} {sentiment_score}分</span>
        </div>
        <p class="header-sub">数据来源：AkShare &middot; 新闻来源：Tavily &middot; 报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        <div class="price-hero">
            <span class="price-val">{current_price:.2f}</span>
            <span class="price-change {color_class(change_pct)}">{sign_str(change_abs)} ({sign_str(change_pct)}%)</span>
        </div>
        <div class="stats-row">
            <div class="stat-pill">
                <span class="stat-pill-label">成交额</span>
                <span class="stat-pill-val">{format_amount_yi(market.get('total_amount', 0))}</span>
            </div>
            <div class="stat-pill">
                <span class="stat-pill-label">涨停</span>
                <span class="stat-pill-val up">{market.get('up_limit', 0)}</span>
            </div>
            <div class="stat-pill">
                <span class="stat-pill-label">跌停</span>
                <span class="stat-pill-val down">{market.get('down_limit', 0)}</span>
            </div>
            <div class="stat-pill">
                <span class="stat-pill-label">涨跌比</span>
                <span class="stat-pill-val">{market.get('up_count', 0)}:{market.get('down_count', 0)}</span>
            </div>
            <div class="stat-pill">
                <span class="stat-pill-label">换手率</span>
                <span class="stat-pill-val">{safe_float(market.get('avg_turnover', 0)):.2f}%</span>
            </div>
        </div>
    </header>

    <!-- 七层分析 -->
    <section class="card" id="layer1">
        <h2 class="card-title"><span class="layer-num">01</span> 宏观背景速递</h2>
        {macro_html}
    </section>

    <section class="card" id="layer2">
        <h2 class="card-title"><span class="layer-num">02</span> 市场情绪温度计</h2>
        {sentiment_html}
    </section>

    <section class="card" id="layer3">
        <h2 class="card-title"><span class="layer-num">03</span> 板块结构性分析</h2>
        {sector_html}
        <div id="industryChart" style="width:100%;height:400px;margin-top:20px;"></div>
    </section>

    <section class="card" id="layer4">
        <h2 class="card-title"><span class="layer-num">04</span> 资金路线图</h2>
        {fund_html}
    </section>

    <section class="card" id="layer5">
        <h2 class="card-title"><span class="layer-num">05</span> 技术形态诊断</h2>
        {tech_html}
        <div id="klineChart" style="width:100%;height:450px;margin-top:20px;"></div>
    </section>

    <section class="card" id="layer6">
        <h2 class="card-title"><span class="layer-num">06</span> 次日预判</h2>
        {prediction_html}
    </section>

    <section class="card" id="layer7">
        <h2 class="card-title"><span class="layer-num">07</span> 可回测的历史对比</h2>
        {history_html}
    </section>

    <footer>
        <p>本报告由AI自动生成，仅供参考，不构成任何投资建议。投资有风险，入市需谨慎。</p>
        <p>生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </footer>
</div>

<script>
// ====== K线图 ======
(function() {{
    var el = document.getElementById('klineChart');
    if (!el) return;
    var chart = echarts.init(el);
    var dates = {kline_dates};
    var opens = {kline_opens};
    var closes = {kline_closes};
    var lows = {kline_lows};
    var highs = {kline_highs};
    var volumes = {kline_volumes};

    // OHLC组合
    var ohlc = [];
    for (var i = 0; i < dates.length; i++) {{
        ohlc.push([opens[i], closes[i], lows[i], highs[i]]);
    }}

    var option = {{
        animation: false,
        tooltip: {{
            trigger: 'axis',
            axisPointer: {{ type: 'cross' }}
        }},
        grid: [
            {{ left: '8%', right: '3%', top: '8%', height: '55%' }},
            {{ left: '8%', right: '3%', top: '70%', height: '20%' }}
        ],
        xAxis: [
            {{ type: 'category', data: dates, gridIndex: 0, axisLine: {{ lineStyle: {{ color: '#718096' }} }} }},
            {{ type: 'category', data: dates, gridIndex: 1, axisLine: {{ lineStyle: {{ color: '#718096' }} }} }}
        ],
        yAxis: [
            {{ type: 'value', scale: true, gridIndex: 0, splitLine: {{ lineStyle: {{ color: '#E2E8F0' }} }} }},
            {{ type: 'value', scale: true, gridIndex: 1, splitLine: {{ lineStyle: {{ color: '#E2E8F0' }} }} }}
        ],
        series: [
            {{
                name: 'K线',
                type: 'candlestick',
                data: ohlc,
                xAxisIndex: 0,
                yAxisIndex: 0,
                itemStyle: {{
                    color: '#E53E3E',
                    color0: '#38A169',
                    borderColor: '#E53E3E',
                    borderColor0: '#38A169'
                }}
            }},
            {{
                name: '成交量',
                type: 'bar',
                data: volumes,
                xAxisIndex: 1,
                yAxisIndex: 1,
                itemStyle: {{
                    color: function(params) {{
                        var idx = params.dataIndex;
                        return closes[idx] >= opens[idx] ? '#E53E3E' : '#38A169';
                    }}
                }}
            }}
        ]
    }};
    chart.setOption(option);
    window.addEventListener('resize', function() {{ chart.resize(); }});
}})();

// ====== 行业板块图 ======
(function() {{
    var el = document.getElementById('industryChart');
    if (!el) return;
    var chart = echarts.init(el);
    var names = {industry_names};
    var changes = {industry_changes};
    var option = {{
        tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
        grid: {{ left: '18%', right: '5%', bottom: '5%', top: '5%' }},
        xAxis: {{
            type: 'value',
            axisLabel: {{ formatter: '{{value}}%' }},
            splitLine: {{ lineStyle: {{ color: '#E2E8F0' }} }}
        }},
        yAxis: {{
            type: 'category',
            data: names,
            axisLabel: {{ fontSize: 12 }}
        }},
        series: [{{
            name: '涨跌幅',
            type: 'bar',
            data: changes,
            label: {{
                show: true,
                position: 'right',
                formatter: '{{c}}%',
                fontSize: 11
            }},
            itemStyle: {{
                color: function(params) {{
                    return params.data >= 0 ? '#E53E3E' : '#38A169';
                }},
                borderRadius: [0, 4, 4, 0]
            }}
        }}]
    }};
    chart.setOption(option);
    window.addEventListener('resize', function() {{ chart.resize(); }});
}})();
</script>

</body>
</html>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"报告已生成: {output_path}", file=sys.stderr)
    return output_path


# ====================================================================
# 情绪评分
# ====================================================================

def calculate_sentiment_score(market, northbound, margin):
    """计算市场情绪综合评分 (0-100)"""
    score = 50

    # 成交额因子 (权重25%)
    amount = safe_float(market.get('total_amount', 0))
    if amount > 1.5e12:
        score += 15
    elif amount > 1.2e12:
        score += 10
    elif amount > 1e12:
        score += 5
    elif amount < 8e11:
        score -= 10
    elif amount < 5e11:
        score -= 15

    # 涨跌停比 (权重20%)
    up_limit = safe_int(market.get('up_limit', 0))
    down_limit = safe_int(market.get('down_limit', 0))
    if up_limit > 0 and down_limit > 0:
        ratio = up_limit / down_limit
        if ratio > 5:
            score += 12
        elif ratio > 2:
            score += 8
        elif ratio < 0.5:
            score -= 8
        elif ratio < 0.2:
            score -= 12
    elif up_limit > 50:
        score += 10
    elif down_limit > 50:
        score -= 10

    # 北向资金 (权重20%)
    nb_data = northbound.get('latest', {})
    nb_amount = 0
    for key in ['当日净流入', '北向资金', '净流入', '当日成交净买额']:
        if key in nb_data:
            nb_amount = safe_float(nb_data[key])
            break
    if nb_amount > 5e9:
        score += 10
    elif nb_amount > 0:
        score += 5
    elif nb_amount < -5e9:
        score -= 10
    elif nb_amount < 0:
        score -= 5

    # 两融变化 (权重20%)
    margin_change = safe_float(margin.get('margin_change', 0))
    if margin_change > 5e9:
        score += 10
    elif margin_change > 0:
        score += 5
    elif margin_change < -5e9:
        score -= 10
    elif margin_change < 0:
        score -= 5

    # 换手率 (权重15%)
    turnover = safe_float(market.get('avg_turnover', 0))
    if turnover > 3.0:
        score += 7
    elif turnover > 2.0:
        score += 3
    elif turnover < 1.0:
        score -= 5

    return max(0, min(100, score))


def get_sentiment_level(score):
    """情绪档位"""
    if score >= 80:
        return {"text": "过热", "css": "hot", "icon": "🔥"}
    elif score >= 60:
        return {"text": "乐观", "css": "optimistic", "icon": "☀️"}
    elif score >= 40:
        return {"text": "中性", "css": "neutral", "icon": "☁️"}
    elif score >= 20:
        return {"text": "悲观", "css": "pessimistic", "icon": "🌧️"}
    else:
        return {"text": "极度悲观", "css": "cold", "icon": "❄️"}


# ====================================================================
# 各Section生成
# ====================================================================

def build_macro_section(news_data, analysis):
    """第一层：宏观背景速递"""
    # 优先使用AI分析结论
    ai_macro = analysis.get('macro_analysis', '')
    if ai_macro:
        return f'<div class="analysis-text">{ai_macro}</div>'

    # 否则从新闻数据构建
    all_news = []
    for category in ['macro_news', 'policy_news', 'international_news']:
        cat_data = news_data.get(category, {})
        news_list = cat_data.get('news', [])
        all_news.extend(news_list)

    if not all_news:
        return '<p class="placeholder">暂无当日宏观新闻数据。请确保已配置TAVILY_API_KEY并运行fetch_news.py。</p>'

    html = '<div class="news-grid">'
    for item in all_news[:8]:
        title = escape(item.get('title', ''))
        content = escape(item.get('content', '')[:200])
        url = item.get('url', '')
        html += f'''
        <div class="news-card">
            <div class="news-card-title">{title}</div>
            <div class="news-card-content">{content}</div>
        </div>'''
    html += '</div>'
    return html


def build_sentiment_section(market, northbound, margin, score, level):
    """第二层：市场情绪温度计"""
    amount = safe_float(market.get('total_amount', 0))
    up_limit = safe_int(market.get('up_limit', 0))
    down_limit = safe_int(market.get('down_limit', 0))
    turnover = safe_float(market.get('avg_turnover', 0))

    nb_amount = 0
    nb_data = northbound.get('latest', {})
    for key in ['当日净流入', '北向资金', '净流入', '当日成交净买额']:
        if key in nb_data:
            nb_amount = safe_float(nb_data[key])
            break

    margin_change = safe_float(margin.get('margin_change', 0))

    # 情绪仪表盘
    gauge_pct = score  # 0-100

    return f'''
    <div class="sentiment-gauge-wrap">
        <div class="sentiment-gauge">
            <div class="gauge-fill" style="width:{gauge_pct}%"></div>
            <div class="gauge-labels">
                <span>极度悲观</span><span>悲观</span><span>中性</span><span>乐观</span><span>过热</span>
            </div>
        </div>
        <div class="sentiment-score-big">{score}<span class="score-unit">分</span></div>
        <div class="sentiment-level-text sentiment-{level['css']}">{level['icon']} {level['text']}</div>
    </div>

    <table class="data-table">
        <thead>
            <tr>
                <th>指标</th>
                <th>权重</th>
                <th>当日值</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>全市场成交额</td>
                <td>25%</td>
                <td>{format_amount_yi(amount)}</td>
            </tr>
            <tr>
                <td>涨停/跌停比</td>
                <td>20%</td>
                <td>{up_limit} : {down_limit}</td>
            </tr>
            <tr>
                <td>两融余额变化</td>
                <td>20%</td>
                <td class="{color_class(margin_change)}">{sign_str(margin_change / 1e8)}亿</td>
            </tr>
            <tr>
                <td>北向资金净流向</td>
                <td>20%</td>
                <td class="{color_class(nb_amount)}">{format_amount_yi(nb_amount)}</td>
            </tr>
            <tr>
                <td>市场平均换手率</td>
                <td>15%</td>
                <td>{turnover:.2f}%</td>
            </tr>
        </tbody>
    </table>
    '''


def build_sector_section(industry, concept, analysis):
    """第三层：板块结构性分析"""
    ai_sector = analysis.get('sector_analysis', '')

    html = ''
    if ai_sector:
        html += f'<div class="analysis-text">{ai_sector}</div>'

    # 行业板块表格
    if industry:
        html += '<h3 class="sub-title">行业板块涨跌榜 TOP10</h3>'
        html += '<table class="data-table"><thead><tr><th>板块</th><th>涨跌幅</th><th>成交额</th><th>换手率</th></tr></thead><tbody>'
        for item in industry[:10]:
            name = escape(item.get('板块名称', ''))
            change = safe_float(item.get('涨跌幅', 0))
            amount = item.get('成交额', 0)
            turnover = safe_float(item.get('换手率', 0))
            html += f'''<tr>
                <td><strong>{name}</strong></td>
                <td class="{color_class(change)}">{sign_str(change)}%</td>
                <td>{format_amount_yi(amount)}</td>
                <td>{turnover:.2f}%</td>
            </tr>'''
        html += '</tbody></table>'

    # 概念板块表格
    if concept:
        html += '<h3 class="sub-title" style="margin-top:20px;">概念板块涨跌榜 TOP10</h3>'
        html += '<table class="data-table"><thead><tr><th>板块</th><th>涨跌幅</th><th>成交额</th></tr></thead><tbody>'
        for item in concept[:10]:
            name = escape(item.get('板块名称', ''))
            change = safe_float(item.get('涨跌幅', 0))
            amount = item.get('成交额', 0)
            html += f'''<tr>
                <td><strong>{name}</strong></td>
                <td class="{color_class(change)}">{sign_str(change)}%</td>
                <td>{format_amount_yi(amount)}</td>
            </tr>'''
        html += '</tbody></table>'

    if not html:
        html = '<p class="placeholder">暂无板块数据</p>'

    return html


def build_fund_section(northbound, margin, lhb, sector_flow, analysis):
    """第四层：资金路线图"""
    ai_fund = analysis.get('fund_analysis', '')
    html = ''

    if ai_fund:
        html += f'<div class="analysis-text">{ai_fund}</div>'

    # 资金概览卡片
    nb_data = northbound.get('latest', {})
    nb_amount = 0
    for key in ['当日净流入', '北向资金', '净流入', '当日成交净买额']:
        if key in nb_data:
            nb_amount = safe_float(nb_data[key])
            break

    margin_balance = safe_float(margin.get('margin_balance', 0))
    margin_change = safe_float(margin.get('margin_change', 0))

    lhb_data = lhb.get('data', []) if isinstance(lhb, dict) else lhb
    lhb_count = len(lhb_data) if isinstance(lhb_data, list) else 0

    html += f'''
    <div class="fund-cards">
        <div class="fund-card">
            <div class="fund-card-label">北向资金净流入</div>
            <div class="fund-card-val {color_class(nb_amount)}">{format_amount_yi(nb_amount)}</div>
        </div>
        <div class="fund-card">
            <div class="fund-card-label">融资余额</div>
            <div class="fund-card-val">{format_amount_yi(margin_balance)}</div>
        </div>
        <div class="fund-card">
            <div class="fund-card-label">融资日变化</div>
            <div class="fund-card-val {color_class(margin_change)}">{sign_str(margin_change / 1e8)}亿</div>
        </div>
        <div class="fund-card">
            <div class="fund-card-label">龙虎榜上榜数</div>
            <div class="fund-card-val">{lhb_count}只</div>
        </div>
    </div>'''

    # 板块资金流向
    if sector_flow:
        html += '<h3 class="sub-title" style="margin-top:20px;">板块资金流向</h3>'
        html += '<table class="data-table"><thead><tr><th>板块</th><th>净流入</th></tr></thead><tbody>'
        for item in sector_flow[:10]:
            name = escape(str(item.get('名称', item.get('板块名称', ''))))
            flow = safe_float(item.get('净额', item.get('净流入', 0)))
            html += f'<tr><td>{name}</td><td class="{color_class(flow)}">{format_amount_yi(flow)}</td></tr>'
        html += '</tbody></table>'

    # 龙虎榜
    if lhb_data and isinstance(lhb_data, list) and len(lhb_data) > 0:
        html += '<h3 class="sub-title" style="margin-top:20px;">龙虎榜亮点</h3>'
        html += '<table class="data-table"><thead><tr><th>股票</th><th>上榜原因</th><th>买入额</th><th>卖出额</th></tr></thead><tbody>'
        for item in lhb_data[:8]:
            code = escape(str(item.get('代码', item.get('股票代码', ''))))
            name = escape(str(item.get('名称', item.get('股票名称', ''))))
            reason = escape(str(item.get('解读', item.get('上榜原因', ''))))
            buy = format_amount_yi(item.get('买入额', item.get('龙虎榜净买额', 0)))
            sell = format_amount_yi(item.get('卖出额', 0))
            html += f'<tr><td><strong>{name}</strong><br><small>{code}</small></td><td>{reason}</td><td class="up">{buy}</td><td class="down">{sell}</td></tr>'
        html += '</tbody></table>'

    return html


def build_technical_section(sh_index, index_data, analysis):
    """第五层：技术形态诊断"""
    ai_tech = analysis.get('technical_analysis', '')
    html = ''

    if ai_tech:
        html += f'<div class="analysis-text">{ai_tech}</div>'

    if not sh_index or not isinstance(sh_index, list) or len(sh_index) < 2:
        html += '<p class="placeholder">K线数据不足，无法进行技术分析</p>'
        return html

    latest = sh_index[-1]
    prev = sh_index[-2]
    close = safe_float(latest.get('收盘', 0))
    open_p = safe_float(latest.get('开盘', 0))
    high = safe_float(latest.get('最高', 0))
    low = safe_float(latest.get('最低', 0))
    volume = safe_float(latest.get('成交量', 0))
    prev_vol = safe_float(prev.get('成交量', volume))

    # 均线计算
    closes = [safe_float(k.get('收盘', 0)) for k in sh_index]
    ma_vals = {}
    for n in [5, 10, 20, 60]:
        if len(closes) >= n:
            ma_vals[f'MA{n}'] = round(sum(closes[-n:]) / n, 2)

    # K线形态识别
    body = abs(close - open_p)
    upper_shadow = high - max(close, open_p)
    lower_shadow = min(close, open_p) - low
    total_range = high - low if high > low else 0.01

    if total_range > 0 and body / total_range < 0.15:
        pattern = "十字星 — 多空博弈激烈，市场犹豫"
    elif close > open_p and body / open_p > 0.03:
        pattern = "大阳线 — 多头主导，强势上攻"
    elif close > open_p and body / open_p > 0.01:
        pattern = "中阳线 — 温和上涨"
    elif close < open_p and body / open_p > 0.03:
        pattern = "大阴线 — 空头主导，调整压力大"
    elif close < open_p and body / open_p > 0.01:
        pattern = "中阴线 — 偏弱震荡"
    elif lower_shadow > body * 2 and close >= open_p:
        pattern = "锤头线 — 潜在见底信号"
    elif upper_shadow > body * 2 and close <= open_p:
        pattern = "射击之星 — 高位可能反转"
    else:
        pattern = "小幅震荡 — 方向不明"

    # 量价关系
    vol_ratio = volume / prev_vol if prev_vol > 0 else 1
    if vol_ratio > 1.3 and close > open_p:
        vol_status = "放量上涨 — 量价配合良好"
    elif vol_ratio > 1.3 and close < open_p:
        vol_status = "放量下跌 — 抛压较重"
    elif vol_ratio < 0.7 and close > open_p:
        vol_status = "缩量上涨 — 追高意愿不强"
    elif vol_ratio < 0.7 and close < open_p:
        vol_status = "缩量下跌 — 惜售为主，调整温和"
    else:
        vol_status = "量能平稳"

    html += '<div class="tech-grid">'
    # 关键价位
    html += '<div class="tech-box"><h3 class="sub-title">关键价位</h3><table class="data-table">'
    html += f'<tr><td>收盘价</td><td><strong>{close:.2f}</strong></td></tr>'
    html += f'<tr><td>开盘价</td><td>{open_p:.2f}</td></tr>'
    html += f'<tr><td>最高价</td><td class="up">{high:.2f}</td></tr>'
    html += f'<tr><td>最低价</td><td class="down">{low:.2f}</td></tr>'
    html += '</table></div>'

    # 均线
    html += '<div class="tech-box"><h3 class="sub-title">均线位置</h3><table class="data-table">'
    for ma_name, ma_val in ma_vals.items():
        pos = "位于之上 ↑" if close > ma_val else "位于之下 ↓"
        css = "up" if close > ma_val else "down"
        html += f'<tr><td>{ma_name}</td><td>{ma_val:.2f}</td><td class="{css}">{pos}</td></tr>'
    html += '</table></div>'

    html += '</div>'  # tech-grid

    # 形态和量价
    html += f'''
    <div class="tech-indicators">
        <div class="tech-indicator">
            <span class="tech-ind-label">K线形态</span>
            <span class="tech-ind-val">{escape(pattern)}</span>
        </div>
        <div class="tech-indicator">
            <span class="tech-ind-label">量价关系</span>
            <span class="tech-ind-val">{escape(vol_status)}</span>
        </div>
        <div class="tech-indicator">
            <span class="tech-ind-label">量比</span>
            <span class="tech-ind-val">{vol_ratio:.2f}</span>
        </div>
    </div>'''

    return html


def build_prediction_section(analysis):
    """第六层：次日预判"""
    core = analysis.get('core_prediction', '')
    optimistic = analysis.get('optimistic_prediction', '')
    pessimistic = analysis.get('pessimistic_prediction', '')

    if not any([core, optimistic, pessimistic]):
        return '''
        <p class="placeholder">次日预判需基于当日数据和AI分析综合生成。请在analysis字段中提供：</p>
        <ul class="placeholder-list">
            <li><code>core_prediction</code> — 核心情景（60%概率）</li>
            <li><code>optimistic_prediction</code> — 乐观情景（25%概率）</li>
            <li><code>pessimistic_prediction</code> — 悲观情景（15%概率）</li>
        </ul>'''

    return f'''
    <div class="prediction-card prediction-core">
        <div class="prediction-header">
            <span class="prob-badge prob-core">60%</span>
            <strong>核心情景</strong>
        </div>
        <p>{escape(core)}</p>
    </div>
    <div class="prediction-card prediction-optimistic">
        <div class="prediction-header">
            <span class="prob-badge prob-optimistic">25%</span>
            <strong>乐观情景</strong>
        </div>
        <p>{escape(optimistic)}</p>
    </div>
    <div class="prediction-card prediction-pessimistic">
        <div class="prediction-header">
            <span class="prob-badge prob-pessimistic">15%</span>
            <strong>悲观情景</strong>
        </div>
        <p>{escape(pessimistic)}</p>
    </div>'''


def build_history_section(analysis):
    """第七层：历史对比"""
    similar = analysis.get('similar_periods', '')
    probability = analysis.get('probability_distribution', '')
    validation = analysis.get('previous_validation', '')

    if not any([similar, probability, validation]):
        return '''
        <p class="placeholder">历史对比需基于当前市场状态和历史数据分析生成。请在analysis字段中提供：</p>
        <ul class="placeholder-list">
            <li><code>similar_periods</code> — 历史相似时期</li>
            <li><code>probability_distribution</code> — 历史概率分布</li>
            <li><code>previous_validation</code> — 上期预判验证</li>
        </ul>'''

    html = ''
    if similar:
        html += f'<h3 class="sub-title">历史相似时期</h3><div class="analysis-text">{escape(similar)}</div>'
    if probability:
        html += f'<h3 class="sub-title">历史概率分布</h3><div class="analysis-text">{escape(probability)}</div>'
    if validation:
        html += f'<h3 class="sub-title">上期预判验证</h3><div class="analysis-text">{escape(validation)}</div>'
    return html


# ====================================================================
# CSS样式
# ====================================================================

CSS_STYLES = """
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
    background: #F0F4F8;
    color: #2D3748;
    line-height: 1.7;
    font-size: 15px;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 32px 40px;
}

/* Header */
.report-header {
    background: linear-gradient(135deg, #1A365D 0%, #2C5282 50%, #2B6CB0 100%);
    color: #fff;
    padding: 36px 40px;
    border-radius: 16px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}
.report-header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(255,255,255,0.06) 0%, transparent 60%);
    pointer-events: none;
}
.header-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
}
.header-top h1 {
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.5px;
}
.header-sub {
    font-size: 13px;
    opacity: 0.75;
    margin-top: 6px;
}

/* Badge */
.badge {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 600;
    white-space: nowrap;
}
.sentiment-hot { background: rgba(229,62,62,0.25); color: #FED7D7; }
.sentiment-optimistic { background: rgba(72,187,120,0.25); color: #C6F6D5; }
.sentiment-neutral { background: rgba(160,174,192,0.3); color: #E2E8F0; }
.sentiment-pessimistic { background: rgba(66,153,225,0.25); color: #BEE3F8; }
.sentiment-cold { background: rgba(128,90,213,0.25); color: #E9D8FD; }

/* Price */
.price-hero {
    display: flex;
    align-items: baseline;
    gap: 16px;
    margin-top: 20px;
}
.price-val {
    font-size: 48px;
    font-weight: 800;
    letter-spacing: -1px;
}
.price-change {
    font-size: 22px;
    font-weight: 600;
    padding: 4px 14px;
    border-radius: 8px;
}
.price-change.up { background: rgba(229,62,62,0.2); color: #FEB2B2; }
.price-change.down { background: rgba(56,161,105,0.2); color: #9AE6B4; }

/* Stats Row */
.stats-row {
    display: flex;
    gap: 12px;
    margin-top: 20px;
    flex-wrap: wrap;
}
.stat-pill {
    background: rgba(255,255,255,0.12);
    border-radius: 10px;
    padding: 10px 18px;
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 100px;
}
.stat-pill-label {
    font-size: 12px;
    opacity: 0.75;
    margin-bottom: 2px;
}
.stat-pill-val {
    font-size: 18px;
    font-weight: 700;
}

/* Cards */
.card {
    background: #fff;
    border-radius: 14px;
    padding: 28px 32px;
    margin-bottom: 24px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.03);
    transition: box-shadow 0.2s;
}
.card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.06), 0 8px 24px rgba(0,0,0,0.05); }
.card-title {
    font-size: 20px;
    font-weight: 700;
    color: #1A365D;
    margin-bottom: 20px;
    padding-bottom: 14px;
    border-bottom: 2px solid #E2E8F0;
    display: flex;
    align-items: center;
    gap: 12px;
}
.layer-num {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: #1A365D;
    color: #fff;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 700;
    flex-shrink: 0;
}

/* Sub Title */
.sub-title {
    font-size: 16px;
    font-weight: 600;
    color: #2D3748;
    margin-bottom: 12px;
}

/* Tables */
.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}
.data-table th {
    background: #F7FAFC;
    font-weight: 600;
    color: #4A5568;
    padding: 10px 14px;
    text-align: left;
    border-bottom: 2px solid #E2E8F0;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}
.data-table td {
    padding: 10px 14px;
    border-bottom: 1px solid #EDF2F7;
}
.data-table tbody tr:hover {
    background: #F7FAFC;
}
.data-table tbody tr:nth-child(even) {
    background: #FAFBFC;
}

/* Colors */
.up { color: #E53E3E; }
.down { color: #38A169; }

/* News */
.news-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 14px;
}
.news-card {
    padding: 16px;
    border-left: 3px solid #4299E1;
    background: #EBF8FF;
    border-radius: 0 8px 8px 0;
}
.news-card-title {
    font-weight: 600;
    font-size: 14px;
    margin-bottom: 6px;
    color: #1A365D;
}
.news-card-content {
    font-size: 13px;
    color: #4A5568;
    line-height: 1.6;
}

/* Sentiment Gauge */
.sentiment-gauge-wrap {
    display: flex;
    align-items: center;
    gap: 24px;
    margin-bottom: 24px;
    flex-wrap: wrap;
}
.sentiment-gauge {
    flex: 1;
    min-width: 300px;
    position: relative;
}
.gauge-fill {
    height: 14px;
    border-radius: 7px;
    background: linear-gradient(90deg, #805AD5 0%, #4299E1 25%, #A0AEC0 50%, #48BB78 75%, #E53E3E 100%);
    position: relative;
}
.gauge-fill::after {
    content: '';
    position: absolute;
    right: 0;
    top: -3px;
    width: 4px;
    height: 20px;
    background: #1A365D;
    border-radius: 2px;
}
.gauge-labels {
    display: flex;
    justify-content: space-between;
    margin-top: 4px;
    font-size: 11px;
    color: #718096;
}
.sentiment-score-big {
    font-size: 48px;
    font-weight: 800;
    color: #1A365D;
    line-height: 1;
}
.score-unit {
    font-size: 18px;
    font-weight: 400;
    color: #718096;
}
.sentiment-level-text {
    font-size: 18px;
    font-weight: 700;
    padding: 6px 16px;
    border-radius: 8px;
}
.sentiment-level-text.sentiment-hot { background: #FED7D7; color: #C53030; }
.sentiment-level-text.sentiment-optimistic { background: #C6F6D5; color: #276749; }
.sentiment-level-text.sentiment-neutral { background: #E2E8F0; color: #4A5568; }
.sentiment-level-text.sentiment-pessimistic { background: #BEE3F8; color: #2B6CB0; }
.sentiment-level-text.sentiment-cold { background: #E9D8FD; color: #6B46C1; }

/* Fund cards */
.fund-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 14px;
}
.fund-card {
    background: #F7FAFC;
    border-radius: 10px;
    padding: 18px;
    text-align: center;
}
.fund-card-label {
    font-size: 13px;
    color: #718096;
    margin-bottom: 6px;
}
.fund-card-val {
    font-size: 22px;
    font-weight: 700;
    color: #1A365D;
}

/* Technical */
.tech-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
}
.tech-box {
    background: #F7FAFC;
    border-radius: 10px;
    padding: 18px;
}
.tech-indicators {
    display: flex;
    gap: 14px;
    margin-top: 20px;
    flex-wrap: wrap;
}
.tech-indicator {
    flex: 1;
    min-width: 200px;
    background: #F7FAFC;
    border-radius: 10px;
    padding: 14px 18px;
}
.tech-ind-label {
    font-size: 12px;
    color: #718096;
    display: block;
    margin-bottom: 4px;
}
.tech-ind-val {
    font-size: 14px;
    font-weight: 600;
    color: #2D3748;
}

/* Predictions */
.prediction-card {
    padding: 18px 22px;
    border-radius: 10px;
    margin-bottom: 12px;
}
.prediction-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
}
.prediction-card p {
    font-size: 14px;
    line-height: 1.7;
    color: #2D3748;
}
.prediction-core { background: #F0FFF4; border-left: 4px solid #48BB78; }
.prediction-optimistic { background: #FFFFF0; border-left: 4px solid #ECC94B; }
.prediction-pessimistic { background: #FFF5F5; border-left: 4px solid #F56565; }

.prob-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 4px;
    font-size: 13px;
    font-weight: 700;
    color: #fff;
}
.prob-core { background: #48BB78; }
.prob-optimistic { background: #ECC94B; color: #744210; }
.prob-pessimistic { background: #F56565; }

/* Analysis text */
.analysis-text {
    font-size: 14px;
    line-height: 1.8;
    color: #2D3748;
    margin-bottom: 16px;
    white-space: pre-wrap;
}

/* Placeholder */
.placeholder {
    color: #A0AEC0;
    font-style: italic;
    font-size: 14px;
}
.placeholder-list {
    color: #A0AEC0;
    font-size: 13px;
    margin-top: 8px;
    padding-left: 20px;
}
.placeholder-list li { margin-bottom: 4px; }

/* Footer */
footer {
    text-align: center;
    padding: 28px 16px;
    color: #A0AEC0;
    font-size: 13px;
    border-top: 1px solid #E2E8F0;
    margin-top: 16px;
}
footer p { margin-bottom: 4px; }

/* Responsive */
@media (max-width: 768px) {
    .container { padding: 16px; }
    .report-header { padding: 24px; }
    .header-top h1 { font-size: 22px; }
    .price-val { font-size: 36px; }
    .card { padding: 20px; }
    .stats-row { gap: 8px; }
    .stat-pill { min-width: 80px; padding: 8px 12px; }
    .fund-cards { grid-template-columns: repeat(2, 1fr); }
    .tech-grid { grid-template-columns: 1fr; }
    .news-grid { grid-template-columns: 1fr; }
}
"""


def main():
    parser = argparse.ArgumentParser(description='生成A股日报HTML报告')
    parser.add_argument('--input', '-i', required=True, help='输入数据JSON文件路径')
    parser.add_argument(
        '--output', '-o', default='market_debrief.html', help='输出HTML文件路径')
    parser.add_argument('--title', '-t', help='报告标题（默认自动生成）')

    args = parser.parse_args()

    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)

        output_path = generate_html_report(data, args.output, args.title)
        print(f"成功生成报告: {output_path}")

    except FileNotFoundError:
        print(f"错误: 输入文件不存在 - {args.input}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"错误: JSON解析失败 - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
