# xf build

基于python制作的构建系统，目的是为了生成成makefile cmake等其它的构建方式的构建器。
与传统的构建方式不同的是，本构建方式不会直接编译，且不会产生直接用于编译的其它构建脚本。
而是收集编译需要的相关信息生成json，最终需要配合插件系统适配不同底层环境，最终完成与底层sdk工程的合作编译。

# 原理

首先，我们了解一下环境变量

XF_ROOT: 记录 xfusion 根目录绝对路径
XF_TARGET：记录具体激活的平台
XF_TARGET_PATH: 记录激活平台的源工程绝对路径

XF_PROJECT_PATH(可选): 记录当前工程绝对路径，如果没有设置，则会将当前执行命令的路径设置为工程路径 
XF_PROJECT(可选): 记录当前工程名称，如果没有设置，则会将当前执行命令的文件夹名设置为工程路径

# 开源地址

[github](https://github.com/x-eks-fusion/xf_build)

[gitee](https://gitee.com/x-eks-fusion/xf_build)

# 安装

```shell
pip install xf_build
```

# 命令介绍

```shell
xf --help        
Usage: xf [OPTIONS] COMMAND [ARGS]...

Options:
  -v, --verbose  Enable verbose mode.
  -r, --rich     Enable rich mode.
  -t, --test     Enable test mode.
  --help         Show this message and exit.

Commands:
  build       编译工程
  clean       清空编译中间产物
  create      初始化创建一个新工程
  export      导出对应sdk的工程（需要port对接）
  flash       烧录工程（需要port对接）
  install     安装指定的包
  menuconfig  全局宏的配置
  search      模糊搜索包名
  uninstall   卸载指定的包
  update      更新对应sdk的工程（需要port对接）
  version     查询当前版本
```

### build 命令

build 命令在执行时，会检查当前路径下是否有 xf_project.py 来判断是否出于工程文件夹中。如果不是则无法继续执行。而后，会检查当前的 target 和 project 是与上次不同则会调用 clean 命令清除之前编译生成的中间文件。然后，直接执行当前的 xf_project.py ，xf_project.py 来将 XF_ROOT/components/\*/xf_collect.py , XF_PROJECT_PATH/components/\*/xf_collect.py 和 XF_PROJECT_PATH/main/xf_collect.py 执行一遍。最后，收集成为 build 文件夹下 build_info.json 文件。
然后调用 XF_ROOT/plugins/XF_TARGET 路径下的插件。完成后续 build_info.json 转换成构建脚本，并编译的功能。

### clean 命令

clean 会删除当前的 build 文件夹，而后会调用插件的 clean 命令。

### create 命令

create 命令会复制 XF_ROOT/example/get_started/template_project 到当前目录并改名

### export 命令

export 命令需要插件实现其功能

### flash 命令

flash 命令需要插件实现其功能

### install 命令

install 命令是通过 requests 请求远端的服务器下载指定的软件包。
如果远端有则下载后解压并放入 compoents 文件夹中

### menuconfig 命令

install 命令是收集 XF_ROOT/components/\*/XFKconfig 和 XF_PROJECT_PATH/components/\*/XFKconfig 并生成命令行可视化配置界面。配置完成后会在 build/header_config 文件夹下，生成 xfconfig.h 文件。

### search 命令

search 命令是可以查询包名是否存在

### uninstall 命令

uninstall 命令可以帮你删除指定的组件

### update 命令

update 命令需要底层插件支持，其功能是更新导出的工程。与 export 不同的是，该命令不会创建新工程

### version 命令   

version 命令会获取当前 xf_build 版本

