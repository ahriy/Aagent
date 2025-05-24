import tushare as ts
import pandas as pd
import numpy as np
from loguru import logger
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.font_manager import FontProperties
from config import TUSHARE_TOKEN, ANALYSIS_INDICATORS, THRESHOLDS, REPORT_SAVE_PATH

# 设置中文字体
try:
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
    plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
except:
    logger.warning("无法设置中文字体，图表中的中文可能无法正常显示")

class StockAnalyzer:
    def __init__(self):
        # 初始化Tushare
        ts.set_token(TUSHARE_TOKEN)
        self.pro = ts.pro_api()
        
        # 创建报告目录
        os.makedirs(REPORT_SAVE_PATH, exist_ok=True)
        
    def get_stock_info(self, stock_code):
        """获取股票基本信息"""
        try:
            stock_info = self.pro.stock_basic(ts_code=stock_code)
            return stock_info.iloc[0] if not stock_info.empty else None
        except Exception as e:
            logger.error(f"获取股票信息失败: {e}")
            return None

    def get_financial_data(self, stock_code, start_date, end_date):
        """获取财务数据"""
        try:
            # 获取资产负债表
            balance_sheet = self.pro.balancesheet(
                ts_code=stock_code,
                start_date=start_date,
                end_date=end_date
            )
            
            # 获取利润表
            income = self.pro.income(
                ts_code=stock_code,
                start_date=start_date,
                end_date=end_date
            )
            
            # 获取现金流量表
            cashflow = self.pro.cashflow(
                ts_code=stock_code,
                start_date=start_date,
                end_date=end_date
            )
            
            return balance_sheet, income, cashflow
        except Exception as e:
            logger.error(f"获取财务数据失败: {e}")
            return None, None, None

    def calculate_financial_ratios(self, balance_sheet, income):
        """计算财务比率"""
        if balance_sheet is None or income is None:
            return None
            
        # 确保使用报告期作为索引，并处理重复值
        balance_sheet = balance_sheet.sort_values('end_date').drop_duplicates('end_date', keep='last')
        income = income.sort_values('end_date').drop_duplicates('end_date', keep='last')
        
        balance_sheet = balance_sheet.set_index('end_date')
        income = income.set_index('end_date')
        
        # 确保两个数据框的索引一致
        common_dates = balance_sheet.index.intersection(income.index)
        balance_sheet = balance_sheet.loc[common_dates]
        income = income.loc[common_dates]
        
        ratios = pd.DataFrame(index=common_dates)
        
        # ROE = 净利润 / 股东权益
        ratios['roe'] = income['n_income'] / balance_sheet['total_hldr_eqy_exc_min_int'] * 100
        
        # ROA = 净利润 / 总资产
        ratios['roa'] = income['n_income'] / balance_sheet['total_assets'] * 100
        
        # 毛利率 = （营业收入 - 营业成本）/ 营业收入
        ratios['gross_profit_margin'] = (income['revenue'] - income['oper_cost']) / income['revenue'] * 100
        
        # 净利率 = 净利润 / 营业收入
        ratios['net_profit_margin'] = income['n_income'] / income['revenue'] * 100
        
        # 资产负债率 = 总负债 / 总资产
        ratios['debt_to_assets'] = balance_sheet['total_liab'] / balance_sheet['total_assets'] * 100
        
        # 按时间排序
        ratios = ratios.sort_index()
        return ratios

    def analyze_growth(self, income, periods=5):
        """分析增长性"""
        if income is None or income.empty:
            return None
            
        # 处理重复的报告期
        income = income.sort_values('end_date').drop_duplicates('end_date', keep='last')
        income = income.set_index('end_date')
        
        growth = pd.DataFrame(index=income.index)
        
        # 计算营收增长率
        revenue = income['revenue']
        growth['revenue_growth'] = revenue.pct_change() * 100
        
        # 计算净利润增长率
        net_income = income['n_income']
        growth['profit_growth'] = net_income.pct_change() * 100
        
        # 按时间排序
        growth = growth.sort_index()
        return growth

    def generate_report(self, stock_code, ratios, growth):
        """生成分析报告"""
        if ratios is None or growth is None:
            return
            
        report = []
        report.append(f"# {stock_code} 基本面分析报告")
        report.append(f"\n## 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 财务比率分析
        report.append("\n## 财务比率分析")
        for indicator in ANALYSIS_INDICATORS:
            if indicator in ratios.columns:
                latest_value = ratios[indicator].iloc[-1]
                threshold = THRESHOLDS.get(indicator)
                if pd.notna(latest_value) and threshold is not None:
                    status = "高于" if latest_value > threshold else "低于"
                    report.append(f"\n- {indicator}: {latest_value:.2f}% {status}基准线({threshold}%)")
                else:
                    report.append(f"\n- {indicator}: {latest_value:.2f}% (无基准线)")
        
        # 增长性分析
        report.append("\n## 增长性分析")
        if not growth.empty:
            avg_revenue_growth = growth['revenue_growth'].mean()
            avg_profit_growth = growth['profit_growth'].mean()
            if pd.notna(avg_revenue_growth):
                report.append(f"\n- 平均营收增长率: {avg_revenue_growth:.2f}%")
            if pd.notna(avg_profit_growth):
                report.append(f"\n- 平均利润增长率: {avg_profit_growth:.2f}%")
        
        # 保存报告
        report_path = os.path.join(REPORT_SAVE_PATH, f"{stock_code}_analysis_{datetime.now().strftime('%Y%m%d')}.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        return report_path

    def plot_financial_trends(self, stock_code, ratios, growth):
        """绘制财务趋势图"""
        if ratios is None or growth is None:
            return
            
        plt.figure(figsize=(15, 10))
        
        # 绘制财务比率趋势
        plt.subplot(2, 1, 1)
        for col in ratios.columns:
            plt.plot(pd.to_datetime(ratios.index), ratios[col], label=col, marker='o')
        plt.title('财务比率趋势')
        plt.xlabel('报告期')
        plt.ylabel('比率 (%)')
        plt.legend(loc='best')
        plt.grid(True)
        plt.xticks(rotation=45)
        
        # 绘制增长率趋势
        plt.subplot(2, 1, 2)
        for col in growth.columns:
            plt.plot(pd.to_datetime(growth.index), growth[col], label=col, marker='o')
        plt.title('增长率趋势')
        plt.xlabel('报告期')
        plt.ylabel('增长率 (%)')
        plt.legend(loc='best')
        plt.grid(True)
        plt.xticks(rotation=45)
        
        # 调整布局，防止标签重叠
        plt.tight_layout()
        
        # 保存图表
        plot_path = os.path.join(REPORT_SAVE_PATH, f"{stock_code}_trends_{datetime.now().strftime('%Y%m%d')}.png")
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return plot_path 