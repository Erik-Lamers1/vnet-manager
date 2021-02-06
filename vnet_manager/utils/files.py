from os.path import isfile, join
from os import walk
from yaml import safe_load
from logging import getLogger
from typing import AnyStr, List

logger = getLogger(__name__)


def get_yaml_content(path: str) -> dict:
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


def write_file_to_disk(path: str, content: AnyStr):
    """
    Write a file to disk
    Overwrites if file already exists
    :param: str: path: The filepath to write the file to
    :param: content: The content to write to the file
    """
    logger.debug("Writing content to {}".format(path))
    with open(path, "w") as fh:
        fh.write(content)


def get_yaml_files_from_disk_path(path: str, excludes_files: List[str] = None) -> List[str]:
    """
    Returns a list of yaml files from a path (recursive search)
    :param path: str: The path to search in
    :param excludes_files: list: Of filenames to exclude
    :return: list of paths: the found yaml files
    """

    def should_be_excluded(root_path, file):
        if excludes_files:
            return file in excludes_files or join(root_path, file) in excludes_files
        return False

    yaml_files = []
    logger.debug("Retrieving yaml files from path: {}".format(path))
    for root, _, files in walk(path):
        for f in files:
            if (f.endswith("yaml") or f.endswith("yml")) and not should_be_excluded(root, f):
                yaml_files.append(join(root, f))
    return yaml_files
