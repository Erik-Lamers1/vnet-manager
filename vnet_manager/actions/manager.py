from logging import getLogger
from os import EX_OK, EX_USAGE, EX_OSERR
from os.path import isdir
from typing import Optional, Tuple, List

import vnet_manager.operations.machine as machine_op
from vnet_manager.conf import settings
from vnet_manager.config.config import get_config
from vnet_manager.config.validate import ValidateConfig
from vnet_manager.utils.version import show_version
from vnet_manager.utils.user import request_confirmation, generate_bash_completion_script
from vnet_manager.utils.files import write_file_to_disk, get_yaml_files_from_disk_path
from vnet_manager.environment.lxc import ensure_vnet_lxc_environment, cleanup_vnet_lxc_environment
from vnet_manager.operations.image import destroy_lxc_image
from vnet_manager.operations.files import put_files_on_machine, generate_vnet_hosts_file, place_vnet_hosts_file_on_machines
from vnet_manager.operations.interface import (
    bring_up_vnet_interfaces,
    bring_down_vnet_interfaces,
    delete_vnet_interfaces,
    show_vnet_interface_status,
    show_vnet_veth_interface_status,
    kill_tcpdump_processes_on_vnet_interfaces,
)

logger = getLogger(__name__)


class ActionManager:
    """
    The VNet Action Manager class
    Use this class to initiate specific VNet action in a controlled manner
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        machines: Optional[List[str]] = None,
        sniffer: bool = False,
        base_image: bool = False,
        no_hosts: bool = False,
        purge: bool = False,
        pcap_dir: str = settings.VNET_SNIFFER_PCAP_DIR,
        provider: str = "lxc",
    ):
        """
        :param str config_path: The path to the config
        :param bool sniffer: Whether to enable sniffers on 'start'
        :param bool base_image: Whether to delete the base image on 'destroy'
        """
        self.config_path = config_path
        self.config = None
        self.sniffer = sniffer
        self.base_image = base_image
        self.no_hosts = no_hosts
        self.provider = provider
        self.machines = machines
        self.purge = purge
        self.pcap_dir = pcap_dir
        self._config_validated = False

    def execute(self, action: str) -> int:
        """
        Execute an action
        :param str action: The name of the action to execute
        :return: int: returncode of the action
        """
        # First do a sanity check on the action
        action_func = action.replace("-", "_")
        if not hasattr(self, f"preform_{action_func}_action"):
            logger.critical(f"{action} is not a valid action")
            return EX_USAGE
        if self.config_path and action not in ("connect", "list") and not self.parse_config():
            logger.critical("Config NOT OK, can't proceed")
            return EX_USAGE
        # Preform the action
        logger.info(f"Initiating {action} action")
        # Return the exit code provided by the execute function or exit EX_OK if no exit code is provided
        return getattr(self, f"preform_{action_func}_action")() or EX_OK

    def parse_config(self) -> bool:
        """
        Parses the user config
        Updates the config accordingly
        :return: bool: True if config parsing successful, False otherwise
        """
        self.config = get_config(self.config_path)
        # Config passed and required, validate it
        check_result, self.config = self.check_and_update_config()
        if not check_result:
            # Config NOT OK, quit execution and return usage code
            return False
        return True

    def check_and_update_config(self) -> Tuple[bool, dict]:
        """
        Validates the config passed to this instance.
        The validator can also fix some minor config issues, these are returned.
        :return: bool: True if config successfully validated, False otherwise / dict: The updated config
        """
        validator = ValidateConfig(self.config)
        validator.validate()
        if not validator.config_validation_successful:
            logger.error("The config seems to have unrecoverable issues, please fix them before proceeding")
            return False, {}
        # Everything okay
        logger.debug("Config validation successful")
        return True, validator.updated_config

    def preform_show_action(self):
        machine_op.show_status(self.config)
        show_vnet_interface_status(self.config)
        if "veths" in self.config:
            show_vnet_veth_interface_status(self.config)

    def preform_start_action(self):
        bring_up_vnet_interfaces(self.config, sniffer=self.sniffer, pcap_dir=self.pcap_dir)
        machine_op.change_machine_status(self.config, machines=self.machines, status="start")

    def preform_stop_action(self):
        machine_op.change_machine_status(self.config, machines=self.machines, status="stop")
        # If specific machines are specified, we don't want to mess with the interfaces
        if self.machines:
            logger.warning("Not bringing down VNet interfaces as we are only stopping specific machines, this may leave lingering sniffers")
        else:
            # Bring down VNet interfaces and check with user if we should kill any lingering sniffers
            if bring_down_vnet_interfaces(self.config):
                request_confirmation(
                    message="Lingering sniffers have been found for the VNet interfaces that have been brought down",
                    prompt="Kill lingering sniffers? (y/n) ",
                )
                kill_tcpdump_processes_on_vnet_interfaces(self.config)

    def preform_connect_action(self):
        # Make the provider exists
        if self.provider not in settings.PROVIDERS.keys():
            logger.error(f"Provider {self.provider} not supported")
            return EX_USAGE
        # Connect to it
        getattr(machine_op, f"connect_to_{self.provider}_machine")(self.config_path)
        return EX_OK

    def preform_create_action(self):
        # Make sure the provider environments are correct
        ensure_vnet_lxc_environment(self.config)
        # Make the machines
        machine_op.create_machines(self.config, machines=self.machines)
        # Put user requested file on the machines
        put_files_on_machine(self.config)
        if not self.no_hosts:
            # Put /etc/hosts on the machines
            generate_vnet_hosts_file(self.config)
            place_vnet_hosts_file_on_machines(self.config)
        # Configure type specific stuff
        machine_op.enable_type_specific_machine_configuration(self.config)

    def preform_destroy_action(self):
        if self.purge:
            self.preform_purge_action()
        elif self.base_image:
            request_confirmation(prompt="Are you sure you want to delete the VNet base images (y/n)? ")
            destroy_lxc_image(settings.LXC_BASE_IMAGE_ALIAS, by_alias=True)
        else:
            machine_op.destroy_machines(self.config, machines=self.machines)
            # If specific machines are specified, we don't want to mess with the interfaces
            if self.machines:
                logger.warning(
                    "Not deleting VNet interfaces as we are only destroying specific machines, this may leave lingering sniffers"
                )
            else:
                delete_vnet_interfaces(self.config)

    def preform_list_action(self):
        if not isdir(self.config_path):
            logger.error(f"Provided path {self.config_path} does not seem to be a directory")
            return EX_OSERR
        yaml_files = get_yaml_files_from_disk_path(self.config_path)
        for path in yaml_files:
            self.config_path = path
            if not self.parse_config():
                logger.error(f"Config {path} does not seem to be a valid config, skipping")
                continue
            logger.info(f"Showing machine status for {path}")
            machine_op.show_status(self.config)
        return EX_OK

    @staticmethod
    def preform_version_action():
        show_version()

    @staticmethod
    def preform_bash_completion_action():
        bash_script_content = generate_bash_completion_script()
        write_file_to_disk(settings.VNET_BASH_COMPLETION_PATH, bash_script_content)
        logger.info("Bash completion generated and placed. Use ' . /etc/bash_completion' to load in this terminal")

    @staticmethod
    def preform_purge_action():
        cleanup_vnet_lxc_environment()
