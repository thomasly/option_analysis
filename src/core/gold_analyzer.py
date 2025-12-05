#!/usr/bin/env python3
"""
黄金现货价格分析器
获取上海黄金交易所现货合约日线行情，进行分析和可视化
"""

import logging
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

from .data_fetcher import DataFetcher


class GoldAnalyzer:
    """黄金现货价格分析器"""
    
    def __init__(self, years: int = 5):
        """
        初始化黄金现货价格分析器
        
        Args:
            years: 分析的历史数据年限
        """
        self.years = years
        self.data = None
        self.result_dict = None
        self.data_fetcher = DataFetcher()
        
        # 定义要获取的主要黄金合约 - 只保留Au99.99
        self.major_contracts = {
            'Au99.99': '黄金99.99'
        }
        
        # 创建分析结果目录
        self.analysis_dir = "analysis_results"
        os.makedirs(self.analysis_dir, exist_ok=True)
    
    def _fetch_gold_data(self):
        """获取黄金现货历史数据"""
        logging.info("获取黄金现货历史数据...")
        
        # 用于存储所有黄金合约的历史数据
        gold_data = {}
        
        # 获取每个黄金合约的历史数据
        for contract_code, contract_name in self.major_contracts.items():
            logging.info(f"获取 {contract_name} ({contract_code}) 的历史数据...")
            try:
                # 使用 DataFetcher 获取黄金数据
                df = self.data_fetcher.fetch_gold_data(
                    ts_code=contract_code,
                    years=self.years
                )
                
                if not df.empty:
                    # 仅保留需要的列
                    df = df[['trade_date', 'close', 'open', 'high', 'low', 'vol']]
                    gold_data[contract_code] = df
                    logging.info(f"获取到 {len(df)} 条数据")
                else:
                    logging.warning(f"未获取到 {contract_name} ({contract_code}) 的数据")
                    
            except Exception as e:
                logging.error(f"获取 {contract_name} ({contract_code}) 数据失败: {e}")
        
        self.data = gold_data
    
    def _generate_plot(self):
        """生成黄金现货价格历史走势图"""
        if not self.data:
            logging.error("没有数据可用于生成图表")
            return
        
        logging.info("生成黄金现货价格历史走势图...")
        
        # 创建图表
        plt.figure(figsize=(15, 8))
        
        # 为Au99.99合约绘制折线图
        contract_code = 'Au99.99'
        df = self.data[contract_code]
        if 'close' in df.columns:
            # 计算10000人民币等价的黄金克数：10000 / 黄金价格（元/克）
            equivalent_gold = 10000 / df['close']
            plt.plot(df['trade_date'], equivalent_gold, 
                    label='Au99.99', 
                    color='gold', 
                    linewidth=2)
        
        # 添加图表元素（使用英文）
        plt.title('Historical Trend of Shanghai Gold Exchange Spot Contract', fontsize=16)
        plt.xlabel('Date', fontsize=14)
        plt.ylabel('Gold Weight per 10,000 CNY (grams)', fontsize=14)
        plt.legend(fontsize=12, loc='best')
        plt.grid(True, alpha=0.3)
        
        # 设置x轴日期格式
        plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m'))
        plt.gca().xaxis.set_major_locator(plt.matplotlib.dates.YearLocator())
        plt.xticks(rotation=45)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图表到文件
        plot_path = os.path.join(self.analysis_dir, 'gold_price_history_plot.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        logging.info(f"黄金价格走势图已保存到 {plot_path} 文件")
        
        # 关闭图表，释放资源
        plt.close()
        
        return plot_path
    
    def _calculate_statistics(self):
        """计算黄金价格的统计信息"""
        if not self.data:
            logging.error("没有数据可用于计算统计信息")
            return None
        
        logging.info("计算黄金价格的统计信息...")
        
        # 计算每个黄金合约的统计信息
        statistics = {}
        for contract_code, df in self.data.items():
            if 'close' in df.columns:
                contract_name = self.major_contracts[contract_code]
                stats = df['close'].describe()
                statistics[contract_name] = {
                    'mean': stats['mean'],
                    'median': stats['50%'],
                    'min': stats['min'],
                    'max': stats['max'],
                    'std': stats['std']
                }
        
        # 添加数据时间范围信息
        time_range = {}
        for contract_code, df in self.data.items():
            if 'trade_date' in df.columns and not df.empty:
                contract_name = self.major_contracts[contract_code]
                time_range[contract_name] = {
                    'start_date': df['trade_date'].min().strftime('%Y-%m-%d'),
                    'end_date': df['trade_date'].max().strftime('%Y-%m-%d'),
                    'total_rows': len(df)
                }
        
        return {
            'time_range': time_range,
            'statistics': statistics
        }
    
    def analyze(self):
        """
        执行完整的黄金现货价格分析
        
        Returns:
            dict: 包含分析结果和统计信息
        """
        logging.info("开始黄金现货价格分析...")
        
        # 获取黄金数据
        self._fetch_gold_data()
        
        # 生成图表
        plot_path = self._generate_plot()
        
        # 计算统计信息
        statistics = self._calculate_statistics()
        
        # 构建分析结果
        result = {
            'plot_path': plot_path,
            'statistics': statistics
        }
        
        logging.info("黄金现货价格分析完成！")
        
        return result
    
    def print_analysis_result(self, result):
        """
        打印分析结果
        
        Args:
            result: 分析结果字典
        """
        print("\n" + "="*60)
        print("📊 黄金现货价格分析结果")
        print("="*60)
        
        # 打印数据时间范围
        print("\n1. 数据时间范围：")
        for contract_name, time_info in result['statistics']['time_range'].items():
            print(f"   {contract_name}:")
            print(f"      起始日期: {time_info['start_date']}")
            print(f"      结束日期: {time_info['end_date']}")
            print(f"      总数据行数: {time_info['total_rows']}")
        
        # 打印统计信息
        print("\n2. 各黄金合约统计信息：")
        for contract_name, stats in result['statistics']['statistics'].items():
            print(f"\n   {contract_name}:")
            print(f"      均值: {stats['mean']:.2f} 元/克")
            print(f"      中位数: {stats['median']:.2f} 元/克")
            print(f"      最小值: {stats['min']:.2f} 元/克")
            print(f"      最大值: {stats['max']:.2f} 元/克")
            print(f"      标准差: {stats['std']:.2f} 元/克")
        
        # 打印图表保存路径
        print(f"\n3. 图表保存路径：")
        print(f"   {result['plot_path']}")
        
        print("\n" + "="*60)
    
    def generate_email_content(self, result):
        """
        生成邮件内容
        
        Args:
            result: 分析结果字典
            
        Returns:
            str: HTML格式的邮件内容
        """
        # 生成统计信息的HTML
        stats_html = ""
        if result['statistics']:
            stats_html = """
            <h3 style="font-size: 18px; margin-top: 20px;">1. 数据时间范围</h3>
            <div style="margin: 10px 0;">
            """
            
            for contract_name, time_info in result['statistics']['time_range'].items():
                stats_html += f"""
                <p style="font-size: 16px; margin: 5px 0;"><strong>{contract_name}</strong>: {time_info['start_date']} 至 {time_info['end_date']} ({time_info['total_rows']} 条记录)</p>
                """
            
            stats_html += """
            </div>
            
            <h3 style="font-size: 18px; margin-top: 20px;">2. 各黄金合约统计信息</h3>
            <div style="overflow-x: auto; margin: 10px 0;">
                <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; max-width: 100%; font-size: 14px;">
                    <tr style="background-color: #f2f2f2;">
                        <th style="white-space: nowrap; padding: 10px; text-align: center;">黄金合约</th>
                        <th style="white-space: nowrap; padding: 10px; text-align: center;">均值 (元/克)</th>
                        <th style="white-space: nowrap; padding: 10px; text-align: center;">中位数 (元/克)</th>
                        <th style="white-space: nowrap; padding: 10px; text-align: center;">最小值 (元/克)</th>
                        <th style="white-space: nowrap; padding: 10px; text-align: center;">最大值 (元/克)</th>
                        <th style="white-space: nowrap; padding: 10px; text-align: center;">标准差</th>
                    </tr>
            """
            
            for contract_name, stats in result['statistics']['statistics'].items():
                stats_html += f"""
                    <tr>
                        <td style="padding: 8px; text-align: center;">{contract_name}</td>
                        <td style="padding: 8px; text-align: center;">{stats['mean']:.2f} </td>
                        <td style="padding: 8px; text-align: center;">{stats['median']:.2f} </td>
                        <td style="padding: 8px; text-align: center;">{stats['min']:.2f} </td>
                        <td style="padding: 8px; text-align: center;">{stats['max']:.2f} </td>
                        <td style="padding: 8px; text-align: center;">{stats['std']:.2f} </td>
                    </tr>
                """
            
            stats_html += """
                </table>
            </div>
            """
        
        # 组合完整的HTML内容
        html_content = f"""
        <div class="analysis-section" style="font-size: 16px; line-height: 1.6;">
            <h2 style="font-size: 20px; margin-bottom: 20px;">✨ 黄金现货价格分析</h2>
            {stats_html}
        </div>
        """
        
        return html_content


if __name__ == "__main__":
    analyzer = GoldAnalyzer(years=5)
    result = analyzer.analyze()
    analyzer.print_analysis_result(result)