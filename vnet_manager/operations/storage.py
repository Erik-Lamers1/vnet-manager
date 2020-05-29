from logging import getLogger
from pylxd.exceptions import LXDAPIException

from vnet_manager.providers.lxc import get_lxd_client
from vnet_manager.conf import settings

logger = getLogger(__name__)


def check_if_lxc_storage_pool_exists(name=settings.LXC_STORAGE_POOL_NAME):
    """
    Check for the existence of the LXC storage pool defined in the settings
    :param str name: The name of the storage pool to check for (default from the settings)
    :return: bool: True if the pool exists, False otherwise
    """
    logger.debug("Checking for the existence of LXC {} storage pool".format(name))
    return get_lxd_client().storage_pools.exists(settings.LXC_STORAGE_POOL_NAME)


def create_lxc_storage_pool(name=settings.LXC_STORAGE_POOL_NAME, driver=settings.LXC_STORAGE_POOL_DRIVER):
    """
    Creates a new LXC storage pool with the passed driver and name
    :param str name: The name of the storage pool to create (default from settings)
    :param str driver: The driver to use (default from settings)
    """
    # Sanity check, we don't want to create duplicate pools
    if check_if_lxc_storage_pool_exists(name):
        raise RuntimeError("LXC storage pool {} already exists, cannot create duplicate".format(name))

    # Make it
    logger.info("Creating LXC storage pool {} with driver {}".format(name, driver))
    client = get_lxd_client()
    try:
        client.storage_pools.create({"name": name, "driver": driver})
        logger.info("Storage pool {} with driver {} successfully created".format(name, driver))
    except LXDAPIException as e:
        logger.error("Got API error while creating storage pool {}. Error: {}".format(name, e))
