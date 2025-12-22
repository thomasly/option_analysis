#!/usr/bin/env python3
"""
时变谐波函数分析器
使用多个时变谐波函数对时间序列数据进行拟合
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from scipy.optimize import curve_fit
from scipy.stats import percentileofscore

from .data_fetcher import DataFetcher

# from .font_config import setup_chinese_font


class HarmonicAnalyzer:
    """时变谐波函数分析器"""

    def __init__(
        self,
        stock_code="399006.SZ",
        years=14,
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
        self.daily_p0 = [0.44, -0.06, -592.09, 0.0045, 0.43, 1303.89]  # 拟合初始值

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 设置中文字体
        # setup_chinese_font()

    def objective_function(self, x, a, b, c, k, q, d):
        """
        目标函数
        """
        return a * x + (b * x + c) * np.sin(k * x + q) + d

    def _prepare_plot_data(self, params, df, offset, freq):
        """计算绘图所需的序列与统计指标"""
        x = np.linspace(0, len(df), len(df))
        x1 = np.linspace(0, len(df) + offset, len(df) + offset)
        y = df.close
        y1 = self.objective_function(x1, *params)

        dates = pd.to_datetime(df["trade_date"])

        # 添加额外的天数，用于画拟合的曲线图
        extra = len(x1) - len(df)
        future_dates = pd.date_range(
            start=dates.iloc[-1] + pd.Timedelta(days=1),  # 或 freq='W'
            periods=extra,
            freq=freq,  # 根据数据频率改成 'W', 'B' 等
        )

        full_dates = pd.concat(
            [dates, pd.Series(future_dates)],
            ignore_index=True,
        )

        diffs = y - y1[:-offset]
        curr_diff = diffs.iloc[-1]
        percentile = percentileofscore(diffs, curr_diff, kind="rank")
        mean_diff = np.mean(diffs)
        std_diff = np.std(diffs)

        return {
            "dates": dates,
            "full_dates": full_dates,
            "y": y,
            "y1": y1,
            "diffs": diffs,
            "stats": {
                "mean": mean_diff,
                "std": std_diff,
                "curr": curr_diff,
                "percentile": percentile,
            },
        }

    def _plot_harmonic_fit(self, params, df, offset=100, freq="D"):
        """绘制谐波拟合结果"""

        data = self._prepare_plot_data(params, df, offset, freq)
        dates = data["dates"]
        full_dates = data["full_dates"]
        y = data["y"]
        y1 = data["y1"]
        diffs = data["diffs"]
        stats = data["stats"]

        fig, axes = plt.subplots(2, 1, figsize=(16, 12))
        fig.subplots_adjust(hspace=0.15)

        # 子图1：完整拟合结果
        axes[0].plot(dates, y, label="Close prices")
        axes[0].plot(full_dates, y1, label="fit")
        axes[0].legend()
        axes[0].xaxis.set_major_locator(mdates.YearLocator(1))
        axes[0].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        axes[0].set_ylabel(f"{self.stock_code} index")
        xmin, xmax = axes[0].get_xlim()
        # axes[0].title("Price trend prediction")

        # 子图2：残差分析
        axes[1].plot(dates, diffs)
        axes[1].set_xlabel("x")
        axes[1].set_ylabel("diff")
        # axes[1].title("Differences between prices and fit")
        axes[1].text(
            0.02,
            0.98,  # 相对于轴的 2%/98% 位置
            f"mean: {stats['mean']:.4f}\nstd: {stats['std']:.4f}\n"
            f"curr_diff: {stats['curr']:.4f}\n"
            f"curr_diff/std: {stats['curr']/stats['std']:.4f}\n"
            f"percentile: {stats['percentile']:.4f}",
            transform=axes[1].transAxes,  # 使用 [0,1] 轴坐标，而不是数据坐标
            fontsize=10,
            va="top",
            ha="left",
            bbox=dict(facecolor="white", alpha=0.6, edgecolor="none"),
        )
        axes[1].set_xlim(xmin, xmax)  # 让下图沿用同一日期范围
        axes[1].xaxis.set_major_locator(mdates.YearLocator())
        axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

        # fig.tight_layout()

        # 保存图像
        timestamp = datetime.now().strftime("%Y%m%d")
        freq_label = "Daily" if freq == "D" else "Weekly"
        output_path = os.path.join(
            self.output_dir,
            f"{timestamp}_{self.stock_code}_{freq_label}_harmonic_analysis.png",
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
            self._plot_harmonic_fit(params, df, offset=offset, freq=freq)
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
