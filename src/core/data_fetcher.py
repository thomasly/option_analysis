import os
import pandas as pd
import tushare as ts
import hashlib
import dotenv
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DataFetcher:
    """数据获取器类，用于获取和缓存金融数据"""

    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化数据获取器

        Args:
            data_dir (str, optional): 数据缓存目录，默认为项目根目录下的data文件夹
        """
        self.pro = None
        self.data_dir = data_dir or self._get_default_data_dir()

        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)

        # 初始化Tushare API
        self._configure_tushare()

    def _get_default_data_dir(self) -> str:
        """获取默认数据目录"""
        # 获取项目根目录（analysis_module目录）
        current_dir = os.path.dirname(__file__)  # src/core
        project_root = os.path.dirname(
            os.path.dirname(current_dir)
        )  # analysis_module目录
        return os.path.join(project_root, "data")

    def _configure_tushare(self):
        """配置Tushare API"""
        dotenv.load_dotenv()
        tushare_token = os.getenv("TUSHARE_TOKEN")
        if not tushare_token:
            raise ValueError("TUSHARE_TOKEN 未正确配置，请检查.env文件设置")
        ts.set_token(tushare_token)
        self.pro = ts.pro_api()

    def fetch_index_data(
        self,
        index_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        years: int = 15,
        freq: str = "W",
    ) -> pd.DataFrame:
        """
        获取指数历史数据

        Args:
            index_code (str): 指数代码，如 "399006.SZ"
            start_date (str, optional): 开始日期，格式 "YYYYMMDD"
            end_date (str, optional): 结束日期，格式 "YYYYMMDD"
            years (int): 获取的年数，默认15年
            freq (str): 数据频率，"D"为日线，"W"为周线

        Returns:
            pd.DataFrame: 处理后的指数数据
        """
        # 设置默认日期范围
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365 * years)).strftime(
                "%Y%m%d"
            )

        # 生成缓存文件名
        cache_filename = self._generate_cache_filename(
            index_code, start_date, end_date, freq
        )
        cache_path = os.path.join(self.data_dir, cache_filename)

        # 尝试从缓存加载数据
        if os.path.exists(cache_path):
            logger.info(f"从缓存加载{freq}数据: {cache_filename}")
            df = pd.read_csv(
                cache_path,
                dtype={"ts_code": str},
                converters={"trade_date": str},
            )
        else:
            logger.info(f"从Tushare API获取{freq}数据...")
            df = self._fetch_from_api(index_code, start_date, end_date, freq)

            # 保存到缓存
            df.to_csv(cache_path, index=False)
            logger.info(f"数据已缓存至: {cache_path}")

        # 处理数据
        return self._process_data(df)

    def _generate_cache_filename(
        self, index_code: str, start_date: str, end_date: str, freq: str
    ) -> str:
        """生成缓存文件名"""
        date_hash = hashlib.md5(f"{start_date}_{end_date}_{freq}".encode()).hexdigest()[
            :8
        ]
        return f"{index_code}_{freq}_{date_hash}.csv"

    def _fetch_from_api(
        self, index_code: str, start_date: str, end_date: str, freq: str
    ) -> pd.DataFrame:
        """从API获取数据"""
        if freq == "W":
            df = self.pro.index_weekly(
                ts_code=index_code, start_date=start_date, end_date=end_date
            )
        elif freq == "D":
            df = self.pro.index_daily(
                ts_code=index_code, start_date=start_date, end_date=end_date
            )
        else:
            raise ValueError(f"不支持的频率类型: {freq}")

        return df

    def _process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理数据格式"""
        # 转换日期格式
        df["trade_date"] = pd.to_datetime(
            df["trade_date"].astype(str).str.strip(), format="%Y%m%d", errors="coerce"
        )

        # 过滤无效日期
        invalid_dates = df[df["trade_date"].isna()]
        if not invalid_dates.empty:
            logger.warning(f"发现 {len(invalid_dates)} 条无效日期数据，已过滤")
            df = df.dropna(subset=["trade_date"])

        return df.sort_values("trade_date").reset_index(drop=True)

    def get_data_info(
        self, index_code: str, freq: str = "W", years: int = 15
    ) -> Dict[str, Any]:
        """
        获取数据信息摘要

        Args:
            index_code (str): 指数代码
            freq (str): 数据频率
            years (int): 年数

        Returns:
            Dict[str, Any]: 数据信息字典
        """
        df = self.fetch_index_data(index_code, years=years, freq=freq)

        return {
            "index_code": index_code,
            "frequency": freq,
            "start_date": df["trade_date"].min().date(),
            "end_date": df["trade_date"].max().date(),
            "total_records": len(df),
            "price_range": {
                "min": df["close"].min(),
                "max": df["close"].max(),
                "mean": df["close"].mean(),
                "std": df["close"].std(),
            },
            "volume_range": {
                "min": df["vol"].min() if "vol" in df.columns else None,
                "max": df["vol"].max() if "vol" in df.columns else None,
                "mean": df["vol"].mean() if "vol" in df.columns else None,
            },
        }

    def fetch_fx_data(
        self,
        fx_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        years: int = 5
    ) -> pd.DataFrame:
        """
        获取外汇历史数据

        Args:
            fx_code (str): 外汇代码，如 "USDCNH.FXCM"
            start_date (str, optional): 开始日期，格式 "YYYYMMDD"
            end_date (str, optional): 结束日期，格式 "YYYYMMDD"
            years (int): 获取的年数，默认5年

        Returns:
            pd.DataFrame: 处理后的外汇数据
        """
        # 设置默认日期范围
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365 * years)).strftime(
                "%Y%m%d"
            )

        # 生成缓存文件名
        cache_filename = self._generate_fx_cache_filename(
            fx_code, start_date, end_date
        )
        cache_path = os.path.join(self.data_dir, cache_filename)

        # 尝试从缓存加载数据
        if os.path.exists(cache_path):
            logger.info(f"从缓存加载外汇数据: {cache_filename}")
            df = pd.read_csv(
                cache_path,
                converters={"trade_date": str},
            )
        else:
            logger.info(f"从Tushare API获取外汇数据...")
            df = self._fetch_fx_from_api(fx_code, start_date, end_date)

            # 保存到缓存
            df.to_csv(cache_path, index=False)
            logger.info(f"外汇数据已缓存至: {cache_path}")

        # 处理数据
        return self._process_fx_data(df)

    def _generate_fx_cache_filename(
        self, fx_code: str, start_date: str, end_date: str
    ) -> str:
        """生成外汇数据缓存文件名"""
        date_hash = hashlib.md5(f"{start_date}_{end_date}".encode()).hexdigest()[:8]
        # 替换点号，避免文件名问题
        fx_code_safe = fx_code.replace(".", "_")
        return f"fx_{fx_code_safe}_{date_hash}.csv"

    def _fetch_fx_from_api(
        self, fx_code: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """从API获取外汇数据"""
        df = self.pro.query(
            'fx_daily',
            ts_code=fx_code,
            start_date=start_date,
            end_date=end_date
        )
        return df

    def _process_fx_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理外汇数据格式"""
        # 转换日期格式
        df['trade_date'] = pd.to_datetime(
            df['trade_date'].astype(str).str.strip(), format="%Y%m%d", errors="coerce"
        )

        # 过滤无效日期
        invalid_dates = df[df["trade_date"].isna()]
        if not invalid_dates.empty:
            logger.warning(f"发现 {len(invalid_dates)} 条无效日期数据，已过滤")
            df = df.dropna(subset=["trade_date"])

        return df.sort_values("trade_date").reset_index(drop=True)

    def fetch_gold_data(
        self,
        ts_code: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        years: int = 5,
    ) -> pd.DataFrame:
        """
        获取上海黄金交易所现货合约日线行情

        Args:
            ts_code (str, optional): 合约代码，可通过基础信息获得
            start_date (str, optional): 开始日期，格式 "YYYYMMDD"
            end_date (str, optional): 结束日期，格式 "YYYYMMDD"
            years (int): 获取的年数，默认5年

        Returns:
            pd.DataFrame: 处理后的黄金现货数据
        """
        # 设置默认日期范围
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365 * years)).strftime(
                "%Y%m%d"
            )

        # 生成缓存文件名
        cache_filename = self._generate_gold_cache_filename(
            ts_code, start_date, end_date
        )
        cache_path = os.path.join(self.data_dir, cache_filename)

        # 尝试从缓存加载数据
        if os.path.exists(cache_path):
            logger.info(f"从缓存加载黄金数据: {cache_filename}")
            df = pd.read_csv(
                cache_path,
                dtype={"ts_code": str},
                converters={"trade_date": str},
            )
        else:
            logger.info(f"从Tushare API获取黄金数据...")
            df = self._fetch_gold_from_api(ts_code, start_date, end_date)

            # 保存到缓存
            df.to_csv(cache_path, index=False)
            logger.info(f"黄金数据已缓存至: {cache_path}")

        # 处理数据
        return self._process_gold_data(df)

    def _generate_gold_cache_filename(
        self, ts_code: Optional[str], start_date: str, end_date: str
    ) -> str:
        """生成黄金数据缓存文件名"""
        ts_code_part = ts_code.replace(".", "_") if ts_code else "all"
        date_hash = hashlib.md5(f"{start_date}_{end_date}".encode()).hexdigest()[:8]
        return f"gold_{ts_code_part}_{date_hash}.csv"

    def _fetch_gold_from_api(
        self, ts_code: Optional[str], start_date: str, end_date: str
    ) -> pd.DataFrame:
        """从API获取黄金数据"""
        kwargs = {
            "start_date": start_date,
            "end_date": end_date
        }
        if ts_code:
            kwargs["ts_code"] = ts_code
        
        df = self.pro.sge_daily(**kwargs)
        return df

    def _process_gold_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理黄金数据格式"""
        # 转换日期格式
        df["trade_date"] = pd.to_datetime(
            df["trade_date"].astype(str).str.strip(), format="%Y%m%d", errors="coerce"
        )

        # 过滤无效日期
        invalid_dates = df[df["trade_date"].isna()]
        if not invalid_dates.empty:
            logger.warning(f"发现 {len(invalid_dates)} 条无效日期数据，已过滤")
            df = df.dropna(subset=["trade_date"])

        return df.sort_values("trade_date").reset_index(drop=True)

    def clear_cache(self, pattern: Optional[str] = None):
        """
        清理缓存数据

        Args:
            pattern (str, optional): 文件名模式，如 "399006.SZ_*" 清理特定指数的缓存
        """
        if pattern is None:
            # 清理所有缓存
            for file in os.listdir(self.data_dir):
                if file.endswith(".csv"):
                    os.remove(os.path.join(self.data_dir, file))
            logger.info("已清理所有缓存数据")
        else:
            # 清理匹配模式的缓存
            import glob

            pattern_path = os.path.join(self.data_dir, pattern)
            for file_path in glob.glob(pattern_path):
                os.remove(file_path)
            logger.info(f"已清理匹配模式 '{pattern}' 的缓存数据")
