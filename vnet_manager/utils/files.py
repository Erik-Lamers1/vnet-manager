from os.path import isfile, join
from os import walk
from logging import getLogger
from typing import AnyStr, List
from yaml import safe_load

logger = getLogger(__name__)


def get_yaml_content(path: str) -> dict:
    """
    Loads a YAML config file and returns the contents
    :param str path: The YAML file to load
    :return: dict: The YAML file contents
    """
    if not isfile(path):
        logger.error(f"File {path} does not exist")
        raise IOError(f"File {path} does not exist")

    logger.debug(f"Loading YAML values from {path}")
    with open(path, "r", encoding="utf-8") as fh:
        content = safe_load(fh)
    return content


def write_file_to_disk(path: str, content: AnyStr):
    """
    Write a file to disk
    Overwrites if file already exists
    :param: str: path: The filepath to write the file to
    :param: content: The content to write to the file
    """
    logger.debug(f"Writing content to {path}")
    with open(path, "w", encoding="utf-8") as fh:
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
    logger.debug(f"Retrieving yaml files from path: {path}")
    for root, _, files in walk(path):
        for f in files:
            if (f.endswith("yaml") or f.endswith("yml")) and not should_be_excluded(root, f):
                yaml_files.append(join(root, f))
    return yaml_files
