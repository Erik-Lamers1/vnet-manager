#!/usr/bin/env python
from logging import getLogger, DEBUG
from argparse import ArgumentParser
from yamllint.config import YamlLintConfig
from yamllint.cli import show_problems
from yamllint import linter
from typing import List

from vnet_manager.conf import settings
from vnet_manager.log import setup_console_logging
from vnet_manager.utils.files import get_yaml_files_from_disk_path


logger = getLogger("tools.yaml_syntax_validator")


def check_yaml_file_syntax(files: List[str]) -> int:
    """
    Check each file with yamllint and print the errors if any
    :param files: The files to put through yamllint
    :return: int: The amount of lint errors encountered
    """
    errors = 0
    config = YamlLintConfig(file=settings.YAMLLINT_CONFIG_FILE)
    for file_path in files:
        try:
            with open(file_path, "r") as f:
                gen = linter.run(f, config)
                problems = list(gen)
                if problems:
                    errors += 1
                    show_problems(problems, file_path, "colored", False)
        except IOError:
            logger.error("ERROR: Could not open {} for yaml syntax checking".format(file_path))
            errors += 1
    return errors


def main():
    """
    This script will check for each valid sls yaml file is the file passes the yamllint checks.
    A valid yamllint config file should be present in YAMLLINT_CONFIG_FILE
    """
    setup_console_logging(verbosity=DEBUG)
    parser = ArgumentParser(description="Verify (example) config files for valid YAML syntax")
    parser.parse_args()

    yaml_files = get_yaml_files_from_disk_path(settings.CONFIG_FILE_DIR)
    errors = check_yaml_file_syntax(yaml_files)

    logger.debug("#" * 80)
    if errors:
        logger.info("{} files have yamllint issues, please fix them before proceeding".format(errors))
    else:
        logger.info("No yamllint errors encountered, nice :)")
    logger.debug("#" * 80)

    exit(1 if errors else 0)


if __name__ == "__main__":
    main()
