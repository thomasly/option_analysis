import numpy as np
import pandas as pd
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from .data_fetcher import DataFetcher

logger = logging.getLogger(__name__)


class QuantumModel:
    """量子模型类，用于获取股市历史数据"""

    def __init__(self, index_code: str = "399006.SZ"):
        """
        初始化量子模型

        Args:
            index_code (str): 要分析的指数代码，默认为创业板指数
        """
        self.index_code = index_code
        self.data_fetcher = DataFetcher()
        self.data = None
        self.data_info = None

        logger.info(f"量子模型初始化完成，分析标的: {index_code}")

    def load_data(
        self,
        years: int = 15,
        freq: str = "D",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        加载指数历史数据

        Args:
            years (int): 获取的年数，默认15年
            freq (str): 数据频率，"D"为日线，"W"为周线
            start_date (str, optional): 开始日期，格式 "YYYYMMDD"
            end_date (str, optional): 结束日期，格式 "YYYYMMDD"

        Returns:
            pd.DataFrame: 加载的数据
        """
        logger.info(f"开始加载 {self.index_code} 的历史数据...")

        # 获取数据
        self.data = self.data_fetcher.fetch_index_data(
            index_code=self.index_code,
            years=years,
            freq=freq,
            start_date=start_date,
            end_date=end_date,
        )

        # 获取数据信息
        self.data_info = self.data_fetcher.get_data_info(
            index_code=self.index_code, freq=freq, years=years
        )

        logger.info(f"数据加载完成，共 {len(self.data)} 条记录")
        logger.info(
            f"时间范围: {self.data_info['start_date']} 至 {self.data_info['end_date']}"
        )

        return self.data

    def get_data_summary(self) -> Dict[str, Any]:
        """
        获取数据摘要

        Returns:
            Dict[str, Any]: 数据摘要信息
        """
        if self.data is None:
            raise ValueError("请先调用 load_data() 方法加载数据")

        summary = {
            "index_code": self.index_code,
            "data_info": self.data_info,
            "data_shape": self.data.shape,
            "columns": list(self.data.columns),
            "date_range": {
                "start": self.data["trade_date"].min(),
                "end": self.data["trade_date"].max(),
                "days": (
                    self.data["trade_date"].max() - self.data["trade_date"].min()
                ).days,
            },
        }

        return summary
