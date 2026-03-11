#!/usr/bin/env python3
"""
A股市场数据获取脚本 - 基于AkShare
获取市场总貌、指数K线、板块涨跌、资金流向、龙虎榜、两融等数据
输出JSON格式，供generate_report.py使用

用法：
  python scripts/fetch_market_data.py                    # 获取全部数据
  python scripts/fetch_market_data.py --action overview   # 仅市场总貌
  python scripts/fetch_market_data.py --action index --symbol 000001 --days 60
  python scripts/fetch_market_data.py --action industry --top 20
  python scripts/fetch_market_data.py --action concept --top 20
  python scripts/fetch_market_data.py --action northbound
  python scripts/fetch_market_data.py --action margin
  python scripts/fetch_market_data.py --action lhb --date 20250310
  python scripts/fetch_market_data.py --action flow --symbol 600519
  python scripts/fetch_market_data.py --action sector-flow  # 板块资金流向
  python scripts/fetch_market_data.py --output market_data.json  # 保存到文件
"""
import argparse
import json
import sys
from datetime import datetime, timedelta

try:
    import akshare as ak
    import pandas as pd
except ImportError:
    print(json.dumps(
        {"error": "请先安装依赖: pip install akshare pandas"}), file=sys.stderr)
    sys.exit(1)


def safe_float(val, default=0.0):
    """安全转换为float"""
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def df_to_records(df, max_rows=None):
    """DataFrame安全转换为records列表"""
    if df is None or df.empty:
        return []
    if max_rows:
        df = df.head(max_rows)
    # 处理NaN和Timestamp等不可序列化类型
    df = df.fillna(0)
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].astype(str)
    return df.to_dict(orient='records')


def get_market_overview():
    """获取市场总貌数据：成交额、涨跌停、换手率等"""
    df = ak.stock_zh_a_spot_em()

    total_stocks = len(df)
    total_amount = safe_float(df['成交额'].sum()) if '成交额' in df.columns else 0
    total_volume = safe_float(df['成交量'].sum()) if '成交量' in df.columns else 0
    avg_turnover = safe_float(df['换手率'].mean()) if '换手率' in df.columns else 0

    # 涨跌统计
    if '涨跌幅' in df.columns:
        up_count = len(df[df['涨跌幅'] > 0])
        down_count = len(df[df['涨跌幅'] < 0])
        flat_count = len(df[df['涨跌幅'] == 0])
        # 涨跌停需考虑ST和创业板/科创板不同涨跌幅限制
        up_limit = len(df[df['涨跌幅'] >= 9.9])
        down_limit = len(df[df['涨跌幅'] <= -9.9])
        avg_change = safe_float(df['涨跌幅'].mean())
        median_change = safe_float(df['涨跌幅'].median())
    else:
        up_count = down_count = flat_count = up_limit = down_limit = 0
        avg_change = median_change = 0

    return {
        "total_stocks": total_stocks,
        "total_amount": total_amount,
        "total_amount_yi": round(total_amount / 1e8, 2),
        "total_volume": total_volume,
        "avg_turnover": round(avg_turnover, 2),
        "up_count": up_count,
        "down_count": down_count,
        "flat_count": flat_count,
        "up_limit": up_limit,
        "down_limit": down_limit,
        "limit_ratio": f"{up_limit}:{down_limit}",
        "avg_change_pct": round(avg_change, 2),
        "median_change_pct": round(median_change, 2),
    }


def get_index_kline(symbol="000001", days=60):
    """获取指数K线数据（默认上证指数）"""
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days + 10)
                  ).strftime('%Y%m%d')

    df = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust="qfq"
    )
    records = df_to_records(df)

    # 计算均线（MA5/10/20/60/250）
    if len(records) > 0:
        closes = [safe_float(r.get('收盘', 0)) for r in records]
        for ma_n in [5, 10, 20, 60]:
            if len(closes) >= ma_n:
                ma_val = sum(closes[-ma_n:]) / ma_n
                records[-1][f'MA{ma_n}'] = round(ma_val, 2)
        # MA250需要更长数据，此处标记为需额外获取
        if len(closes) >= 250:
            records[-1]['MA250'] = round(sum(closes[-250:]) / 250, 2)

    return records


def get_multi_index_kline(days=60):
    """获取多个主要指数K线数据"""
    indices = {
        "000001": "上证指数",
        "399001": "深证成指",
        "399006": "创业板指",
        "000016": "上证50",
        "000905": "中证500",
        "000688": "科创50",
    }
    result = {}
    for symbol, name in indices.items():
        try:
            data = get_index_kline(symbol, days)
            result[symbol] = {"name": name, "data": data}
        except Exception as e:
            print(f"获取{name}({symbol})失败: {e}", file=sys.stderr)
            result[symbol] = {"name": name, "data": [], "error": str(e)}
    return result


def get_industry_boards(top_n=30):
    """获取行业板块涨跌榜"""
    df = ak.stock_board_industry_name_em()
    return df_to_records(df, top_n)


def get_concept_boards(top_n=30):
    """获取概念板块涨跌榜"""
    df = ak.stock_board_concept_name_em()
    return df_to_records(df, top_n)


def get_northbound_flow():
    """获取北向资金流向数据"""
    try:
        # 沪股通+深股通资金流向
        df = ak.stock_hsgt_north_net_flow_in_em(symbol="北向")
        if df is not None and not df.empty:
            records = df_to_records(df.tail(30))
            latest = records[-1] if records else {}
            return {
                "latest": latest,
                "recent_data": records,
                "data_count": len(records),
            }
    except Exception as e:
        print(f"获取北向资金数据失败: {e}", file=sys.stderr)

    # 备用方法
    try:
        df = ak.stock_hsgt_hist_em(symbol="沪股通")
        if df is not None and not df.empty:
            records = df_to_records(df.tail(20))
            return {"latest": records[-1] if records else {}, "recent_data": records}
    except Exception as e2:
        print(f"备用北向资金数据也失败: {e2}", file=sys.stderr)

    return {"latest": {}, "recent_data": [], "error": "数据获取失败"}


def get_margin_data():
    """获取融资融券数据"""
    try:
        df = ak.stock_margin_sse(start_date="20250101")
        if df is not None and not df.empty:
            records = df_to_records(df.tail(20))
            latest = records[-1] if records else {}
            prev = records[-2] if len(records) > 1 else {}

            # 计算日变化
            balance_today = safe_float(latest.get('融资余额', 0))
            balance_prev = safe_float(prev.get('融资余额', 0))
            margin_change = balance_today - balance_prev if balance_prev > 0 else 0

            return {
                "latest": latest,
                "recent_data": records,
                "margin_balance": balance_today,
                "margin_change": margin_change,
                "margin_change_yi": round(margin_change / 1e8, 2),
            }
    except Exception as e:
        print(f"获取融资融券数据失败: {e}", file=sys.stderr)

    return {"latest": {}, "recent_data": [], "margin_balance": 0, "margin_change": 0}


def get_lhb_data(date=None):
    """获取龙虎榜数据"""
    if date is None:
        # 尝试获取最近几天的数据（交易日不确定）
        for delta in range(0, 5):
            try_date = (datetime.now() - timedelta(days=delta)
                        ).strftime('%Y%m%d')
            try:
                df = ak.stock_lhb_detail_em(
                    start_date=try_date, end_date=try_date)
                if df is not None and not df.empty:
                    return {
                        "date": try_date,
                        "count": len(df),
                        "data": df_to_records(df),
                    }
            except Exception:
                continue
        return {"date": "", "count": 0, "data": []}
    else:
        try:
            df = ak.stock_lhb_detail_em(start_date=date, end_date=date)
            return {
                "date": date,
                "count": len(df) if df is not None else 0,
                "data": df_to_records(df),
            }
        except Exception as e:
            print(f"获取龙虎榜数据失败: {e}", file=sys.stderr)
            return {"date": date, "count": 0, "data": [], "error": str(e)}


def get_sector_fund_flow():
    """获取板块资金流向排行"""
    try:
        df = ak.stock_sector_fund_flow_rank(
            indicator="今日", sector_type="行业资金流")
        return df_to_records(df, 30)
    except Exception as e:
        print(f"获取板块资金流向失败: {e}", file=sys.stderr)
        return []


def get_stock_fund_flow(stock, market="sh"):
    """获取个股资金流向"""
    try:
        df = ak.stock_individual_fund_flow(stock=stock, market=market)
        return df_to_records(df, 20)
    except Exception as e:
        print(f"获取{stock}资金流向失败: {e}", file=sys.stderr)
        return []


def get_all_data(args):
    """获取全部市场数据"""
    result = {
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime('%Y-%m-%d'),
    }

    print("正在获取市场总貌...", file=sys.stderr)
    try:
        result["market_overview"] = get_market_overview()
    except Exception as e:
        print(f"市场总貌获取失败: {e}", file=sys.stderr)
        result["market_overview"] = {"error": str(e)}

    print("正在获取指数K线...", file=sys.stderr)
    try:
        result["index_kline"] = get_multi_index_kline(args.days)
    except Exception as e:
        print(f"指数K线获取失败: {e}", file=sys.stderr)
        result["index_kline"] = {"error": str(e)}

    print("正在获取行业板块...", file=sys.stderr)
    try:
        result["industry_boards"] = get_industry_boards(args.top)
    except Exception as e:
        print(f"行业板块获取失败: {e}", file=sys.stderr)
        result["industry_boards"] = []

    print("正在获取概念板块...", file=sys.stderr)
    try:
        result["concept_boards"] = get_concept_boards(args.top)
    except Exception as e:
        print(f"概念板块获取失败: {e}", file=sys.stderr)
        result["concept_boards"] = []

    print("正在获取北向资金...", file=sys.stderr)
    try:
        result["northbound_flow"] = get_northbound_flow()
    except Exception as e:
        print(f"北向资金获取失败: {e}", file=sys.stderr)
        result["northbound_flow"] = {"error": str(e)}

    print("正在获取融资融券...", file=sys.stderr)
    try:
        result["margin_data"] = get_margin_data()
    except Exception as e:
        print(f"融资融券获取失败: {e}", file=sys.stderr)
        result["margin_data"] = {"error": str(e)}

    print("正在获取龙虎榜...", file=sys.stderr)
    try:
        result["lhb_data"] = get_lhb_data(args.date)
    except Exception as e:
        print(f"龙虎榜获取失败: {e}", file=sys.stderr)
        result["lhb_data"] = {"error": str(e)}

    print("正在获取板块资金流向...", file=sys.stderr)
    try:
        result["sector_fund_flow"] = get_sector_fund_flow()
    except Exception as e:
        print(f"板块资金流向获取失败: {e}", file=sys.stderr)
        result["sector_fund_flow"] = []

    return result


def main():
    parser = argparse.ArgumentParser(description='A股市场数据获取工具')
    parser.add_argument('--action', default='all',
                        choices=['all', 'overview', 'index', 'multi-index',
                                 'industry', 'concept', 'northbound', 'margin',
                                 'lhb', 'flow', 'sector-flow'],
                        help='数据获取类型')
    parser.add_argument('--symbol', default='000001', help='股票/指数代码')
    parser.add_argument('--market', default='sh', help='市场(sh/sz)')
    parser.add_argument('--date', help='日期(YYYYMMDD)')
    parser.add_argument('--days', type=int, default=60, help='获取天数')
    parser.add_argument('--top', type=int, default=30, help='返回条数')
    parser.add_argument('--output', '-o', help='输出到JSON文件（默认stdout）')

    args = parser.parse_args()

    try:
        if args.action == 'all':
            result = get_all_data(args)
        elif args.action == 'overview':
            result = get_market_overview()
        elif args.action == 'index':
            result = get_index_kline(args.symbol, args.days)
        elif args.action == 'multi-index':
            result = get_multi_index_kline(args.days)
        elif args.action == 'industry':
            result = get_industry_boards(args.top)
        elif args.action == 'concept':
            result = get_concept_boards(args.top)
        elif args.action == 'northbound':
            result = get_northbound_flow()
        elif args.action == 'margin':
            result = get_margin_data()
        elif args.action == 'lhb':
            result = get_lhb_data(args.date)
        elif args.action == 'flow':
            result = get_stock_fund_flow(args.symbol, args.market)
        elif args.action == 'sector-flow':
            result = get_sector_fund_flow()
        else:
            result = {"error": f"未知action: {args.action}"}

        output = json.dumps(result, ensure_ascii=False, indent=2)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"数据已保存到: {args.output}", file=sys.stderr)
        else:
            print(output)

    except Exception as e:
        print(json.dumps({"error": str(e)},
              ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
