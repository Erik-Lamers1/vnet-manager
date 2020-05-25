#!/usr/bin/env python3
import os
from setuptools import setup, find_packages

VERSION = "0.1"

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="vnet-manager",
    version=VERSION,
    url="https://github.com/Erik-Lamers1/vnet-manager",
    packages=find_packages(exclude=["tests", "tests.*", "vnet_manager.tests", "vnet_manager.tests.*"]),
    author="Erik Lamers",
    license="MIT",
    install_requires=["colorama", "unipath", "six", "PyYAML", "tabulate"],
    entry_points={"console_scripts": ["vnet-manager = vnet_manager.vnet_manager:main",],},
)
