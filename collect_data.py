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
    parser = argparse.ArgumentParser(description='股票数据收集工具')
    parser.add_argument('--use-cache', action='store_true', help='使用缓存数据')
    parser.add_argument('--batch-size', type=int, default=50, help='每批处理的股票数量')
    parser.add_argument('--limit', type=int, help='限制处理的股票数量（用于测试）')
    args = parser.parse_args()
    
    setup_logger()
    
    try:
        # 检查环境变量
        tushare_token = check_environment()
        
        # 设置时间范围
        today = datetime.now()
        end_year = today.year
        start_year = end_year - 7  # 获取近7年数据
        
        logger.info(f"数据收集时间范围：{start_year} 至 {end_year}")
        
        # 创建数据收集器
        collector = StockDataCollector(tushare_token, batch_size=args.batch_size)
        
        # 获取所有股票列表
        stocks = collector.get_all_stocks()
        if stocks is None:
            logger.error("获取股票列表失败")
            return
        
        # 如果设置了限制，只处理指定数量的股票
        if args.limit:
            stocks = stocks.head(args.limit)
            logger.info(f"限制模式：只处理前 {args.limit} 只股票")
        
        # 计算总批次数
        total_batches = math.ceil(len(stocks) / args.batch_size)
        all_results = []
        
        # 按批次处理
        for i in tqdm(range(total_batches), desc="处理批次"):
            start_idx = i * args.batch_size
            end_idx = min((i + 1) * args.batch_size, len(stocks))
            stocks_batch = stocks.iloc[start_idx:end_idx]
            
            # 处理当前批次
            batch_data = collector.process_batch(
                stocks_batch,
                start_year,
                end_year,
                use_cache=args.use_cache
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
            logger.info(f"数据已保存到: {output_file}")
            logger.info(f"共处理了 {len(all_results)} 只股票")
        else:
            logger.error("没有收集到任何数据")
            
    except Exception as e:
        logger.error(f"主程序执行失败: {e}")

if __name__ == "__main__":
    main() 