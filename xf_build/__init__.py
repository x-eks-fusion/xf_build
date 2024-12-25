#!/usr/bin/env python3

# 该部分是给开发者于编译的时候调用的
from .build import Project

default_project = None
program = None
collect = None
collect_srcs = None
get_define = None


def project_init(user_dirs: list = []) -> None:
    global default_project, program, collect, collect_srcs, add_folders, get_define
    default_project = Project(user_dirs)
    program = default_project.program
    collect = default_project.collect
    get_define = default_project.get_define
