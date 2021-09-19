#!/usr/bin/env python3
import os
from setuptools import setup, find_packages

VERSION = "0.8.1"

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="vnet-manager",
    version=VERSION,
    url="https://github.com/Erik-Lamers1/vnet-manager",
    download_url="https://github.com/Erik-Lamers1/vnet-manager/archive/{}.tar.gz".format(VERSION),
    packages=find_packages(exclude=["tools", "tools.*", "tests", "tests.*", "*.tests", "*.tests.*"]),
    author="Erik Lamers",
    license="MIT",
    # PyLXD 2.2.11 is currently broken: https://github.com/lxc/pylxd/issues/404
    install_requires=["colorama", "PyYAML", "tabulate", "pylxd==2.2.10", "pyroute2", "psutil", "distro"],
    entry_points={
        "console_scripts": [
            "vnet-manager = vnet_manager.vnet_manager:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
