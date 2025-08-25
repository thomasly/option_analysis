# 迁移自主项目 src/core/fft_email_service.py
import os
import logging
from datetime import datetime, time
from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import smtplib

from .fft_analyzer import FFTAnalyzer
from src.config import AppConfig

logger = logging.getLogger(__name__)

# ... 其余内容保持不变，直接粘贴原文件内容 ...
