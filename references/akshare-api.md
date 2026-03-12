# AkShare 数据接口参考

> 本文件列出 market-debrief-cn 用到的全部 akshare 接口、参数、返回字段和调用示例。
> 当接口报错或字段变化时，查阅此文件排查。

---

## 目录

1. [指数日线 - stock_zh_index_daily_em](#1-指数日线)
2. [指数PE - stock_index_pe_lg](#2-指数pe)
3. [全A PB - stock_a_all_pb](#3-全a-pb)
4. [全市场资金流向 - stock_market_fund_flow](#4-全市场资金流向)
5. [行业资金流向 - stock_sector_fund_flow_rank](#5-行业资金流向)
6. [行业板块行情 - stock_board_industry_name_em](#6-行业板块行情)
7. [涨停池 - stock_zt_pool_em](#7-涨停池)
8. [跌停池 - stock_zt_pool_dtgc_em](#8-跌停池)
9. [炸板池 - stock_zt_pool_zbgc_em](#9-炸板池)
10. [强势股池 - stock_zt_pool_strong_em](#10-强势股池)
11. [北向资金 - stock_hsgt_hist_em](#11-北向资金)
12. [两融余额 - stock_margin_account_info](#12-两融余额)
13. [国债收益率 - bond_china_yield](#13-国债收益率)
14. [龙虎榜 - stock_lhb_detail_em](#14-龙虎榜)

---

## 1. 指数日线

```python
ak.stock_zh_index_daily_em(symbol="sh000001", start_date="20260101", end_date="20260311")
```

**指数代码映射**：

| 名称 | 代码 |
|------|------|
| 上证指数 | sh000001 |
| 深证成指 | sz399001 |
| 创业板指 | sz399006 |
| 科创50 | sh000688 |
| 沪深300 | sh000300 |
| 中证500 | sh000905 |

**返回字段**：`date, open, close, high, low, volume, amount`

---

## 2. 指数PE

```python
ak.stock_index_pe_lg(symbol="沪深300")
```

**可用 symbol 值**（必须用中文名）：`沪深300`, `中证500`, `中证1000`, `上证50`

**返回字段**：`日期, 指数, 等权静态市盈率, 静态市盈率, 静态市盈率中位数, 等权滚动市盈率, 滚动市盈率, 滚动市盈率中位数`

> PE 百分位需自行计算：`(df["滚动市盈率"] < current_pe).mean()`

---

## 3. 全A PB

```python
ak.stock_a_all_pb()
```

**返回字段**：`date, middlePB, equalWeightAveragePB, close, quantileInAllHistoryMiddlePB, quantileInRecent10YearsMiddlePB, quantileInAllHistoryEqualWeightAveragePB, quantileInRecent10YearsEqualWeightAveragePB`

> 已自带历史百分位字段，无需额外计算。

---

## 4. 全市场资金流向

```python
ak.stock_market_fund_flow()
```

**返回字段**：`日期, 上证-收盘价, 上证-涨跌幅, 深证-收盘价, 深证-涨跌幅, 主力净流入-净额, 主力净流入-净占比, 超大单净流入-净额, 超大单净流入-净占比, 大单净流入-净额, 大单净流入-净占比, 中单净流入-净额, 中单净流入-净占比, 小单净流入-净额, 小单净流入-净占比`

> 净额单位为元。超大单（≥100万）、大单（20-100万）、中单（4-20万）、小单（<4万）。

---

## 5. 行业资金流向

```python
ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流")
```

**indicator 可选**：`今日`, `5日`, `10日`

**返回字段**：`序号, 名称, 今日涨跌幅, 今日主力净流入-净额, 今日主力净流入-净占比, 今日超大单净流入-净额, 今日超大单净流入-净占比, 今日大单净流入-净额, 今日大单净流入-净占比, 今日中单净流入-净额, 今日中单净流入-净占比, 今日小单净流入-净额, 今日小单净流入-净占比, 今日主力净流入最大股`

---

## 6. 行业板块行情

```python
ak.stock_board_industry_name_em()
```

**返回字段**：`排名, 板块名称, 板块代码, 最新价, 涨跌额, 涨跌幅, 总市值, 换手率, 上涨家数, 下跌家数, 领涨股票, 领涨股票-涨跌幅`

---

## 7. 涨停池

```python
ak.stock_zt_pool_em(date="20260311")
```

**限制**：仅可获取最近 30 个交易日数据。

**关键字段**：`代码, 名称, 涨停价, 最新价, 成交额, 流通市值, 总市值, 换手率, 封板资金, 首次封板时间, 最后封板时间, 炸板次数, 涨停统计, 连板数, 所属行业`

---

## 8. 跌停池

```python
ak.stock_zt_pool_dtgc_em(date="20260311")
```

**限制**：仅可获取最近 30 个交易日数据。

---

## 9. 炸板池

```python
ak.stock_zt_pool_zbgc_em(date="20260311")
```

**限制**：仅可获取最近 30 个交易日数据。

---

## 10. 强势股池

```python
ak.stock_zt_pool_strong_em(date="20260311")
```

用于获取连板数据，判断市场赚钱效应。

---

## 11. 北向资金

```python
ak.stock_hsgt_hist_em(symbol="沪股通")  # 或 "深股通"
```

**返回字段**：`日期, 当日成交净买额, 买入成交额, 卖出成交额, 历史累计净买额, 当日资金流入, 当日余额, 持股市值, 领涨股, 领涨股-涨跌幅, 上证指数, 上证指数-涨跌幅, 领涨股-代码`

> 近期数据可能 NaN（延迟发布），使用时注意过滤。

---

## 12. 两融余额

```python
ak.stock_margin_account_info()
```

**返回字段**：`日期, 融资余额, 融券余额, 融资买入额, 融券卖出额, 证券公司数量, 营业部数量, 个人投资者数量, 机构投资者数量, 参与交易的投资者数量, 有融资融券负债的投资者数量, 担保物总价值, 平均维持担保比例`

> 融资余额单位为亿元。

---

## 13. 国债收益率

```python
ak.bond_china_yield(start_date="20260301", end_date="20260311")
```

**返回字段**：`曲线名称, 日期, 3月, 6月, 1年, 3年, 5年, 7年, 10年, 30年`

> 筛选 `曲线名称 == "中债国债收益率曲线"` 取10年期。

---

## 14. 龙虎榜

```python
ak.stock_lhb_detail_em(start_date="20260311", end_date="20260311")
```

**返回字段**：`序号, 代码, 名称, 上榜日, 解读, 收盘价, 涨跌幅, 龙虎榜净买额, 龙虎榜买入额, 龙虎榜卖出额, 龙虎榜成交额, 市场总成交额, 净买额占总成交比, 成交额占总成交比, 换手率, 流通市值, 上榜原因, 上榜后1日, 上榜后2日, 上榜后5日, 上榜后10日`

---

## 常见问题

**Q: 接口报 RemoteDisconnected 错误？**
A: 东方财富数据源限流。等待 5-10 秒重试，或在 `fetch_market_data.py` 中已内置 `safe_call` 容错。

**Q: 涨跌停数据返回空？**
A: 数据仅保留最近 30 个交易日，超出范围返回空。

**Q: 北向资金数据显示 NaN？**
A: 当日/近日数据可能延迟发布，属正常现象。分析时跳过 NaN 行。
