#!/usr/bin/env python3
"""
A股日报数据分析脚本 - 量化指标计算引擎

从 fetch_market_data.py 生成的 market_data_YYYY-MM-DD.json 中读取原始数据，
输出一份结构化的 analysis_YYYY-MM-DD.json，包含所有供 AI Subagent 直接使用的
量化指标和特征，大幅提升分析深度与效率。

覆盖指标：
  - 情绪评分系统（综合分、散户分、机构分、各分项、60日百分位）
  - 技术状态矩阵（MA偏离度、均线排列、量比、K线形态）
  - 支撑/压力位计算（MA/斐波那契/VWAP/整数关口）
  - 日内/隔夜涨幅拆解
  - 行业强弱四分类 + 成长/价值风格计算
  - 资金结构分析（超大/大/中/小单行为判断）
  - 资金迁移路线（来源板块 TOP3 vs 目标板块 TOP3）
  - 涨停板生态（封板率、连板分布、主题集中度、赚钱效应）
  - 估值水位（PE/PB 历史百分位）
  - 股债性价比 ERP（含历史均值、发出信号）
  - 北向资金20日趋势

用法：
  python scripts/analyze_market.py --date YYYYMMDD
  python scripts/analyze_market.py --input assets/market_data_2026-03-12.json
"""

import argparse
import json
import sys
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings("ignore")

SKILL_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = SKILL_ROOT / "assets"

try:
    import numpy as np
    import pandas as pd
except ImportError:
    print("请先安装依赖: pip install numpy pandas", file=sys.stderr)
    sys.exit(1)


# ── 常量 ──────────────────────────────────────────────────────

# 申万一级行业：成长/价值分类（经验聚类）
GROWTH_SECTORS = {"电子", "计算机", "通信", "国防军工", "医药生物", "电力设备", "新能源"}
VALUE_SECTORS = {"银行", "非银金融", "房地产", "建筑装饰",
                 "公用事业", "交通运输", "采掘", "钢铁", "建筑材料"}

# 整数关口（用于识别心理关口压力位/支撑位）
ROUND_LEVELS = {
    "上证指数": [2800, 3000, 3200, 3500, 3800, 4000, 4200, 4500],
    "沪深300": [3200, 3500, 3800, 4000, 4200, 4500],
    "创业板指": [1600, 1800, 2000, 2200, 2500, 3000],
    "科创50": [700, 800, 900, 1000, 1100],
}

# ── 工具函数 ──────────────────────────────────────────────────


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def to_df(records: list, date_col: str = "date") -> pd.DataFrame:
    """list[dict] → DataFrame，解析日期索引"""
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.sort_values(date_col).reset_index(drop=True)
    return df


def percentile_rank(series: pd.Series, value: float) -> float:
    """value 在 series 中的历史百分位（0-1）"""
    if series.empty or len(series) < 2:
        return 0.5
    return float((series < value).mean())


def linear_score(value: float, lo: float, hi: float,
                 score_lo: float = 10.0, score_hi: float = 90.0) -> float:
    """将 value 线性映射到 [score_lo, score_hi] 区间，超出范围截断"""
    if hi == lo:
        return (score_lo + score_hi) / 2
    ratio = (value - lo) / (hi - lo)
    return float(np.clip(score_lo + ratio * (score_hi - score_lo), score_lo, score_hi))


def parse_cn_number(value):
    """解析包含中文单位的数值字符串（亿/万/千）为绝对数值。"""
    if value is None:
        return np.nan
    if isinstance(value, (int, float, np.number)):
        return float(value)
    s = str(value).strip().replace(",", "")
    if not s:
        return np.nan

    multiplier = 1.0
    if s.endswith("亿"):
        multiplier = 1e8
        s = s[:-1]
    elif s.endswith("万"):
        multiplier = 1e4
        s = s[:-1]
    elif s.endswith("千"):
        multiplier = 1e3
        s = s[:-1]
    elif s.endswith("%"):
        s = s[:-1]

    try:
        return float(s) * multiplier
    except ValueError:
        return np.nan


# ── 1. 情绪评分系统 ───────────────────────────────────────────

def calc_sentiment(data: dict) -> dict:
    """
    计算综合情绪分（0-100）以及散户分/机构分，
    并给出5日趋势序列、60日百分位、趋势斜率描述。
    """
    result = {}

    # -- 成交额/量 vs 20日均值 (权重 20%)
    mff = to_df(data.get("market_fund_flow", []))
    vol_score = 50.0
    turnover = None

    if not mff.empty and "成交额" in mff.columns:
        turnover = mff["成交额"].astype(float)
    else:
        sz_daily = to_df(data.get("index_daily", {}).get("上证指数", []))
        if not sz_daily.empty and "volume" in sz_daily.columns:
            turnover = sz_daily["volume"].astype(float)

    if turnover is not None and not turnover.empty:
        latest_turn = turnover.iloc[-1]
        ma20_turn = turnover.tail(
            21).iloc[:-1].mean() if len(turnover) > 20 else turnover.mean()
        ratio_turn = latest_turn / ma20_turn if ma20_turn > 0 else 1.0
        vol_score = linear_score(ratio_turn, 0.5, 1.5)
        result["turnover_latest"] = round(float(latest_turn), 2)
        result["turnover_ma20"] = round(float(ma20_turn), 2)
        result["turnover_ratio"] = round(float(ratio_turn), 3)

    # -- 涨停/跌停比 (权重 15%)
    zt = data.get("limit_up", {})
    dt = data.get("limit_down", {})
    zt_count = zt.get("count", 0)
    dt_count = dt.get("count", 0)
    zt_dt_ratio = zt_count / max(dt_count, 1)
    zt_dt_score = linear_score(zt_dt_ratio, 0.2, 5.0)

    # -- 封板率 (权重 15%)
    broken = data.get("broken_limit", {})
    broken_count = broken.get("count", 0)
    seal_rate = zt_count / max(zt_count + broken_count, 1)
    seal_score = linear_score(seal_rate, 0.2, 0.8)

    # -- 两融余额变化（亿元/日，权重 15%）
    margin = to_df(data.get("margin", []))
    margin_score = 50.0
    margin_daily_change = 0.0
    if not margin.empty:
        bal_col = next((c for c in margin.columns if "余额" in c), None)
        if bal_col:
            bal = margin[bal_col].astype(float)
            if len(bal) >= 2:
                margin_daily_change = float(bal.iloc[-1] - bal.iloc[-2])
                # 单位: 亿元；±50亿 → score 80/20
                margin_score = linear_score(margin_daily_change / 1e8, -50, 50)

    # -- 北向资金净额（亿元/日，权重 15%）
    nb_score = 50.0
    nb_net_today = 0.0
    nb = data.get("northbound", {})
    if nb:
        frames = []
        for channel_data in nb.values():
            frames.append(to_df(channel_data))
        if frames:
            nb_all = pd.concat(frames)
            net_col = next(
                (c for c in nb_all.columns if "净买入" in c or "净额" in c), None)
            if net_col:
                nb_all[net_col] = pd.to_numeric(
                    nb_all[net_col], errors="coerce")
                nb_net_today = float(nb_all.tail(2).groupby(nb_all.tail(2).columns[0])[
                                     net_col].sum().iloc[-1]) if len(nb_all) > 1 else 0.0
                nb_score = linear_score(nb_net_today / 1e8, -50, 50)

    # -- 超大单净流方向（权重 10%）
    super_score = 50.0
    super_net = 0.0
    if not mff.empty:
        sf_col = next(
            (c for c in mff.columns if "超大单" in c and "净" in c), None)
        if sf_col:
            sv = mff[sf_col].astype(float)
            super_net = float(sv.iloc[-1])
            super_score = linear_score(super_net / 1e8, -100, 100, 30, 70)

    # -- 市场广度（上涨家数占比，权重 15%）
    breadth_score = 50.0
    breadth_up_ratio = None
    breadth = data.get("market_breadth", {})
    if isinstance(breadth, dict):
        up_ratio = breadth.get("up_ratio")
        if up_ratio is not None:
            breadth_up_ratio = float(up_ratio)
            breadth_score = linear_score(breadth_up_ratio, 0.30, 0.70)

    # -- 综合加权
    composite = (
        vol_score * 0.20
        + zt_dt_score * 0.15
        + seal_score * 0.15
        + margin_score * 0.10
        + nb_score * 0.15
        + super_score * 0.10
        + breadth_score * 0.15
    )
    composite = round(composite, 1)

    # -- 散户分 / 机构分
    retail_score = round(
        (zt_dt_score * 0.33 + seal_score * 0.33 + margin_score * 0.34), 1)
    inst_score = round((nb_score * 0.5 + super_score * 0.5), 1)

    divergence = _classify_divergence(retail_score, inst_score)

    result.update({
        "composite_score": composite,
        "retail_score": retail_score,
        "institutional_score": inst_score,
        "divergence_type": divergence,
        "component_scores": {
            "turnover_vs_ma20": round(vol_score, 1),
            "zt_dt_ratio": round(zt_dt_score, 1),
            "seal_rate": round(seal_score, 1),
            "margin_change": round(margin_score, 1),
            "northbound": round(nb_score, 1),
            "super_large_flow": round(super_score, 1),
            "market_breadth": round(breadth_score, 1),
        },
        "raw_values": {
            "zt_count": zt_count,
            "dt_count": dt_count,
            "zt_dt_ratio": round(zt_dt_ratio, 2),
            "seal_rate_pct": round(seal_rate * 100, 1),
            "broken_count": broken_count,
            "margin_daily_change_yi": round(margin_daily_change / 1e8, 2),
            "northbound_net_today_yi": round(nb_net_today / 1e8, 2),
            "super_large_net_yi": round(super_net / 1e8, 2),
            "breadth_up_ratio": round(breadth_up_ratio, 4) if breadth_up_ratio is not None else None,
            "breadth_down_ratio": breadth.get("down_ratio") if isinstance(breadth, dict) else None,
        },
    })
    return result


def _classify_divergence(retail: float, inst: float) -> str:
    if retail >= 60 and inst >= 60:
        return "共识多头"
    if retail <= 40 and inst <= 40:
        return "共识空头"
    if retail >= 60 and inst <= 40:
        return "散户热机构冷"
    if retail <= 40 and inst >= 60:
        return "散户冷机构热"
    return "情绪中性"


# ── 2. 技术状态矩阵 ───────────────────────────────────────────

def calc_technical(data: dict) -> dict:
    """
    对 6 大指数计算：MA偏离度、均线排列、量比、K线形态、
    支撑/压力位（MA/斐波那契/VWAP_近似/整数关口）、
    日内/隔夜涨幅拆解。
    """
    index_daily = data.get("index_daily", {})
    result = {}

    for name, records in index_daily.items():
        df = to_df(records, date_col="date")
        if df.empty or "close" not in df.columns:
            continue

        close = df["close"].astype(float)
        high = df["high"].astype(float) if "high" in df.columns else close
        low = df["low"].astype(float) if "low" in df.columns else close
        open_ = df["open"].astype(float) if "open" in df.columns else close
        volume = df["volume"].astype(
            float) if "volume" in df.columns else pd.Series([1.0] * len(df))

        latest_close = float(close.iloc[-1])
        latest_open = float(open_.iloc[-1])
        prev_close = float(close.iloc[-2]) if len(close) >= 2 else latest_close

        # MA 计算
        ma = {}
        for n in [5, 10, 20, 60, 120, 250]:
            if len(close) >= n:
                ma[f"ma{n}"] = round(
                    float(close.tail(n + 1).iloc[:-1].mean()), 2)

        # MA 偏离度
        deviation = {}
        for n in [5, 20, 60, 250]:
            key = f"ma{n}"
            if key in ma and ma[key] > 0:
                deviation[f"ma{n}_dev_pct"] = round(
                    (latest_close - ma[key]) / ma[key] * 100, 2)

        # 均线排列判断
        arrangement = _judge_ma_arrangement(latest_close, ma)

        # 量比（今日成交量 / 5日平均成交量）及量价配合度（速度与加速度）
        vol_ratio = 1.0
        volume_price_desc = "数据不足"
        if len(volume) >= 6:
            avg5 = float(volume.tail(6).iloc[:-1].mean())
            vol_ratio = round(
                float(volume.iloc[-1]) / avg5, 2) if avg5 > 0 else 1.0

        # 预先计算总涨跌幅用于量价配合度判断
        total_chg = round((latest_close - prev_close) / prev_close * 100, 2)

        if vol_ratio > 1.2 and total_chg > 0.5:
            volume_price_desc = "放量上涨 (多头确认/入场)"
        elif vol_ratio > 1.2 and total_chg < -0.5:
            volume_price_desc = "放量下跌 (恐慌/抛压沉重)"
        elif vol_ratio < 0.8 and total_chg > 0.5:
            volume_price_desc = "缩量上涨 (跟风不足/抛压轻)"
        elif vol_ratio < 0.8 and total_chg < -0.5:
            volume_price_desc = "缩量下跌 (抛压衰竭/情绪低迷)"
        elif vol_ratio >= 1.5 and abs(total_chg) <= 0.5:
            volume_price_desc = "放量滞涨 (资金现强分歧)"
        elif vol_ratio <= 0.8 and abs(total_chg) <= 0.5:
            volume_price_desc = "地量震荡 (变盘前兆)"
        else:
            volume_price_desc = "量价平稳"

        # K线形态识别
        kline_pattern = _identify_kline_pattern(
            open_=latest_open, close=latest_close,
            high=float(high.iloc[-1]), low=float(low.iloc[-1])
        )

        # 日内/隔夜涨幅拆解
        overnight_chg = round((latest_open - prev_close) / prev_close * 100, 2)
        intraday_chg = round(
            (latest_close - latest_open) / latest_open * 100, 2)

        # 支撑/压力位
        supports, resistances = _calc_key_levels(
            close=close, high=high, low=low, volume=volume,
            latest_close=latest_close, ma=ma,
            index_name=name
        )

        result[name] = {
            "latest_close": latest_close,
            "total_chg_pct": total_chg,
            "overnight_chg_pct": overnight_chg,
            "intraday_chg_pct": intraday_chg,
            "ma": ma,
            "ma_deviations": deviation,
            "ma_arrangement": arrangement,
            "volume_ratio": vol_ratio,
            "volume_price_desc": volume_price_desc,
            "kline_pattern": kline_pattern,
            "supports": supports,
            "resistances": resistances,
        }

    return result


def _judge_ma_arrangement(close: float, ma: dict) -> str:
    """判断均线排列：多头/空头/粘合"""
    ma5 = ma.get("ma5")
    ma20 = ma.get("ma20")
    ma60 = ma.get("ma60")
    if None in (ma5, ma20, ma60):
        return "数据不足"
    # 各均线之间偏差全部小于1%则认为粘合
    spread = abs(ma5 - ma60) / ma60 * 100
    if spread < 1.5:
        return "粘合"
    if ma5 > ma20 > ma60:
        return "多头排列"
    if ma5 < ma20 < ma60:
        return "空头排列"
    if ma5 > ma20 and ma20 < ma60:
        return "短线反弹，中期仍弱"
    if ma5 < ma20 and ma20 > ma60:
        return "短线调整，中期仍强"
    return "多空交织"


def _identify_kline_pattern(open_: float, close: float, high: float, low: float) -> dict:
    """识别当日K线主要形态，返回 {name, bearish_signal, probability_hint, explanation}"""
    body = close - open_
    body_abs = abs(body)
    upper_shadow = high - max(open_, close)
    lower_shadow = min(open_, close) - low
    total_range = high - low if high > low else 1e-9

    pct_chg = body / open_ * 100

    name = "普通K线"
    probability_hint = ""
    explanation = ""

    if body_abs / open_ * 100 >= 2.0 and upper_shadow / body_abs < 0.5 and lower_shadow / body_abs < 0.5:
        if body > 0:
            name = "大阳线"
            probability_hint = "后3日继续上涨概率 ~55%"
            explanation = "实体涨幅 ≥2%，上下影线短，多头强势"
        else:
            name = "大阴线"
            probability_hint = "后3日继续下跌概率 ~50%"
            explanation = "实体跌幅 ≥2%，上下影线短，空头主导"
    elif upper_shadow > body_abs * 2 and upper_shadow / total_range > 0.4:
        name = "长上影线"
        probability_hint = "3日内回调概率 ~65%"
        explanation = "上影线>实体2倍，上方压力显著，警惕回落"
    elif lower_shadow > body_abs * 2 and lower_shadow / total_range > 0.4:
        name = "长下影线"
        probability_hint = "3日内反弹概率 ~60%"
        explanation = "下影线>实体2倍，下方有强支撑，关注低吸机会"
    elif body_abs / open_ * 100 < 0.3 and upper_shadow > 0 and lower_shadow > 0:
        name = "十字星"
        probability_hint = "变盘信号，方向看后续量能"
        explanation = "实体极小，多空势均力敌，次日方向需量能确认"
    elif lower_shadow >= body_abs * 2 and body > 0 and upper_shadow < body_abs:
        name = "锤子线"
        probability_hint = "底部反转信号概率 ~58%"
        explanation = "下影线长、实体在上方，低位出现时为底部反转信号"
    elif upper_shadow >= body_abs * 2 and body < 0 and lower_shadow < body_abs:
        name = "上吊线"
        probability_hint = "顶部反转信号概率 ~52%"
        explanation = "高位出现，上方承压，注意顶部形态"

    return {
        "name": name,
        "pct_change": round(pct_chg, 2),
        "body_pct": round(body_abs / open_ * 100, 2),
        "upper_shadow_pct": round(upper_shadow / open_ * 100, 2),
        "lower_shadow_pct": round(lower_shadow / open_ * 100, 2),
        "probability_hint": probability_hint,
        "explanation": explanation,
    }


def _calc_key_levels(close, high, low, volume, latest_close, ma, index_name):
    """计算支撑位和压力位（MA / 斐波那契 / VWAP近似 / 整数关口）"""
    supports = []
    resistances = []

    # 1. MA 支撑/压力
    for n, label in [(5, "MA5"), (20, "MA20"), (60, "MA60"), (250, "MA250")]:
        val = ma.get(f"ma{n}")
        if val is None:
            continue
        dist_pct = round((val - latest_close) / latest_close * 100, 2)
        entry = {"level": val, "type": label, "distance_pct": dist_pct}
        if val < latest_close:
            supports.append(entry)
        else:
            resistances.append(entry)

    # 2. 斐波那契回撤位（基于近60日高低点）
    n60 = min(60, len(close))
    if n60 >= 20:
        period_high = float(high.tail(n60).max())
        period_low = float(low.tail(n60).min())
        swings = period_high - period_low
        for ratio, label in [(0.382, "Fib38.2%"), (0.500, "Fib50.0%"), (0.618, "Fib61.8%")]:
            fib_level = round(period_high - swings * ratio, 2)
            dist_pct = round((fib_level - latest_close) /
                             latest_close * 100, 2)
            entry = {"level": fib_level, "type": label,
                     "distance_pct": dist_pct}
            if fib_level < latest_close:
                supports.append(entry)
            else:
                resistances.append(entry)

    # 3. VWAP近似（近30日成交量加权均价）
    n30 = min(30, len(close))
    if n30 >= 5:
        c30 = close.tail(n30).values.astype(float)
        v30 = volume.tail(n30).values.astype(float)
        vwap_val = round(float(np.average(c30, weights=v30)),
                         2) if v30.sum() > 0 else None
        if vwap_val:
            dist_pct = round((vwap_val - latest_close) / latest_close * 100, 2)
            entry = {"level": vwap_val, "type": "VWAP30日",
                     "distance_pct": dist_pct}
            if vwap_val < latest_close:
                supports.append(entry)
            else:
                resistances.append(entry)

    # 4. 整数关口
    round_levels = ROUND_LEVELS.get(index_name, [])
    for lvl in round_levels:
        dist_pct = round((lvl - latest_close) / latest_close * 100, 2)
        if abs(dist_pct) <= 8.0:  # 只取8%以内的关口
            entry = {"level": lvl, "type": "整数关口", "distance_pct": dist_pct}
            if lvl < latest_close:
                supports.append(entry)
            else:
                resistances.append(entry)

    # 按距离排序（最近的排在最前）
    supports = sorted(supports, key=lambda x: abs(x["distance_pct"]))[:5]
    resistances = sorted(resistances, key=lambda x: abs(x["distance_pct"]))[:5]

    return supports, resistances


# ── 3. 估值 & 股债性价比 ERP ──────────────────────────────────

def calc_valuation(data: dict) -> dict:
    """计算各指数PE历史百分位、全A PB百分位、ERP及信号"""
    result = {}

    # PE 百分位（已在 fetch 脚本中算入 recent_60）
    pe_data = data.get("index_pe", {})
    pe_result = {}
    for idx_name, info in pe_data.items():
        if not info:
            continue
        latest = info.get("latest", {})
        recent = to_df(info.get("recent_60", []))
        pe_col = "滚动市盈率"
        current_pe = None
        pe_pct = None
        for k, v in latest.items():
            if "市盈率" in k or "PE" in k.upper():
                try:
                    current_pe = float(v)
                except (TypeError, ValueError):
                    pass
        if pe_col in recent.columns and current_pe is not None:
            pe_pct = round(percentile_rank(
                recent[pe_col].astype(float), current_pe) * 100, 1)
        pe_result[idx_name] = {
            "current_pe": current_pe,
            "pe_percentile_60d": pe_pct,
            "pe_zone": _pe_zone(pe_pct),
        }
    result["index_pe"] = pe_result

    # 全A PB
    pb_raw = data.get("all_a_pb")
    if pb_raw:
        pb_val = None
        for k, v in pb_raw.items():
            if "PB" in k.upper() or "市净率" in k:
                try:
                    pb_val = float(v)
                except (TypeError, ValueError):
                    pass
        result["all_a_pb"] = {"current_pb": pb_val}
    else:
        result["all_a_pb"] = {}

    # ERP = 1/PE(沪深300) - 10年期国债收益率
    bond = to_df(data.get("bond_yield", []))
    erp_result = {}
    hs300_pe = pe_result.get("沪深300", {}).get("current_pe")
    if hs300_pe and hs300_pe > 0 and not bond.empty:
        yield_col = next((c for c in bond.columns if "10年" in c), None)
        if yield_col:
            bond[yield_col] = pd.to_numeric(bond[yield_col], errors="coerce")
            bond_yield_latest = float(
                bond[yield_col].dropna().iloc[-1]) / 100  # 转为小数
            earnings_yield = 1.0 / hs300_pe
            erp = round((earnings_yield - bond_yield_latest) * 100, 3)  # 百分比
            # 历史 ERP 近似（用近60条）
            erp_history = (1.0 / pd.to_numeric(
                to_df(pe_data.get("沪深300", {}).get("recent_60", []))
                .get("滚动市盈率", pd.Series(dtype=float)), errors="coerce"
            ).dropna() - bond_yield_latest) * 100
            erp_mean = round(float(erp_history.mean()), 3) if len(
                erp_history) > 5 else None
            erp_std = round(float(erp_history.std()), 3) if len(
                erp_history) > 5 else None
            erp_signal = _erp_signal(erp, erp_mean, erp_std)
            erp_result = {
                "erp_pct": erp,
                "earnings_yield_pct": round(earnings_yield * 100, 3),
                "bond_yield_10y_pct": round(bond_yield_latest * 100, 3),
                "erp_mean_60d": erp_mean,
                "erp_std_60d": erp_std,
                "erp_signal": erp_signal,
            }
    result["erp"] = erp_result

    return result


def _pe_zone(pe_pct):
    if pe_pct is None:
        return "数据不足"
    if pe_pct < 30:
        return "历史低位（安全边际较高）"
    if pe_pct < 60:
        return "历史中位（估值中性）"
    return "历史高位（需警惕估值风险）"


def _erp_signal(erp, mean, std):
    if mean is None or std is None:
        return "数据不足"
    if erp > mean + std:
        return "股票极具配置价值（ERP > 均值+1σ）"
    if erp > mean:
        return "股票性价比偏高"
    if erp > mean - std:
        return "股债中性"
    return "债券性价比更优（ERP < 均值-1σ）"


# ── 4. 行业分析 ───────────────────────────────────────────────

def calc_industry(data: dict) -> dict:
    """
    行业强弱四分类、成长/价值风格计算、资金流向 TOP/BOTTOM 榜。
    """
    # 优先使用 sector_fund_flow (含涨跌幅和资金流)，不再依赖 industry_board
    board = to_df(data.get("sector_fund_flow", []))
    sector_flow = board.copy()
    # 为兼容旧代码，保留 data.get("industry_board", []) 读取，但 fetch_market_data.py 已移除该字段
    if board.empty:
        board = to_df(data.get("industry_board", []))
        sector_flow = board.copy()

    result = {}
    if board.empty:
        return result

    # 寻找涨跌幅列
    # stock_sector_fund_flow_rank 通常包含 "今日涨跌幅"
    chg_col = next((c for c in board.columns if "涨跌幅" in c), None)
    name_col = next(
        (c for c in board.columns if "板块" in c or "行业" in c or "名称" in c), None)

    if not chg_col or not name_col:
        return result

    # 转换涨跌幅为 float (需处理 % 号)
    def parse_chg(val):
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            val = val.replace("%", "")
            try:
                return float(val)
            except:
                return 0.0
        return 0.0

    board[chg_col] = board[chg_col].apply(parse_chg)
    board = board.dropna(subset=[chg_col])

    # 四分类
    heatmap = {
        "strong": [],   # ≥ +2%
        "moderate": [],  # +0.5% ~ +2%
        "neutral": [],  # -0.5% ~ +0.5%
        "weak": [],     # ≤ -0.5%
    }
    for _, row in board.iterrows():
        name = str(row[name_col])
        chg = float(row[chg_col])
        entry = {"name": name, "chg_pct": round(chg, 2)}
        if chg >= 2.0:
            heatmap["strong"].append(entry)
        elif chg >= 0.5:
            heatmap["moderate"].append(entry)
        elif chg > -0.5:
            heatmap["neutral"].append(entry)
        else:
            heatmap["weak"].append(entry)

    # 各档按涨幅降序
    for k in heatmap:
        heatmap[k] = sorted(heatmap[k], key=lambda x: -x["chg_pct"])

    result["heatmap"] = heatmap
    result["strong_count"] = len(heatmap["strong"])
    result["weak_count"] = len(heatmap["weak"])

    # 成长/价值风格
    growth_chgs = [r["chg_pct"] for r in heatmap["strong"] + heatmap["moderate"] + heatmap["neutral"] + heatmap["weak"]
                   if any(g in r["name"] for g in GROWTH_SECTORS)]
    value_chgs = [r["chg_pct"] for r in heatmap["strong"] + heatmap["moderate"] + heatmap["neutral"] + heatmap["weak"]
                  if any(v in r["name"] for v in VALUE_SECTORS)]
    growth_avg = round(sum(growth_chgs) / len(growth_chgs),
                       2) if growth_chgs else None
    value_avg = round(sum(value_chgs) / len(value_chgs),
                      2) if value_chgs else None
    style_spread = round(growth_avg - value_avg,
                         2) if (growth_avg is not None and value_avg is not None) else None
    if style_spread is not None:
        if style_spread > 1.0:
            style_dominant = "成长占优"
        elif style_spread < -1.0:
            style_dominant = "价值占优"
        else:
            style_dominant = "均衡"
    else:
        style_dominant = "数据不足"

    result["style"] = {
        "growth_avg_chg": growth_avg,
        "value_avg_chg": value_avg,
        "spread": style_spread,
        "dominant": style_dominant,
    }

    # 行业资金流向 TOP/BOTTOM
    if not sector_flow.empty:
        net_col = next(
            (c for c in sector_flow.columns if "净额" in c or "净流入" in c), None)
        sf_name_col = next(
            (c for c in sector_flow.columns if "板块" in c or "行业" in c or "名称" in c), None)
        if net_col and sf_name_col:
            sector_flow[net_col] = sector_flow[net_col].apply(parse_cn_number)
            sector_flow = sector_flow.dropna(subset=[net_col])
            top3_in = sector_flow.nlargest(
                3, net_col)[[sf_name_col, net_col]].to_dict("records")
            top3_out = sector_flow.nsmallest(
                3, net_col)[[sf_name_col, net_col]].to_dict("records")
            result["fund_flow_top3_inflow"] = [
                {"name": str(r[sf_name_col]), "net_yi": round(float(r[net_col]) / 1e8, 2)} for r in top3_in
            ]
            result["fund_flow_top3_outflow"] = [
                {"name": str(r[sf_name_col]), "net_yi": round(float(r[net_col]) / 1e8, 2)} for r in top3_out
            ]
            # 迁移路线判断
            migration_type = _judge_migration(
                [r["name"] for r in result["fund_flow_top3_outflow"]],
                [r["name"] for r in result["fund_flow_top3_inflow"]],
            )
            result["migration_type"] = migration_type

    return result


def _judge_migration(out_sectors: list, in_sectors: list) -> str:
    offensive = {"电子", "计算机", "通信", "国防军工", "医药生物", "电力设备"}
    defensive = {"银行", "非银金融", "公用事业", "食品饮料", "家用电器"}
    out_off = any(any(o in s for o in offensive) for s in out_sectors)
    out_def = any(any(d in s for d in defensive) for s in out_sectors)
    in_off = any(any(o in s for o in offensive) for s in in_sectors)
    in_def = any(any(d in s for d in defensive) for s in in_sectors)

    if out_off and in_def:
        return "进攻→防御（Risk-off）"
    if out_def and in_off:
        return "防御→进攻（Risk-on）"
    if not in_off and not in_def:
        return "整体出场"
    return "行业内轮动"


# ── 5. 涨停板生态 ─────────────────────────────────────────────

def calc_limit_up_ecology(data: dict) -> dict:
    """
    分析涨停板生态：连板分布、封板率、炸板率、主题集中度、赚钱效应评级。
    """
    zt = data.get("limit_up", {})
    dt = data.get("limit_down", {})
    broken = data.get("broken_limit", {})
    strong = to_df(data.get("strong_limit_up", []))

    zt_stocks = zt.get("stocks", [])
    zt_count = zt.get("count", 0)
    dt_count = dt.get("count", 0)
    broken_count = broken.get("count", 0)

    seal_rate = round(zt_count / max(zt_count + broken_count, 1) * 100, 1)

    # 连板分布（从强势连板数据中统计）
    consecutive_dist = {"first_board": 0,
                        "2_board": 0, "3_board": 0, "4plus_board": 0}
    max_consecutive = 1
    highest_stock = ""
    if not strong.empty:
        # 寻找连板数列
        cont_col = next(
            (c for c in strong.columns if "连板" in c or "天数" in c), None)
        name_col = next(
            (c for c in strong.columns if "名称" in c or "股票名" in c), None)
        if cont_col and name_col:
            strong[cont_col] = pd.to_numeric(strong[cont_col], errors="coerce")
            for _, row in strong.dropna(subset=[cont_col]).iterrows():
                n = int(row[cont_col])
                if n >= 4:
                    consecutive_dist["4plus_board"] += 1
                elif n == 3:
                    consecutive_dist["3_board"] += 1
                elif n == 2:
                    consecutive_dist["2_board"] += 1
                if n > max_consecutive:
                    max_consecutive = n
                    try:
                        highest_stock = str(row[name_col])
                    except Exception:
                        pass

    # 首板估算（总涨停 - 连板）
    multi_board = consecutive_dist["2_board"] + \
        consecutive_dist["3_board"] + consecutive_dist["4plus_board"]
    consecutive_dist["first_board"] = max(zt_count - multi_board, 0)

    # 主题集中度（基于涨停池的概念/行业）
    theme_concentration = None
    if zt_stocks:
        theme_col = next((k for k in (zt_stocks[0].keys() if zt_stocks else [])
                          if "题材" in k or "概念" in k or "行业" in k), None)
        if theme_col:
            themes = [str(s.get(theme_col, ""))
                      for s in zt_stocks if s.get(theme_col)]
            if themes:
                from collections import Counter
                top_theme, top_count = Counter(themes).most_common(1)[0]
                theme_concentration = {
                    "top_theme": top_theme,
                    "count": top_count,
                    "pct": round(top_count / len(themes) * 100, 1),
                }

    # 赚钱效应评级
    profit_effect = _judge_profit_effect(seal_rate, zt_count, max_consecutive)

    return {
        "zt_count": zt_count,
        "dt_count": dt_count,
        "broken_count": broken_count,
        "seal_rate_pct": seal_rate,
        "consecutive_distribution": consecutive_dist,
        "max_consecutive_boards": max_consecutive,
        "highest_consecutive_stock": highest_stock,
        "theme_concentration": theme_concentration,
        "profit_effect": profit_effect,
        "profit_effect_explanation": _profit_effect_explanation(seal_rate, zt_count, max_consecutive),
    }


def _judge_profit_effect(seal_rate: float, zt_count: int, max_consec: int) -> str:
    if seal_rate >= 70 and zt_count >= 50 and max_consec >= 5:
        return "强"
    if seal_rate >= 50 and zt_count >= 30 and max_consec >= 3:
        return "中"
    return "弱"


def _profit_effect_explanation(seal_rate: float, zt_count: int, max_consec: int) -> str:
    return (f"封板率{seal_rate}%，涨停数{zt_count}只，"
            f"最高连板{max_consec}连板。"
            + ("积极入场信号。" if seal_rate >= 70 and zt_count >= 50 else
               "精选题材为主。" if seal_rate >= 50 else "观望为主，追板风险高。"))


# ── 6. 资金结构分析 ───────────────────────────────────────────

def calc_fund_structure(data: dict) -> dict:
    """
    全市场超大/大/中/小单净流入、行为类型判断、30日趋势的
    描述性统计。
    """
    mff = to_df(data.get("market_fund_flow", []))
    if mff.empty:
        return {}

    # 找各类净流入列
    def find_col(df, keywords):
        for c in df.columns:
            if all(k in c for k in keywords):
                return c
        return None

    col_super = find_col(mff, ["超大单", "净"])
    col_large = find_col(mff, ["大单", "净"])
    col_medium = find_col(mff, ["中单", "净"])
    col_small = find_col(mff, ["小单", "净"])

    def latest_val_yi(col):
        if col and col in mff.columns:
            v = pd.to_numeric(mff[col], errors="coerce").dropna()
            return round(float(v.iloc[-1]) / 1e8, 2) if len(v) > 0 else 0.0
        return 0.0

    super_net = latest_val_yi(col_super)
    large_net = latest_val_yi(col_large)
    medium_net = latest_val_yi(col_medium)
    small_net = latest_val_yi(col_small)

    inst_direction = "流入" if (super_net + large_net) >= 0 else "流出"
    retail_direction = "流入" if small_net >= 0 else "流出"

    behavior_map = {
        ("流入", "流入"): "共识多头",
        ("流出", "流出"): "共识空头",
        ("流入", "流出"): "机构建仓、散户减仓",
        ("流出", "流入"): "机构减仓、散户接盘 ⚠️",
    }
    behavior_type = behavior_map.get((inst_direction, retail_direction), "混合")

    # 30日超大单净流入序列（供AI生成趋势图）
    trend_30d = []
    if col_super:
        v = pd.to_numeric(mff[col_super], errors="coerce").tail(30)
        trend_30d = [round(float(x) / 1e8, 2) for x in v.tolist()]

    return {
        "super_large_net_yi": super_net,
        "large_net_yi": large_net,
        "medium_net_yi": medium_net,
        "small_net_yi": small_net,
        "institutional_direction": inst_direction,
        "retail_direction": retail_direction,
        "behavior_type": behavior_type,
        "super_large_trend_30d_yi": trend_30d,
    }


# ── 7. 北向资金分析 ───────────────────────────────────────────

def calc_northbound(data: dict) -> dict:
    """
    北向资金：当日净额、20日净额序列、20日累计净额、趋势描述。
    """
    nb = data.get("northbound", {})
    if not nb:
        return {}

    frames = []
    for ch, records in nb.items():
        df = to_df(records)
        if not df.empty:
            net_col = next(
                (c for c in df.columns if "净买入" in c or "净额" in c), None)
            if net_col:
                df["channel"] = ch
                df["net"] = pd.to_numeric(df[net_col], errors="coerce")
                frames.append(df[["date", "channel", "net"]].dropna())

    if not frames:
        return {}

    combined = pd.concat(frames).sort_values("date")
    daily_net = combined.groupby("date")["net"].sum().reset_index()
    daily_net = daily_net.tail(22)  # 取最近22个交易日

    net_today = round(float(daily_net["net"].iloc[-1]) / 1e8, 2)
    net_20d = [round(float(x) / 1e8, 2)
               for x in daily_net["net"].tail(20).tolist()]
    cum_20d = round(sum(net_20d), 2)

    # 趋势描述
    if len(net_20d) >= 5:
        recent5 = net_20d[-5:]
        pos_days = sum(1 for x in recent5 if x > 0)
        if pos_days >= 4:
            trend_desc = "近5日持续净流入，外资积极布局"
        elif pos_days <= 1:
            trend_desc = "近5日持续净流出，外资撤离"
        else:
            trend_desc = "近5日净流向震荡，无明显方向"
    else:
        trend_desc = "数据不足"

    return {
        "net_today_yi": net_today,
        "net_20d_series_yi": net_20d,
        "cum_20d_yi": cum_20d,
        "trend_description": trend_desc,
    }


# ── 8. 情绪趋势历史百分位 ─────────────────────────────────────

def calc_sentiment_history_context(sentiment_today: dict, data: dict) -> dict:
    """
    基于历史成交额序列估算今日情绪分在近60日中的百分位，
    并增加【趋势与加速度】(Velocity/Acceleration) 维度判断。
    （注：完整历史情绪分需要历史数据库，此处用成交额及变动率近似）
    """
    # 增加资金加速度判断 (最近3日平均成交额 vs 前期3日平均成交额)
    # 如果 market_fund_flow 中没有成交额，则尝试用 上证指数 的成交量
    series = None
    mff = to_df(data.get("market_fund_flow", []))
    if not mff.empty:
        turn_col = next((c for c in mff.columns if "成交额" in c), None)
        if turn_col:
            series = pd.to_numeric(mff[turn_col], errors="coerce").dropna()

    if series is None or len(series) < 10:
        # Fallback 到上证指数的 volume
        sz_daily = to_df(data.get("index_daily", {}).get("上证指数", []))
        if not sz_daily.empty and "volume" in sz_daily.columns:
            series = pd.to_numeric(
                sz_daily["volume"], errors="coerce").dropna()

    if series is None or len(series) < 10:
        return {}

    latest_val = float(series.iloc[-1])
    pct = round(percentile_rank(series.iloc[:-1], latest_val) * 100, 1)

    momentum_desc = "数据不足"
    if len(series) >= 6:
        last_3_avg = series.iloc[-3:].mean()
        prev_3_avg = series.iloc[-6:-3].mean()
        dod_change = (last_3_avg - prev_3_avg) / \
            prev_3_avg * 100 if prev_3_avg > 0 else 0

        if dod_change > 10:
            momentum_desc = f"进场加速 (近3日均量环比增加 {dod_change:.1f}%)"
        elif dod_change < -10:
            momentum_desc = f"抛压衰减/情绪退潮 (近3日均量环比萎缩 {abs(dod_change):.1f}%)"
        elif dod_change > 0:
            momentum_desc = f"温和放量 (变化率 {dod_change:.1f}%)"
        else:
            momentum_desc = f"略微缩量 (变化率 {dod_change:.1f}%)"

    return {
        "turnover_percentile_60d": pct,
        "momentum_velocity": momentum_desc,
        "approximate_note": "以成交额历史百分位及3日环比变动近似代表情绪斜率",
    }


# ── 主流程 ────────────────────────────────────────────────────

def analyze(market_data_path: Path) -> dict:
    data = load_json(market_data_path)
    date_str = data.get("meta", {}).get("target_date", "unknown")
    print(f"[INFO] 分析目标日期: {date_str}", file=sys.stderr)

    print("[1/7] 情绪评分...", file=sys.stderr)
    sentiment = calc_sentiment(data)

    print("[2/7] 情绪历史百分位...", file=sys.stderr)
    sentiment_hist = calc_sentiment_history_context(sentiment, data)
    sentiment.update(sentiment_hist)

    print("[3/7] 技术状态矩阵 + 支撑/压力位...", file=sys.stderr)
    technical = calc_technical(data)

    print("[4/7] 估值水位 + ERP...", file=sys.stderr)
    valuation = calc_valuation(data)

    print("[5/7] 行业分析...", file=sys.stderr)
    industry = calc_industry(data)

    print("[6/7] 涨停板生态...", file=sys.stderr)
    limit_up_ecology = calc_limit_up_ecology(data)

    print("[7/7] 资金结构 + 北向资金...", file=sys.stderr)
    fund_structure = calc_fund_structure(data)
    northbound = calc_northbound(data)

    result = {
        "meta": {
            "target_date": date_str,
            "analyzed_at": datetime.now().isoformat(),
            "source_file": str(market_data_path),
        },
        "sentiment": sentiment,
        "technical": technical,
        "valuation": valuation,
        "industry": industry,
        "limit_up_ecology": limit_up_ecology,
        "fund_structure": fund_structure,
        "northbound": northbound,
    }

    print("[DONE] 分析完成", file=sys.stderr)
    return result


def main():
    parser = argparse.ArgumentParser(description="A股日报量化分析引擎")
    parser.add_argument(
        "--date", help="目标日期 YYYYMMDD，自动匹配 skill 目录下 assets/ 中的数据文件")
    parser.add_argument("--input", "-i", help="直接指定 market_data JSON 文件路径")
    parser.add_argument(
        "--output", "-o", help="输出文件路径（默认写入 skill 目录下 assets/analysis_YYYY-MM-DD.json）")
    args = parser.parse_args()

    # 确定输入文件
    if args.input:
        input_path = Path(args.input)
    elif args.date:
        d = args.date
        date_fmt = f"{d[:4]}-{d[4:6]}-{d[6:]}"
        input_path = ASSETS_DIR / f"market_data_{date_fmt}.json"
    else:
        # 自动寻找 skill 目录下 assets/ 中最新的 market_data 文件
        candidates = sorted(ASSETS_DIR.glob("market_data_*.json"))
        if not candidates:
            print(
                "错误: 未找到 skill 目录下 assets/market_data_*.json 文件，请先运行 fetch_market_data.py", file=sys.stderr)
            sys.exit(1)
        input_path = candidates[-1]
        print(f"[INFO] 自动选择最新数据文件: {input_path}", file=sys.stderr)

    if not input_path.exists():
        print(f"错误: 文件不存在: {input_path}", file=sys.stderr)
        sys.exit(1)

    # 确定输出文件
    if args.output:
        output_path = Path(args.output)
    else:
        # 从输入文件名中提取日期
        stem = input_path.stem  # e.g. market_data_2026-03-12
        date_part = stem.replace("market_data_", "")
        output_path = ASSETS_DIR / f"analysis_{date_part}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    result = analyze(input_path)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)

    print(f"[INFO] 分析结果已写入 {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
