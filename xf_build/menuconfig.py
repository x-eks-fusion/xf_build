import os
from pathlib import Path
from kconfiglib import Kconfig
from menuconfig import menuconfig
import logging
import json

from .env import XF_ROOT, ROOT_BOARDS, ROOT_PORT
from .env import PROJECT_BUILD_INFO
from .env import PROJECT_CONFIG_PATH


class MenuConfig(Kconfig):
    """
    menuconfig相关操作内容
    """

    CONFIG_NAME: str = "xfconfig"
    HEADER_DIR: str = "header_config"
    HEADER_NAME: str = "xfconfig.h"
    XFKCONFIG_NAME: str = "XFKconfig"
    DEFAULT_CONFIG: str = "xfconfig.defaults"
    KCONFIG_PREFIX: str = "CONFIG_"
    KCONFIG_CONFIG_HEADER: str = "# Welcome to xfusion\n"
    MENUCONFIG_STYLE: str = "default selection=fg:white,bg:blue"
    HEADER_TEMPLATE: str = ("#ifndef __XF_CONFIG_H__\n"
                            "#define __XF_CONFIG_H__\n"
                            "\n{0}\n\n"
                            "#endif // __XF_CONFIG_H__\n")

    def __init__(self,
                 config_in: Path,
                 target_path: Path,
                 build_path: Path) -> None:
        logging.debug(f"config_in:{config_in}")
        super().__init__(str(config_in), True, True, "utf-8", False)
        project_path = build_path / ".."
        proj_config_path = project_path / self.CONFIG_NAME
        self.header_path = build_path / self.HEADER_DIR / self.HEADER_NAME

        os.environ["MENUCONFIG_STYLE"] = self.MENUCONFIG_STYLE
        os.environ["KCONFIG_CONFIG"] = proj_config_path.as_posix()
        os.environ["KCONFIG_CONFIG_HEADER"] = self.KCONFIG_CONFIG_HEADER
        os.environ["CONFIG_"] = self.KCONFIG_PREFIX

        proj_default_config_path = project_path / self.DEFAULT_CONFIG
        target_default_config_path = target_path / self.DEFAULT_CONFIG

        if proj_config_path.exists():
            logging.debug(f"load config: {proj_config_path}")
            self.load_config(proj_config_path.as_posix())
        elif proj_default_config_path.exists():
            logging.debug(f"load config: {proj_default_config_path}")
            self.load_config(proj_default_config_path.as_posix())
        elif target_default_config_path.exists():
            logging.debug(f"load config: {target_default_config_path}")
            self.load_config(target_default_config_path.as_posix())

        # 防止文件夹及文件夹没被建立
        if not self.header_path.is_file():
            header_dirs = self.header_path.parent
            if not header_dirs.is_dir():
                header_dirs.mkdir(parents=True, exist_ok=True)
            with self.header_path.open("w", encoding="utf-8") as f:
                f.write("")

        self.write_autoconf(self.header_path.as_posix())
        self.__add_header()

    def __add_header(self) -> None:
        with open(self.header_path, "r", encoding="utf-8") as f:
            header_contents = f.read()
        with open(self.header_path, "w", encoding="utf-8") as f:
            header_contents = self.HEADER_TEMPLATE.format(header_contents)
            f.write(header_contents)

    def start(self) -> None:
        """
        运行menuconfig配置页面，并生成头文件
        """
        menuconfig(self)
        self.write_autoconf(self.header_path)
        self.__add_header()

    def get_macro(self, macro):
        """
        获取menuconfig产生的宏
        """
        value = self.syms.get(macro)
        if value is None:
            return None
        return value.str_value

    @classmethod
    def scan_kconfig(cls):
        """
        扫描收集kconfig, 并生成头文件
        """
        logging.info("scan config")
        path: list = [
            XF_ROOT / cls.XFKCONFIG_NAME,
            ROOT_BOARDS / cls.XFKCONFIG_NAME,
        ]
        port_xfconfig = ROOT_PORT / cls.XFKCONFIG_NAME
        if port_xfconfig.exists():
            path.append(port_xfconfig)

        path_file: str = "\n".join([f'source "{i.as_posix()}"' for i in path])
        path_file += "\n"

        with PROJECT_BUILD_INFO.open("r", encoding="utf-8") as f:
            build_info = json.load(f)
            public_components = [
                Path(i) for i in build_info["public_components"]]
            user_main = Path(build_info["user_main"][0])
            user_components = [Path(i)
                               for i in build_info["user_components"]]
            user_dirs = [Path(i)
                         for i in build_info["user_dirs"]]

        # public components 部分的处理
        if public_components != []:
            path_file += "menu \"public components\"\n"
            for i in public_components:
                public_component_xfconfig = i / cls.XFKCONFIG_NAME
                if not public_component_xfconfig.exists():
                    continue
                public_component_config = "  menu \"" + i.name + "\"\n"
                public_component_config += "    source \"" + \
                    public_component_xfconfig.as_posix() + "\"\n"
                public_component_config += "  endmenu\n"
                path_file += public_component_config + "\n"
            path_file += "endmenu\n\n"

        # main 部分的处理
        user_main_xfconfig = user_main / cls.XFKCONFIG_NAME
        if user_main_xfconfig.exists():
            user_main_config = "menu \"main\"\n"
            user_main_config += "  source \"" + user_main_xfconfig.as_posix() + "\"\n"
            user_main_config += "endmenu\n"
            path_file += user_main_config + "\n"

        # components 部分的处理
        if user_components != []:
            path_file += "menu \"user components\"\n"
            for i in user_components:
                user_component_xfconfig = i / cls.XFKCONFIG_NAME
                if not user_component_xfconfig.exists():
                    continue
                user_component_config = "  menu \"" + i.name + "\"\n"
                user_component_config += "    source \"" + \
                    user_component_xfconfig.as_posix() + "\"\n"
                user_component_config += "  endmenu\n"
                path_file += user_component_config + "\n"
            path_file += "endmenu\n\n"

        if user_dirs != []:
            # dirs 部分的处理
            path_file += "menu \"user dirs\"\n"
            for i in user_dirs:
                user_dir_xfconfig = i / cls.XFKCONFIG_NAME
                if not user_dir_xfconfig.exists():
                    continue
                user_dir_config = "  menu \"" + i.name + "\"\n"
                user_dir_config += "    source \"" + user_dir_xfconfig.as_posix() + "\"\n"
                user_dir_config += "  endmenu\n"
                path_file += user_dir_config + "\n"
            path_file += "endmenu\n\n"

        with PROJECT_CONFIG_PATH.open("w", encoding="utf-8") as f:
            f.write(path_file)

        logging.info("scan config done")
