#!/usr/bin/env python3

import os
import json
import shutil
import logging
from pathlib import Path

ENTER_SCRIPT = "xf_project.py"
COLLECT_SCRIPT = "xf_collect.py"

XF_ROOT = Path(os.environ.get("XF_ROOT")).resolve()
XF_TARGET = os.environ.get("XF_TARGET")
XF_TARGET_PATH = Path(os.environ.get("XF_TARGET_PATH")).resolve()

XF_PROJECT_PATH = Path(os.environ.get("XF_PROJECT_PATH", Path("."))).resolve()
os.environ["XF_PROJECT_PATH"] = XF_PROJECT_PATH.as_posix()
XF_PROJECT = os.environ.get("XF_PROJECT", XF_PROJECT_PATH.name)
os.environ["XF_PROJECT"] = XF_PROJECT

PROJECT_BUILD_PATH = XF_PROJECT_PATH / "build"
PROJECT_CONFIG_PATH = PROJECT_BUILD_PATH / "config.in"
PROJECT_BUILD_INFO = PROJECT_BUILD_PATH / "build_info.json"
PROJECT_BUILD_ENV = PROJECT_BUILD_PATH / "build_environ.json"
PROJECT_COMPONENTS = XF_PROJECT_PATH / "components"

ROOT_BUILD_PATH = XF_ROOT / "build"
ROOT_PROJECT_INFO = ROOT_BUILD_PATH / "project_info.json"

ROOT_BOARDS = XF_ROOT / "boards"
ROOT_COMPONENTS = XF_ROOT / "components"
ROOT_PORT = XF_ROOT / "port" / XF_TARGET

ROOT_PLUGIN = XF_ROOT / "plugins" / XF_TARGET

ROOT_TEMPLATE_PATH = XF_ROOT / "examples" / "get_started" / "template_project"


def clean_project_build() -> None:
    shutil.rmtree(PROJECT_BUILD_PATH, ignore_errors=True)
    PROJECT_BUILD_PATH.mkdir()


def clean_root_build() -> None:
    shutil.rmtree(ROOT_BUILD_PATH, ignore_errors=True)
    ROOT_BUILD_PATH.mkdir()


def is_project(folder) -> bool:
    """
    判断目标文件夹是否是xf工程
    """
    if (Path(folder)/ENTER_SCRIPT).exists():
        return 
    raise Exception("该目录不是工程文件夹")


def check_target():
    """
    检测目标是否改变，如果改变清除工程
    """
    info = {}
    if ROOT_PROJECT_INFO.exists():
        with ROOT_PROJECT_INFO.open("r", encoding="utf-8") as f:
            info = json.load(f)
            if info.get("XF_TARGET_PATH") == XF_TARGET_PATH.as_posix():
                logging.debug("目标未改变")
                return
    else:
        ROOT_BUILD_PATH.mkdir(parents=True, exist_ok=True)

    logging.debug("目标改变，重新生成build")
    logging.debug(f"info target:{info.get('XF_TARGET_PATH')}")
    logging.debug(f"env target:{XF_TARGET_PATH}")
    os.system("xf clean")
    with ROOT_PROJECT_INFO.open("w", encoding="utf-8") as f:
        logging.debug(f"XF_TARGET_PATH:{XF_TARGET_PATH}")
        info["XF_TARGET_PATH"] = XF_TARGET_PATH.as_posix()
        json.dump(info, f, indent=4)


def check_project():
    """
    检测工程是否改变，如果改变清除工程
    """
    info = {}
    if ROOT_PROJECT_INFO.exists():
        with ROOT_PROJECT_INFO.open("r", encoding="utf-8") as f:
            info = json.load(f)
            if info.get("XF_PROJECT_PATH") == XF_PROJECT_PATH.as_posix():
                logging.debug("工程未改变")
                return
    else:
        ROOT_BUILD_PATH.mkdir(parents=True, exist_ok=True)

    logging.debug("工程项目改变，重新生成build")
    logging.debug(f"info project:{info.get('XF_PROJECT_PATH')}")
    logging.debug(f"env project:{XF_PROJECT_PATH}")
    os.system("xf clean")
    with ROOT_PROJECT_INFO.open("w", encoding="utf-8") as f:
        logging.debug(f"XF_PROJECT_PATH:{XF_PROJECT_PATH}")
        info["XF_PROJECT_PATH"] = XF_PROJECT_PATH.as_posix()
        json.dump(info, f, indent=4)


def run_build() -> None:
    """
    执行一遍脚本产生编译信息
    """
    check_target()
    check_project()

    try:
        with open(ENTER_SCRIPT, "r", encoding="utf-8") as f:
            exec(f.read())
    except Exception as e:
        logging.error(f"预编译错误: {e}")
        return
