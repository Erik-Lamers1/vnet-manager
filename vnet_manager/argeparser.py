from argparse import Namespace, ArgumentParser
from typing import Sequence

from vnet_manager.conf import settings


class VNetParser(ArgumentParser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Add verbosity args and force arg to each subparser
        # Add force option
        self.add_argument("-y", "--yes", action="store_true", help="Answer yes to all questions (force)")
        # Verbosity
        logging_group = self.add_argument_group("Verbosity options", "Control output verbosity (can be supplied multiple times)")
        logging_group.add_argument("-v", "--verbose", action="count", default=0, help="Be more verbose")
        logging_group.add_argument("-q", "--quite", action="count", default=0, help="Be more quite")


def parse_vnet_args(args: Sequence = None) -> Namespace:
    parser = ArgumentParser(description="VNet-manager a virtual network manager - manages containers to create virtual networks")
    # Add parsers for all the possible user actions
    add_action_parsers(parser)
    return parser.parse_args(args=args)


def add_action_parsers(parser: ArgumentParser) -> ArgumentParser:
    action_parser = parser.add_subparsers(
        title="Actions",
        description="Which action to preform, each individual action has its own help menu",
        dest="action",
        required=True,
        parser_class=VNetParser,
    )

    # Let's try to keep this list in alphabetical order
    action_parser.add_parser("bash-completion", help="Places the bash completion script")

    create_parser = action_parser.add_parser("create", help="Builds a VNet configuration")
    create_parser.add_argument(
        "config", help="The config (YAML) to build, creates any configuration for providers that have not been initialized yet"
    )
    create_parser.add_argument("-nh", "--no-hosts", action="store_true", help="Disable creation of /etc/hosts")
    create_parser.add_argument(
        "-m", "--machines", nargs="*", help="Only create the following machines (defaults to all machines in the config file)"
    )

    connect_parser = action_parser.add_parser("connect", help="Open a shell on a machine")
    connect_parser.add_argument("config", help="Which machine to connect to", metavar="machine")
    connect_parser.add_argument(
        "-p",
        "--provider",
        default="lxc",
        choices=settings.PROVIDERS.keys(),
        help="The provider to use to connect to the machine (default: lxc)",
    )

    destroy_parser = action_parser.add_parser("destroy", help="Destroy options for machines, images and configs")
    destroy_opt = destroy_parser.add_mutually_exclusive_group(required=True)
    destroy_opt.add_argument("-c", "--config", help="The config (YAML) to destroy the machines and VNet-interfaces for")
    destroy_opt.add_argument("-b", "--base-image", action="store_true", help="Destroy the VNet-manager base image")
    destroy_opt.add_argument(
        "-p",
        "--purge",
        action="store_true",
        help="Purge the VNet-manager provider specific configurations from this machine. "
        "All previously build configs must have been destroyed. (This operation was previously called 'clean'",
    )

    list_parser = action_parser.add_parser("list", help="Recursive search for all configs in the supplied directory")
    list_parser.add_argument("directory", help="The directory in which to list the machines statuses")

    show_parser = action_parser.add_parser("show", help="Show the current status of the supplied config file", aliases=["status"])
    show_parser.add_argument("config", help="The config (YAML) to get the status for")

    start_parser = action_parser.add_parser("start", help="Starts up a previously built config")
    start_parser.add_argument("config", help="The config (YAML) to startup")
    start_parser.add_argument("-s", "--sniffer", action="store_true", help="Start a TCPdump sniffer on the VNet interfaces")
    start_parser.add_argument(
        "-pd",
        "--pcap-dir",
        default=settings.VNET_SNIFFER_PCAP_DIR,
        help=f"The directory to store the PCAP files in (default: {settings.VNET_SNIFFER_PCAP_DIR})",
    )
    start_parser.add_argument(
        "-m", "--machines", nargs="*", help="Only start the following machines (defaults to all machines in the config file)"
    )

    stop_parser = action_parser.add_parser("stop", help="Stops a previously started config.")
    stop_parser.add_argument("config", help="The config (YAML) to stop")
    stop_parser.add_argument(
        "-m", "--machines", nargs="*", help="Only stop the following machines (defaults to all machines in the config file)"
    )

    return parser
