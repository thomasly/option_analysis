#!/usr/bin/env python3
"""
斐波那契分析器
用于分析标的的斐波那契支撑位和阻力位
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

from .data_fetcher import DataFetcher
from src.config.config import AnalysisConfig


class FaboAnalyzer:
    """斐波那契分析器"""

    def __init__(
        self,
        stock_code="399006.SZ",
        years=15,
        output_dir="analysis_results",
        config=None,
    ):
        """
        初始化斐波那契分析器

        参数:
        stock_code: 股票代码
        years: 分析年数
        output_dir: 输出目录
        config: 分析配置
        """
        self.stock_code = stock_code
        self.years = years
        self.output_dir = output_dir
        self.data_fetcher = DataFetcher()
        self.config = config or AnalysisConfig()

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

    def _calculate_fibonacci_levels(self, high, low, trend):
        """
        计算斐波那契水平
        
        参数:
        high: 高点价格
        low: 低点价格
        trend: 趋势方向 ("up" 或 "down")
        
        返回:
        dict: 斐波那契水平字典
        """
        price_range = high - low
        fib_ratios = self.config.fibonacci.fib_ratios
        
        fib_levels = {}
        if trend == "down":
            # 下降趋势：计算反弹水平
            for ratio in fib_ratios:
                fib_levels[f"{ratio:.3f}"] = low + ratio * price_range
            # 添加0%和100%水平
            fib_levels["0.000"] = low
            fib_levels["1.000"] = high
        else:
            # 上升趋势：计算回撤水平
            for ratio in fib_ratios:
                fib_levels[f"{ratio:.3f}"] = high - ratio * price_range
            # 添加0%和100%水平
            fib_levels["0.000"] = high
            fib_levels["1.000"] = low
        
        return fib_levels
    
    def _plot_fibonacci_chart(self, df, high, low, trend, chart_type="resistance"):
        """
        绘制斐波那契分析图表
        
        参数:
        df: 标的数据
        high: 高点价格
        low: 低点价格
        trend: 趋势方向
        chart_type: 图表类型，"resistance"表示压力位，"support"表示支撑位
        
        返回:
        str: 图表保存路径
        """
        # 准备数据
        dates = pd.to_datetime(df["trade_date"])
        close_prices = df["close"]
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(16, 8))
        
        # 绘制收盘价曲线
        ax.plot(dates, close_prices, label="Close Prices", color="blue", linewidth=1.5)
        
        # 计算斐波那契水平
        fib_levels = self._calculate_fibonacci_levels(high, low, trend)
        
        # 定义颜色映射
        colors = {
            "0.000": "red",
            "0.236": "orange",
            "0.382": "black",
            "0.500": "green",
            "0.618": "blue",
            "0.786": "indigo",
            "1.000": "violet"
        }
        
        # 绘制斐波那契线
        for ratio, level in sorted(fib_levels.items(), key=lambda x: x[1], reverse=(trend == "up")):
            color = colors.get(ratio, "gray")
            ax.axhline(y=level, color=color, linestyle="--", alpha=0.7, linewidth=1)
            
            # 添加标签
            label = f"Fib {ratio}"
            ax.text(
                ax.get_xlim()[1] + 0.01,  # 图表右侧
                level,
                label,
                color=color,
                verticalalignment="center",
                fontsize=8,
                rotation=0
            )
        
        # 添加标题和标签（使用英文避免matplotlib乱码）
        chart_type_name = "Resistance" if chart_type == "resistance" else "Support"
        ax.set_title(f"{self.stock_code} Fibonacci {chart_type_name} Analysis", fontsize=16)
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Price", fontsize=12)
        
        # 设置日期格式
        ax.xaxis.set_major_locator(mdates.YearLocator(1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        plt.xticks(rotation=45)
        
        # 添加图例
        ax.legend()
        
        # 添加网格
        ax.grid(True, alpha=0.3)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图像
        timestamp = datetime.now().strftime("%Y%m%d")
        chart_type_label = "resistance" if chart_type == "resistance" else "support"
        output_path = os.path.join(
            self.output_dir,
            f"{timestamp}_{self.stock_code}_fibonacci_{chart_type_label}_analysis.png",
        )
        fig.savefig(output_path, dpi=200, bbox_inches="tight")
        print(f"Fibonacci {chart_type_name} chart saved to: {output_path}")
        
        # 关闭图表
        plt.close()
        
        return output_path
    
    def analyze(self):
        """
        执行斐波那契分析
        
        返回:
        dict: 分析结果，包含压力位和支撑位图表
        """
        print(f"\nStarting Fibonacci analysis for {self.stock_code}...")
        
        # 获取标的日线数据
        df = self.data_fetcher.fetch_index_data(
            index_code=self.stock_code, years=self.years, freq="D"
        )
        
        if df is None or df.empty:
            print(f"Unable to fetch data for {self.stock_code}")
            return None
        
        # 绘制压力位斐波那契图表
        resistance_high = self.config.fibonacci.resistance_high
        resistance_low = self.config.fibonacci.resistance_low
        resistance_trend = self.config.fibonacci.resistance_trend
        resistance_chart = self._plot_fibonacci_chart(df, resistance_high, resistance_low, resistance_trend, "resistance")
        
        # 绘制支撑位斐波那契图表
        support_low = self.config.fibonacci.support_low
        support_high = self.config.fibonacci.support_high
        support_trend = self.config.fibonacci.support_trend
        support_chart = self._plot_fibonacci_chart(df, support_high, support_low, support_trend, "support")
        
        # 构建分析结果
        result = {
            "stock_code": self.stock_code,
            "resistance_chart": resistance_chart,
            "resistance_high": resistance_high,
            "resistance_low": resistance_low,
            "resistance_trend": resistance_trend,
            "support_chart": support_chart,
            "support_low": support_low,
            "support_high": support_high,
            "support_trend": support_trend,
            "fib_ratios": self.config.fibonacci.fib_ratios
        }
        
        print(f"Fibonacci analysis completed for {self.stock_code}!")
        return result
    
    def print_analysis_result(self, result):
        """
        打印分析结果
        
        参数:
        result: 分析结果
        """
        print("\n" + "="*60)
        print("📐 斐波那契分析结果")
        print("="*60)
        
        print(f"\n标的代码: {result['stock_code']}")
        print(f"斐波那契比率: {', '.join([f'{ratio:.3f}' for ratio in result['fib_ratios']])}")
        
        # 打印压力位分析信息
        print(f"\n📈 压力位分析:")
        print(f"   高点价格: {result['resistance_high']}")
        print(f"   低点价格: {result['resistance_low']}")
        print(f"   趋势方向: {result['resistance_trend']}")
        print(f"   图表路径: {result['resistance_chart']}")
        
        # 打印支撑位分析信息
        print(f"\n📉 支撑位分析:")
        print(f"   低点价格: {result['support_low']}")
        print(f"   高点价格: {result['support_high']}")
        print(f"   趋势方向: {result['support_trend']}")
        print(f"   图表路径: {result['support_chart']}")
        
        print("\n" + "="*60)
    
    def generate_email_content(self, result):
        """
        生成邮件内容
        
        参数:
        result: 分析结果
        
        返回:
        str: HTML格式的邮件内容
        """
        html_content = f"""
        <div class="analysis-section" style="font-size: 16px; line-height: 1.6;">
            <h2 style="font-size: 20px; margin-bottom: 20px;">📊 斐波那契分析</h2>
            <div style="margin-bottom: 20px;">
                <h3 style="font-size: 18px; margin-bottom: 10px;">分析参数</h3>
                <p>标的代码: <strong>{result['stock_code']}</strong></p>
                <p>斐波那契比率: <strong>{', '.join([f'{ratio:.3f}' for ratio in result['fib_ratios']])}</strong></p>
            </div>
            
            <div style="margin-bottom: 20px;">
                <h3 style="font-size: 18px; margin-bottom: 10px;">📈 压力位分析</h3>
                <p>高点价格: <strong>{result['resistance_high']}</strong></p>
                <p>低点价格: <strong>{result['resistance_low']}</strong></p>
                <p>趋势方向: <strong>{result['resistance_trend']}</strong></p>
            </div>
            
            <div style="margin-bottom: 20px;">
                <h3 style="font-size: 18px; margin-bottom: 10px;">📉 支撑位分析</h3>
                <p>低点价格: <strong>{result['support_low']}</strong></p>
                <p>高点价格: <strong>{result['support_high']}</strong></p>
                <p>趋势方向: <strong>{result['support_trend']}</strong></p>
            </div>
        </div>
        """
        
        return html_content


def main():
    """主函数"""
    analyzer = FaboAnalyzer(stock_code="399006.SZ", years=15)
    result = analyzer.analyze()
    if result:
        analyzer.print_analysis_result(result)


if __name__ == "__main__":
    main()
