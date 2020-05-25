from yaml import safe_load
from os.path import isfile
from logging import getLogger

from vnet_manager.conf import settings

logger = getLogger(__name__)


def get_config(path):
    """
    Produces the vnet config that can be used by other functions
    :param str path: The path to load the user config from (overwrites the default config)
    :return: dict: The merged user and default configs
    """
    logger.info("Getting user config")
    user_config = get_yaml_content(path)
    logger.info("Getting default config")
    defaults = get_yaml_content(settings.CONFIG_DEFAULTS_LOCATION)
    logger.debug("Merging configs")
    # This statement requires Python3.5+
    return {**defaults, **user_config}


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
