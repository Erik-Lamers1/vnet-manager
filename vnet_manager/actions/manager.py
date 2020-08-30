from logging import getLogger
from os import EX_OK, EX_USAGE

from vnet_manager.conf import settings
from vnet_manager.config.config import get_config
from vnet_manager.config.validate import ValidateConfig
from vnet_manager.utils.version import show_version
from vnet_manager.utils.user import request_confirmation, generate_bash_completion_script
from vnet_manager.utils.files import write_file_to_disk
from vnet_manager.environment.lxc import ensure_vnet_lxc_environment, cleanup_vnet_lxc_environment
from vnet_manager.operations.image import destroy_lxc_image
from vnet_manager.operations.files import put_files_on_machine, generate_vnet_hosts_file, place_vnet_hosts_file_on_machines
from vnet_manager.actions.help import display_help_for_action
from vnet_manager.operations.machine import (
    show_status,
    change_machine_status,
    create_machines,
    destroy_machines,
    enable_type_specific_machine_configuration,
)
from vnet_manager.operations.interface import (
    bring_up_vnet_interfaces,
    bring_down_vnet_interfaces,
    delete_vnet_interfaces,
    show_vnet_interface_status,
    show_vnet_veth_interface_status,
)

logger = getLogger(__name__)


def action_manager(action, config, machines=None, sniffer=False, base_image=False):
    # pylint: disable=too-many-branches, too-many-statements
    # TODO: Refactor, if-statements, branches
    # Maybe make this into a class?
    """
    Initiate an action
    :param str action: The action to preform
    :param str config: The path to the user config file, or literal string 'help' for docs
    :param list machines: The specific container to execute actions on
    :param bool sniffer: Start a sniffer on the VNet interfaces on start
    :param bool base_image: Destroy the image image instead of the machines
    :return int: exit_code
    """
    # Check for valid action
    if action not in settings.VALID_ACTIONS:
        raise NotImplementedError("{} is not a valid action".format(action))

    # These actions do not require the config
    if action == "version":
        show_version()
        return EX_OK
    if config.lower() == "help":
        display_help_for_action(action)
        return EX_OK
    if action == "bash-completion":
        bash_script_content = generate_bash_completion_script()
        write_file_to_disk(settings.VNET_BASH_COMPLETION_PATH, bash_script_content)
        logger.info("Bash completion generated and placed. Use ' . /etc/bash_completion' to load in this terminal")
        return EX_OK
    if action == "clean":
        cleanup_vnet_lxc_environment()
        return EX_OK

    logger.info("Initiating {} action".format(action))
    # For these actions we need the config
    config = get_config(config)
    # Validate the config
    validator = ValidateConfig(config)
    validator.validate()
    if validator.config_validation_successful:
        logger.debug("Config successfully validated")
    else:
        logger.critical("The config seems to have unrecoverable issues, please fix them before proceeding")
        return EX_USAGE
    # Use the updated values from the config validator
    config = validator.updated_config

    if action == "list":
        show_status(config)
        show_vnet_interface_status(config)
        if "veths" in config:
            show_vnet_veth_interface_status(config)
    elif action == "start":
        bring_up_vnet_interfaces(config, sniffer=sniffer)
        change_machine_status(config, machines=machines, status="start")
    elif action == "stop":
        change_machine_status(config, machines=machines, status="stop")
        # If specific machines are specified, we don't want to mess with the interfaces
        if machines:
            logger.warning("Not bringing down VNet interfaces as we are only stopping specific machines, this may leave lingering sniffers")
        else:
            bring_down_vnet_interfaces(config)
    elif action == "create":
        # Make sure the provider environments are correct
        ensure_vnet_lxc_environment(config)
        # Make the machines
        create_machines(config, machines=machines)
        # Put user requested file on the machines
        put_files_on_machine(config)
        # Put /etc/hosts on the machines
        generate_vnet_hosts_file(config)
        place_vnet_hosts_file_on_machines(config)
        # Configure type specific stuff
        enable_type_specific_machine_configuration(config)
    elif action == "destroy":
        if base_image:
            request_confirmation(prompt="Are you sure you want to delete the VNet base images (y/n)? ")
            destroy_lxc_image(settings.LXC_BASE_IMAGE_ALIAS, by_alias=True)
        else:
            destroy_machines(config, machines=machines)
            # If specific machines are specified, we don't want to mess with the interfaces
            if machines:
                logger.warning(
                    "Not deleting VNet interfaces as we are only destroying specific machines, this may leave lingering sniffers"
                )
            else:
                delete_vnet_interfaces(config)

    # Finally return all OK
    return EX_OK
