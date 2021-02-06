from logging import getLogger
from os.path import realpath, dirname

from vnet_manager.utils.files import get_yaml_content

logger = getLogger(__name__)


def get_config(path: str) -> dict:
    """
    Produces the vnet config that can be used by other functions
    :param str path: The path to load the user config from (overwrites the default config)
    :return: dict: The merged user and default configs
    """
    logger.debug("Getting user config")
    config = get_yaml_content(path)
    # Add the config directory
    config["config_dir"] = dirname(realpath(path))
    return config
