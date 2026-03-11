#!/usr/bin/env python3
"""
A股资讯获取脚本 (Tavily 增强版)
基于 Tavily Search/Research 能力并行采集多维度宏观资讯。

用法：
  python scripts/fetch_news.py --output news_data.json
  python scripts/fetch_news.py --query "半导体产业最新政策"

依赖：
  pip install requests python-dotenv aiohttp
"""
import argparse
import json
import os
import sys
import asyncio
from datetime import datetime

# 从.env加载环境变量
try:
    from dotenv import load_dotenv
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

async def tavily_search_async(session, query, max_results=5, search_depth="advanced", time_range="day"):
    """异步调用Tavily搜索API"""
    api_key = get_tavily_key()
    if not api_key:
        return {"results": [], "error": "API Key missing"}

    url = "https://api.tavily.com/search"
    payload = {
        "query": query,
        "max_results": max_results,
        "search_depth": search_depth,
        "include_answer": True,
        "include_raw_content": False,
        "time_range": time_range
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with session.post(url, json=payload, headers=headers, timeout=30) as resp:
            if resp.status != 200:
                text = await resp.text()
                return {"results": [], "query": query, "error": f"HTTP {resp.status}: {text}"}
            return await resp.json()
    except Exception as e:
        return {"results": [], "query": query, "error": str(e)}

async def get_all_news_async(max_results=5):
    """并行获取全方位新闻"""
    import aiohttp
    
    categories = {
        "macro": [
            "今日 A股 宏观经济 重要政策 央行动态",
            "中国经济指标 最新发布 GDP CPI PMI 影响分析"
        ],
        "policy": [
            "中国股市 监管新规 证监会 声明 公告",
            "A股 产业扶持政策 利好板块 工信部 财政部"
        ],
        "international": [
            "美股收盘 隔夜行情 纳斯达克 标普500",
            "美联储 降息预期 鲍威尔 表态 对全球市场影响",
            "地缘政治 最新动态 原油 黄金 趋势"
        ]
    }

    async with aiohttp.ClientSession() as session:
        result = {
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime('%Y-%m-%d'),
            "news": {}
        }

        tasks = []
        for cat, queries in categories.items():
            for q in queries:
                tasks.append((cat, q, tavily_search_async(session, q, max_results=3)))

        # 并行执行
        done_tasks = await asyncio.gather(*(t for c, q, t in tasks))
        
        # 结果归类与去重
        for (cat, q, _), res in zip(tasks, done_tasks):
            if cat not in result["news"]:
                result["news"][cat] = {"results": [], "answers": []}
            
            if res.get("answer"):
                result["news"][cat]["answers"].append(res["answer"])
            
            for item in res.get("results", []):
                # 简单去重逻辑
                if not any(it["url"] == item["url"] for it in result["news"][cat]["results"]):
                    result["news"][cat]["results"].append({
                        "title": item.get("title"),
                        "content": item.get("content"),
                        "url": item.get("url"),
                        "score": item.get("score")
                    })
        
        # 排序
        for cat in result["news"]:
            result["news"][cat]["results"].sort(key=lambda x: x.get("score", 0), reverse=True)
            result["news"][cat]["results"] = result["news"][cat]["results"][:15]

        return result

async def main_async():
    parser = argparse.ArgumentParser(description='A股深度资讯采集 (Tavily 增强版)')
    parser.add_argument('--query', help='执行专项自定义搜索')
    parser.add_argument('--output', '-o', help='输出到JSON文件')
    parser.add_argument('--max-results', type=int, default=5, help='最大分项结果数')

    args = parser.parse_args()

    try:
        if args.query:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                print(f"执行专项搜索: {args.query}...", file=sys.stderr)
                result = await tavily_search_async(session, args.query, max_results=args.max_results)
        else:
            print("正在并行采集多维度宏观资讯...", file=sys.stderr)
            result = await get_all_news_async(max_results=args.max_results)

        output = json.dumps(result, ensure_ascii=False, indent=2)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"成功保存资讯数据到: {args.output}", file=sys.stderr)
        else:
            print(output)

    except ImportError:
        print("错误: 请安装 aiohttp 以支持并行采集: pip install aiohttp", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"运行失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main_async())
