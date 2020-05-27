from os import geteuid


def check_for_root_user():
    """
    Checks if the user running this is root
    :return: bool: True if the user is root, False otherwise
    """
    return geteuid() == 0
