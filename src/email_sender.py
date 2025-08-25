#!/usr/bin/env python3
"""
邮件发送器模块
负责发送分析结果邮件，支持图片嵌入正文
"""

import smtplib
import logging
import base64
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.header import Header


class EmailSender:
    """邮件发送器类"""

    def __init__(self, config: dict):
        """
        初始化邮件发送器

        Args:
            config: 邮件配置字典，包含以下键：
                - sender: 发件人邮箱
                - password: 邮箱密码
                - smtp_server: SMTP服务器地址
                - smtp_port: SMTP服务器端口
        """
        self.sender = config["sender"]
        self.password = config["password"]
        self.smtp_server = config["smtp_server"]
        self.smtp_port = config["smtp_port"]

        # 验证配置
        if not all([self.sender, self.password, self.smtp_server, self.smtp_port]):
            raise ValueError("邮件配置不完整")

    def send_email(
        self, recipient: str, subject: str, body: str, is_html: bool = False
    ):
        """
        发送邮件

        Args:
            recipient: 收件人邮箱
            subject: 邮件主题
            body: 邮件正文
            is_html: 是否为HTML格式，默认为False（纯文本）
        """
        try:
            # 创建邮件对象
            msg = MIMEMultipart()
            msg["From"] = self.sender
            msg["To"] = recipient
            msg["Subject"] = Header(subject, "utf-8")

            # 设置邮件正文
            if is_html:
                msg.attach(MIMEText(body, "html", "utf-8"))
            else:
                msg.attach(MIMEText(body, "plain", "utf-8"))

            # 连接SMTP服务器并发送邮件
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender, self.password)
                server.send_message(msg)

            logging.info(f"成功发送邮件给 {recipient}")

        except smtplib.SMTPAuthenticationError:
            logging.error(f"SMTP认证失败，请检查邮箱和密码: {recipient}")
            raise
        except smtplib.SMTPRecipientsRefused:
            logging.error(f"收件人邮箱无效: {recipient}")
            raise
        except smtplib.SMTPServerDisconnected:
            logging.error("SMTP服务器连接断开")
            raise
        except Exception as e:
            logging.error(f"发送邮件失败: {e}")
            raise

    def send_email_with_embedded_images(
        self, recipient: str, subject: str, html_body: str, image_paths: list
    ):
        """
        发送带嵌入图片的HTML邮件

        Args:
            recipient: 收件人邮箱
            subject: 邮件主题
            html_body: HTML格式的邮件正文
            image_paths: 要嵌入的图片文件路径列表
        """
        try:
            # 创建邮件对象
            msg = MIMEMultipart("related")
            msg["From"] = self.sender
            msg["To"] = recipient
            msg["Subject"] = Header(subject, "utf-8")

            # 创建HTML部分
            html_part = MIMEText(html_body, "html", "utf-8")
            msg.attach(html_part)

            # 嵌入图片
            for i, image_path in enumerate(image_paths):
                try:
                    if os.path.exists(image_path):
                        with open(image_path, "rb") as img_file:
                            img_data = img_file.read()

                        # 创建图片MIME对象
                        img = MIMEImage(img_data)

                        # 设置Content-ID，用于HTML中引用
                        img_name = os.path.basename(image_path)
                        img.add_header("Content-ID", f"<image_{i}>")
                        img.add_header(
                            "Content-Disposition", "inline", filename=img_name
                        )

                        msg.attach(img)
                        logging.info(f"成功嵌入图片: {image_path}")
                    else:
                        logging.warning(f"图片文件不存在: {image_path}")

                except Exception as e:
                    logging.error(f"嵌入图片 {image_path} 失败: {e}")

            # 连接SMTP服务器并发送邮件
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender, self.password)
                server.send_message(msg)

            logging.info(f"成功发送带嵌入图片的邮件给 {recipient}")

        except Exception as e:
            logging.error(f"发送带嵌入图片的邮件失败: {e}")
            raise

    def send_email_with_attachment(
        self,
        recipient: str,
        subject: str,
        body: str,
        attachment_path: str,
        is_html: bool = False,
    ):
        """
        发送带附件的邮件

        Args:
            recipient: 收件人邮箱
            subject: 邮件主题
            body: 邮件正文
            attachment_path: 附件文件路径
            is_html: 是否为HTML格式，默认为False（纯文本）
        """
        try:
            from email.mime.base import MIMEBase
            from email import encoders

            # 创建邮件对象
            msg = MIMEMultipart()
            msg["From"] = self.sender
            msg["To"] = recipient
            msg["Subject"] = Header(subject, "utf-8")

            # 设置邮件正文
            if is_html:
                msg.attach(MIMEText(body, "html", "utf-8"))
            else:
                msg.attach(MIMEText(body, "plain", "utf-8"))

            # 添加附件
            try:
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())

                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f'attachment; filename= {Header(attachment_path.split("/")[-1], "utf-8")}',
                )
                msg.attach(part)

            except FileNotFoundError:
                logging.warning(f"附件文件不存在: {attachment_path}")

            # 连接SMTP服务器并发送邮件
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender, self.password)
                server.send_message(msg)

            logging.info(f"成功发送带附件的邮件给 {recipient}")

        except Exception as e:
            logging.error(f"发送带附件的邮件失败: {e}")
            raise

    def test_connection(self):
        """
        测试SMTP连接

        Returns:
            bool: 连接是否成功
        """
        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender, self.password)
                logging.info("SMTP连接测试成功")
                return True
        except Exception as e:
            logging.error(f"SMTP连接测试失败: {e}")
            return False
