#!/usr/bin/env python3

# 该部分是给开发者于编译的时候调用的
from .build import Project

# 该部分是移植者注册插件的时候调用的
from .plugins import Plugins
from .plugins import get_hookimpl
from .env import XF_VERSION

default_project = None
program = None
collect = None
collect_srcs = None
add_folders = None
get_define = None


def project_init(name: str = "") -> None:
    global default_project, program, collect, collect_srcs, add_folders, get_define
    default_project = Project(name)
    program = default_project.program
    collect = default_project.collect
    add_folders = default_project.add_folders
    get_define = default_project.get_define
