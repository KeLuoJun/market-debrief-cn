# AkShare 接口参考

本文档记录 `fetch_market_data.py` 中使用的核心AkShare接口及其字段说明。

## 目录

1. [市场总貌](#市场总貌)
2. [历史K线](#历史k线)
3. [行业/概念板块](#行业概念板块)
4. [北向资金](#北向资金)
5. [融资融券](#融资融券)
6. [龙虎榜](#龙虎榜)
7. [板块资金流向](#板块资金流向)
8. [常见错误处理](#常见错误处理)

---

## 市场总貌

```python
df = ak.stock_zh_a_spot_em()
```

**关键字段**：

| 字段 | 说明 |
|-----|-----|
| `代码` | 股票代码 |
| `名称` | 股票名称 |
| `最新价` | 当前价格 |
| `涨跌幅` | 今日涨跌幅(%) |
| `成交额` | 今日成交额(元) |
| `成交量` | 今日成交量(手) |
| `换手率` | 换手率(%) |

**`fetch_market_data.py` 输出的 `market_overview` 字段**：

```json
{
  "total_stocks": 5100,
  "total_amount": 1234567890000,
  "total_amount_yi": 12345.68,
  "avg_turnover": 2.3,
  "up_count": 3200,
  "down_count": 1500,
  "up_limit": 45,
  "down_limit": 8,
  "limit_ratio": "45:8",
  "avg_change_pct": 0.35,
  "median_change_pct": 0.12
}
```

---

## 历史K线

```python
df = ak.stock_zh_a_hist(
    symbol="000001",       # 上证指数
    period="daily",
    start_date="20250101",
    end_date="20251231",
    adjust="qfq"           # 前复权
)
```

**常用指数代码**：

| 代码 | 名称 |
|-----|-----|
| `000001` | 上证指数 |
| `399001` | 深证成指 |
| `399006` | 创业板指 |
| `000016` | 上证50 |
| `000905` | 中证500 |
| `000688` | 科创50 |

**K线字段**：`日期`, `开盘`, `收盘`, `最高`, `最低`, `成交量`, `成交额`, `振幅`, `涨跌幅`, `涨跌额`, `换手率`

**`fetch_market_data.py` 输出的 `index_kline` 结构**（`--action multi-index`）：

```json
{
  "000001": {
    "name": "上证指数",
    "data": [
      {
        "日期": "2025-03-10",
        "开盘": 3350.0,
        "收盘": 3380.0,
        "最高": 3395.0,
        "最低": 3340.0,
        "成交量": 123456789,
        "MA5": 3360.0,
        "MA20": 3320.0,
        "MA60": 3280.0
      }
    ]
  }
}
```

---

## 行业/概念板块

```python
# 行业板块
df = ak.stock_board_industry_name_em()

# 概念板块
df = ak.stock_board_concept_name_em()
```

**字段**：`板块名称`, `涨跌幅`, `成交额`, `换手率`, `上涨家数`, `下跌家数`, `领涨股票`

**`fetch_market_data.py` 注意**：默认返回前30条（按涨跌幅降序排列）。

---

## 北向资金

```python
# 北向资金净流向（主方法）
df = ak.stock_hsgt_north_net_flow_in_em(symbol="北向")

# 备用：沪股通历史
df = ak.stock_hsgt_hist_em(symbol="沪股通")
```

**常见字段（因接口版本不同而异）**：
- `当日净流入` / `净流入` / `当日成交净买额`（单位：元）
- `日期`

**`fetch_market_data.py` 输出的 `northbound_flow` 结构**：

```json
{
  "latest": {
    "日期": "2025-03-10",
    "当日净流入": 3200000000
  },
  "recent_data": [...],
  "data_count": 20
}
```

**注意**：北向资金接口较不稳定，脚本会自动fallback。若两种方法都失败，返回 `{"error": "..."}`。

---

## 融资融券

```python
# 上交所融资融券数据
df = ak.stock_margin_sse(start_date="20250101")
```

**字段**：`交易日期`, `融资余额`, `融资买入额`, `融资偿还额`, `融券余量`, `融券余额`

**`fetch_market_data.py` 输出的 `margin_data` 结构**：

```json
{
  "latest": { "融资余额": 1580000000000, ... },
  "margin_balance": 1580000000000,
  "margin_change": 5200000000,
  "margin_change_yi": 52.0
}
```

---

## 龙虎榜

```python
df = ak.stock_lhb_detail_em(start_date="20250310", end_date="20250310")
```

**字段**：`代码`, `名称`, `解读`（上榜原因）, `收盘价`, `涨跌幅`, `龙虎榜净买额`, `龙虎榜买入额`, `龙虎榜卖出额`, `市场总成交额`

**`fetch_market_data.py` 输出的 `lhb_data` 结构**：

```json
{
  "date": "20250310",
  "count": 25,
  "data": [
    {
      "代码": "600000",
      "名称": "浦发银行",
      "解读": "连续三日涨停",
      "龙虎榜净买额": 123456789
    }
  ]
}
```

**注意**：`stock_lhb_detail_em` 的参数名在不同akshare版本中可能是 `date` 或 `start_date`/`end_date`，脚本已处理兼容性。

---

## 板块资金流向

```python
df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流")
```

**字段**：`名称`, `净额`, `净占比`, `主力净流入`, `超大单净流入`, `大单净流入`, `中单净流入`, `小单净流入`（单位：元）

---

## 常见错误处理

`fetch_market_data.py` 对每个接口都有独立 try/except，失败时返回空结构而不中断整体数据获取。

### 接口调用频率注意事项
- AkShare 部分接口有访问频率限制，建议连续调用之间加 `time.sleep(0.5)`
- 股市收盘后（15:30后）数据完整度最高
- 盘中获取的数据为实时/准实时，可能存在轻微延迟

### 常见失败原因
| 错误 | 可能原因 | 解决方法 |
|-----|---------|---------|
| `ConnectionError` | 网络问题 | 检查网络，重试 |
| `KeyError: '字段名'` | AkShare版本不同，字段名变化 | 更新akshare: `pip install -U akshare` |
| `Empty DataFrame` | 非交易日、数据未更新 | 确认当日是否为交易日 |
| 北向资金接口失败 | 该接口较不稳定 | 脚本会自动fallback到备用接口 |

### 更新akshare
```bash
pip install -U akshare
```
