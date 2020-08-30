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


def write_file_to_disk(path, content):
    """
    Write a file to disk
    Overwrites if file already exists
    :param: str: path: The filepath to write the file to
    :param: content: The content to write to the file
    """
    logger.debug("Writing content to {}".format(path))
    with open(path, "w") as fh:
        fh.write(content)
