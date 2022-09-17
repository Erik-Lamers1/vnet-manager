import sys
from logging import getLogger
from pylxd import client
from pylxd.exceptions import ClientConnectionFailed

logger = getLogger(__name__)


def get_lxd_client(**kwargs) -> client.Client:
    """
    Get an LXC client.Client() with the passed parameters
    :return: pylxd.client.Client()
    """
    try:
        return client.Client(**kwargs)
    except ClientConnectionFailed as e:
        logger.error(f"Error while connecting to LXD: {e}")
        logger.critical("Unable to talk to LXD API, crashing out of program")
        sys.exit(1)
