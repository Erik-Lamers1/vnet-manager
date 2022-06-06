from logging import getLogger

from vnet_manager.providers.lxc import get_lxd_client
from vnet_manager.conf import settings

logger = getLogger(__name__)


def check_if_lxc_profile_exists(name: str) -> bool:
    """
    Check if an LXC profile exists
    :param str name: The LXC profile to check for
    :return bool: True if it exists, false otherwise
    """
    return get_lxd_client().profiles.exists(name)


def create_vnet_lxc_profile(name: str):
    """
    Create a VNet specific LXC profile
    :param str name: The LXC profile to create
    """
    client = get_lxd_client()
    # Check if the profile already exists
    if check_if_lxc_profile_exists(name):
        raise RuntimeError(f"Tried to create VNet LXC profile {name}, but it already exists")

    devices = {
        # Disk config
        "root": {
            "path": "/",
            "pool": settings.LXC_STORAGE_POOL_NAME,
            "type": "disk",
        }
    }
    logger.info(f"Creating LXC profile for storage pool {settings.LXC_STORAGE_POOL_NAME}")
    client.profiles.create(name, config={}, devices=devices)


def delete_vnet_lxc_profile(name: str):
    """
    Deletes a VNet specific LXC profile
    Profile must not be used when deleting
    :param str name: The LXC profile to delete
    """
    # Check if the profile even exists
    if not check_if_lxc_profile_exists(name):
        logger.warning(f"Tried to delete LXC profile {name}, but it didn't exist, skipping...")
        return

    client = get_lxd_client()
    # Check if the profile is still in use
    profile = client.profiles.get(name)
    if profile.used_by:
        logger.error(f"LXC profile {name} still used by: {', '.join(profile.used_by)}")
        logger.critical(f"LXC profile {name} is still in use, please destroy any remaining machines first")
        raise RuntimeError(f"LXC profile {name} is still in use")
    logger.info(f"Deleting LXC profile {name}")
    profile.delete()
