from argparse import Namespace, ArgumentParser
from typing import Sequence

from vnet_manager.conf import settings


def parse_vnet_args(args: Sequence = None) -> Namespace:
    parser = ArgumentParser(description="VNet-manager a virtual network manager - manages containers to create virtual networks")
    parser.add_argument(
        "action",
        choices=sorted(settings.VALID_ACTIONS),
        help="The action to preform on the virtual network, use '<action> help' for information about that action",
    )
    parser.add_argument("config", help="The yaml config file to use", nargs="?", default="default")

    # Options
    parser.add_argument(
        "-m",
        "--machines",
        nargs="*",
        help="Just apply the actions on the following machine names " "(default is all machines defined in the config file)",
    )
    parser.add_argument("-y", "--yes", action="store_true", help="Answer yes to all questions")
    parser.add_argument("-nh", "--no-hosts", action="store_true", help="Disable creation of /etc/hosts")

    start_group = parser.add_argument_group("Start options", "These options can be specified for the start action")
    start_group.add_argument("-s", "--sniffer", action="store_true", help="Start a TCPdump sniffer on the VNet interfaces")

    destroy_group = parser.add_argument_group("Destroy options", "These options can be specified for the destroy action")
    destroy_group.add_argument("-b", "--base-image", action="store_true", help="Destroy the base image instead of the machines")

    connect_group = parser.add_argument_group("Connect actions", "These options can be specified for the connect action")
    connect_group.add_argument("-p", "--provider", default="lxc", help="The provider to use to connect to the container (default: lxc)")

    logging_group = parser.add_argument_group("Verbosity options", "Control output verbosity (can be supplied multiple times)")
    logging_group.add_argument("-v", "--verbose", action="count", default=0, help="Be more verbose")
    logging_group.add_argument("-q", "--quite", action="count", default=0, help="Be more quite")
    return validate_argument_sanity(parser.parse_args(args=args), parser)


def validate_argument_sanity(args: Namespace, parser: ArgumentParser) -> Namespace:
    """
    Validates the passed arguments for sanity
    :param args: Namespace, The already processed user arguments
    :param parser: ArgumentParser, The parser object
    :return: Namespace, The validated arguments
    :raises: SystemExit, if arguments are not sane
    """
    # User input sanity checks
    if args.action == "status":
        # For people who are used to status calls
        args.action = "show"
    if args.config == "default" and args.action in settings.CONFIG_REQUIRED_ACTIONS:
        msg = (
            "This action requires a machine name to be passed"
            if args.action == "connect"
            else "This action requires a config file to be passed"
        )
        parser.error(msg)
    if args.sniffer and not args.action == "start":
        parser.error("The sniffer option only makes sense with the 'start' action")
    if args.base_image and not args.action == "destroy":
        parser.error("The base_image option only makes sense with the 'destroy' action")
    if args.no_hosts and not args.action == "create":
        parser.error("The no_hosts option only makes sense with the 'create' action")
    return args
