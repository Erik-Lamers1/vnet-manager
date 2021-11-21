from argparse import Namespace, ArgumentParser
from typing import Sequence

from vnet_manager.conf import settings


def parse_vnet_args(args: Sequence = None) -> Namespace:
    # Global Options
    parser = ArgumentParser(description="VNet-manager a virtual network manager - manages containers to create virtual networks")
    parser.add_argument("-y", "--yes", action="store_true", help="Answer yes to all questions")
    logging_group = parser.add_argument_group("Verbosity options", "Control output verbosity (can be supplied multiple times)")
    logging_group.add_argument("-v", "--verbose", action="count", default=0, help="Be more verbose")
    logging_group.add_argument("-q", "--quite", action="count", default=0, help="Be more quite")

    parent_parser = ArgumentParser(add_help=False)
    parent_parser.add_argument("config", help="The yaml config file to use")
    parent_parser.add_argument(
        "-m",
        "--machines",
        nargs="*",
        help="Just apply the actions on the following machine names " "(default is all machines defined in the config file)",
    )

    # Subcommand Options
    subparsers = parser.add_subparsers(dest="action", required=True)
    show_parser = subparsers.add_parser("show", parents=[parent_parser], aliases=["status"])
    start_parser = subparsers.add_parser("start", parents=[parent_parser])
    start_parser.add_argument("-s", "--sniffer", action="store_true", help="Start a TCPdump sniffer on the VNet interfaces")
    start_parser.add_argument("-nh", "--no-hosts", action="store_true", help="Disable creation of /etc/hosts")
    stop_parser = subparsers.add_parser("stop", parents=[parent_parser])
    create_parser = subparsers.add_parser("create", parents=[parent_parser])
    destroy_parser = subparsers.add_parser("destroy", parents=[parent_parser])
    destroy_parser.add_argument("-b", "--base-image", action="store_true", help="Destroy the base image instead of the machines")

    list_parser = subparsers.add_parser("list")
    clean_parser = subparsers.add_parser("clean")
    version_parser = subparsers.add_parser("version")
    bash_parser = subparsers.add_parser("bash-completion")

    return parser.parse_args(args=args)