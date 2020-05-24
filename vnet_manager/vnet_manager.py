import sys
from argparse import ArgumentParser

from vnet_manager.utils.version import show_version


def parse_args(args=None):
    parser = ArgumentParser(description="VNet-manager a virtual network manager - manages containers and VMs to create virtual networks")
    parser.add_argument("config", help="The yaml config file to use")

    # Actions
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-l", "--list", action="store_true", help="Show the virtual network")
    group.add_argument("-s", "--start", action="store_true", help="Start the resources")
    group.add_argument("-S", "--stop", action="store_true", help="Stop the resources")
    group.add_argument("-c", "--create", action="store_true", help="Create the resources")
    group.add_argument("-d", "--destroy", action="store_true", help="Destroy the resources")
    group.add_argument("-V", "--version", action="store_true", help="Print version and exit")

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
    args = parse_args(args)
    if args.version:
        show_version()
        sys.exit(0)


if __name__ == "__main__":
    main()
