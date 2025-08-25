"""
金融数据分析模块

提供FFT分析和相关性分析功能
"""

__version__ = "1.0.0"
__author__ = "OptionMonitor Team"

from .src.core import FFTAnalyzer, CauchyCorrelationAnalyzer
from .src.config import AnalysisConfig

__all__ = ["FFTAnalyzer", "CauchyCorrelationAnalyzer", "AnalysisConfig"]
