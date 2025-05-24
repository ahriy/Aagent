import pandas as pd
import os
import json
import requests
from loguru import logger
from datetime import datetime
from dotenv import load_dotenv

class DeepseekAnalyzer:
    def __init__(self, api_key, api_url, system_prompt_file="system_prompt.md"):
        self.api_key = api_key
        self.api_url = api_url
        self.system_prompt = self._load_system_prompt(system_prompt_file)
        
    def _load_system_prompt(self, file_path):
        """加载系统提示词"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"无法读取系统提示词文件 {file_path}: {e}")
            return "你是一个专业的股票分析师，请基于提供的数据进行深入的基本面分析。"
        
    def analyze_stock(self, stock_data):
        """使用Deepseek API分析股票数据"""
        # 构建提示词
        prompt = self._build_prompt(stock_data)
        
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-ai/DeepSeek-R1",
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,  # 降低温度，提高一致性
                    "max_tokens": 6000   # 增加输出长度
                },
                timeout=120  # 增加超时时间
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.error(f"API调用失败: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"分析过程中出现错误: {e}")
            return None
            
    def _build_prompt(self, stock_data):
        """构建分析提示词"""
        prompt = f"""请按照你的专业分析框架，对以下股票进行深度价值投资分析：

## 基本信息
- **公司名称**: {stock_data['stock_name']}
- **股票代码**: {stock_data['stock_code']}
- **所属行业**: {stock_data['industry']}

## 财务数据（近7年）

### ROE（净资产收益率）%
"""
        # 添加ROE数据
        roe_data = []
        for col in sorted([c for c in stock_data.index if c.startswith('roe_')]):
            year = col.split('_')[1]
            if pd.notna(stock_data[col]):
                roe_data.append(f"{year}年: {stock_data[col]:.2f}%")
        
        if roe_data:
            prompt += " | ".join(roe_data) + "\n"
        else:
            prompt += "数据缺失\n"
            
        prompt += "\n### PE（市盈率）倍\n"
        # 添加PE数据
        pe_data = []
        for col in sorted([c for c in stock_data.index if c.startswith('pe_')]):
            year = col.split('_')[1]
            if pd.notna(stock_data[col]):
                pe_data.append(f"{year}年: {stock_data[col]:.2f}x")
        
        if pe_data:
            prompt += " | ".join(pe_data) + "\n"
        else:
            prompt += "数据缺失\n"
            
        prompt += "\n### 股息率 %\n"
        # 添加股息率数据
        div_data = []
        for col in sorted([c for c in stock_data.index if c.startswith('dividend_')]):
            year = col.split('_')[1]
            if pd.notna(stock_data[col]):
                div_data.append(f"{year}年: {stock_data[col]:.2f}%")
        
        if div_data:
            prompt += " | ".join(div_data) + "\n"
        else:
            prompt += "数据缺失\n"
            
        prompt += "\n### 毛利率 %\n"
        # 添加毛利率数据
        gm_data = []
        for col in sorted([c for c in stock_data.index if c.startswith('gross_margin_')]):
            year = col.split('_')[1]
            if pd.notna(stock_data[col]):
                gm_data.append(f"{year}年: {stock_data[col]:.2f}%")
        
        if gm_data:
            prompt += " | ".join(gm_data) + "\n"
        else:
            prompt += "数据缺失（银行等金融企业通常无此指标）\n"
            
        prompt += "\n### 净利率 %\n"
        # 添加净利率数据
        nm_data = []
        for col in sorted([c for c in stock_data.index if c.startswith('net_margin_')]):
            year = col.split('_')[1]
            if pd.notna(stock_data[col]):
                nm_data.append(f"{year}年: {stock_data[col]:.2f}%")
        
        if nm_data:
            prompt += " | ".join(nm_data) + "\n"
        else:
            prompt += "数据缺失\n"
            
        prompt += """\n## 分析要求

请严格按照你的【商业本质诊断→财务健康透视→安全边际测算】三阶分析框架进行分析，并给出：

1. **投资摘要**（一句话观点+明确评级：强烈推荐/推荐/中性/回避/强烈回避）
2. **商业本质分析**（结合行业特点分析护城河和竞争优势）
3. **财务健康诊断**（基于提供数据的深度分析）
4. **估值与安全边际**（当前估值水平+内在价值判断）
5. **关键风险因素**（主要下行风险+概率评估）
6. **投资建议**（目标价格区间+持有期建议+仓位配置建议）

请用markdown格式输出，确保分析有理有据，避免模糊表述。"""
        
        return prompt

def setup_logger():
    """配置日志"""
    log_path = "logs"
    os.makedirs(log_path, exist_ok=True)
    logger.add(
        os.path.join(log_path, "analysis_{time}.log"),
        rotation="500 MB",
        encoding="utf-8"
    )

def load_config():
    """加载配置"""
    load_dotenv()
    config = {}
    
    # API密钥
    config['api_key'] = os.getenv('DEEPSEEK_API_KEY')
    if not config['api_key']:
        logger.error("未找到DEEPSEEK_API_KEY环境变量，请设置API密钥")
        logger.info("请在.env文件中添加：DEEPSEEK_API_KEY=your_api_key_here")
        return None
    
    # API URL
    config['api_url'] = os.getenv('API_URL', 'https://api.deepseek.com/v1/chat/completions')
    logger.info(f"使用API URL: {config['api_url']}")
    
    return config

def simulate_analysis(stock_data):
    """模拟分析结果（当没有API密钥时使用）"""
    analysis = f"""# {stock_data['stock_name']}（{stock_data['stock_code']}）投资分析报告

## 投资摘要
**核心观点**: 基于现有财务数据的初步分析 | **评级**: 中性（需更多数据验证）

## 基本信息
- **公司名称**: {stock_data['stock_name']}
- **股票代码**: {stock_data['stock_code']}
- **所属行业**: {stock_data['industry']}
- **分析日期**: {datetime.now().strftime('%Y-%m-%d')}

## 财务数据概览

### ROE（净资产收益率）趋势
"""
    
    # 添加ROE分析
    roe_data = []
    for col in sorted([c for c in stock_data.index if c.startswith('roe_')]):
        year = col.split('_')[1]
        if pd.notna(stock_data[col]):
            roe_data.append(f"- {year}年：{stock_data[col]:.2f}%")
    
    if roe_data:
        analysis += "\n".join(roe_data)
    else:
        analysis += "- 数据缺失"
    
    analysis += """

### PE（市盈率）水平
"""
    
    # 添加PE分析
    pe_data = []
    for col in sorted([c for c in stock_data.index if c.startswith('pe_')]):
        year = col.split('_')[1]
        if pd.notna(stock_data[col]):
            pe_data.append(f"- {year}年：{stock_data[col]:.2f}倍")
    
    if pe_data:
        analysis += "\n".join(pe_data)
    else:
        analysis += "- 数据缺失"
    
    analysis += """

### 股息率水平
"""
    
    # 添加股息率分析
    div_data = []
    for col in sorted([c for c in stock_data.index if c.startswith('dividend_')]):
        year = col.split('_')[1]
        if pd.notna(stock_data[col]):
            div_data.append(f"- {year}年：{stock_data[col]:.2f}%")
    
    if div_data:
        analysis += "\n".join(div_data)
    else:
        analysis += "- 数据缺失"
    
    analysis += """

## 投资建议

**注意**: 这是基于有限数据的模拟分析，如需详细的价值投资分析，请配置Deepseek API密钥以获得专业的三阶分析框架报告。

### 风险提示
- 本分析仅基于历史财务数据，未考虑宏观环境、行业变化等因素
- 投资有风险，建议结合更多信息进行决策
- 股市波动较大，请注意风险控制

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    return analysis

def main():
    """主程序入口"""
    setup_logger()
    
    # 创建报告目录
    reports_dir = "analysis_reports"
    os.makedirs(reports_dir, exist_ok=True)
    
    # 读取Excel文件
    try:
        df = pd.read_excel('stock_analysis_data.xlsx')
        logger.info(f"成功读取Excel文件，共{len(df)}只股票")
    except Exception as e:
        logger.error(f"读取Excel文件失败: {e}")
        return
        
    # 获取需要分析的股票
    stocks_to_analyze = df[df['need_analysis'] == True]
    
    if len(stocks_to_analyze) == 0:
        logger.info("没有找到需要分析的股票（need_analysis=True）")
        return
        
    logger.info(f"找到{len(stocks_to_analyze)}只需要分析的股票")
    
    # 加载配置
    config = load_config()
    
    if config:
        # 初始化分析器
        analyzer = DeepseekAnalyzer(config['api_key'], config['api_url'])
        logger.info("使用Deepseek API进行专业价值投资分析")
        logger.info(f"系统提示词已加载：{len(analyzer.system_prompt)}字符")
    else:
        logger.info("未配置API密钥，将使用模拟分析")
        analyzer = None
    
    # 分析每只股票
    for idx, stock in stocks_to_analyze.iterrows():
        logger.info(f"开始分析: {stock['stock_name']} ({stock['stock_code']})")
        
        # 进行深度分析
        if analyzer:
            analysis_result = analyzer.analyze_stock(stock)
        else:
            analysis_result = simulate_analysis(stock)
        
        if analysis_result:
            # 保存分析报告
            report_file = os.path.join(
                reports_dir, 
                f"{stock['stock_code']}_{datetime.now().strftime('%Y%m%d')}.md"
            )
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(analysis_result)
                
            logger.info(f"分析报告已保存: {report_file}")
        else:
            logger.error(f"分析失败: {stock['stock_code']}")
    
    logger.info("所有分析完成")

if __name__ == "__main__":
    main() 