import os
from pathlib import Path
from kconfiglib import Kconfig
from menuconfig import menuconfig
from collections import defaultdict
import logging


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

    @classmethod
    def search_XFKconfig(cls, name, path) -> str:
        """
        收集path路径下的XFKconfig，并自动通过路径生成多级菜单

        :param name 最上层菜单名称
        :param path 搜索根路径
        :return 格式化完成的多级菜单XFKconfig字符串
        """

        def build_tree_from_paths(paths) -> dict:
            def _add_path_to_tree(tree, path) -> None:
                parts = path.split("/")
                node = tree
                for part in parts:
                    node = node.setdefault(part, {})

            tree = defaultdict(dict)
            for path in paths:
                _add_path_to_tree(tree, path.as_posix())

            return dict(tree)

        def format_tree(tree, menu, base_path) -> str:
            path = Path("")
            stack = [(1, "", tree, iter(tree.items()))]
            output: list[str] = [f'menu "{menu}"']
            while stack:
                try:
                    indent, _, __, iterator = stack[-1]
                    sub_indent = "  " * indent
                    child_key, child_node = next(iterator)
                    if child_node != {}:
                        path = path / child_key
                        output.append(f'{sub_indent}menu "{child_key}"')
                        stack.append(
                            (
                                indent + 1,
                                child_key,
                                child_node,
                                iter(child_node.items()),
                            )
                        )
                    else:
                        _path = base_path / path / child_key
                        output.append(
                            f'{sub_indent}source "{_path.as_posix()}"')
                except StopIteration:
                    stack.pop()
                    if len(stack) == 0:
                        break
                    path = path.parent
                    indent, _, __, iterator = stack[-1]
                    sub_indent = "  " * indent
                    output.append(f"{sub_indent}endmenu")
            output.append("endmenu")
            return "\n".join(output)

        file_paths = []  # 存储文件路径的列表

        if isinstance(path, str):
            path = Path(path).resolve()
        else:
            path = path.resolve()

        for entry in path.iterdir():
            if not entry.is_dir():
                continue
            for entry2 in entry.iterdir():
                if not entry2.is_file() or entry2.name != cls.XFKCONFIG_NAME:
                    continue
                file_paths.append(entry2)

        path_rel = [i.relative_to(path) for i in file_paths]
        path_tree = build_tree_from_paths(path_rel)
        path_file: str = format_tree(path_tree, name, path)
        path_file += "\n"

        return path_file

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
