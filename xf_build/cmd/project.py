
import logging
import shutil
from pathlib import Path
import os
from rich.panel import Panel
from rich.text import Text
from rich.console import Console
from art import text2art
import json

from ..menuconfig import MenuConfig
from ..env import is_project
from ..env import run_build
from ..env import clean_project_build
from ..env import ENTER_SCRIPT, EXPORT_SCRIPT
from ..env import ROOT_TEMPLATE_PATH, XF_ROOT
from ..env import PROJECT_CONFIG_PATH, PROJECT_BUILD_PATH
from ..env import XF_TARGET, XF_TARGET_PATH

from serial.tools.miniterm import Miniterm
import serial


def build():
    is_project(".")

    logging.info("run build")
    run_build()


def clean():
    is_project(".")
    clean_project_build()


def menuconfig():
    is_project(".")
    run_build()
    config = MenuConfig(PROJECT_CONFIG_PATH,
                        XF_TARGET_PATH, PROJECT_BUILD_PATH)
    config.start()


def create(name):
    name = Path(name)
    abspath = name.resolve()
    if abspath.exists():
        logging.error(f"工程已存在:{abspath}")
        return
    logging.info("正在生成模板工程。。。")
    try:
        shutil.copytree(ROOT_TEMPLATE_PATH, abspath)
        logging.info("生成模板工程成功！")
    except Exception as e:
        logging.error(f"发生错误: {e}")


def before_export(name):
    is_project(".")

    def is_subdirectory(parent: Path, child: Path) -> bool:
        """
        判断一个文件夹是否是另一个文件夹的子文件夹。

        :param child: 子文件夹的路径
        :param parent: 父文件夹的路径
        :return: 如果 child 是 parent 的子文件夹，则返回 True，否则返回 False
        """
        try:
            # 解析路径以获得绝对路径
            parent = parent.resolve()
            child = child.resolve()
            # 通过相对路径检查父子关系
            child.relative_to(parent)
            return True
        except ValueError:
            return False

    name = Path(name)
    current_path = Path(".").resolve()

    if not (current_path / ENTER_SCRIPT).exists():
        logging.error("请在正确的xfusion工程下导出，或者指定xfusion工程路径-p/--path")
        return
    if name.exists():
        logging.error("文件夹已存在，如想更新，则通过update命令更新导出")
        return

    name_abspath = name.resolve()

    if is_subdirectory(name_abspath, current_path):
        logging.error("导出sdk工程文件夹不能是xfusion工程的子文件夹")
        return

    run_build(False)

    return name_abspath


def before_update(name):
    is_project(".")
    name = Path(name)
    current_path = Path(".").resolve()
    if not (current_path / ENTER_SCRIPT).exists():
        logging.error("请在正确的工程下导出，或者指定路径-p/--path")
        return
    if not name.exists():
        logging.error("文件夹不存在，如想导出，则通过export命令更新导出")
        return
    if not current_path.exists():
        logging.error(f"path路径不存在，请确认：{current_path}")
        return
    name_abspath = name.resolve()
    run_build(False)
    return name_abspath


def monitor(port, baud=115200):
    if os.linesep == "\r\n":
        linesep = "crlf"
    else:
        linesep = "lf"

    serial_instance = serial.Serial(port, baud)

    # 设置流控信号拉低
    serial_instance.rts = False  # 拉低 RTS
    serial_instance.dtr = False  # 拉低 DTR
    miniterm = Miniterm(serial_instance, echo=True, eol=linesep)
    miniterm.set_rx_encoding('utf-8')
    miniterm.set_tx_encoding('utf-8')
    miniterm.start()  # 启动读写线程
    miniterm.join()   # 阻塞等待


def show_target():
    console = Console()

    # 创建彩色文本
    target_art = text2art(XF_TARGET)
    target_text = Text(f"{target_art}", style="bold magenta")
    target_path_text = Text(f"{XF_TARGET_PATH}", style="bold cyan")

    # 使用 Panel 包装输出
    console.print(Panel(target_text, title="🔍 Target",
                  subtitle="XF_TARGET", expand=False))
    console.print(Panel(target_path_text, title="📁 Path",
                  subtitle="XF_TARGET_PATH", expand=False))


def download_sdk():
    target_json_path = Path(XF_TARGET_PATH) / "target.json"
    if not target_json_path.exists():
        raise Exception("target.json文件不存在")

    with target_json_path.open("r", encoding="utf-8") as f:
        target_json = json.load(f)

    if not target_json.get("sdks"):
        logging.error("未找到需要下载的sdk")
        return

    if not target_json["sdks"].get("dir"):
        logging.error("需要配置SDK下载的文件夹位置")
        return

    if not target_json["sdks"].get("url"):
        logging.error("需要配置SDK下载的url")
        return

    if (XF_ROOT/"sdks"/target_json["sdks"]["dir"]).exists():
        logging.info("SDK已下载，无需重复下载")
        return

    logging.info("开始下载SDK")
    url = target_json["sdks"]["url"]
    dir = XF_ROOT/"sdks"/target_json["sdks"]["dir"]
    commit = target_json["sdks"].get("commit")
    branch = target_json["sdks"].get("branch")
    logging.info(f"下载SDK地址:{url}")
    logging.info(f"下载SDK文件夹位置:{dir}")
    if not branch:
        os.system("git clone --depth 1 %s %s" % (url, dir))
    else:
        os.system("git clone --depth 1 -b %s %s %s" % (branch, url, dir))
    os.chdir(dir)
    if commit:
        os.system("git fetch --depth=1 origin %s" % (commit))
        os.system("git reset --hard %s" % (commit))


def simulate():
    is_project(".")
    cmd = []
    cmd.append(f"source {EXPORT_SCRIPT} sim_linux")
    cmd.append("xf build")
    cmd.append("xf flash")
    cmd_str = "&&".join(cmd)
    os.system(cmd_str)
