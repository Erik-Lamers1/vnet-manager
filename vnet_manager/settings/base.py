import sys
from unipath import Path
from os.path import join, expanduser
from os import getenv

PYTHON_PACKAGE_NAME = "vnet-manager"
PROJECT_DIR = Path(__file__).absolute().ancestor(3)

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
        "console": {"class": "logging.StreamHandler", "formatter": "console",},
        "syslog": {
            "class": "logging.handlers.SysLogHandler",
            "formatter": "syslog",
            "address": "/dev/log",  # remove this to use UDP port 514
        },
    },
    "root": {"handlers": ["console", "syslog"], "level": "DEBUG",},
    # Silence debug heavy loggers here
    "loggers": {"urllib3": {"level": "INFO",}, "ws4py": {"level": "WARNING",}, "pyroute2.netlink": {"level": "INFO"}},
}

# VNet Manager static settings / config
VALID_ACTIONS = ["list", "start", "stop", "create", "destroy", "version"]
CONFIG_DEFAULTS_LOCATION = getenv("VNET_DEFAULT_CONFIG_PATH", join(expanduser("~"), PYTHON_PACKAGE_NAME, "config/defaults.yaml"))
VNET_BRIDGE_NAME = "vnet-br"
VNET_SNIFFER_PCAP_DIR = getenv("VNET_SNIFFER_PCAP_DIR", "/tmp")
SUPPORTED_MACHINE_TYPES = ["host", "router"]
MACHINE_TYPE_PROVIDER_MAPPING = {
    "host": "lxc",
    "router": "lxc",
}
MACHINE_TYPE_CONFIG_FUNCTION_MAPPING = {
    # For each machine type specify the type specific functions that should be called for it
    "host": [],
    "router": ["configure_{}_ip_forwarding".format(MACHINE_TYPE_PROVIDER_MAPPING["router"])],
}
VALID_STATUSES = ["start", "stop"]
VNET_FORCE_ENV_VAR = "VNET_FORCE"
VNET_ETC_HOSTS_FILE_PATH = "/tmp/vnet_etc_hosts"
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

# LXC specific settings
LXC_MAX_STATUS_WAIT_ATTEMPTS = 15
LXC_STATUS_WAIT_SLEEP = 4
LXC_STORAGE_POOL_NAME = "vnet-pool"
LXC_STORAGE_POOL_DRIVER = "btrfs"
LXC_STORAGE_POOL_SIZE = "30GB"
LXC_BASE_IMAGE_ALIAS = getenv("VNET_LXC_BASE_IMAGE", "vnet-base-image")
LXC_BASE_IMAGE_MACHINE_NAME = "vnet-base"
LXC_VNET_PROFILE = "vnet-profile"

# FRR settings
FRR_RELEASE = "frr-stable"
