#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从缓存文件重新导入数据到SQLite数据库
清空现有数据并重新导入
"""

import json
import os
import sqlite3
import pandas as pd
from loguru import logger
from datetime import datetime

def setup_logger():
    """设置日志"""
    logger.add(
        "logs/cache_reimport_{time}.log",
        rotation="10 MB",
        encoding="utf-8"
    )

def clear_database(db_path='stock_analysis.db'):
    """清空数据库现有数据"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    logger.info("🗑️ 清空数据库现有数据...")
    
    # 删除所有数据
    cursor.execute('DELETE FROM financial_metrics')
    cursor.execute('DELETE FROM stocks')
    
    # 重置自增ID
    cursor.execute('DELETE FROM sqlite_sequence WHERE name="financial_metrics"')
    
    conn.commit()
    conn.close()
    
    logger.info("✅ 数据库已清空")

def process_cache_data(cache_data):
    """处理缓存数据，转换为标准格式"""
    results = []
    
    for stock_code, stock_info in cache_data.items():
        if not stock_info or 'data' not in stock_info:
            continue
            
        name = stock_info.get('name', '')
        industry = stock_info.get('industry', '')
        data = stock_info['data']
        
        # 基础信息
        row = {
            'stock_code': stock_code,
            'stock_name': name,
            'industry': industry
        }
        
        # 处理财务指标
        if 'financial_indicators' in data:
            for indicator in data['financial_indicators']:
                year = indicator.get('end_date', '')[:4]
                if year and year.isdigit():
                    year = int(year)
                    
                    # ROE
                    if indicator.get('roe') is not None:
                        row[f'roe_{year}'] = indicator['roe']
                    
                    # 毛利率
                    if indicator.get('grossprofit_margin') is not None:
                        row[f'gross_margin_{year}'] = indicator['grossprofit_margin']
                    
                    # 净利率
                    if indicator.get('netprofit_margin') is not None:
                        row[f'net_margin_{year}'] = indicator['netprofit_margin']
                    
                    # 资产负债率
                    if indicator.get('debt_to_assets') is not None:
                        row[f'debt_ratio_{year}'] = indicator['debt_to_assets'] / 100
                    
                    # 流动比率
                    if indicator.get('current_ratio') is not None:
                        row[f'current_ratio_{year}'] = indicator['current_ratio']
                    
                    # 资产周转率
                    if indicator.get('assets_turn') is not None:
                        row[f'asset_turnover_{year}'] = indicator['assets_turn']
        
        # 处理PE数据
        if 'pe' in data:
            for pe_record in data['pe']:
                year = pe_record.get('trade_date', '')[:4]
                if year and year.isdigit() and pe_record.get('pe') is not None:
                    row[f'pe_{year}'] = pe_record['pe']
        
        # 处理PB数据
        if 'pb' in data:
            for pb_record in data['pb']:
                year = pb_record.get('trade_date', '')[:4]
                if year and year.isdigit() and pb_record.get('pb') is not None:
                    row[f'pb_{year}'] = pb_record['pb']
        
        # 处理股息率数据
        if 'dividend' in data:
            for div_record in data['dividend']:
                year = div_record.get('trade_date', '')[:4]
                if year and year.isdigit() and div_record.get('dv_ratio') is not None:
                    row[f'dividend_{year}'] = div_record['dv_ratio']
        
        # 处理总资产数据
        if 'balance_sheet' in data:
            for bs_record in data['balance_sheet']:
                year = bs_record.get('end_date', '')[:4]
                if year and year.isdigit() and bs_record.get('total_assets') is not None:
                    row[f'total_assets_{year}'] = bs_record['total_assets']
        
        results.append(row)
    
    return results

def save_to_sqlite(data, db_path='stock_analysis.db'):
    """保存数据到SQLite数据库"""
    conn = sqlite3.connect(db_path)
    
    for _, row in data.iterrows():
        # 插入股票基本信息
        conn.execute('''
            INSERT OR REPLACE INTO stocks (stock_code, stock_name, industry)
            VALUES (?, ?, ?)
        ''', (row['stock_code'], row['stock_name'], row['industry']))
        
        # 插入财务指标数据
        for col in row.index:
            if col in ['stock_code', 'stock_name', 'industry']:
                continue
                
            # 解析指标名称和年份
            if '_' in col:
                parts = col.split('_')
                if len(parts) >= 2:
                    metric_name = '_'.join(parts[:-1])
                    year = parts[-1]
                    
                    if pd.notna(row[col]) and year.isdigit():
                        conn.execute('''
                            INSERT OR REPLACE INTO financial_metrics 
                            (stock_code, year, metric_name, metric_value)
                            VALUES (?, ?, ?, ?)
                        ''', (row['stock_code'], int(year), metric_name, float(row[col])))
    
    conn.commit()
    conn.close()

def create_sqlite_database(db_path='stock_analysis.db'):
    """创建SQLite数据库和表结构"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建股票基本信息表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            stock_code TEXT PRIMARY KEY,
            stock_name TEXT,
            industry TEXT,
            list_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建财务指标表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financial_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT,
            year INTEGER,
            metric_name TEXT,
            metric_value REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stock_code) REFERENCES stocks (stock_code)
        )
    ''')
    
    # 创建索引
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_stock_year 
        ON financial_metrics (stock_code, year)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_metric_name 
        ON financial_metrics (metric_name)
    ''')
    
    conn.commit()
    conn.close()

def main():
    """主程序"""
    setup_logger()
    
    logger.info("🚀 开始重新导入缓存数据到数据库...")
    
    # 创建数据库
    create_sqlite_database()
    
    # 清空现有数据
    clear_database()
    
    cache_dir = 'cache'
    all_results = []
    
    logger.info("🔄 开始从缓存文件导入数据...")
    
    # 处理所有批次缓存文件
    batch_files = sorted([f for f in os.listdir(cache_dir) if f.startswith('batch_') and f.endswith('.json')])
    
    if not batch_files:
        logger.error("❌ 未找到任何缓存文件!")
        print("\n😔 未找到任何缓存文件，请先运行 collect_data.py 收集数据")
        return
    
    logger.info(f"📦 找到 {len(batch_files)} 个批次缓存文件")
    
    for batch_file in batch_files:
        batch_path = os.path.join(cache_dir, batch_file)
        batch_num = batch_file.replace('batch_', '').replace('.json', '')
        
        logger.info(f"📦 处理批次 {batch_num}: {batch_file}")
        
        try:
            with open(batch_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 处理缓存数据
            batch_results = process_cache_data(cache_data)
            
            if batch_results:
                # 转换为DataFrame并保存到数据库
                batch_df = pd.DataFrame(batch_results)
                save_to_sqlite(batch_df)
                
                all_results.extend(batch_results)
                
                logger.info(f"✅ 批次 {batch_num}: 成功导入 {len(batch_results)} 只股票")
            else:
                logger.warning(f"⚠️ 批次 {batch_num}: 没有有效数据")
                
        except Exception as e:
            logger.error(f"❌ 处理批次 {batch_num} 失败: {e}")
    
    # 统计信息
    if all_results:
        logger.info(f"🎯 重新导入完成!")
        logger.info(f"  • 总共处理了 {len(batch_files)} 个批次")
        logger.info(f"  • 成功导入 {len(all_results)} 只股票")
        
        # 检查数据库状态
        conn = sqlite3.connect('stock_analysis.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM stocks')
        stock_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM financial_metrics')
        metrics_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT stock_code) FROM financial_metrics')
        stocks_with_data = cursor.fetchone()[0]
        
        # 检查是否有重复数据
        cursor.execute('''
            SELECT stock_code, year, metric_name, COUNT(*) as cnt
            FROM financial_metrics 
            GROUP BY stock_code, year, metric_name 
            HAVING COUNT(*) > 1
            LIMIT 5
        ''')
        duplicates = cursor.fetchall()
        
        conn.close()
        
        logger.info(f"📊 数据库统计:")
        logger.info(f"  • 股票总数: {stock_count}")
        logger.info(f"  • 有财务数据的股票: {stocks_with_data}")
        logger.info(f"  • 财务指标记录数: {metrics_count}")
        
        if duplicates:
            logger.warning(f"⚠️ 发现 {len(duplicates)} 组重复数据")
            for dup in duplicates:
                logger.warning(f"  重复: {dup[0]} {dup[1]}年 {dup[2]} (x{dup[3]})")
        else:
            logger.info("✅ 未发现重复数据")
        
        print(f"\n🎉 缓存数据重新导入成功!")
        print(f"📈 数据库中现在有 {stocks_with_data} 只股票的财务数据")
        print(f"📊 总共 {metrics_count} 条财务指标记录")
        
        if duplicates:
            print(f"⚠️ 注意：发现 {len(duplicates)} 组重复数据，建议检查")
        else:
            print("✅ 数据没有重复，导入干净!")
        
    else:
        logger.warning("😔 没有找到有效的缓存数据")

if __name__ == "__main__":
    main() 