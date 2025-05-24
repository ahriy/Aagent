import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Tushare API配置
TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN")

# Deepseek API配置  
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# 数据文件路径
EXCEL_FILE_PATH = "stock_analysis_data.xlsx"

# 日志配置
LOG_LEVEL = "INFO"
LOG_DIR = "logs"

# 缓存配置
CACHE_DIR = "cache"
CACHE_BATCH_SIZE = 50

# 报告配置
REPORTS_DIR = "reports"
ANALYSIS_REPORTS_DIR = "analysis_reports"

# API请求配置
REQUEST_DELAY = 0.2  # 请求间隔（秒）
MAX_RETRIES = 3      # 最大重试次数

# 分析配置
DEFAULT_TIMEPERIOD = 5  # 默认分析最近5年的数据
ANALYSIS_INDICATORS = [
    'roe',  # 净资产收益率
    'roa',  # 总资产收益率
    'gross_profit_margin',  # 毛利率
    'net_profit_margin',  # 净利率
    'debt_to_assets',  # 资产负债率
    'current_ratio',  # 流动比率
    'quick_ratio',  # 速动比率
]

# 指标阈值设置
THRESHOLDS = {
    'roe': 15.0,  # ROE基准线
    'debt_to_assets': 60.0,  # 资产负债率警戒线
    'current_ratio': 2.0,  # 流动比率基准线
    'quick_ratio': 1.0,  # 速动比率基准线
    'revenue_growth': 10.0,  # 营收增长率基准线
    'profit_growth': 10.0,  # 利润增长率基准线
}

# 数据缓存配置
CACHE_EXPIRY = 24 * 60 * 60  # 缓存过期时间（秒） 