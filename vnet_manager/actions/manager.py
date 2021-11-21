from logging import getLogger
from os import EX_OK, EX_USAGE
from os.path import isdir, isfile
from warnings import warn
from typing import Optional, Tuple, List

from vnet_manager.conf import settings
from vnet_manager.config.config import get_config
from vnet_manager.config.validate import ValidateConfig
from vnet_manager.utils.version import show_version
from vnet_manager.utils.user import request_confirmation, generate_bash_completion_script
from vnet_manager.utils.files import write_file_to_disk, get_yaml_files_from_disk_path
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


class ActionManager:
    """
    The VNet Action Manager class
    Use this class to initiate specific VNet action in a controlled manner
    """

    def __init__(self, config_path: str = None, sniffer: bool = False, base_image: bool = False, no_hosts: bool = False):
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
        self._machines = None
        self._config_validated = False

    @property
    def machines(self) -> Optional[List[str]]:
        return self._machines

    @machines.setter
    def machines(self, machines: List[str]):
        """
        Only preform actions on a certain amount of machines.
        Note that this only applies to the machine actions, all general actions will ignore this value.
        :param list machines: The machine names to preform actions on, defaults to all
        """
        self._machines = machines

    def execute(self, action: str) -> int:
        """
        Execute an action
        :param str action: The name of the action to execute
        :raises NotImplementedError: If the action is unknown
        :raises RuntimeError
        :return: int: returncode of the action
        """
        # First do a sanity check on the action
        if action not in settings.VALID_ACTIONS:
            raise NotImplementedError("{} is not a valid action".format(action))
        # Check if the operator only wants to see the help text
        if self.config_path and self.config_path.lower() == "help":
            display_help_for_action(action)
            return EX_OK
        # Check if a config is required
        if action in settings.CONFIG_REQUIRED_ACTIONS:
            if not self.config_path:
                raise RuntimeError("The {} action requires a config to be passed, but it wasn't".format(action))
            if not self.parse_config():
                logger.critical("Config NOT OK, can't proceed")
                return EX_USAGE
        # Preform the action
        logger.info("Initiating {} action".format(action))
        getattr(self, "preform_{}_action".format(action.replace("-", "_")))()
        return EX_OK

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
            return False, dict()
        # Everything okay
        logger.debug("Config validation successful")
        return True, validator.updated_config

    def preform_show_action(self):
        show_status(self.config)
        show_vnet_interface_status(self.config)
        if "veths" in self.config:
            show_vnet_veth_interface_status(self.config)

    def preform_status_action(self):
        self.preform_show_action()

    def preform_start_action(self):
        bring_up_vnet_interfaces(self.config, sniffer=self.sniffer)
        change_machine_status(self.config, machines=self._machines, status="start")

    def preform_stop_action(self):
        change_machine_status(self.config, machines=self._machines, status="stop")
        # If specific machines are specified, we don't want to mess with the interfaces
        if self._machines:
            logger.warning("Not bringing down VNet interfaces as we are only stopping specific machines, this may leave lingering sniffers")
        else:
            bring_down_vnet_interfaces(self.config)

    def preform_create_action(self):
        # Make sure the provider environments are correct
        ensure_vnet_lxc_environment(self.config)
        # Make the machines
        create_machines(self.config, machines=self._machines)
        # Put user requested file on the machines
        put_files_on_machine(self.config)
        if not self.no_hosts:
            # Put /etc/hosts on the machines
            generate_vnet_hosts_file(self.config)
            place_vnet_hosts_file_on_machines(self.config)
        # Configure type specific stuff
        enable_type_specific_machine_configuration(self.config)

    def preform_destroy_action(self):
        if self.base_image:
            request_confirmation(prompt="Are you sure you want to delete the VNet base images (y/n)? ")
            destroy_lxc_image(settings.LXC_BASE_IMAGE_ALIAS, by_alias=True)
        else:
            destroy_machines(self.config, machines=self._machines)
            # If specific machines are specified, we don't want to mess with the interfaces
            if self._machines:
                logger.warning(
                    "Not deleting VNet interfaces as we are only destroying specific machines, this may leave lingering sniffers"
                )
            else:
                delete_vnet_interfaces(self.config)

    def preform_list_action(self):
        # First check if we have been passed a file or directory
        if isfile(self.config_path):
            dep_msg = "List action with a regular config file is deprecated, use the 'show' action instead"
            logger.warning(dep_msg)
            warn(dep_msg)
            # Execute the show action instead
            self.execute("show")
        elif isdir(self.config_path):
            # We exclude the default.yaml config file because it is not a valid user config
            yaml_files = get_yaml_files_from_disk_path(self.config_path)
            for path in yaml_files:
                self.config_path = path
                if not self.parse_config():
                    logger.error("Config {} does not seem to be a valid config, skipping".format(path))
                    continue
                logger.info("Showing machine status for {}".format(path))
                show_status(self.config)
        else:
            logger.error(
                "Path {} does not seem to be a file or a directory, did you forget to pass a config directory?".format(self.config_path)
            )

    @staticmethod
    def preform_version_action():
        show_version()

    @staticmethod
    def preform_bash_completion_action():
        bash_script_content = generate_bash_completion_script()
        write_file_to_disk(settings.VNET_BASH_COMPLETION_PATH, bash_script_content)
        logger.info("Bash completion generated and placed. Use ' . /etc/bash_completion' to load in this terminal")

    @staticmethod
    def preform_clean_action():
        cleanup_vnet_lxc_environment()
