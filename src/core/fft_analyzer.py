import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import dotenv
from matplotlib.dates import AutoDateLocator
from scipy.fft import fft, ifft

from .data_fetcher import DataFetcher
from .font_config import setup_chinese_font


class FFTAnalyzer:
    """FFT分析器类，用于股票数据的傅里叶变换分析"""

    def __init__(self, stock_code="399006.SZ", years=15, num_components=6):
        """
        初始化FFT分析器

        Args:
            stock_code (str): 股票代码，默认为创业板指数
            years (int): 分析的年数，默认15年
            num_components (int): 傅里叶分析的主要成分数量，默认6个
        """
        self.stock_code = stock_code
        self.years = years
        self.num_components = num_components
        self.data_fetcher = DataFetcher()
        self.output_dir = None

        # 初始化环境
        self._configure_plot_settings()
        self._setup_directories()

    def _configure_plot_settings(self):
        """配置图表显示设置"""
        # 使用跨平台字体配置
        setup_chinese_font()

    def _setup_directories(self):
        """设置输出目录"""
        # 获取项目根目录（analysis_module目录）
        current_dir = os.path.dirname(__file__)  # src/core
        project_root = os.path.dirname(
            os.path.dirname(current_dir)
        )  # analysis_module目录

        self.output_dir = os.path.join(project_root, "analysis_results")
        os.makedirs(self.output_dir, exist_ok=True)

    def fetch_data(self, freq="W"):
        """
        获取并缓存数据

        Args:
            freq (str): 数据频率，"D"为日线，"W"为周线

        Returns:
            pd.DataFrame: 处理后的数据
        """
        return self.data_fetcher.fetch_index_data(
            index_code=self.stock_code, years=self.years, freq=freq
        )

    def generate_combined_analysis(self, df, freq_label):
        """生成综合趋势分析图"""
        # 计算线性趋势
        dates = df["trade_date"].map(lambda x: x.toordinal())
        close_prices = df["close"].values
        slope, intercept = np.polyfit(dates, close_prices, 1)
        linear_trend = slope * dates + intercept

        # 计算周期成分
        residuals = close_prices - linear_trend
        n = len(residuals)
        fft_vals = fft(residuals)
        freqs = np.fft.fftfreq(n)
        amplitudes = np.abs(fft_vals)
        top_indices = np.argsort(amplitudes)[-self.num_components :]

        # 重建周期信号
        filtered_fft = np.zeros_like(fft_vals)
        valid_indices = [i for i in top_indices if i != 0]
        for i in valid_indices:
            if i <= n // 2:
                filtered_fft[i] = fft_vals[i]
                filtered_fft[-i] = fft_vals[-i]
        cycles = np.real(ifft(filtered_fft))
        cycles -= np.mean(cycles)

        # 合成最终预测
        combined = linear_trend + cycles

        # 可视化
        plt.figure(figsize=(14, 8))

        # 绘制原始价格
        plt.plot(
            df["trade_date"],
            close_prices,
            label="Actual Price",
            color="navy",
            linewidth=2,
            alpha=0.8,
        )

        # 绘制综合预测
        plt.plot(
            df["trade_date"],
            combined,
            label=f"Combined Forecast ({self.num_components} Components)",
            color="crimson",
            linestyle="--",
            linewidth=2,
        )

        # 分解显示各成分
        plt.plot(
            df["trade_date"],
            linear_trend,
            label="Linear Trend",
            color="darkgreen",
            alpha=0.6,
        )

        # 设置图表格式
        plt.title(f"{self.stock_code} {freq_label} Trend Analysis")
        plt.xlabel("Date")
        plt.ylabel("Price")
        ax = plt.gca()
        ax.xaxis.set_major_locator(AutoDateLocator(maxticks=12))
        plt.xticks(rotation=35, ha="right")
        plt.legend(loc="upper left")
        plt.grid(alpha=0.2)
        plt.tight_layout()

        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d")
        output_path = os.path.join(
            self.output_dir,
            f"{timestamp}_{self.stock_code}_{freq_label}_combined_analysis.png",
        )
        plt.savefig(output_path, dpi=200, bbox_inches="tight")
        plt.close()
        print(f"已生成综合趋势分析图：{output_path}")

    def analyze(self, frequencies=None):
        """
        执行完整的分析流程

        Args:
            frequencies (list): 要分析的频率列表，默认为["D", "W"]（日线和周线）
        """
        if frequencies is None:
            frequencies = [("D", "Daily"), ("W", "Weekly")]

        for freq, freq_label in frequencies:
            print(f"\n开始分析 {freq_label} 数据...")

            # 获取数据
            df = self.fetch_data(freq=freq)

            # 创建频率子目录
            freq_output_dir = os.path.join(self.output_dir, freq)
            os.makedirs(freq_output_dir, exist_ok=True)

            # 临时修改输出目录
            original_output_dir = self.output_dir
            self.output_dir = freq_output_dir

            # 只执行综合趋势分析
            self.generate_combined_analysis(df, freq_label)

            # 恢复原始输出目录
            self.output_dir = original_output_dir

            # 打印数据信息
            print(f"\n{freq_label}数据摘要:")
            print(
                f"时间范围: {df['trade_date'].min().date()} 至 {df['trade_date'].max().date()}"
            )
            print(f"总数据量: {len(df)} 条")

    def get_data_info(self, freq="W"):
        """
        获取数据信息

        Args:
            freq (str): 数据频率

        Returns:
            dict: 数据信息字典
        """
        df = self.fetch_data(freq=freq)
        return {
            "stock_code": self.stock_code,
            "frequency": freq,
            "start_date": df["trade_date"].min().date(),
            "end_date": df["trade_date"].max().date(),
            "total_records": len(df),
            "price_range": {
                "min": df["close"].min(),
                "max": df["close"].max(),
                "mean": df["close"].mean(),
            },
        }


# --------------------------
# 主函数（保持向后兼容）
# --------------------------
def main():
    """主函数，保持向后兼容性"""
    analyzer = FFTAnalyzer()
    analyzer.analyze()


if __name__ == "__main__":
    main()
