#!/usr/bin/env python3
"""
分析模块主入口文件
提供FFT分析和相关性分析功能
"""

import argparse
import logging
from src.config import AnalysisConfig
from src.core import FFTAnalyzer, CauchyCorrelationAnalyzer, CorrelationAnalysisConfig


def setup_logging(level: str = "INFO"):
    """设置日志配置"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def run_fft_analysis(config: AnalysisConfig):
    """运行FFT分析"""
    print("开始FFT分析...")

    for stock_code in config.fft.default_stock_codes:
        print(f"\n分析股票代码: {stock_code}")
        analyzer = FFTAnalyzer(
            stock_code=stock_code,
            years=config.fft.analysis_years,
            num_components=config.fft.num_components,
        )
        analyzer.analyze(config.fft.frequencies)


def run_correlation_analysis(config: AnalysisConfig):
    """运行相关性分析"""
    print("开始相关性分析...")

    correlation_config = CorrelationAnalysisConfig(
        index_code=config.correlation.index_code,
        years=config.correlation.years,
        freq=config.correlation.freq,
        n_days=config.correlation.n_days,
        start_idx=config.correlation.start_idx,
        x_min=config.correlation.x_min,
        x_max=config.correlation.x_max,
        n_centers=config.correlation.n_centers,
        n_gammas=config.correlation.n_gammas,
        gamma_min=config.correlation.gamma_min,
        gamma_max=config.correlation.gamma_max,
        analysis_dir=config.correlation.analysis_dir,
        index_power=config.correlation.index_power,
    )

    analyzer = CauchyCorrelationAnalyzer(correlation_config)
    analyzer.run()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="金融数据分析模块")
    parser.add_argument(
        "--analysis-type",
        choices=["fft", "correlation", "all"],
        default="all",
        help="分析类型: fft(FFT分析), correlation(相关性分析), all(全部)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别",
    )

    args = parser.parse_args()

    # 设置日志
    setup_logging(args.log_level)

    # 加载配置
    config = AnalysisConfig()

    # 根据参数运行相应的分析
    if args.analysis_type == "fft":
        run_fft_analysis(config)
    elif args.analysis_type == "correlation":
        run_correlation_analysis(config)
    elif args.analysis_type == "all":
        run_fft_analysis(config)
        run_correlation_analysis(config)

    print("\n分析完成！")


if __name__ == "__main__":
    main()
