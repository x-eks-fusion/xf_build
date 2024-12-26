#!/usr/bin/env python3


from pathlib import Path
import logging
import sys
import json

from .env import XF_PROJECT, XF_PROJECT_PATH
from .env import PROJECT_BUILD_PATH, PROJECT_BUILD_INFO
from .env import ROOT_COMPONENTS, PROJECT_COMPONENTS
from .env import COLLECT_SCRIPT, PROJECT_BUILD_ENV, ROOT_PORT
from .env import PROJECT_CONFIG_PATH, XF_TARGET_PATH
from .menuconfig import MenuConfig


class Project:
    def __init__(self, user_dirs=[]) -> None:
        """
        完成env的创建，完成自定义指令的创建

        :param user_dirs: 用户额外添加的文件夹
        """
        self.build_env = {
            "project_name": " ",
            "user_components": {},
            "user_main": {},
            "user_dirs": {},
            "public_components": {},
            "public_port": {},
            "config_path": "",
            "cflags": [],
        }

        # 用户工程路径，menuconfig生成的配置头文件路径
        self.build_env["project_name"] = XF_PROJECT
        self.build_env["config_path"] = (
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

    def program(self, cflags: list = []):
        """
        工程建立，这里开始调用最外层脚本开始构建工程

        :param cflags: 影响全局的cflags
        """
        self.build_env["cflags"] = cflags
        build_info = {
            "user_components": [],
            "user_dirs": [],
            "public_components": [],
            "public_port": [],
            "user_main": [],
        }
        components_name = []

        # 收集移植对接
        port_path = (ROOT_PORT / COLLECT_SCRIPT).resolve()
        name = ROOT_PORT.name
        if name in components_name:
            logging.error(f"组件名重复{name}")
            raise ValueError(f"component {name} already exists")
        components_name.append(name)
        self.build_env["public_port"][name] = {}
        self.build_env["public_port"][name]["path"] = ROOT_PORT.as_posix()
        self.build_env["public_port"][name]["srcs"] = []
        self.build_env["public_port"][name]["inc_dirs"] = []
        self.build_env["public_port"][name]["requires"] = []
        self.build_env["public_port"][name]["cflags"] = []
        # 收集路径
        build_info["public_port"].append(port_path.parent.as_posix())

        # 收集全局组件
        for item in ROOT_COMPONENTS.iterdir():
            full_path = ROOT_COMPONENTS / item
            if full_path.is_file():
                continue  # 如果是文件，则跳过

            script_path = (full_path / COLLECT_SCRIPT).resolve()
            if not script_path.exists():
                continue  # 如果脚本不存在，则跳过
            name = full_path.name
            if name in components_name:
                logging.error(f"组件名重复{name}")
                raise ValueError(f"component {name} already exists")
            components_name.append(name)
            self.build_env["public_components"][name] = {}
            self.build_env["public_components"][name]["path"] = full_path.as_posix()
            self.build_env["public_components"][name]["srcs"] = []
            self.build_env["public_components"][name]["inc_dirs"] = []
            self.build_env["public_components"][name]["requires"] = []
            self.build_env["public_components"][name]["cflags"] = []
            # 收集路径
            build_info["public_components"].append(full_path.as_posix())

        # 收集用户组件
        if PROJECT_COMPONENTS.exists():
            for item in PROJECT_COMPONENTS.iterdir():
                full_path = PROJECT_COMPONENTS / item
                if full_path.is_file():
                    continue  # 如果是文件，则跳过

                script_path = (full_path / COLLECT_SCRIPT).resolve()
                if not script_path.exists():
                    continue  # 如果脚本不存在，则跳过
                name = full_path.name
                if name in components_name:
                    logging.error(f"组件名重复{name}")
                    raise ValueError(f"component {name} already exists")
                components_name.append(name)
                self.build_env["user_components"][name] = {}
                self.build_env["user_components"][name]["path"] = full_path.as_posix()
                self.build_env["user_components"][name]["srcs"] = []
                self.build_env["user_components"][name]["inc_dirs"] = []
                self.build_env["user_components"][name]["requires"] = []
                self.build_env["user_components"][name]["cflags"] = []
                # 收集路径
                build_info["user_components"].append(full_path.as_posix())

        # 收集用户目录
        for user_dir in self.user_dirs:
            script_path: Path = (user_dir / COLLECT_SCRIPT).resolve()
            if not script_path.exists():
                continue  # 如果脚本不存在，则跳过
            name = full_path.name
            if name in components_name:
                logging.error(f"组件名重复{name}")
                raise ValueError(f"component {name} already exists")
            components_name.append(name)
            self.build_env["user_dirs"][name] = {}
            self.build_env["user_dirs"][name]["path"] = user_dir.as_posix()
            self.build_env["user_dirs"][name]["srcs"] = []
            self.build_env["user_dirs"][name]["inc_dirs"] = []
            self.build_env["user_dirs"][name]["requires"] = []
            self.build_env["user_dirs"][name]["cflags"] = []
            # 收集路径
            build_info["user_dirs"].append(user_dir.as_posix())

        # 处理主程序下的内容
        main_path = Path(f"main/{COLLECT_SCRIPT}").resolve()
        if not main_path.exists():
            logging.error(f"must have main and main/{COLLECT_SCRIPT}")
            raise FileNotFoundError(
                f"must have main and main/{COLLECT_SCRIPT}")
        self.build_env["user_main"]["path"] = main_path.parent.as_posix()
        self.build_env["user_main"]["srcs"] = []
        self.build_env["user_main"]["inc_dirs"] = []
        self.build_env["user_main"]["requires"] = []
        self.build_env["user_main"]["cflags"] = []
        # 收集路径
        build_info["user_main"].append(main_path.parent.as_posix())

        # 保存成json
        with PROJECT_BUILD_INFO.open("w", encoding="utf-8") as f:
            json.dump(build_info, f, indent=4)

        # 扫描XFKconfig并生成头文件
        MenuConfig.scan_kconfig()

        # 执行脚本
        for values in build_info.values():
            for value in values:
                self.script_path = Path(value).resolve()
                script_path = self.script_path / COLLECT_SCRIPT
                logging.info(f"run script {script_path}")
                sys.path.append(self.script_path.as_posix())
                with script_path.open("r", encoding="utf-8") as f:
                    exec(f.read())
        # 收集编译信息保存成json
        with PROJECT_BUILD_ENV.open("w", encoding="utf-8") as f:
            json.dump(self.build_env, f, indent=4)

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
        inc_dirs.append(self.build_env["config_path"])  # 添加menuconfig生成的头文件
        name: str = script_path.name
        script_dir = script_path.parent
        if name == "main":
            self.build_env["user_main"]["srcs"].extend(srcs)
            self.build_env["user_main"]["inc_dirs"].extend(inc_dirs)
            self.build_env["user_main"]["requires"].extend(list(self.build_env["public_components"].keys(
            ))+list(self.build_env["user_components"].keys())+list(self.build_env["user_dirs"].keys())+list(self.build_env["public_port"].keys()))
            self.build_env["user_main"]["cflags"].extend(cflags)
            # 去重
            self.build_env["user_main"]["srcs"] = list(
                set(self.build_env["user_main"]["srcs"]))
            self.build_env["user_main"]["inc_dirs"] = list(
                set(self.build_env["user_main"]["inc_dirs"]))
            self.build_env["user_main"]["requires"] = list(
                set(self.build_env["user_main"]["requires"]))
            self.build_env["user_main"]["cflags"] = list(
                set(self.build_env["user_main"]["cflags"]))
        elif script_dir == ROOT_COMPONENTS:
            self.build_env["public_components"][name]["srcs"].extend(srcs)
            self.build_env["public_components"][name]["inc_dirs"].extend(
                inc_dirs)
            self.build_env["public_components"][name]["requires"].extend(
                requires)
            self.build_env["public_components"][name]["cflags"].extend(cflags)
            # 去重
            self.build_env["public_components"][name]["srcs"] = list(
                set(self.build_env["public_components"][name]["srcs"]))
            self.build_env["public_components"][name]["inc_dirs"] = list(
                set(self.build_env["public_components"][name]["inc_dirs"]))
            self.build_env["public_components"][name]["requires"] = list(
                set(self.build_env["public_components"][name]["requires"]))
            self.build_env["public_components"][name]["cflags"] = list(
                set(self.build_env["public_components"][name]["cflags"]))
        elif script_dir == PROJECT_COMPONENTS:
            self.build_env["user_components"][name]["srcs"].extend(srcs)
            self.build_env["user_components"][name]["inc_dirs"].extend(
                inc_dirs)
            self.build_env["user_components"][name]["requires"].extend(
                requires)
            self.build_env["user_components"][name]["cflags"].extend(cflags)
            # 去重
            self.build_env["user_components"][name]["srcs"] = list(
                set(self.build_env["user_components"][name]["srcs"]))
            self.build_env["user_components"][name]["inc_dirs"] = list(
                set(self.build_env["user_components"][name]["inc_dirs"]))
            self.build_env["user_components"][name]["requires"] = list(
                set(self.build_env["user_components"][name]["requires"]))
            self.build_env["user_components"][name]["cflags"] = list(
                set(self.build_env["user_components"][name]["cflags"]))
        elif script_dir == ROOT_PORT.parent:
            self.build_env["public_port"][name]["srcs"].extend(srcs)
            self.build_env["public_port"][name]["inc_dirs"].extend(inc_dirs)
            self.build_env["public_port"][name]["requires"].extend(requires)
            self.build_env["public_port"][name]["cflags"].extend(cflags)
            # 去重
            self.build_env["public_port"][name]["srcs"] = list(
                set(self.build_env["public_port"][name]["srcs"]))
            self.build_env["public_port"][name]["inc_dirs"] = list(
                set(self.build_env["public_port"][name]["inc_dirs"]))
            self.build_env["public_port"][name]["requires"] = list(
                set(self.build_env["public_port"][name]["requires"]))
            self.build_env["public_port"][name]["cflags"] = list(
                set(self.build_env["public_port"][name]["cflags"]))
        else:
            self.build_env["user_dirs"][name]["srcs"].extend(srcs)
            self.build_env["user_dirs"][name]["inc_dirs"].extend(inc_dirs)
            self.build_env["user_dirs"][name]["requires"].extend(requires)
            self.build_env["user_dirs"][name]["cflags"].extend(cflags)
            # 去重
            self.build_env["user_dirs"][name]["srcs"] = list(
                set(self.build_env["user_dirs"][name]["srcs"]))
            self.build_env["user_dirs"][name]["inc_dirs"] = list(
                set(self.build_env["user_dirs"][name]["inc_dirs"]))
            self.build_env["user_dirs"][name]["requires"] = list(
                set(self.build_env["user_dirs"][name]["requires"]))
            self.build_env["user_dirs"][name]["cflags"] = list(
                set(self.build_env["user_dirs"][name]["cflags"]))

    def get_define(self, define: str):
        """
        从menuconfig中获取宏定义的值

        :param define 获取到的宏定义的值
        """
        config = MenuConfig(PROJECT_CONFIG_PATH,
                            XF_TARGET_PATH, PROJECT_BUILD_PATH)
        return config.get_macro(define)
