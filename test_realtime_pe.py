#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试实时PE功能
"""

from value_investment_agent import ValueInvestmentAgent
from loguru import logger

def test_realtime_pe():
    """测试实时PE获取功能"""
    
    agent = ValueInvestmentAgent()
    
    # 测试股票列表（几个知名股票）
    test_stocks = [
        '000001',  # 平安银行
        '000858',  # 五粮液
        '600036',  # 招商银行
        '600519',  # 贵州茅台
        '000002'   # 万科A
    ]
    
    print("🧪 测试实时PE获取功能")
    print("=" * 60)
    
    for stock_code in test_stocks:
        print(f"\n📊 测试股票: {stock_code}")
        
        # 测试初步筛选
        print("1️⃣ 初步筛选（不含PE）...")
        preliminary_result = agent.preliminary_screening(stock_code)
        
        if 'error' in preliminary_result:
            print(f"   ❌ 初步筛选失败: {preliminary_result['error']}")
            continue
        
        print(f"   ✅ {preliminary_result['stock_name']} - 初步得分: {preliminary_result['preliminary_score']:.1f}")
        
        # 测试最终评估（含实时PE）
        print("2️⃣ 最终评估（含实时PE）...")
        final_result = agent.comprehensive_evaluation(stock_code, use_realtime_pe=True)
        
        if 'error' in final_result:
            print(f"   ❌ 最终评估失败: {final_result['error']}")
            continue
        
        print(f"   ✅ {final_result['stock_name']} - 最终得分: {final_result['total_score']:.1f}")
        print(f"   📈 实时PE: {final_result.get('realtime_pe', 'N/A')}")
        print(f"   🔗 API使用: {'是' if final_result.get('pe_api_used') else '否'}")
        print(f"   🏆 评级: {final_result['grade']}")

def test_smart_screening():
    """测试智能筛选功能"""
    
    agent = ValueInvestmentAgent()
    
    print("\n🎯 测试智能筛选功能")
    print("=" * 60)
    
    # 小规模测试（限制5只股票）
    value_stocks = agent.screen_value_stocks(
        min_score=50,           # 降低最终分数要求
        preliminary_threshold=30, # 降低初步筛选阈值
        limit=5                 # 限制数量
    )
    
    if value_stocks:
        print(f"\n🌟 发现 {len(value_stocks)} 只价值股票:")
        print("-" * 80)
        
        for i, stock in enumerate(value_stocks, 1):
            pe_info = f"实时PE: {stock.get('realtime_pe'):.2f}" if stock.get('realtime_pe') else "历史PE"
            print(f"{i}. {stock['stock_name']} ({stock['stock_code']}) - "
                  f"得分: {stock['total_score']:.1f} - {pe_info}")
    else:
        print("😔 未发现符合条件的价值股票")

if __name__ == "__main__":
    # 测试单个股票功能
    test_realtime_pe()
    
    # 测试智能筛选功能
    test_smart_screening() 