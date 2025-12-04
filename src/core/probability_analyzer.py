#!/usr/bin/env python3
"""
概率转移矩阵分析器
使用一阶和二阶概率转移矩阵进行行情预测
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from .data_fetcher import DataFetcher

# 状态标签
STATE_LABELS = ['大跌', '中跌', '小跌', '小涨', '中涨', '大涨']


class ProbabilityAnalyzer:
    """概率转移矩阵分析器"""
    
    def __init__(self, stock_code: str, years: int = 5):
        """
        初始化概率转移矩阵分析器
        
        Args:
            stock_code: 股票代码，如"399006.SZ"
            years: 分析的历史数据年限
        """
        self.stock_code = stock_code
        self.years = years
        self.data = None
        self.thresholds = None
        self.data_fetcher = DataFetcher()
        
        # 获取历史数据
        self._fetch_data()
        
        # 计算阈值
        self._calculate_thresholds()
    
    def _fetch_data(self):
        """获取历史数据"""
        logging.info(f"获取 {self.stock_code} 的历史数据...")
        
        # 使用DataFetcher获取日线数据
        self.data = self.data_fetcher.fetch_index_data(
            index_code=self.stock_code, 
            years=self.years, 
            freq="D"
        )
        
        # 确保trade_date列是字符串格式，用于后续处理
        self.data["trade_date"] = self.data["trade_date"].dt.strftime("%Y%m%d")
        
        logging.info(f"获取到 {len(self.data)} 条历史数据")
    
    def _calculate_thresholds(self):
        """计算收益率的分位数阈值"""
        # 使用历史收益率的分位数作为状态划分阈值
        self.thresholds = self.data["pct_chg"].quantile([0.1, 0.25, 0.5, 0.75, 0.9]).values
        self.thresholds[2] = 0 # 涨跌的分界线必须是0
        logging.info(f"计算得到的阈值: {self.thresholds}")
    
    def _map_return_to_state(self, ret):
        """将收益率映射到状态
        
        Args:
            ret: 收益率
            
        Returns:
            int: 状态索引 (0-5)
        """
        if ret <= self.thresholds[0]:
            return 0  # 大跌
        elif ret <= self.thresholds[1]:
            return 1  # 中跌
        elif ret <= self.thresholds[2]:
            return 2  # 小跌
        elif ret <= self.thresholds[3]:
            return 3  # 小涨
        elif ret <= self.thresholds[4]:
            return 4  # 中涨
        else:
            return 5  # 大涨
    
    def create_first_order_matrix(self, window_size=60, include_today=True):
        """创建一阶转移矩阵
        
        Args:
            window_size: 滚动窗口大小
            include_today: 是否包含今天的数据，默认为True
            
        Returns:
            tuple: (转移矩阵, 状态序列)
        """
        logging.info(f"创建一阶转移矩阵，窗口大小: {window_size}, include_today: {include_today}")
        
        # 获取数据范围
        if include_today:
            # 包含今天的数据
            recent_data = self.data["pct_chg"].values[-window_size:]
        else:
            # 不包含今天的数据，只使用昨天及之前的数据
            recent_data = self.data["pct_chg"].values[-window_size-1:-1]
        
        # 将收益率映射到状态
        states = [self._map_return_to_state(ret) for ret in recent_data]
        
        # 初始化6x6转移矩阵
        transition_matrix = np.zeros((6, 6))
        
        # 统计状态转移次数
        for i in range(len(states) - 1):
            from_state = states[i]
            to_state = states[i + 1]
            transition_matrix[from_state, to_state] += 1
        
        # 转换为概率（行归一化）
        row_sums = transition_matrix.sum(axis=1)
        row_sums[row_sums == 0] = 1  # 避免除零错误
        transition_matrix = transition_matrix / row_sums[:, np.newaxis]
        
        return transition_matrix, states
    
    def create_second_order_matrix(self, window_size=360, include_today=True):
        """创建二阶转移矩阵
        
        Args:
            window_size: 滚动窗口大小
            include_today: 是否包含今天的数据，默认为True
            
        Returns:
            tuple: (转移矩阵, 状态序列)
        """
        logging.info(f"创建二阶转移矩阵，窗口大小: {window_size}, include_today: {include_today}")
        
        # 获取数据范围
        if include_today:
            # 包含今天的数据
            recent_data = self.data["pct_chg"].values[-window_size:]
        else:
            # 不包含今天的数据，只使用昨天及之前的数据
            recent_data = self.data["pct_chg"].values[-window_size-1:-1]
        
        # 将收益率映射到状态
        states = [self._map_return_to_state(ret) for ret in recent_data]
        
        # 确保有足够的数据点进行二阶转移分析
        if len(states) < 3:
            logging.warning("数据点不足，无法创建二阶转移矩阵")
            return np.zeros((36, 6)), states
        
        # 创建36x6的转移矩阵（6^2个可能的前状态组合）
        transition_matrix = np.zeros((36, 6))
        
        # 统计状态转移次数
        for i in range(2, len(states)):
            prev_state1 = states[i-2]
            prev_state2 = states[i-1]
            current_state = states[i]
            
            # 将两个前状态编码为一个组合状态 (0-35)
            combined_state = prev_state1 * 6 + prev_state2
            transition_matrix[combined_state, current_state] += 1
        
        # 归一化
        row_sums = transition_matrix.sum(axis=1)
        row_sums[row_sums == 0] = 1  # 避免除零错误
        transition_matrix = transition_matrix / row_sums[:, np.newaxis]
        
        return transition_matrix, states
    
    def _predict_with_first_order_matrix(self, matrix, current_state):
        """使用一阶转移矩阵进行预测
        
        Args:
            matrix: 一阶转移矩阵
            current_state: 当前状态（0-5）
            
        Returns:
            tuple: (预测概率分布, 使用的状态)
        """
        if current_state is None:
            logging.warning("一阶矩阵预测失败：当前状态为None")
            return np.zeros(6), None
        
        # 确保current_state是有效的状态值
        if not 0 <= current_state <= 5:
            logging.warning(f"一阶矩阵预测失败：无效的状态值 {current_state}")
            return np.zeros(6), None
        
        return matrix[current_state], current_state
    
    def _predict_with_second_order_matrix(self, matrix, current_state):
        """使用二阶转移矩阵进行预测
        
        Args:
            matrix: 二阶转移矩阵
            current_state: 当前状态组合，格式为 (state1, state2)
            
        Returns:
            tuple: (预测概率分布, 使用的状态组合)
        """
        if current_state is None:
            logging.warning("二阶矩阵预测失败：当前状态组合为None")
            return np.zeros(6), None
        
        # 确保current_state是有效的状态组合
        if not isinstance(current_state, tuple) or len(current_state) != 2:
            logging.warning(f"二阶矩阵预测失败：无效的状态组合 {current_state}")
            return np.zeros(6), None
        
        state1, state2 = current_state
        if not (0 <= state1 <= 5 and 0 <= state2 <= 5):
            logging.warning(f"二阶矩阵预测失败：无效的状态值 {current_state}")
            return np.zeros(6), None
        
        combined_state = state1 * 6 + state2
        return matrix[combined_state], current_state
    
    def analyze_today(self):
        """分析今天的走势预测
        
        Returns:
            dict: 包含一阶和二阶矩阵的预测结果
        """
        logging.info("开始分析今天的走势...")
        
        # 获取今天的实际状态
        today_return = self.data["pct_chg"].values[-1]
        today_state = self._map_return_to_state(today_return)
        
        # 创建一阶转移矩阵 - 不包含今天的数据
        # 使用今天之前的数据来创建转移矩阵
        first_order_matrix, first_order_states = self.create_first_order_matrix(window_size=60, include_today=False)
        
        # 获取一阶矩阵的预测概率
        # 使用昨天的状态来预测今天的走势
        first_order_probs = np.zeros(6)
        if len(first_order_states) >= 1:
            yesterday_state = first_order_states[-1]
            first_order_probs, _ = self._predict_with_first_order_matrix(first_order_matrix, yesterday_state)
        else:
            logging.warning("一阶矩阵数据点不足，无法进行预测")
        
        # 创建二阶转移矩阵 - 不包含今天的数据
        second_order_matrix, second_order_states = self.create_second_order_matrix(window_size=360, include_today=False)
        
        # 获取二阶矩阵的预测概率
        # 使用前天和昨天的状态来预测今天的走势
        second_order_probs = np.zeros(6)
        if len(second_order_states) >= 2:
            prev_state = second_order_states[-2]
            yesterday_state = second_order_states[-1]
            second_order_probs, _ = self._predict_with_second_order_matrix(second_order_matrix, (prev_state, yesterday_state))
        else:
            logging.warning("二阶矩阵数据点不足，无法进行预测")
        
        # 检查今天的走势是否符合预测
        first_order_prob = first_order_probs[today_state]
        second_order_prob = second_order_probs[today_state]
        
        # 确定预警级别
        alert_level = "none"
        if first_order_prob == 0 and second_order_prob == 0:
            alert_level = "strong"
            logging.warning("强预警：今天的走势在一阶和二阶矩阵预测中概率均为0！")
        elif first_order_prob == 0 or second_order_prob == 0:
            alert_level = "normal"
            logging.warning("预警：今天的走势在一阶或二阶矩阵预测中概率为0！")
        
        # 构建结果
        result = {
            "today_return": today_return,
            "today_state": today_state,
            "today_state_label": STATE_LABELS[today_state],
            "first_order_probs": first_order_probs,
            "second_order_probs": second_order_probs,
            "alert_level": alert_level,
            "first_order_prob": first_order_prob,
            "second_order_prob": second_order_prob
        }
        
        return result
    
    def predict_tomorrow(self):
        """预测明天的走势
        
        Returns:
            dict: 包含一阶和二阶矩阵的预测结果
        """
        logging.info("开始预测明天的走势...")
        
        # 创建一阶转移矩阵（包含今天的数据，因为我们是在今天的基础上预测明天）
        first_order_matrix, first_order_states = self.create_first_order_matrix(window_size=60, include_today=True)
        
        # 获取一阶矩阵的预测概率
        # 使用今天的状态来预测明天的走势
        first_order_probs = np.zeros(6)
        current_state = None
        if len(first_order_states) >= 1:
            current_state = first_order_states[-1]
            first_order_probs, _ = self._predict_with_first_order_matrix(first_order_matrix, current_state)
        else:
            logging.warning("一阶矩阵数据点不足，无法进行预测")
            # 设置默认状态
            current_state = 3  # 小涨
        
        # 创建二阶转移矩阵（包含今天的数据，因为我们是在今天的基础上预测明天）
        second_order_matrix, second_order_states = self.create_second_order_matrix(window_size=360, include_today=True)
        
        # 获取二阶矩阵的预测概率
        # 使用昨天和今天的状态来预测明天的走势
        second_order_probs = np.zeros(6)
        if len(second_order_states) >= 2:
            yesterday_state = second_order_states[-2]
            today_state = second_order_states[-1]
            second_order_probs, _ = self._predict_with_second_order_matrix(second_order_matrix, (yesterday_state, today_state))
        else:
            logging.warning("二阶矩阵数据点不足，无法进行预测")
        
        # 构建结果
        result = {
            "current_state": current_state,
            "current_state_label": STATE_LABELS[current_state],
            "first_order_probs": first_order_probs,
            "second_order_probs": second_order_probs
        }
        
        return result
    
    def analyze(self):
        """执行完整的分析
        
        Returns:
            dict: 包含今天分析和明天预测的结果
        """
        logging.info("开始概率转移矩阵分析...")
        
        # 分析今天的走势
        today_analysis = self.analyze_today()
        
        # 预测明天的走势
        tomorrow_prediction = self.predict_tomorrow()
        
        # 构建完整结果
        result = {
            "today": today_analysis,
            "tomorrow": tomorrow_prediction
        }
        
        logging.info("概率转移矩阵分析完成！")
        
        return result
    
    def print_analysis_result(self, result):
        """打印分析结果
        
        Args:
            result: 分析结果字典
        """
        print("\n" + "="*60)
        print("📊 概率转移矩阵分析结果")
        print("="*60)
        
        # 打印今天的分析
        print("\n1. 今天的走势分析：")
        print(f"   今天的实际收益率: {result['today']['today_return']:.2f}%")
        print(f"   今天的实际走势: {result['today']['today_state_label']}")
        
        print("\n   一阶矩阵预测的今天走势概率：")
        for i, prob in enumerate(result['today']['first_order_probs']):
            print(f"     {STATE_LABELS[i]}: {prob:.2%}")
        
        print("\n   二阶矩阵预测的今天走势概率：")
        for i, prob in enumerate(result['today']['second_order_probs']):
            print(f"     {STATE_LABELS[i]}: {prob:.2%}")
        
        # 打印预警信息
        alert_level = result['today']['alert_level']
        if alert_level == "strong":
            print("\n   ⚠️  强预警：今天的走势在一阶和二阶矩阵预测中概率均为0，市场可能出现了重大变化！")
        elif alert_level == "normal":
            print("\n   ⚠️  预警：今天的走势在一阶或二阶矩阵预测中概率为0，市场可能出现了变化！")
        
        # 打印明天的预测
        print("\n2. 明天的走势预测：")
        print(f"   当前状态: {result['tomorrow']['current_state_label']}")
        
        print("\n   一阶矩阵预测的明天走势概率：")
        for i, prob in enumerate(result['tomorrow']['first_order_probs']):
            print(f"     {STATE_LABELS[i]}: {prob:.2%}")
        
        print("\n   二阶矩阵预测的明天走势概率：")
        for i, prob in enumerate(result['tomorrow']['second_order_probs']):
            print(f"     {STATE_LABELS[i]}: {prob:.2%}")
        
        print("\n" + "="*60)
    
    def generate_email_content(self, result):
        """生成邮件内容
        
        Args:
            result: 分析结果字典
            
        Returns:
            str: HTML格式的邮件内容
        """
        # 生成今天分析的HTML
        today_html = f"""
        <h3>1. 今天的走势分析</h3>
        <p>今天的实际收益率: <strong>{result['today']['today_return']:.2f}%</strong></p>
        <p>今天的实际走势: <strong>{result['today']['today_state_label']}</strong></p>
        
        <h4>一阶矩阵预测的今天走势概率：</h4>
        <div style="overflow-x: auto; margin: 10px 0;">
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; max-width: 100%; font-size: 14px;">
                <tr style="background-color: #f2f2f2;">
                    <th style="white-space: nowrap; padding: 10px;">走势类型</th>
                    <th style="white-space: nowrap; padding: 10px;">概率</th>
                </tr>
        """
        
        for i, prob in enumerate(result['today']['first_order_probs']):
            today_html += f"""
                <tr>
                    <td style="padding: 8px; text-align: center;">{STATE_LABELS[i]}</td>
                    <td style="padding: 8px; text-align: center;">{prob:.2%}</td>
                </tr>
            """
        
        today_html += f"""
            </table>
        </div>
        
        <h4>二阶矩阵预测的今天走势概率：</h4>
        <div style="overflow-x: auto; margin: 10px 0;">
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; max-width: 100%; font-size: 14px;">
                <tr style="background-color: #f2f2f2;">
                    <th style="white-space: nowrap; padding: 10px;">走势类型</th>
                    <th style="white-space: nowrap; padding: 10px;">概率</th>
                </tr>
        """
        
        for i, prob in enumerate(result['today']['second_order_probs']):
            today_html += f"""
                <tr>
                    <td style="padding: 8px; text-align: center;">{STATE_LABELS[i]}</td>
                    <td style="padding: 8px; text-align: center;">{prob:.2%}</td>
                </tr>
            """
        
        today_html += f"""
            </table>
        </div>
        """
        
        # 添加预警信息
        alert_level = result['today']['alert_level']
        if alert_level == "strong":
            today_html += f"""
            <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; padding: 10px; margin-top: 10px; font-size: 14px;">
                <strong>⚠️  强预警：</strong>今天的走势在一阶和二阶矩阵预测中概率均为0，市场可能出现了重大变化！
            </div>
            """
        elif alert_level == "normal":
            today_html += f"""
            <div style="background-color: #fff3cd; border: 1px solid #ffeeba; border-radius: 4px; padding: 10px; margin-top: 10px; font-size: 14px;">
                <strong>⚠️  预警：</strong>今天的走势在一阶或二阶矩阵预测中概率为0，市场可能出现了变化！
            </div>
            """
        
        # 生成明天预测的HTML
        tomorrow_html = f"""
        <h3>2. 明天的走势预测</h3>
        <p>当前状态: <strong>{result['tomorrow']['current_state_label']}</strong></p>
        
        <h4>一阶矩阵预测的明天走势概率：</h4>
        <div style="overflow-x: auto; margin: 10px 0;">
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; max-width: 100%; font-size: 14px;">
                <tr style="background-color: #f2f2f2;">
                    <th style="white-space: nowrap; padding: 10px;">走势类型</th>
                    <th style="white-space: nowrap; padding: 10px;">概率</th>
                </tr>
        """
        
        for i, prob in enumerate(result['tomorrow']['first_order_probs']):
            tomorrow_html += f"""
                <tr>
                    <td style="padding: 8px; text-align: center;">{STATE_LABELS[i]}</td>
                    <td style="padding: 8px; text-align: center;">{prob:.2%}</td>
                </tr>
            """
        
        tomorrow_html += f"""
            </table>
        </div>
        
        <h4>二阶矩阵预测的明天走势概率：</h4>
        <div style="overflow-x: auto; margin: 10px 0;">
            <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; max-width: 100%; font-size: 14px;">
                <tr style="background-color: #f2f2f2;">
                    <th style="white-space: nowrap; padding: 10px;">走势类型</th>
                    <th style="white-space: nowrap; padding: 10px;">概率</th>
                </tr>
        """
        
        for i, prob in enumerate(result['tomorrow']['second_order_probs']):
            tomorrow_html += f"""
                <tr>
                    <td style="padding: 8px; text-align: center;">{STATE_LABELS[i]}</td>
                    <td style="padding: 8px; text-align: center;">{prob:.2%}</td>
                </tr>
            """
        
        tomorrow_html += f"""
            </table>
        </div>
        """
        
        # 组合完整的HTML内容
        html_content = f"""
        <div class="analysis-section" style="font-size: 16px; line-height: 1.6;">
            <h2 style="font-size: 20px; margin-bottom: 20px;">📊 概率转移矩阵分析</h2>
            {today_html}
            {tomorrow_html}
        </div>
        """
        
        return html_content


if __name__ == "__main__":
    analyzer = ProbabilityAnalyzer("399006.SZ")
    transition_matrix, states = analyzer.create_first_order_matrix()
    second_order_matrix, _ = analyzer.create_second_order_matrix()
    print(analyzer.data.tail())
    print(transition_matrix, states)
    print(second_order_matrix)