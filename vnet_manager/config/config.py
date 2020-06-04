from logging import getLogger
from os.path import realpath, dirname

from vnet_manager.conf import settings
from vnet_manager.utils.files import get_yaml_content

logger = getLogger(__name__)


def get_config(path):
    """
    Produces the vnet config that can be used by other functions
    :param str path: The path to load the user config from (overwrites the default config)
    :return: dict: The merged user and default configs
    """
    logger.debug("Getting user config")
    user_config = get_yaml_content(path)
    logger.debug("Getting default config")
    defaults = get_yaml_content(settings.CONFIG_DEFAULTS_LOCATION)
    logger.debug("Merging configs")
    # This statement requires Python3.5+
    config = {**defaults, **user_config}
    # Add the config directory
    config["config_dir"] = dirname(realpath(path))
    return config
