import os
import datetime as dt
from dataclasses import dataclass, field
from typing import List
import dotenv

dotenv.load_dotenv()


@dataclass
class TushareConfig:
    """Tushare配置"""

    token: str = os.getenv("TUSHARE_TOKEN", "")
    exchange: str = "SZSE"
    list_status: str = "L"


@dataclass
class FFTConfig:
    """FFT analysis configuration"""

    # Default list of stock codes for analysis
    default_stock_codes: List[str] = field(default_factory=lambda: ["399006.SZ"])

    # FFT analysis parameters
    analysis_years: int = int(
        os.getenv("FFT_ANALYSIS_YEARS", "15")
    )  # Number of analysis years
    num_components: int = int(
        os.getenv("FFT_NUM_COMPONENTS", "6")
    )  # Number of periodic components

    # Analysis frequencies
    frequencies: List[tuple] = field(
        default_factory=lambda: [("D", "Daily"), ("W", "Weekly")]
    )

    # Whether to enable FFT analysis
    enable_fft_analysis: bool = (
        os.getenv("ENABLE_FFT_ANALYSIS", "true").lower() == "true"
    )


@dataclass
class HarmonicConfig:
    # Default list of stock codes for analysis
    default_stock_codes: List[str] = field(default_factory=lambda: ["399006.SZ"])

    # FFT analysis parameters
    analysis_years: int = int(os.getenv("FFT_ANALYSIS_YEARS", "14"))

    # Analysis frequencies
    frequencies: List[tuple] = field(
        default_factory=lambda: [("D", "Daily"), ("W", "Weekly")]
    )

    # Whether to enable FFT analysis
    enable_harmonic_analysis: bool = (
        os.getenv("ENABLE_HARMONIC_ANALYSIS", "true").lower() == "true"
    )


@dataclass
class CorrelationConfig:
    """Correlation analysis configuration"""

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


@dataclass
class AlexNetConfig:
    """AlexNet模型配置"""

    # 模型参数
    input_size: int = 16  # 输入图像尺寸 16x16
    num_classes: int = 10  # 分类数量
    dropout_rate: float = 0.5

    # 训练参数
    batch_size: int = int(os.getenv("ALEXNET_BATCH_SIZE", "32"))
    learning_rate: float = float(os.getenv("ALEXNET_LEARNING_RATE", "0.001"))
    num_epochs: int = int(os.getenv("ALEXNET_NUM_EPOCHS", "100"))
    weight_decay: float = float(os.getenv("ALEXNET_WEIGHT_DECAY", "1e-4"))

    # 数据参数
    train_split: float = 0.8  # 训练集比例
    val_split: float = 0.1  # 验证集比例
    test_split: float = 0.1  # 测试集比例

    # 保存路径
    model_save_dir: str = "models"
    checkpoint_dir: str = "checkpoints"
    log_dir: str = "logs"

    # 设备配置
    device: str = (
        "cuda" if os.getenv("CUDA_AVAILABLE", "true").lower() == "true" else "cpu"
    )

    # 早停参数
    patience: int = 10  # 早停耐心值
    min_delta: float = 0.001  # 最小改善阈值


@dataclass
class FibonacciConfig:
    """Fibonacci analysis configuration"""
    
    # Fibonacci levels configuration
    enable_fibonacci: bool = True
    
    # Fibonacci resistance levels configuration (压力位)
    resistance_high: float = 3576.12
    resistance_low: float = 1482.98
    resistance_trend: str = "down"  # "up" or "down"
    
    # Fibonacci support levels configuration (支撑位)
    support_low: float = 1756.64
    support_high: float = 3322.44
    support_trend: str = "up"  # "up" or "down"
    
    # Fibonacci ratios
    fib_ratios: List[float] = field(
        default_factory=lambda: [0.236, 0.382, 0.5, 0.618, 0.786]
    )


@dataclass
class AnalysisConfig:
    """Main configuration for analysis modules"""

    tushare: TushareConfig = field(default_factory=TushareConfig)
    fft: FFTConfig = field(default_factory=FFTConfig)
    correlation: CorrelationConfig = field(default_factory=CorrelationConfig)
    alexnet: AlexNetConfig = field(default_factory=AlexNetConfig)
    harmonic: HarmonicConfig = field(default_factory=HarmonicConfig)
    fibonacci: FibonacciConfig = field(default_factory=FibonacciConfig)

    # Run configuration
    data_dir: str = "data"
    output_dir: str = "analysis_results"
    log_level: str = "INFO"
