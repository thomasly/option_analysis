#!/usr/bin/env python3
"""
时变谐波函数分析器
使用多个时变谐波函数对时间序列数据进行拟合
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from scipy.optimize import curve_fit

from .data_fetcher import DataFetcher

# from .font_config import setup_chinese_font


class HarmonicAnalyzer:
    """时变谐波函数分析器"""

    def __init__(
        self,
        stock_code="399006.SZ",
        years=15,
        output_dir="analysis_results",
    ):
        """
        初始化谐波分析器

        参数:
        stock_code: 股票代码
        years: 分析年数
        num_harmonics: 谐波函数数量
        output_dir: 输出目录
        """
        self.stock_code = stock_code
        self.years = years
        self.output_dir = output_dir
        self.data_fetcher = DataFetcher()
        self.weekly_p0 = [2, 0.5, 500, 0.02, np.pi, 1000]
        self.daily_p0 = [0.43, 0.1, 1000, 0.003, np.pi / 3 * 2, 1084]  # 拟合初始值

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 设置中文字体
        # setup_chinese_font()

    def objective_function(self, x, a, b, c, k, q, d):
        """
        目标函数
        """
        return a * x + (b * x + c) * np.sin(k * x + q) + d

    def _plot_harmonic_fit(self, params, df, offset=100):
        """绘制谐波拟合结果"""

        fig, axes = plt.subplots(2, 1, figsize=(16, 12))

        x = np.linspace(0, len(df), len(df))
        x1 = np.linspace(0, len(df) + offset, len(df) + offset)
        y = df.close
        y1 = self.objective_function(x1, *params)

        # 子图1：完整拟合结果
        axes[0].plot(x, y, label="Close prices")
        axes[0].plot(x1, y1, label="fit")
        axes[0].legend()
        axes[0].tick_params(labelbottom=False)
        xmin, xmax = axes[0].get_xlim()
        # axes[0].title("Price trend prediction")

        # 子图2：残差分析
        diffs = y - y1[:-offset]
        axes[1].plot(x, diffs)
        mean_diff = np.mean(diffs)
        std_diff = np.std(diffs)
        axes[1].set_xlim(xmin, xmax)
        axes[1].set_xlabel("x")
        axes[1].set_ylabel("diff")
        # axes[1].title("Differences between prices and fit")
        axes[1].text(
            0.04 * len(x),  # x coordinate (5% of x-axis)
            max(diffs),  # y coordinate (top of diffs)
            f"mean: {mean_diff:.4f}\nstd: {std_diff:.4f}",
            fontsize=10,
            verticalalignment="top",
            bbox=dict(facecolor="white", alpha=0.6, edgecolor="none"),
        )

        # fig.tight_layout()

        # 保存图像
        timestamp = datetime.now().strftime("%Y%m%d")
        output_path = os.path.join(
            self.output_dir, f"{timestamp}_{self.stock_code}_harmonic_analysis.png"
        )
        fig.savefig(output_path, dpi=200, bbox_inches="tight")
        print(f"Harmonic analysis chart saved to: {output_path}")

    def analyze(self, frequencies=None):
        """
        执行完整的谐波分析

        参数:
        frequencies: 要分析的频率列表
        """
        if frequencies is None:
            frequencies = [("D", "Daily"), ("W", "Weekly")]

        for freq, freq_label in frequencies:
            print(f"\nStarting harmonic analysis for {freq_label} data...")

            # 获取数据
            df = self.data_fetcher.fetch_index_data(
                index_code=self.stock_code, years=self.years, freq=freq
            )

            if df is None or df.empty:
                print(f"Unable to fetch {freq_label} data")
                continue

            # 创建频率子目录
            freq_output_dir = os.path.join(self.output_dir, freq)
            os.makedirs(freq_output_dir, exist_ok=True)

            # 临时修改输出目录
            original_output_dir = self.output_dir
            self.output_dir = freq_output_dir

            # 执行谐波拟合
            x = np.linspace(0, len(df), len(df))
            y = df.close

            if freq == "W":
                p0 = self.weekly_p0
                offset = 100
            else:
                p0 = self.daily_p0
                offset = 500
            params, _ = curve_fit(self.objective_function, x, y, p0=p0)
            a, b, c, k, q, d = params
            self._plot_harmonic_fit(params, df, offset=offset)
            print(f"\n{freq_label} harmonic analysis completed!")
            print(
                f"Analysis result: {a:.2f} * x + ({b:.2f} * x + {c:.2f}) * "
                f"sin({k:.4f} * x + {q:.2f}) + {d:.2f}"
            )

            # 恢复原始输出目录
            self.output_dir = original_output_dir


def main():
    """主函数"""
    analyzer = HarmonicAnalyzer(stock_code="399006.SZ", years=15)
    analyzer.analyze()


if __name__ == "__main__":
    main()
