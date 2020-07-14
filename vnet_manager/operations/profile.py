from logging import getLogger

from vnet_manager.providers.lxc import get_lxd_client
from vnet_manager.conf import settings

logger = getLogger(__name__)


def check_if_lxc_profile_exists(name):
    """
    Check if an LXC profile exists
    :param str name: The LXC profile to check for
    :return bool: True if it exists, false otherwise
    """
    return get_lxd_client().profiles.exists(name)


def create_vnet_lxc_profile(name):
    """
    Create a VNet specific LXC profile
    :param str name: The LXC profile to create
    """
    client = get_lxd_client()
    # Check if the profile already exists
    if check_if_lxc_profile_exists(name):
        raise RuntimeError("Tried to create VNet LXC profile {}, but it already exists".format(name))

    devices = {
        # Disk config
        "root": {"path": "/", "pool": settings.LXC_STORAGE_POOL_NAME, "type": "disk",}
    }
    logger.info("Creating LXC profile for storage pool {}".format(settings.LXC_STORAGE_POOL_NAME))
    client.profiles.create(name, config={}, devices=devices)


def delete_vnet_lxc_profile(name):
    """
    Deletes a VNet specific LXC profile
    Profile must not be used when deleting
    :param str name: The LXC profile to delete
    """
    # Check if the profile even exists
    if not check_if_lxc_profile_exists(name):
        logger.warning("Tried to delete LXC profile {}, but it didn't exist, skipping...".format(name))
        return

    client = get_lxd_client()
    # Check if the profile is still in use
    profile = client.profiles.get(name)
    if profile.used_by:
        logger.error("LXC profile {} still used by: {}".format(name, ", ".join(profile.used_by)))
        logger.critical("LXC profile {} is still in use, please destroy any remaining machines first".format(name))
        raise RuntimeError("LXC profile {} is still in use".format(name))
    logger.info("Deleting LXC profile {}".format(name))
    profile.delete()
