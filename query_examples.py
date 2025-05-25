#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A股基本面数据SQLite查询示例
包含常用的价值投资筛选查询
"""

import sqlite3
import pandas as pd
from datetime import datetime

class StockQueryHelper:
    def __init__(self, db_path='stock_analysis.db'):
        self.db_path = db_path
    
    def connect(self):
        """连接数据库"""
        return sqlite3.connect(self.db_path)
    
    def get_available_metrics(self):
        """获取所有可用的指标名称"""
        conn = self.connect()
        query = """
        SELECT DISTINCT metric_name 
        FROM financial_metrics 
        ORDER BY metric_name
        """
        result = pd.read_sql_query(query, conn)
        conn.close()
        return result['metric_name'].tolist()
    
    def get_available_years(self):
        """获取所有可用的年份"""
        conn = self.connect()
        query = """
        SELECT DISTINCT year 
        FROM financial_metrics 
        ORDER BY year DESC
        """
        result = pd.read_sql_query(query, conn)
        conn.close()
        return result['year'].tolist()
    
    def find_high_roe_stocks(self, min_roe=15, year=2023):
        """查找高ROE股票"""
        conn = self.connect()
        query = """
        SELECT s.stock_code, s.stock_name, s.industry, fm.metric_value as roe
        FROM stocks s
        JOIN financial_metrics fm ON s.stock_code = fm.stock_code
        WHERE fm.metric_name = 'roe' 
        AND fm.year = ?
        AND fm.metric_value >= ?
        ORDER BY fm.metric_value DESC
        """
        result = pd.read_sql_query(query, conn, params=[year, min_roe])
        conn.close()
        return result
    
    def find_value_stocks(self, min_roe=15, max_pe=20, year=2023):
        """查找价值股票（高ROE + 低PE）"""
        conn = self.connect()
        query = """
        SELECT s.stock_code, s.stock_name, s.industry,
               roe.metric_value as roe,
               pe.metric_value as pe
        FROM stocks s
        JOIN financial_metrics roe ON s.stock_code = roe.stock_code
        JOIN financial_metrics pe ON s.stock_code = pe.stock_code
        WHERE roe.metric_name = 'roe' AND roe.year = ?
        AND pe.metric_name = 'pe' AND pe.year = ?
        AND roe.metric_value >= ?
        AND pe.metric_value <= ?
        AND pe.metric_value > 0
        ORDER BY roe.metric_value DESC, pe.metric_value ASC
        """
        result = pd.read_sql_query(query, conn, params=[year, year, min_roe, max_pe])
        conn.close()
        return result
    
    def find_dividend_stocks(self, min_dividend=3, year=2023):
        """查找高股息股票"""
        conn = self.connect()
        query = """
        SELECT s.stock_code, s.stock_name, s.industry, fm.metric_value as dividend_yield
        FROM stocks s
        JOIN financial_metrics fm ON s.stock_code = fm.stock_code
        WHERE fm.metric_name = 'dividend' 
        AND fm.year = ?
        AND fm.metric_value >= ?
        ORDER BY fm.metric_value DESC
        """
        result = pd.read_sql_query(query, conn, params=[year, min_dividend])
        conn.close()
        return result
    
    def get_stock_complete_data(self, stock_code):
        """获取单只股票的完整财务数据"""
        conn = self.connect()
        query = """
        SELECT s.stock_name, s.industry, fm.year, fm.metric_name, fm.metric_value
        FROM stocks s
        JOIN financial_metrics fm ON s.stock_code = fm.stock_code
        WHERE s.stock_code = ?
        ORDER BY fm.year DESC, fm.metric_name
        """
        result = pd.read_sql_query(query, conn, params=[stock_code])
        conn.close()
        return result
    
    def get_industry_analysis(self, industry_name, year=2023):
        """行业分析"""
        conn = self.connect()
        query = """
        SELECT s.stock_code, s.stock_name,
               roe.metric_value as roe,
               pe.metric_value as pe,
               dividend.metric_value as dividend_yield
        FROM stocks s
        LEFT JOIN financial_metrics roe ON s.stock_code = roe.stock_code 
            AND roe.metric_name = 'roe' AND roe.year = ?
        LEFT JOIN financial_metrics pe ON s.stock_code = pe.stock_code 
            AND pe.metric_name = 'pe' AND pe.year = ?
        LEFT JOIN financial_metrics dividend ON s.stock_code = dividend.stock_code 
            AND dividend.metric_name = 'dividend' AND dividend.year = ?
        WHERE s.industry = ?
        ORDER BY roe.metric_value DESC
        """
        result = pd.read_sql_query(query, conn, params=[year, year, year, industry_name])
        conn.close()
        return result
    
    def find_safe_stocks(self, max_debt_ratio=0.5, min_current_ratio=1.5, year=2023):
        """查找财务安全的股票（低负债率 + 高流动比率）"""
        conn = self.connect()
        query = """
        SELECT s.stock_code, s.stock_name, s.industry,
               debt.metric_value as debt_ratio,
               current.metric_value as current_ratio
        FROM stocks s
        JOIN financial_metrics debt ON s.stock_code = debt.stock_code
        JOIN financial_metrics current ON s.stock_code = current.stock_code
        WHERE debt.metric_name = 'debt_ratio' AND debt.year = ?
        AND current.metric_name = 'current_ratio' AND current.year = ?
        AND debt.metric_value <= ?
        AND current.metric_value >= ?
        ORDER BY debt.metric_value ASC, current.metric_value DESC
        """
        result = pd.read_sql_query(query, conn, params=[year, year, max_debt_ratio, min_current_ratio])
        conn.close()
        return result
    
    def find_undervalued_stocks(self, max_pb=2.0, max_pe=15, min_roe=10, year=2023):
        """查找低估值股票（低PB + 低PE + 合理ROE）"""
        conn = self.connect()
        query = """
        SELECT s.stock_code, s.stock_name, s.industry,
               roe.metric_value as roe,
               pe.metric_value as pe,
               pb.metric_value as pb
        FROM stocks s
        JOIN financial_metrics roe ON s.stock_code = roe.stock_code
        JOIN financial_metrics pe ON s.stock_code = pe.stock_code
        JOIN financial_metrics pb ON s.stock_code = pb.stock_code
        WHERE roe.metric_name = 'roe' AND roe.year = ?
        AND pe.metric_name = 'pe' AND pe.year = ?
        AND pb.metric_name = 'pb' AND pb.year = ?
        AND roe.metric_value >= ?
        AND pe.metric_value <= ? AND pe.metric_value > 0
        AND pb.metric_value <= ? AND pb.metric_value > 0
        ORDER BY pb.metric_value ASC, pe.metric_value ASC
        """
        result = pd.read_sql_query(query, conn, params=[year, year, year, min_roe, max_pe, max_pb])
        conn.close()
        return result
    
    def find_efficient_stocks(self, min_asset_turnover=0.5, min_ocf_ratio=0.8, year=2023):
        """查找运营高效股票（高资产周转率 + 高现金流质量）"""
        conn = self.connect()
        query = """
        SELECT s.stock_code, s.stock_name, s.industry,
               turnover.metric_value as asset_turnover,
               ocf.metric_value as ocf_to_profit
        FROM stocks s
        JOIN financial_metrics turnover ON s.stock_code = turnover.stock_code
        LEFT JOIN financial_metrics ocf ON s.stock_code = ocf.stock_code
        WHERE turnover.metric_name = 'asset_turnover' AND turnover.year = ?
        AND (ocf.metric_name = 'ocf_to_profit' AND ocf.year = ?) OR ocf.metric_name IS NULL
        AND turnover.metric_value >= ?
        AND (ocf.metric_value >= ? OR ocf.metric_value IS NULL)
        ORDER BY turnover.metric_value DESC
        """
        result = pd.read_sql_query(query, conn, params=[year, year, min_asset_turnover, min_ocf_ratio])
        conn.close()
        return result
    
    def comprehensive_screening(self, min_roe=15, max_pe=20, max_pb=3, max_debt=0.6, year=2023):
        """综合筛选优质股票"""
        conn = self.connect()
        query = """
        SELECT s.stock_code, s.stock_name, s.industry,
               roe.metric_value as roe,
               pe.metric_value as pe,
               pb.metric_value as pb,
               debt.metric_value as debt_ratio,
               dividend.metric_value as dividend_yield
        FROM stocks s
        JOIN financial_metrics roe ON s.stock_code = roe.stock_code
        JOIN financial_metrics pe ON s.stock_code = pe.stock_code
        JOIN financial_metrics pb ON s.stock_code = pb.stock_code
        JOIN financial_metrics debt ON s.stock_code = debt.stock_code
        LEFT JOIN financial_metrics dividend ON s.stock_code = dividend.stock_code 
            AND dividend.metric_name = 'dividend' AND dividend.year = ?
        WHERE roe.metric_name = 'roe' AND roe.year = ?
        AND pe.metric_name = 'pe' AND pe.year = ?
        AND pb.metric_name = 'pb' AND pb.year = ?
        AND debt.metric_name = 'debt_ratio' AND debt.year = ?
        AND roe.metric_value >= ?
        AND pe.metric_value <= ? AND pe.metric_value > 0
        AND pb.metric_value <= ? AND pb.metric_value > 0
        AND debt.metric_value <= ?
        ORDER BY roe.metric_value DESC, pe.metric_value ASC
        """
        result = pd.read_sql_query(query, conn, params=[year, year, year, year, year, min_roe, max_pe, max_pb, max_debt])
        conn.close()
        return result

def demo_queries():
    """演示查询功能"""
    helper = StockQueryHelper()
    
    print("=" * 60)
    print("A股基本面数据查询示例")
    print("=" * 60)
    
    # 检查可用数据
    print("\n📊 可用指标:")
    metrics = helper.get_available_metrics()
    print(f"  {', '.join(metrics)}")
    
    print("\n📅 可用年份:")
    years = helper.get_available_years()
    print(f"  {', '.join(map(str, years))}")
    
    # 示例查询1：高ROE股票
    print("\n🎯 高ROE股票 (ROE >= 20%, 2023年):")
    high_roe = helper.find_high_roe_stocks(min_roe=20, year=2023)
    if not high_roe.empty:
        print(high_roe.head(10).to_string(index=False))
    else:
        print("  暂无符合条件的股票")
    
    # 示例查询2：价值股票
    print("\n💎 价值股票 (ROE >= 15%, PE <= 15, 2023年):")
    value_stocks = helper.find_value_stocks(min_roe=15, max_pe=15, year=2023)
    if not value_stocks.empty:
        print(value_stocks.head(10).to_string(index=False))
    else:
        print("  暂无符合条件的股票")
    
    # 示例查询3：高股息股票
    print("\n💰 高股息股票 (股息率 >= 4%, 2023年):")
    dividend_stocks = helper.find_dividend_stocks(min_dividend=4, year=2023)
    if not dividend_stocks.empty:
        print(dividend_stocks.head(10).to_string(index=False))
    else:
        print("  暂无符合条件的股票")
    
    # 新增查询4：财务安全股票
    print("\n🛡️ 财务安全股票 (负债率 <= 50%, 流动比率 >= 1.5, 2023年):")
    safe_stocks = helper.find_safe_stocks(max_debt_ratio=0.5, min_current_ratio=1.5, year=2023)
    if not safe_stocks.empty:
        print(safe_stocks.head(10).to_string(index=False))
    else:
        print("  暂无符合条件的股票")
    
    # 新增查询5：低估值股票
    print("\n📉 低估值股票 (PB <= 2, PE <= 15, ROE >= 10%, 2023年):")
    undervalued = helper.find_undervalued_stocks(max_pb=2.0, max_pe=15, min_roe=10, year=2023)
    if not undervalued.empty:
        print(undervalued.head(10).to_string(index=False))
    else:
        print("  暂无符合条件的股票")
    
    # 新增查询6：运营高效股票
    print("\n⚡ 运营高效股票 (资产周转率 >= 0.5, 现金流质量 >= 0.8, 2023年):")
    efficient = helper.find_efficient_stocks(min_asset_turnover=0.5, min_ocf_ratio=0.8, year=2023)
    if not efficient.empty:
        print(efficient.head(10).to_string(index=False))
    else:
        print("  暂无符合条件的股票")
    
    # 新增查询7：综合优质股票
    print("\n🏆 综合优质股票 (ROE>=15%, PE<=20, PB<=3, 负债率<=60%, 2023年):")
    comprehensive = helper.comprehensive_screening(min_roe=15, max_pe=20, max_pb=3, max_debt=0.6, year=2023)
    if not comprehensive.empty:
        print(comprehensive.head(10).to_string(index=False))
    else:
        print("  暂无符合条件的股票")

if __name__ == "__main__":
    demo_queries() 