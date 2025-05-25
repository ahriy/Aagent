#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股基本面分析Agent - 主程序
使用collect_data.py进行数据收集
"""

import os
import subprocess
import sys
from datetime import datetime
from config import TUSHARE_TOKENS

def print_banner():
    """打印程序横幅"""
    print("=" * 80)
    print("🚀 A股基本面分析Agent")
    print("=" * 80)
    print(f"🔧 Token数量: {len(TUSHARE_TOKENS)}")
    print(f"⏱️  启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

def check_environment():
    """检查运行环境"""
    print("\n🔍 检查运行环境...")
    
    # 检查Token配置
    if not TUSHARE_TOKENS:
        print("❌ 错误: 未配置Tushare Token")
        print("请在.env文件中配置:")
        print("  TUSHARE_TOKENS=token1,token2,token3  # 多个token用逗号分隔")
        print("  或")
        print("  TUSHARE_TOKEN=single_token           # 单个token")
        return False
    
    print(f"✅ Token配置: {len(TUSHARE_TOKENS)} 个")
    
    # 检查必要的库
    try:
        import tushare as ts
        import pandas as pd
        import sqlite3
        print("✅ 依赖库检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖库: {e}")
        return False
    
    # 检查数据目录
    cache_dir = 'cache'
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
        print(f"✅ 创建缓存目录: {cache_dir}")
    else:
        print(f"✅ 缓存目录存在: {cache_dir}")
    
    return True

def main():
    """主函数"""
    print_banner()
    
    # 检查环境
    if not check_environment():
        print("\n❌ 环境检查失败，程序退出")
        return
    
    print("\n💡 使用说明:")
    print("本程序使用 collect_data.py 进行数据收集")
    print("支持以下功能:")
    print("  🔄 断点续传 - 程序中断后可继续")
    print("  📊 Excel优化 - 自动生成多种分析视图")
    print("  🗄️  SQLite存储 - 支持复杂数据查询")
    print("  🧠 智能过滤 - 自动跳过连续亏损股票")
    
    print("\n🚀 推荐使用方式:")
    print("  测试: python collect_data.py --limit 10 --start-year 2023 --end-year 2024")
    print("  生产: python collect_data.py --start-year 2020 --end-year 2024")
    
    # 获取用户选择
    print("\n请选择操作:")
    print("  1. 运行完整数据收集 (2020-2024)")
    print("  2. 运行测试收集 (10只股票)")
    print("  3. 自定义参数")
    print("  4. 退出")
    
    try:
        choice = input("\n请选择 (1-4): ").strip()
        
        if choice == "1":
            print("\n🚀 启动完整数据收集...")
            cmd = ["python", "collect_data.py", "--start-year", "2020", "--end-year", "2024"]
            subprocess.run(cmd)
            
        elif choice == "2":
            print("\n🧪 启动测试数据收集...")
            cmd = ["python", "collect_data.py", "--limit", "10", "--start-year", "2023", "--end-year", "2024"]
            subprocess.run(cmd)
            
        elif choice == "3":
            print("\n⚙️ 自定义参数模式")
            print("请直接运行: python collect_data.py --help 查看所有参数")
            
        elif choice == "4":
            print("\n👋 再见!")
            
        else:
            print("\n❌ 无效选择，请重新运行")
            
    except KeyboardInterrupt:
        print("\n⚠️  程序被用户中断")
        
    except Exception as e:
        print(f"\n❌ 程序执行失败: {e}")

if __name__ == "__main__":
    main() 