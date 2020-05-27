import sys
from argparse import ArgumentParser
from logging import INFO, DEBUG, getLogger
from os import EX_NOPERM

from vnet_manager.conf import settings
from vnet_manager.log import setup_console_logging
from vnet_manager.actions.manager import action_manager
from vnet_manager.utils.user import check_for_root_user

logger = getLogger(__name__)


def parse_args(args=None):
    parser = ArgumentParser(description="VNet-manager a virtual network manager - manages containers and VMs to create virtual networks")
    parser.add_argument("action", choices=settings.VALID_ACTIONS, help="The action to preform on the virtual network")
    parser.add_argument("config", help="The yaml config file to use")

    # Options
    parser.add_argument(
        "-m",
        "--machines",
        nargs="*",
        help="Just apply the actions on the following machine names " "(default is all machines defined in the config file)",
    )
    parser.add_argument("-y", "--yes", action="store_true", help="Answer yes to all questions")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print debug messages")

    return parser.parse_args(args=args)


def main(args=None):
    """
    Program entry point
    :param list args: The pre-cooked arguments to pass to the ArgParser
    :return int: exit_code
    """
    args = parse_args(args)
    setup_console_logging(verbosity=DEBUG if args.verbose else INFO)
    if not check_for_root_user():
        logger.critical("This program should only be run as root")
        return EX_NOPERM
    return action_manager(args.action, args.config, force=args.yes, machines=args.machines)


if __name__ == "__main__":
    sys.exit(main())
