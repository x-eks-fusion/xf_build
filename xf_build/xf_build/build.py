#!/usr/bin/env python3


from pathlib import Path
import logging
import json
from copy import deepcopy

from .env import XF_PROJECT
from .env import XF_PROJECT_PATH
from .env import PROJECT_BUILD_PATH
from .env import ROOT_COMPONENTS, PROJECT_COMPONENTS
from .env import COLLECT_SCRIPT, PROJECT_BUILD_ENV
from .env import PROJECT_CONFIG_PATH, XF_TARGET_PATH
from .env import set_XF_PROJECT, save_other_dirs
from .menuconfig import MenuConfig


class Project:
    DEFAULT_BUILD_INFO_DICT = {
        "project_name": " ",
        "user_components": {},
        "user_main": {},
        "other_components": {},
        "public_components": {},
        "config_path": ""}

    def __init__(self, name: str = "") -> None:
        """
        完成env的创建，完成自定义指令的创建
        """
        self.build_info: dict = deepcopy(self.DEFAULT_BUILD_INFO_DICT)
        self.user_dirs: list[Path] = []  # 这里用于用户添加额外文件夹进入编译

        # 获取用户的文件路径，menuconfig生成的配置头文件路径
        if name != "":
            set_XF_PROJECT(name)
        else:
            set_XF_PROJECT(XF_PROJECT_PATH.name)
        self.build_info["project_name"] = XF_PROJECT
        self.build_info["config_path"] = (
            PROJECT_BUILD_PATH / MenuConfig.HEADER_DIR).as_posix()

        # 编译生成的产物路径
        if not PROJECT_BUILD_PATH.exists():
            PROJECT_BUILD_PATH.mkdir(parents=True, exist_ok=True)

    def __exec(self, file: Path):
        self.script_path = file.parent.resolve()
        with file.open("r", encoding="utf-8") as f:
            code = f.read()
        exec(code)

    def __prepare_building(self):
        """
        准备构建阶段，此阶段会收集全局组件，用户组件，用户额外组件，主函数等
        在构建之前建立一个全局依赖结构，并展开所有依赖，为构建做准备
        """
        # 收集全局组件
        self.__collection_components(True)
        # 收集用户组件
        if PROJECT_COMPONENTS.exists():
            self.__collection_components(False)

        for i in self.user_dirs:
            script = i / COLLECT_SCRIPT
            self.__exec(script)

        # 处理主程序下的内容
        main_path = Path(f"main/{COLLECT_SCRIPT}").resolve()
        if main_path.exists():
            self.__exec(main_path)
        else:
            raise f"must have main and main/{COLLECT_SCRIPT}"

    def __deepflatte(self, iterable):
        result = []
        stack = [iter(iterable)]

        while stack:
            current = stack[-1]
            try:
                item = next(current)
                if isinstance(item, list):
                    stack.append(iter(item))
                else:
                    result.append(item)
            except StopIteration:
                stack.pop()

        return result

    def __save_build_args(self):

        # 保存成json
        with PROJECT_BUILD_ENV.open("w", encoding="utf-8") as f:
            json.dump(self.build_info, f, indent=4)

        save_other_dirs(self.user_dirs)

    def __collection_components(self, is_root: bool = True):
        if is_root:
            comp_path = ROOT_COMPONENTS
        else:
            comp_path = PROJECT_COMPONENTS

        if not comp_path.exists():
            logging.error(
                f"There are no components under the {comp_path} path")
            return

        for item in comp_path.iterdir():
            full_path = comp_path / item
            if full_path.is_file():
                continue  # 如果是文件，则跳过

            script_path = full_path / COLLECT_SCRIPT
            if not script_path.exists():
                continue  # 如果脚本不存在，则跳过

            self.__exec(script_path)  # 执行脚本

    def program(self):
        """
        工程建立，这里开始调用最外层脚本开始构建工程

        :param name: 工程名，如果没有工程名，则自动以工程文件夹名为工程名
        """

        self.__prepare_building()
        self.__save_build_args()

    def collect(
        self,
        srcs: list = ["*.c"],
        inc_dirs: list = ["."],
        requires: list = [],
    ):

        script_path: Path = self.script_path
        srcs = [list(script_path.glob(i)) for i in srcs]
        srcs = self.__deepflatte(srcs)
        srcs = [i.as_posix() for i in srcs]
        inc_dirs = [(script_path / i).resolve().as_posix() for i in inc_dirs]
        inc_dirs.append(self.build_info["config_path"])  # 添加menuconfig生成的头文件
        name = script_path.name
        script_dir = script_path.parent
        if name == "main":
            self.build_info["user_main"]["path"] = script_path.as_posix()
            self.build_info["user_main"]["srcs"] = srcs
            self.build_info["user_main"]["inc_dirs"] = inc_dirs
            self.build_info["user_main"]["requires"] = list(self.build_info["public_components"].keys(
            ))+list(self.build_info["user_components"].keys())
        elif script_dir == ROOT_COMPONENTS:
            self.build_info["public_components"][name] = {}
            self.build_info["public_components"][name]["path"] = script_path.as_posix()
            self.build_info["public_components"][name]["srcs"] = srcs
            self.build_info["public_components"][name]["inc_dirs"] = inc_dirs
            self.build_info["public_components"][name]["requires"] = requires
        elif script_dir == PROJECT_COMPONENTS:
            self.build_info["user_components"][name] = {}
            self.build_info["user_components"][name]["path"] = script_path.as_posix()
            self.build_info["user_components"][name]["srcs"] = srcs
            self.build_info["user_components"][name]["inc_dirs"] = inc_dirs
            self.build_info["user_components"][name]["requires"] = requires

    def add_folders(self, user_folders):
        """
        添加额外编译的文件夹，通常来说仅仅会收集用户文件夹下的components和main文件
        我们可以通过该方法，将其它名称的文件夹加入编译

        :param user_folders 文件夹路径，可以是单个文件夹（字符串），也可以是多个文件夹（列表）
        """
        if isinstance(user_folders, str):
            user_folders = Path(user_folders)
            if user_folders.exists():
                self.user_dirs.append(user_folders.resolve())
        elif isinstance(user_folders, list):
            user_folders = [Path(i).resolve() for i in user_folders]
            for i in user_folders:
                if not i.exists():
                    logging.error(f"{i} is not exists")
                    return
            self.user_dirs.extend(user_folders)

    def get_define(self, define: str):
        config = MenuConfig(PROJECT_CONFIG_PATH,
                            XF_TARGET_PATH, PROJECT_BUILD_PATH)
        return config.get_macro(define)
