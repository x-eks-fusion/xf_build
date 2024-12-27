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
  -v, --verbose  打印更多日志信息
  -r, --rich     使用rich库打印日志
  -t, --test     测试模式（不会调用插件）
  --help         Show this message and exit.

Commands:
  build       编译工程
  clean       清空编译中间产物
  create      初始化创建一个新工程
  export      导出对应sdk的工程（需要port对接）
  flash       烧录工程（需要port对接）
  install     安装指定的包
  menuconfig  全局宏的配置
  monitor     串口监视器
  search      模糊搜索包名
  target      target 相关操作：展示目标或下载SDK
  uninstall   卸载指定的包
  update      更新对应sdk的工程（需要port对接）
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

### monitor 命令

使用命令行串口监视器，Ctrl+]退出串口监视器

### search 命令

search 命令是可以查询包名是否存在

### target 命令

该命令主要用于和target相关的操作，-s展示当前的target信息，-d下载当前的target sdk

### uninstall 命令

uninstall 命令可以帮你删除指定的组件

### update 命令

update 命令需要底层插件支持，其功能是更新导出的工程。与 export 不同的是，该命令不会创建新工程


# 历史更新记录

**v0.4.0**
1. 重构了命令行和插件系统，抛弃了 click 和 pluggy 库的引用
2. 修复串口流控拉高导致的串口无法打印
3. 修复 update 不会生成 json 问题
4. 修复 export 和 update 会调用 clean 问题
5. 增加 xf simulate 指令。可以配合 [xfusion_simulator](https://github.com/x-eks-fusion/xfusion_simulator)
6. 支持组件中 import 包含子构建脚本

**v0.3.9**
1. xf target 默认执行 xf target -s 功能
2. 新增pyseiral依赖
3. 对 xfusion 未激活的报错进行处理，提醒 export

**v0.3.7**
1. 修复 user_dirs 在 apply_components_template() 中无效的bug
2. 新增获取target的sdk路径的API

**v0.3.6**
1. 新增monitor功能，用户可以通过monitor使用命令行串口监视器
2. 新增target功能，-s可以查询当前target信息，-d可以下载对应的sdk
3. 当某些指令判断当前不是project工程，则直接raise报错
4. 修改了文件夹结构

**v0.3.1**
1. 预编译阶段调用xf_project.py从被动的执行，改为读取后exec执行。
2. 预编译前期会搜索：public components，user components 的所有子文件夹下是否含有xf_collect.py ，然后将user_dirs也搜索一遍，最后将user_main。构成初期的检索结果 build_info.json
3. 中期调用menuconfig进行生成，menuconfig也会通过build_info.json的路径，进行XFKconfig的搜索
4. 后期会将build_info.json的路径下的xf_collect.py全部执行一遍


**v0.2.3**
1. collect方法添加cflag参数
2. 支持用户自定义文件夹
3. 修改XFKconfig的扫描逻辑，现在会根据build_environ.json进行扫描。
4. port部分的XFConfig会加入扫描中
