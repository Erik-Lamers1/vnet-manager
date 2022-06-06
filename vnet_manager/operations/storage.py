from logging import getLogger
from pylxd.exceptions import LXDAPIException

from vnet_manager.providers.lxc import get_lxd_client
from vnet_manager.conf import settings

logger = getLogger(__name__)


def check_if_lxc_storage_pool_exists(name: str = settings.LXC_STORAGE_POOL_NAME) -> bool:
    """
    Check for the existence of the LXC storage pool defined in the settings
    :param str name: The name of the storage pool to check for (default from the settings)
    :return: bool: True if the pool exists, False otherwise
    """
    logger.debug(f"Checking for the existence of LXC {name} storage pool")
    return get_lxd_client().storage_pools.exists(name)


def create_lxc_storage_pool(name: str = settings.LXC_STORAGE_POOL_NAME, driver: str = settings.LXC_STORAGE_POOL_DRIVER):
    """
    Creates a new LXC storage pool with the passed driver and name
    :param str name: The name of the storage pool to create (default from settings)
    :param str driver: The driver to use (default from settings)
    """
    # Sanity check, we don't want to create duplicate pools
    if check_if_lxc_storage_pool_exists(name):
        raise RuntimeError(f"LXC storage pool {name} already exists, cannot create duplicate")

    # Make it
    logger.info(f"Creating LXC storage pool {name} with driver {driver}")
    client = get_lxd_client()
    try:
        client.storage_pools.create({"name": name, "driver": driver, "config": {"size": settings.LXC_STORAGE_POOL_SIZE}})
        logger.info(f"Storage pool {name} with driver {driver} successfully created")
    except LXDAPIException as e:
        logger.critical(f"Got API error while creating storage pool {name}. Error: {e}")
        raise RuntimeError(f"Received API error while creating storage pool {name}") from e


def delete_lxc_storage_pool(name: str):
    """
    Deletes a LXC storage pool
    Pool must be empty before deletion
    :param str name: The name of the pool to delete
    """
    # Check if the pool even exists
    if not check_if_lxc_storage_pool_exists(name):
        logger.warning(f"Tried to delete LXC storage pool {name}, but it didn't exist, skipping...")
        return

    client = get_lxd_client()
    # Try to delete it
    try:
        logger.info(f"Deleting LXC storage pool {name}")
        client.storage_pools.get(name).delete()
    except LXDAPIException as e:
        logger.critical(f"Got API error while deleting storage pool {name}. Error: {e}")
        raise RuntimeError(f"Received API error while deleting storage pool {name}") from e
