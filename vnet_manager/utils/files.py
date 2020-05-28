from os.path import isfile
from yaml import safe_load
from logging import getLogger

logger = getLogger(__name__)


def get_yaml_content(path):
    """
    Loads a YAML config file and returns the contents
    :param str path: The YAML file to load
    :return: dict: The YAML file contents
    """
    if not isfile(path):
        logger.error("File {} does not exist".format(path))
        raise IOError("File {} does not exist".format(path))

    logger.debug("Loading YAML values from {}".format(path))
    with open(path, "r") as fh:
        content = safe_load(fh)
    return content
