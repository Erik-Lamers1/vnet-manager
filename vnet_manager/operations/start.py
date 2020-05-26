from pylxd.exceptions import NotFound
from logging import getLogger
from sys import modules

from vnet_manager.conf import settings
from vnet_manager.providers.lxc import get_lxd_client
from vnet_manager.operations.status import wait_for_lxc_machine_status

logger = getLogger(__name__)


def start_machines(config, machines=None):
    """
    Starts the provider start procedure for the passed machine names
    :param dict config: The config provided by get_config()
    :param list machines: A list of machine names to start, if None all will be started
    """
    machines = machines if machines else config["machines"].keys()
    for machine in machines:
        provider = settings.MACHINE_TYPE_PROVIDER_MAPPING[config["machines"][machine]["type"]]
        logger.info("Starting machine {} with provider {}".format(machine, provider))
        getattr(modules[__name__], "start_{}_machine".format(provider))(machine)


def start_lxc_machine(machine):
    """
    Start a LXC machine
    :param str machine: The name of the machine to start
    """
    client = get_lxd_client()
    try:
        machine = client.containers.get(machine)
    except NotFound:
        logger.error("Tried to start LXC container {}, but it doesn't exist!")
    machine.start()
    try:
        wait_for_lxc_machine_status(machine, "Running")
        logger.debug("LXC container {} is running".format(machine.name))
    except TimeoutError:
        logger.error("Unable to start LXC container {}, got timeout after issuing start command".format(machine.name))
