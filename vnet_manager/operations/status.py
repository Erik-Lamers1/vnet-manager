from lxc import Container
from sys import modules
from logging import getLogger
from tabulate import tabulate

from vnet_manager.conf import settings

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
    machine = Container(name)
    state = machine.state if machine.defined else "NA"
    return [name, state, "LXC"]
