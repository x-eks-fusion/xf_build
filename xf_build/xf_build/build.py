#!/usr/bin/env python3


from pathlib import Path
import logging
import json

from .env import XF_PROJECT
from .env import PROJECT_BUILD_PATH
from .env import ROOT_COMPONENTS, PROJECT_COMPONENTS
from .env import COLLECT_SCRIPT, PROJECT_BUILD_ENV
from .env import PROJECT_CONFIG_PATH, XF_TARGET_PATH
from .menuconfig import MenuConfig


class Project:
    def __init__(self, user_dirs=[]) -> None:
        """
        完成env的创建，完成自定义指令的创建

        :param user_dirs: 用户额外添加的文件夹
        """
        self.build_info = {
            "project_name": " ",
            "user_components": {},
            "user_main": {},
            "user_dirs": {},
            "public_components": {},
            "config_path": "",
            "cflags": [],
        }

        # 用户工程路径，menuconfig生成的配置头文件路径
        self.build_info["project_name"] = XF_PROJECT
        self.build_info["config_path"] = (
            PROJECT_BUILD_PATH / MenuConfig.HEADER_DIR).as_posix()

        # 编译生成的产物路径
        if not PROJECT_BUILD_PATH.exists():
            PROJECT_BUILD_PATH.mkdir(parents=True, exist_ok=True)

        self.user_dirs = []
        if user_dirs == []:
            return
        for i in user_dirs:
            if "*" in i:
                self.user_dirs.extend(Path('.').glob(i))
                self.user_dirs = [i.resolve() for i in self.user_dirs]
            else:
                self.user_dirs.append(Path(i).resolve())

    def program(self):
        """
        工程建立，这里开始调用最外层脚本开始构建工程

        :param name: 工程名，如果没有工程名，则自动以工程文件夹名为工程名
        """

        # 收集全局组件
        for item in ROOT_COMPONENTS.iterdir():
            full_path = ROOT_COMPONENTS / item
            if full_path.is_file():
                continue  # 如果是文件，则跳过

            script_path = full_path / COLLECT_SCRIPT
            if not script_path.exists():
                continue  # 如果脚本不存在，则跳过

            # 执行脚本
            self.script_path = script_path.parent.resolve()
            with script_path.open("r", encoding="utf-8") as f:
                code = f.read()
            exec(code)

        # 收集用户组件
        if PROJECT_COMPONENTS.exists():
            for item in PROJECT_COMPONENTS.iterdir():
                full_path = PROJECT_COMPONENTS / item
                if full_path.is_file():
                    continue  # 如果是文件，则跳过

                script_path = full_path / COLLECT_SCRIPT
                if not script_path.exists():
                    continue  # 如果脚本不存在，则跳过

            # 执行脚本
            self.script_path = script_path.parent.resolve()
            with script_path.open("r", encoding="utf-8") as f:
                code = f.read()
            exec(code)

        for i in self.user_dirs:
            script_path:Path = i / COLLECT_SCRIPT
            # 执行脚本
            self.script_path = script_path.parent.resolve()
            with script_path.open("r", encoding="utf-8") as f:
                code = f.read()
            exec(code)

        # 处理主程序下的内容
        main_path = Path(f"main/{COLLECT_SCRIPT}").resolve()
        if not main_path.exists():
            raise f"must have main and main/{COLLECT_SCRIPT}"
        # 执行脚本
        self.script_path = main_path.parent.resolve()
        with main_path.open("r", encoding="utf-8") as f:
            code = f.read()
        exec(code)  
        
        # 保存成json
        with PROJECT_BUILD_ENV.open("w", encoding="utf-8") as f:
            json.dump(self.build_info, f, indent=4)

    def collect(self,
        srcs: list = ["*.c"],
        inc_dirs: list = ["."],
        requires: list = [],
        cflags: list = [],
    ):
        def deep_flatte(iterable):
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
        script_path: Path = self.script_path
        srcs = [list(script_path.glob(i)) for i in srcs]
        srcs = deep_flatte(srcs)
        srcs = [i.as_posix() for i in srcs]
        inc_dirs = [(script_path / i).resolve().as_posix() for i in inc_dirs]
        inc_dirs.append(self.build_info["config_path"])  # 添加menuconfig生成的头文件
        name: str = script_path.name
        script_dir = script_path.parent
        if name == "main":
            self.build_info["user_main"]["path"] = script_path.as_posix()
            self.build_info["user_main"]["srcs"] = srcs
            self.build_info["user_main"]["inc_dirs"] = inc_dirs
            self.build_info["user_main"]["requires"] = list(self.build_info["public_components"].keys(
            ))+list(self.build_info["user_components"].keys())+list(self.build_info["user_dirs"].keys())
            self.build_info["user_main"]["cflags"] = cflags
        elif script_dir == ROOT_COMPONENTS:
            if name in self.build_info["public_components"]:
                raise f"component {name} already exists"
            self.build_info["public_components"][name] = {}
            self.build_info["public_components"][name]["path"] = script_path.as_posix()
            self.build_info["public_components"][name]["srcs"] = srcs
            self.build_info["public_components"][name]["inc_dirs"] = inc_dirs
            self.build_info["public_components"][name]["requires"] = requires
            self.build_info["public_components"][name]["cflags"] = cflags
        elif script_dir == PROJECT_COMPONENTS:
            if name in self.build_info["user_components"]:
                raise f"component {name} already exists"
            self.build_info["user_components"][name] = {}
            self.build_info["user_components"][name]["path"] = script_path.as_posix()
            self.build_info["user_components"][name]["srcs"] = srcs
            self.build_info["user_components"][name]["inc_dirs"] = inc_dirs
            self.build_info["user_components"][name]["requires"] = requires
            self.build_info["user_components"][name]["cflags"] = cflags
        else:
            if name in self.build_info["user_dirs"]:
                raise f"component {name} already exists"
            self.build_info["user_dirs"][name] = {}
            self.build_info["user_dirs"][name]["path"] = script_path.as_posix()
            self.build_info["user_dirs"][name]["srcs"] = srcs
            self.build_info["user_dirs"][name]["inc_dirs"] = inc_dirs
            self.build_info["user_dirs"][name]["requires"] = requires
            self.build_info["user_dirs"][name]["cflags"] = cflags

    def get_define(self, define: str):
        config = MenuConfig(PROJECT_CONFIG_PATH,
                            XF_TARGET_PATH, PROJECT_BUILD_PATH)
        return config.get_macro(define)
