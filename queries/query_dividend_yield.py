#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计算和查询股息率排名的脚本
股息率 = 年度股息 / 股价 * 100%
"""

import sqlite3
import pandas as pd
import os

def calculate_dividend_yield():
    """计算股息率并排名"""
    # 获取脚本所在目录的上级目录（项目根目录）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    db_path = os.path.join(project_root, 'stock_analysis.db')
    
    conn = sqlite3.connect(db_path)
    
    # 由于我们没有直接的股价数据，我们先按股息绝对值和其他指标综合评估
    # 查询有股息数据的公司的综合财务指标
    
    query = '''
    SELECT 
        s.stock_code,
        s.stock_name,
        d.metric_value as dividend,
        pe.metric_value as pe_ratio,
        pb.metric_value as pb_ratio,
        roe.metric_value as roe,
        d.year,
        -- 简化的股息率估算：股息/PE比率 作为近似指标
        CASE 
            WHEN pe.metric_value > 0 AND pe.metric_value < 100 
            THEN (d.metric_value / pe.metric_value) * 100
            ELSE NULL 
        END as estimated_dividend_yield
    FROM financial_metrics d
    JOIN stocks s ON d.stock_code = s.stock_code
    LEFT JOIN financial_metrics pe ON d.stock_code = pe.stock_code 
        AND d.year = pe.year AND pe.metric_name = 'pe'
    LEFT JOIN financial_metrics pb ON d.stock_code = pb.stock_code 
        AND d.year = pb.year AND pb.metric_name = 'pb'
    LEFT JOIN financial_metrics roe ON d.stock_code = roe.stock_code 
        AND d.year = roe.year AND roe.metric_name = 'roe'
    WHERE d.metric_name = 'dividend' 
        AND d.metric_value > 0
        AND d.year = 2024
    ORDER BY estimated_dividend_yield DESC
    LIMIT 20;
    '''
    
    df = pd.read_sql_query(query, conn)
    
    print("🎯 2024年股息率排名前二十的公司:")
    print("=" * 100)
    print(f"{'排名':>4} | {'股票代码':>10} | {'股票名称':>12} | {'股息':>8} | {'估算股息率':>10} | {'PE':>6} | {'ROE':>6}")
    print("-" * 100)
    
    for i, row in df.iterrows():
        if pd.notna(row['estimated_dividend_yield']):
            print(f"{i+1:4d} | {row['stock_code']:>10} | {row['stock_name'] if row['stock_name'] else '未知':>12} | "
                  f"{row['dividend']:>8.2f} | {row['estimated_dividend_yield']:>9.2f}% | "
                  f"{row['pe_ratio']:>6.1f} | {row['roe']:>6.1f}")
    
    # 也按股息金额排序（作为参考）
    print("\n" + "=" * 100)
    print("🎯 2024年股息金额排名前十五（参考）:")
    print("=" * 80)
    
    query_dividend = '''
    SELECT 
        s.stock_code,
        s.stock_name,
        fm.metric_value as dividend,
        pe.metric_value as pe_ratio,
        roe.metric_value as roe
    FROM financial_metrics fm
    JOIN stocks s ON fm.stock_code = s.stock_code
    LEFT JOIN financial_metrics pe ON fm.stock_code = pe.stock_code 
        AND fm.year = pe.year AND pe.metric_name = 'pe'
    LEFT JOIN financial_metrics roe ON fm.stock_code = roe.stock_code 
        AND fm.year = roe.year AND roe.metric_name = 'roe'
    WHERE fm.metric_name = 'dividend' 
        AND fm.metric_value > 0 
        AND fm.year = 2024
    ORDER BY fm.metric_value DESC
    LIMIT 15;
    '''
    
    df_dividend = pd.read_sql_query(query_dividend, conn)
    
    print(f"{'排名':>4} | {'股票代码':>10} | {'股票名称':>12} | {'股息':>8} | {'PE':>6} | {'ROE':>6}")
    print("-" * 70)
    
    for i, row in df_dividend.iterrows():
        print(f"{i+1:4d} | {row['stock_code']:>10} | {row['stock_name'] if row['stock_name'] else '未知':>12} | "
              f"{row['dividend']:>8.2f} | {row['pe_ratio'] if pd.notna(row['pe_ratio']) else 'N/A':>6} | "
              f"{row['roe'] if pd.notna(row['roe']) else 'N/A':>6}")
    
    # 查找低PE高股息的股票（可能有高股息率）
    print("\n" + "=" * 100)
    print("🎯 低PE高股息股票（潜在高股息率）:")
    print("=" * 80)
    
    query_low_pe = '''
    SELECT 
        s.stock_code,
        s.stock_name,
        d.metric_value as dividend,
        pe.metric_value as pe_ratio,
        roe.metric_value as roe,
        (d.metric_value / pe.metric_value) * 100 as estimated_yield
    FROM financial_metrics d
    JOIN stocks s ON d.stock_code = s.stock_code
    JOIN financial_metrics pe ON d.stock_code = pe.stock_code 
        AND d.year = pe.year AND pe.metric_name = 'pe'
    LEFT JOIN financial_metrics roe ON d.stock_code = roe.stock_code 
        AND d.year = roe.year AND roe.metric_name = 'roe'
    WHERE d.metric_name = 'dividend' 
        AND d.metric_value > 2  -- 股息大于2元
        AND pe.metric_value > 0 
        AND pe.metric_value < 20  -- PE小于20
        AND d.year = 2024
    ORDER BY estimated_yield DESC
    LIMIT 10;
    '''
    
    df_low_pe = pd.read_sql_query(query_low_pe, conn)
    
    print(f"{'排名':>4} | {'股票代码':>10} | {'股票名称':>12} | {'股息':>8} | {'PE':>6} | {'估算收益率':>10}")
    print("-" * 75)
    
    for i, row in df_low_pe.iterrows():
        print(f"{i+1:4d} | {row['stock_code']:>10} | {row['stock_name'] if row['stock_name'] else '未知':>12} | "
              f"{row['dividend']:>8.2f} | {row['pe_ratio']:>6.1f} | {row['estimated_yield']:>9.2f}%")
    
    conn.close()

if __name__ == "__main__":
    calculate_dividend_yield() 