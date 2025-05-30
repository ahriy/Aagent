# 🎯 A股价值投资分析系统

一个基于Python的A股价值投资分析系统，融合巴菲特、查理芒格、格雷厄姆三位投资大师的智慧，帮助投资者发现具有长期投资价值的股票。

## ✨ 核心功能

### 📊 数据收集系统
- **多Token管理**：智能切换Tushare API token，避免频率限制
- **断点续传**：支持中断后继续收集，提高效率
- **智能过滤**：自动跳过连续3年亏损的股票
- **批量处理**：分批处理5,000+只股票数据
- **SQLite存储**：高效的本地数据库存储

### 🧠 价值投资Agent
融合三位投资大师的理念：

#### 🏆 巴菲特标准 (权重40%)
- 持续高ROE (>15%)
- 低债务比率 (<30%)
- 稳定盈利能力
- 强劲现金流

#### 🧠 查理芒格标准 (权重30%)
- 优质行业选择
- 高经营效率
- 强定价权（高毛利率）
- 合理估值

#### 📚 格雷厄姆标准 (权重30%)
- 低PE估值 (<15x)
- 低PB比率 (<2x)
- 安全边际充足
- 稳定股息回报

### 📈 分析工具
- **股票筛选器**：基于多维度指标筛选价值股票
- **详细报告**：生成专业的投资分析报告
- **数据质量检查**：确保数据完整性和准确性

## 🚀 快速开始

### 1. 环境配置
```bash
# 克隆项目
git clone <repository-url>
cd Aagent

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置API Token
在 `config.py` 中配置您的Tushare token：
```python
TUSHARE_TOKENS = [
    "your_token_1_here",
    "your_token_2_here"  # 可选，支持多token
]
```

### 3. 数据收集
```bash
# 收集2020-2024年的股票数据
python collect_data.py --start-year 2020 --end-year 2024

# 测试收集（限制10只股票）
python collect_data.py --limit 10
```

### 4. 价值投资分析
```bash
# 筛选价值股票（最低分数60分，限制30只）
python value_investment_agent.py --min-score 60 --limit 30

# 分析单个股票
python value_investment_agent.py --stock-code 000001.SZ

# 生成自定义报告
python value_investment_agent.py --min-score 50 --output my_report.md
```

## 📁 项目结构

```
📁 Aagent/
├── 🔧 核心收集器
│   └── collect_data.py            ⭐ 数据收集器（多Token支持）
│
├── 🧠 价值投资Agent
│   └── value_investment_agent.py  ⭐ 价值投资分析引擎
│
├── 📊 分析工具
│   ├── analyze_stocks.py          📈 股票分析工具
│   ├── stock_analyzer.py          🔍 深度分析器
│   └── import_cache_to_db.py      📁 缓存数据导入工具
│
├── 🔍 查询脚本
│   ├── queries/                   📋 正式查询脚本目录
│   │   ├── query_dividend_ranking.py  💰 股息排名查询
│   │   ├── query_dividend_yield.py    📊 股息率排名查询
│   │   └── README.md              📖 查询脚本说明
│   │
│   └── tmp/                       🧪 临时脚本目录
│       ├── test_connection.py     🔗 数据库连接测试
│       ├── test_collect_data.py   🧪 数据收集测试
│       ├── check_data.py          ✅ 数据检查工具
│       ├── data_quality_report.py 📋 数据质量报告
│       ├── query_examples.py      📝 查询示例
│       └── README.md              📖 临时脚本说明
│
├── ⚙️ 配置文件
│   ├── config.py                  🔧 配置管理
│   ├── main.py                    🚀 统一入口
│   └── requirements.txt           📦 依赖管理
│
├── 📚 文档
│   ├── README.md                  📖 项目说明
│   ├── TOKEN_CONFIG.md            🔑 Token配置指南
│   ├── PROJECT_OPTIMIZATION.md    📊 优化记录
│   └── system_prompt.md           🤖 系统提示
│
└── 📁 数据目录
    ├── cache/                     💾 缓存文件
    ├── logs/                      📝 日志文件
    └── stock_analysis.db          🗄️ SQLite数据库
```

## 🎯 使用示例

### 价值投资分析示例
```bash
# 发现高质量价值股票
python value_investment_agent.py --min-score 70 --limit 20

# 输出示例：
🌟 发现 3 只价值股票:
--------------------------------------------------------------------------------
 1. 深物业A       (000011.SZ) | 得分:  75.2 | A 推荐买入     | 房产服务
 2. 平安银行       (000001.SZ) | 得分:  72.8 | A 推荐买入     | 银行
 3. 万科A        (000002.SZ) | 得分:  70.1 | A 推荐买入     | 全国地产

📋 详细报告已生成: value_investment_report_20250525_184848.md
```

### 单股分析示例
```bash
python value_investment_agent.py --stock-code 000001.SZ

# 输出示例：
🎯 平安银行 (000001.SZ)
📊 综合评分: 72.8/100 - A 推荐买入
🏭 所属行业: 银行

🏆 巴菲特分析 (75/100):
   🌟 卓越ROE: 18.5% (>20%)
   💪 低债务负担: 15.2% (<20%)
   📈 持续盈利: 净利率 23.7%

🧠 芒格分析 (70/100):
   🎯 优质行业: 银行
   💰 合理估值: PE 8.6x

📚 格雷厄姆分析 (75/100):
   🎯 低估值: PE 8.6x (<10)
   💎 破净股: PB 0.85x (<1)
   ✅ 资产正增长: 9.4%
```

## 🔧 高级功能

### 多Token管理
系统支持多个Tushare token自动切换：
- **智能检测**：自动识别API限制
- **无缝切换**：token耗尽时自动切换
- **重试机制**：指数退避重试策略
- **统计监控**：详细的请求成功率统计

### 数据质量保证
- **智能过滤**：跳过连续亏损股票
- **数据验证**：确保财务指标合理性
- **缓存机制**：避免重复请求
- **断点续传**：支持中断后继续

### 投资评分体系
- **多维度评估**：ROE、债务率、估值、增长等
- **权重分配**：巴菲特40% + 芒格30% + 格雷厄姆30%
- **等级划分**：A+/A/B+/B/C 五级评分
- **详细解释**：每个评分点都有具体说明

## ⚠️ 重要声明

1. **投资风险**：本系统仅基于历史财务数据分析，不构成投资建议
2. **数据延迟**：财务数据存在滞后性，请结合实时信息
3. **风险控制**：投资有风险，入市需谨慎
4. **长期视角**：价值投资需要长期持有，避免短期投机

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

MIT License

---

*让价值投资的智慧指引您的投资决策* 🎯 