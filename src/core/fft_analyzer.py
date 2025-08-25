import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager
import pandas as pd
from datetime import datetime
import dotenv
from matplotlib.dates import AutoDateLocator
from scipy.fft import fft, ifft

from .data_fetcher import DataFetcher


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
        plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

        # 尝试加载Windows字体
        font_dirs = ["/mnt/c/Windows/Fonts"]
        font_files = font_manager.findSystemFonts(fontpaths=font_dirs)
        for font_file in font_files:
            try:
                font_manager.fontManager.addfont(font_file)
            except Exception:
                pass

        # 设置中文字体
        chinese_fonts = [
            "SimHei",
            "Microsoft YaHei",
            "SimSun",
            "NSimSun",
            "FangSong",
            "KaiTi",
        ]
        for font in chinese_fonts:
            if font.lower() in [
                f.name.lower() for f in font_manager.fontManager.ttflist
            ]:
                plt.rcParams["font.sans-serif"] = [font]
                break

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

    def generate_linear_fit(self, df, freq_label):
        """生成线性回归拟合图"""
        # 转换日期为数值格式
        dates = df["trade_date"].map(lambda x: x.toordinal())
        close_prices = df["close"].values

        # 执行线性回归
        slope, intercept = np.polyfit(dates, close_prices, 1)
        fit_line = slope * dates + intercept

        # 新增残差分析
        residuals = close_prices - fit_line

        # 绘制残差图
        plt.figure(figsize=(12, 6))
        plt.plot(
            df["trade_date"],
            residuals,
            color="purple",
            label="残差（实际价格 - 拟合值）",
        )
        plt.axhline(0, color="gray", linestyle="--", alpha=0.5)

        # 设置残差图格式
        plt.title(f"{self.stock_code} {freq_label}线性拟合残差分析")
        plt.xlabel("日期")
        plt.ylabel("残差值")
        ax = plt.gca()
        ax.xaxis.set_major_locator(
            AutoDateLocator(maxticks=20 if freq_label == "日线" else 10)
        )
        plt.xticks(rotation=30, ha="right")
        plt.legend(loc="upper left")
        plt.grid(alpha=0.2)
        plt.tight_layout()

        # 计算Y轴范围
        y_abs_max = np.max(np.abs(residuals)) * 1.2
        plt.ylim(-y_abs_max, y_abs_max)

        # 保存残差图
        residual_path = os.path.join(
            self.output_dir, f"{self.stock_code}_{freq_label}_linear_residuals.png"
        )
        plt.savefig(residual_path, dpi=200, bbox_inches="tight")
        plt.close()
        print(f"已生成残差分析图：{residual_path}")

    def generate_residual_analysis(self, df, freq_label):
        """对残差进行周期分析"""
        # 计算线性拟合残差
        dates = df["trade_date"].map(lambda x: x.toordinal())
        close_prices = df["close"].values
        slope, intercept = np.polyfit(dates, close_prices, 1)
        residuals = close_prices - (slope * dates + intercept)

        # 傅里叶分析参数
        n = len(residuals)
        fft_vals = fft(residuals)
        freqs = np.fft.fftfreq(n)
        amplitudes = np.abs(fft_vals)

        # 选择主要周期成分
        top_indices = np.argsort(amplitudes)[-self.num_components :]

        # 修改后的傅里叶重建部分
        filtered_fft = np.zeros_like(fft_vals)

        # 选择成分时排除直流分量（索引0）
        valid_indices = [i for i in top_indices if i != 0]

        # 添加对称频率成分（针对实数信号）
        for i in valid_indices:
            if i <= n // 2:  # 仅处理正频率部分
                # 添加正负频率对
                filtered_fft[i] = fft_vals[i]
                filtered_fft[-i] = fft_vals[-i]

        # 使用逆变换自动处理缩放
        reconstructed = np.real(ifft(filtered_fft))

        # 去均值处理（确保残差本身已去趋势）
        reconstructed -= np.mean(reconstructed)

        # 计算统一Y轴范围
        y_min = min(np.min(residuals), np.min(reconstructed)) * 1.1
        y_max = max(np.max(residuals), np.max(reconstructed)) * 1.1

        # 可视化
        plt.figure(figsize=(12, 6))
        plt.plot(df["trade_date"], residuals, label="残差", color="purple")
        plt.plot(
            df["trade_date"],
            reconstructed,
            label=f"周期拟合 ({self.num_components}成分)",
            color="teal",
            linestyle="--",
        )

        # 设置图表格式
        plt.title(f"{self.stock_code} {freq_label}残差周期分析")
        plt.xlabel("日期")
        plt.ylabel("残差值")
        ax = plt.gca()
        ax.xaxis.set_major_locator(AutoDateLocator(maxticks=10))
        plt.xticks(rotation=30, ha="right")
        plt.legend(loc="upper left")
        plt.grid(alpha=0.2)
        plt.tight_layout()

        # 设置统一Y轴范围
        plt.ylim(y_min, y_max)

        # 保存结果
        output_path = os.path.join(
            self.output_dir, f"{self.stock_code}_{freq_label}_residual_cycles.png"
        )
        plt.savefig(output_path, dpi=200, bbox_inches="tight")
        plt.close()
        print(f"已生成残差周期分析图：{output_path}")

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
            label="实际点数",
            color="navy",
            linewidth=2,
            alpha=0.8,
        )

        # 绘制综合预测
        plt.plot(
            df["trade_date"],
            combined,
            label=f"综合预测 ({self.num_components}周期成分)",
            color="crimson",
            linestyle="--",
            linewidth=2,
        )

        # 分解显示各成分
        plt.plot(
            df["trade_date"],
            linear_trend,
            label="线性趋势",
            color="darkgreen",
            alpha=0.6,
        )

        # 设置图表格式
        plt.title(f"{self.stock_code} {freq_label}综合趋势分析")
        plt.xlabel("日期")
        plt.ylabel("点数")
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
            frequencies = [("D", "日线"), ("W", "周线")]

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

            # 执行分析
            self.generate_linear_fit(df, freq_label)
            self.generate_residual_analysis(df, freq_label)
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
