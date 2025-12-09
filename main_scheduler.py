#!/usr/bin/env python3
"""
分析模块主入口文件 - 定时版本
提供FFT分析和相关性分析功能，并定时发送邮件
"""

import argparse
import logging
import schedule
import time
import json
import os
import glob
from datetime import datetime
from dotenv import load_dotenv
from src.config import AnalysisConfig
from src.core import HarmonicAnalyzer, ProbabilityAnalyzer, FxAnalyzer, GoldAnalyzer, FaboAnalyzer
from src.email_sender import EmailSender


def setup_logging(level: str = "INFO"):
    """设置日志配置"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("analysis.log"), logging.StreamHandler()],
    )


def load_email_recipients(recipients_file: str = "email_recipients.json"):
    """加载邮件接收者列表"""
    try:
        with open(recipients_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("recipients", [])
    except FileNotFoundError:
        logging.warning(f"邮件接收者文件 {recipients_file} 不存在，使用默认配置")
        return []
    except json.JSONDecodeError:
        logging.error(f"邮件接收者文件 {recipients_file} 格式错误")
        return []


def get_latest_analysis_images():
    """获取最新的分析结果图片文件"""
    try:
        # 查找所有PNG图片文件
        image_patterns = ["analysis_results/**/*.png", "analysis_results/*.png"]

        image_files = []
        for pattern in image_patterns:
            files = glob.glob(pattern, recursive=True)
            image_files.extend(files)

        # 去重并排序
        image_files = sorted(list(set(image_files)))

        if image_files:
            logging.info(f"找到 {len(image_files)} 个分析结果图片文件")
            return image_files
        else:
            logging.warning("未找到分析结果图片文件")
            return []

    except Exception as e:
        logging.error(f"获取分析结果图片失败: {e}")
        return []


def run_harmonic_analysis(config: AnalysisConfig):
    """运行谐波分析"""
    logging.info("开始谐波分析...")

    for stock_code in config.harmonic.default_stock_codes:
        logging.info(f"分析股票代码: {stock_code}")
        analyzer = HarmonicAnalyzer(
            stock_code=stock_code,
            years=config.harmonic.analysis_years,
        )
        analyzer.analyze(config.harmonic.frequencies)


def run_probability_analysis(config: AnalysisConfig):
    """运行概率转移矩阵分析"""
    logging.info("开始概率转移矩阵分析...")
    
    # 存储所有分析结果
    probability_results = []
    
    for stock_code in config.harmonic.default_stock_codes:
        logging.info(f"分析股票代码: {stock_code}")
        analyzer = ProbabilityAnalyzer(
            stock_code=stock_code,
            years=config.harmonic.analysis_years,
        )
        
        # 执行分析
        result = analyzer.analyze()
        
        # 打印分析结果
        analyzer.print_analysis_result(result)
        
        # 保存结果
        probability_results.append({
            "stock_code": stock_code,
            "result": result,
            "analyzer": analyzer
        })
    
    logging.info("概率转移矩阵分析完成！")
    
    return probability_results


def run_fx_analysis(config: AnalysisConfig):
    """运行外汇汇率分析"""
    logging.info("开始外汇汇率分析...")
    
    # 创建外汇分析器实例
    analyzer = FxAnalyzer(
        years=config.harmonic.analysis_years,
    )
    
    # 执行分析
    result = analyzer.analyze()
    
    # 打印分析结果
    analyzer.print_analysis_result(result)
    
    logging.info("外汇汇率分析完成！")
    
    return {
        "result": result,
        "analyzer": analyzer
    }


def run_gold_analysis(config: AnalysisConfig):
    """运行黄金现货价格分析"""
    logging.info("开始黄金现货价格分析...")
    
    analyzer = GoldAnalyzer(
        years=config.harmonic.analysis_years,
    )
    
    result = analyzer.analyze()
    analyzer.print_analysis_result(result)
    
    logging.info("黄金现货价格分析完成！")
    
    return {
        "result": result,
        "analyzer": analyzer
    }


def run_fabo_analysis(config: AnalysisConfig):
    """运行斐波那契分析"""
    logging.info("开始斐波那契分析...")
    
    analyzer = FaboAnalyzer(
        years=config.harmonic.analysis_years,
    )
    
    result = analyzer.analyze()
    analyzer.print_analysis_result(result)
    
    logging.info("斐波那契分析完成！")
    
    return {
        "result": result,
        "analyzer": analyzer
    }


def run_daily_analysis():
    """执行每日分析任务"""
    try:
        logging.info("开始执行每日分析任务...")

        # 加载配置
        config = AnalysisConfig()

        # 运行所有分析
        run_harmonic_analysis(config)
        probability_results = run_probability_analysis(config)
        fx_results = run_fx_analysis(config)
        gold_results = run_gold_analysis(config)
        fabo_results = run_fabo_analysis(config)

        logging.info("每日分析任务完成！")

        # 发送邮件
        send_analysis_email(probability_results, fx_results, gold_results, fabo_results)

    except Exception as e:
        logging.error(f"每日分析任务执行失败: {e}")
        # 发送错误通知邮件
        send_error_email(str(e))


def generate_html_email_body(image_files=None, probability_results=None, fx_results=None, gold_results=None, fabo_results=None):
    """生成HTML格式的邮件正文，包含嵌入的图片和概率分析结果"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 分离并排序图片
    fx_images = []
    gold_images = []
    fabo_images = []
    daily_images = []
    weekly_images = []
    other_images = []
    
    if image_files:
        for i, img_path in enumerate(image_files):
            img_name = os.path.basename(img_path)
            if "fx_cny" in img_name:
                fx_images.append((i, img_path, "外汇汇率分析"))
            elif "gold_price" in img_name:
                gold_images.append((i, img_path, "黄金现货价格分析"))
            elif "fibonacci" in img_name:
                fabo_images.append((i, img_path, "斐波那契分析"))
            elif "Daily" in img_name:
                daily_images.append((i, img_path, "Daily Analysis"))
            elif "Weekly" in img_name:
                weekly_images.append((i, img_path, "Weekly Analysis"))
            else:
                other_images.append((i, img_path, "Analysis"))
    
    # 生成外汇分析结果HTML代码 - 作为独立block
    fx_html = ""
    if fx_results:
        analyzer = fx_results["analyzer"]
        analysis_result = fx_results["result"]
        
        # 生成外汇分析HTML
        fx_content = analyzer.generate_email_content(analysis_result)
        
        # 添加外汇分析图表
        fx_charts = ""
        if fx_images:
            fx_charts = """
            <h2>📊 外汇汇率分析图表</h2>
            <p>以下是外汇汇率分析生成的图表：</p>
            """
            for i, img_path, desc in fx_images:
                fx_charts += f"""
                <div class="image-container">
                    <h3>{desc}</h3>
                    <img src="cid:image_{i}" alt="{desc}" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; margin: 10px 0;">
                    <p class="image-caption">文件名: {os.path.basename(img_path)}</p>
                </div>
                """
        
        # 整合为完整的外汇分析block
        fx_html = f"""
        <div class="analysis-block">
            <div class="analysis-block-header">
                <h2>💱 外汇汇率分析</h2>
            </div>
            <div class="analysis-block-content">
                {fx_content}
                {fx_charts}
            </div>
        </div>
        """
    
    # 生成黄金分析结果HTML代码 - 作为独立block
    gold_html = ""
    if gold_results:
        analyzer = gold_results["analyzer"]
        analysis_result = gold_results["result"]
        
        # 生成黄金分析HTML
        gold_content = analyzer.generate_email_content(analysis_result)
        
        # 添加黄金分析图表
        gold_charts = ""
        if gold_images:
            gold_charts = """
            <h2>📊 黄金现货价格分析图表</h2>
            <p>以下是黄金现货价格分析生成的图表：</p>
            """
            for i, img_path, desc in gold_images:
                gold_charts += f"""
                <div class="image-container">
                    <h3>{desc}</h3>
                    <img src="cid:image_{i}" alt="{desc}" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; margin: 10px 0;">
                    <p class="image-caption">文件名: {os.path.basename(img_path)}</p>
                </div>
                """
        
        # 整合为完整的黄金分析block
        gold_html = f"""
        <div class="analysis-block">
            <div class="analysis-block-header">
                <h2>✨ 黄金现货价格分析</h2>
            </div>
            <div class="analysis-block-content">
                {gold_content}
                {gold_charts}
            </div>
        </div>
        """
    
    # 生成斐波那契分析结果HTML代码 - 作为独立block
    fabo_html = ""
    if fabo_results:
        analyzer = fabo_results["analyzer"]
        analysis_result = fabo_results["result"]
        
        # 生成斐波那契分析HTML
        fabo_content = analyzer.generate_email_content(analysis_result)
        
        # 添加斐波那契分析图表
        fabo_charts = ""
        if fabo_images:
            fabo_charts = """
            <h2>📊 斐波那契分析图表</h2>
            <p>以下是斐波那契分析生成的图表：</p>
            """
            for i, img_path, desc in fabo_images:
                fabo_charts += f"""
                <div class="image-container">
                    <h3>{desc}</h3>
                    <img src="cid:image_{i}" alt="{desc}" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; margin: 10px 0;">
                    <p class="image-caption">文件名: {os.path.basename(img_path)}</p>
                </div>
                """
        
        # 整合为完整的斐波那契分析block
        fabo_html = f"""
        <div class="analysis-block">
            <div class="analysis-block-header">
                <h2>📐 斐波那契分析</h2>
            </div>
            <div class="analysis-block-content">
                {fabo_content}
                {fabo_charts}
            </div>
        </div>
        """
    
    # 生成谐波分析图表HTML代码 - 作为独立block
    harmonic_images_html = ""
    if daily_images or weekly_images:
        harmonic_charts = ""
        # 日线分析图
        for i, img_path, desc in daily_images:
            harmonic_charts += f"""
            <div class="image-container">
                <h3>{desc}</h3>
                <img src="cid:image_{i}" alt="{desc}" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; margin: 10px 0;">
                <p class="image-caption">文件名: {os.path.basename(img_path)}</p>
            </div>
            """
        # 周线分析图
        for i, img_path, desc in weekly_images:
            harmonic_charts += f"""
            <div class="image-container">
                <h3>{desc}</h3>
                <img src="cid:image_{i}" alt="{desc}" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; margin: 10px 0;">
                <p class="image-caption">文件名: {os.path.basename(img_path)}</p>
            </div>
            """
        
        # 整合为完整的谐波分析block
        harmonic_images_html = f"""
        <div class="analysis-block">
            <div class="analysis-block-header">
                <h2>📈 谐波分析</h2>
            </div>
            <div class="analysis-block-content">
                <h3>📊 谐波分析图表</h3>
                <p>以下是谐波分析生成的图表：</p>
                {harmonic_charts}
            </div>
        </div>
        """
    
    # 生成其他图表HTML代码 - 作为独立block
    other_images_html = ""
    if other_images:
        other_charts = ""
        for i, img_path, desc in other_images:
            other_charts += f"""
            <div class="image-container">
                <h3>{desc}</h3>
                <img src="cid:image_{i}" alt="{desc}" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; margin: 10px 0;">
                <p class="image-caption">文件名: {os.path.basename(img_path)}</p>
            </div>
            """
        
        # 整合为完整的其他分析block
        other_images_html = f"""
        <div class="analysis-block">
            <div class="analysis-block-header">
                <h2>📊 其他分析图表</h2>
            </div>
            <div class="analysis-block-content">
                <p>以下是其他分析生成的图表：</p>
                {other_charts}
            </div>
        </div>
        """
    
    # 生成概率分析结果HTML代码 - 作为独立block
    probability_html = ""
    if probability_results:
        prob_content = ""
        for result in probability_results:
            stock_code = result["stock_code"]
            analyzer = result["analyzer"]
            analysis_result = result["result"]
            
            # 生成当前股票的概率分析HTML
            stock_probability_html = analyzer.generate_email_content(analysis_result)
            prob_content += f"""
            <h2>📈 {stock_code} 概率转移矩阵分析</h2>
            {stock_probability_html}
            """
        
        # 整合为完整的概率分析block
        probability_html = f"""
        <div class="analysis-block">
            <div class="analysis-block-header">
                <h2>🎲 概率转移矩阵分析</h2>
            </div>
            <div class="analysis-block-content">
                {prob_content}
            </div>
        </div>
        """

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>金融数据分析报告</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f7fa;
            }}
            .header {{
                background-color: #2c3e50;
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 30px;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .content {{
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            /* 新增的分析block样式 */
            .analysis-block {{
                margin: 30px 0;
                border-radius: 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                overflow: hidden;
                background-color: white;
                border: 1px solid #e1e8ed;
            }}
            .analysis-block-header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
            }}
            .analysis-block-header h2 {{
                margin: 0;
                font-size: 22px;
                font-weight: bold;
            }}
            .analysis-block-content {{
                padding: 25px;
            }}
            /* 增强的分析section样式 */
            .analysis-section {{
                margin: 20px 0;
                padding: 15px;
                background-color: #f8fafc;
                border-radius: 8px;
                border-left: 4px solid #3498db;
            }}
            /* 增强的标题样式 */
            h2 {{
                color: #2c3e50;
                margin-top: 0;
                margin-bottom: 20px;
                font-size: 20px;
                border-bottom: 2px solid #ecf0f1;
                padding-bottom: 10px;
            }}
            h3 {{
                color: #34495e;
                margin-top: 20px;
                margin-bottom: 15px;
                font-size: 18px;
            }}
            /* 增强的图片容器样式 */
            .image-row {{
                display: flex;
                justify-content: space-between;
                gap: 20px;
                margin: 20px 0;
            }}
            .image-container {{
                flex: 1;
                padding: 20px;
                background-color: #f8fafc;
                border-radius: 8px;
                text-align: center;
                margin: 15px 0;
                border: 1px solid #e1e8ed;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }}
            .image-caption {{
                color: #666;
                font-size: 0.9em;
                margin-top: 15px;
                font-style: italic;
            }}
            /* 增强的表格样式 */
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }}
            th, td {{
                border: 1px solid #e1e8ed;
                padding: 12px;
                text-align: left;
            }}
            th {{
                background-color: #f8fafc;
                font-weight: bold;
                color: #2c3e50;
            }}
            tr:nth-child(even) {{
                background-color: #f8fafc;
            }}
            /* 增强的footer样式 */
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 2px solid #ecf0f1;
                text-align: center;
                color: #666;
                font-size: 0.9em;
            }}
            .highlight {{
                background-color: #f39c12;
                color: white;
                padding: 3px 8px;
                border-radius: 4px;
                font-weight: bold;
            }}
            /* 增强的段落样式 */
            p {{
                margin-bottom: 15px;
                line-height: 1.7;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 金融数据分析报告</h1>
            <p>{current_time}</p>
        </div>
        
        <div class="content">
            {fx_html}
            {gold_html}
            {harmonic_images_html}
            {fabo_html}
            {probability_html}
            {other_images_html}
        </div>
    </body>
    </html>
    """

    return html_body


def send_analysis_email(probability_results=None, fx_results=None, gold_results=None, fabo_results=None):
    """发送分析结果邮件"""
    try:
        # 加载环境变量
        load_dotenv()

        # 邮件配置
        email_config = {
            "sender": os.getenv("EMAIL_SENDER"),
            "password": os.getenv("NETEASE_EMAIL_PASSWORD"),
            "smtp_server": os.getenv("SMTP_SERVER"),
            "smtp_port": int(os.getenv("SMTP_PORT", 465)),
        }

        # 检查配置完整性
        if not all(email_config.values()):
            logging.error("邮件配置不完整，请检查.env文件")
            return

        # 加载接收者
        recipients = load_email_recipients()
        if not recipients:
            logging.warning("没有配置邮件接收者")
            return

        # 创建邮件发送器
        email_sender = EmailSender(email_config)

        # 获取分析结果图片
        image_files = get_latest_analysis_images()
        
        # 如果有外汇分析结果，将外汇图表添加到图片列表中
        if fx_results and fx_results['result']['plot_path']:
            fx_plot_path = fx_results['result']['plot_path']
            if fx_plot_path not in image_files:
                image_files.append(fx_plot_path)
        
        # 如果有黄金分析结果，将黄金图表添加到图片列表中
        if gold_results and gold_results['result']['plot_path']:
            gold_plot_path = gold_results['result']['plot_path']
            if gold_plot_path not in image_files:
                image_files.append(gold_plot_path)
        
        # 如果有斐波那契分析结果，将斐波那契图表添加到图片列表中
        if fabo_results:
            # 添加压力位图表
            if fabo_results['result']['resistance_chart']:
                resistance_chart_path = fabo_results['result']['resistance_chart']
                if resistance_chart_path not in image_files:
                    image_files.append(resistance_chart_path)
            # 添加支撑位图表
            if fabo_results['result']['support_chart']:
                support_chart_path = fabo_results['result']['support_chart']
                if support_chart_path not in image_files:
                    image_files.append(support_chart_path)

        # 生成邮件内容
        subject = f"金融数据分析报告 - {datetime.now().strftime('%Y-%m-%d')}"

        # 发送邮件
        for recipient in recipients:
            try:
                if image_files:
                    # 选择主要的图片嵌入到邮件正文中
                    main_images = []

                    # 分别选择日线、周线的综合趋势分析图、外汇分析图、黄金分析图和斐波那契分析图
                    daily_images = []
                    weekly_images = []
                    fx_images = []
                    gold_images = []
                    fabo_images = []

                    for img in image_files:
                        if "Daily" in img:
                            daily_images.append(img)
                        elif "Weekly" in img:
                            weekly_images.append(img)
                        elif "fx_cny" in img:
                            fx_images.append(img)
                        elif "gold_price" in img:
                            gold_images.append(img)
                        elif "fibonacci" in img:
                            fabo_images.append(img)

                    # 选择最新的图片（按文件名排序）
                    if fx_images:
                        fx_images.sort()
                        main_images.append(fx_images[-1])
                    if gold_images:
                        gold_images.sort()
                        main_images.append(gold_images[-1])
                    if fabo_images:
                        fabo_images.sort()
                        # 添加所有斐波那契图片（压力位和支撑位）
                        for img in fabo_images:
                            main_images.append(img)
                    if daily_images:
                        daily_images.sort()
                        main_images.append(daily_images[-1])
                    if weekly_images:
                        weekly_images.sort()
                        main_images.append(weekly_images[-1])

                    if main_images:
                        logging.info(
                            f"发送带 {len(main_images)} 个嵌入图片的邮件给: {recipient}"
                        )
                        # 生成包含图片和概率分析结果的HTML邮件正文
                        html_body = generate_html_email_body(main_images, probability_results, fx_results, gold_results, fabo_results)
                        # 发送带嵌入图片的HTML邮件
                        email_sender.send_email_with_embedded_images(
                            recipient, subject, html_body, main_images
                        )
                    else:
                        # 发送普通HTML邮件
                        html_body = generate_html_email_body(None, probability_results, fx_results, gold_results, fabo_results)
                        email_sender.send_email(
                            recipient, subject, html_body, is_html=True
                        )
                else:
                    # 发送普通HTML邮件
                    html_body = generate_html_email_body(None, probability_results, fx_results, gold_results, fabo_results)
                    email_sender.send_email(recipient, subject, html_body, is_html=True)

                logging.info(f"成功发送邮件给: {recipient}")

            except Exception as e:
                logging.error(f"发送邮件给 {recipient} 失败: {e}")

    except Exception as e:
        logging.error(f"发送邮件失败: {e}")


def send_error_email(error_msg: str):
    """发送错误通知邮件"""
    try:
        # 加载环境变量
        load_dotenv()

        # 邮件配置
        email_config = {
            "sender": os.getenv("EMAIL_SENDER"),
            "password": os.getenv("NETEASE_EMAIL_PASSWORD"),
            "smtp_server": os.getenv("SMTP_SERVER"),
            "smtp_port": int(os.getenv("SMTP_PORT", 465)),
        }

        # 检查配置完整性
        if not all(email_config.values()):
            logging.error("邮件配置不完整，无法发送错误通知")
            return

        # 加载接收者
        recipients = load_email_recipients()
        if not recipients:
            logging.warning("没有配置邮件接收者，无法发送错误通知")
            return

        # 创建邮件发送器
        email_sender = EmailSender(email_config)

        # 生成错误邮件内容
        subject = f"金融数据分析任务执行失败 - {datetime.now().strftime('%Y-%m-%d')}"
        body = f"""
        分析任务执行失败！

        错误时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        错误信息: {error_msg}

        请检查日志文件获取详细信息。
        """

        # 发送邮件
        for recipient in recipients:
            try:
                email_sender.send_email(recipient, subject, body)
                logging.info(f"成功发送错误通知邮件给: {recipient}")
            except Exception as e:
                logging.error(f"发送错误通知邮件给 {recipient} 失败: {e}")

    except Exception as e:
        logging.error(f"发送错误通知邮件失败: {e}")


def run_once():
    """运行一次分析（用于测试）"""
    logging.info("执行单次分析...")
    run_daily_analysis()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="金融数据分析模块 - 定时版本")
    parser.add_argument(
        "--mode",
        choices=["schedule", "once"],
        default="schedule",
        help="运行模式: schedule(定时运行), once(运行一次)",
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
    run_time = "16:30"

    if args.mode == "once":
        # 运行一次
        run_once()
    else:
        # 定时运行模式
        logging.info("启动定时任务模式...")

        # 设置定时任务 - 每天下午3点05分执行
        schedule.every().day.at(run_time).do(run_daily_analysis)

        logging.info(f"定时任务已设置，每天{run_time}执行分析")
        logging.info("程序正在运行中，按 Ctrl+C 停止...")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            logging.info("程序被用户中断")
        except Exception as e:
            logging.error(f"程序运行出错: {e}")


if __name__ == "__main__":
    main()
