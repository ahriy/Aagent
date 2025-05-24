import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger
import os
import json
import time
from tqdm import tqdm
from dotenv import load_dotenv
import argparse
import math
import numpy as np
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment
import config

def check_environment():
    """检查环境变量是否正确设置"""
    load_dotenv()
    tushare_token = os.getenv('TUSHARE_TOKEN')
    if not tushare_token:
        raise ValueError("请在 .env 文件中设置 TUSHARE_TOKEN")
    return tushare_token

class StockDataCollector:
    def __init__(self, token, cache_dir='cache', batch_size=50):
        # 初始化Tushare
        ts.set_token(token)
        self.pro = ts.pro_api()
        logger.info("Tushare API 初始化成功")
        
        # 创建缓存目录
        self.cache_dir = cache_dir
        self.batch_size = batch_size
        os.makedirs(cache_dir, exist_ok=True)
        
    def _get_batch_cache_path(self, batch_index):
        """获取批次缓存文件路径"""
        return os.path.join(self.cache_dir, f"batch_{batch_index}.json")
        
    def _save_batch_to_cache(self, batch_data, batch_index):
        """保存批次数据到缓存"""
        if not batch_data:
            return
            
        cache_path = self._get_batch_cache_path(batch_index)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(batch_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存批次缓存失败 {cache_path}: {e}")
            
    def _load_batch_from_cache(self, batch_index):
        """从缓存加载批次数据"""
        cache_path = self._get_batch_cache_path(batch_index)
        if not os.path.exists(cache_path):
            return None
            
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"读取批次缓存失败 {cache_path}: {e}")
            return None

    def get_all_stocks(self):
        """获取所有A股上市公司列表"""
        try:
            # 从API获取数据
            stocks = self.pro.stock_basic(exchange='', list_status='L')
            return stocks[['ts_code', 'name', 'industry']]
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return None

    def get_annual_data(self, stock_code, start_year, end_year):
        """获取单个股票的年度数据"""
        try:
            # 构建年份范围（排除当前年份，只获取完整年份的数据）
            current_year = datetime.now().year
            actual_end_year = min(end_year, current_year - 1)  # 不包含当前年份
            years = range(start_year, actual_end_year + 1)
            
            data = {
                'financial_indicators': [],
                'dividend': [],
                'pe': []
            }
            
            # 获取每年的年报财务指标
            for year in years:
                # 获取年报财务指标（使用年末日期）
                year_end = f"{year}1231"
                
                indicators = self.pro.fina_indicator(
                    ts_code=stock_code,
                    end_date=year_end,
                    period_type='Y',
                    fields='ts_code,end_date,roe,grossprofit_margin,netprofit_margin'
                )
                if indicators is not None and not indicators.empty:
                    # 过滤出该年的年报数据
                    year_indicators = indicators[indicators['end_date'].str.startswith(str(year))]
                    if not year_indicators.empty:
                        # 只取最新的一条年报数据
                        latest_indicator = year_indicators.iloc[0:1]
                        data['financial_indicators'].extend(latest_indicator.to_dict('records'))
                
                # 获取年末股息率（尝试多个日期）
                dividend_found = False
                for month_day in ['1231', '1230', '1229', '1228']:  # 尝试年末几天
                    test_date = f"{year}{month_day}"
                    dividend = self.pro.daily_basic(
                        ts_code=stock_code,
                        trade_date=test_date,
                        fields='ts_code,trade_date,dv_ratio'
                    )
                    if dividend is not None and not dividend.empty:
                        data['dividend'].extend(dividend.to_dict('records'))
                        dividend_found = True
                        break
                    time.sleep(0.1)  # 短暂延时
                
                # 获取年末PE（尝试多个日期）
                pe_found = False
                for month_day in ['1231', '1230', '1229', '1228']:  # 尝试年末几天
                    test_date = f"{year}{month_day}"
                    pe = self.pro.daily_basic(
                        ts_code=stock_code,
                        trade_date=test_date,
                        fields='ts_code,trade_date,pe'
                    )
                    if pe is not None and not pe.empty:
                        data['pe'].extend(pe.to_dict('records'))
                        pe_found = True
                        break
                    time.sleep(0.1)  # 短暂延时
                
                time.sleep(0.3)  # 添加延时避免频率限制
            
            return data
            
        except Exception as e:
            logger.error(f"获取年度数据失败 {stock_code}: {e}")
            return None

    def process_batch(self, stocks_batch, start_year, end_year, use_cache=True):
        """处理一批股票数据"""
        batch_index = stocks_batch.index[0] // self.batch_size
        
        # 尝试从缓存加载
        if use_cache:
            cached_data = self._load_batch_from_cache(batch_index)
            if cached_data is not None:
                return cached_data
        
        # 获取新数据
        batch_data = {}
        for _, stock in stocks_batch.iterrows():
            stock_code = stock['ts_code']
            stock_data = self.get_annual_data(stock_code, start_year, end_year)
            if stock_data:
                batch_data[stock_code] = {
                    'name': stock['name'],
                    'industry': stock['industry'],
                    'data': stock_data
                }
        
        # 保存到缓存
        if batch_data:
            self._save_batch_to_cache(batch_data, batch_index)
        
        return batch_data

class ExcelOptimizer:
    """Excel数据优化器"""
    def __init__(self, df):
        self.df = df
        
    def create_summary_view(self):
        """创建汇总视图 - 只显示关键信息"""
        if self.df is None:
            return None
            
        # 基本信息列
        basic_cols = ['stock_code', 'stock_name', 'industry', 'need_analysis']
        
        # 计算各指标的最新值和平均值
        summary_data = []
        
        for _, row in self.df.iterrows():
            summary_row = {}
            
            # 基本信息
            for col in basic_cols:
                if col in row:
                    summary_row[col] = row[col]
            
            # ROE汇总
            roe_cols = [col for col in self.df.columns if col.startswith('roe_')]
            roe_values = [row[col] for col in roe_cols if pd.notna(row[col])]
            if roe_values:
                summary_row['roe_最新'] = roe_values[-1]
                summary_row['roe_平均'] = np.mean(roe_values)
                summary_row['roe_趋势'] = '上升' if len(roe_values) > 1 and roe_values[-1] > roe_values[0] else '下降'
            
            # 毛利率汇总
            gm_cols = [col for col in self.df.columns if col.startswith('gross_margin_')]
            gm_values = [row[col] for col in gm_cols if pd.notna(row[col])]
            if gm_values:
                summary_row['毛利率_最新'] = gm_values[-1]
                summary_row['毛利率_平均'] = np.mean(gm_values)
            
            # 净利率汇总
            nm_cols = [col for col in self.df.columns if col.startswith('net_margin_')]
            nm_values = [row[col] for col in nm_cols if pd.notna(row[col])]
            if nm_values:
                summary_row['净利率_最新'] = nm_values[-1]
                summary_row['净利率_平均'] = np.mean(nm_values)
            
            # PE汇总
            pe_cols = [col for col in self.df.columns if col.startswith('pe_')]
            pe_values = [row[col] for col in pe_cols if pd.notna(row[col])]
            if pe_values:
                summary_row['PE_最新'] = pe_values[-1]
                summary_row['PE_平均'] = np.mean(pe_values)
            
            # 股息率汇总
            div_cols = [col for col in self.df.columns if col.startswith('dividend_')]
            div_values = [row[col] for col in div_cols if pd.notna(row[col])]
            if div_values:
                summary_row['股息率_最新'] = div_values[-1]
                summary_row['股息率_平均'] = np.mean(div_values)
            
            # 综合评分（简单评分逻辑）
            score = 0
            if 'roe_平均' in summary_row and summary_row['roe_平均'] > 15:
                score += 20
            if '毛利率_平均' in summary_row and summary_row['毛利率_平均'] > 30:
                score += 20
            if '净利率_平均' in summary_row and summary_row['净利率_平均'] > 10:
                score += 20
            if 'PE_平均' in summary_row and 10 < summary_row['PE_平均'] < 25:
                score += 20
            if '股息率_平均' in summary_row and summary_row['股息率_平均'] > 2:
                score += 20
            
            summary_row['综合评分'] = score
            summary_data.append(summary_row)
        
        return pd.DataFrame(summary_data)
    
    def create_sector_analysis(self):
        """创建行业分析视图"""
        if self.df is None:
            return None
            
        # 按行业分组统计
        sector_stats = []
        
        for industry in self.df['industry'].unique():
            if pd.isna(industry):
                continue
                
            industry_data = self.df[self.df['industry'] == industry]
            
            # 计算行业平均指标
            roe_cols = [col for col in self.df.columns if col.startswith('roe_')]
            pe_cols = [col for col in self.df.columns if col.startswith('pe_')]
            
            sector_row = {
                '行业': industry,
                '公司数量': len(industry_data),
                '平均ROE': industry_data[roe_cols].mean().mean(),
                '平均PE': industry_data[pe_cols].mean().mean(),
                '高ROE公司数': (industry_data[roe_cols].mean(axis=1) > 15).sum(),
                '需要分析数': (industry_data['need_analysis'] == True).sum()
            }
            sector_stats.append(sector_row)
        
        return pd.DataFrame(sector_stats).sort_values('平均ROE', ascending=False)
    
    def create_filtered_views(self):
        """创建筛选视图"""
        if self.df is None:
            return {}
            
        views = {}
        
        # 高ROE股票（ROE均值>15%）
        roe_cols = [col for col in self.df.columns if col.startswith('roe_')]
        high_roe_mask = self.df[roe_cols].mean(axis=1) > 15
        views['高ROE股票'] = self.df[high_roe_mask][['stock_code', 'stock_name', 'industry'] + roe_cols]
        
        # 低PE股票（PE均值<20）
        pe_cols = [col for col in self.df.columns if col.startswith('pe_')]
        low_pe_mask = self.df[pe_cols].mean(axis=1) < 20
        views['低PE股票'] = self.df[low_pe_mask][['stock_code', 'stock_name', 'industry'] + pe_cols]
        
        # 高股息股票（股息率均值>3%）
        div_cols = [col for col in self.df.columns if col.startswith('dividend_')]
        high_div_mask = self.df[div_cols].mean(axis=1) > 3
        views['高股息股票'] = self.df[high_div_mask][['stock_code', 'stock_name', 'industry'] + div_cols]
        
        # 稳定盈利股票（净利率连续正值）
        nm_cols = [col for col in self.df.columns if col.startswith('net_margin_')]
        stable_profit_mask = (self.df[nm_cols] > 0).all(axis=1)
        views['稳定盈利股票'] = self.df[stable_profit_mask][['stock_code', 'stock_name', 'industry'] + nm_cols]
        
        return views
    
    def _apply_styles(self, excel_file):
        """应用Excel样式"""
        try:
            wb = load_workbook(excel_file)
            
            # 为每个工作表添加样式
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                
                # 设置标题行样式
                header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                header_font = Font(color="FFFFFF", bold=True)
                
                for col in range(1, ws.max_column + 1):
                    cell = ws.cell(row=1, column=col)
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal="center")
                
                # 设置数据行样式
                for row in range(2, ws.max_row + 1):
                    for col in range(1, ws.max_column + 1):
                        cell = ws.cell(row=row, column=col)
                        cell.alignment = Alignment(horizontal="center")
                        
                        # 为数值类型的单元格设置条件格式
                        if isinstance(cell.value, (int, float)):
                            if cell.value is not None and cell.value < 0:
                                cell.font = Font(color="FF0000")  # 负值显示红色
                            elif cell.value is not None and cell.value > 20:
                                cell.font = Font(color="008000")  # 高值显示绿色
                
                # 自动调整列宽
                for column in ws.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 20)
                    ws.column_dimensions[column_letter].width = adjusted_width
            
            wb.save(excel_file)
            
        except Exception as e:
            logger.error(f"应用样式失败: {e}")
    
    def generate_analysis_suggestions(self):
        """生成分析建议"""
        if self.df is None:
            return None
            
        suggestions = []
        
        # 1. 高价值股票推荐
        summary_df = self.create_summary_view()
        if summary_df is not None:
            high_score_stocks = summary_df[summary_df['综合评分'] >= 80].sort_values('综合评分', ascending=False)
            if not high_score_stocks.empty:
                suggestions.append("🌟 高价值股票推荐：")
                for _, stock in high_score_stocks.head(10).iterrows():
                    suggestions.append(f"  • {stock['stock_name']}({stock['stock_code']}) - 评分:{stock['综合评分']}")
        
        # 2. 行业机会
        sector_df = self.create_sector_analysis()
        if sector_df is not None:
            top_sectors = sector_df.head(5)
            suggestions.append("\n📈 优势行业：")
            for _, sector in top_sectors.iterrows():
                suggestions.append(f"  • {sector['行业']} - 平均ROE:{sector['平均ROE']:.2f}%")
        
        # 3. 筛选建议
        filtered_views = self.create_filtered_views()
        suggestions.append("\n🔍 筛选建议：")
        for view_name, view_df in filtered_views.items():
            suggestions.append(f"  • {view_name}: {len(view_df)}只股票")
        
        return '\n'.join(suggestions)
    
    def save_optimized_excel(self, output_file='stock_analysis_optimized.xlsx'):
        """保存优化后的Excel文件"""
        if self.df is None:
            logger.error("没有数据可保存")
            return False
            
        try:
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # 1. 汇总视图
                summary_df = self.create_summary_view()
                if summary_df is not None:
                    summary_df.to_excel(writer, sheet_name='汇总视图', index=False)
                    logger.info(f"汇总视图已创建，包含{len(summary_df)}行数据")
                
                # 2. 行业分析
                sector_df = self.create_sector_analysis()
                if sector_df is not None:
                    sector_df.to_excel(writer, sheet_name='行业分析', index=False)
                    logger.info(f"行业分析已创建，包含{len(sector_df)}个行业")
                
                # 3. 筛选视图
                filtered_views = self.create_filtered_views()
                for view_name, view_df in filtered_views.items():
                    if not view_df.empty:
                        view_df.to_excel(writer, sheet_name=view_name, index=False)
                        logger.info(f"{view_name}已创建，包含{len(view_df)}只股票")
                
                # 4. 原始数据（可选）
                self.df.to_excel(writer, sheet_name='原始数据', index=False)
                logger.info("原始数据已保留")
            
            # 添加样式
            self._apply_styles(output_file)
            logger.info(f"优化后的Excel文件已保存: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"保存Excel文件失败: {e}")
            return False

def setup_logger():
    """配置日志"""
    log_path = "logs"
    os.makedirs(log_path, exist_ok=True)
    logger.add(
        os.path.join(log_path, "data_collection_{time}.log"),
        rotation="500 MB",
        encoding="utf-8"
    )

def process_stock_data(batch_data):
    """处理股票数据为最终格式"""
    results = []
    for stock_code, stock_info in batch_data.items():
        row = {
            'stock_code': stock_code,
            'stock_name': stock_info['name'],
            'industry': stock_info['industry'],
            'need_analysis': False
        }
        
        # 处理财务指标
        for indicator in stock_info['data']['financial_indicators']:
            year = indicator['end_date'][:4]
            row[f'roe_{year}'] = indicator['roe']
            row[f'gross_margin_{year}'] = indicator['grossprofit_margin']
            row[f'net_margin_{year}'] = indicator['netprofit_margin']
        
        # 处理股息率
        for dividend in stock_info['data']['dividend']:
            year = dividend['trade_date'][:4]
            row[f'dividend_{year}'] = dividend['dv_ratio']
        
        # 处理PE
        for pe_data in stock_info['data']['pe']:
            year = pe_data['trade_date'][:4]
            row[f'pe_{year}'] = pe_data['pe']
        
        results.append(row)
    
    return results

def main():
    """主程序入口"""
    setup_logger()
    
    # 命令行参数解析
    parser = argparse.ArgumentParser(description='A股基本面数据收集工具')
    parser.add_argument('--limit', type=int, default=None, help='限制处理的股票数量（测试用）')
    parser.add_argument('--batch-size', type=int, default=50, help='批处理大小')
    parser.add_argument('--no-cache', action='store_true', help='不使用缓存，重新获取数据')
    parser.add_argument('--start-year', type=int, default=2018, help='开始年份')
    parser.add_argument('--end-year', type=int, default=2025, help='结束年份')
    parser.add_argument('--no-optimize', action='store_true', help='不生成优化Excel视图')
    
    args = parser.parse_args()
    
    # 从配置文件获取token
    token = config.TUSHARE_TOKEN
    if not token:
        logger.error("请在.env文件中设置TUSHARE_TOKEN")
        return
    
    # 初始化收集器
    collector = StockDataCollector(token, cache_dir='cache', batch_size=args.batch_size)
    
    try:
        logger.info(f"数据收集时间范围：{args.start_year} 至 {args.end_year}")
        
        # 获取股票列表
        stocks = collector.get_all_stocks()
        if stocks is None:
            logger.error("获取股票列表失败")
            return
        
        # 限制股票数量（测试模式）
        if args.limit:
            stocks = stocks.head(args.limit)
            logger.info(f"限制模式：只处理前 {args.limit} 只股票")
        
        logger.info(f"共获取到 {len(stocks)} 只股票")
        
        # 计算批次数量
        total_batches = (len(stocks) + args.batch_size - 1) // args.batch_size
        logger.info(f"将分 {total_batches} 个批次处理")
        
        all_results = []
        
        # 按批次处理
        for i in tqdm(range(total_batches), desc="处理批次"):
            start_idx = i * args.batch_size
            end_idx = min((i + 1) * args.batch_size, len(stocks))
            stocks_batch = stocks.iloc[start_idx:end_idx]
            
            # 处理当前批次
            batch_data = collector.process_batch(
                stocks_batch,
                args.start_year,
                args.end_year,
                use_cache=not args.no_cache
            )
            
            # 处理数据并添加到结果
            if batch_data:
                batch_results = process_stock_data(batch_data)
                all_results.extend(batch_results)
                logger.info(f"完成第 {i+1}/{total_batches} 批次处理，当前已处理 {len(all_results)} 只股票")
        
        # 保存最终结果
        if all_results:
            df = pd.DataFrame(all_results)
            output_file = 'stock_analysis_data.xlsx'
            df.to_excel(output_file, index=False)
            logger.info(f"原始数据已保存到: {output_file}")
            logger.info(f"共处理了 {len(all_results)} 只股票，{len(df.columns)} 列数据")
            
            # 自动生成优化视图
            if not args.no_optimize:
                logger.info("开始生成优化Excel视图...")
                optimizer = ExcelOptimizer(df)
                
                if optimizer.save_optimized_excel():
                    logger.info("✅ 优化Excel文件创建成功: stock_analysis_optimized.xlsx")
                    
                    # 生成分析建议
                    suggestions = optimizer.generate_analysis_suggestions()
                    if suggestions:
                        logger.info("📋 投资分析建议：")
                        print("\n" + suggestions)
                        
                        # 保存建议到文件
                        with open('analysis_suggestions.txt', 'w', encoding='utf-8') as f:
                            f.write(suggestions)
                        logger.info("💾 分析建议已保存到: analysis_suggestions.txt")
                    
                    print(f"\n🎯 数据处理完成！生成了以下文件：")
                    print(f"  📄 {output_file} - 原始数据 ({len(df.columns)}列)")
                    print(f"  📊 stock_analysis_optimized.xlsx - 优化视图 (7个工作表)")
                    print(f"  📝 analysis_suggestions.txt - 投资建议")
                else:
                    logger.error("优化Excel文件创建失败")
            else:
                logger.info("已跳过优化Excel视图生成（使用--no-optimize参数）")
                
        else:
            logger.error("没有收集到任何数据")
            
    except Exception as e:
        logger.error(f"主程序执行失败: {e}")

if __name__ == "__main__":
    main() 