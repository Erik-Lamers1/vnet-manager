from logging import getLogger
from distro import codename

from vnet_manager.conf import settings

logger = getLogger(__name__)


def check_for_supported_os(provider: str) -> bool:
    """
    Checks if VNet is running on a supported OS for a provider
    :param str provider: The provider to check OS support for
    :return: bool: True if the current OS is supported, False otherwise
    """
    logger.debug(f"Checking if your os is supported for provider {provider}")
    return codename().lower() in settings["PROVIDERS"][provider]["supported_operating_systems"]
