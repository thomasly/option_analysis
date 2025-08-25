import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
from dataclasses import dataclass
from typing import Dict

from .quantum_model import QuantumModel
from .font_config import setup_chinese_font

# 设置中文字体
setup_chinese_font()


@dataclass
class CorrelationAnalysisConfig:
    """相关性分析配置"""

    index_code: str = "399006.SZ"
    years: int = 2
    freq: str = "D"
    n_days: int = 11
    start_idx: int = 120
    x_min: float = -10
    x_max: float = 10
    n_centers: int = 11  # -10, -8, ..., 10
    n_gammas: int = 8
    gamma_min: float = 0.5
    gamma_max: float = 4.0
    analysis_dir: str = "analysis_results"
    index_power: float = 2


class CauchyCorrelationAnalyzer:
    """
    用于分析收盘价与一组正负柯西波函数的相关性，并可视化。
    """

    def __init__(self, config: CorrelationAnalysisConfig = None):
        """
        初始化相关性分析器

        Args:
            config: 分析配置，如果为None则使用默认配置
        """
        self.config = config or CorrelationAnalysisConfig()
        self.centers = np.arange(
            self.config.x_min,
            self.config.x_max + 1,
            (self.config.x_max - self.config.x_min) / (self.config.n_centers - 1),
        )
        self.gammas = np.linspace(
            self.config.gamma_min, self.config.gamma_max, self.config.n_gammas
        )
        self.x = np.linspace(self.config.x_min, self.config.x_max, 1000)
        self.signs = [1, -1]

        # 设置输出目录
        self._setup_output_directory()

        self.correlation_coefficients: Dict[str, Dict] = {}
        self.best_corr_key: str = ""
        self.best_corr_value: Dict = {}

    def _setup_output_directory(self):
        """设置输出目录"""
        # 获取项目根目录（analysis_module目录）
        current_dir = os.path.dirname(__file__)  # src/core
        project_root = os.path.dirname(
            os.path.dirname(current_dir)
        )  # analysis_module目录

        self.output_dir = os.path.join(project_root, self.config.analysis_dir)
        os.makedirs(self.output_dir, exist_ok=True)

    def load_data(self):
        """加载数据"""
        model = QuantumModel(index_code=self.config.index_code)
        data = model.load_data(years=self.config.years, freq=self.config.freq)
        if len(data) < self.config.n_days:
            raise ValueError(f"Not enough data for {self.config.n_days} days")
        sample = data.iloc[
            self.config.start_idx : self.config.start_idx + self.config.n_days
        ].copy()
        close = sample["close"].values
        close_norm = (close - close.min()) / (close.max() - close.min()) * 0.95 + 0.05
        price_x = np.linspace(self.config.x_min, self.config.x_max, self.config.n_days)
        return price_x, close_norm

    @staticmethod
    def cauchy(x: np.ndarray, x0: float, gamma: float, sign: int = 1) -> np.ndarray:
        """生成正/负柯西波函数"""
        return sign * 1 / (np.pi * gamma * (1 + ((x - x0) / gamma) ** 2))

    def compute_correlations(self, price_x: np.ndarray, close_norm: np.ndarray):
        """计算所有正负柯西波函数与收盘价的相关系数"""
        for x0 in self.centers:
            for gamma in self.gammas:
                for sign in self.signs:
                    y = self.cauchy(price_x, x0, gamma, sign)
                    corr, p_value = pearsonr(close_norm, y)
                    key = f"x0={x0}, gamma={gamma:.2f}, sign={'+' if sign==1 else '-'}"
                    self.correlation_coefficients[key] = {
                        "correlation": corr,
                        "p_value": p_value,
                        "x0": x0,
                        "gamma": gamma,
                        "sign": sign,
                    }
        # 找出最大相关系数
        self.best_corr_key = max(
            self.correlation_coefficients.keys(),
            key=lambda k: abs(self.correlation_coefficients[k]["correlation"]),
        )
        self.best_corr_value = self.correlation_coefficients[self.best_corr_key]

    def plot_transparency(self, price_x: np.ndarray, close_norm: np.ndarray):
        """绘制所有柯西波函数，透明度按相关系数正负映射"""
        plt.figure(figsize=(12, 8))
        for x0 in self.centers:
            for gamma in self.gammas:
                for sign in self.signs:
                    y = self.cauchy(self.x, x0, gamma, sign)
                    key = f"x0={x0}, gamma={gamma:.2f}, sign={'+' if sign==1 else '-'}"
                    correlation = self.correlation_coefficients[key]["correlation"]
                    normed_correlation = (correlation + 1) / 2
                    # alpha=0.99(最不透明,正相关), alpha=0.01(最透明,负相关)
                    # alpha是一个correlation的指数函数
                    alpha = 0.1 * 10 ** (normed_correlation**self.config.index_power)
                    plt.plot(self.x, y, linewidth=1.2, alpha=alpha, zorder=1)
        plt.plot(
            price_x,
            close_norm,
            "ko-",
            label="Normalized Close Price",
            linewidth=3,
            markersize=10,
            zorder=10,
        )
        plt.title(
            "Cauchy Wave Functions (Continuous, Both Signs) with Transparency Based on Correlation Coefficient Sign"
        )
        plt.xlabel("x")
        plt.ylabel("Value")
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "step13_transparency.png"))
        plt.close()

    def run(self):
        """主流程：加载数据、计算相关性、绘图"""
        try:
            price_x, close_norm = self.load_data()
            self.compute_correlations(price_x, close_norm)
            self.plot_transparency(price_x, close_norm)
            print("Analysis completed. Transparency plot saved.")
        except Exception as e:
            print(f"Error: {e}")


# 保持向后兼容的函数
def run_correlation_analysis(config: CorrelationAnalysisConfig = None):
    """
    运行相关性分析的便捷函数

    Args:
        config: 分析配置，如果为None则使用默认配置
    """
    analyzer = CauchyCorrelationAnalyzer(config)
    analyzer.run()


if __name__ == "__main__":
    config = CorrelationAnalysisConfig()
    analyzer = CauchyCorrelationAnalyzer(config)
    analyzer.run()
