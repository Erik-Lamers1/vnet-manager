from logging import getLogger

from vnet_manager.conf import settings
from vnet_manager.utils.version import show_version

logger = getLogger(__name__)


def action_manager(action, force=False):
    """
    Initiate an action
    :param str action: The action to preform
    :param bool force: Do not ask for user input on dangerous actions, just do it
    """
    logger.debug("Initiating {} action".format(action))
    if action == "version":
        show_version()
        return

    # For these actions we need the config
    if action not in settings.VALID_ACTIONS:
        raise NotImplementedError("{} is not a valid action".format(action))
    if action == "list":
        raise NotImplementedError("The list action has not been made yet, sorry.")
    if action == "start":
        raise NotImplementedError("The list action has not been made yet, sorry.")
    if action == "stop":
        raise NotImplementedError("The list action has not been made yet, sorry.")
    if action == "create":
        raise NotImplementedError("The list action has not been made yet, sorry.")
    if action == "destroy":
        raise NotImplementedError("The list action has not been made yet, sorry.")
