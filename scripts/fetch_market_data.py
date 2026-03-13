#!/usr/bin/env python3
"""
A股日报数据采集脚本 - 基于 AkShare
一次性拉取所有分析模块所需的市场数据，输出结构化 JSON。

用法：
  python scripts/fetch_market_data.py                    # 默认最近交易日
  python scripts/fetch_market_data.py --date 20260311    # 指定日期
  python scripts/fetch_market_data.py --output data.json # 写入文件
"""

import argparse
import json
import sys
import warnings
from datetime import datetime, timedelta
from pathlib import Path

warnings.filterwarnings("ignore")

SKILL_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = SKILL_ROOT / "assets"

try:
    import akshare as ak
    import pandas as pd
except ImportError:
    print("请先安装依赖: pip install akshare pandas", file=sys.stderr)
    sys.exit(1)


# ── 失败项追踪 ────────────────────────────────────────────────
_failed_items: list = []

# ── 指数代码映射 ─────────────────────────────────────────────
INDEX_MAP = {
    "上证指数": "sh000001",
    "深证成指": "sz399001",
    "创业板指": "sz399006",
    "科创50":  "sh000688",
    "沪深300": "sh000300",
    "中证500": "sh000905",
}

# PE 查询用名（stock_index_pe_lg 接口支持的中文名）
PE_SYMBOLS = {
    "沪深300": "沪深300",
    "中证500": "中证500",
    "中证1000": "中证1000",
    "上证50": "上证50",
}


def safe_call(func, *args, **kwargs):
    """安全调用 akshare 接口，失败返回 None，并记录失败项"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        label = func.__name__.replace("fetch_", "").replace("_", " ")
        _failed_items.append(label)
        print(f"[WARN] {func.__name__} 调用失败: {e}", file=sys.stderr)
        return None


def df_to_records(df, n=None):
    """DataFrame → list[dict]，可选截取前 n 行"""
    if df is None or df.empty:
        return []
    if n:
        df = df.head(n)
    return json.loads(df.to_json(orient="records", force_ascii=False, date_format="iso"))


def get_latest_trade_date(target_date=None):
    """确定目标交易日（默认取最近收盘日）"""
    if target_date:
        return target_date
    # 用上证指数最近数据判断
    df = safe_call(ak.stock_zh_index_daily_em, symbol="sh000001",
                   start_date=(datetime.now() - timedelta(days=10)
                               ).strftime("%Y%m%d"),
                   end_date=datetime.now().strftime("%Y%m%d"))
    if df is not None and len(df) > 0:
        return pd.to_datetime(df["date"].iloc[-1]).strftime("%Y%m%d")
    return datetime.now().strftime("%Y%m%d")


# ── 数据采集函数 ─────────────────────────────────────────────

def fetch_index_daily(date_str, lookback_days=365):
    """主要指数近一年日线数据（OHLCV），用于 MA、K线、量价分析"""
    start = (datetime.strptime(date_str, "%Y%m%d") -
             timedelta(days=lookback_days)).strftime("%Y%m%d")
    result = {}
    for name, code in INDEX_MAP.items():
        df = safe_call(ak.stock_zh_index_daily_em, symbol=code,
                       start_date=start, end_date=date_str)
        if df is not None and len(df) > 0:
            result[name] = df_to_records(df)
    return result


def fetch_index_pe():
    """主要指数 PE(TTM) 历史序列"""
    result = {}
    for label, symbol in PE_SYMBOLS.items():
        df = safe_call(ak.stock_index_pe_lg, symbol=symbol)
        if df is not None and len(df) > 0:
            latest = df.iloc[-1].to_dict()
            # 计算历史百分位
            pe_col = "滚动市盈率"
            if pe_col in df.columns:
                current_pe = df[pe_col].iloc[-1]
                percentile = (df[pe_col] < current_pe).mean()
                latest["历史百分位"] = round(percentile, 4)
            result[label] = {
                "latest": {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in latest.items()},
                "recent_60": df_to_records(df.tail(60)),
            }
    return result


def fetch_all_a_pb():
    """全A股 PB 中位数及历史百分位"""
    df = safe_call(ak.stock_a_all_pb)
    if df is None:
        return None
    latest = df.iloc[-1].to_dict()
    return {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in latest.items()}


def fetch_market_fund_flow():
    """全市场资金流向（超大单/大单/中单/小单）"""
    df = safe_call(ak.stock_market_fund_flow)
    if df is None:
        return []
    return df_to_records(df.tail(30))


def fetch_sector_fund_flow():
    """行业资金流向排名 & 涨跌幅数据 (替代 unreliable stock_board_industry_name_em)"""
    # 获取全部行业板块资金流向，包含涨跌幅
    df = safe_call(ak.stock_sector_fund_flow_rank,
                   indicator="今日", sector_type="行业资金流")
    if df is None:
        return []
    # 确保只要有数据就全部返回，不做截断，以便后续计算行业强弱分布
    return df_to_records(df)


def fetch_market_breadth():
    """市场广度摘要（上涨/下跌家数、涨跌分布、极值）"""
    df = safe_call(ak.stock_zh_a_spot_em)
    if df is None or df.empty:
        return {}

    # 常见字段：涨跌幅、代码、名称、最新价、成交额
    chg_col = next((c for c in df.columns if "涨跌幅" in c), None)
    code_col = next((c for c in df.columns if "代码" in c), None)
    name_col = next((c for c in df.columns if "名称" in c), None)
    amount_col = next((c for c in df.columns if "成交额" in c), None)

    if not chg_col:
        return {}

    tmp = df.copy()
    tmp[chg_col] = pd.to_numeric(tmp[chg_col], errors="coerce")
    tmp = tmp.dropna(subset=[chg_col])
    if tmp.empty:
        return {}

    up_count = int((tmp[chg_col] > 0).sum())
    down_count = int((tmp[chg_col] < 0).sum())
    flat_count = int((tmp[chg_col] == 0).sum())
    total = up_count + down_count + flat_count

    summary = {
        "total_count": total,
        "up_count": up_count,
        "down_count": down_count,
        "flat_count": flat_count,
        "up_ratio": round(up_count / total, 4) if total else None,
        "down_ratio": round(down_count / total, 4) if total else None,
        "median_chg_pct": round(float(tmp[chg_col].median()), 2),
        "mean_chg_pct": round(float(tmp[chg_col].mean()), 2),
        "count_gt_3pct": int((tmp[chg_col] >= 3).sum()),
        "count_lt_minus3pct": int((tmp[chg_col] <= -3).sum()),
    }

    if code_col and name_col:
        top_up = tmp.nlargest(10, chg_col)
        top_down = tmp.nsmallest(10, chg_col)

        def _to_row(row):
            out = {
                "code": str(row.get(code_col, "")),
                "name": str(row.get(name_col, "")),
                "chg_pct": round(float(row.get(chg_col, 0.0)), 2),
            }
            if amount_col:
                amt_val = pd.to_numeric(row.get(amount_col), errors="coerce")
                if pd.notna(amt_val):
                    out["amount_yi"] = round(float(amt_val) / 1e8, 2)
            return out

        summary["top_up"] = [_to_row(r) for _, r in top_up.iterrows()]
        summary["top_down"] = [_to_row(r) for _, r in top_down.iterrows()]

    return summary


def fetch_lhb_institution(date_str):
    """龙虎榜机构席位统计 (替代 unreliable stock_lhb_detail_em)"""
    # 机构买卖每日统计
    df = safe_call(ak.stock_lhb_jgmmtj_em,
                   start_date=date_str, end_date=date_str)
    if df is None:
        return []
    return df_to_records(df)


def fetch_limit_up(date_str):
    """涨停池"""
    df = safe_call(ak.stock_zt_pool_em, date=date_str)
    if df is None:
        return {"count": 0, "stocks": []}
    return {
        "count": len(df),
        "stocks": df_to_records(df),
    }


def fetch_limit_down(date_str):
    """跌停池"""
    df = safe_call(ak.stock_zt_pool_dtgc_em, date=date_str)
    if df is None:
        return {"count": 0, "stocks": []}
    return {
        "count": len(df),
        "stocks": df_to_records(df),
    }


def fetch_broken_limit(date_str):
    """炸板池"""
    df = safe_call(ak.stock_zt_pool_zbgc_em, date=date_str)
    if df is None:
        return {"count": 0, "stocks": []}
    return {
        "count": len(df),
        "stocks": df_to_records(df),
    }


def fetch_northbound():
    """北向资金历史数据（沪股通+深股通汇总）"""
    result = {}
    for channel in ["沪股通", "深股通"]:
        df = safe_call(ak.stock_hsgt_hist_em, symbol=channel)
        if df is not None and len(df) > 0:
            result[channel] = df_to_records(df.tail(30))
    return result


def fetch_margin_account():
    """两融余额"""
    df = safe_call(ak.stock_margin_account_info)
    if df is None:
        return []
    return df_to_records(df.tail(30))


def fetch_bond_yield(date_str):
    """国债收益率"""
    start = (datetime.strptime(date_str, "%Y%m%d") -
             timedelta(days=30)).strftime("%Y%m%d")
    df = safe_call(ak.bond_china_yield, start_date=start, end_date=date_str)
    if df is None:
        return []
    # 只取中债国债收益率曲线
    df_gov = df[df["曲线名称"] == "中债国债收益率曲线"]
    return df_to_records(df_gov)


def fetch_lhb_top_stocks(date_str):
    """龙虎榜个股上榜统计 (补充)"""
    # 不同版本 akshare 参数签名存在差异：优先尝试按日期，其次尝试无参。
    try:
        df = ak.stock_lhb_stock_statistic_em(date=date_str)
    except TypeError:
        try:
            df = ak.stock_lhb_stock_statistic_em()
        except Exception as e:
            _failed_items.append("stock lhb stock statistic em")
            print(
                f"[WARN] stock_lhb_stock_statistic_em 调用失败: {e}", file=sys.stderr)
            return []
    except Exception as e:
        _failed_items.append("stock lhb stock statistic em")
        print(
            f"[WARN] stock_lhb_stock_statistic_em 调用失败: {e}", file=sys.stderr)
        return []

    if df is None:
        return []
    # 按净买入额排序取前20
    if "净买入额" in df.columns:
        df = df.sort_values("净买入额", ascending=False).head(20)
    return df_to_records(df)


def fetch_strong_limit_up(date_str):
    """强势连板股"""
    df = safe_call(ak.stock_zt_pool_strong_em, date=date_str)
    if df is None:
        return []
    return df_to_records(df)


# ── 主流程 ───────────────────────────────────────────────────

def collect_all(date_str):
    """采集全部数据，返回结构化字典"""
    print(f"[INFO] 目标交易日: {date_str}", file=sys.stderr)

    data = {
        "meta": {
            "target_date": date_str,
            "collected_at": datetime.now().isoformat(),
        },
    }

    print("[1/11] 拉取主要指数日线...", file=sys.stderr)
    data["index_daily"] = fetch_index_daily(date_str)

    print("[2/11] 拉取指数PE估值...", file=sys.stderr)
    data["index_pe"] = fetch_index_pe()

    print("[3/11] 拉取全A PB...", file=sys.stderr)
    data["all_a_pb"] = fetch_all_a_pb()

    print("[4/11] 拉取全市场资金流向...", file=sys.stderr)
    data["market_fund_flow"] = fetch_market_fund_flow()

    print("[5/11] 拉取行业资金流向(含涨跌幅)...", file=sys.stderr)
    data["sector_fund_flow"] = fetch_sector_fund_flow()

    print("[6/11] 拉取市场广度摘要...", file=sys.stderr)
    data["market_breadth"] = fetch_market_breadth()

    # 移除 data["industry_board"]，改用 sector_fund_flow 替代其功能

    print("[7/11] 拉取涨跌停数据...", file=sys.stderr)
    data["limit_up"] = fetch_limit_up(date_str)
    data["limit_down"] = fetch_limit_down(date_str)
    data["broken_limit"] = fetch_broken_limit(date_str)
    data["strong_limit_up"] = fetch_strong_limit_up(date_str)

    print("[8/11] 拉取北向资金...", file=sys.stderr)
    data["northbound"] = fetch_northbound()

    print("[9/11] 拉取两融余额...", file=sys.stderr)
    data["margin"] = fetch_margin_account()

    print("[10/11] 拉取国债收益率...", file=sys.stderr)
    data["bond_yield"] = fetch_bond_yield(date_str)

    print("[11/11] 拉取龙虎榜(机构/个股)...", file=sys.stderr)
    data["lhb_jgmmtj"] = fetch_lhb_institution(date_str)
    data["lhb_stocks"] = fetch_lhb_top_stocks(date_str)

    data["_failed_items"] = _failed_items.copy()
    if _failed_items:
        print(f"[WARN] 采集失败项: {', '.join(_failed_items)}", file=sys.stderr)
    print("[DONE] 数据采集完成", file=sys.stderr)
    return data


def main():
    parser = argparse.ArgumentParser(description="A股日报数据采集")
    parser.add_argument("--date", help="目标日期 YYYYMMDD（默认最近交易日）")
    parser.add_argument("--output", "-o",
                        help="输出文件路径（默认写入 skill 目录下 assets/market_data_YYYY-MM-DD.json）")
    args = parser.parse_args()

    date_str = get_latest_trade_date(args.date)
    data = collect_all(date_str)

    # 默认写入 skill 目录下 assets/，文件名包含日期
    if args.output:
        output_path = Path(args.output)
    else:
        date_fmt = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        output_path = ASSETS_DIR / f"market_data_{date_fmt}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    json_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(json_str)
    print(f"[INFO] 已写入 {output_path}", file=sys.stderr)

    if _failed_items:
        print(f"[WARN] 以下数据项获取失败，将在报告中标注: {', '.join(_failed_items)}",
              file=sys.stderr)


if __name__ == "__main__":
    main()
