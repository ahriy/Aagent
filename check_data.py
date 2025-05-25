import pandas as pd
import numpy as np

def check_value_investing_indicators():
    """系统性检查价值投资指标"""
    try:
        df = pd.read_excel('stock_analysis_data.xlsx')
        print('📊 价值投资指标数据检查报告')
        print('=' * 60)
        print(f'数据概况: {df.shape[0]}只股票, {df.shape[1]}个指标列')
        
        # 显示股票基本信息
        print('\n🏢 股票基本信息:')
        for i, row in df.iterrows():
            status = "✅需要分析" if row['need_analysis'] else "⏸️跳过分析"
            print(f'  {row["stock_code"]} - {row["stock_name"]} ({row["industry"]}) - {status}')
        
        # 1. 检查ROE数据（价值投资核心指标）
        roe_cols = [col for col in df.columns if col.startswith('roe_')]
        print(f'\n🎯 ROE指标 ({len(roe_cols)}年):')
        print('  年份:', [col.split('_')[1] for col in sorted(roe_cols)])
        
        roe_data = df[roe_cols]
        print(f'  数据完整性: {roe_data.notna().sum().sum()}/{len(roe_cols)*len(df)} 个数据点')
        print(f'  平均ROE: {roe_data.mean().mean():.2f}%')
        print(f'  ROE > 15%的数据点: {(roe_data > 15).sum().sum()}个')
        
        # 2. 检查PE数据（估值指标）
        pe_cols = [col for col in df.columns if col.startswith('pe_')]
        print(f'\n💰 PE指标 ({len(pe_cols)}年):')
        pe_data = df[pe_cols]
        print(f'  数据完整性: {pe_data.notna().sum().sum()}/{len(pe_cols)*len(df)} 个数据点')
        print(f'  平均PE: {pe_data.mean().mean():.2f}倍')
        print(f'  PE < 20的数据点: {(pe_data < 20).sum().sum()}个')
        print(f'  异常高PE (>100): {(pe_data > 100).sum().sum()}个')
        
        # 3. 检查PB数据（账面价值指标）
        pb_cols = [col for col in df.columns if col.startswith('pb_')]
        print(f'\n📈 PB指标 ({len(pb_cols)}年):')
        pb_data = df[pb_cols]
        print(f'  数据完整性: {pb_data.notna().sum().sum()}/{len(pb_cols)*len(df)} 个数据点')
        print(f'  平均PB: {pb_data.mean().mean():.2f}倍')
        print(f'  PB < 2的数据点: {(pb_data < 2).sum().sum()}个')
        
        # 4. 检查股息率数据（收益指标）
        div_cols = [col for col in df.columns if col.startswith('dividend_')]
        print(f'\n💵 股息率指标 ({len(div_cols)}年):')
        div_data = df[div_cols]
        print(f'  数据完整性: {div_data.notna().sum().sum()}/{len(div_cols)*len(df)} 个数据点')
        print(f'  平均股息率: {div_data.mean().mean():.2f}%')
        print(f'  高股息率 (>3%): {(div_data > 3).sum().sum()}个')
        
        # 5. 检查盈利能力指标
        print(f'\n🏆 盈利能力指标:')
        net_margin_cols = [col for col in df.columns if col.startswith('net_margin_')]
        gross_margin_cols = [col for col in df.columns if col.startswith('gross_margin_')]
        
        net_data = df[net_margin_cols]
        gross_data = df[gross_margin_cols]
        
        print(f'  净利率: {len(net_margin_cols)}年数据')
        print(f'    数据完整性: {net_data.notna().sum().sum()}/{len(net_margin_cols)*len(df)}')
        print(f'    平均净利率: {net_data.mean().mean():.2f}%')
        print(f'    净利率>10%: {(net_data > 10).sum().sum()}个')
        
        print(f'  毛利率: {len(gross_margin_cols)}年数据')
        print(f'    数据完整性: {gross_data.notna().sum().sum()}/{len(gross_margin_cols)*len(df)}')
        print(f'    平均毛利率: {gross_data.mean().mean():.2f}%')
        print(f'    毛利率>30%: {(gross_data > 30).sum().sum()}个')
        
        # 6. 检查财务安全性指标
        print(f'\n🛡️ 财务安全性指标:')
        debt_cols = [col for col in df.columns if col.startswith('debt_ratio_')]
        current_cols = [col for col in df.columns if col.startswith('current_ratio_')]
        
        debt_data = df[debt_cols]
        current_data = df[current_cols]
        
        print(f'  资产负债率: {len(debt_cols)}年数据')
        print(f'    平均负债率: {debt_data.mean().mean():.2f}%')
        print(f'    低负债率(<50%): {(debt_data < 50).sum().sum()}个')
        
        print(f'  流动比率: {len(current_cols)}年数据')
        print(f'    平均流动比率: {current_data.mean().mean():.2f}')
        print(f'    良好流动性(>2): {(current_data > 2).sum().sum()}个')
        
        # 7. 现金流质量指标
        ocf_cols = [col for col in df.columns if col.startswith('ocf_to_profit_')]
        print(f'\n💧 现金流质量指标: {len(ocf_cols)}年数据')
        if ocf_cols:
            ocf_data = df[ocf_cols]
            print(f'  数据完整性: {ocf_data.notna().sum().sum()}/{len(ocf_cols)*len(df)}')
            valid_ocf = ocf_data.dropna()
            if not valid_ocf.empty:
                print(f'  平均现金流/净利润: {valid_ocf.mean().mean():.2f}')
                print(f'  优质现金流(>1): {(ocf_data > 1).sum().sum()}个')
        
        # 8. 年度数据覆盖检查
        print(f'\n📅 时间覆盖度分析:')
        years = set()
        for col in df.columns:
            if '_' in col and col.split('_')[-1].isdigit():
                years.add(col.split('_')[-1])
        
        years = sorted(years)
        print(f'  覆盖年份: {years}')
        print(f'  数据跨度: {len(years)}年 ({years[0]}-{years[-1]})')
        
        # 9. 优秀股票识别
        print(f'\n⭐ 基于指标的优秀股票识别:')
        
        # 计算最新年份的关键指标
        latest_year = max(years)
        excellent_stocks = []
        
        for i, row in df.iterrows():
            score = 0
            reasons = []
            
            # ROE > 15%
            latest_roe = row.get(f'roe_{latest_year}')
            if pd.notna(latest_roe) and latest_roe > 15:
                score += 20
                reasons.append(f'ROE {latest_roe:.1f}%')
            
            # PE < 20
            latest_pe = row.get(f'pe_{latest_year}')
            if pd.notna(latest_pe) and 5 < latest_pe < 20:
                score += 20
                reasons.append(f'PE {latest_pe:.1f}倍')
            
            # PB < 2
            latest_pb = row.get(f'pb_{latest_year}')
            if pd.notna(latest_pb) and latest_pb < 2:
                score += 15
                reasons.append(f'PB {latest_pb:.1f}倍')
            
            # 股息率 > 3%
            latest_div = row.get(f'dividend_{latest_year}')
            if pd.notna(latest_div) and latest_div > 3:
                score += 15
                reasons.append(f'股息率 {latest_div:.1f}%')
            
            # 净利率 > 10%
            latest_net_margin = row.get(f'net_margin_{latest_year}')
            if pd.notna(latest_net_margin) and latest_net_margin > 10:
                score += 15
                reasons.append(f'净利率 {latest_net_margin:.1f}%')
            
            # 负债率 < 50%
            latest_debt = row.get(f'debt_ratio_{latest_year}')
            if pd.notna(latest_debt) and latest_debt < 50:
                score += 15
                reasons.append(f'负债率 {latest_debt:.1f}%')
            
            if score >= 60:  # 60分以上认为是优秀股票
                excellent_stocks.append({
                    'code': row['stock_code'],
                    'name': row['stock_name'],
                    'industry': row['industry'],
                    'score': score,
                    'reasons': reasons
                })
        
        excellent_stocks.sort(key=lambda x: x['score'], reverse=True)
        
        if excellent_stocks:
            print(f'  发现 {len(excellent_stocks)} 只优秀股票:')
            for stock in excellent_stocks:
                print(f'    {stock["code"]} - {stock["name"]} ({stock["industry"]})')
                print(f'      综合评分: {stock["score"]}/100')
                print(f'      优势指标: {", ".join(stock["reasons"])}')
        else:
            print('  未发现符合标准的优秀股票')
        
        print(f'\n✅ 数据检查完成!')
        return True
        
    except Exception as e:
        print(f'❌ 数据检查失败: {e}')
        return False

if __name__ == "__main__":
    check_value_investing_indicators() 