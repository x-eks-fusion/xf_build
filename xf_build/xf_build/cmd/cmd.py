#!/usr/bin/env python3

import click
import pluggy
import logging


from ..log import logging_setup
from ..env import is_project
from ..env import XF_ROOT
from ..env import ROOT_PLUGIN
from ..plugins import Plugins

from . import project
from .package import download_file
from .package import remove_file
from .package import search_by_name

pass_context = click.make_pass_decorator(dict, ensure=True)


@click.group()
@click.option('--verbose', '-v', is_flag=True, default=False, help="Enable verbose mode.")
@click.option('--rich', '-r', is_flag=True, default=False, help="Enable rich mode.")
@click.option('--test', '-t', is_flag=True, default=False, help="Enable test mode.")
@pass_context
def cli(ctx, verbose, rich, test) -> None:
    ctx["test"] = test
    if verbose:
        logging_setup(level=logging.DEBUG, rich=rich)
    else:
        logging_setup(level=logging.INFO, rich=rich)
    if XF_ROOT == "":
        logging.error(
            "please run '. export.sh <target>' then run 'xf' command!")
        raise "not have 'XF_ROOT' in your environ"


@cli.command()
@click.argument("args", nargs=-1)  # 使用 nargs=-1 接受任意数量的位置参数
@pass_context
def build(ctx, args) -> None:
    """
    编译工程
    """
    project.build()

    if ctx["test"]:
        return

    # 启动插件调用用户的build指令
    plugin = Plugins()
    plugin.add(ROOT_PLUGIN)
    hook: pluggy.HookRelay = plugin.get_hook()
    hook.build(args=args)


@cli.command()
@click.argument("args", nargs=-1)  # 使用 nargs=-1 接受任意数量的位置参数
@pass_context
def clean(ctx, args) -> None:
    """
    清空编译中间产物
    """
    project.clean()

    if ctx["test"]:
        return

    # 启动插件调用用户的clean指令
    plugin = Plugins()
    plugin.add(ROOT_PLUGIN)
    hook: pluggy.HookRelay = plugin.get_hook()
    hook.clean(args=args)


@cli.command()
@click.argument("args", nargs=-1)
def menuconfig(args) -> None:
    """
    全局宏的配置
    """

    if len(args) == 0:
        project.menuconfig()
    else:
        plugin = Plugins()
        plugin.add(ROOT_PLUGIN)
        hook: pluggy.HookRelay = plugin.get_hook()
        hook.menuconfig(args=args)


@cli.command()
@click.argument("args", nargs=-1)  # 使用 nargs=-1 接受任意数量的位置参数
def flash(args) -> None:
    """
    烧录工程（需要port对接）
    """
    if not is_project("."):
        logging.warning("该目录不是工程文件夹")
        return

    plugin = Plugins()
    plugin.add(ROOT_PLUGIN)
    hook: pluggy.HookRelay = plugin.get_hook()
    hook.flash(args=args)


@cli.command()
@click.argument("name", type=str)
def create(name) -> None:
    """
    初始化创建一个新工程
    """
    project.create(name)


@cli.command()
@click.argument("name", type=click.Path(exists=False))
@click.argument("args", nargs=-1)
@pass_context
def export(ctx, name, args) -> None:
    """
    导出对应sdk的工程（需要port对接）
    """
    name_abspath = project.before_export(name)

    if ctx["test"]:
        return

    plugin = Plugins()
    plugin.add(ROOT_PLUGIN)
    hook: pluggy.HookRelay = plugin.get_hook()
    hook.export(name=name_abspath, args=args)


@cli.command()
@click.argument("name", type=click.Path(exists=False))
@click.argument("args", nargs=-1)
@pass_context
def update(ctx, name, args) -> None:
    """
    更新对应sdk的工程（需要port对接）
    """
    name_abspath = project.before_update(name)

    if ctx["test"]:
        return

    plugin = Plugins()
    plugin.add(ROOT_PLUGIN)
    hook: pluggy.HookRelay = plugin.get_hook()
    hook.update(name=name_abspath, args=args)


@cli.command()
@click.argument("name", type=click.Path(exists=False))
@click.option("-v", "--version", help="指定版本", default=None)
@click.option("-g", "--glob", is_flag=True, help="安装到全局还是本地", default=False)
def install(name, version, glob):
    """
    安装指定的包
    """
    if not is_project("."):
        logging.warning("该目录不是工程文件夹")
        return
    download_file(name, version, glob)


@cli.command()
@click.argument("name", type=click.Path(exists=False))
@click.option("-g", "--glob", is_flag=True, help="卸载全局还是本地的包", default=False)
def uninstall(name, glob):
    """
    卸载指定的包
    """
    if not is_project("."):
        logging.warning("该目录不是工程文件夹")
        return
    remove_file(name, glob)


@cli.command()
@click.argument("name", type=click.Path(exists=False))
def search(name):
    """
    模糊搜索包名
    """
    if not is_project("."):
        logging.warning("该目录不是工程文件夹")
        return
    search_by_name(name)


@cli.command()
@click.argument("port", type=click.Path(exists=False))
@click.option("-b", "--baud", type=int, default=115200)
def monitor(port, baud):
    """
    串口监视器
    """
    project.monitor(port, baud)

@cli.command()
@click.option("-s", "--show", is_flag=True, default=False, help="展示目标和目标路径")
@click.option("-d", "--download", is_flag=True, default=False, help="下载SDK")
def target(show, download):
    """
    target 相关操作：展示目标或下载SDK
    """
    if show and not download:
        project.show_target()
    elif download and not show:
        project.download_sdk()
    else:
        logging.error("参数错误")

if __name__ == "__main__":
    cli()
