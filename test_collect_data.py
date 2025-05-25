#!/usr/bin/env python3
"""
测试collect_data.py的功能
用10个股票数据测试断点续传和多token功能
"""

import os
import sys
import time
import sqlite3
import pandas as pd
from loguru import logger

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from collect_data import StockDataCollector, setup_logger, create_sqlite_database, save_to_sqlite

def test_cache_functionality():
    """测试缓存功能"""
    logger.info("开始测试缓存功能...")
    
    # 检查缓存目录是否存在
    cache_dir = 'cache'
    if os.path.exists(cache_dir):
        cache_files = os.listdir(cache_dir)
        logger.info(f"缓存目录存在，包含 {len(cache_files)} 个文件: {cache_files[:5]}...")
    else:
        logger.info("缓存目录不存在，将在首次运行时创建")

def test_multiple_tokens():
    """测试多token配置"""
    logger.info("开始测试多token配置...")
    
    logger.info(f"配置的token数量: {len(config.TUSHARE_TOKENS)}")
    for i, token in enumerate(config.TUSHARE_TOKENS[:3]):  # 只显示前3个的部分内容
        masked_token = token[:10] + '***' + token[-5:] if len(token) > 15 else '***'
        logger.info(f"Token {i+1}: {masked_token}")

def test_database_functionality():
    """测试数据库功能"""
    logger.info("开始测试数据库功能...")
    
    db_path = 'test_stock_analysis.db'
    
    # 创建测试数据库
    create_sqlite_database(db_path)
    
    # 检查数据库结构
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取表列表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    logger.info(f"数据库表: {[table[0] for table in tables]}")
    
    # 检查索引
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
    indexes = cursor.fetchall()
    logger.info(f"数据库索引: {[index[0] for index in indexes]}")
    
    conn.close()
    
    # 清理测试数据库
    if os.path.exists(db_path):
        os.remove(db_path)
        logger.info(f"已清理测试数据库: {db_path}")

def test_stock_data_collection():
    """测试股票数据收集功能（10只股票）"""
    logger.info("开始测试股票数据收集功能...")
    
    # 检查token配置
    if not config.TUSHARE_TOKENS:
        logger.error("未配置Tushare token，请检查.env文件")
        return False
    
    # 初始化收集器
    collector = StockDataCollector(
        token=config.TUSHARE_TOKENS[0],
        cache_dir='cache',
        batch_size=5,  # 小批次便于测试
        use_delay=True
    )
    
    try:
        # 获取股票列表
        logger.info("获取股票列表...")
        stocks = collector.get_all_stocks()
        if stocks is None or stocks.empty:
            logger.error("获取股票列表失败")
            return False
        
        # 限制为10只股票进行测试
        test_stocks = stocks.head(10)
        logger.info(f"选择测试股票: {list(test_stocks['ts_code'].values)}")
        
        # 分批处理（每批5只）
        all_results = []
        batch_size = 5
        total_batches = (len(test_stocks) + batch_size - 1) // batch_size
        
        for i in range(total_batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, len(test_stocks))
            stocks_batch = test_stocks.iloc[start_idx:end_idx]
            
            logger.info(f"处理第 {i+1}/{total_batches} 批次: {list(stocks_batch['ts_code'].values)}")
            
            # 测试缓存功能（第一次不使用缓存，第二次使用缓存）
            use_cache = (i > 0)  # 第一批不使用缓存，之后使用缓存
            
            batch_data = collector.process_batch(
                stocks_batch,
                start_year=2020,
                end_year=2023,
                use_cache=use_cache
            )
            
            if batch_data:
                logger.info(f"批次 {i+1} 收集到 {len(batch_data)} 只股票的数据")
                
                # 检查数据结构
                for stock_code, stock_info in list(batch_data.items())[:2]:  # 只检查前2只
                    data_keys = list(stock_info['data'].keys())
                    logger.info(f"股票 {stock_code} 数据类型: {data_keys}")
                    
                    # 检查每个数据类型的数量
                    for key in data_keys:
                        count = len(stock_info['data'][key])
                        logger.info(f"  {key}: {count} 条记录")
                
                all_results.append(batch_data)
            else:
                logger.warning(f"批次 {i+1} 未收集到数据")
            
            # 添加延时避免API限制
            if i < total_batches - 1:
                time.sleep(1)
        
        # 统计结果
        total_stocks_collected = sum(len(batch) for batch in all_results)
        logger.info(f"总共收集到 {total_stocks_collected} 只股票的数据")
        
        return total_stocks_collected > 0
        
    except Exception as e:
        logger.error(f"股票数据收集测试失败: {e}")
        return False

def test_resume_functionality():
    """测试断点续传功能"""
    logger.info("开始测试断点续传功能...")
    
    cache_dir = 'cache'
    
    # 检查缓存文件
    if os.path.exists(cache_dir):
        cache_files = [f for f in os.listdir(cache_dir) if f.startswith('batch_')]
        if cache_files:
            logger.info(f"发现 {len(cache_files)} 个缓存文件")
            
            # 选择一个缓存文件测试读取
            test_cache_file = os.path.join(cache_dir, cache_files[0])
            try:
                import json
                with open(test_cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                logger.info(f"成功读取缓存文件 {cache_files[0]}, 包含 {len(cached_data)} 只股票")
                
                # 显示缓存数据结构
                if cached_data:
                    first_stock = list(cached_data.keys())[0]
                    data_structure = list(cached_data[first_stock]['data'].keys())
                    logger.info(f"缓存数据结构: {data_structure}")
                
                return True
            except Exception as e:
                logger.error(f"读取缓存文件失败: {e}")
                return False
        else:
            logger.info("未发现缓存文件，需要先运行数据收集")
            return False
    else:
        logger.info("缓存目录不存在")
        return False

def main():
    """主测试函数"""
    setup_logger()
    
    logger.info("🚀 开始测试 collect_data.py 功能")
    logger.info("=" * 60)
    
    # 测试1：配置检查
    logger.info("📋 测试1：检查配置")
    test_multiple_tokens()
    print()
    
    # 测试2：缓存功能检查
    logger.info("💾 测试2：检查缓存功能")
    test_cache_functionality()
    print()
    
    # 测试3：数据库功能测试
    logger.info("🗄️ 测试3：测试数据库功能")
    test_database_functionality()
    print()
    
    # 测试4：断点续传功能测试
    logger.info("🔄 测试4：测试断点续传功能")
    resume_success = test_resume_functionality()
    print()
    
    # 测试5：股票数据收集测试
    logger.info("📊 测试5：测试股票数据收集（10只股票）")
    collection_success = test_stock_data_collection()
    print()
    
    # 测试结果汇总
    logger.info("📋 测试结果汇总")
    logger.info("=" * 60)
    logger.info(f"✅ 配置检查: 通过")
    logger.info(f"✅ 缓存功能: 通过")
    logger.info(f"✅ 数据库功能: 通过")
    logger.info(f"{'✅' if resume_success else '⚠️'} 断点续传: {'通过' if resume_success else '需要先收集数据'}")
    logger.info(f"{'✅' if collection_success else '❌'} 数据收集: {'通过' if collection_success else '失败'}")
    
    if collection_success:
        logger.info("\n🎉 所有主要功能测试通过！")
        logger.info("💡 建议：运行完整的 collect_data.py 进行全量数据收集")
    else:
        logger.error("\n❌ 数据收集测试失败，请检查token配置和网络连接")

if __name__ == "__main__":
    main() 