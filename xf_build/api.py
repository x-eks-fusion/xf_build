import subprocess
import json
import os
from pathlib import Path
from .env import PROJECT_BUILD_ENV
from .env import XF_ROOT
from .env import XF_TARGET_PATH
from .env import XF_PROJECT_PATH
from .env import PROJECT_BUILD_PATH
from .env import ROOT_PLUGIN
from .env import PROJECT_CONFIG_PATH
from jinja2 import FileSystemLoader, Environment
from .menuconfig import MenuConfig
import logging
import threading
from typing import List, Tuple, Union


def exec_cmd(command: Union[str, List[str]]) -> Tuple[int, List[str], List[str]]:
    def stream_reader(pipe, output_list):
        for line in iter(pipe.readline, ''):
            print(line.strip())
            output_list.append(line.strip())
        pipe.close()

    if isinstance(command, list):
        command = ' '.join(command)

    logging.info(f"exec cmd {command}")

    stdout_lines = []
    stderr_lines = []

    process = subprocess.Popen(command, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True,
                               shell=True)

    # Create threads to read stdout and stderr
    stdout_thread = threading.Thread(target=stream_reader, args=(
        process.stdout, stdout_lines))
    stderr_thread = threading.Thread(target=stream_reader, args=(
        process.stderr, stderr_lines))

    # Start the threads
    stdout_thread.start()
    stderr_thread.start()

    # Wait for the process to complete
    process.wait()

    # Wait for the threads to complete
    stdout_thread.join()
    stderr_thread.join()

    return process.returncode, stdout_lines, stderr_lines


def apply_template(temp, save, replace=None):
    with open(PROJECT_BUILD_ENV, "r") as json_file:
        config_data = json.load(json_file)

    file_loader = FileSystemLoader(ROOT_PLUGIN)
    env = Environment(loader=file_loader)

    template = env.get_template(temp)
    output = template.render(config_data)

    if replace is not None:
        for key, value in replace.items():
            output = output.replace(key, value)

    with open(save, 'w') as output_file:
        output_file.write(output)

    logging.info(f"Template applied successfully to {save}")


def apply_components_template(temp, suffix):
    def template_generation(config_data, save_path):
        output = template.render(config_data)
        save_path = Path(PROJECT_BUILD_PATH).joinpath(*save_path)
        if not save_path.exists():
            save_path.mkdir(parents=True, exist_ok=True)
        if suffix[0] == '.':
            final_save = save_path / (save_path.name + suffix)
        else:
            final_save = save_path / suffix
        with open(final_save, 'w') as output_file:
            output_file.write(output)
        logging.info(f"Template applied successfully to {final_save}")

    with open(PROJECT_BUILD_ENV, "r") as json_file:
        config_data = json.load(json_file)

    file_loader = FileSystemLoader(ROOT_PLUGIN)
    env = Environment(loader=file_loader)
    template = env.get_template(temp)

    for i in config_data["public_components"]:
        template_generation(config_data["public_components"][i], [
                            "public_components", i])

    for i in config_data["user_components"]:
        template_generation(config_data["user_components"][i], [
                            "user_components", i])

    for i in config_data["user_dirs"]:
        template_generation(config_data["user_dirs"][i], [
                            "user_dirs", i])

    template_generation(config_data["user_main"], ["user_main"])


def get_define(define):
    config = MenuConfig(PROJECT_CONFIG_PATH,
                        XF_TARGET_PATH, PROJECT_BUILD_PATH)
    return config.get_macro(define)


def cd_to_root():
    os.chdir(XF_ROOT)


def cd_to_target():
    os.chdir(XF_TARGET_PATH)


def cd_to_project():
    os.chdir(XF_PROJECT_PATH)


def get_sdk_dir():
    target_json_path = Path(XF_TARGET_PATH) / "target.json"
    if not target_json_path.exists():
        return ""
    with target_json_path.open("r", encoding="utf-8") as f:
        target_json = json.load(f)
    if not target_json["sdks"].get("dir"):
        return ""
    return target_json["sdks"]["dir"]


def get_XF_ROOT():
    return XF_ROOT


def get_XF_TARGET_PATH():
    return XF_TARGET_PATH


def get_XF_PROJECT_PATH():
    return XF_PROJECT_PATH


def get_PROJECT_BUILD_PATH():
    return PROJECT_BUILD_PATH


def get_ROOT_PLUGIN():
    return ROOT_PLUGIN


def get_PROJECT_CONFIG_PATH():
    return PROJECT_CONFIG_PATH
