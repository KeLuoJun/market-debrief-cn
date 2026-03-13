#!/usr/bin/env python3
"""
A股日报新闻采集脚本 - 基于 Tavily Search API（Python 跨平台版）
用法:
    python scripts/search_news.py                            # 默认今日
    python scripts/search_news.py --date 2026-03-12          # 指定日期
    python scripts/search_news.py --date 2026-03-12 --output out.json
"""

import argparse
import base64
import json
import os
import re
import sys
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print("错误: 需要安装 requests 库: pip install requests", file=sys.stderr)
    sys.exit(1)


SKILL_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = SKILL_ROOT / "assets"

TRUSTED_DOMAINS = {
    "stcn.com",
    "eastmoney.com",
    "finance.sina.com.cn",
    "cls.cn",
    "cnstock.com",
    "cs.com.cn",
    "yicai.com",
    "caixin.com",
    "wallstreetcn.com",
    "news.futunn.com",
    "21jingji.com",
}

NOISE_KEYWORDS = {
    "小时报",
    "财富号",
    "免责声明",
    "AI大模型",
    "扫码",
    "会员",
    "广告",
    "登录",
    "注册链接",
    "APP专享",
    "责任编辑",
}


# ── Token 管理 ────────────────────────────────────────────────


def _decode_jwt_payload(token: str) -> dict:
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    payload = parts[1]
    payload += "=" * (-len(payload) % 4)
    try:
        return json.loads(base64.b64decode(payload).decode("utf-8", errors="ignore"))
    except Exception:
        return {}


def _is_valid_tavily_jwt(token: str) -> bool:
    payload = _decode_jwt_payload(token)
    if payload.get("iss") != "https://mcp.tavily.com/":
        return False
    exp = payload.get("exp")
    if exp and int(time.time()) >= int(exp):
        return False
    return True


def _get_mcp_token() -> str:
    mcp_dir = Path.home() / ".mcp-auth"
    if not mcp_dir.exists():
        return ""
    for token_file in mcp_dir.rglob("*_tokens.json"):
        try:
            data = json.loads(token_file.read_text(encoding="utf-8"))
            token = data.get("access_token", "")
            if token and _is_valid_tavily_jwt(token):
                return token
        except Exception:
            continue
    return ""


def _get_api_key() -> tuple:
    """Returns (api_key, key_type) where key_type is 'rest' or 'mcp'."""
    key = os.environ.get("TAVILY_API_KEY", "")
    if key:
        if key.startswith("tvly-"):
            return key, "rest"
        return key, "mcp"
    token = _get_mcp_token()
    if token:
        return token, "mcp"
    return "", ""


# ── API 调用 ──────────────────────────────────────────────────


def _search_rest(api_key: str, query: str) -> dict:
    """tvly-... API key → Tavily REST API"""
    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "search_depth": "advanced",
                "max_results": 8,
                "time_range": "day",
                "topic": "general",
            },
            timeout=30,
            headers={"x-client-source": "market-debrief-cn"},
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[WARN] REST API 调用失败: {e}", file=sys.stderr)
        return {}


def _search_mcp(api_key: str, query: str) -> dict:
    """JWT OAuth token → Tavily MCP endpoint"""
    mcp_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "tavily_search",
            "arguments": {
                "query": query,
                "search_depth": "advanced",
                "max_results": 8,
                "time_range": "day",
                "topic": "general",
            },
        },
    }
    try:
        resp = requests.post(
            "https://mcp.tavily.com/mcp",
            json=mcp_request,
            timeout=30,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "x-client-source": "market-debrief-cn",
            },
        )
        resp.raise_for_status()
        # Handle SSE response (data: {...})
        for line in resp.text.splitlines():
            if line.startswith("data:"):
                data = json.loads(line[5:].strip())
                result = data.get("result", {})
                return result.get("structuredContent") or result
        return {}
    except Exception as e:
        print(f"[WARN] MCP API 调用失败: {e}", file=sys.stderr)
        return {}


def _domain_from_url(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower().strip()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return text[:800]


def _is_low_quality(title: str, content: str, domain: str) -> bool:
    blob = f"{title} {content}"
    if not title or not content:
        return True
    if len(content) < 80:
        return True
    if any(k.lower() in blob.lower() for k in NOISE_KEYWORDS):
        return True
    # 过滤明显无关或乱码域名
    if not domain or len(domain) < 4:
        return True
    return False


def _normalize_batch(query: str, batch: dict) -> list:
    items = batch.get("results", []) if isinstance(batch, dict) else []
    normalized = []
    for item in items:
        url = str(item.get("url", "")).strip()
        title = _clean_text(str(item.get("title", "")))
        content = _clean_text(str(item.get("content", "")))
        score = float(item.get("score", 0) or 0)
        domain = _domain_from_url(url)

        if _is_low_quality(title, content, domain):
            continue

        trust_bonus = 0.15 if domain in TRUSTED_DOMAINS else 0.0
        quality_score = round(min(score + trust_bonus, 1.0), 4)

        normalized.append({
            "query": query,
            "url": url,
            "domain": domain,
            "title": title,
            "content": content,
            "score": round(score, 4),
            "quality_score": quality_score,
            "trusted_source": domain in TRUSTED_DOMAINS,
        })
    return normalized


def _dedupe_and_rank(items: list, top_n: int = 40) -> list:
    dedup = {}
    for item in items:
        key = item.get("url") or f"{item.get('domain')}|{item.get('title')}"
        if key not in dedup or item.get("quality_score", 0) > dedup[key].get("quality_score", 0):
            dedup[key] = item

    ranked = sorted(
        dedup.values(),
        key=lambda x: (x.get("trusted_source", False),
                       x.get("quality_score", 0)),
        reverse=True,
    )
    return ranked[:top_n]


# ── 主程序 ────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="A股日报新闻采集")
    parser.add_argument(
        "--date",
        default=date.today().strftime("%Y-%m-%d"),
        help="目标日期 YYYY-MM-DD（默认今日）",
    )
    parser.add_argument("--output", default=None,
                        help="输出文件路径（默认写入 skill 目录下 assets/news_data_YYYY-MM-DD.json）")
    args = parser.parse_args()

    target_date = args.date
    output_file = str(args.output) if args.output else str(
        ASSETS_DIR / f"news_data_{target_date}.json")

    api_key, key_type = _get_api_key()
    if not api_key:
        print("错误: 未找到 Tavily API token", file=sys.stderr)
        print("请设置 TAVILY_API_KEY 环境变量，或通过 Tavily MCP 登录", file=sys.stderr)
        sys.exit(1)

    print(
        f"[INFO] 使用 {'REST API (tvly key)' if key_type == 'rest' else 'MCP (JWT)'} 模式", file=sys.stderr)

    queries = [
        f"A股 市场 {target_date} 重要新闻 政策",
        f"A股 板块 热点 {target_date} 涨停 主线",
        f"美股 港股 隔夜 大宗商品 {target_date}",
        f"中国 宏观经济 货币政策 MLF LPR CPI PMI {target_date}",
        # 新增深度分析类查询
        f"{target_date} A股 机构观点 研报 策略 分析",
        f"{target_date} 北向资金 动向 净流入 全天分析",
        f"{target_date} A股 突发 利好 利空 消息",
    ]

    query_batches = []
    curated_items = []
    failed_queries = 0

    for query in queries:
        print(f"[搜索] {query}", file=sys.stderr)
        result = _search_rest(
            api_key, query) if key_type == "rest" else _search_mcp(api_key, query)
        if result:
            query_batches.append({"query": query, "raw": result})
            curated_items.extend(_normalize_batch(query, result))
        else:
            failed_queries += 1
            print(f"[WARN] 查询无有效结果: {query}", file=sys.stderr)

    curated_results = _dedupe_and_rank(curated_items, top_n=40)
    trusted_count = sum(1 for x in curated_results if x.get("trusted_source"))

    output = {
        "target_date": target_date,
        "search_count": len(query_batches),
        "_failed_queries": failed_queries,
        "results": curated_results,
        "query_batches": query_batches,
        "quality_summary": {
            "curated_count": len(curated_results),
            "trusted_count": trusted_count,
            "trusted_ratio": round(trusted_count / len(curated_results), 4) if curated_results else 0.0,
        },
    }

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    Path(output_file).write_text(json.dumps(
        output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[完成] 已写入 {output_file}", file=sys.stderr)
    if failed_queries > 0:
        print(f"[WARN] {failed_queries}/{len(queries)} 个查询失败", file=sys.stderr)


if __name__ == "__main__":
    main()
