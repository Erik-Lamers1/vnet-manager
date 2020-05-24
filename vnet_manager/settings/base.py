import sys
from unipath import Path
from os.path import join

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
}

# VNet Manager static settings / config
VALID_ACTIONS = ["list", "start", "stop", "create", "destroy", "version"]
CONFIG_DEFAULTS_LOCATION = join(PROJECT_DIR, "config/defaults.yaml")
VNET_BRIDGE_NAME = PYTHON_PACKAGE_NAME + "-br"
