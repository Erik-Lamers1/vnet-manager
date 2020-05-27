import sys
from os import geteuid
from logging import getLogger

logger = getLogger(__name__)


def check_for_root_user():
    """
    Checks if the user running this is root
    :return: bool: True if the user is root, False otherwise
    """
    return geteuid() == 0


def request_confirmation(message=None, prompt="Continue? (yes/no) ", func=sys.exit, args=None, kwargs=None):
    """
    Prompt user for confirmation before continuing program execution.

    :param message:
        An optional message to print before showing the prompt.
    :param prompt:
        The prompt to display.
    :param func:
        The function that is called when the user answers NO
    :param args:
        Positional arguments passed to the above function.
    :param kwargs:
        Keyword arguments passed to the above function.
    """
    if args is None and func == sys.exit:
        args = [1]
    elif args is None:
        args = []
    if kwargs is None:
        kwargs = {}

    if message is not None:
        logger.warning(message)

    response = None
    while True:
        if response in ("y", "yes"):
            return
        elif response in ("n", "no"):
            func(*args, **kwargs)
            return
        elif response is not None:
            print("Please answer yes or no.")
        response = input(prompt).lower()
