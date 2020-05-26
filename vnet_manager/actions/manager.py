from logging import getLogger
from os import EX_OK, EX_USAGE

from vnet_manager.conf import settings
from vnet_manager.config.config import get_config
from vnet_manager.config.validate import validate_config
from vnet_manager.utils.version import show_version
from vnet_manager.operations.status import show_status, change_machine_status

logger = getLogger(__name__)


def action_manager(action, config, force=False, machines=None):
    """
    Initiate an action
    :param str action: The action to preform
    :param str config: The path to the user config file
    :param bool force: Do not ask for user input on dangerous actions, just do it
    :param list machines: The specific container to execute actions on
    :return int: exit_code
    """
    # Check for valid action
    if action not in settings.VALID_ACTIONS:
        raise NotImplementedError("{} is not a valid action".format(action))
    logger.debug("Initiating {} action".format(action))

    # These actions do not require the config
    if action == "version":
        show_version()
        return EX_OK

    # For these actions we need the config
    config = get_config(config)
    # Validate the config
    config_ok, config = validate_config(config)
    if config_ok:
        logger.debug("Config successfully validated")
    else:
        logger.critical("The config seems to have unrecoverable issues, please fix them before proceeding")
        return EX_USAGE

    if action == "list":
        show_status(config)
    if action == "start":
        change_machine_status(config, machines=machines, status="start")
    if action == "stop":
        change_machine_status(config, machines=machines, status="stop")
    if action == "create":
        raise NotImplementedError("The list action has not been made yet, sorry.")
    if action == "destroy":
        raise NotImplementedError("The list action has not been made yet, sorry.")

    # Finally return all OK
    return EX_OK
