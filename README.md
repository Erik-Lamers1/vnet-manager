# VNet-manager
[![Pytest](https://github.com/Erik-Lamers1/vnet-manager/actions/workflows/pytest.yml/badge.svg)](https://github.com/Erik-Lamers1/vnet-manager/actions/workflows/pytest.yml)
[![codecov](https://codecov.io/gh/Erik-Lamers1/vnet-manager/branch/master/graph/badge.svg)](https://codecov.io/gh/Erik-Lamers1/vnet-manager)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

VNet-manager a virtual network manager - manages containers to create virtual networks.

## What is it?
VNet-manager allows you to create quick virtual network setups using LXC containers.
VNet-manager will create and manage the containers you need to create a virtual network.
This is done in combination with [FRRouting](https://frrouting.org/).  
Because VNet-manager makes heavy use of LXC, the current supported operating systems are Ubuntu Focal Fossa (20.04) and Jammy Jellyfish (22.04).

## How to use it
In order to run VNet-manager you need to create a config file for the program to works with. In this config file you can create your network topology.
When this config file is created it should always be passed to VNet-manager as an argument. This ensures that the program itself does not have to store any state.
See the [README](config/README.md) for a more detailed explanation on how to create a config file. There are also some [example config files](config)


## Setup

#### Install the required packages
```bash
apt-get update
apt-get install gcc python3-dev python3-apt python3-pip git lxc bridge-utils tcpdump net-tools curl
```
For Ubuntu 18.04;
```bash
# Note that vnet-manager requires python3.8
apt-get install lxd
```
In later versions of Ubuntu;
```bash
snap install lxd
```


#### Clone the repo
```bash
git clone https://github.com/Erik-Lamers1/vnet-manager.git ~/vnet-manager
pip3 install vnet-manager
cd ~/vnet-manager
```
Optionally, vnet-manager can be installed from the cloned repo directly if you want to make changes to the repo locally;
```bash
python3 setup.py install
```

#### Setup LXD
If you are running a clean LXD install you can import the provided preseed file;
```bash
source /etc/os-release
lxd init --preseed < config/lxd/ubuntu$VERSION_ID.yaml
```

If you already had LXD installed, make sure that the there is a the default storage pool, profile and `lxdbr0` network bridge are present.
Depending on your configuration it might still be safe to run the preseed file using `lxd init`.

### Quick start
Use one of the [example](config) configs to see if your environment is working correctly.
```bash
vnet-manager create config/example.yaml
vnet-manager start config/example.yaml
lxc exec host1 -- ping -c 2 router1
```

### Advanced usage
There are a couple of things that can be tweaked when using VNet-manager. This can be done using specific environment variables.
```yaml
VNET_SNIFFER_PCAP_DIR    - Sets the directory where the sniffer PCAP files will be created
VNET_LXC_BASE_IMAGE      - Sets the alias for the LXC base image, only set when using a custom base image
VNET_FORCE               - Internal env var, used with --yes. Do not set manually
```
### Rebuilding the Base Container
Sometimes you will have to rebuild the base container, for instance if you want to install additional packages. To do this you will first have to destroy the base container and then when creating the new setup the base container will be automagically recreated. This might take a bit longer for that reason.
```
$ vnet-manager destroy -b
$ vnet-manager create /path/to/your/config.yaml
```
### Installing Additional Packages
The provider specific packages list can be found in the settings under [`PROVIDERS`](vnet_manager/settings/base.py). 
Here you can specify which packages the host should have and which to install on the base container.
### Extending settings
The default [settings](vnet_manager/settings/base.py) file can be extended with anything you think should be added (or removed) to make your local project work.
The way this can be done is similar to the way settings are loaded in Django, meaning you can set the `SETTINGS_MODULE` env var to let vnet-manager know you are using a custom settings module.
For example, say we want to add support for Gentoo, you can create a custom setting file like this in `vnet_manager/settings/dev.py`;
```python
from .base import *  # pylint: disable=W0401

PROVIDERS["lxc"]["supported_operating_systems"].append("gentoo")
```
Then set your `SETTINGS_MODULE` to point to this file
```bash
export SETTINGS_MODULE=vnet_manager.settings.dev
```

## Development
Opening pull requests for new features and bug fixes is highly appreciated!  
Before you do make sure you set up your development environment.
```bash
apt-get install -y tox virtualenvwrapper libapt-pkg-dev intltool
# Depending on your console setup, you might have to logout and in again to make sure virtualenvwrapper is loaded
# cd to your development directory
cd ~/vnet-manager
mkvirtualenv -p /usr/bin/python3.8 -a $(pwd) vnet-manager
pip install -U pip
pip install -r requirements/development.txt
pre-commit install
```
### Running the tests
Simply run `tox` in the vnet-manager directory.
