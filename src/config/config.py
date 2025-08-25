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
    """FFT分析配置"""

    # 默认分析的股票代码列表
    default_stock_codes: List[str] = field(default_factory=lambda: ["399006.SZ"])

    # FFT分析参数
    analysis_years: int = int(os.getenv("FFT_ANALYSIS_YEARS", "15"))  # 分析年数
    num_components: int = int(os.getenv("FFT_NUM_COMPONENTS", "6"))  # 周期成分数量

    # 分析频率
    frequencies: List[tuple] = field(
        default_factory=lambda: [("D", "日线"), ("W", "周线")]
    )

    # 是否启用FFT分析
    enable_fft_analysis: bool = (
        os.getenv("ENABLE_FFT_ANALYSIS", "true").lower() == "true"
    )


@dataclass
class CorrelationConfig:
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


@dataclass
class AnalysisConfig:
    """分析模块主配置"""

    tushare: TushareConfig = field(default_factory=TushareConfig)
    fft: FFTConfig = field(default_factory=FFTConfig)
    correlation: CorrelationConfig = field(default_factory=CorrelationConfig)

    # 运行配置
    data_dir: str = "data"
    output_dir: str = "analysis_results"
    log_level: str = "INFO"
