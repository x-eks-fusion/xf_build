#!/usr/bin/env python3

import pluggy

HOOK_NAME = "xf_plugins"

_hookspec = pluggy.HookspecMarker(HOOK_NAME)


class PluginsHookspec():
    """
    这里用来指定插件的规则模板，
    后续的插件按照这个类去做，
    加上装饰器后会自动搜索同名的函数作为钩子
    """
    @_hookspec
    def build(self, args) -> None:
        pass

    @_hookspec
    def clean(self, args) -> None:
        pass

    @_hookspec
    def flash(self, args) -> None:
        pass

    @_hookspec
    def menuconfig(self, args) -> None:
        pass

    @_hookspec
    def export(self, name, args) -> None:
        pass

    @_hookspec
    def update(self, name, args) -> None:
        pass
