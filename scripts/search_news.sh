#!/bin/bash
# A股日报新闻采集脚本 - 基于 Tavily Search API
# 用法:
#   ./scripts/search_news.sh                             # 默认搜索今日A股新闻
#   ./scripts/search_news.sh '{"date": "2026-03-11"}'    # 指定日期
#   ./scripts/search_news.sh '{"date": "2026-03-11"}' output.json  # 写入文件

set -e

# ── Token 管理 ─────────────────────────────────────────────

decode_jwt_payload() {
    local token="$1"
    local payload=$(echo "$token" | cut -d'.' -f2)
    local padded_payload="$payload"
    case $((${#payload} % 4)) in
        2) padded_payload="${payload}==" ;;
        3) padded_payload="${payload}=" ;;
    esac
    echo "$padded_payload" | base64 -d 2>/dev/null
}

is_valid_tavily_token() {
    local token="$1"
    local payload=$(decode_jwt_payload "$token")
    local iss=$(echo "$payload" | jq -r '.iss // empty' 2>/dev/null)
    if [ "$iss" != "https://mcp.tavily.com/" ]; then
        return 1
    fi
    local exp=$(echo "$payload" | jq -r '.exp // empty' 2>/dev/null)
    if [ -n "$exp" ] && [ "$exp" != "null" ]; then
        local current_time=$(date +%s)
        if [ "$current_time" -ge "$exp" ]; then
            return 1
        fi
    fi
    return 0
}

get_mcp_token() {
    MCP_AUTH_DIR="$HOME/.mcp-auth"
    if [ -d "$MCP_AUTH_DIR" ]; then
        while IFS= read -r token_file; do
            if [ -f "$token_file" ]; then
                token=$(jq -r '.access_token // empty' "$token_file" 2>/dev/null)
                if [ -n "$token" ] && [ "$token" != "null" ]; then
                    if is_valid_tavily_token "$token"; then
                        echo "$token"
                        return 0
                    fi
                fi
            fi
        done < <(find "$MCP_AUTH_DIR" -name "*_tokens.json" 2>/dev/null)
    fi
    return 1
}

# 尝试从 MCP 缓存获取 token
if [ -z "$TAVILY_API_KEY" ]; then
    token=$(get_mcp_token) || true
    if [ -n "$token" ]; then
        export TAVILY_API_KEY="$token"
    fi
fi

# 若仍无 token，尝试 OAuth 流程
if [ -z "$TAVILY_API_KEY" ]; then
    set +e
    echo "未找到 Tavily token，启动 OAuth 认证..." >&2
    npx -y mcp-remote https://mcp.tavily.com/mcp </dev/null >/dev/null 2>&1 &
    MCP_PID=$!
    TIMEOUT=120
    ELAPSED=0
    while [ $ELAPSED -lt $TIMEOUT ]; do
        sleep 3
        ELAPSED=$((ELAPSED + 3))
        token=$(get_mcp_token) || true
        if [ -n "$token" ]; then
            export TAVILY_API_KEY="$token"
            echo "认证成功!" >&2
            break
        fi
    done
    kill $MCP_PID 2>/dev/null || true
    wait $MCP_PID 2>/dev/null || true
    set -e
fi

if [ -z "$TAVILY_API_KEY" ]; then
    echo "错误: 未能获取 Tavily API token" >&2
    echo "请先在 https://tavily.com 注册，或手动设置 TAVILY_API_KEY 环境变量" >&2
    exit 1
fi

# ── 参数解析 ─────────────────────────────────────────────

JSON_INPUT="${1:-{}}"
OUTPUT_FILE="$2"

# 解析日期
TARGET_DATE=$(echo "$JSON_INPUT" | jq -r '.date // empty' 2>/dev/null)
if [ -z "$TARGET_DATE" ]; then
    TARGET_DATE=$(date +%Y-%m-%d)
fi

# 默认写入 assets/ 目录，文件名包含日期
if [ -z "$OUTPUT_FILE" ]; then
    OUTPUT_FILE="assets/news_data_${TARGET_DATE}.json"
fi
mkdir -p "$(dirname "$OUTPUT_FILE")"

# ── 搜索查询列表 ─────────────────────────────────────────

# 并行执行多个搜索查询以覆盖所有分析模块需要的新闻
QUERIES=(
    "A股 市场 ${TARGET_DATE} 重要新闻 政策"
    "A股 板块 热点 ${TARGET_DATE} 涨停 主线"
    "美股 港股 隔夜 大宗商品 ${TARGET_DATE}"
    "中国 宏观经济 货币政策 MLF LPR CPI PMI ${TARGET_DATE}"
)

ALL_RESULTS="[]"
FAILED_QUERIES=0

for query in "${QUERIES[@]}"; do
    echo "[搜索] $query" >&2

    MCP_REQUEST=$(jq -n \
        --arg q "$query" \
        '{
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "tavily_search",
                "arguments": {
                    "query": $q,
                    "search_depth": "advanced",
                    "max_results": 8,
                    "time_range": "day",
                    "topic": "general"
                }
            }
        }')

    RESPONSE=$(curl -s --request POST \
        --url "https://mcp.tavily.com/mcp" \
        --header "Authorization: Bearer $TAVILY_API_KEY" \
        --header 'Content-Type: application/json' \
        --header 'Accept: application/json, text/event-stream' \
        --header 'x-client-source: market-debrief-cn' \
        --data "$MCP_REQUEST") || RESPONSE=""

    JSON_DATA=$(echo "$RESPONSE" | grep '^data:' | sed 's/^data://' | head -1)

    QUERY_SUCCESS=0
    if [ -n "$JSON_DATA" ]; then
        RESULT=$(echo "$JSON_DATA" | jq '.result.structuredContent // .result.content[0].text // empty' 2>/dev/null)
        if [ -n "$RESULT" ] && [ "$RESULT" != "null" ]; then
            ALL_RESULTS=$(echo "$ALL_RESULTS" | jq --argjson r "[$RESULT]" '. + $r' 2>/dev/null || echo "$ALL_RESULTS")
            QUERY_SUCCESS=1
        fi
    fi
    if [ "$QUERY_SUCCESS" -eq 0 ]; then
        FAILED_QUERIES=$((FAILED_QUERIES + 1))
        echo "[WARN] 查询无有效结果: $query" >&2
    fi
done

# ── 输出 ────────────────────────────────────────────────

OUTPUT=$(jq -n \
    --arg date "$TARGET_DATE" \
    --argjson results "$ALL_RESULTS" \
    --argjson failed "$FAILED_QUERIES" \
    '{
        "target_date": $date,
        "search_count": ($results | length),
        "_failed_queries": $failed,
        "results": $results
    }')

echo "$OUTPUT" > "$OUTPUT_FILE"
echo "[完成] 已写入 $OUTPUT_FILE" >&2
if [ "$FAILED_QUERIES" -gt 0 ]; then
    echo "[WARN] ${FAILED_QUERIES}/${#QUERIES[@]} 个查询失败" >&2
fi
