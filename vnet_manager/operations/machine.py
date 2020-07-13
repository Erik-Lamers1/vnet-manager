from pylxd.exceptions import NotFound, LXDAPIException
from sys import modules
from logging import getLogger
from tabulate import tabulate
from time import sleep

from vnet_manager.conf import settings
from vnet_manager.operations.files import place_lxc_interface_configuration_on_container
from vnet_manager.providers.lxc import get_lxd_client
from vnet_manager.utils.user import request_confirmation

logger = getLogger(__name__)


def show_status(config):
    """
    Print a table with the current machine statuses
    :param dict config: The config provided by vnet_manager.config.get_config()
    """
    logger.info("Listing VNet machine statuses")
    header = ["Name", "Status", "Provider"]
    statuses = []
    for name, info in config["machines"].items():
        provider = settings.MACHINE_TYPE_PROVIDER_MAPPING[info["type"]]
        # Call the relevant provider get_%s_machine_status function
        statuses.append(getattr(modules[__name__], "get_{}_machine_status".format(provider))(name))
    print(tabulate(statuses, headers=header, tablefmt="pretty"))


def check_if_lxc_machine_exists(machine):
    """
    Checks if an LXC machine exists
    :param str machine: The machine/container to check for
    :return: bool: True if it exists, false otherwise
    """
    return get_lxd_client().containers.exists(machine)


def get_lxc_machine_status(name):
    """
    Gets the LXC machine state and returns a list
    :param name: str: The name of the machine
    :return: list: [name, state, provider]
    """
    # TODO: Let's not return a list here, simply the status
    client = get_lxd_client()
    try:
        status = client.containers.get(name).status
    except NotFound:
        status = "NA"
    return [name, status, "LXC"]


def wait_for_lxc_machine_status(container, status):
    """
    Waits for a LXC machine to converge to the requested status
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
        # Container not in desired state yet, wait and try again
        sleep_time = settings.LXC_STATUS_WAIT_SLEEP + \
                     (i * (settings.LXC_STATUS_WAIT_SLEEP * settings.LCX_STATUS_BACKOFF_MULTIPLIER))
        logger.info(
            "Container {} not yet in {} status, waiting for {} seconds".format(container.name, status, sleep_time)
        )
        sleep(sleep_time)
    raise TimeoutError("Wait time for container {} to converge to {} status expired, giving up".format(container.name, status))


def change_machine_status(config, status="stop", machines=None):
    """
    Change the status of the passed machines to the requested state
    :param dict config: The config provided by get_config()
    :param str status: The status to change the machine to
    :param list machines: A list of machine names to stop/start, if None all will be changed
    """
    # Check for valid status change
    if status not in settings.VALID_STATUSES:
        raise NotImplementedError("Requested machine status change {} unknown".format(status))

    # Get all the machines from the config if not already provided
    machines = machines if machines else config["machines"].keys()

    # For each machine get the provider and execute the relevant status change function
    for machine in machines:
        # First check if the machine exists
        if machine not in config["machines"]:
            logger.error("Tried to {} machine {}, but there is no config entry for it, skipping...".format(status, machine))
            continue
        # Get the provider
        provider = settings.MACHINE_TYPE_PROVIDER_MAPPING[config["machines"][machine]["type"]]
        # Call the provider change_status function
        logger.info("{} machine {} with provider {}".format("Starting" if status == "start" else "Stopping", machine, provider))
        getattr(modules[__name__], "change_{}_machine_status".format(provider))(machine, status=status)


def change_lxc_machine_status(machine, status="stop"):
    """
    Start a LXC machine
    :param str machine: The name of the machine to change the status of
    :param str status: The status to change the LXC machine to
    """
    client = get_lxd_client()
    try:
        machine = client.containers.get(machine)
    except NotFound:
        logger.error("Tried to change machine status of LXC container {}, but it doesn't exist!".format(machine))
        return
    # Change the status
    if status == "stop":
        machine.stop()
    elif status == "start":
        try:
            # On start we wait, as we might catch invalid configs
            machine.start(wait=True)
        except LXDAPIException as e:
            logger.error("Unable to start LXC container {}, got error: {}".format(machine.name, e))
            return
    # Take a short nap after issuing the start/stop command, so we might pass the first status check
    sleep(1)
    try:
        required_state = "Stopped" if status == "stop" else "Running"
        wait_for_lxc_machine_status(machine, required_state)
        logger.debug("LXC container {} is {}".format(machine.name, machine.state().status))
    except TimeoutError:
        logger.error("Unable to change LXC status container {}, got timeout after issuing {} command".format(machine.name, status))


def create_machines(config, machines=None):
    """
    Meta function to call the other machine creation functions per provider
    :param dict config: The config generated by get_config()
    :param list machines: A list of machine to create, defaults to all machines in the config
    """
    # Get all the machines from the config if not already provided
    machines = machines if machines else config["machines"].keys()
    create_lxc_machines_from_base_image(config, machines)


def create_lxc_machines_from_base_image(config, containers):
    """
    Create LXC machines from the base image specified in the settings
    :param dict config: The config generated by get_config()
    :param list containers: A list of machines to create
    """
    containers_to_create = []
    containers_already_created = False

    # Get all the LXC machines to create
    for container in containers:
        # Check if the requested machine name is present in the config
        if container not in config["machines"]:
            logger.error(
                "Tried to get provider for container {}, but the container was not found in the config, skipping".format(container)
            )
        # Quick check if the machine already exists
        elif check_if_lxc_machine_exists(container):
            logger.error("A LXC container with the name {} already exists, skipping".format(container))
            containers_already_created = True
        # Check if LXC is the provider
        elif settings.MACHINE_TYPE_PROVIDER_MAPPING[config["machines"][container]["type"]].lower() == "lxc":
            logger.debug("Selecting LXC machine {} for creation".format(container))
            containers_to_create.append(container)
        else:
            logger.debug("Machine {} is not provided by LXC, skipping LXC container creation".format(container))

    # Create it
    client = get_lxd_client()
    for container in containers_to_create:
        logger.debug("Generating LXC config for container {}".format(container))
        # Interface config
        # First add eth0 (default), which does nothing
        device_config = {"eth0": {"type": "none"}}
        # Then for each interface in the config add the configuration for that interface to the interfaces_config dict
        for inet_name, inet_config in config["machines"][container]["interfaces"].items():
            device_config[inet_name] = {
                "name": inet_name,  # The name of the interface inside the instance
                "host_name": "{}-{}".format(container, inet_name),  # The name of the interface inside the host
                "parent": "{}{}".format(settings.VNET_BRIDGE_NAME, inet_config["bridge"]),  # The name of the host device
                "type": "nic",
                "nictype": "bridged",
                "hwaddr": inet_config["mac"],
            }
        container_config = {
            "name": container,
            "source": {"alias": settings.LXC_BASE_IMAGE_ALIAS, "type": "image"},
            "ephemeral": False,
            "config": {"user.network-config": "disabled"},
            "devices": device_config,
            "profiles": [settings.LXC_VNET_PROFILE],
        }
        logger.info("Creating LXC container {}".format(container))
        # TODO: Make this nicer by not waiting here but doing the configuration after we've created all containers
        client.containers.create(container_config, wait=True)
        place_lxc_interface_configuration_on_container(config, container)

    # Check with the user if it is okay to overwrite config files
    if containers_already_created:
        request_confirmation(
            message="Some containers already existed, the next operation will overwrite network, "
            "host and user config files on those containers",
        )


def destroy_machines(config, machines=None):
    """
    Destroy's the passed machines
    :param dict config: The config generated by get config
    :param list machines: The machines to destroy, defaults to all machines in the config
    :param bool force: Don't ask the user questions, just do it
    """
    # Get all the machines from the config if not already provided
    machines = machines if machines else config["machines"].keys()

    # Ask the user if he is sure
    request_confirmation(
        message="Requesting confirmation of deletion for the following machines: {}".format(", ".join(machines)),
        prompt="This operation cannot be undone. Are you sure?! ",
    )

    for machine in machines:
        # First check if the machine exists
        if machine not in config["machines"]:
            logger.error("Tried to get the config for machine {}, but there is no config entry for this machine, skipping".format(machine))
            continue
        # Get the provider
        provider = settings.MACHINE_TYPE_PROVIDER_MAPPING[config["machines"][machine]["type"]]
        # Call the provider destroy function
        getattr(modules[__name__], "destroy_{}_machine".format(provider))(machine)


def destroy_lxc_machine(machine, wait=False):
    """
    Deletes an LXC machine
    :param str machine: The name of the machine to delete
    :param bool wait: Wait for the deletion to be complete before returning
    :return:
    """
    client = get_lxd_client()
    try:
        container = client.containers.get(machine)
    except NotFound:
        logger.warning("Tried to delete LXC machine {}, but it does not exist. Maybe it was already deleted?".format(machine))
        return
    # Check if the container is still running
    if container.status.lower() == "running":
        logger.info("Stopping LXC container {}".format(machine))
        container.stop(wait=True)
    logger.info("Deleting LXC container {}".format(machine))
    container.delete(wait=wait)


def create_lxc_base_image_container(config):
    """
    Creates the LXC base image container
    :param dict config: The config generated by get_config()
    :raises RuntimeError: if any issues are encountered during creation
    """
    # Check if the base image machine already exists and destroy it
    if check_if_lxc_machine_exists(settings.LXC_BASE_IMAGE_MACHINE_NAME):
        logger.warning("LXC base image machine already exists")
        request_confirmation(message="Recreating it will destroy any local changes", prompt="Recreate the LXC base image machine? ")
        destroy_lxc_machine(settings.LXC_BASE_IMAGE_MACHINE_NAME, wait=True)

    # Now create the base image machine
    client = get_lxd_client()

    machine_config = {
        "name": settings.LXC_BASE_IMAGE_MACHINE_NAME,
        "architecture": "x86_64",
        "profiles": [settings.LXC_VNET_PROFILE],
        "ephemeral": False,
        "config": {},
        "devices": {
            "eth0": {
                "name": "eth0",
                "parent": "lxdbr0",
                "type": "nic",
                "nictype": "bridged",
                "host_name": "{}-eth0".format(settings.LXC_BASE_IMAGE_MACHINE_NAME),
            }
        },
        "source": {
            "type": "image",
            "protocol": str(config["providers"]["lxc"]["base_image"]["protocol"]),
            "server": config["providers"]["lxc"]["base_image"]["server"],
            "alias": str(config["providers"]["lxc"]["base_image"]["os"]),
        },
    }
    logger.info("Creating LXC base image container")
    client.containers.create(machine_config, wait=True)


def enable_type_specific_machine_configuration(config):
    """
    Call type and provider specific machine configuration functions based on the settings
    :param dict config: The config generated by get_config()
    """
    for machine_name, machine_data in config["machines"].items():
        for func in settings.MACHINE_TYPE_CONFIG_FUNCTION_MAPPING[machine_data["type"]]:
            getattr(modules[__name__], func)(machine_name)


def configure_lxc_ip_forwarding(container_name):
    """
    Configure a LXC machine to enable IP forwarding
    :param str container_name: The name of the container to enable IP forwarding on
    """
    try:
        container = get_lxd_client().containers.get(container_name)
    except NotFound:
        logger.warning("Tried to enable IP forwarding on LXC container {} but it does not exists".format(container_name))
        return

    logger.info("Enabling IP forwarding on LXC container {}".format(container_name))
    container.files.put("/etc/sysctl.d/20-net.ipv4.ip_forward.conf", "net.ipv4.ip_forward=1\n")
    container.files.put("/etc/sysctl.d/20-net.ipv6.conf.all.forwarding.conf", "net.ipv6.conf.all.forwarding=1\n")
