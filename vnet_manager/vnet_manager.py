import sys
from argparse import ArgumentParser
from logging import INFO, DEBUG, getLogger
from os import EX_NOPERM, environ

from vnet_manager.conf import settings
from vnet_manager.log import setup_console_logging
from vnet_manager.actions.manager import ActionManager
from vnet_manager.utils.user import check_for_root_user

logger = getLogger(__name__)


def parse_args(args=None):
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
    parser.add_argument("-v", "--verbose", action="store_true", help="Print debug messages")
    parser.add_argument("-nh", "--no-hosts", action="store_true", help="Disable creation of /etc/hosts")

    start_group = parser.add_argument_group("Start options", "These options can be specified for the start action")
    start_group.add_argument("-s", "--sniffer", action="store_true", help="Start a TCPdump sniffer on the VNet interfaces")
    destroy_group = parser.add_argument_group("Destroy options", "These options can be specified for the destroy action")
    destroy_group.add_argument("-b", "--base-image", action="store_true", help="Destroy the base image instead of the machines")
    args = parser.parse_args(args=args)

    # User input sanity checks
    if args.config == "default" and args.action in settings.CONFIG_REQUIRED_ACTIONS:
        parser.error("This action requires a config file to be passed")
    if args.sniffer and not args.action == "start":
        parser.error("The sniffer option only makes sense with the 'start' action")
    if args.base_image and not args.action == "destroy":
        parser.error("The base_image option only makes sense with the 'destroy' action")
    if args.no_hosts and not args.action == "create":
        parser.error("The no_hosts option only makes sense with the 'create' action")
    return args


def main(args=None):
    """
    Program entry point
    :param list args: The pre-cooked arguments to pass to the ArgParser
    :return int: exit_code
    """
    args = parse_args(args)
    # Set the VNET_FORCE variable, if --yes is given this will answer yes to all questions
    environ[settings.VNET_FORCE_ENV_VAR] = "true" if args.yes else "false"
    # Setup logging
    setup_console_logging(verbosity=DEBUG if args.verbose else INFO)
    # Most VNet operation require root. So, do a root check
    if not check_for_root_user():
        logger.critical("This program should only be run as root")
        return EX_NOPERM
    # Let the action manager handle the rest
    manager = ActionManager(config_path=args.config, sniffer=args.sniffer, base_image=args.base_image, no_hosts=args.no_hosts)
    if args.machines:
        manager.machines = args.machines
    return manager.execute(args.action)


if __name__ == "__main__":
    sys.exit(main())
