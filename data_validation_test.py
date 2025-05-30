#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import random
import requests
import time
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import json
from loguru import logger

class DataValidator:
    def __init__(self, db_path='stock_analysis.db'):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_random_stocks(self, count: int = 25) -> List[Dict]:
        """从数据库中随机获取股票列表"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 获取所有股票代码，排除ST股票和特殊股票
            query = """
            SELECT DISTINCT stock_code, stock_name 
            FROM stocks 
            WHERE stock_code NOT LIKE '%.BJ' 
            AND stock_name NOT LIKE '%ST%'
            AND stock_name NOT LIKE '%退%'
            ORDER BY RANDOM() 
            LIMIT ?
            """
            
            df = pd.read_sql_query(query, conn, params=(count,))
            conn.close()
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"获取随机股票失败: {e}")
            return []
    
    def get_stock_data_from_db(self, stock_code: str) -> Dict:
        """从数据库获取股票数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 获取基本信息
            basic_query = """
            SELECT * FROM stocks 
            WHERE stock_code = ? 
            LIMIT 1
            """
            basic_df = pd.read_sql_query(basic_query, conn, params=(stock_code,))
            
            if basic_df.empty:
                return {}
            
            basic_info = basic_df.iloc[0].to_dict()
            
            # 获取最新财务指标数据 
            financial_query = """
            SELECT metric_name, metric_value, year
            FROM financial_metrics 
            WHERE stock_code = ? 
            AND year = (
                SELECT MAX(year) 
                FROM financial_metrics 
                WHERE stock_code = ?
            )
            """
            financial_df = pd.read_sql_query(financial_query, conn, params=(stock_code, stock_code))
            
            # 将财务指标数据转换为字典格式
            financial_data = {}
            latest_year = None
            if not financial_df.empty:
                latest_year = financial_df['year'].iloc[0]
                for _, row in financial_df.iterrows():
                    financial_data[row['metric_name']] = row['metric_value']
                financial_data['year'] = latest_year
            
            conn.close()
            
            return {
                'basic': basic_info,
                'financial': financial_data,
                'latest_year': latest_year
            }
            
        except Exception as e:
            logger.error(f"获取股票 {stock_code} 数据库数据失败: {e}")
            return {}
    
    def get_online_data(self, stock_code: str) -> Dict:
        """从网上获取股票实时数据"""
        try:
            # 转换股票代码格式
            if stock_code.endswith('.SZ'):
                code = '0' + stock_code.replace('.SZ', '')
            elif stock_code.endswith('.SH'):
                code = '1' + stock_code.replace('.SH', '')
            else:
                return {}
            
            # 使用新浪财经API获取实时数据
            url = f"http://hq.sinajs.cn/list={code}"
            
            response = self.session.get(url, timeout=10)
            response.encoding = 'gbk'
            
            if response.status_code == 200:
                content = response.text
                if 'var hq_str_' in content:
                    # 解析新浪财经数据
                    data_str = content.split('"')[1]
                    if data_str:
                        data_parts = data_str.split(',')
                        if len(data_parts) >= 10:
                            return {
                                'name': data_parts[0],
                                'current_price': float(data_parts[3]) if data_parts[3] else 0,
                                'volume': float(data_parts[8]) if data_parts[8] else 0,
                                'market_cap': float(data_parts[3]) * float(data_parts[8]) if data_parts[3] and data_parts[8] else 0
                            }
            
            # 备选：使用腾讯财经API
            time.sleep(0.5)  # 避免请求过快
            tencent_code = stock_code.replace('.SZ', '').replace('.SH', '')
            if stock_code.endswith('.SZ'):
                tencent_code = 'sz' + tencent_code
            elif stock_code.endswith('.SH'):
                tencent_code = 'sh' + tencent_code
            
            tencent_url = f"http://qt.gtimg.cn/q={tencent_code}"
            response = self.session.get(tencent_url, timeout=10)
            response.encoding = 'gbk'
            
            if response.status_code == 200:
                content = response.text
                if 'v_' in content:
                    data_str = content.split('"')[1]
                    if data_str:
                        data_parts = data_str.split('~')
                        if len(data_parts) >= 47:  # 确保数据足够长
                            try:
                                return {
                                    'name': data_parts[1],
                                    'current_price': float(data_parts[3]) if data_parts[3] and data_parts[3] != '0' else None,
                                    'pe_ratio': float(data_parts[39]) if len(data_parts) > 39 and data_parts[39] and data_parts[39] != '0' else None,
                                    'pb_ratio': float(data_parts[46]) if len(data_parts) > 46 and data_parts[46] and data_parts[46] != '0' else None
                                }
                            except (ValueError, IndexError):
                                pass
            
            return {}
            
        except Exception as e:
            logger.warning(f"获取股票 {stock_code} 在线数据失败: {e}")
            return {}
    
    def validate_stock_data(self, stock_code: str) -> Dict:
        """验证单个股票的数据"""
        logger.info(f"验证股票: {stock_code}")
        
        # 获取数据库数据
        db_data = self.get_stock_data_from_db(stock_code)
        
        # 获取在线数据
        online_data = self.get_online_data(stock_code)
        
        # 等待一秒避免请求过快
        time.sleep(1)
        
        # 比较结果
        comparison = {
            'stock_code': stock_code,
            'db_name': db_data.get('basic', {}).get('stock_name', 'N/A'),
            'online_name': online_data.get('name', 'N/A'),
            'name_match': False,
            'db_pe': db_data.get('financial', {}).get('pe', 'N/A'),
            'online_pe': online_data.get('pe_ratio', 'N/A'),
            'pe_diff': 'N/A',
            'db_pb': db_data.get('financial', {}).get('pb', 'N/A'),
            'online_pb': online_data.get('pb_ratio', 'N/A'),
            'pb_diff': 'N/A',
            'db_roe': db_data.get('financial', {}).get('roe', 'N/A'),
            'db_gross_margin': db_data.get('financial', {}).get('gross_margin', 'N/A'),
            'db_current_ratio': db_data.get('financial', {}).get('current_ratio', 'N/A'),
            'db_year': db_data.get('latest_year', 'N/A'),
            'data_available': {
                'db_basic': bool(db_data.get('basic')),
                'db_financial': bool(db_data.get('financial')),
                'online': bool(online_data)
            }
        }
        
        # 检查名称匹配
        if comparison['db_name'] != 'N/A' and comparison['online_name'] != 'N/A':
            comparison['name_match'] = comparison['db_name'] in comparison['online_name'] or comparison['online_name'] in comparison['db_name']
        
        # 计算PE差异
        if (isinstance(comparison['db_pe'], (int, float)) and 
            isinstance(comparison['online_pe'], (int, float)) and
            comparison['db_pe'] > 0 and comparison['online_pe'] > 0):
            comparison['pe_diff'] = abs(comparison['db_pe'] - comparison['online_pe'])
        
        # 计算PB差异
        if (isinstance(comparison['db_pb'], (int, float)) and 
            isinstance(comparison['online_pb'], (int, float)) and
            comparison['db_pb'] > 0 and comparison['online_pb'] > 0):
            comparison['pb_diff'] = abs(comparison['db_pb'] - comparison['online_pb'])
        
        return comparison
    
    def run_validation(self, count: int = 25) -> List[Dict]:
        """运行数据验证"""
        logger.info(f"开始随机验证 {count} 只股票的数据准确性")
        
        # 获取随机股票
        stocks = self.get_random_stocks(count)
        if not stocks:
            logger.error("无法获取随机股票列表")
            return []
        
        logger.info(f"获取到 {len(stocks)} 只随机股票")
        
        # 验证每只股票
        results = []
        for i, stock in enumerate(stocks, 1):
            logger.info(f"进度: {i}/{len(stocks)} - {stock['stock_code']}")
            result = self.validate_stock_data(stock['stock_code'])
            results.append(result)
            
            # 每5个股票暂停一下
            if i % 5 == 0:
                time.sleep(2)
        
        return results
    
    def generate_report(self, results: List[Dict]) -> str:
        """生成验证报告"""
        if not results:
            return "无验证结果"
        
        report = []
        report.append("# 📊 股票数据验证报告")
        report.append(f"**验证时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**验证样本**: {len(results)} 只股票")
        report.append("")
        
        # 统计信息
        total_stocks = len(results)
        name_matches = sum(1 for r in results if r['name_match'])
        db_data_available = sum(1 for r in results if r['data_available']['db_basic'])
        online_data_available = sum(1 for r in results if r['data_available']['online'])
        both_pe_available = sum(1 for r in results if isinstance(r['pe_diff'], (int, float)))
        both_pb_available = sum(1 for r in results if isinstance(r['pb_diff'], (int, float)))
        
        report.append("## 📈 验证统计")
        report.append(f"- 总验证股票: {total_stocks} 只")
        report.append(f"- 名称匹配: {name_matches} 只 ({name_matches/total_stocks*100:.1f}%)")
        report.append(f"- 数据库数据可用: {db_data_available} 只 ({db_data_available/total_stocks*100:.1f}%)")
        report.append(f"- 在线数据可用: {online_data_available} 只 ({online_data_available/total_stocks*100:.1f}%)")
        report.append(f"- PE数据可对比: {both_pe_available} 只 ({both_pe_available/total_stocks*100:.1f}%)")
        report.append(f"- PB数据可对比: {both_pb_available} 只 ({both_pb_available/total_stocks*100:.1f}%)")
        report.append("")
        
        # PE差异分析
        if both_pe_available > 0:
            pe_diffs = [r['pe_diff'] for r in results if isinstance(r['pe_diff'], (int, float))]
            avg_pe_diff = sum(pe_diffs) / len(pe_diffs)
            max_pe_diff = max(pe_diffs)
            large_pe_diffs = sum(1 for diff in pe_diffs if diff > 5)
            
            report.append("## 🎯 PE数据对比分析")
            report.append(f"- 平均PE差异: {avg_pe_diff:.2f}")
            report.append(f"- 最大PE差异: {max_pe_diff:.2f}")
            report.append(f"- PE差异>5的股票: {large_pe_diffs} 只 ({large_pe_diffs/both_pe_available*100:.1f}%)")
            report.append("")
        
        # PB差异分析
        if both_pb_available > 0:
            pb_diffs = [r['pb_diff'] for r in results if isinstance(r['pb_diff'], (int, float))]
            avg_pb_diff = sum(pb_diffs) / len(pb_diffs)
            max_pb_diff = max(pb_diffs)
            large_pb_diffs = sum(1 for diff in pb_diffs if diff > 1)
            
            report.append("## 🎯 PB数据对比分析")
            report.append(f"- 平均PB差异: {avg_pb_diff:.2f}")
            report.append(f"- 最大PB差异: {max_pb_diff:.2f}")
            report.append(f"- PB差异>1的股票: {large_pb_diffs} 只 ({large_pb_diffs/both_pb_available*100:.1f}%)")
            report.append("")
        
        # 详细对比表
        report.append("## 📋 详细验证结果")
        report.append("")
        report.append("| 序号 | 股票代码 | 数据库名称 | 在线名称 | 名称匹配 | 数据库PE | 在线PE | PE差异 | 数据库PB | 在线PB | PB差异 | 数据库ROE | 数据年份 |")
        report.append("|------|----------|------------|----------|----------|----------|--------|--------|----------|--------|--------|-----------|----------|")
        
        for i, result in enumerate(results, 1):
            pe_diff_str = f"{result['pe_diff']:.2f}" if isinstance(result['pe_diff'], (int, float)) else "N/A"
            pb_diff_str = f"{result['pb_diff']:.2f}" if isinstance(result['pb_diff'], (int, float)) else "N/A"
            name_match_str = "✅" if result['name_match'] else "❌"
            
            db_pe_str = f"{result['db_pe']:.2f}" if isinstance(result['db_pe'], (int, float)) else "N/A"
            online_pe_str = f"{result['online_pe']:.2f}" if isinstance(result['online_pe'], (int, float)) else "N/A"
            db_pb_str = f"{result['db_pb']:.2f}" if isinstance(result['db_pb'], (int, float)) else "N/A"
            online_pb_str = f"{result['online_pb']:.2f}" if isinstance(result['online_pb'], (int, float)) else "N/A"
            db_roe_str = f"{result['db_roe']:.2f}%" if isinstance(result['db_roe'], (int, float)) else "N/A"
            
            report.append(f"| {i} | {result['stock_code']} | {result['db_name'][:10]} | {result['online_name'][:10]} | {name_match_str} | {db_pe_str} | {online_pe_str} | {pe_diff_str} | {db_pb_str} | {online_pb_str} | {pb_diff_str} | {db_roe_str} | {result['db_year']} |")
        
        report.append("")
        
        # 数据质量分析
        report.append("## 🔍 数据质量分析")
        
        # 分析数据库数据完整性
        db_financial_complete = sum(1 for r in results if r['data_available']['db_financial'])
        pe_available_db = sum(1 for r in results if isinstance(r['db_pe'], (int, float)))
        pb_available_db = sum(1 for r in results if isinstance(r['db_pb'], (int, float)))
        roe_available_db = sum(1 for r in results if isinstance(r['db_roe'], (int, float)))
        
        report.append("### 数据库数据完整性")
        report.append(f"- 有财务数据的股票: {db_financial_complete}/{total_stocks} ({db_financial_complete/total_stocks*100:.1f}%)")
        report.append(f"- PE数据可用: {pe_available_db}/{total_stocks} ({pe_available_db/total_stocks*100:.1f}%)")
        report.append(f"- PB数据可用: {pb_available_db}/{total_stocks} ({pb_available_db/total_stocks*100:.1f}%)")
        report.append(f"- ROE数据可用: {roe_available_db}/{total_stocks} ({roe_available_db/total_stocks*100:.1f}%)")
        report.append("")
        
        # 分析在线数据获取情况
        online_pe_available = sum(1 for r in results if isinstance(r['online_pe'], (int, float)))
        online_pb_available = sum(1 for r in results if isinstance(r['online_pb'], (int, float)))
        
        report.append("### 在线数据获取情况")
        report.append(f"- 成功获取在线数据: {online_data_available}/{total_stocks} ({online_data_available/total_stocks*100:.1f}%)")
        report.append(f"- 在线PE数据可用: {online_pe_available}/{total_stocks} ({online_pe_available/total_stocks*100:.1f}%)")
        report.append(f"- 在线PB数据可用: {online_pb_available}/{total_stocks} ({online_pb_available/total_stocks*100:.1f}%)")
        report.append("")
        
        # 结论与建议
        report.append("## 🔍 结论与建议")
        
        if name_matches / total_stocks < 0.8:
            report.append("⚠️ **名称匹配率较低**，可能存在股票代码映射问题")
        else:
            report.append("✅ 股票名称匹配良好")
        
        if db_financial_complete / total_stocks < 0.8:
            report.append("⚠️ **数据库财务数据完整性不足**，建议补充数据收集")
        else:
            report.append("✅ 数据库财务数据较为完整")
        
        if both_pe_available > 0:
            pe_diffs = [r['pe_diff'] for r in results if isinstance(r['pe_diff'], (int, float))]
            avg_pe_diff = sum(pe_diffs) / len(pe_diffs)
            if avg_pe_diff > 10:
                report.append("⚠️ **PE数据差异较大**，建议检查PE计算方法或数据源时效性")
            elif avg_pe_diff > 5:
                report.append("📊 PE数据存在一定差异，可能与数据源和时间差异有关")
            else:
                report.append("✅ PE数据基本一致")
        
        if both_pb_available > 0:
            pb_diffs = [r['pb_diff'] for r in results if isinstance(r['pb_diff'], (int, float))]
            avg_pb_diff = sum(pb_diffs) / len(pb_diffs)
            if avg_pb_diff > 1:
                report.append("⚠️ **PB数据差异较大**，建议检查PB计算方法或数据源时效性")
            else:
                report.append("✅ PB数据基本一致")
        
        report.append("")
        report.append("---")
        report.append("*注：数据库中的财务数据通常来自年报，而在线数据可能是实时或季报数据，存在一定时间差异是正常的。*")
        
        return "\n".join(report)

def main():
    logger.info("开始数据验证测试")
    
    validator = DataValidator()
    results = validator.run_validation(25)
    
    if results:
        report = validator.generate_report(results)
        
        # 保存报告
        report_file = f"数据验证报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"验证完成，报告已保存到: {report_file}")
        
        # 输出简要结果
        print("\n" + "="*80)
        print("📊 数据验证测试完成")
        print("="*80)
        print(f"验证样本: {len(results)} 只股票")
        
        name_matches = sum(1 for r in results if r['name_match'])
        print(f"名称匹配: {name_matches}/{len(results)} ({name_matches/len(results)*100:.1f}%)")
        
        both_pe_available = sum(1 for r in results if isinstance(r['pe_diff'], (int, float)))
        if both_pe_available > 0:
            pe_diffs = [r['pe_diff'] for r in results if isinstance(r['pe_diff'], (int, float))]
            avg_pe_diff = sum(pe_diffs) / len(pe_diffs)
            print(f"PE数据对比: {both_pe_available} 只，平均差异: {avg_pe_diff:.2f}")
        
        both_pb_available = sum(1 for r in results if isinstance(r['pb_diff'], (int, float)))
        if both_pb_available > 0:
            pb_diffs = [r['pb_diff'] for r in results if isinstance(r['pb_diff'], (int, float))]
            avg_pb_diff = sum(pb_diffs) / len(pb_diffs)
            print(f"PB数据对比: {both_pb_available} 只，平均差异: {avg_pb_diff:.2f}")
        
        print(f"\n📄 详细报告: {report_file}")
        print("="*80)
    else:
        logger.error("验证失败，无结果")

if __name__ == "__main__":
    main() 