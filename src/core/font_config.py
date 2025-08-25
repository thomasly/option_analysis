#!/usr/bin/env python3
"""
跨平台字体配置文件
解决Linux和Windows服务器上的中文字体显示问题
"""

import platform
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import logging
import os


def setup_chinese_font():
    """
    设置中文字体支持，自动适配不同操作系统
    """
    system = platform.system()
    logging.info(f"检测到操作系统: {system}")

    if system == "Linux":
        setup_linux_font()
    elif system == "Windows":
        setup_windows_font()
    elif system == "Darwin":  # macOS
        setup_macos_font()
    else:
        setup_fallback_font()


def setup_linux_font():
    """Linux系统字体配置"""
    logging.info("配置Linux系统中文字体...")

    # Linux常见中文字体
    linux_chinese_fonts = [
        "WenQuanYi Micro Hei",
        "WenQuanYi Zen Hei",
        "Noto Sans CJK SC",
        "Noto Sans CJK TC",
        "Noto Sans CJK JP",
        "Droid Sans Fallback",
        "AR PL UMing CN",
        "AR PL UKai CN",
        "DejaVu Sans",
    ]

    # 尝试设置字体
    for font in linux_chinese_fonts:
        try:
            # 检查字体是否可用
            font_path = fm.findfont(font)
            if font_path != fm.rcParams["font.sans-serif"][0]:
                plt.rcParams["font.sans-serif"] = [font] + plt.rcParams[
                    "font.sans-serif"
                ]
                logging.info(f"成功设置Linux中文字体: {font}")
                break
        except Exception as e:
            logging.debug(f"字体 {font} 不可用: {e}")
            continue

    # 如果没有找到中文字体，尝试安装字体
    if not has_chinese_font():
        install_linux_fonts()

    plt.rcParams["axes.unicode_minus"] = False


def setup_windows_font():
    """Windows系统字体配置"""
    logging.info("配置Windows系统中文字体...")

    # Windows常见中文字体
    windows_chinese_fonts = [
        "SimHei",
        "Microsoft YaHei",
        "SimSun",
        "NSimSun",
        "FangSong",
        "KaiTi",
    ]

    # 尝试设置字体
    for font in windows_chinese_fonts:
        try:
            font_path = fm.findfont(font)
            if font_path != fm.rcParams["font.sans-serif"][0]:
                plt.rcParams["font.sans-serif"] = [font] + plt.rcParams[
                    "font.sans-serif"
                ]
                logging.info(f"成功设置Windows中文字体: {font}")
                break
        except Exception as e:
            logging.debug(f"字体 {font} 不可用: {e}")
            continue

    plt.rcParams["axes.unicode_minus"] = False


def setup_macos_font():
    """macOS系统字体配置"""
    logging.info("配置macOS系统中文字体...")

    # macOS常见中文字体
    macos_chinese_fonts = [
        "PingFang SC",
        "Hiragino Sans GB",
        "STHeiti",
        "Arial Unicode MS",
    ]

    # 尝试设置字体
    for font in macos_chinese_fonts:
        try:
            font_path = fm.findfont(font)
            if font_path != fm.rcParams["font.sans-serif"][0]:
                plt.rcParams["font.sans-serif"] = [font] + plt.rcParams[
                    "font.sans-serif"
                ]
                logging.info(f"成功设置macOS中文字体: {font}")
                break
        except Exception as e:
            logging.debug(f"字体 {font} 不可用: {e}")
            continue

    plt.rcParams["axes.unicode_minus"] = False


def setup_fallback_font():
    """设置备用字体"""
    logging.warning("未知操作系统，使用备用字体配置")

    # 尝试使用系统默认字体
    fallback_fonts = ["DejaVu Sans", "Liberation Sans", "Arial"]

    for font in fallback_fonts:
        try:
            font_path = fm.findfont(font)
            if font_path != fm.rcParams["font.sans-serif"][0]:
                plt.rcParams["font.sans-serif"] = [font] + plt.rcParams[
                    "font.sans-serif"
                ]
                logging.info(f"设置备用字体: {font}")
                break
        except Exception:
            continue

    plt.rcParams["axes.unicode_minus"] = False


def has_chinese_font():
    """检查是否有可用的中文字体"""
    try:
        # 测试中文字符显示
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "测试中文", fontsize=12)
        plt.close(fig)
        return True
    except Exception:
        return False


def install_linux_fonts():
    """尝试安装Linux中文字体"""
    logging.info("尝试安装Linux中文字体...")

    try:
        import subprocess

        # 检测包管理器并安装字体
        if os.path.exists("/usr/bin/apt-get"):
            # Ubuntu/Debian
            subprocess.run(["sudo", "apt-get", "update"], check=False)
            subprocess.run(
                [
                    "sudo",
                    "apt-get",
                    "install",
                    "-y",
                    "fonts-wqy-microhei",
                    "fonts-wqy-zenhei",
                ],
                check=False,
            )
            logging.info("已尝试安装文泉驿字体")

        elif os.path.exists("/usr/bin/yum"):
            # CentOS/RHEL
            subprocess.run(
                [
                    "sudo",
                    "yum",
                    "install",
                    "-y",
                    "wqy-microhei-fonts",
                    "wqy-zenhei-fonts",
                ],
                check=False,
            )
            logging.info("已尝试安装文泉驿字体")

        elif os.path.exists("/usr/bin/dnf"):
            # Fedora
            subprocess.run(
                ["sudo", "dnf", "install", "-y", "google-noto-cjk-fonts"], check=False
            )
            logging.info("已尝试安装Noto CJK字体")

        # 更新字体缓存
        subprocess.run(["sudo", "fc-cache", "-fv"], check=False)
        logging.info("已更新字体缓存")

    except Exception as e:
        logging.warning(f"自动安装字体失败: {e}")
        logging.info("请手动安装中文字体包")


def get_available_fonts():
    """获取系统中可用的字体列表"""
    fonts = []
    for font in fm.fontManager.ttflist:
        try:
            fonts.append(font.name)
        except:
            continue
    return sorted(list(set(fonts)))


def test_chinese_display():
    """测试中文字符显示"""
    try:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.8, "金融数据分析系统", fontsize=20, ha="center", va="center")
        ax.text(0.5, 0.6, "FFT分析结果", fontsize=16, ha="center", va="center")
        ax.text(0.5, 0.4, "相关性分析", fontsize=16, ha="center", va="center")
        ax.text(0.5, 0.2, "测试时间: 2024年", fontsize=14, ha="center", va="center")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

        # 保存测试图片
        test_path = "chinese_font_test.png"
        plt.savefig(test_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        logging.info(f"中文字体测试完成，测试图片保存为: {test_path}")
        return True

    except Exception as e:
        logging.error(f"中文字体测试失败: {e}")
        return False


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)

    # 配置字体
    setup_chinese_font()

    # 测试字体
    if test_chinese_display():
        print("✓ 中文字体配置成功！")
    else:
        print("✗ 中文字体配置失败，请检查字体安装")

    # 显示可用字体
    print(f"\n可用字体数量: {len(get_available_fonts())}")
    print("前10个字体:", get_available_fonts()[:10])
