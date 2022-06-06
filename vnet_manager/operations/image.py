from logging import getLogger
from pylxd.exceptions import NotFound

from vnet_manager.providers.lxc import get_lxd_client
from vnet_manager.operations.machine import change_lxc_machine_status

logger = getLogger(__name__)


def check_if_lxc_image_exists(image: str, by_alias: bool = True) -> bool:
    """
    Check if an LXC image exists
    :param str image: The image fingerprint or alias
    :param bool by_alias: Search by image alias instead of fingerprint
    :return: bool: True if the image exists false otherwise
    """
    logger.debug(f"Checking for the existence of LXC image {image}")
    client = get_lxd_client()
    if by_alias:
        try:
            client.images.get_by_alias(image)
            return True
        except NotFound:
            return False
    # Search by fingerprint
    return client.images.exists(image)


def create_lxc_image_from_container(container: str, alias: str = None, description: str = None):
    """
    Create a LXC image from a container
    :param str container: The container to create the image from
    :param str alias: Creates an alias for the image
    :param str description: A description for the image alias
    """
    # Stop it first
    change_lxc_machine_status(container, status="stop")

    # Create the image
    logger.info(f"Creating image from LXC container {container}")
    client = get_lxd_client()
    container = client.containers.get(container)
    img = container.publish(wait=True)
    logger.info(f"Image {img.fingerprint} created successfully")

    # Create the alias if requested
    if alias:
        logger.info(f"Adding alias {alias} to newly created image")
        img.add_alias(alias, description)


def destroy_lxc_image(image: str, by_alias: bool = True, wait: bool = False):
    """
    Destroy a LXC image
    :param str image: The fingerprint or alias of the image to destroy
    :param bool by_alias: Search by alias instead of fingerprint
    :param bool wait: Whether to wait for deletion to be completed or return after the delete call
    """
    # Check if it even exists
    if not check_if_lxc_image_exists(image, by_alias=by_alias):
        logger.warning(f"Tried to destroy LXC image {image}, but it is already gone")
        return
    # Delete it
    logger.info(f"Deleting LXC image {image}")
    client = get_lxd_client()
    image = client.images.get_by_alias(image) if by_alias else client.images.get(image)
    image.delete(wait=wait)
