import shlex
from logging import getLogger
from time import sleep
from typing import Tuple, AnyStr

from vnet_manager.operations.image import check_if_lxc_image_exists, create_lxc_image_from_container
from vnet_manager.operations.profile import check_if_lxc_profile_exists, create_vnet_lxc_profile, delete_vnet_lxc_profile
from vnet_manager.operations.storage import check_if_lxc_storage_pool_exists, create_lxc_storage_pool, delete_lxc_storage_pool
from vnet_manager.operations.machine import create_lxc_base_image_container, change_lxc_machine_status, destroy_lxc_machine
from vnet_manager.environment.host import check_for_supported_os, check_for_installed_packages
from vnet_manager.providers.lxc import get_lxd_client
from vnet_manager.conf import settings
from vnet_manager.utils.user import request_confirmation

logger = getLogger(__name__)


def ensure_vnet_lxc_environment(config: dict):
    """
    Checks and creates the LXC environment
    param: dict config: The config created by get_config()
    :raises RuntimeError: If unsupported OS, or missing packages
    """
    # Check if there are any LXC machines in the config
    if "lxc" not in [settings.MACHINE_TYPE_PROVIDER_MAPPING[machine["type"]] for machine in config["machines"].values()]:
        logger.debug("Skipping LXC environment creation, no LXC machines in config")
        return

    # Check if we are on a supported OS
    if not check_for_supported_os("lxc"):
        logger.critical("Unable to create LXC environment on your machine, OS not supported")
        raise RuntimeError("OS not supported for provider LXC")

    # Check if all required packages have been installed
    if not check_for_installed_packages("lxc"):
        logger.critical("Not all required host packages seem to be installed, please fix this before proceeding")
        raise RuntimeError("Missing host packages")

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
        create_lxc_base_image_container()
        change_lxc_machine_status(settings.LXC_BASE_IMAGE_MACHINE_NAME, status="start")
        configure_lxc_base_machine()
        create_lxc_image_from_container(settings.LXC_BASE_IMAGE_MACHINE_NAME, alias=settings.LXC_BASE_IMAGE_ALIAS)
        destroy_lxc_machine(settings.LXC_BASE_IMAGE_MACHINE_NAME, wait=False)
    else:
        logger.debug("Base image {} found".format(settings.LXC_BASE_IMAGE_ALIAS))


def cleanup_vnet_lxc_environment():
    """
    Cleans up specific VNet LXC configuration
    No environments should be active when calling this function
    """
    request_confirmation(message="Cleanup will delete the VNet LXC configurations, such as profile and storage pools")
    logger.info("Cleaning up VNet LXC configuration")
    delete_vnet_lxc_profile(settings.LXC_VNET_PROFILE)
    delete_lxc_storage_pool(settings.LXC_STORAGE_POOL_NAME)


def configure_lxc_base_machine():
    """
    Configure the LXC base machine to get a fully functional VNet base machine which we can make an image from
    :raises RuntimeError: If the base machine is started without networking/dns
    """
    logger.info("Configuring LXC base machine {}, this might take a while".format(settings.LXC_BASE_IMAGE_MACHINE_NAME))
    client = get_lxd_client()
    machine = client.containers.get(settings.LXC_BASE_IMAGE_MACHINE_NAME)

    def execute_and_log(command: str, **kwargs) -> Tuple[int, AnyStr, AnyStr]:
        result = machine.execute(shlex.split(command), **kwargs)
        logger.debug(result)
        return result

    # Check for DNS
    logger.debug("Checking for DNS connectivity")
    dns = False
    for _ in range(0, settings.LXC_MAX_STATUS_WAIT_ATTEMPTS):
        if execute_and_log("host -t A google.com")[0] == 0:
            dns = True
            break
        # No DNS connectivity (yet), try again
        sleep(2)
    if not dns:
        # Shutdown base if DNS check fails
        logger.debug("Stopping base machine")
        machine.stop()
        raise RuntimeError("Base machine started without working DNS, unable to continue")

    # Set the FRR routing source and key
    execute_and_log("bash -c 'curl -s https://deb.frrouting.org/frr/keys.asc | apt-key add'")
    execute_and_log(
        "bash -c 'echo deb https://deb.frrouting.org/frr $(lsb_release -s -c) {} | tee -a /etc/apt/sources.list.d/frr.list'".format(
            settings.FRR_RELEASE
        )
    )

    # Update and install packages
    execute_and_log("apt-get update")
    execute_and_log(
        "apt-get upgrade -y -o Dpkg::Options::='--force-confdef' -o Dpkg::Options::='--force-confold'",
        environment={"DEBIAN_FRONTEND": "noninteractive"},
    )
    execute_and_log(
        "apt-get install -y -o Dpkg::Options::='--force-confdef' -o Dpkg::Options::='--force-confold' {}".format(
            " ".join(settings["PROVIDERS"]["lxc"]["guest_packages"])
        ),
        environment={"DEBIAN_FRONTEND": "noninteractive"},
    )

    # Disable radvd by default
    execute_and_log("systemctl disable radvd")
    # Disable cloud init messing with our networking
    execute_and_log("bash -c 'echo network: {config: disabled} > /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg'")
    # Set the default VTYSH_PAGER
    execute_and_log("bash -c 'export VTYSH_PAGER=more >> ~/.bashrc'")
    # Make all files in the FRR dir owned by the frr user
    execute_and_log(
        "bash -c 'echo -e \"#!/bin/bash\nchown -R frr:frr /etc/frr\nsystemctl restart frr\" > /etc/rc.local; chmod +x /etc/rc.local'"
    )
    # All done, stop the container
    machine.stop(wait=True)
    logger.debug("LXC base machine {} successfully configured".format(settings.LXC_BASE_IMAGE_MACHINE_NAME))
