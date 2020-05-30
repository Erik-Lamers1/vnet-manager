from logging import getLogger

from vnet_manager.operations.image import check_if_lxc_image_exists, create_lxc_image_from_container
from vnet_manager.operations.profile import check_if_lxc_profile_exists, create_vnet_lxc_profile
from vnet_manager.operations.storage import check_if_lxc_storage_pool_exists, create_lxc_storage_pool
from vnet_manager.operations.machine import create_lxc_base_image_container
from vnet_manager.conf import settings

logger = getLogger(__name__)


def ensure_vnet_lxc_environment(config):
    """
    Checks and creates the LXC environment
    param: dict config: The config created by get_config()
    """
    # Check if there are any LXC machines in the config
    if "lxc" not in [settings.MACHINE_TYPE_PROVIDER_MAPPING[machine["type"]] for machine in config["machines"].values()]:
        logger.debug("Skipping LXC environment creation, no LXC machines in config")
        return

    # Check if the storage pool exists
    if not check_if_lxc_storage_pool_exists(settings.LXC_STORAGE_POOL_NAME):
        logger.info("VNet LXC storage pool does not exist, creating it")
        create_lxc_storage_pool(name=settings.LXC_STORAGE_POOL_NAME, driver=settings.LXC_STORAGE_POOL_DRIVER)
    else:
        logger.debug("VNet LXC storage pool {} found".format(settings.LXC_STORAGE_POOL_NAME))

    # Check if the profile exists
    if not check_if_lxc_profile_exists(settings.LXC_VNET_PROFILE):
        logger.info("VNet LXC profile does not exist, creating it")
        create_vnet_lxc_profile(settings.LXC_VNET_PROFILE)
    else:
        logger.debug("VNet profile {} found".format(settings.LXC_VNET_PROFILE))

    # Check if the base image exists
    if not check_if_lxc_image_exists(settings.LXC_BASE_IMAGE_ALIAS, by_alias=True):
        logger.info("Base image does not exist, creating it")
        create_lxc_base_image_container(config)
        create_lxc_image_from_container(settings.LXC_BASE_IMAGE_MACHINE_NAME, alias=settings.LXC_BASE_IMAGE_ALIAS)
    else:
        logger.debug("Base image {} found".format(settings.LXC_BASE_IMAGE_ALIAS))
