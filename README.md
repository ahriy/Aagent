# A股基本面分析Agent

这是一个基于Tushare API和Deepseek AI的A股基本面分析工具，能够帮助投资者系统性地收集和分析上市公司的基本面数据。

## 功能特点

### 阶段一：数据收集
- 自动获取所有A股公司基本信息
- 收集近7年的核心财务数据：
  - ROE（净资产收益率）
  - 毛利率和净利率
  - PE市盈率
  - 股息率
- 智能缓存机制，支持断点续传
- 批量处理，每50只股票一个缓存文件
- 生成完整的Excel数据表格

### 阶段二：深度分析
- 基于Deepseek AI的专业分析
- 对选定股票进行深度基本面分析
- 生成详细的Markdown分析报告
- 包含投资建议和风险评估

## 项目结构

```
Aagent/
├── collect_data.py          # 数据收集程序
├── analyze_stocks.py        # AI分析程序
├── stock_analyzer.py        # 基础分析类
├── main.py                  # 原始分析程序（单股票）
├── config.py               # 配置文件
├── .env.template           # 环境变量模板
├── requirements.txt        # 依赖包
├── system_prompt.md        # AI分析提示词
├── cache/                  # 数据缓存目录
├── logs/                   # 日志文件目录
├── reports/                # 图表报告目录
├── analysis_reports/       # AI分析报告目录
└── stock_analysis_data.xlsx # 最终数据表格
```

## 安装说明

1. 克隆项目到本地：
```bash
git clone git@github.com:ahriy/Aagent.git
cd Aagent
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
```bash
# 复制环境变量模板
cp .env.template .env

# 编辑.env文件，填入您的API密钥
# TUSHARE_TOKEN=你的tushare_token
# DEEPSEEK_API_KEY=你的deepseek_api_key
```

## 使用方法

### 1. 数据收集阶段

收集所有A股数据（约需1-2小时）：
```bash
python collect_data.py
```

测试模式（只处理10只股票）：
```bash
python collect_data.py --limit 10
```

### 2. 数据分析阶段

在Excel文件中将需要分析的股票"是否分析"列设为TRUE，然后运行：
```bash
python analyze_stocks.py
```

### 3. 单股票分析（旧版本）

分析单只股票：
```bash
python main.py
```

## 配置说明

主要配置项在 `config.py` 中：

- **数据收集配置**：缓存目录、批次大小、请求延迟
- **分析配置**：报告目录、分析指标、阈值设置
- **API配置**：请求间隔、重试次数

敏感配置项在 `.env` 文件中：
- `TUSHARE_TOKEN`：Tushare Pro API token
- `DEEPSEEK_API_KEY`：Deepseek AI API密钥

## 输出说明

### 数据文件
- `stock_analysis_data.xlsx`：包含所有A股基本面数据的Excel文件
- `cache/batch_*.json`：分批缓存的原始数据

### 分析报告
- `analysis_reports/`：AI生成的Markdown分析报告
- `reports/`：图表和基础分析报告

### 日志文件
- `logs/`：详细的运行日志，用于调试和监控

## API要求

### Tushare Pro
- 注册账号：https://tushare.pro/
- 获取API token
- 建议使用积分较高的账号以获得更好的数据权限

### Deepseek AI
- 注册账号：https://platform.deepseek.com/
- 获取API密钥
- 按使用量付费

## 注意事项

- **数据权限**：确保Tushare账号有足够积分访问所需数据
- **请求频率**：程序已内置请求延迟，避免触发API限制
- **存储空间**：全量数据收集需要约100MB存储空间
- **运行时间**：首次数据收集需要1-2小时
- **数据更新**：建议定期运行数据收集程序更新数据
- **投资风险**：分析结果仅供参考，投资决策请自行判断

## 技术特性

- **智能缓存**：支持断点续传，避免重复下载
- **批量处理**：高效处理大量股票数据
- **错误处理**：完善的异常处理和重试机制
- **日志记录**：详细的运行日志便于问题排查
- **配置灵活**：支持各种参数调整和定制

## 版本要求

- Python 3.8+
- 推荐使用虚拟环境
- 网络连接稳定（用于API调用）

## 开源协议

本项目遵循MIT开源协议，欢迎贡献代码和反馈问题。 