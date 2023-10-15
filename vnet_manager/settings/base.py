import sys
from pathlib import Path
from os.path import join
from os import getenv

PYTHON_PACKAGE_NAME = "vnet-manager"
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
YAMLLINT_CONFIG_FILE = join(PROJECT_DIR, "yamllint.yaml")
CONFIG_FILE_DIR = join(PROJECT_DIR, "config")

# Log settings
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "()": "vnet_manager.utils.logging.formatters.ConsoleFormatter",
            "fmt": "%(asctime)s [%(name)8s] [%(levelname)s] %(message)s",
            "colored": sys.stderr.isatty,  # StreamHandler uses stderr by default
        },
        "syslog": {"format": "[%(process)d] %(name)s [%(levelname)s]: %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
        "syslog": {
            "class": "logging.handlers.SysLogHandler",
            "formatter": "syslog",
            "address": "/dev/log",  # remove this to use UDP port 514
        },
    },
    "root": {
        "handlers": ["console", "syslog"],
        "level": "DEBUG",
    },
    # Silence debug heavy loggers here
    "loggers": {
        "urllib3": {
            "level": "INFO",
        },
        "ws4py": {
            "level": "CRITICAL",
        },
        "pyroute2": {"level": "INFO"},
        "pyroute2.ndb": {"level": "WARNING"},
    },
}
LOGGING_DEFAULT_VERBOSITY = 3  # logging.INFO

# VNet Manager static settings / config
# provider config
# The provider config defines some parameters that are used by VNet-manager for configuration. Most notably, the provider settings.
# Below the provider, config options are defined.
PROVIDERS = {
    "lxc": {
        "supported_operating_systems": ["bionic", "focal", "jammy"],  # Will not run on any other OSes
        "dns-nameserver": "8.8.8.8",
        "guest_packages": [
            "man",  # List of packages to install on the guest
            "net-tools",
            "traceroute",
            "nano",
            "vim",
            "bridge-utils",
            "radvd",
            "frr",
            "frr-pythontools",
            "vlan",
            "avahi-daemon",
            "avahi-utils",
        ],
        "base_image": {  # Download info for the base image
            "os": "22.04",
            "server": "https://cloud-images.ubuntu.com/daily",
            "protocol": "simplestreams",
        },
    }
}
SHELL = "/bin/bash"
VNET_BRIDGE_NAME = "vnet-br"
VNET_SNIFFER_PCAP_DIR = getenv("VNET_SNIFFER_PCAP_DIR", "/tmp")
SUPPORTED_MACHINE_TYPES = ["host", "router"]
MACHINE_TYPE_PROVIDER_MAPPING = {
    "host": "lxc",
    "router": "lxc",
}
MACHINE_TYPE_CONFIG_FUNCTION_MAPPING = {
    # For each machine type specify the type specific functions that should be called for it
    "host": [f"disable_{MACHINE_TYPE_PROVIDER_MAPPING['router']}_ip_forwarding"],
    "router": [f"enable_{MACHINE_TYPE_PROVIDER_MAPPING['router']}_ip_forwarding"],
}
VALID_STATUSES = ["start", "stop"]
VNET_FORCE_ENV_VAR = "VNET_FORCE"
VNET_ETC_HOSTS_FILE_PATH = "/tmp/.vnet_etc_hosts"
VNET_STATIC_HOSTS_FILE_PART = """
127.0.0.1 localhost

# The following lines are desirable for IPv6 capable hosts
::1 ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
ff02::3 ip6-allhosts

# VNet hosts

"""
VNET_NETPLAN_CONFIG_FILE_PATH = "/etc/netplan/10-vnet-config.yaml"
VNET_BASH_COMPLETION_TEMPLATE = """#!/usr/bin/env bash

_{name}_completions() {{
    local opts
    opts="{options}"
    case $COMP_CWORD in
        1)
            COMPREPLY=( $(compgen -W "${{opts}}" -- "${{COMP_WORDS[COMP_CWORD]}}") )
            ;;
        2)
            COMPREPLY=( $(compgen -o default -- "${{COMP_WORDS[COMP_CWORD]}}") )
            ;;
    esac
    return 0
}}
complete -F _{name}_completions {name}
"""
VNET_BASH_COMPLETION_PATH = f"/etc/bash_completion.d/{PYTHON_PACKAGE_NAME}.bash"

# LXC specific settings
LXC_MAX_STATUS_WAIT_ATTEMPTS = 15
LXC_STATUS_WAIT_SLEEP = 4
LXC_STATUS_BACKOFF_MULTIPLIER = 0.3
LXC_STORAGE_POOL_NAME = "vnet-pool"
LXC_STORAGE_POOL_DRIVER = "btrfs"
LXC_STORAGE_POOL_SIZE = "30GB"
LXC_BASE_IMAGE_ALIAS = getenv("VNET_LXC_BASE_IMAGE", "vnet-base-image")
LXC_BASE_IMAGE_MACHINE_NAME = "vnet-base"
LXC_VNET_PROFILE = "vnet-profile"

# FRR settings
FRR_RELEASE = "frr-stable"
