# A股基本面分析Agent

基于Tushare API的A股基本面数据收集和分析系统，采用双格式存储方案。

## 📋 功能特性

### 数据收集
- **全市场覆盖**：自动收集所有A股上市公司数据
- **核心指标**：ROE、PE、PB、股息率、毛利率、净利率（2019-2023年，5年数据）
- **财务安全指标**：资产负债率、流动比率
- **运营效率指标**：总资产周转率、现金流质量比率
- **智能筛选**：自动过滤ST股票和连续亏损企业
- **断点续传**：支持缓存和中断恢复

### 双格式存储
1. **Excel格式**（便于查看）
   - 简洁视图，核心指标一目了然
   - 多工作表优化布局
   - 投资建议自动生成

2. **SQLite数据库**（便于查询）
   - 标准化数据结构
   - 强大的SQL查询功能
   - 便于程序化分析

### AI分析
- 集成Deepseek-R1 API
- 三阶分析框架：商业本质→财务健康→安全边际
- 自动生成投资分析报告

## 🗄️ 数据库结构

### 表结构
```sql
-- 股票基本信息表
CREATE TABLE stocks (
    stock_code TEXT PRIMARY KEY,  -- 股票代码
    stock_name TEXT,              -- 股票名称
    industry TEXT,                -- 所属行业
    list_date TEXT,               -- 上市日期
    created_at TIMESTAMP          -- 创建时间
);

-- 财务指标表
CREATE TABLE financial_metrics (
    stock_code TEXT,    -- 股票代码
    year INTEGER,       -- 年份
    metric_name TEXT,   -- 指标名称（roe/pe/pb/dividend/gross_margin/net_margin/debt_ratio/current_ratio/asset_turnover/ocf_to_profit）
    metric_value REAL,  -- 指标数值
    created_at TIMESTAMP
);
```

### 常用查询示例
```sql
-- 查找高ROE股票
SELECT s.stock_name, fm.metric_value as roe
FROM stocks s JOIN financial_metrics fm ON s.stock_code = fm.stock_code
WHERE fm.metric_name = 'roe' AND fm.year = 2023 AND fm.metric_value >= 15
ORDER BY fm.metric_value DESC;

-- 价值股筛选（高ROE + 低PE + 低PB）
SELECT s.stock_name, roe.metric_value as roe, pe.metric_value as pe, pb.metric_value as pb
FROM stocks s
JOIN financial_metrics roe ON s.stock_code = roe.stock_code
JOIN financial_metrics pe ON s.stock_code = pe.stock_code  
JOIN financial_metrics pb ON s.stock_code = pb.stock_code
WHERE roe.metric_name = 'roe' AND roe.year = 2023 AND roe.metric_value >= 15
AND pe.metric_name = 'pe' AND pe.year = 2023 AND pe.metric_value <= 20
AND pb.metric_name = 'pb' AND pb.year = 2023 AND pb.metric_value <= 3;

-- 财务安全股票（低负债率 + 高流动比率）
SELECT s.stock_name, debt.metric_value as debt_ratio, current.metric_value as current_ratio
FROM stocks s
JOIN financial_metrics debt ON s.stock_code = debt.stock_code
JOIN financial_metrics current ON s.stock_code = current.stock_code
WHERE debt.metric_name = 'debt_ratio' AND debt.year = 2023 AND debt.metric_value <= 0.5
AND current.metric_name = 'current_ratio' AND current.year = 2023 AND current.metric_value >= 1.5;
```

## 🚀 快速开始

### 环境准备
```bash
# 1. 克隆项目
git clone <repository-url>
cd Aagent

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置API密钥
# 编辑 config.py，设置你的 TUSHARE_TOKEN
```

### 数据收集
```bash
# 收集所有A股数据（双格式输出）
python collect_data.py

# 限制股票数量（测试）
python collect_data.py --limit 100

# 自定义时间范围
python collect_data.py --start-year 2020 --end-year 2024
```

### 数据查询
```bash
# 运行查询示例
python query_examples.py

# 或者直接使用
from query_examples import StockQueryHelper
helper = StockQueryHelper()
value_stocks = helper.find_value_stocks(min_roe=15, max_pe=20)
```

### AI分析
```bash
# 1. 在Excel中标记需要分析的股票（need_analysis=True）
# 2. 配置 Deepseek API 密钥
# 3. 运行分析
python analyze_stocks.py
```

## 📊 输出文件

### Excel文件
- `stock_analysis_data.xlsx` - 原始数据（所有指标）
- `stock_analysis_optimized.xlsx` - 优化视图（多工作表）
- `analysis_suggestions.txt` - 投资建议

### SQLite数据库
- `stock_analysis.db` - 完整数据库文件

### 分析报告
- `analysis_reports/*.md` - 个股深度分析报告

## 🔧 高级用法

### 自定义查询
```python
import sqlite3
import pandas as pd

# 连接数据库
conn = sqlite3.connect('stock_analysis.db')

# 复杂筛选示例
query = """
SELECT s.stock_name, s.industry,
       AVG(CASE WHEN fm.metric_name = 'roe' THEN fm.metric_value END) as avg_roe,
       AVG(CASE WHEN fm.metric_name = 'pe' THEN fm.metric_value END) as avg_pe
FROM stocks s
JOIN financial_metrics fm ON s.stock_code = fm.stock_code
WHERE fm.year BETWEEN 2021 AND 2023
GROUP BY s.stock_code, s.stock_name, s.industry
HAVING avg_roe >= 15 AND avg_pe <= 20
ORDER BY avg_roe DESC;
"""

result = pd.read_sql_query(query, conn)
conn.close()
```

### 添加自定义指标
修改 `collect_data.py` 中的数据收集逻辑，添加新的财务指标。

## 📈 投资策略模板

系统内置多种筛选策略：
- **价值投资**：高ROE + 低PE + 低PB
- **股息投资**：高股息率 + 稳定分红
- **成长投资**：高ROE + 营收增长
- **行业分析**：同行业财务指标对比

## ⚠️ 注意事项

1. **API限制**：Tushare有频率限制，程序会自动处理
2. **数据质量**：自动过滤异常数据，但建议人工复核
3. **投资风险**：本工具仅供参考，投资决策需谨慎
4. **数据更新**：建议定期重新运行收集程序

## 🛠️ 开发计划

- [ ] 添加更多财务指标（资产负债率、现金流等）
- [ ] Web界面开发
- [ ] 实时数据更新
- [ ] 更多AI分析模型
- [ ] 回测系统

## 📞 支持

如有问题，请查看：
1. 日志文件（`logs/` 目录）
2. 缓存状态（`cache/` 目录）
3. 数据库完整性检查

---

**免责声明**：本工具仅用于学习和研究，投资有风险，入市需谨慎。 