
import logging
import shutil
from pathlib import Path
import json

from ..menuconfig import MenuConfig
from ..env import is_project
from ..env import run_build
from ..env import clean_project_build
from ..env import ENTER_SCRIPT, ROOT_PORT, ROOT_BOARDS
from ..env import ROOT_TEMPLATE_PATH, PROJECT_BUILD_ENV
from ..env import PROJECT_CONFIG_PATH, PROJECT_BUILD_PATH
from ..env import XF_ROOT, XF_TARGET_PATH


def build():
    if not is_project("."):
        logging.warning("该目录不是工程文件夹")
        return

    logging.info("run build")
    run_build()


def clean():
    if not is_project("."):
        logging.warning("该目录不是工程文件夹")
        return
    clean_project_build()


def menuconfig():
    if not is_project("."):
        logging.warning("该目录不是工程文件夹")
        return
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
    if not is_project("."):
        logging.warning("该目录不是工程文件夹")
        return

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

    run_build()

    return name_abspath


def before_update(name):
    if not is_project("."):
        logging.warning("该目录不是工程文件夹")
        return
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
    return name_abspath
