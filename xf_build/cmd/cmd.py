#!/usr/bin/env python3

import argparse
import logging
import sys


from ..log import logging_setup
from ..env import is_project
from ..env import XF_ROOT
from ..env import ROOT_PLUGIN
from ..plugins import Plugins

from . import project
from .package import download_file
from .package import remove_file
from .package import search_by_name


def main():
    parser = argparse.ArgumentParser(description="欢迎来到 xfusion 构建系统")
    parser.add_argument('-v', '--verbose',
                        action='store_true', help="打印更多日志信息")
    parser.add_argument('-r', '--rich', action='store_true',
                        help="使用rich库打印日志")
    parser.add_argument('-t', '--test', action='store_true',
                        help="测试模式（不会调用插件）")

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # build command
    build_parser = subparsers.add_parser('build',
                                         help="编译工程", aliases=['b'])
    build_parser.add_argument('args', nargs=argparse.REMAINDER, help="参数传递给插件")

    # clean command
    clean_parser = subparsers.add_parser('clean',
                                         help="清空编译中间产物", aliases=['c'])
    clean_parser.add_argument('args', nargs=argparse.REMAINDER, help="参数传递给插件")

    # menuconfig command
    menuconfig_parser = subparsers.add_parser('menuconfig',
                                              help="全局宏的配置", aliases=['menu'])
    menuconfig_parser.add_argument('args', nargs=argparse.REMAINDER,
                                   help="参数传递给插件")

    # flash command
    flash_parser = subparsers.add_parser('flash',
                                         help="烧录工程（需要port对接）", aliases=['f'])
    flash_parser.add_argument('args', nargs=argparse.REMAINDER, help="参数传递给插件")

    # create command
    create_parser = subparsers.add_parser('create', help="初始化创建一个新工程")
    create_parser.add_argument('name', type=str, help="工程名称")

    # export command
    export_parser = subparsers.add_parser('export',
                                          help="导出对应sdk的工程（需要port对接）", aliases=['e'])
    export_parser.add_argument('name', type=str, help="工程名称")
    export_parser.add_argument('args', nargs=argparse.REMAINDER,
                               help="参数传递给插件")

    # update command
    update_parser = subparsers.add_parser('update',
                                          help="更新对应sdk的工程（需要port对接）", aliases=['u'])
    update_parser.add_argument('name', type=str, help="工程名称")
    update_parser.add_argument('args', nargs=argparse.REMAINDER,
                               help="参数传递给插件")

    # install command
    install_parser = subparsers.add_parser('install',
                                           help="安装指定的包", aliases=['i'])
    install_parser.add_argument('name', type=str, help="包名")
    install_parser.add_argument('-v', '--version', type=str, default=None,
                                help="指定版本")
    install_parser.add_argument('-g', '--glob', action='store_true',
                                help="安装到全局还是本地")

    # uninstall command
    uninstall_parser = subparsers.add_parser('uninstall', help="卸载指定的包")
    uninstall_parser.add_argument('name', type=str, help="包名")
    uninstall_parser.add_argument('-g', '--glob', action='store_true',
                                  help="卸载全局的包")

    # search command
    search_parser = subparsers.add_parser('search',
                                          help="模糊搜索包名", aliases=['s'])
    search_parser.add_argument('name', type=str, help="包名")

    # monitor command
    monitor_parser = subparsers.add_parser('monitor',
                                           help="串口监视器", aliases=['m'])
    monitor_parser.add_argument('port', type=str, help="端口")
    monitor_parser.add_argument('-b', '--baud', type=int, default=115200,
                                help="波特率")

    # target command
    target_parser = subparsers.add_parser('target',
                                          help="target 相关操作：展示目标或下载SDK", aliases=['t'])
    target_parser.add_argument('-s', '--show', action='store_true',
                               help="展示目标和目标路径")
    target_parser.add_argument('-d', '--download', action='store_true',
                               help="下载SDK")

    # simulate command
    simulate_parser = subparsers.add_parser('simulate',
                                            help="模拟器运行", aliases=['sim'])

    args = parser.parse_args()

    # Logging setup
    if args.verbose:
        logging_setup(level=logging.DEBUG, rich=args.rich)
    else:
        logging_setup(level=logging.INFO, rich=args.rich)

    if XF_ROOT == "":
        logging.error(
            "please run '. export.sh <target>' then run 'xf' command!")
        sys.exit("not have 'XF_ROOT' in your environ")

    # Command execution
    if args.command == 'build' or args.command == "b":
        handle_build(args)
    elif args.command == 'clean' or args.command == "c":
        handle_clean(args)
    elif args.command == 'menuconfig' or args.command == "m":
        handle_menuconfig(args)
    elif args.command == 'flash' or args.command == "f":
        handle_flash(args)
    elif args.command == 'create':
        project.create(args.name)
    elif args.command == 'export' or args.command == "e":
        handle_export(args)
    elif args.command == 'update' or args.command == "u":
        handle_update(args)
    elif args.command == 'install' or args.command == "i":
        download_file(args.name, args.version, args.glob)
    elif args.command == 'uninstall':
        remove_file(args.name, args.glob)
    elif args.command == 'search' or args.command == "s":
        search_by_name(args.name)
    elif args.command == 'monitor' or args.command == "m":
        project.monitor(args.port, args.baud)
    elif args.command == 'target' or args.command == "t":
        handle_target(args)
    elif args.command == 'simulate' or args.command == "sim":
        project.simulate()
    else:
        parser.print_help()


def handle_build(args):
    project.build()
    if args.test:
        return
    plugin = Plugins(ROOT_PLUGIN)

    hook = plugin.get_hook()
    hook.build(args.args)


def handle_clean(args):
    project.clean()
    if args.test:
        return
    plugin = Plugins(ROOT_PLUGIN)

    hook = plugin.get_hook()
    hook.clean(args.args)


def handle_menuconfig(args):
    if len(args.args) == 0:
        project.menuconfig()
    else:
        plugin = Plugins(ROOT_PLUGIN)

        hook = plugin.get_hook()
        hook.menuconfig(args.args)


def handle_flash(args):
    is_project(".")
    plugin = Plugins(ROOT_PLUGIN)

    hook = plugin.get_hook()
    hook.flash(args.args)


def handle_export(args):
    name_abspath = project.before_export(args.name)
    if args.test:
        return
    plugin = Plugins(ROOT_PLUGIN)

    hook = plugin.get_hook()
    hook.export(name_abspath, args.args)


def handle_update(args):
    name_abspath = project.before_update(args.name)
    if args.test:
        return
    plugin = Plugins(ROOT_PLUGIN)

    hook = plugin.get_hook()
    hook.update(name_abspath, args.args)


def handle_target(args):
    logging.info(f"args: {args}")
    if args.download and not args.show:
        project.download_sdk()
    else:
        project.show_target()


if __name__ == "__main__":
    main()
