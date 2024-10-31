import requests
import json
import logging
from pathlib import Path
import hashlib
from zipfile import ZipFile
import io
import shutil
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

from ..env import ROOT_COMPONENTS, PROJECT_COMPONENTS

HOST = "http://server1.ptwsmart.com:31300"
SEARCH_API = "{HOST}/api/component/search/{keywords}"
INSTALL_API = "{HOST}/api/component/download/{name}:{version}.zip"


class ComponentNotFoundError(Exception):
    pass


class ComponentBroken(Exception):
    pass


def search_component(name: str):
    res = requests.get(SEARCH_API.format(HOST=HOST, keywords=name))
    if res.status_code == 200:
        return json.loads(res.content.decode())
    elif res.status_code == 404:
        raise ComponentNotFoundError(
            "can't found components {name}".format(name=name))


def search_by_name(name: str):
    console = Console()
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="dim", width=12)
    table.add_column("Version")
    table.add_column("license")
    table.add_column("author")
    result = search_component(name)
    if not result:
        logging.error("not find components")
        return
    for item in result:
        table.add_row(item["name"], item["version"],
                      item["license"], item["author"])
    console.print(table)


def download_component(name: str, version):
    _version = version if version else "last"
    res = requests.get(INSTALL_API.format(
        HOST=HOST, name=name, version=_version))
    if res.status_code != 200:
        res.raise_for_status()
    data = json.loads(res.content.decode())
    file_url = data["url"]
    check_sum = data["file_hash"]

    with requests.get(file_url, stream=True) as response:
        if response.status_code == 404:
            raise ComponentNotFoundError(
                f"Can't find component {name}"
            )
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 Kibibyte
        progress = Progress()
        task = progress.add_task("Downloading...", total=total_size)

        content = b""
        with progress:
            for data in response.iter_content(block_size):
                progress.update(task, advance=len(data))
                content += data
    return content, check_sum


def calculate_zip_hash(content):
    hasher = hashlib.sha256()
    hasher.update(content)
    return hasher.hexdigest()


def decompress_zip_response(extract_path, content):
    with ZipFile(io.BytesIO(content)) as zip_file:
        for member in zip_file.namelist():
            zip_file.extract(member, path=extract_path)


def download_file(name: str, version=None, glob=False):
    extract_path = Path(ROOT_COMPONENTS if glob else PROJECT_COMPONENTS)
    extract_path = extract_path / name
    if extract_path.exists():
        logging.error(f"组件{name}已存在")
        return

    content, check_sum = download_component(name=name, version=version)
    file_hash = calculate_zip_hash(content)
    logging.debug(f"file_hash:{file_hash}")
    logging.debug(f"check_sum:{check_sum}")
    if file_hash != check_sum:
        raise ComponentBroken(f"The component {name} is invalid")
    decompress_zip_response(extract_path, content)
    logging.info(f"组件{name}安装成功")


def remove_file(name, glob=False):
    file_path: Path = Path(ROOT_COMPONENTS if glob else PROJECT_COMPONENTS)
    file_path = file_path / name
    if file_path.exists():
        shutil.rmtree(file_path)
        logging.info(f"组件{name}移除成功")
