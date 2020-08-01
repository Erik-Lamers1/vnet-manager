from logging import getLogger
from pylxd.exceptions import NotFound

from vnet_manager.providers.lxc import get_lxd_client
from vnet_manager.operations.machine import change_lxc_machine_status

logger = getLogger(__name__)


def check_if_lxc_image_exists(image, by_alias=True):
    """
    Check if an LXC image exists
    :param str image: The image fingerprint or alias
    :param bool by_alias: Search by image alias instead of fingerprint
    :return: bool: True if the image exists false otherwise
    """
    logger.debug("Checking for the existence of LXC image {}".format(image))
    client = get_lxd_client()
    if by_alias:
        try:
            client.images.get_by_alias(image)
            return True
        except NotFound:
            return False
    # Search by fingerprint
    return client.images.exists(image)


def create_lxc_image_from_container(container, alias=None, description=None):
    """
    Create a LXC image from a container
    :param str container: The container to create the image from
    :param str alias: Creates an alias for the image
    :param str description: A description for the image alias
    """
    # Stop it first
    change_lxc_machine_status(container, status="stop")

    # Create the image
    logger.info("Creating image from LXC container {}".format(container))
    client = get_lxd_client()
    container = client.containers.get(container)
    img = container.publish(wait=True)
    logger.info("Image {} created successfully".format(img.fingerprint))

    # Create the alias if requested
    if alias:
        logger.info("Adding alias {} to newly created image".format(alias))
        img.add_alias(alias, description)


def destroy_lxc_image(image, by_alias=True):
    """
    Destroy a LXC image
    :param str image: The fingerprint or alias of the image to destroy
    :param bool by_alias: Search by alias instead of fingerprint
    """
    # Check if it even exists
    if not check_if_lxc_image_exists(image, by_alias=by_alias):
        logger.warning("Tried to destroy LXC image {}, but it is already gone".format(image))
        return
    # Delete it
    logger.info("Deleting LXC image {}".format(image))
    client = get_lxd_client()
    image = client.images.get_by_alias(image) if by_alias else client.images.get(image)
    image.delete()
