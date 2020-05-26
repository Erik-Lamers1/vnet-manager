from pylxd.exceptions import NotFound
from sys import modules
from logging import getLogger
from tabulate import tabulate
from time import sleep

from vnet_manager.conf import settings
from vnet_manager.providers.lxc import get_lxd_client

logger = getLogger(__name__)


def show_status(config):
    """
    Print a table with the current machine statuses
    :param dict config: The config provided by vnet_manager.config.get_config()
    """
    logger.info("Listing machine statuses")
    header = ["Name", "Status", "Provider"]
    statuses = []
    for name, info in config["machines"].items():
        provider = settings.MACHINE_TYPE_PROVIDER_MAPPING[info["type"]]
        # Call the relevant provider get_%s_machine_status function
        statuses.append(getattr(modules[__name__], "get_{}_machine_status".format(provider))(name, info))
    print(tabulate(statuses, headers=header, tablefmt="pretty"))


def get_lxc_machine_status(name, _):
    """
    Gets the LXC machine state and returns a list
    :param name: str: The name of the machine
    :return: list: [name, state, provider]
    """
    client = get_lxd_client()
    try:
        status = client.containers.get(name).status
    except NotFound:
        status = "NA"
    return [name, status, "LXC"]


def wait_for_lxc_machine_status(container, status):
    """
    Waits for a LXC machine to start up
    :param pylxd.client.Client.container() container: The container to wait for
    :param str status: The status to wait for
    :raise TimeoutError if wait time expires
    """
    logger.debug("Waiting for LXC container {} to get a {} status".format(container.name, status))
    for i in range(1, settings.LXC_MAX_STATUS_WAIT_ATTEMPTS):
        # Actually ask for the container.state().status, because container.status is a static value
        if container.state().status.lower() == status.lower():
            logger.debug("Container successfully converged to {} status".format(status))
            return
        else:
            logger.info(
                "Container {} not yet in {} status, waiting for {} seconds".format(container.name, status, settings.LXC_STATUS_WAIT_SLEEP)
            )
            sleep(settings.LXC_STATUS_WAIT_SLEEP)
    raise TimeoutError("Wait time for container {} to converge to {} status expired, giving up".format(container.name, status))
