#!/usr/bin/env python3
"""
宏观新闻获取脚本 - 基于Tavily API
获取当日A股相关宏观新闻、政策消息、国际市场动态

用法：
  python scripts/fetch_news.py                          # 获取全部新闻
  python scripts/fetch_news.py --action macro           # 宏观新闻
  python scripts/fetch_news.py --action policy          # 政策新闻
  python scripts/fetch_news.py --action international   # 国际新闻
  python scripts/fetch_news.py --query "半导体 政策"     # 自定义搜索
  python scripts/fetch_news.py --output news.json       # 保存到文件

环境变量：
  TAVILY_API_KEY - Tavily API密钥（从 .env 文件或环境变量读取）
"""
import argparse
import json
import os
import sys
from datetime import datetime

# 从.env加载环境变量
try:
    from dotenv import load_dotenv
    # 尝试多个位置的.env文件
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    for env_path in [
        os.path.join(project_root, '.env'),
        os.path.join(os.getcwd(), '.env'),
    ]:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            break
except ImportError:
    pass


def get_tavily_key():
    """获取Tavily API Key"""
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        print("警告: TAVILY_API_KEY未设置。请设置环境变量或在项目根目录创建.env文件", file=sys.stderr)
        return None
    return key


def tavily_search(query, max_results=5, search_depth="advanced", time_range="day"):
    """调用Tavily搜索API"""
    api_key = get_tavily_key()
    if not api_key:
        return {"results": [], "error": "TAVILY_API_KEY未设置"}

    try:
        import requests
    except ImportError:
        return {"results": [], "error": "请安装requests: pip install requests"}

    url = "https://api.tavily.com/search"
    payload = {
        "query": query,
        "max_results": max_results,
        "search_depth": search_depth,
        "include_answer": True,
        "include_raw_content": False,
    }
    # time_range仅在需要时添加
    if time_range:
        payload["time_range"] = time_range

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data
    except requests.exceptions.Timeout:
        return {"results": [], "error": "请求超时"}
    except requests.exceptions.HTTPError as e:
        return {"results": [], "error": f"HTTP错误: {e}"}
    except Exception as e:
        return {"results": [], "error": str(e)}


def search_news(query, max_results=5):
    """搜索新闻，返回结构化结果"""
    raw = tavily_search(query, max_results=max_results, time_range="day")

    results = []
    for item in raw.get("results", []):
        results.append({
            "title": item.get("title", ""),
            "content": item.get("content", ""),
            "url": item.get("url", ""),
            "score": item.get("score", 0),
        })

    return {
        "query": query,
        "answer": raw.get("answer", ""),
        "results": results,
        "error": raw.get("error"),
    }


def get_macro_news():
    """获取当日宏观经济新闻"""
    queries = [
        "今日A股 宏观政策 央行 国务院 证监会",
        "美联储 利率 鲍威尔 对A股影响",
        "大宗商品 原油 黄金 铜 今日价格变动",
        "北向资金 外资 今日流向 A股",
        "中国经济数据 GDP CPI PMI 最新发布",
    ]
    all_results = []
    for q in queries:
        data = search_news(q, max_results=3)
        all_results.extend(data.get("results", []))

    # 去重（按title）
    seen_titles = set()
    unique = []
    for r in all_results:
        t = r.get("title", "")
        if t and t not in seen_titles:
            seen_titles.add(t)
            unique.append(r)

    # 按相关性排序
    unique.sort(key=lambda x: x.get("score", 0), reverse=True)

    return {
        "date": datetime.now().strftime('%Y-%m-%d'),
        "category": "macro",
        "news_count": len(unique),
        "news": unique[:15],
    }


def get_policy_news():
    """获取政策相关新闻"""
    queries = [
        "中国 株市政策 证监会新规 最新",
        "A股 IPO 注册制 退市 监管政策",
        "国务院 财政部 工信部 产业政策 利好板块",
    ]
    all_results = []
    for q in queries:
        data = search_news(q, max_results=3)
        all_results.extend(data.get("results", []))

    seen_titles = set()
    unique = []
    for r in all_results:
        t = r.get("title", "")
        if t and t not in seen_titles:
            seen_titles.add(t)
            unique.append(r)

    unique.sort(key=lambda x: x.get("score", 0), reverse=True)

    return {
        "date": datetime.now().strftime('%Y-%m-%d'),
        "category": "policy",
        "news_count": len(unique),
        "news": unique[:10],
    }


def get_international_news():
    """获取国际市场新闻"""
    queries = [
        "美国股市 纳斯达克 标普500 隔夜收盘",
        "中美关系 贸易 关税 制裁 最新",
        "全球股市 欧洲 日本 亚太 今日行情",
        "地缘政治 冲突 制裁 对全球市场影响",
    ]
    all_results = []
    for q in queries:
        data = search_news(q, max_results=3)
        all_results.extend(data.get("results", []))

    seen_titles = set()
    unique = []
    for r in all_results:
        t = r.get("title", "")
        if t and t not in seen_titles:
            seen_titles.add(t)
            unique.append(r)

    unique.sort(key=lambda x: x.get("score", 0), reverse=True)

    return {
        "date": datetime.now().strftime('%Y-%m-%d'),
        "category": "international",
        "news_count": len(unique),
        "news": unique[:10],
    }


def get_all_news():
    """获取全部新闻"""
    result = {
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime('%Y-%m-%d'),
    }

    print("正在获取宏观新闻...", file=sys.stderr)
    result["macro_news"] = get_macro_news()

    print("正在获取政策新闻...", file=sys.stderr)
    result["policy_news"] = get_policy_news()

    print("正在获取国际新闻...", file=sys.stderr)
    result["international_news"] = get_international_news()

    total = (result["macro_news"]["news_count"]
             + result["policy_news"]["news_count"]
             + result["international_news"]["news_count"])
    print(f"共获取 {total} 条新闻", file=sys.stderr)

    return result


def main():
    parser = argparse.ArgumentParser(description='宏观新闻获取工具')
    parser.add_argument('--action', default='all',
                        choices=['all', 'macro', 'policy',
                                 'international', 'search'],
                        help='新闻类型')
    parser.add_argument('--query', help='自定义搜索关键词（仅search模式）')
    parser.add_argument('--max-results', type=int, default=10, help='最大结果数')
    parser.add_argument('--output', '-o', help='输出到JSON文件（默认stdout）')

    args = parser.parse_args()

    try:
        if args.action == 'all':
            result = get_all_news()
        elif args.action == 'macro':
            result = get_macro_news()
        elif args.action == 'policy':
            result = get_policy_news()
        elif args.action == 'international':
            result = get_international_news()
        elif args.action == 'search':
            if not args.query:
                print("search模式需要 --query 参数", file=sys.stderr)
                sys.exit(1)
            result = search_news(args.query, args.max_results)
        else:
            result = {"error": f"未知action: {args.action}"}

        output = json.dumps(result, ensure_ascii=False, indent=2)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"新闻数据已保存到: {args.output}", file=sys.stderr)
        else:
            print(output)

    except Exception as e:
        print(json.dumps({"error": str(e)},
              ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
