from stock_analyzer import StockAnalyzer
from datetime import datetime, timedelta
from loguru import logger
import sys
import os

def setup_logger():
    """配置日志"""
    log_path = "logs"
    os.makedirs(log_path, exist_ok=True)
    logger.add(
        os.path.join(log_path, "stock_analysis_{time}.log"),
        rotation="500 MB",
        encoding="utf-8"
    )

def main():
    """主程序入口"""
    setup_logger()
    
    # 创建分析器实例
    analyzer = StockAnalyzer()
    
    # 设置分析时间范围
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=365*5)).strftime('%Y%m%d')
    
    # 示例股票代码（格式：000001.SZ）
    stock_code = input("请输入股票代码（例如：000001.SZ）：").strip()
    
    try:
        # 获取股票信息
        stock_info = analyzer.get_stock_info(stock_code)
        if stock_info is None:
            logger.error(f"未找到股票 {stock_code} 的信息")
            return
            
        logger.info(f"开始分析 {stock_code} {stock_info['name']}")
        
        # 获取财务数据
        balance_sheet, income, cashflow = analyzer.get_financial_data(
            stock_code, start_date, end_date
        )
        
        if balance_sheet is None or income is None or cashflow is None:
            logger.error("获取财务数据失败")
            return
            
        # 计算财务比率
        ratios = analyzer.calculate_financial_ratios(balance_sheet, income)
        
        # 分析增长性
        growth = analyzer.analyze_growth(income)
        
        # 生成报告
        report_path = analyzer.generate_report(stock_code, ratios, growth)
        if report_path:
            logger.info(f"分析报告已生成：{report_path}")
            
        # 绘制趋势图
        plot_path = analyzer.plot_financial_trends(stock_code, ratios, growth)
        if plot_path:
            logger.info(f"趋势图已生成：{plot_path}")
            
        logger.info("分析完成！")
        
    except Exception as e:
        logger.error(f"分析过程中出现错误: {e}")
        raise

if __name__ == "__main__":
    main() 