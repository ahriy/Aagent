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
from value_investment_agent import ValueInvestmentAgent

class AgentResultValidator:
    def __init__(self, db_path='stock_analysis.db'):
        self.db_path = db_path
        self.agent = ValueInvestmentAgent()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_random_stocks(self, count: int = 25) -> List[str]:
        """从数据库中随机获取股票代码列表"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = """
            SELECT DISTINCT stock_code 
            FROM stocks 
            WHERE stock_code NOT LIKE '%.BJ' 
            AND stock_name NOT LIKE '%ST%'
            AND stock_name NOT LIKE '%退%'
            ORDER BY RANDOM() 
            LIMIT ?
            """
            
            df = pd.read_sql_query(query, conn, params=(count,))
            conn.close()
            
            return df['stock_code'].tolist()
            
        except Exception as e:
            logger.error(f"获取随机股票失败: {e}")
            return []
    
    def get_agent_analysis(self, stock_code: str) -> Dict:
        """获取agent对股票的分析结果"""
        try:
            logger.info(f"获取agent分析: {stock_code}")
            result = self.agent.comprehensive_evaluation(stock_code, use_realtime_pe=True)
            return result
        except Exception as e:
            logger.error(f"获取股票 {stock_code} agent分析失败: {e}")
            return {}
    
    def get_online_realtime_data(self, stock_code: str) -> Dict:
        """从网上获取股票实时数据"""
        try:
            # 先尝试通过Tushare API获取实时PE
            realtime_pe = self.agent.get_realtime_pe(stock_code)
            
            result = {'realtime_pe': realtime_pe}
            
            # 使用腾讯财经API获取更多实时数据
            time.sleep(0.5)
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
                        if len(data_parts) >= 47:
                            try:
                                result.update({
                                    'name': data_parts[1],
                                    'current_price': float(data_parts[3]) if data_parts[3] and data_parts[3] != '0' else None,
                                    'online_pe': float(data_parts[39]) if len(data_parts) > 39 and data_parts[39] and data_parts[39] != '0' else None,
                                    'online_pb': float(data_parts[46]) if len(data_parts) > 46 and data_parts[46] and data_parts[46] != '0' else None,
                                    'market_cap': float(data_parts[45]) if len(data_parts) > 45 and data_parts[45] and data_parts[45] != '0' else None
                                })
                            except (ValueError, IndexError):
                                pass
            
            return result
            
        except Exception as e:
            logger.warning(f"获取股票 {stock_code} 在线数据失败: {e}")
            return {}
    
    def validate_single_stock(self, stock_code: str) -> Dict:
        """验证单个股票的agent结果与在线数据"""
        logger.info(f"验证股票: {stock_code}")
        
        # 获取agent分析结果
        agent_result = self.get_agent_analysis(stock_code)
        
        # 获取在线实时数据
        online_data = self.get_online_realtime_data(stock_code)
        
        # 等待避免请求过快
        time.sleep(1)
        
        # 构建比较结果
        comparison = {
            'stock_code': stock_code,
            'agent_success': bool(agent_result and 'error' not in agent_result),
            'online_success': bool(online_data),
            
            # 基本信息
            'agent_name': agent_result.get('stock_name', 'N/A'),
            'online_name': online_data.get('name', 'N/A'),
            'name_match': False,
            
            # PE对比
            'agent_pe': agent_result.get('realtime_pe', agent_result.get('pe_ratio', 'N/A')),
            'agent_pe_source': 'realtime' if agent_result.get('realtime_pe') else 'historical',
            'tushare_pe': online_data.get('realtime_pe', 'N/A'),
            'online_pe': online_data.get('online_pe', 'N/A'),
            'pe_diff_tushare': 'N/A',
            'pe_diff_online': 'N/A',
            
            # PB对比
            'agent_pb': 'N/A',
            'online_pb': online_data.get('online_pb', 'N/A'),
            'pb_diff': 'N/A',
            
            # 财务指标
            'agent_roe': 'N/A',
            'agent_debt_ratio': 'N/A',
            'agent_current_ratio': 'N/A',
            'agent_score': agent_result.get('total_score', 'N/A'),
            'agent_grade': agent_result.get('grade', 'N/A'),
        }
        
        # 从agent结果中提取财务指标
        if agent_result:
            stock_data = self.agent.get_stock_metrics(stock_code)
            if stock_data and 'metrics' in stock_data:
                metrics = stock_data['metrics']
                
                # ROE
                roe_data = metrics.get('roe', {})
                if roe_data:
                    latest_year = max(roe_data.keys())
                    comparison['agent_roe'] = roe_data[latest_year]
                
                # PB
                pb_data = metrics.get('pb', {})
                if pb_data:
                    latest_year = max(pb_data.keys())
                    comparison['agent_pb'] = pb_data[latest_year]
                
                # 债务比率
                debt_data = metrics.get('debt_ratio', {})
                if debt_data:
                    latest_year = max(debt_data.keys())
                    comparison['agent_debt_ratio'] = debt_data[latest_year]
                
                # 流动比率
                current_data = metrics.get('current_ratio', {})
                if current_data:
                    latest_year = max(current_data.keys())
                    comparison['agent_current_ratio'] = current_data[latest_year]
        
        # 检查名称匹配
        if comparison['agent_name'] != 'N/A' and comparison['online_name'] != 'N/A':
            comparison['name_match'] = comparison['agent_name'] in comparison['online_name'] or comparison['online_name'] in comparison['agent_name']
        
        # 计算PE差异（agent vs tushare实时PE）
        if (isinstance(comparison['agent_pe'], (int, float)) and 
            isinstance(comparison['tushare_pe'], (int, float)) and
            comparison['agent_pe'] > 0 and comparison['tushare_pe'] > 0):
            comparison['pe_diff_tushare'] = abs(comparison['agent_pe'] - comparison['tushare_pe'])
        
        # 计算PE差异（agent vs 在线PE）
        if (isinstance(comparison['agent_pe'], (int, float)) and 
            isinstance(comparison['online_pe'], (int, float)) and
            comparison['agent_pe'] > 0 and comparison['online_pe'] > 0):
            comparison['pe_diff_online'] = abs(comparison['agent_pe'] - comparison['online_pe'])
        
        # 计算PB差异
        if (isinstance(comparison['agent_pb'], (int, float)) and 
            isinstance(comparison['online_pb'], (int, float)) and
            comparison['agent_pb'] > 0 and comparison['online_pb'] > 0):
            comparison['pb_diff'] = abs(comparison['agent_pb'] - comparison['online_pb'])
        
        return comparison
    
    def run_validation(self, count: int = 25) -> List[Dict]:
        """运行验证"""
        logger.info(f"开始验证价值投资agent的 {count} 只股票分析结果")
        
        # 获取随机股票
        stocks = self.get_random_stocks(count)
        if not stocks:
            logger.error("无法获取随机股票列表")
            return []
        
        logger.info(f"获取到 {len(stocks)} 只随机股票")
        
        # 验证每只股票
        results = []
        for i, stock_code in enumerate(stocks, 1):
            logger.info(f"进度: {i}/{len(stocks)} - {stock_code}")
            result = self.validate_single_stock(stock_code)
            results.append(result)
            
            # 每5个股票暂停一下
            if i % 5 == 0:
                logger.info(f"已完成 {i} 只股票，暂停2秒...")
                time.sleep(2)
        
        return results
    
    def generate_report(self, results: List[Dict]) -> str:
        """生成验证报告"""
        if not results:
            return "无验证结果"
        
        report = []
        report.append("# 📊 价值投资Agent结果验证报告")
        report.append(f"**验证时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**验证样本**: {len(results)} 只股票")
        report.append("")
        
        # 统计信息
        total_stocks = len(results)
        agent_success = sum(1 for r in results if r['agent_success'])
        online_success = sum(1 for r in results if r['online_success'])
        name_matches = sum(1 for r in results if r['name_match'])
        pe_tushare_available = sum(1 for r in results if isinstance(r['pe_diff_tushare'], (int, float)))
        pe_online_available = sum(1 for r in results if isinstance(r['pe_diff_online'], (int, float)))
        pb_available = sum(1 for r in results if isinstance(r['pb_diff'], (int, float)))
        
        report.append("## 📈 验证统计")
        report.append(f"- 总验证股票: {total_stocks} 只")
        report.append(f"- Agent分析成功: {agent_success} 只 ({agent_success/total_stocks*100:.1f}%)")
        report.append(f"- 在线数据获取成功: {online_success} 只 ({online_success/total_stocks*100:.1f}%)")
        report.append(f"- 股票名称匹配: {name_matches} 只 ({name_matches/total_stocks*100:.1f}%)")
        report.append(f"- PE数据可对比(Tushare): {pe_tushare_available} 只 ({pe_tushare_available/total_stocks*100:.1f}%)")
        report.append(f"- PE数据可对比(在线): {pe_online_available} 只 ({pe_online_available/total_stocks*100:.1f}%)")
        report.append(f"- PB数据可对比: {pb_available} 只 ({pb_available/total_stocks*100:.1f}%)")
        report.append("")
        
        # PE差异分析（Tushare）
        if pe_tushare_available > 0:
            pe_diffs = [r['pe_diff_tushare'] for r in results if isinstance(r['pe_diff_tushare'], (int, float))]
            avg_pe_diff = sum(pe_diffs) / len(pe_diffs)
            max_pe_diff = max(pe_diffs)
            large_pe_diffs = sum(1 for diff in pe_diffs if diff > 5)
            
            report.append("## 🎯 PE数据对比分析 (Agent vs Tushare)")
            report.append(f"- 平均PE差异: {avg_pe_diff:.2f}")
            report.append(f"- 最大PE差异: {max_pe_diff:.2f}")
            report.append(f"- PE差异>5的股票: {large_pe_diffs} 只 ({large_pe_diffs/pe_tushare_available*100:.1f}%)")
            report.append("")
        
        # PE差异分析（在线）
        if pe_online_available > 0:
            pe_diffs = [r['pe_diff_online'] for r in results if isinstance(r['pe_diff_online'], (int, float))]
            avg_pe_diff = sum(pe_diffs) / len(pe_diffs)
            max_pe_diff = max(pe_diffs)
            large_pe_diffs = sum(1 for diff in pe_diffs if diff > 5)
            
            report.append("## 🎯 PE数据对比分析 (Agent vs 在线)")
            report.append(f"- 平均PE差异: {avg_pe_diff:.2f}")
            report.append(f"- 最大PE差异: {max_pe_diff:.2f}")
            report.append(f"- PE差异>5的股票: {large_pe_diffs} 只 ({large_pe_diffs/pe_online_available*100:.1f}%)")
            report.append("")
        
        # 详细对比表
        report.append("## 📋 详细验证结果")
        report.append("")
        report.append("| 序号 | 股票代码 | Agent名称 | 在线名称 | 名称匹配 | Agent PE | PE来源 | Tushare PE | 在线PE | PE差异(T) | PE差异(O) | Agent PB | 在线PB | PB差异 | Agent评分 |")
        report.append("|------|----------|-----------|----------|----------|----------|--------|------------|--------|-----------|-----------|----------|--------|--------|-----------|")
        
        for i, result in enumerate(results, 1):
            name_match_str = "✅" if result['name_match'] else "❌"
            
            agent_pe_str = f"{result['agent_pe']:.2f}" if isinstance(result['agent_pe'], (int, float)) else "N/A"
            tushare_pe_str = f"{result['tushare_pe']:.2f}" if isinstance(result['tushare_pe'], (int, float)) else "N/A"
            online_pe_str = f"{result['online_pe']:.2f}" if isinstance(result['online_pe'], (int, float)) else "N/A"
            
            pe_diff_t_str = f"{result['pe_diff_tushare']:.2f}" if isinstance(result['pe_diff_tushare'], (int, float)) else "N/A"
            pe_diff_o_str = f"{result['pe_diff_online']:.2f}" if isinstance(result['pe_diff_online'], (int, float)) else "N/A"
            
            agent_pb_str = f"{result['agent_pb']:.2f}" if isinstance(result['agent_pb'], (int, float)) else "N/A"
            online_pb_str = f"{result['online_pb']:.2f}" if isinstance(result['online_pb'], (int, float)) else "N/A"
            pb_diff_str = f"{result['pb_diff']:.2f}" if isinstance(result['pb_diff'], (int, float)) else "N/A"
            
            agent_score_str = f"{result['agent_score']:.1f}" if isinstance(result['agent_score'], (int, float)) else "N/A"
            
            pe_source = result['agent_pe_source']
            
            report.append(f"| {i} | {result['stock_code']} | {result['agent_name'][:8]} | {result['online_name'][:8]} | {name_match_str} | {agent_pe_str} | {pe_source} | {tushare_pe_str} | {online_pe_str} | {pe_diff_t_str} | {pe_diff_o_str} | {agent_pb_str} | {online_pb_str} | {pb_diff_str} | {agent_score_str} |")
        
        report.append("")
        
        # 数据质量分析
        report.append("## 🔍 Agent性能分析")
        
        agent_with_realtime_pe = sum(1 for r in results if r['agent_pe_source'] == 'realtime')
        agent_with_historical_pe = sum(1 for r in results if r['agent_pe_source'] == 'historical')
        
        report.append("### PE数据源分布")
        report.append(f"- 使用实时PE: {agent_with_realtime_pe}/{agent_success} ({agent_with_realtime_pe/agent_success*100:.1f}%)" if agent_success > 0 else "- 使用实时PE: 0")
        report.append(f"- 使用历史PE: {agent_with_historical_pe}/{agent_success} ({agent_with_historical_pe/agent_success*100:.1f}%)" if agent_success > 0 else "- 使用历史PE: 0")
        report.append("")
        
        # 评分分布
        scores = [r['agent_score'] for r in results if isinstance(r['agent_score'], (int, float))]
        if scores:
            avg_score = sum(scores) / len(scores)
            high_scores = sum(1 for s in scores if s >= 70)
            medium_scores = sum(1 for s in scores if 50 <= s < 70)
            
            report.append("### Agent评分分布")
            report.append(f"- 平均评分: {avg_score:.1f}")
            report.append(f"- 高分股票(≥70): {high_scores} 只")
            report.append(f"- 中等股票(50-69): {medium_scores} 只")
            report.append("")
        
        # 结论与建议
        report.append("## 🔍 结论与建议")
        
        if agent_success / total_stocks < 0.8:
            report.append("⚠️ **Agent分析成功率较低**，建议检查数据完整性和程序稳定性")
        else:
            report.append("✅ Agent分析成功率良好")
        
        if name_matches / total_stocks < 0.8:
            report.append("⚠️ **股票名称匹配率较低**，建议检查股票代码映射")
        else:
            report.append("✅ 股票名称匹配良好")
        
        if pe_tushare_available > 0:
            pe_diffs = [r['pe_diff_tushare'] for r in results if isinstance(r['pe_diff_tushare'], (int, float))]
            avg_pe_diff = sum(pe_diffs) / len(pe_diffs)
            if avg_pe_diff > 10:
                report.append("⚠️ **PE数据差异较大(vs Tushare)**，建议检查PE获取逻辑")
            elif avg_pe_diff > 5:
                report.append("📊 PE数据与Tushare存在一定差异，可能与数据更新时间有关")
            else:
                report.append("✅ PE数据与Tushare基本一致")
        
        if agent_with_realtime_pe / agent_success < 0.5 if agent_success > 0 else False:
            report.append("📊 **实时PE获取率较低**，建议优化实时数据获取策略")
        
        report.append("")
        report.append("---")
        report.append("*注：Agent使用的PE数据可能是实时获取或历史数据，与不同在线数据源存在差异是正常的。*")
        
        return "\n".join(report)

def main():
    logger.info("开始Agent结果验证测试")
    
    validator = AgentResultValidator()
    results = validator.run_validation(25)
    
    if results:
        report = validator.generate_report(results)
        
        # 保存报告
        report_file = f"Agent验证报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"验证完成，报告已保存到: {report_file}")
        
        # 输出简要结果
        print("\n" + "="*80)
        print("📊 Agent结果验证测试完成")
        print("="*80)
        print(f"验证样本: {len(results)} 只股票")
        
        agent_success = sum(1 for r in results if r['agent_success'])
        print(f"Agent成功分析: {agent_success}/{len(results)} ({agent_success/len(results)*100:.1f}%)")
        
        name_matches = sum(1 for r in results if r['name_match'])
        print(f"名称匹配: {name_matches}/{len(results)} ({name_matches/len(results)*100:.1f}%)")
        
        pe_tushare_available = sum(1 for r in results if isinstance(r['pe_diff_tushare'], (int, float)))
        if pe_tushare_available > 0:
            pe_diffs = [r['pe_diff_tushare'] for r in results if isinstance(r['pe_diff_tushare'], (int, float))]
            avg_pe_diff = sum(pe_diffs) / len(pe_diffs)
            print(f"PE数据对比(Tushare): {pe_tushare_available} 只，平均差异: {avg_pe_diff:.2f}")
        
        scores = [r['agent_score'] for r in results if isinstance(r['agent_score'], (int, float))]
        if scores:
            avg_score = sum(scores) / len(scores)
            print(f"平均评分: {avg_score:.1f}")
        
        print(f"\n📄 详细报告: {report_file}")
        print("="*80)
    else:
        logger.error("验证失败，无结果")

if __name__ == "__main__":
    main() 