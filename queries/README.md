# 查询脚本目录

本目录包含各种数据库查询和分析脚本。

## 📊 脚本列表

### 1. 股息相关查询
- **`query_dividend_ranking.py`** - 查询股息排名前十的公司
- **`query_dividend_yield.py`** - 计算和查询股息率排名

### 🚀 使用方法

所有脚本都需要在项目根目录运行，因为它们引用上级目录的数据库文件：

```bash
# 方法1：从根目录运行
python queries/query_dividend_ranking.py
python queries/query_dividend_yield.py

# 方法2：进入queries目录运行
cd queries
python query_dividend_ranking.py
python query_dividend_yield.py
```

### 📋 数据要求

- 确保 `stock_analysis.db` 存在于项目根目录
- 数据库中需要有股息、PE、ROE等财务指标数据

### 🔧 自定义查询

您可以基于这些脚本创建更多的自定义查询，只需：
1. 复制现有脚本作为模板
2. 修改SQL查询语句
3. 调整输出格式

### 📝 注意事项

- 所有脚本使用相对路径 `../stock_analysis.db` 访问数据库
- 如果移动脚本位置，请相应调整数据库路径 