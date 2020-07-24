# VNet-manager
[![Build Status](https://travis-ci.org/Erik-Lamers1/vnet-manager.svg?branch=master)](https://travis-ci.org/Erik-Lamers1/vnet-manager)
[![codecov](https://codecov.io/gh/Erik-Lamers1/vnet-manager/branch/master/graph/badge.svg)](https://codecov.io/gh/Erik-Lamers1/vnet-manager)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

VNet-manager a virtual network manager - manages containers to create virtual networks

## What is it?
VNet-manager allows you to create quick virtual network setups using LXC containers.
VNet-manager will create and manage the containers you need to create a virtual network.
This is done in combination with [FRRouting](https://frrouting.org/).
## Setup
```bash
apt-get update
apt-get install gcc python3-dev python3-apt python3-pip git lxd lxc bridge-utils tcpdump net-tools curl
# LXD defaults are fine
echo -e "\n\n\n\n\n\n\n\n\n\n\n\n" | lxd init
git clone https://github.com/Erik-Lamers1/vnet-manager.git
cd vnet-manager
python3 setup.py install
# The following is only needed on Xenial
apt-get install btrfs-tools
# Now you are able to use
vnet-manager --help
```

#### Quick start
```bash
cd ~/vnet-manager
vnet-manager create config/example.yaml
vnet-manager start config/example.yaml
lxc exec host1 -- ping -c 2 router1
```
## How to use it
First you need to create a config file for VNet-manager to work with.
In your config file you define the topology of your network. See the [config](config) directory for examples.  

There are two important config files. First off the config file you use to create your topology (the user config file).
The second config file is the defaults config, which stores generic information you might want to edit if you are an advanced user.
The user config file should always be passed to VNet-manager as an argument. This allows for multiple topologies to exist at once.
The defaults config file can be set using the `VNET_DEFAULT_CONFIG_PATH` environment variable. If this variable does not exist VNet-manager will assume `~/vnet-manager/config/defaults.yaml`, which is usually fine.

### Advanced usage
There are a couple of things that can be tweaked when using VNet-manager. This can be done using specific environment variables.
```yaml
VNET_DEFAULT_CONFIG_PATH - Sets the absolute location of the defaults.yaml config
VNET_SNIFFER_PCAP_DIR    - Sets the directory where the sniffer PCAP files will be created
VNET_LXC_BASE_IMAGE      - Sets the alias for the LXC base image, only set when using a custom base image
VNET_FORCE               - Internal env var, used with --yes. Do not set manually
```

## Development
Opening pull requests for new features and bug fixes is highly appreciated!  
Before you do make sure you setup your development environment.
```bash
apt-get install tox virtualenvwrapper libapt-pkg-dev intltool
# Depending on your console setup, you might have to logout and in again to make sure virtualenvwrapper is loaded
# cd to your development directory
cd ~/vnet-manager
mkvirtualenv -p /usr/bin/python3.6 -a $(pwd) vnet-manager
pip install -U pip
pip install -r requirements/development.txt
pre-commit install
```
### Running the tests
Simply run `tox` in the vnet-manager directory.
