# 🤖 价值投资Agent - DeepSeek AI深度分析集成

## 📋 概述

价值投资Agent现已集成DeepSeek AI分析功能，为筛选出的高价值股票提供专业的AI深度分析报告。

## ✨ 新增功能

### 🔧 核心功能
- **AI深度分析**: 对筛选出的股票进行专业价值投资分析
- **专业系统提示词**: 基于20年A股实战经验的价值投资专家角色
- **三阶分析框架**: 商业本质诊断 → 财务健康透视 → 安全边际测算
- **智能分析流程**: 自动将评分数据和财务指标传递给AI分析

### 📊 分析框架

#### 第一阶段：商业本质诊断
- 商业模式可持续性（客户粘性、定价权、规模效应）
- 行业竞争格局与公司护城河宽度
- 管理层诚信度与资本配置能力
- 产业生命周期位置判断

#### 第二阶段：财务健康透视
- **盈利质量**: ROE驱动因子拆解（杜邦分析）、会计稳健性
- **现金流质量**: 经营现金流与净利润匹配度、资本开支效率
- **财务杠杆**: 债务结构合理性、偿债能力压力测试
- **成长可持续性**: 内生增长率、再投资回报率

#### 第三阶段：安全边际测算
- **内在价值评估**: DCF模型、PEG估值、资产重置成本
- **相对估值比较**: 同业横比、历史纵比、PB-ROE象限分析
- **极端情景分析**: 熊市、行业衰退、黑天鹅事件的价值底线
- **风险收益比**: 预期回报率vs最大损失概率

## ⚙️ 配置方法

### 1. 环境变量配置（推荐）

在`.env`文件中添加：
```bash
DEEPSEEK_API_KEY=your_deepseek_api_key
```

### 2. config.py配置

在`config.py`文件中设置：
```python
DEEPSEEK_API_KEY = "your_deepseek_api_key"
```

### 3. JSON配置文件

在`config.json`文件中配置：
```json
{
    "deepseek_api_key": "your_deepseek_api_key",
    "tushare_tokens": ["your_tushare_tokens"]
}
```

## 🚀 使用方法

### 基本使用
```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行价值投资分析（包含AI分析）
python value_investment_agent.py --min-score 60 --limit 10
```

### 分析单个股票
```bash
python value_investment_agent.py --stock-code 000858
```

### 自定义参数
```bash
python value_investment_agent.py \
    --min-score 65 \
    --preliminary-threshold 50 \
    --limit 15 \
    --output my_analysis_report.md
```

## 📝 输出报告格式

生成的报告现在包含以下部分：

1. **投资摘要** - 一句话核心观点+评级
2. **巴菲特分析** - 基于价值投资标准的评分
3. **芒格分析** - 基于理性思维和质量导向的评分
4. **格雷厄姆分析** - 基于安全边际的评分
5. **🤖 AI深度分析** - DeepSeek专业分析报告
   - 商业本质分析（护城河+竞争优势）
   - 财务健康诊断（盈利质量+现金流+债务）
   - 估值与安全边际（内在价值+相对估值+风险评估）
   - 催化剂与风险因素
   - 投资建议（目标价+持有期+仓位建议）

## 🔄 分析流程

1. **初步筛选**: 基于历史数据快速筛选候选股票
2. **实时PE评估**: 调用Tushare API获取实时PE数据
3. **🆕 DeepSeek AI分析**: 对通过筛选的股票进行深度AI分析
4. **生成报告**: 包含AI分析的综合投资报告

## ⚠️ 注意事项

- DeepSeek API有调用频率限制，系统会自动控制调用间隔
- AI分析需要消耗API额度，建议合理设置筛选数量
- 如果未配置DeepSeek API Key，系统会跳过AI分析环节
- AI分析结果仅供参考，不构成投资建议

## 🛠️ 技术特性

- **智能错误处理**: API调用失败时提供友好的错误信息
- **配置灵活性**: 支持多种配置方式，优先级：环境变量 > config.py > JSON文件
- **性能优化**: 仅对高分股票进行AI分析，减少不必要的API调用
- **日志完整**: 详细记录AI分析过程和结果统计

## 📊 统计信息

系统会提供详细的分析统计，包括：
- 总股票数和筛选结果
- Tushare API调用次数和成功率
- **🆕 AI分析成功数量和可用性统计**

## 🎯 最佳实践

1. **合理设置筛选参数**: 避免过多股票进行AI分析
2. **监控API用量**: 关注DeepSeek API的使用情况
3. **结合人工判断**: AI分析作为辅助工具，结合专业判断
4. **定期更新**: 保持系统提示词和分析框架的及时更新

---

*🤖 现在的价值投资Agent不仅具备量化筛选能力，还拥有了AI深度分析的专业判断力！* 