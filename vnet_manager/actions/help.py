from logging import getLogger

from vnet_manager.conf import settings

logger = getLogger(__name__)


def display_help_for_action(action: str) -> None:
    """
    Print a help text for the supplied action
    :param str action: The action to display the help text for
    """
    # First check if we have help text for this action
    if action not in settings.HELP_TEXT_ACTION_MAPPING:
        logger.warning("No help text available for action {}".format(action))
        return

    # Display the help text
    logger.debug("Displaying help text for action {}".format(action))
    print(settings.HELP_TEXT_ACTION_MAPPING[action])
