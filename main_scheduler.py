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
from src.core import (
    FFTAnalyzer,
    # CauchyCorrelationAnalyzer,
    # CorrelationAnalysisConfig,
    HarmonicAnalyzer,
)
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


def run_fft_analysis(config: AnalysisConfig):
    """运行FFT分析"""
    logging.info("开始FFT分析...")

    for stock_code in config.fft.default_stock_codes:
        logging.info(f"分析股票代码: {stock_code}")
        analyzer = FFTAnalyzer(
            stock_code=stock_code,
            years=config.fft.analysis_years,
            num_components=config.fft.num_components,
        )
        analyzer.analyze(config.fft.frequencies)


def run_harmonic_analysis(config: AnalysisConfig):
    """运行FFT分析"""
    logging.info("开始FFT分析...")

    for stock_code in config.harmonic.default_stock_codes:
        logging.info(f"分析股票代码: {stock_code}")
        analyzer = HarmonicAnalyzer(
            stock_code=stock_code,
            years=config.harmonic.analysis_years,
        )
        analyzer.analyze(config.harmonic.frequencies)


# def run_correlation_analysis(config: AnalysisConfig):
#     """运行相关性分析"""
#     logging.info("开始相关性分析...")

#     correlation_config = CorrelationAnalysisConfig(
#         index_code=config.correlation.index_code,
#         years=config.correlation.years,
#         freq=config.correlation.freq,
#         n_days=config.correlation.n_days,
#         start_idx=config.correlation.start_idx,
#         x_min=config.correlation.x_min,
#         x_max=config.correlation.x_max,
#         n_centers=config.correlation.n_centers,
#         n_gammas=config.correlation.n_gammas,
#         gamma_min=config.correlation.gamma_min,
#         gamma_max=config.correlation.gamma_max,
#         analysis_dir=config.correlation.analysis_dir,
#         index_power=config.correlation.index_power,
#     )

#     analyzer = CauchyCorrelationAnalyzer(correlation_config)
#     analyzer.run()


def run_daily_analysis():
    """执行每日分析任务"""
    try:
        logging.info("开始执行每日分析任务...")

        # 加载配置
        config = AnalysisConfig()

        # 运行所有分析
        # run_fft_analysis(config)
        # run_correlation_analysis(config)
        run_harmonic_analysis(config)

        logging.info("每日分析任务完成！")

        # 发送邮件
        send_analysis_email()

    except Exception as e:
        logging.error(f"每日分析任务执行失败: {e}")
        # 发送错误通知邮件
        send_error_email(str(e))


def generate_html_email_body(image_files=None):
    """生成HTML格式的邮件正文，包含嵌入的图片"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 生成图片HTML代码
    images_html = ""
    if image_files:
        images_html = """
            <h2>📊 分析结果图表</h2>
            <p>以下是本次分析生成的关键图表：</p>
        """

        # 创建左右排列的图片布局
        if len(image_files) >= 2:
            # 第一行：两张图片左右排列
            images_html += """
            <div class="image-row">
            """

            for i in range(min(2, len(image_files))):
                img_path = image_files[i]
                img_name = os.path.basename(img_path)
                if "Weekly" in img_name:
                    desc = "Weekly Analysis"
                elif "Daily" in img_name:
                    desc = "Daily Analysis"
                else:
                    desc = "Analysis"

                images_html += f"""
                <div class="image-container">
                    <h3>{desc}</h3>
                    <img src="cid:image_{i}" alt="{desc}" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; margin: 10px 0;">
                    <p class="image-caption">文件名: {img_name}</p>
                </div>
                """

            images_html += """
            </div>
            """
        else:
            # 如果只有一张图片，使用原来的布局
            for i, img_path in enumerate(image_files):
                img_name = os.path.basename(img_path)
                if "Weekly" in img_name:
                    desc = "Weekly Analysis"
                elif "Daily" in img_name:
                    desc = "Daily Analysis"
                else:
                    desc = "Analysis"

                images_html += f"""
                <div class="image-container">
                    <h3>{desc}</h3>
                    <img src="cid:image_{i}" alt="{desc}" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; margin: 10px 0;">
                    <p class="image-caption">文件名: {img_name}</p>
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
            }}
            .header {{
                background-color: #2c3e50;
                color: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
                text-align: center;
            }}
            .content {{
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .analysis-section {{
                margin: 20px 0;
                padding: 15px;
                background-color: #ecf0f1;
                border-radius: 5px;
                border-left: 4px solid #3498db;
            }}
            .image-row {{
                display: flex;
                justify-content: space-between;
                gap: 20px;
                margin: 20px 0;
            }}
            .image-container {{
                flex: 1;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 5px;
                text-align: center;
            }}
            .image-caption {{
                color: #666;
                font-size: 0.9em;
                margin-top: 10px;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                text-align: center;
                color: #666;
            }}
            .highlight {{
                background-color: #f39c12;
                color: white;
                padding: 2px 6px;
                border-radius: 3px;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 金融数据分析报告</h1>
            <p>{current_time}</p>
        </div>
        
        <div class="content">
            {images_html}
        </div>
    </body>
    </html>
    """

    return html_body


def send_analysis_email():
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

        # 生成邮件内容
        subject = f"金融数据分析报告 - {datetime.now().strftime('%Y-%m-%d')}"

        # 发送邮件
        for recipient in recipients:
            try:
                if image_files:
                    # 选择主要的图片嵌入到邮件正文中
                    main_images = []

                    # 分别选择日线和周线的综合趋势分析图
                    daily_images = []
                    weekly_images = []

                    for img in image_files:
                        if "Daily" in img:
                            daily_images.append(img)
                        elif "Weekly" in img:
                            weekly_images.append(img)

                    # 选择最新的图片（按文件名排序，选择最后一个）
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
                        # 生成包含图片的HTML邮件正文
                        html_body = generate_html_email_body(main_images)
                        # 发送带嵌入图片的HTML邮件
                        email_sender.send_email_with_embedded_images(
                            recipient, subject, html_body, main_images
                        )
                    else:
                        # 发送普通HTML邮件
                        html_body = generate_html_email_body()
                        email_sender.send_email(
                            recipient, subject, html_body, is_html=True
                        )
                else:
                    # 发送普通HTML邮件
                    html_body = generate_html_email_body()
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

    if args.mode == "once":
        # 运行一次
        run_once()
    else:
        # 定时运行模式
        logging.info("启动定时任务模式...")

        # 设置定时任务 - 每天下午3点05分执行
        schedule.every().day.at("15:05").do(run_daily_analysis)

        logging.info("定时任务已设置，每天下午3:05执行分析")
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
