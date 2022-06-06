from sys import modules
from logging import getLogger
from time import sleep
from typing import List
from tabulate import tabulate
from yaml import safe_dump
from pylxd.exceptions import NotFound, LXDAPIException

from vnet_manager.conf import settings
from vnet_manager.operations.files import write_file_to_lxc_container
from vnet_manager.providers.lxc import get_lxd_client
from vnet_manager.utils.user import request_confirmation

logger = getLogger(__name__)


def show_status(config: dict):
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
        statuses.append(getattr(modules[__name__], f"get_{provider}_machine_status")(name))
    print(tabulate(statuses, headers=header, tablefmt="pretty"))


def check_if_lxc_machine_exists(machine: str) -> bool:
    """
    Checks if an LXC machine exists
    :param str machine: The machine/container to check for
    :return: bool: True if it exists, false otherwise
    """
    return get_lxd_client().containers.exists(machine)


def get_lxc_machine_status(name: str) -> List[str]:
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


# NOTE: Container should be `container: pylxd.models.container.Container`, but this breaks testing atm.
def wait_for_lxc_machine_status(container, status: str):
    """
    Waits for a LXC machine to converge to the requested status
    :param pylxd.client.Client.container() container: The container to wait for
    :param str status: The status to wait for
    :raise TimeoutError if wait time expires
    """
    logger.debug(f"Waiting for LXC container {container.name} to get a {status} status")
    for i in range(1, settings.LXC_MAX_STATUS_WAIT_ATTEMPTS):
        # Actually ask for the container.state().status, because container.status is a static value
        if container.state().status.lower() == status.lower():
            logger.debug(f"Container successfully converged to {status} status")
            return
        # Container not in desired state yet, wait and try again
        sleep_time = i * (settings.LXC_STATUS_WAIT_SLEEP * settings.LXC_STATUS_BACKOFF_MULTIPLIER)
        logger.info(f"Container {container.name} not yet in {status} status, waiting for {sleep_time} seconds")
        sleep(sleep_time)
    raise TimeoutError(f"Wait time for container {container.name} to converge to {status} status expired, giving up")


def change_machine_status(config: dict, status: str = "stop", machines: List[str] = None):
    """
    Change the status of the passed machines to the requested state
    :param dict config: The config provided by get_config()
    :param str status: The status to change the machine to
    :param list machines: A list of machine names to stop/start, if None all will be changed
    """
    # Check for valid status change
    if status not in settings.VALID_STATUSES:
        raise NotImplementedError(f"Requested machine status change {status} unknown")

    # Get all the machines from the config if not already provided
    machines = machines if machines else config["machines"].keys()

    # For each machine get the provider and execute the relevant status change function
    for machine in machines:
        # First check if the machine exists
        if machine not in config["machines"]:
            logger.error(f"Tried to {status} machine {machine}, but there is no config entry for it, skipping...")
            continue
        # Get the provider
        provider = settings.MACHINE_TYPE_PROVIDER_MAPPING[config["machines"][machine]["type"]]
        # Call the provider change_status function
        logger.info(f"{'Starting' if status == 'start' else 'Stopping'} machine {machine} with provider {provider}")
        getattr(modules[__name__], f"change_{provider}_machine_status")(machine, status=status)


def change_lxc_machine_status(machine: str, status: str = "stop"):
    """
    Start a LXC machine
    :param str machine: The name of the machine to change the status of
    :param str status: The status to change the LXC machine to
    """
    client = get_lxd_client()
    try:
        machine = client.containers.get(machine)
    except NotFound:
        logger.error(f"Tried to change machine status of LXC container {machine}, but it doesn't exist!")
        return
    # Change the status
    if status == "stop":
        machine.stop()
    elif status == "start":
        try:
            # On start we wait, as we might catch invalid configs
            machine.start(wait=True)
        except LXDAPIException as e:
            logger.error(f"Unable to start LXC container {machine.name}, got error: {e}")
            return
    # Take a short nap after issuing the start/stop command, so we might pass the first status check
    sleep(1)
    try:
        required_state = "Stopped" if status == "stop" else "Running"
        wait_for_lxc_machine_status(machine, required_state)
        logger.debug(f"LXC container {machine.name} is {machine.state().status}")
    except TimeoutError:
        logger.error(f"Unable to change LXC status container {machine.name}, got timeout after issuing {status} command")


def create_machines(config: dict, machines: List[str] = None):
    """
    Meta function to call the other machine creation functions per provider
    :param dict config: The config generated by get_config()
    :param list machines: A list of machine to create, defaults to all machines in the config
    """
    # Get all the machines from the config if not already provided
    machines = machines if machines else config["machines"].keys()
    create_lxc_machines_from_base_image(config, machines)


def create_lxc_machines_from_base_image(config: dict, containers: List[str]):
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
            logger.error(f"Tried to get provider for container {container}, but the container was not found in the config, skipping")
        # Quick check if the machine already exists
        elif check_if_lxc_machine_exists(container):
            logger.error(f"A LXC container with the name {container} already exists, skipping")
            containers_already_created = True
        # Check if LXC is the provider
        elif settings.MACHINE_TYPE_PROVIDER_MAPPING[config["machines"][container]["type"]].lower() == "lxc":
            logger.debug(f"Selecting LXC machine {container} for creation")
            containers_to_create.append(container)
        else:
            logger.debug(f"Machine {container} is not provided by LXC, skipping LXC container creation")

    # Create it
    client = get_lxd_client()
    for container in containers_to_create:
        logger.debug(f"Generating LXC config for container {container}")
        # Interface config
        # First add eth0 (default), which does nothing
        device_config = {"eth0": {"type": "none"}}
        # Then for each interface in the config add the configuration for that interface to the interfaces_config dict
        for inet_name, inet_config in config["machines"][container]["interfaces"].items():
            device_config[inet_name] = {
                "name": inet_name,  # The name of the interface inside the instance
                "host_name": f"{container}-{inet_name}",  # The name of the interface inside the host
                "parent": f"{settings.VNET_BRIDGE_NAME}{inet_config['bridge']}",  # The name of the host device
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
        logger.info(f"Creating LXC container {container}")
        # TODO: Make this nicer by not waiting here but doing the configuration after we've created all containers
        client.containers.create(container_config, wait=True)
        place_lxc_interface_configuration_on_container(config, container)

    # Check with the user if it is okay to overwrite config files
    if containers_already_created:
        request_confirmation(
            message="Some containers already existed, the next operation will overwrite network, "
            "host and user config files on those containers",
        )


def destroy_machines(config: dict, machines: List[str] = None):
    """
    Destroy's the passed machines
    :param dict config: The config generated by get config
    :param list machines: The machines to destroy, defaults to all machines in the config
    """
    # Get all the machines from the config if not already provided
    machines = machines if machines else config["machines"].keys()

    # Ask the user if he is sure
    request_confirmation(
        message=f"Requesting confirmation of deletion for the following machines: {', '.join(machines)}",
        prompt="This operation cannot be undone. Are you sure?! (yes/no) ",
    )

    for machine in machines:
        # First check if the machine exists
        if machine not in config["machines"]:
            logger.error(f"Tried to get the config for machine {machine}, but there is no config entry for this machine, skipping")
            continue
        # Get the provider
        provider = settings.MACHINE_TYPE_PROVIDER_MAPPING[config["machines"][machine]["type"]]
        # Call the provider destroy function
        getattr(modules[__name__], f"destroy_{provider}_machine")(machine)


def destroy_lxc_machine(machine: str, wait: bool = False):
    """
    Deletes an LXC machine
    :param str machine: The name of the machine to delete
    :param bool wait: Wait for the deletion to be complete before returning
    """
    client = get_lxd_client()
    try:
        container = client.containers.get(machine)
    except NotFound:
        logger.warning(f"Tried to delete LXC machine {machine}, but it does not exist. Maybe it was already deleted?")
        return
    # Check if the container is still running
    if container.status.lower() == "running":
        logger.info(f"Stopping LXC container {machine}")
        container.stop(wait=True)
    logger.info(f"Deleting LXC container {machine}")
    container.delete(wait=wait)


def create_lxc_base_image_container():
    """
    Creates the LXC base image container
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
                "host_name": f"{settings.LXC_BASE_IMAGE_MACHINE_NAME}-eth0",
            }
        },
        "source": {
            "type": "image",
            "protocol": str(settings["PROVIDERS"]["lxc"]["base_image"]["protocol"]),
            "server": settings["PROVIDERS"]["lxc"]["base_image"]["server"],
            "alias": str(settings["PROVIDERS"]["lxc"]["base_image"]["os"]),
        },
    }
    logger.info("Creating LXC base image container")
    client.containers.create(machine_config, wait=True)


def enable_type_specific_machine_configuration(config: dict):
    """
    Call type and provider specific machine configuration functions based on the settings
    :param dict config: The config generated by get_config()
    """
    for machine_name, machine_data in config["machines"].items():
        for func in settings.MACHINE_TYPE_CONFIG_FUNCTION_MAPPING[machine_data["type"]]:
            getattr(modules[__name__], func)(machine_name)


def enable_lxc_ip_forwarding(container_name: str):
    """
    Enables LXC IP forwarding for a machine
    (Wrapper function for configure_lxc_ip_forwarding)
    :param container_name: str The name of the container
    """
    configure_lxc_ip_forwarding(container_name, enable=True)


def disable_lxc_ip_forwarding(container_name: str):
    """
    Disables LXC IP forwarding for a machine
    (Wrapper function for configure_lxc_ip_forwarding)
    :param container_name: str The name of the container
    """
    configure_lxc_ip_forwarding(container_name, enable=False)


def configure_lxc_ip_forwarding(container_name: str, enable: bool = True):
    """
    Configure a LXC machine to enable IP forwarding
    :param str container_name: The name of the container to enable IP forwarding on
    :param bool enable: Whether to enable IP forwarding or disable it
    """
    value = 1 if enable else 0
    logger.info(f"{'Enabling' if enable else 'Disabling'} IP forwarding on LXC container {container_name}")
    write_file_to_lxc_container(container_name, "/etc/sysctl.d/20-net.ipv4.ip_forward.conf", f"net.ipv4.ip_forward={value}\n")
    write_file_to_lxc_container(
        container_name, "/etc/sysctl.d/20-net.ipv6.conf.all.forwarding.conf", f"net.ipv6.conf.all.forwarding={value}\n"
    )


def place_lxc_interface_configuration_on_container(config: dict, container: str):
    """
    Places the interfaces configuration on the LXC container
    :param dict config: The config generated by get_config()
    :param str container: The name of the container to place the interfaces configuration on
    """
    logger.debug(f"Generating network config for LXC container {container}")
    network_conf = generate_machine_netplan_config(config, container)
    logger.info(f"Placing network config on LXC container {container}")
    write_file_to_lxc_container(container, settings.VNET_NETPLAN_CONFIG_FILE_PATH, safe_dump(network_conf))


def generate_machine_netplan_config(config: dict, machine: str) -> dict:
    """
    Generates a Netplan config based on the machine configuration
    :param config: dict: The config generates by get_config()
    :param machine: str: The machine name to generate the netplan config for
    :return: dict: The netplan config
    """
    no_dhcp = {
        "dhcp4": "no",
        "dhcp6": "no",
    }
    machine_config = config.get("machines").get(machine)
    network_conf = {
        "network": {
            "version": 2,
            "renderer": "networkd",
            "ethernets": {},
        }
    }
    for int_name, int_data in machine_config["interfaces"].items():
        addresses = []
        if "ipv4" in int_data:
            addresses.append(int_data["ipv4"])
        if "ipv6" in int_data:
            addresses.append(int_data["ipv6"])
        network_conf["network"]["ethernets"][int_name] = {
            "match": {
                "macaddress": int_data["mac"],
            },
            "set-name": int_name,
            "addresses": addresses,
        }
        network_conf["network"]["ethernets"][int_name].update(no_dhcp)
        if "routes" in int_data:
            network_conf["network"]["ethernets"][int_name]["routes"] = int_data["routes"]
    if "vlans" in machine_config:
        network_conf["network"]["vlans"] = {}
        for vlan, vlan_data in machine_config["vlans"].items():
            network_conf["network"]["vlans"][vlan] = {"id": vlan_data["id"], "link": vlan_data["link"], "addresses": vlan_data["addresses"]}
            network_conf["network"]["vlans"][vlan].update(no_dhcp)
    if "bridges" in machine_config:
        network_conf["network"]["bridges"] = {}
        for br_name, br_data in machine_config["bridges"].items():
            addresses = []
            if "ipv4" in br_data:
                addresses.append(br_data["ipv4"])
            if "ipv6" in br_data:
                addresses.append(br_data["ipv6"])
            network_conf["network"]["bridges"][br_name] = {
                "interfaces": br_data["slaves"],
                "addresses": addresses,
            }
            network_conf["network"]["bridges"][br_name].update(no_dhcp)
    return network_conf
