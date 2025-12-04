#!/usr/bin/env python3
"""
外汇汇率分析器
获取主要外汇对人民币的历史数据，进行分析和可视化
"""

import logging
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import tushare as ts

# 初始化Tushare Pro API
TUSHARE_TOKEN = "31027a741637467ff31f65faada254d6306a66f966063cefdcef9b40"
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()


class FxAnalyzer:
    """外汇汇率分析器"""
    
    def __init__(self, years: int = 5):
        """
        初始化外汇汇率分析器
        
        Args:
            years: 分析的历史数据年限
        """
        self.years = years
        self.data = None
        self.result_df = None
        
        # 定义要获取的主要外汇对
        self.major_pairs = {
            'USDCNH.FXCM': '美元兑人民币',
            'EURUSD.FXCM': '欧元兑美元',
            'GBPUSD.FXCM': '英镑兑美元',
            'AUDUSD.FXCM': '澳元兑美元',
            'NZDUSD.FXCM': '新西兰元兑美元',
            'USDJPY.FXCM': '美元兑日元'
        }
        
        # 创建分析结果目录
        self.analysis_dir = "analysis_results"
        os.makedirs(self.analysis_dir, exist_ok=True)
    
    def _fetch_fx_data(self):
        """获取外汇历史数据"""
        logging.info("获取外汇历史数据...")
        
        # 设置时间范围
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=365*self.years)).strftime("%Y%m%d")
        
        logging.info(f"时间范围：{start_date} 到 {end_date}")
        
        # 用于存储所有货币对的历史数据
        fx_data = {}
        
        # 获取每个货币对的历史数据
        for pair_code, pair_name in self.major_pairs.items():
            logging.info(f"获取 {pair_name} ({pair_code}) 的历史数据...")
            try:
                # 使用 fx_daily 接口获取历史数据
                df = pro.query('fx_daily', ts_code=pair_code, start_date=start_date, end_date=end_date)
                
                if not df.empty:
                    # 将日期转换为 datetime 类型
                    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
                    # 按日期排序
                    df = df.sort_values('trade_date')
                    # 重置索引
                    df = df.reset_index(drop=True)
                    # 仅保留需要的列
                    df = df[['trade_date', 'bid_close']]
                    # 重命名 bid_close 列为对应的货币对名称
                    df.rename(columns={'bid_close': pair_code.split('.')[0]}, inplace=True)
                    
                    fx_data[pair_code] = df
                    logging.info(f"获取到 {len(df)} 条数据")
                else:
                    logging.warning(f"未获取到 {pair_name} ({pair_code}) 的数据")
                    
            except Exception as e:
                logging.error(f"获取 {pair_name} ({pair_code}) 数据失败: {e}")
        
        # 合并所有数据到一个共同的日期索引
        logging.info("合并所有数据到共同的日期索引...")
        
        # 首先获取美元兑离岸人民币数据，作为基础
        if 'USDCNH.FXCM' in fx_data:
            base_df = fx_data['USDCNH.FXCM'][['trade_date', 'USDCNH']]
            
            # 依次合并其他货币对数据
            for pair_code, df in fx_data.items():
                if pair_code != 'USDCNH.FXCM':
                    base_df = base_df.merge(df, on='trade_date', how='outer')
            
            # 按日期排序
            base_df = base_df.sort_values('trade_date')
            # 重置索引
            base_df = base_df.reset_index(drop=True)
            
            logging.info(f"合并后的数据行数: {len(base_df)}")
            
            self.data = base_df
        else:
            logging.error("未获取到美元兑人民币数据，无法继续分析")
            self.data = None
    
    def _calculate_cny_rates(self):
        """计算所有主要外汇对人民币的汇率"""
        if self.data is None:
            logging.error("没有数据可用于计算汇率")
            return
        
        logging.info("计算所有主要外汇对人民币的汇率...")
        
        # 计算逻辑：
        # 外汇对人民币 = 外汇对美元 * 美元兑人民币
        # 日元特殊：日元兑人民币 = 1 / 美元兑日元 * 美元兑人民币
        
        # 计算欧元兑人民币
        self.data['EURCNH'] = self.data['EURUSD'] * self.data['USDCNH']
        
        # 计算英镑兑人民币
        self.data['GBPCNH'] = self.data['GBPUSD'] * self.data['USDCNH']
        
        # 计算澳元兑人民币
        self.data['AUDCNH'] = self.data['AUDUSD'] * self.data['USDCNH']
        
        # 计算新西兰元兑人民币
        self.data['NZDCNH'] = self.data['NZDUSD'] * self.data['USDCNH']
        
        # 计算日元兑人民币
        self.data['JPYCNH'] = (1 / self.data['USDJPY']) * self.data['USDCNH']
        
        # 筛选需要保存和可视化的列
        result_columns = ['trade_date', 'USDCNH', 'EURCNH', 'GBPCNH', 'AUDCNH', 'NZDCNH', 'JPYCNH']
        self.result_df = self.data[result_columns].dropna()
        
        logging.info(f"筛选后的数据行数: {len(self.result_df)}")
    
    def _generate_plot(self):
        """生成外汇汇率历史走势图"""
        if self.result_df is None:
            logging.error("没有数据可用于生成图表")
            return
        
        logging.info("生成主要外汇对人民币汇率历史走势图...")
        
        # 选择要绘制的列和对应的标签
        columns_to_plot = {
            'USDCNH': 'USD to CNY',
            'EURCNH': 'EUR to CNY',
            'GBPCNH': 'GBP to CNY',
            'AUDCNH': 'AUD to CNY',
            'NZDCNH': 'NZD to CNY',
            'JPYCNH': 'JPY to CNY (×100)'
        }
        
        # 创建图表
        plt.figure(figsize=(15, 8))
        
        # 为每个外汇对绘制折线图
        colors = ['blue', 'green', 'red', 'orange', 'purple', 'brown']
        for i, (col, label) in enumerate(columns_to_plot.items()):
            if col == 'JPYCNH':
                # 将日元对人民币的汇率乘以100，使其与其他汇率在同一数量级
                plt.plot(self.result_df['trade_date'], self.result_df[col] * 100, label=label, color=colors[i], linewidth=2)
            else:
                plt.plot(self.result_df['trade_date'], self.result_df[col], label=label, color=colors[i], linewidth=2)
        
        # 添加图表元素
        plt.title('Major Foreign Exchange Rates vs CNY History', fontsize=16)
        plt.xlabel('Date', fontsize=14)
        plt.ylabel('Exchange Rate', fontsize=14)
        plt.legend(fontsize=12, loc='best')
        plt.grid(True, alpha=0.3)
        
        # 设置x轴日期格式
        plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m'))
        plt.gca().xaxis.set_major_locator(plt.matplotlib.dates.YearLocator())
        plt.xticks(rotation=45)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图表到文件
        plot_path = os.path.join(self.analysis_dir, 'fx_cny_history_plot.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        logging.info(f"图表已保存到 {plot_path} 文件")
        
        # 关闭图表，释放资源
        plt.close()
        
        return plot_path
    
    def _calculate_statistics(self):
        """计算外汇汇率的统计信息"""
        if self.result_df is None:
            logging.error("没有数据可用于计算统计信息")
            return None
        
        logging.info("计算外汇汇率的统计信息...")
        
        # 选择要计算统计信息的列和对应的标签
        columns_to_plot = {
            'USDCNH': 'USD to CNY',
            'EURCNH': 'EUR to CNY',
            'GBPCNH': 'GBP to CNY',
            'AUDCNH': 'AUD to CNY',
            'NZDCNH': 'NZD to CNY',
            'JPYCNH': 'JPY to CNY'
        }
        
        # 计算每个外汇对的统计信息
        statistics = {}
        for col, label in columns_to_plot.items():
            stats = self.result_df[col].describe()
            statistics[label] = {
                'mean': stats['mean'],
                'median': stats['50%'],
                'min': stats['min'],
                'max': stats['max'],
                'std': stats['std']
            }
        
        # 添加数据时间范围信息
        time_range = {
            'start_date': self.result_df['trade_date'].min().strftime('%Y-%m-%d'),
            'end_date': self.result_df['trade_date'].max().strftime('%Y-%m-%d'),
            'total_rows': len(self.result_df)
        }
        
        return {
            'time_range': time_range,
            'statistics': statistics
        }
    
    def analyze(self):
        """
        执行完整的外汇汇率分析
        
        Returns:
            dict: 包含分析结果和统计信息
        """
        logging.info("开始外汇汇率分析...")
        
        # 获取外汇数据
        self._fetch_fx_data()
        
        # 计算外汇对人民币的汇率
        self._calculate_cny_rates()
        
        # 生成图表
        plot_path = self._generate_plot()
        
        # 计算统计信息
        statistics = self._calculate_statistics()
        
        # 构建分析结果
        result = {
            'plot_path': plot_path,
            'statistics': statistics
        }
        
        logging.info("外汇汇率分析完成！")
        
        return result
    
    def print_analysis_result(self, result):
        """
        打印分析结果
        
        Args:
            result: 分析结果字典
        """
        print("\n" + "="*60)
        print("📊 外汇汇率分析结果")
        print("="*60)
        
        # 打印数据时间范围
        print("\n1. 数据时间范围：")
        time_range = result['statistics']['time_range']
        print(f"   起始日期: {time_range['start_date']}")
        print(f"   结束日期: {time_range['end_date']}")
        print(f"   总数据行数: {time_range['total_rows']}")
        
        # 打印统计信息
        print("\n2. 各外汇对统计信息：")
        for currency, stats in result['statistics']['statistics'].items():
            print(f"\n   {currency}:")
            print(f"      均值: {stats['mean']:.4f}")
            print(f"      中位数: {stats['median']:.4f}")
            print(f"      最小值: {stats['min']:.4f}")
            print(f"      最大值: {stats['max']:.4f}")
            print(f"      标准差: {stats['std']:.4f}")
        
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
            stats_html = f"""
            <h3 style="font-size: 18px; margin-top: 20px;">1. 数据时间范围</h3>
            <p style="font-size: 16px; margin: 8px 0;">起始日期: <strong>{result['statistics']['time_range']['start_date']}</strong></p>
            <p style="font-size: 16px; margin: 8px 0;">结束日期: <strong>{result['statistics']['time_range']['end_date']}</strong></p>
            <p style="font-size: 16px; margin: 8px 0;">总数据行数: <strong>{result['statistics']['time_range']['total_rows']}</strong></p>
            
            <h3 style="font-size: 18px; margin-top: 20px;">2. 各外汇对统计信息</h3>
            <div style="overflow-x: auto; margin: 10px 0;">
                <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; max-width: 100%; font-size: 14px;">
                    <tr style="background-color: #f2f2f2;">
                        <th style="white-space: nowrap; padding: 10px; text-align: center;">货币对</th>
                        <th style="white-space: nowrap; padding: 10px; text-align: center;">均值</th>
                        <th style="white-space: nowrap; padding: 10px; text-align: center;">中位数</th>
                        <th style="white-space: nowrap; padding: 10px; text-align: center;">最小值</th>
                        <th style="white-space: nowrap; padding: 10px; text-align: center;">最大值</th>
                        <th style="white-space: nowrap; padding: 10px; text-align: center;">标准差</th>
                    </tr>
            """
            
            for currency, stats in result['statistics']['statistics'].items():
                stats_html += f"""
                    <tr>
                        <td style="padding: 8px; text-align: center;">{currency}</td>
                        <td style="padding: 8px; text-align: center;">{stats['mean']:.4f} </td>
                        <td style="padding: 8px; text-align: center;">{stats['median']:.4f} </td>
                        <td style="padding: 8px; text-align: center;">{stats['min']:.4f} </td>
                        <td style="padding: 8px; text-align: center;">{stats['max']:.4f} </td>
                        <td style="padding: 8px; text-align: center;">{stats['std']:.4f} </td>
                    </tr>
                """
            
            stats_html += f"""
                </table>
            </div>
            """
        
        # 组合完整的HTML内容
        html_content = f"""
        <div class="analysis-section" style="font-size: 16px; line-height: 1.6;">
            <h2 style="font-size: 20px; margin-bottom: 20px;">💱 外汇汇率分析</h2>
            {stats_html}
        </div>
        """
        
        return html_content


if __name__ == "__main__":
    analyzer = FxAnalyzer(years=5)
    result = analyzer.analyze()
    analyzer.print_analysis_result(result)
