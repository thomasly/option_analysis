# 金融数据分析系统 - 定时任务版本

## 概述

这个版本在原有分析功能基础上，增加了定时任务和邮件发送功能。程序可以自动在每天下午3:05执行分析，并将结果通过邮件发送给指定接收者。

## 主要功能

- **定时分析**: 每天下午3:05自动执行FFT分析和相关性分析
- **邮件通知**: 分析完成后自动发送邮件报告
- **错误处理**: 分析失败时发送错误通知邮件
- **动态配置**: 邮件接收者列表可以随时修改，无需重启程序

## 文件结构

```
OptionAnalysis/
├── main_scheduler.py          # 新的主程序（定时版本）
├── main.py                   # 原有主程序（单次运行）
├── src/
│   ├── email_sender.py       # 邮件发送器模块
│   └── ...                   # 其他原有模块
├── email_recipients.json     # 邮件接收者配置文件
├── env_template.txt          # 环境变量配置模板
├── start_analysis.sh         # 启动脚本
├── test_email.py             # 邮件功能测试脚本
└── requirements.txt          # Python依赖列表
```

## 安装和配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置邮箱

复制 `env_template.txt` 为 `.env` 文件，并填写您的邮箱配置：

```bash
cp env_template.txt .env
```

编辑 `.env` 文件：

```env
EMAIL_SENDER=your_email@163.com
NETEASE_EMAIL_PASSWORD=your_authorization_password
SMTP_SERVER=smtp.163.com
SMTP_PORT=465
```

**重要提示**：
- 网易邮箱需要使用**授权密码**，不是登录密码
- 需要在邮箱设置中开启SMTP服务
- 请确保 `.env` 文件不会被提交到版本控制系统中

### 3. 配置邮件接收者

编辑 `email_recipients.json` 文件，添加接收者邮箱：

```json
{
    "recipients": [
        "recipient1@example.com",
        "recipient2@example.com"
    ]
}
```

## 使用方法

### 启动定时任务

使用启动脚本（推荐）：
```bash
chmod +x start_analysis.sh
./start_analysis.sh
```

或直接运行Python程序：
```bash
python3 main_scheduler.py --mode schedule
```

### 运行一次分析（测试）

```bash
python3 main_scheduler.py --mode once
```

### 测试邮件功能

```bash
python3 test_email.py
```

## 运行模式

### 定时模式 (schedule)
- 程序启动后会在后台运行
- 每天下午3:05自动执行分析
- 分析完成后发送邮件
- 按 `Ctrl+C` 可以停止程序

### 单次模式 (once)
- 立即执行一次分析
- 完成后发送邮件
- 程序执行完毕后自动退出

## 邮件功能

### 正常邮件
- 分析完成后自动发送
- 包含分析完成时间和内容概述
- 发送给所有配置的接收者

### 错误通知邮件
- 分析失败时自动发送
- 包含错误时间和错误信息
- 帮助管理员快速定位问题

### 邮件接收者管理
- 修改 `email_recipients.json` 文件即可更新接收者列表
- 程序每次发送邮件时都会重新读取该文件
- 无需重启程序

## 日志记录

程序运行时会生成 `analysis.log` 日志文件，记录：
- 分析执行情况
- 邮件发送状态
- 错误信息和异常

## 故障排除

### 常见问题

1. **SMTP认证失败**
   - 检查邮箱和密码是否正确
   - 确认使用的是授权密码，不是登录密码
   - 确认邮箱已开启SMTP服务

2. **邮件发送失败**
   - 检查网络连接
   - 确认SMTP服务器地址和端口正确
   - 查看日志文件获取详细错误信息

3. **定时任务不执行**
   - 确认程序正在运行
   - 检查系统时间是否正确
   - 查看日志文件确认任务状态

### 测试步骤

1. 先运行 `test_email.py` 测试邮件配置
2. 使用 `--mode once` 测试分析功能
3. 确认一切正常后再启动定时任务

## 安全注意事项

- 不要在代码中硬编码邮箱密码
- 定期更换邮箱授权密码
- 确保 `.env` 文件不被意外提交到版本控制
- 限制邮件接收者列表，避免垃圾邮件

## 技术支持

如果遇到问题，请：
1. 查看日志文件 `analysis.log`
2. 运行测试脚本 `test_email.py`
3. 检查配置文件的格式和内容
4. 确认网络和邮箱服务状态
