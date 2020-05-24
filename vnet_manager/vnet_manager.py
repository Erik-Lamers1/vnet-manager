import sys
from argparse import ArgumentParser
from logging import INFO, DEBUG

from vnet_manager.conf import settings
from vnet_manager.log import setup_console_logging
from vnet_manager.actions.manager import action_manager


def parse_args(args=None):
    parser = ArgumentParser(description="VNet-manager a virtual network manager - manages containers and VMs to create virtual networks")
    parser.add_argument("action", choices=settings.VALID_ACTIONS, help="The action to preform on the virtual network")
    parser.add_argument("config", help="The yaml config file to use")

    # Options
    parser.add_argument(
        "--containers",
        nargs="*",
        help="Just apply the actions on the following container names " "(default is all containers defined in the config file)",
    )
    parser.add_argument("-y", "--yes", action="store_true", help="Answer yes to all questions")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print debug messages")

    return parser.parse_args(args=args)


def main(args=None):
    """
    Program entry point
    :param list args: The pre-cooked arguments to pass to the ArgParser
    """
    args = parse_args(args)
    setup_console_logging(verbosity=DEBUG if args.verbose else INFO)
    action_manager(args.action)


if __name__ == "__main__":
    main()
