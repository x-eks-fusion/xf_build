
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


def scan_kconfig() -> MenuConfig:
    """
    扫描收集kconfig, 并生成头文件
    """
    logging.info("scan config")
    path: list = [
        XF_ROOT / MenuConfig.XFKCONFIG_NAME,
        ROOT_BOARDS / MenuConfig.XFKCONFIG_NAME,
    ]
    port_xfconfig = ROOT_PORT / MenuConfig.XFKCONFIG_NAME
    if port_xfconfig.exists():
        path.append(port_xfconfig)

    path_file: str = "\n".join([f'source "{i.as_posix()}"' for i in path])
    path_file += "\n"

    with PROJECT_BUILD_ENV.open("r", encoding="utf-8") as f:
        build_env = json.load(f)
        public_components =  [Path(i["path"]) for i in build_env["public_components"].values()]
        user_main = Path(build_env["user_main"]["path"])
        user_components =  [Path(i["path"]) for i in build_env["user_components"].values()]
        user_dirs =  [Path(i["path"]) for i in build_env["user_dirs"].values()]

    # public components 部分的处理
    if public_components != []:
        path_file += "menu \"public components\"\n"
        for i in public_components:
            public_component_xfconfig = i / MenuConfig.XFKCONFIG_NAME
            if not public_component_xfconfig.exists():
                continue
            public_component_config = "  menu \"" + i.name + "\"\n"
            public_component_config += "    source \"" + public_component_xfconfig.as_posix() + "\"\n"
            public_component_config += "  endmenu\n"
            path_file += public_component_config + "\n"
        path_file += "endmenu\n\n"

    # main 部分的处理
    user_main_xfconfig = user_main / MenuConfig.XFKCONFIG_NAME
    if user_main_xfconfig.exists():
        user_main_config = "menu \"main\"\n"
        user_main_config += "  source \"" + user_main_xfconfig.as_posix() + "\"\n"
        user_main_config += "endmenu\n"
        path_file += user_main_config + "\n"

    # components 部分的处理
    if user_components != []:
        path_file += "menu \"user components\"\n"
        for i in user_components:
            user_component_xfconfig = i / MenuConfig.XFKCONFIG_NAME
            if not user_component_xfconfig.exists():
                continue
            user_component_config = "  menu \"" + i.name + "\"\n"
            user_component_config += "    source \"" + user_component_xfconfig.as_posix() + "\"\n"
            user_component_config += "  endmenu\n"
            path_file += user_component_config + "\n"
        path_file += "endmenu\n\n"

    if user_dirs != []:
        # dirs 部分的处理
        path_file += "menu \"user dirs\"\n"
        for i in user_dirs:
            user_dir_xfconfig = i / MenuConfig.XFKCONFIG_NAME
            if not user_dir_xfconfig.exists():
                continue
            user_dir_config = "  menu \"" + i.name + "\"\n"
            user_dir_config += "    source \"" + user_dir_xfconfig.as_posix() + "\"\n"
            user_dir_config += "  endmenu\n"
            path_file += user_dir_config + "\n"
        path_file += "endmenu\n\n"

    with PROJECT_CONFIG_PATH.open("w", encoding="utf-8") as f:
        f.write(path_file)

    config = MenuConfig(PROJECT_CONFIG_PATH, XF_TARGET_PATH, PROJECT_BUILD_PATH)

    return config


def build():
    if not is_project("."):
        logging.warning("该目录不是工程文件夹")
        return

    logging.info("run build")
    run_build()
    scan_kconfig()


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
    scan_kconfig().start()


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
    scan_kconfig()

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
