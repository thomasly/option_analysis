#!/bin/bash

# 金融数据分析定时任务启动脚本

echo "启动金融数据分析定时任务..."
echo "程序将在每天下午3:05自动执行分析并发送邮件"
echo "按 Ctrl+C 可以停止程序"
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查依赖
echo "检查Python依赖..."
python3 -c "import schedule, dotenv" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "安装Python依赖..."
    pip3 install -r requirements.txt
fi

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "警告: 未找到 .env 配置文件"
    echo "请复制 env_template.txt 为 .env 并填写您的邮箱配置"
    echo ""
fi

if [ ! -f "email_recipients.json" ]; then
    echo "警告: 未找到 email_recipients.json 配置文件"
    echo "请配置邮件接收者列表"
    echo ""
fi

# 启动程序
echo "启动分析程序..."
python3 main_scheduler.py --mode schedule
