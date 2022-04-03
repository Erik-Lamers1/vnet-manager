from logging import getLogger
from sys import modules
from distro import codename

from vnet_manager.conf import settings


logger = getLogger(__name__)

try:
    from apt import Cache
except (ImportError, ModuleNotFoundError):
    logger.error("Python apt module not installed, please 'apt-get install python3-apt' first")
    logger.warning("Will not preform host checks without apt module")


def check_for_supported_os(provider: str) -> bool:
    """
    Checks if VNet is running on a supported OS for a provider
    :param str provider: The provider to check OS support for
    :return: bool: True if the current OS is supported, False otherwise
    """
    logger.debug("Checking if your os is supported for provider {}".format(provider))
    return codename().lower() in settings["PROVIDERS"][provider]["supported_operating_systems"]


def check_for_installed_packages(provider: str) -> bool:
    """
    Checks if the required host packages have been installed
    :param str provider: The provider to check the required host packages for
    :return bool: True if all required packages have been installed, False otherwise
    """
    logger.debug("Checking if all required host packages have been install for provider {}".format(provider))
    all_installed = True
    cache = Cache()
    if "apt" not in modules:
        logger.warning("Skipping host package rquirements check, apt module missing")
    else:
        for package in settings["PROVIDERS"][provider]["required_host_packages"]:
            if not cache[package].is_installed:
                logger.error("Required host package {} for provider {} is not installed".format(package, provider))
                all_installed = False
    return all_installed
