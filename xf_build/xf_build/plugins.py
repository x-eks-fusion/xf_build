#!/usr/bin/env python3

import pluggy

import sys
import importlib
import logging
from pathlib import Path

from .plugins_hookspec import HOOK_NAME, PluginsHookspec


_hookimpl = pluggy.HookimplMarker(HOOK_NAME)  # 用户调用的装饰器


def get_hookimpl() -> pluggy.HookimplMarker:
    return _hookimpl


class Plugins(pluggy.PluginManager):
    def __init__(self) -> None:
        super().__init__(HOOK_NAME)
        self.add_hookspecs(PluginsHookspec)

    def add(self, path) -> None:
        if isinstance(path, str):
            path = Path(path)
        if not path.exists():
            return
        path = path.resolve()
        module_path = path / "__init__.py"
        if not module_path.exists():
            return
        module_name = path.name
        sys.path.append((path / "..").resolve().as_posix())
        module: sys.ModuleType = importlib.import_module(module_name)
        logging.debug(f"module:{module}")
        if not hasattr(module, module_name):
            logging.error(f"module not have {module_name} class")
            return
        module_class = getattr(module, module_name)
        self.register(module_class())

    def get_hook(self) -> pluggy.HookRelay:
        return self.hook
