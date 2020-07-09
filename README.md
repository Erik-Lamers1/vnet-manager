# VNet-manager
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

VNet-manager a virtual network manager - manages containers and VMs to create virtual networks

## Setup
```bash
apt-get update
apt-get install gcc python3-dev git lxd lxc bridge-utils tcpdump net-tools curl
git clone https://github.com/Erik-Lamers1/vnet-manager.git
cd vnet-manager
python3 setup.py install
# The following is only needed on Xenial
apt-get install btrfs-tools
```
