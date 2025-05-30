#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询股息排名的脚本
"""

import sqlite3
import pandas as pd
import os

def query_dividend_ranking():
    """查询股息排名"""
    # 获取脚本所在目录的上级目录（项目根目录）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    db_path = os.path.join(project_root, 'stock_analysis.db')
    
    conn = sqlite3.connect(db_path)
    
    # 查询股息排名前20的公司
    query = '''
    SELECT 
        s.stock_code, 
        s.stock_name, 
        fm.metric_value as dividend, 
        fm.year 
    FROM financial_metrics fm 
    JOIN stocks s ON fm.stock_code = s.stock_code 
    WHERE fm.metric_name = "dividend" 
        AND fm.metric_value > 0 
    ORDER BY fm.metric_value DESC 
    LIMIT 20
    '''
    
    results = cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    
    print("🎯 股息排名前二十的公司:")
    print("=" * 80)
    print(f"{'排名':>4} | {'股票代码':>10} | {'股票名称':>12} | {'股息(元)':>10} | {'年份':>6}")
    print("-" * 80)
    
    for i, (code, name, dividend, year) in enumerate(results, 1):
        name = name if name else "未知公司"
        print(f"{i:4d} | {code:>10} | {name:>12} | {dividend:>10.3f} | {year:>6}")
    
    conn.close()
    
    # 也查询最新年份的股息排名
    print("\n" + "=" * 80)
    print("🎯 2024年股息排名前十的公司:")
    print("=" * 80)
    
    conn = sqlite3.connect(db_path)
    query_2024 = '''
    SELECT 
        s.stock_code, 
        s.stock_name, 
        fm.metric_value as dividend 
    FROM financial_metrics fm 
    JOIN stocks s ON fm.stock_code = s.stock_code 
    WHERE fm.metric_name = "dividend" 
        AND fm.metric_value > 0 
        AND fm.year = 2024
    ORDER BY fm.metric_value DESC 
    LIMIT 10
    '''
    
    cursor = conn.cursor()
    cursor.execute(query_2024)
    results_2024 = cursor.fetchall()
    
    print(f"{'排名':>4} | {'股票代码':>10} | {'股票名称':>12} | {'股息(元)':>10}")
    print("-" * 60)
    
    for i, (code, name, dividend) in enumerate(results_2024, 1):
        name = name if name else "未知公司"
        print(f"{i:4d} | {code:>10} | {name:>12} | {dividend:>10.3f}")
    
    conn.close()

if __name__ == "__main__":
    query_dividend_ranking() 