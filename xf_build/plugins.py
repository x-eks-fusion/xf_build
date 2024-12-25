#!/usr/bin/env python3

import sys
import importlib
import logging
from pathlib import Path


class Plugins:
    def __init__(self, path) -> None:
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
        self.hook = module_class()

    def get_hook(self):
        return self.hook
