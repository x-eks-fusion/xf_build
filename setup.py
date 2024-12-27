#!/usr/bin/env python3

from setuptools import setup, find_packages
from pathlib import Path

XF_VERSION: str = "0.4.0"

HERE = Path(__file__).parent
README = (HERE / "README.md").read_text(encoding="utf-8")

setup(
    name='xf_build',
    version=XF_VERSION,
    author='kirto',
    author_email='sky.kirto@qq.com',
    description="A tools for xfusion",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires='>=3.6',
    include_package_data=True,
    install_requires=[
        'jinja2',
        'kconfiglib',
        'requests',
        'rich',
        'art',
        'pyserial'
    ],
    entry_points='''
        [console_scripts]
        xf=xf_build.cmd.cmd:main
    ''',
    url="http://www.coral-zone.cc/",
    long_description=README,
    long_description_content_type="text/markdown"
)
